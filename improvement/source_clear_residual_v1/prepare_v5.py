"""Corrected context-only profile; adopt all previously correct VERIFY inputs."""
from sr_common import *
import numpy as np
from fractions import Fraction as F
from prepare_v3 import cache_save,cache_load,sample_clock,source_rgb,QUESTION

def context_input65(processor,images,samples,clock,folder):
    import torch
    from PIL import Image
    pts=list(map(F,clock['normalized_exact_pts']));cases=[]
    for ci,start in enumerate(range(0,len(samples),8)):
        ords=samples[start:start+8].tolist();batch=[Image.fromarray(images[i])for i in ords]
        enc=processor.image_processor(images=batch,return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536});original={k:enc[k].contiguous()for k in ('pixel_values','image_grid_thw')};grids=original['image_grid_thw'].tolist();k=len(ords);texts=[]
        for target in range(k):
            content=[dict(type='text',text=QUESTION+'These are ordered frames from a short silent sequence.\n')]
            for j,o in enumerate(ords):content.extend([dict(type='text',text='Frame %d, relative time %.3fs.\n'%(j+1,float(pts[o]-pts[ords[0]]))),dict(type='image')])
            content.append(dict(type='text',text='Does frame %d depict a visual highlight in this context? Answer exactly Yes or No.'%(target+1)))
            text=processor.apply_chat_template([dict(role='user',content=content)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            for g in grids:text=text.replace('<|image_pad|>','<|placeholder|>'*(g[0]*g[1]*g[2]//4),1)
            texts.append(text.replace('<|placeholder|>','<|image_pad|>'))
        text=processor.tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False);text={q:text[q].contiguous()for q in ('input_ids','attention_mask')};require(text['input_ids'].shape[1]<=4096,'Correct context token budget')
        path=folder/('context_%04d.pt'%ci);torch.save(dict(**original,**text),path)
        cases.append(dict(index=ci,path=str(path),sha256=sha(path),queries=k,samples=ords,grids=grids,token_shape=list(text['input_ids'].shape)))
    return cases

def profile(processor,source,reg):
    from PIL import Image
    w=next(w for w in reg['windows']if w['sid']==source['sid']);m=w['meta']
    z=processor.image_processor(images=[Image.new('RGB',(m['width'],m['height']))],return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536})
    return dict(expected_grid=z['image_grid_thw'].tolist()[0],native_geometry=[m['width'],m['height']],processor_dict=processor.image_processor.to_dict(),explicit_call_size=dict(shortest_edge=65536,longest_edge=65536),synthetic_geometry_check_only=True)

def verify_remaining(source,reg,processor,rt,cv,tokens):
    import torch
    records=[];new_video=0
    for w in reg['windows']:
        if w['sid']!=source['sid']or not w['events']:continue
        reqs=[];existing=[]
        for e in w['events']:
            req=cv.request(e,w['meta']);req['prompt']=cv.prompt(req);reqs.append(req)
            p=ROOT/'inputs'/source['sid']/req['request_id']/'input.json'
            if p.exists():
                x=read(p);require(x['request']==req,'Adopted correct VERIFY request changed');records.append(ref(p));existing.append(x)
        missing=[r for r in reqs if not any(x['request']['request_id']==r['request_id']for x in existing)]
        if not missing:continue
        folder=ROOT/'remaining_verify_v4'/source['sid']/w['uid'];folder.mkdir(parents=True,exist_ok=False)
        if existing:
            first=existing[0];vision=cache_load(bound(first['vision_ref']));txt=torch.load(bound(first['text_ref']),map_location='cpu',weights_only=True);encoded={**vision,**txt};first_prompt=first['request']['prompt'];visionref=first['vision_ref']
        else:
            frames=rt.baseline_frames(w['meta']);encoded,_=rt.encode(processor,w['meta'],frames,F(w['meta']['window_start']),missing[0]['prompt']);encoded=dict(encoded);first_prompt=missing[0]['prompt'];new_video+=1
            p=folder/'vision.pt.gz';cache_save(p,{k:encoded[k]for k in tokens.VISION_KEYS});visionref=ref(p)
        oldsig=w['old_proof']['input_evidence']['tensor_signature'];sig={k:rt.tensor_signature(encoded)[k]for k in tokens.VISION_KEYS}
        require(all(sig[k]==oldsig[k]for k in tokens.VISION_KEYS),'Correct TIME native64 vision must retain original131072 profile')
        for req in missing:
            if req['prompt']==first_prompt:txt={k:encoded[k]for k in tokens.TOKEN_KEYS};combined=encoded
            else:txt,combined,_=tokens.retarget(encoded,processor.tokenizer,first_prompt,req['prompt'],rt.tensor_signature)
            out=folder/req['request_id'];out.mkdir();p=out/'text.pt';torch.save(txt,p)
            record=dict(sid=source['sid'],uid=w['uid'],request=req,vision_ref=visionref,text_ref=ref(p),full_signature=rt.tensor_signature(combined),current_vision_signature=sig,historical_vision_signature={k:oldsig[k]for k in tokens.VISION_KEYS},historical_vision_byte_equal=True,new_observation_difference_ref=None,old_input_ref=dict(path=w['old_proof']['input_path'],sha256=w['old_proof']['input_sha256']))
            save(out/'input.json',record);records.append(ref(out/'input.json'))
    return records,new_video

def main():
    cpu();import torch
    from transformers import AutoProcessor
    torch.set_num_threads(1);reg=read(ROOT/'registration.json');require((ROOT/'profile_v3_owned_controlled_stop.json').exists(),'Explicit actual profile failure recovery required')
    require(not(ROOT/'cpu_completion.json').exists(),'Do not overwrite completed full input stage')
    rt=runtime();cv,tokens,_=verify_modules();cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    video=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072);video.tokenizer.padding_side='left'
    context=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True);context.tokenizer.padding_side='left'
    # Exact winning image recipe check against a real prior accepted grid,
    # using only a synthetic geometry fixture (no old successful image encode).
    from PIL import Image
    from PIL import Image as PILImage
    reference=read(PRIOR/'inputs/S01/acceptance.json');g=reference['chunks'][0]['grid'][0]
    sw=next(w for w in reg['windows']if w['sid']=='S01');m=sw['meta']
    factory=read(ROOT/'context65_factory_check_v4.json')
    require(factory['status']=='PASS_ORIGINAL65K_FACTORY_GEOMETRY_NOT_MODEL_QUALITY'and factory['old_accepted_grid']==g and factory['processor_dict']==context.image_processor.to_dict(),'Adopt actual successful original65K factory check, do not repeat it')
    records=[];contexts=[];new_video=0;adopted_sources=[]
    for s in reg['sources']:
        sid=s['sid'];old=ROOT/'inputs'/sid/'source_completion.json'
        if s['group']=='train':
            d=read(old);require(d['registration_sha256']==sha(ROOT/'registration.json'),'Adopt correct SumMe source identity');records.extend(d['verify_inputs']);adopted_sources.append(sid);continue
        out=ROOT/'contexts65_v4'/sid
        if (out/'completion.json').exists()and(out/'remaining_verify_completion.json').exists():
            completed=read(out/'completion.json');vr=read(out/'remaining_verify_completion.json')
            for c in completed['cases']:bound(c);bound(c['profile_ref'])
            for r in vr['verify_inputs']:bound(r)
            contexts.append(completed);records.extend(vr['verify_inputs']);new_video+=vr['new_video_prompt_encodes'];event('ADOPT_COMPLETE_CORRECT65K_SOURCE_NO_REPROCESS',sid=sid);continue
        if out.exists():
            recovery=read(ROOT/'input_remaining_recovery_v5.json');require(sid in recovery['partial_source_ids']and not list(out.glob('context_*.pt')),'Only explicitly failed empty remaining source may resume')
        else:out.mkdir(parents=True,exist_ok=False)
        inp=ROOT/'inputs'/sid
        if (inp/'native.npz').exists()and(inp/'clock.json').exists():
            clock=read(inp/'clock.json');n=np.load(inp/'native.npz');groups=n['groups'];samples=n['sample_ordinals']
        else:
            inp.mkdir(parents=True,exist_ok=True)
            if (inp/'clock.json').exists():clock=read(inp/'clock.json')
            else:
                clock=read(bound(s['clock_ref']));clock['normalized_exact_pts']=clock.get('normalized_exact_pts',clock.get('original_exact_pts'));clock['n_frames']=len(clock['normalized_exact_pts']);save(inp/'clock.json',clock)
            if (inp/'native.npz').exists():
                n=np.load(inp/'native.npz');groups=n['groups'];samples=n['sample_ordinals']
            else:groups,samples=sample_clock(clock);np.savez(inp/'native.npz',groups=groups,sample_ordinals=samples)
        contract=profile(context,s,reg);save(out/'profile.json',contract)
        wins=[w for w in reg['windows']if w['sid']==sid];images,_=source_rgb(s,wins,samples)
        cs=context_input65(context,images,samples,clock,out)
        require(all(all(g==contract['expected_grid']for g in c['grids'])for c in cs),'Every real new context must use the corrected65K grid')
        for c in cs:c['profile_ref']=ref(out/'profile.json')
        row=dict(sid=sid,cells=len(samples),cases=cs);save(out/'completion.json',row);contexts.append(row)
        vr,enc=verify_remaining(s,reg,video,rt,cv,tokens);records.extend(vr);new_video+=enc
        save(out/'remaining_verify_completion.json',dict(verify_inputs=vr,new_video_prompt_encodes=enc))
        del images
        event('CORRECTED65K_SOURCE_AND_VERIFY_REMAINDER_COMPLETE',sid=sid,cells=len(samples),VERIFY=len(vr),new_video_encodes=enc)
    require(len(records)==238 and len(contexts)==8 and sum(s['cells']for s in contexts)==2258,'Full unchanged corrected workload')
    require(len({read(r['path'])['request']['request_id']for r in records})==238,'No duplicate existing/new VERIFY input')
    save(ROOT/'cpu_completion.json',dict(status='NEW_INPUTS_COMPLETE_FIRST_INDEPENDENT_QA_REQUIRED',registration_sha256=sha(ROOT/'registration.json'),verify_inputs=records,context_sources=contexts,corrected_image_budget=65536,video_budget_unchanged=True,new_video_prompt_encodes_in_v4=new_video,correct_SumMe_sources_adopted=adopted_sources,wrong_context_inputs_rejected=True,recovery_ref=ref(ROOT/'context_profile_failure_v3.json'),old_B0_calls_repeated=0,new_model_calls=0))

def qa():
    cpu();ac=read(ROOT/'cpu_completion.json')
    require(ac['corrected_image_budget']==65536 and ac['wrong_context_inputs_rejected'],'Correct profile before any GPU')
    for s in ac['context_sources']:
        for c in s['cases']:
            p=read(bound(c['profile_ref']));require(all(g==p['expected_grid']for g in c['grids']),'Independent expected original65K profile, not producer-only self-consistency')
    from prepare_v3 import qa as original_qa
    original_qa()

if __name__=='__main__':
    try:{'prepare':main,'qa':qa}[sys.argv[1]]()
    except BaseException as e:failure('prepare_v5_'+sys.argv[1],e);raise
