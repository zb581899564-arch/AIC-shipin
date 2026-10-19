"""Only missing new-purpose RGB/VERIFY text/VideoXum context inputs."""
from sr_common import *
from fractions import Fraction as F
from bisect import bisect_left
import gzip

QUESTION='A visual highlight is a distinctive action peak, expressive reaction, informative reveal, or visually striking moment. Idle repetition and ordinary transitions need not be highlights. Consider visible evidence, not sound. '

def cache_save(path,value):
    import torch
    lib=W/'twenty_hour_five_20261014_v1/production_stream_cache_v2/code'
    sys.path.insert(0,str(lib));packing=module('sr_pixel_dictionary',lib/'pixel_dictionary.py')
    payload,_=packing.pack(value)
    with Path(path).open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=1,mtime=0) as f:torch.save(payload,f)

def cache_load(path):
    import torch
    lib=W/'twenty_hour_five_20261014_v1/production_stream_cache_v2/code'
    sys.path.insert(0,str(lib));packing=module('sr_pixel_dictionary',lib/'pixel_dictionary.py')
    with gzip.open(path,'rb') as f:return packing.unpack(torch.load(f,map_location='cpu',weights_only=True))

def sample_clock(clock):
    import numpy as np
    pts=list(map(F,clock['normalized_exact_pts']));end=F(clock['physical_end_exact'])
    cells=np.array([int(t*2)for t in pts],np.int64);occupied=np.unique(cells);groups=np.searchsorted(occupied,cells)
    ordinals=[]
    for c in occupied:
        a,b=F(int(c),2),min(F(int(c)+1,2),end);lo,hi=bisect_left(pts,a),bisect_left(pts,b);require(lo<hi,'Occupied native cell')
        mid=(a+b)/2;p=bisect_left(pts,mid,lo,hi);ordinals.append(min([j for j in (p-1,p)if lo<=j<hi],key=lambda j:(abs(pts[j]-mid),j)))
    return groups,np.array(ordinals,np.int64)

def source_rgb(source,windows,samples):
    """New purpose only. Expired RGB is reconstructed and compared to old pixels."""
    import numpy as np
    wanted=set(map(int,samples));missing=[]
    for w in windows:
        if not Path(w['meta']['frame_array_path']).exists():missing.append(w);wanted.update(w['meta']['source_frame_ordinals'])
    if not wanted:return {},0
    import av
    runtime();from source_color import convert_frame
    p=bound(source['media']);meta=windows[0]['meta'];origin=F(meta.get('original_clock_origin_exact','0'))
    points=list(map(F,meta['all_source_exact_pts']));images={};count=0
    with av.open(str(p)) as c:
        stream=c.streams.video[0];stream.thread_count=1
        for i,frame in enumerate(c.decode(stream)):
            count=i+1
            if i in wanted:
                require(F(frame.pts)*F(frame.time_base)-origin==points[i],'New observation does not match inherited native ordinal/PTS')
                images[i]=convert_frame(frame,source['media']['sha256'],'rgb24')
            if i>=max(wanted):break
    require(set(images)==wanted,'Missing actual new-purpose observations')
    for w in missing:
        m=w['meta'];arr=np.stack([images[i]for i in m['source_frame_ordinals']]);pixels=[hashlib.sha256(a.tobytes()).hexdigest()for a in arr]
        require(pixels==m['pixel_sha256'],'Recovered RGB differs from historical actual sample evidence')
        p=ROOT/'inputs'/source['sid']/(w['uid']+'_recovered_rgb.npz')
        with p.open('xb') as f:np.savez_compressed(f,rgb=arr)
        w['new_RGB_ref']=ref(p)
    event('NEW_PURPOSE_SOURCE_RGB_READY',sid=source['sid'],new_sample_count=len(wanted),expired_old_windows=len(missing),old_native_mapping_recomputed=False)
    return images,count

def context_input(processor,source,images,samples,clock,folder):
    import numpy as np
    import torch
    pts=list(map(F,clock['normalized_exact_pts']));cases=[]
    for ci,start in enumerate(range(0,len(samples),8)):
        ords=samples[start:start+8].tolist();batch=np.stack([images[i]for i in ords])
        enc=processor.image_processor(images=batch,return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536})
        original={k:enc[k].contiguous()for k in ('pixel_values','image_grid_thw')};grids=original['image_grid_thw'].tolist();k=len(ords);texts=[]
        for target in range(k):
            content=[dict(type='text',text=QUESTION+'These are ordered frames from a short silent sequence.\n')]
            for j,o in enumerate(ords):content.extend([dict(type='text',text='Frame %d, relative time %.3fs.\n'%(j+1,float(pts[o]-pts[ords[0]]))),dict(type='image')])
            content.append(dict(type='text',text='Does frame %d depict a visual highlight in this context? Answer exactly Yes or No.'%(target+1)))
            text=processor.apply_chat_template([dict(role='user',content=content)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            for g in grids:text=text.replace('<|image_pad|>','<|placeholder|>'*(g[0]*g[1]*g[2]//4),1)
            texts.append(text.replace('<|placeholder|>','<|image_pad|>'))
        tokens=processor.tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False);tokens={k:tokens[k].contiguous()for k in ('input_ids','attention_mask')}
        require(tokens['input_ids'].shape[1]<=4096,'New context token budget')
        path=folder/('context_%04d.pt'%ci);torch.save(dict(**original,**tokens),path)
        cases.append(dict(index=ci,path=str(path),sha256=sha(path),queries=k,samples=ords,grids=grids,token_shape=list(tokens['input_ids'].shape)))
    return cases

def main(pilot=False):
    cpu();import numpy as np
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(1)
    reg=read(ROOT/'registration.json');require(not (ROOT/'cpu_completion.json').exists(),'Successful new inputs cannot repeat')
    rt=runtime();cv,tokens,_=verify_modules();cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072);processor.tokenizer.padding_side='left'
    require(processor.video_processor.size==cfg['video_size'],'Exact original native-video processor config')
    records=[];context_sources=[];decoded=0;encoded_windows=0
    for source in reg['sources']:
        sid=source['sid'];folder=ROOT/'inputs'/sid
        if (folder/'source_completion.json').exists():
            done=read(folder/'source_completion.json');require(done['registration_sha256']==sha(ROOT/'registration.json'),'Explicit remaining-input adoption binding')
            records.extend(done['verify_inputs']);context_sources.extend(done['context_sources']);decoded+=done['new_decode_passes'];encoded_windows+=done['new_video_prompt_encodes'];continue
        folder.mkdir(parents=True,exist_ok=False);source_records_start=len(records);source_context_start=len(context_sources);source_encodes_start=encoded_windows
        import time
        started=time.monotonic()
        wins=[w for w in reg['windows']if w['sid']==sid];clock=read(bound(source['clock_ref']))
        clock['normalized_exact_pts']=clock.get('normalized_exact_pts',clock.get('original_exact_pts'))
        clock['n_frames']=len(clock['normalized_exact_pts']);require(clock['n_frames']==wins[0]['meta']['source_total_frames'],'Inherited exact clock frame domain')
        if source['group']=='check':groups,samples=sample_clock(clock)
        else:groups=samples=np.array([],np.int64)
        images,count=source_rgb(source,wins,samples);decoded+=int(count>0)
        save(folder/'clock.json',clock)
        if source['group']=='check':
            np.savez(folder/'native.npz',groups=groups,sample_ordinals=samples)
            cs=context_input(processor,source,images,samples,clock,folder);context_sources.append(dict(sid=sid,cells=len(samples),cases=cs))
        del images
        for w in wins:
            m=w['meta'];events=w['events']
            if not events:continue
            if 'new_RGB_ref'in w:arr=np.load(bound(w['new_RGB_ref']))['rgb']
            else:arr=rt.baseline_frames(m)[0]
            first=cv.request(events[0],m);first['prompt']=cv.prompt(first)
            encoded,evidence=rt.encode(processor,m,(arr,m['source_frame_ordinals'],m['sample_exact_pts']),F(m['window_start']),first['prompt']);encoded=dict(encoded)
            # Compare inherited vision tensors, independently of the NEW prompt tokens.
            oldsig=w['old_proof']['input_evidence']['tensor_signature']
            for key in ('pixel_values_videos','video_grid_thw'):require(rt.tensor_signature(encoded)[key]==oldsig[key],'New VERIFY vision differs from actual original B0 CPU evidence')
            path=folder/(w['uid']+'_vision.pt.gz');cache_save(path,{k:encoded[k]for k in tokens.VISION_KEYS});visionref=ref(path);encoded_windows+=1
            for i,event0 in enumerate(events):
                req=cv.request(event0,m);req['prompt']=cv.prompt(req);rid=req['request_id'];newfolder=folder/rid;newfolder.mkdir()
                if i==0:txt={k:encoded[k]for k in tokens.TOKEN_KEYS};comb=encoded
                else:txt,comb,_=tokens.retarget(encoded,processor.tokenizer,first['prompt'],req['prompt'],rt.tensor_signature)
                tp=newfolder/'text.pt';torch.save(txt,tp)
                record=dict(sid=sid,uid=w['uid'],request=req,vision_ref=visionref,text_ref=ref(tp),full_signature=rt.tensor_signature(comb),inherited_vision_signature={k:oldsig[k]for k in tokens.VISION_KEYS},old_input_ref=dict(path=w['old_proof']['input_path'],sha256=w['old_proof']['input_sha256']))
                save(newfolder/'input.json',record);records.append(ref(newfolder/'input.json'))
            del encoded,arr
        event('CPU_NEW_SOURCE_COMPLETE',sid=sid,windows=len(wins),verify_inputs=sum(len(w['events'])for w in wins),contexts=len(context_sources[-1]['cases'])if source['group']=='check'else 0)
        rec=dict(registration_sha256=sha(ROOT/'registration.json'),verify_inputs=records[source_records_start:],context_sources=context_sources[source_context_start:],new_decode_passes=int(count>0),new_video_prompt_encodes=encoded_windows-source_encodes_start,elapsed_seconds=time.monotonic()-started,saved_bytes=sum(p.stat().st_size for p in folder.rglob('*')if p.is_file()))
        save(folder/'source_completion.json',rec)
        if pilot:
            save(ROOT/'cpu_first_source_cost.json',dict(sid=sid,**rec));return
    require(len(records)==238 and len(context_sources)==8,'All new registered input denominator')
    save(ROOT/'cpu_completion.json',dict(status='NEW_INPUTS_COMPLETE_FIRST_INDEPENDENT_QA_REQUIRED',registration_sha256=sha(ROOT/'registration.json'),verify_inputs=records,context_sources=context_sources,new_video_prompt_encodes=encoded_windows,new_source_decode_passes=decoded,old_B0_calls_repeated=0,old_native_mapping_recomputed=False,new_model_calls=0))

def qa():
    cpu();import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(1);rt=runtime();cv,tokens,_=verify_modules();cfg=read(RUN/'b_score_aligned_package_v4/config.json');tok=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    ac=read(ROOT/'cpu_completion.json');count=0
    for r in ac['verify_inputs']:
        x=read(bound(r));vis=cache_load(bound(x['vision_ref']));txt=torch.load(bound(x['text_ref']),map_location='cpu',weights_only=True);combined={**vis,**txt}
        require(rt.tensor_signature(combined)==x['full_signature'],'Independent new serialized CPU input signature')
        require(rt.tensor_signature(vis)==x['inherited_vision_signature'],'Inherited original visual tensor identity')
        decoded=tok.decode(txt['input_ids'][0],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        require(decoded.count(x['request']['prompt'])==1 and txt['input_ids'].shape[1]<=16384 and torch.all(txt['attention_mask']==1),'Independent actual prompt/token budget')
        require(cv.prompt(x['request'])==x['request']['prompt'],'Independent frozen VERIFY prompt')
        count+=1
    imagepad=tok.convert_tokens_to_ids('<|image_pad|>');queries=0;cases=0
    for src in ac['context_sources']:
        for c in src['cases']:
            x=torch.load(bound(c),map_location='cpu',weights_only=True);ids=x['input_ids'];mask=x['attention_mask'];expected=[g[0]*g[1]*g[2]//4 for g in c['grids']]
            require(ids.shape==mask.shape and ids.shape[0]==c['queries'] and x['image_grid_thw'].tolist()==c['grids'],'Independent new context shapes')
            for target in range(c['queries']):
                row=ids[target][mask[target].bool()].tolist();lengths=[];n=0
                for t in row+[None]:
                    if t==imagepad:n+=1
                    elif n:lengths.append(n);n=0
                require(lengths==expected and ('Does frame %d depict a visual highlight'%(target+1))in tok.decode(row),'Independent native target/context image order')
            queries+=c['queries'];cases+=1
    require(not torch.cuda.is_initialized() and count==238,'CPU QA has no CUDA and full denominator')
    save(ROOT/'input_qa.json',dict(status='PASS_FIRST_INDEPENDENT_NEW_INPUT_QA',verify_inputs=count,context_cases=cases,context_queries=queries,cpu_completion_sha256=sha(ROOT/'cpu_completion.json'),qa_pid=os.getpid(),new_processor_calls=0))

if __name__=='__main__':
    try:{'prepare':main,'pilot':lambda:main(True),'qa':qa}[sys.argv[1]]()
    except BaseException as e:failure('prepare_'+sys.argv[1],e);raise
