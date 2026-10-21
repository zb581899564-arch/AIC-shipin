"""Fixed-duration source-relative ranking input preparation only.

Uses only accepted original image patches and original all-rater references.
No inherited launcher or model is executed by import.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback


def require(condition,message):
    if not condition:raise ValueError(message)


def save(path,value):
    with Path(path).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)


def ref(path):
    p=Path(path).resolve(strict=True);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())


def checked(reference,workspace):
    p=Path(reference['path']).resolve(strict=True)
    require(p.is_relative_to(workspace) and ref(p)==reference,'Artifact byte/path binding changed')
    return p


def loadref(reference,workspace):return json.loads(checked(reference,workspace).read_text())


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def context(root):
    root=Path(root).resolve(strict=True);W=root.parent.parent
    reg=json.loads((root/'registration06.json').read_text());checked(reg['code_ref'],W)
    protocol=loadref(reg['protocol_ref'],W)
    require(protocol['training_pairs']==49 and protocol['main_optimizer_updates']==25,'Exact frozen49pair pilot')
    common=load_module('adopted_visual_input_helpers06',checked(reg['visual_helper_ref'],W))
    old03=Path(reg['visual_helper_ref']['path']).parent
    _,_,_,_,_,manifest,Store,_,_,canonical=common.context(old03)
    return root,W,reg,protocol,common,manifest,Store,canonical


def build_pixels(torch,frames,grid,ordinals,pts,overview,block,sid,source_sha):
    h,w=grid;pixels=[];videos=[];points=[Fraction(t) for t in pts]
    views=[dict(overview),dict(role='Excerpt',cells=block['observations'],origin_exact=block['start_exact'])]
    for view in views:
        indices=view['cells'];require(len(indices)%2==0 and len(indices)>0,'Even real observations without padding')
        ids=[ordinals[i] for i in indices];times=[points[i] for i in ids];origin=Fraction(view['origin_exact'])
        for a,b in zip(indices[::2],indices[1::2]):
            left=frames[a].reshape(h*w,3,2,16,16);right=frames[b].reshape(h*w,3,2,16,16)
            require(torch.equal(left[:,:,0],left[:,:,1]) and torch.equal(right[:,:,0],right[:,:,1]),'Retained image temporal duplication invariant')
            pixels.append(torch.stack((left[:,:,0],right[:,:,0]),2).reshape(h*w,1536))
        videos.append(dict(role=view['role'],owner=dict(source_id=sid,source_sha256=source_sha),cells=indices,
            native_ordinals=ids,exact_pts=list(map(str,times)),origin_exact=str(origin),
            group_timestamps_exact=[str((a+b)/2-origin) for a,b in zip(times[::2],times[1::2])],
            observations=len(indices),groups=len(indices)//2,padding=0))
    require(len(videos[1]['cells'])==12 and videos[1]['native_ordinals']==block['native_observation_ordinals'], 'Exact registered12 excerpt observations')
    return dict(pixel_values_videos=torch.cat(pixels).contiguous(),
        video_grid_thw=torch.tensor([[v['groups'],h,w] for v in videos],dtype=torch.int64)),dict(videos=videos,
        window_start_exact=block['start_exact'],window_end_exact=block['end_exact'],
        sparse_visual_observations_not_continuous_motion=True,new_media_decodes=0,new_image_processor_calls=0)


def build_text(processor,plan,grid,source_end,protocol):
    prompt=protocol['prompt']+'\nSource duration %.6fs; Excerpt global interval [%.6f, %.6f).\n'%(
        float(Fraction(source_end)),float(Fraction(plan['window_start_exact'])),float(Fraction(plan['window_end_exact'])))
    raw=processor.apply_chat_template([dict(role='user',content=[dict(type='text',text=prompt+'Overview:\n'),dict(type='video'),
        dict(type='text',text='\nExcerpt:\n'),dict(type='video')])],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    marker=processor.vision_start_token+processor.video_token+processor.vision_end_token
    parts=raw.split(marker);require(len(parts)==3,'Two explicit source-owned videos')
    text=parts[0]
    for i,(video,(_,h,w)) in enumerate(zip(plan['videos'],grid.tolist())):
        text+=''.join('<%.1f seconds>'%float(Fraction(t))+processor.vision_start_token+processor.video_token*(h*w//4)+processor.vision_end_token
                      for t in video['group_timestamps_exact'])+parts[i+1]
    encoded=processor.tokenizer(text,return_tensors='pt',add_special_tokens=False,truncation=False)
    prefix={k:encoded[k].contiguous() for k in ['input_ids','attention_mask']}
    vid=processor.tokenizer.convert_tokens_to_ids(processor.video_token)
    require(0<prefix['input_ids'].shape[1]<=12288 and int((prefix['input_ids']==vid).sum())==sum(t*h*w//4 for t,h,w in grid.tolist()), 'Actual native video-token map; no truncation')
    return prefix,dict(prompt=prompt,raw_template=raw,expanded_text=text,prefix_tokens=prefix['input_ids'].shape[1],
                       feature_position=prefix['input_ids'].shape[1]-1,labels_in_text=False)


def swapped_excerpt(torch,left,right):
    require(left['video_grid_thw'].tolist()==right['video_grid_thw'].tolist(),'Same-source equal observation grids required')
    groups,h,w=left['video_grid_thw'][-1].tolist();n=groups*h*w
    require(groups==6 and torch.equal(left['pixel_values_videos'][:-n],right['pixel_values_videos'][:-n]),'Shared source Overview must remain identical')
    return dict(left,pixel_values_videos=torch.cat((left['pixel_values_videos'][:-n],right['pixel_values_videos'][-n:])).contiguous())


def prepare(root):
    started=time.monotonic();root,W,reg,p,common,manifest,Store,_=context(root)
    import torch
    from transformers import AutoProcessor
    model=manifest['model_spec'];processor=AutoProcessor.from_pretrained(model['model_dir'],revision=model['revision'],local_files_only=True,trust_remote_code=False)
    feasible=loadref(reg['feasibility_ref'],W)
    require(feasible['status']=='READY_FOR_SEPARATE_SMALL_TRAINING_REVIEW','Actual49/14pair data readiness required')
    out=root/'inputs06';out.mkdir();targets={};cases={};pairs_ids=[];swap_refs=[];source_locks=[]
    for scope in ['train','check']:
        store=Store(manifest,scope);target_rows=[]
        sources=[loadref(r,W) for r in feasible['source_refs'] if Path(r['path']).name.startswith(scope+'_')]
        require(len(sources)==(25 if scope=='train' else 8),'All registered source records, including sparse pair sources')
        for source in sources:
            sid=source['source_id'];require(store.sources[sid]['source_sha256']==source['source_sha256'],'Native pair/media source mismatch')
            source_locks.append(dict(scope=scope,source_id=sid,source_sha256=source['source_sha256'],clock_ref=source['clock_ref']))
            frames,grid,ordinals=store._source_pixels(sid);clock=store.clocks[sid]
            overview=store.requests[store.by_source[sid][0]]['plan']['videos'][0]
            block_map={b['index']:b for b in source['blocks']};needed=sorted({k for v in source['selected_pairs'] for k in [v['left_block'],v['right_block']]})
            in_memory={}
            for index in needed:
                require(time.monotonic()-started<p['max_cpu_prepare_seconds'],'Finite CPU input budget')
                block=block_map[index];uid=f'{scope}_{sid}_B{index:04d}'
                values,plan=build_pixels(torch,frames,grid,ordinals,clock['normalized_exact_pts'],overview,block,sid,source['source_sha256'])
                store._helpers().independent_pixels(frames,grid,values,plan,ordinals,clock['normalized_exact_pts'])
                prefix,text=build_text(processor,plan,values['video_grid_thw'],clock['physical_end_exact'],p)
                values.update(prefix)
                store._helpers().independent_text(processor,plan,values,text)
                prefix_path=out/(uid+'.prefix.pt');torch.save(prefix,prefix_path)
                reloaded=torch.load(prefix_path,map_location='cpu',weights_only=True)
                require(all(torch.equal(prefix[k],reloaded[k]) for k in prefix),'Exact prefix save/reload')
                record=dict(uid=uid,scope=scope,sid=sid,block=block,source_sha256=source['source_sha256'],
                    source_clock_ref=source['clock_ref'],prefix_ref=ref(prefix_path),plan=plan,text=text,
                    input_signature=common.signature(values),labels_in_text=False)
                dst=out/(uid+'.json');save(dst,record);cases[uid]=ref(dst);in_memory[uid]=values
            for number,pair in enumerate(source['selected_pairs']):
                left=f'{scope}_{sid}_B{pair["left_block"]:04d}';right=f'{scope}_{sid}_B{pair["right_block"]:04d}'
                pid=f'{scope}_{sid}_P{number:02d}'
                target_rows.append(dict(pair_id=pid,source_id=sid,left=left,right=right,
                    preference_left=pair['preference_left'],source_pair_count=len(source['selected_pairs']),
                    density_difference=pair['mean_density_difference']))
                if scope=='check':
                    pairs_ids.append(dict(pair_id=pid,source_id=sid,left=left,right=right))
                    for recipient,donor in [(left,right),(right,left)]:
                        cf=swapped_excerpt(torch,in_memory[recipient],in_memory[donor])
                        cf_record=dict(uid=recipient,donor_uid=donor,scope='check',pair_id=pid,
                            type='EXCERPT_PIXEL_SWAP_SAME_SOURCE_FIXED_ORIGINAL_TEXT_COUNTERFACTUAL',
                            input_signature=common.signature(cf),truthful_native_observation=False)
                        dst=out/(recipient+'.swap.json');save(dst,cf_record);swap_refs.append(ref(dst))
            store.close();del frames,in_memory
        targets[scope]=target_rows;save(root/(scope+'_targets06.json'),target_rows)
    require(len(targets['train'])==49 and len(targets['check'])==14,'Frozen49train/14check pair denominator')
    require({v['source_sha256'] for v in source_locks if v['scope']=='train'}.isdisjoint({v['source_sha256'] for v in source_locks if v['scope']=='check'}),'Train/check byte separation')
    save(root/'check_pair_ids06.json',pairs_ids)
    result=dict(status='PASS_FIRST_NATIVE_RELATIVE_RANKER_INPUTS',case_refs=cases,swap_refs=swap_refs,
        train_target_ref=ref(root/'train_targets06.json'),check_target_ref=ref(root/'check_targets06.json'),
        check_pair_ids_ref=ref(root/'check_pair_ids06.json'),source_locks=source_locks,
        actual_train_pairs=49,actual_check_pairs=14,actual_unique_cases=len(cases),counterfactual_cases=len(swap_refs),
        new_media_decode=0,new_image_processor=0,new_model_calls=0,seconds=time.monotonic()-started,
        registration_ref=ref(root/'registration06.json'))
    save(root/'input_acceptance06.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['case_refs','swap_refs','source_locks']}))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-root',required=True);parser.add_argument('--phase',choices=['prepare'],required=True)
    args=parser.parse_args()
    try:
        prepare(args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'06.json'),dict(status='ACTUAL_EXECUTION_FAILURE_NOT_EMPTY_OR_NEGATIVE',traceback=traceback.format_exc()))
        raise


if __name__=='__main__':main()
