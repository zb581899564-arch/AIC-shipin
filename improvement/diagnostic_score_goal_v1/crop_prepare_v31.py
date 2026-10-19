"""First actual crop-derived inputs and2000 fixed training micro references."""
import argparse
from collections import OrderedDict
import datetime as dt
import hashlib
import itertools
import os
from pathlib import Path
import sys
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from crop_common_v31 import *
import crop_geometry_v31 as geom
import crop_image_input_v31 as image

GATE='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA'


class CropInputs:
    def __init__(self,root,*,preparing=False):
        self.root=Path(root);self.reg=registration(self.root);self.cache=OrderedDict()
        require(bound(self.reg['preparation_code'])==Path(__file__).resolve(),'Exact crop preparation')
        if preparing:self.prepared=None
        else:
            gate=read(self.root/'crop_inputs_31/input_acceptance.json')
            require(gate['status']==GATE and gate['registration']==ref(self.root/'crop_CPU_registration_31.json'),
                    'All new crop inputs require actual complete first CPU QA')
            self.prepared=read(bound(gate['prepared']))
    def _vision(self,reference):
        import torch
        key=(reference['path'],reference['sha256'])
        if key in self.cache:self.cache.move_to_end(key);return self.cache[key]
        raw=torch.load(bound(reference),map_location='cpu',weights_only=True)
        result={key:raw[key] for key in ('pixel_values','image_grid_thw')}
        self.cache[key]=result
        while len(self.cache)>12:self.cache.popitem(last=False)
        return result
    def get(self,reference):
        import torch
        request=read(bound(reference));visions=[self._vision(r) for r in request['vision_inputs']]
        grid=torch.cat([v['image_grid_thw'] for v in visions]);packed=image.pack_image_pixels([v['pixel_values'] for v in visions],grid)
        tokens=torch.load(bound(request['tokens']),map_location='cpu',weights_only=True);values=dict(**tokens,**packed)
        require(signature(values)==request['input_signature'] and grid.tolist()==request['image_grid_thw'],
                'Actual crop source/A/B consumed input changed after firstQA')
        return values,request


def _key(*values):return hashlib.sha256('|'.join(map(str,values)).encode()).hexdigest()[:24]


def source_inventory(root,reg):
    """Read original accepted identities; targets stay in separate CPU-only rows."""
    D=Path(reg['train_root']);A=Path(reg['eval_root'])
    manifest=read(bound(reg['original_train_manifest']));accepted=read(bound(reg['original_train_acceptance']))
    require(len(manifest)==len(accepted['sources'])==602,'Exact original602 train source registry')
    records=[];targets={}
    for item,proof in zip(manifest,accepted['sources']):
        require(item['id']==proof['id'] and item['source_sha256']==proof['source_sha256'],'Original train identity')
        original_proof=D/'inputs'/proof['sample_id']/'proof.json'
        require(read(original_proof)==proof,'Adopt original successful full-image proof')
        RGB=dict(path=proof['RGB_path'],sha256=proof['RGB_file_sha256'])
        vision=dict(path=proof['tensor_path'],sha256=proof['tensor_sha256'])
        sid=item['id'];W,H=proof['width'],proof['height'];pool=geom.candidate_pool(W,H)
        records.append(dict(source_id=sid,source_sha256=item['source_sha256'],role='train',width=W,height=H,
            RGB=RGB,RGB_pixel_sha256=proof['RGB_pixel_sha256'],original_proof=ref(original_proof),
            source_vision=vision,pool=pool,original_BASE_observed=False))
        targets[sid]=dict(role='train',reference_xywh=geom.reference_from_normalized(item['reference_original_xyxy'],W,H))
    old_eval=read(bound(reg['original_eval_inputs']));labels={r['item_id']:r for r in read(bound(reg['original_eval_labels']))}
    old_screen=read(bound(reg['old_ROI_prepared']))
    screen_rows={read(bound(r))['item_id']:read(bound(r)) for r in old_screen['entries'] if 'validation_' in r['path']}
    import json
    bases={r['item_id']:r for r in map(json.loads,Path(bound(reg['screen_BASE_predictions'])).read_text().splitlines())}
    for item in old_eval:
        if item['role']!='screen':continue
        sid=item['item_id'];row=screen_rows[sid];proof=read(A/item['proof']);W,H=item['width'],item['height']
        require(row['source_sha256']==bases[sid]['source_sha256']==labels[sid]['source_sha256']==item['source_sha256'],
                'Screen source/full-image/Base/reference binding')
        require(row['original_RGB']==ref(A/'rgb'/(item['key']+'.npy')),'Screen accepted RGB reference')
        baseline=bases[sid]['baseline_box'];pool=geom.candidate_pool(W,H,baseline_box=baseline)
        records.append(dict(source_id=sid,source_sha256=item['source_sha256'],role='screen',width=W,height=H,
            RGB=row['original_RGB'],RGB_pixel_sha256=proof['RGB_sha256'],original_proof=row['original_proof'],
            source_vision=row['input'],pool=pool,baseline_box=baseline,original_BASE_observed=True))
        targets[sid]=dict(role='screen',reference_xywh=labels[sid]['reference_xywh'])
    require(sum(r['role']=='screen' for r in records)==20 and len(records)==622,'602train+20screen first scope only')
    train={r['source_sha256'] for r in records if r['role']=='train'};screen={r['source_sha256'] for r in records if r['role']=='screen'}
    require(not train&screen and len(train)==602 and len(screen)==20,'Known file-byte training/screen isolation')
    return records,targets


def planned_cases(records):
    """SHA-only pair choice/schedule; no human target arguments."""
    train=[r for r in records if r['role']=='train'];byid={r['source_id']:r for r in train};pairs={}
    for r in train:
        allpairs=list(itertools.combinations(range(len(r['pool'])),2));require(len(allpairs)>=2,'At least2 nonidentical training pairs')
        pairs[r['source_id']]=sorted(allpairs,key=lambda p:_key(r['source_sha256'],p[0],p[1],'CROP31'))[:2]
    schedule=[];cases={};case_roles={};screen=[];pair_index=[]
    def add(r,a,b):
        cid=_key(r['source_sha256'],a,b,'CROP31_TRIPLET');spec=dict(id=cid,source_id=r['source_id'],a=a,b=b)
        if cid in cases:require(cases[cid]==spec,'One exact ordered case identity')
        else:cases[cid]=spec;case_roles[cid]=r['role']
        return cid
    for cycle in range(4):
        order=sorted(byid,key=lambda sid:_key(byid[sid]['source_sha256'],cycle,'CROP31_SOURCE_ORDER'))
        for sid in order:
            if len(schedule)==2000:break
            a,b=pairs[sid][cycle//2]
            if cycle%2:a,b=b,a
            cid=add(byid[sid],a,b);schedule.append(dict(id='T%04d'%len(schedule),source_id=sid,case_id=cid))
        if len(schedule)==2000:break
    require(len(schedule)==2000 and len({r['source_id'] for r in schedule})==602,'Exactly2000 source-balanced micro')
    for r in records:
        if r['role']!='screen':continue
        for b in range(1,len(r['pool'])):
            first=add(r,0,b);reverse=add(r,b,0);screen.extend([first,reverse])
            pair_index.append(dict(source_id=r['source_id'],candidate_index=b,first_id=first,reverse_id=reverse,same_crop=False))
        own=add(r,0,0);screen.append(own);pair_index.append(dict(source_id=r['source_id'],candidate_index=0,
            first_id=own,reverse_id=own,same_crop=True))
    require(len(screen)<=260 and len(screen)==len(set(screen)),'At most260 actual screen cases')
    return dict(cases=list(cases.values()),train_schedule=schedule,screen_ids=screen,pair_index=pair_index,
                chosen_train_pairs=pairs,case_roles=case_roles,GT_used_for_input_or_pair_choice=False)


def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only CPU child masks ownCUDA')
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2);reg=registration(root)
    require(bound(reg['preparation_code'])==Path(__file__).resolve(),'Exact first crop prepare')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),'Inside Goal window')
    cfg=read(bound(reg['model_config']));processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    out=root/'crop_inputs_31';out.mkdir(exist_ok=False);started=time.monotonic()
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'crop_CPU_registration_31.json'),
        original_decode=0,old_source_processor_repeated=0,eval_reference_not_in_prompt=True))
    completed=[];encoded_crops=[]
    try:
        records,targets=source_inventory(root,reg);plan=planned_cases(records)
        save(out/'label_free_case_plan.json',plan);save(out/'source_catalog.json',dict(sources=records,global_source_independence='UNKNOWN'))
        bysource={}
        for case in plan['cases']:bysource.setdefault(case['source_id'],[]).append(case)
        entries={};classes=None;profiles=[];CPU_targets=[];new_crop_count=0
        for source in records:
            require(time.monotonic()-started<1800 and dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),
                    'Registered CPU budget/overall work window')
            sid=source['source_id'];source_key=_key(sid);directory=out/source_key;directory.mkdir()
            rgb=np.load(bound(source['RGB']),allow_pickle=False)
            require(rgb.dtype==np.uint8 and rgb.shape==(source['height'],source['width'],3) and
                hashlib.sha256(rgb.tobytes()).hexdigest()==source['RGB_pixel_sha256'],'Exact accepted original native RGB, no new decode')
            raw=torch.load(bound(source['source_vision']),map_location='cpu',weights_only=True)
            source_vision={key:raw[key] for key in ('pixel_values','image_grid_thw')};del raw
            needed=sorted({case[k] for case in bysource[sid] for k in ('a','b')});crops={};crop_refs={}
            for index in needed:
                box=source['pool'][index];rendered,render_meta=image.render_crop(rgb,box)
                image.independent_render_check(rgb,box,rendered,render_meta)
                vision=dict(processor.image_processor(images=[Image.fromarray(rendered)],return_tensors='pt'))
                require(set(vision)=={'pixel_values','image_grid_thw'},'First crop image processor two-key output')
                # First independent QA of each NEW crop, not repetition of old source coding.
                check=dict(processor.image_processor(images=[Image.fromarray(rendered.copy())],return_tensors='pt'))
                require(all(torch.equal(vision[k],check[k]) for k in vision),'First new physicalcrop RGB/processor exact independent QA')
                p=directory/('crop_%02d.pt'%index)
                with p.open('xb') as f:torch.save(vision,f)
                require(signature(vision)==signature(torch.load(p,map_location='cpu',weights_only=True)),'New crop exact save/reload')
                proof=directory/('crop_%02d.proof.json'%index)
                save(proof,dict(source_id=sid,source_sha256=source['source_sha256'],RGB=source['RGB'],original_proof=source['original_proof'],
                    box=box,render=render_meta,tensor=ref(p),signature=signature(vision),first_independent_QA=True,old_source_processor_repeated=False))
                append_event(out/'crop_progress.jsonl',event='FIRST_NEW_CROP_QA_ACCEPTED',proof=ref(proof));encoded_crops.append(ref(proof))
                crops[index]=vision;crop_refs[index]=ref(p);new_crop_count+=1
            human=targets[sid]['reference_xywh'];ious=[geom.crop_iou(b,human) for b in source['pool']]
            CPU_targets.append(dict(source_id=sid,source_sha256=source['source_sha256'],role=source['role'],
                original_reference_xywh=human,candidate_ious=ious,baseline_index=0,reference_modified=False))
            for case in bysource[sid]:
                a,b=case['a'],case['b'];views=[source_vision,crops[a],crops[b]];pixels=[v['pixel_values'] for v in views]
                grid=torch.cat([v['image_grid_thw'] for v in views]);packed=image.pack_image_pixels(pixels,grid)
                image.independent_pixel_check(pixels,grid,packed);tokens,text=image.build_text_input(processor,grid)
                image.independent_text_check(processor,packed,tokens,text)
                if classes is None:classes=text['class_token_ids']
                require(text['class_token_ids']==classes,'One actual assistant-context0/1/2 class identity')
                tp=directory/(case['id']+'.tokens.pt')
                with tp.open('xb') as f:torch.save(tokens,f)
                require(signature(tokens)==signature(torch.load(tp,map_location='cpu',weights_only=True)),'Actual new triplet prefix save/reload')
                values=dict(**tokens,**packed);rp=directory/(case['id']+'.json')
                row=dict(id=case['id'],source_id=sid,source_sha256=source['source_sha256'],role=source['role'],
                    boxes=[source['pool'][a],source['pool'][b]],candidate_indices=[a,b],
                    vision_inputs=[source['source_vision'],crop_refs[a],crop_refs[b]],tokens=ref(tp),
                    input_signature=signature(values),image_grid_thw=grid.tolist(),class_token_ids=classes,text_evidence=text,
                    original_RGB=source['RGB'],original_proof=source['original_proof'],reference_or_target_in_prompt=False)
                save(rp,row);entry=dict(id=case['id'],source_id=sid,input=ref(rp));entries[case['id']]=entry;completed.append(entry)
                profiles.append(dict(id=case['id'],source_id=sid,sequence_tokens=int(tokens['input_ids'].shape[-1]),grid=grid.tolist()))
                del values,packed,tokens
            del rgb,source_vision,crops
        schedule=[];target_map={r['source_id']:r for r in CPU_targets}
        for step in plan['train_schedule']:
            case=next(c for c in bysource[step['source_id']] if c['id']==step['case_id']);ious=target_map[step['source_id']]['candidate_ious']
            target=geom.preference_label(ious[case['a']],ious[case['b']]);onehot=[float(i==target) for i in range(3)]
            schedule.append(dict(id=step['id'],source_id=step['source_id'],input=entries[step['case_id']]['input'],target=onehot))
        save(out/'CPU_only_evaluation_targets.json',dict(status='HUMAN_TARGETS_FOR_CPU_COMPARISON_ONLY',sources=CPU_targets,
             pair_index=plan['pair_index'],single_editor=True,historical_exposure=True,no_new_blind_sources=True))
        prepared=out/'prepared.json';save(prepared,dict(source_catalog=ref(out/'source_catalog.json'),train_schedule=schedule,
            screen_inputs=[entries[cid] for cid in plan['screen_ids']],class_token_ids=classes,profiles=profiles,
            case_plan=ref(out/'label_free_case_plan.json'),train_sources=602,screen_sources=20,
            new_crop_count=new_crop_count,new_decode=0,old_source_processor_repeated=0,confirm_or_production_admitted=False))
        require(len(schedule)==2000 and all(len(s['target'])==3 and sum(s['target'])==1 for s in schedule),
                'Exactly2000 actual registered onehot supervised micro')
        save(out/'input_acceptance.json',dict(status=GATE,registration=ref(root/'crop_CPU_registration_31.json'),prepared=ref(prepared),
            train_micro=2000,screen_inputs=len(plan['screen_ids']),unique_inputs=len(entries),new_crop_count=new_crop_count,
            first_independent_pixels_text_native_QA=True,old_source_processor_repeated=0,new_original_decode=0,
            elapsed_seconds=time.monotonic()-started,total_new_patch_bytes=sum(p.stat().st_size for p in out.glob('*/crop_*.pt'))))
        require(not torch.cuda.is_initialized(),'CPU preparation may not initialize CUDA')
        print('CROP31_ALL_FIRST_CPU_QA',len(entries),new_crop_count,flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),completed_inputs=completed,
            completed_crop_proofs=encoded_crops,preserve_all_success=True,no_automatic_retry=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);prepare(parser.parse_args().root)
