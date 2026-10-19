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
        if not Path(w['meta']['frame_array_path']).exists():
            p=ROOT/'inputs'/source['sid']/(w['uid']+'_recovered_rgb.npz')
            if p.exists():
                arr=np.load(p)['rgb'];require([hashlib.sha256(a.tobytes()).hexdigest()for a in arr]==w['meta']['pixel_sha256'],'Adopted successful recovered pixels changed')
                w['new_RGB_ref']=ref(p)
            else:missing.append(w)
    if not wanted and not missing:return {},0
    import av
    runtime();from source_color import convert_frame
    p=bound(source['media']);meta=windows[0]['meta'];origin=F(meta.get('original_clock_origin_exact','0'))
    points=list(map(F,meta['all_source_exact_pts']));images={};count=0
    if wanted:
        with av.open(source['media']['path']) as c:
            stream=c.streams.video[0];stream.thread_count=1
            for i,frame in enumerate(c.decode(stream)):
                count=i+1
                if i in wanted:
                    require(F(frame.pts)*F(frame.time_base)-origin==points[i],'New observation does not match inherited native ordinal/PTS')
                    images[i]=convert_frame(frame,source['media']['sha256'],'rgb24')
                if i>=max(wanted):break
    require(set(images)==wanted,'Missing actual new-purpose observations')
    for w in missing:
        m=w['meta'];desired={points[i]+origin:i for i in m['source_frame_ordinals']};selected={}
        # Exact historical producer used a separate decoder and backward keyframe
        # seek for each window. VP8 seek state can differ from full-source decode.
        with av.open(source['media']['path']) as c:
            stream=c.streams.video[0];first=points[m['source_frame_ordinals'][0]]+origin
            c.seek(int(first/F(stream.time_base)),stream=stream,backward=True,any_frame=False)
            for frame in c.decode(stream):
                point=F(frame.pts)*F(frame.time_base)
                if point>max(desired):break
                if point in desired:selected[desired[point]]=frame.to_ndarray(format='rgb24')
        require(set(selected)==set(m['source_frame_ordinals']),'Original seek did not recover complete exact64')
        arr=np.stack([selected[i]for i in m['source_frame_ordinals']]);pixels=[hashlib.sha256(a.tobytes()).hexdigest()for a in arr]
        if pixels!=m['pixel_sha256']:
            recovery=read(ROOT/'input_recovery_v3.json')
            require(recovery['new_observations_from_same_media_native_ordinals_allowed'] is True,'Must explicitly register genuinely new observations, not pretend old-byte adoption')
            mismatch=[i for i,(a,b)in enumerate(zip(pixels,m['pixel_sha256']))if a!=b]
            proof=ROOT/'inputs'/source['sid']/(w['uid']+'_new_observation_difference.json')
            save(proof,dict(status='NEW_NATIVE_OBSERVATION_NOT_BYTE_IDENTICAL_TO_EXPIRED_OLD_CACHE',media_ref=source['media'],source_frame_ordinals=m['source_frame_ordinals'],sample_exact_pts=m['sample_exact_pts'],old_pixel_sha256=m['pixel_sha256'],new_pixel_sha256=pixels,mismatch_indices=mismatch,old_byte_adoption=False,old_failure_preserved=True,labels_changed=False))
            w['new_observation_difference_ref']=ref(proof)
        p=ROOT/'inputs'/source['sid']/(w['uid']+'_recovered_rgb.npz')
        with p.open('xb') as f:np.savez_compressed(f,rgb=arr)
        w['new_RGB_ref']=ref(p)
    event('NEW_PURPOSE_SOURCE_RGB_READY',sid=source['sid'],new_sample_count=len(wanted),expired_old_windows=len(missing),old_native_mapping_recomputed=False)
    return images,len(missing)+int(bool(wanted))

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
        if folder.exists():
            recovery=read(ROOT/'input_recovery_v3.json');require(sid in recovery['partial_source_ids'],'Only explicitly registered failed partial source may resume')
            require(not list(folder.glob('sr.*')),'No successful new token preparation may repeat')
        else:folder.mkdir(parents=True,exist_ok=False)
        source_records_start=len(records);source_context_start=len(context_sources);source_encodes_start=encoded_windows
        import time
        started=time.monotonic()
        wins=[w for w in reg['windows']if w['sid']==sid];clock=read(bound(source['clock_ref']))
        clock['normalized_exact_pts']=clock.get('normalized_exact_pts',clock.get('original_exact_pts'))
        clock['n_frames']=len(clock['normalized_exact_pts']);require(clock['n_frames']==wins[0]['meta']['source_total_frames'],'Inherited exact clock frame domain')
        if source['group']=='check':groups,samples=sample_clock(clock)
        else:groups=samples=np.array([],np.int64)
        images,count=source_rgb(source,wins,samples);decoded+=count
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
            current_vision={key:rt.tensor_signature(encoded)[key]for key in ('pixel_values_videos','video_grid_thw')}
            historical_equal=all(current_vision[key]==oldsig[key]for key in current_vision)
            require(historical_equal or 'new_observation_difference_ref'in w,'Unexplained historical visual input change')
            path=folder/(w['uid']+'_vision.pt.gz');cache_save(path,{k:encoded[k]for k in tokens.VISION_KEYS});visionref=ref(path);encoded_windows+=1
            for i,event0 in enumerate(events):
                req=cv.request(event0,m);req['prompt']=cv.prompt(req);rid=req['request_id'];newfolder=folder/rid;newfolder.mkdir()
                if i==0:txt={k:encoded[k]for k in tokens.TOKEN_KEYS};comb=encoded
                else:txt,comb,_=tokens.retarget(encoded,processor.tokenizer,first['prompt'],req['prompt'],rt.tensor_signature)
                tp=newfolder/'text.pt';torch.save(txt,tp)
                record=dict(sid=sid,uid=w['uid'],request=req,vision_ref=visionref,text_ref=ref(tp),full_signature=rt.tensor_signature(comb),current_vision_signature=current_vision,historical_vision_signature={k:oldsig[k]for k in tokens.VISION_KEYS},historical_vision_byte_equal=historical_equal,new_observation_difference_ref=w.get('new_observation_difference_ref'),old_input_ref=dict(path=w['old_proof']['input_path'],sha256=w['old_proof']['input_sha256']))
                save(newfolder/'input.json',record);records.append(ref(newfolder/'input.json'))
            del encoded,arr
        event('CPU_NEW_SOURCE_COMPLETE',sid=sid,windows=len(wins),verify_inputs=sum(len(w['events'])for w in wins),contexts=len(context_sources[-1]['cases'])if source['group']=='check'else 0)
        rec=dict(registration_sha256=sha(ROOT/'registration.json'),verify_inputs=records[source_records_start:],context_sources=context_sources[source_context_start:],new_decode_passes=count,new_video_prompt_encodes=encoded_windows-source_encodes_start,elapsed_seconds=time.monotonic()-started,saved_bytes=sum(p.stat().st_size for p in folder.rglob('*')if p.is_file()))
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
        require(rt.tensor_signature(vis)==x.get('current_vision_signature',x.get('inherited_vision_signature')),'First independent current visual tensor identity')
        if x.get('historical_vision_byte_equal') is False:
            difference=read(bound(x['new_observation_difference_ref']))
            require(difference['old_byte_adoption'] is False and difference['labels_changed'] is False,'New observations cannot claim old byte adoption or alter reference labels')
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
    except BaseException as e:failure('prepare_v3_'+sys.argv[1],e);raise
