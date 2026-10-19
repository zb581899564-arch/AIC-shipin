"""Conditional CPU68: adopt successful inputs; first-encode missing crops only.

Registration utility_star_CPU_registration_68.json/schema
UTILITY_CONNECTED_STAR_CPU_V68 binds preparation_code,math_code,input_code,
image_code,geometry_code,policy_code,helper_code,model_config,
old_catalog,original_targets,gain_prepared,gain_input_acceptance,
old55_prepared,old55_input_acceptance,old55_STOP,old55_completion,
old55_progress,old55_adapter_weights,old55_value_weights,protocol, plus
deadline_utc/max_seconds/max_new_bytes and original decode/source processor0.
The image/geometry refs bind31, policy binds33, helper binds17, catalog/targets
bind31 and gain refs bind44; these numbers are not registration key suffixes.
No actions on import; CLI --root. No GPU, decoder, training or old QA rerun.
"""
from collections import OrderedDict
import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

support=Path(__file__).resolve().parents[1]/'pair_code_17'
if support.is_dir():sys.path.insert(0,str(support))
from pair_common import read,ref,bound,require,signature,utc,save,append_event
import utility_star_math_v68 as math68


def module(reference,name):
    p=bound(reference);sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location(name,p)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result);return result


class Writer:
    def __init__(self,out,maximum):self.out,self.maximum,self.bytes=out,maximum,0
    def data(self,path,data):
        require(self.bytes+len(data)<=self.maximum,'Actual new bytes exceed explicit CPU68 budget')
        require(shutil.disk_usage(self.out).free>=len(data),'Current disk cannot hold actual new artifact')
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        self.bytes+=len(data);return ref(path)
    def json(self,path,value):return self.data(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
    def tensor(self,path,value,torch):
        stream=io.BytesIO();torch.save(value,stream);r=self.data(path,stream.getvalue())
        actual=torch.load(bound(r),map_location='cpu',weights_only=True)
        require(signature(actual)==signature(value),'First new tensor bit-exact reload');return r
    def event(self,path,**row):
        data=(json.dumps(dict(utc=utc(),**row),ensure_ascii=False,allow_nan=False)+'\n').encode()
        require(self.bytes+len(data)<=self.maximum and shutil.disk_usage(self.out).free>=len(data),'Actual new journal bytes exceed capacity/budget')
        with Path(path).open('ab') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        self.bytes+=len(data)


def validate_registration(reg,completion,stop,gate55,gain_gate):
    require(reg['schema']=='UTILITY_CONNECTED_STAR_CPU_V68','Separate connected-star registration')
    require(completion['status']=='COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY'
        and completion['completed_updates']==500 and completion['successful_micro']==2000
        and completion['progress']==reg['old55_progress'] and completion['adapter_weights']==reg['old55_adapter_weights']
        and completion['value_weights']==reg['old55_value_weights'],'Immutable successful55 final500 engineering state')
    require(stop['status'].startswith('STOP_') and stop['adapter_weights']==reg['old55_adapter_weights']
        and stop['value_weights']==reg['old55_value_weights'],'Original55 quality STOP remains unchanged')
    require(gate55['status']=='PASS_UTILITY55_TRAIN_TARGETS_AND_ADOPTED_INPUTS_CPU'
        and gate55['prepared']==reg['old55_prepared'] and gain_gate['prepared']==reg['gain_prepared']
        and gain_gate['status']=='PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA','Adopt actual55/44 input acceptance')
    require(reg['new_original_decodes']==reg['old_source_processor_repeated']==0
        and type(reg['max_new_bytes']) is int and reg['max_new_bytes']>0,'No old decode/processor and explicit measured byte budget')


class StarInputs:
    """Explicit6020 train whitelist; never opens human targets or screen files."""
    def __init__(self,root):
        self.root=Path(root);rp=self.root/'utility_star_CPU_registration_68.json';self.reg=read(rp)
        require(bound(self.reg['input_code'])==Path(__file__).resolve(),'Exact new68 input reader')
        gate=read(self.root/'utility_star_inputs_68/input_acceptance.json')
        require(gate['status']==math68.GATE and gate['registration']==ref(rp),'Complete first68 input gate')
        self.prepared=read(bound(gate['prepared']));require(gate['prepared']==ref(self.root/'utility_star_inputs_68/prepared.json')
            and self.prepared['schema']==math68.SCHEMA,'Own registered prepared manifest')
        entries=self.prepared['train_inputs'];require(len(entries)==6020 and len({e['id'] for e in entries})==6020,'Exact6020 ordered whitelist')
        self.allowed={(e['input']['path'],e['input']['sha256']):e for e in entries}
        require(len(self.allowed)==6020,'Unique immutable ordered requests')
        self.image=module(self.reg['image_code'],'_utility68_reader_image31');self.source=None;self.cache={}
    def get(self,reference):
        import torch
        entry=self.allowed.get((reference['path'],reference['sha256']));require(entry is not None,'Input outside6020 star whitelist')
        q=read(bound(reference));require(all(q[k]==entry[k] for k in ('id','source_id','source_sha256'))
            and q['role']=='train' and q['reference_or_target_in_prompt'] is False
            and not any(k in q for k in ('target','labels','candidate_ious','original_reference_xywh')),'Label-free registered train owner')
        if self.source!=q['source_id']:self.cache.clear();self.source=q['source_id']
        views=[]
        for r in q['vision_inputs']:
            k=(r['path'],r['sha256'])
            if k not in self.cache:
                raw=torch.load(bound(r),map_location='cpu',weights_only=True)
                self.cache[k]={n:raw[n] for n in ('pixel_values','image_grid_thw')}
            views.append(self.cache[k])
        grid=torch.cat([v['image_grid_thw'] for v in views]);packed=self.image.pack_image_pixels([v['pixel_values'] for v in views],grid)
        tokens=torch.load(bound(q['tokens']),map_location='cpu',weights_only=True);values=dict(**tokens,**packed)
        require(set(values)=={'input_ids','attention_mask','pixel_values','image_grid_thw'}
            and signature(values)==q['input_signature'] and grid.tolist()==q['image_grid_thw']
            and q['class_token_ids']==self.prepared['class_token_ids'],'Consumed exact accepted four-tensor signature')
        return values,q


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU68 child masks CUDA')
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    require(not torch.cuda.is_initialized(),'CPU68 cannot initialize CUDA');torch.set_num_threads(2)
    root=Path(root);rp=root/'utility_star_CPU_registration_68.json';reg=read(rp)
    require(bound(reg['preparation_code'])==Path(__file__).resolve() and bound(reg['input_code'])==Path(__file__).resolve()
        and bound(reg['math_code'])==Path(math68.__file__).resolve(),'Exact frozen68 code bytes')
    validate_registration(reg,read(bound(reg['old55_completion'])),read(bound(reg['old55_STOP'])),
        read(bound(reg['old55_input_acceptance'])),read(bound(reg['gain_input_acceptance'])))
    for k in ('helper_code','old55_progress','old55_adapter_weights','old55_value_weights','protocol'):bound(reg[k])
    old55=read(bound(reg['old55_prepared']));require(old55['train_target_RMS']==math68.TARGET_RMS,'Original frozen target RMS')
    catalog=read(bound(reg['old_catalog']));gain=read(bound(reg['gain_prepared']))
    requests={e['id']:read(bound(e['input'])) for e in gain['train_inputs']}
    plan=math68.build_plan(catalog,gain,requests)
    require((plan['adopted_inputs'],plan['first_new_combinations'],plan['new_crop_count'])==(856,5164,1549),'Actual67 support counts must still match frozen evidence')
    geometry=module(reg['geometry_code'],'_utility68_geometry31');image=module(reg['image_code'],'_utility68_image31')
    policy=module(reg['policy_code'],'_utility68_policy33')
    for s in plan['sources']:require(s['pool']==geometry.candidate_pool(s['width'],s['height']),'Original six-pool unchanged')
    out=root/'utility_star_inputs_68';out.mkdir(exist_ok=False);writer=Writer(out,reg['max_new_bytes']);started=time.monotonic();completed=[];crop_proofs=[]
    def budget():
        require(time.monotonic()-started<reg['max_seconds'] and dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),'Registered CPU68/Goal budget')
    writer.json(out/'claim.json',dict(utc=utc(),registration=ref(rp),old55_quality='STOP',GPU_admitted=False))
    try:
        writer.json(out/'label_free_plan.json',plan)
        train_catalog={k:copy.deepcopy(v) for k,v in catalog.items() if k!='sources'}
        train_catalog['sources']=plan['sources'];catalog_ref=writer.json(out/'source_catalog.json',train_catalog)
        cfg=read(bound(reg['model_config']));processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
        input_refs={c['id']:c['input'] for c in plan['cases'] if c['adopted_input']}
        for s in plan['sources']:
            budget();sid=s['source_id'];directory=out/math68.key(sid);directory.mkdir();refs=copy.deepcopy(plan['crop_refs'][sid]);views={}
            rgb=np.load(bound(s['RGB']),allow_pickle=False)
            require(rgb.dtype==np.uint8 and rgb.shape==(s['height'],s['width'],3)
                and hashlib.sha256(rgb.tobytes()).hexdigest()==s['RGB_pixel_sha256'],'Adopt exact original602 RGB, no decode')
            for i,box in enumerate(s['pool']):
                budget()
                if i in refs:continue
                writer.event(out/'crop_progress.jsonl',event='BEGIN_FIRST_NEW_CROP',source_id=sid,candidate_index=i)
                rendered,meta=image.render_crop(rgb,box);image.independent_render_check(rgb,box,rendered,meta)
                vision=dict(processor.image_processor(images=[Image.fromarray(rendered)],return_tensors='pt'))
                require(set(vision)=={'pixel_values','image_grid_thw'},'Only actual image patch/grid output')
                tensor=writer.tensor(directory/('crop_%02d.pt'%i),vision,torch)
                writer.event(out/'crop_progress.jsonl',event='FIRST_NEW_CROP_RAW_PERSISTED',source_id=sid,candidate_index=i,tensor=tensor)
                check=dict(processor.image_processor(images=[Image.fromarray(rendered.copy())],return_tensors='pt'))
                require(signature(check)==signature(vision),'Independent FIRST new crop processor exact result')
                proof=writer.json(directory/('crop_%02d.proof.json'%i),dict(source_id=sid,source_sha256=s['source_sha256'],candidate_index=i,
                    box=box,RGB=s['RGB'],original_proof=s['original_proof'],render=meta,tensor=tensor,signature=signature(vision),first_independent_QA=True))
                crop_proofs.append(proof);refs[i]=tensor
                writer.event(out/'crop_progress.jsonl',event='FIRST_NEW_CROP_QA_ACCEPTED',proof=proof)
            del rgb
            source_raw=torch.load(bound(s['source_vision']),map_location='cpu',weights_only=True)
            source_vision={k:source_raw[k] for k in ('pixel_values','image_grid_thw')};del source_raw
            template=requests[plan['templates'][sid]['id']]
            template_tokens=torch.load(bound(template['tokens']),map_location='cpu',weights_only=True)
            for c in [c for c in plan['cases'] if c['source_id']==sid and not c['adopted_input']]:
                budget();a,b=c['a'],c['b']
                for i in (a,b):
                    if i not in views:views[i]=torch.load(bound(refs[i]),map_location='cpu',weights_only=True)
                three=[source_vision,views[a],views[b]];pixels=[v['pixel_values'] for v in three];grid=torch.cat([v['image_grid_thw'] for v in three])
                packed=image.pack_image_pixels(pixels,grid);pixel_check=image.independent_pixel_check(pixels,grid,packed)
                if grid.tolist()==template['image_grid_thw']:
                    tokens=template_tokens;text=copy.deepcopy(template['text_evidence']);token_ref=template['tokens'];reused=True
                else:
                    tokens,text=image.build_text_input(processor,grid);token_ref=writer.tensor(directory/(c['id']+'.tokens.pt'),tokens,torch);reused=False
                text_check=image.independent_text_check(processor,packed,tokens,text)
                require(text['class_token_ids']==plan['class_token_ids'],'Actual digit identities unchanged')
                q=dict(id=c['id'],source_id=sid,source_sha256=s['source_sha256'],role='train',boxes=[s['pool'][a],s['pool'][b]],
                    candidate_indices=[a,b],vision_inputs=[s['source_vision'],refs[a],refs[b]],tokens=token_ref,
                    input_signature=signature(dict(**tokens,**packed)),image_grid_thw=grid.tolist(),class_token_ids=plan['class_token_ids'],
                    text_evidence=text,original_RGB=s['RGB'],original_proof=s['original_proof'],reference_or_target_in_prompt=False,
                    star68_first_new_combination=True,adopted_original_tokens=reused)
                qr=writer.json(directory/(c['id']+'.json'),q)
                proof=writer.json(directory/(c['id']+'.first_QA.json'),dict(request=qr,source_id=sid,source_sha256=s['source_sha256'],
                    pixel_check=pixel_check,text_check=text_check,new_crop_encoding_repeated=False,old_source_processor_repeated=False))
                input_refs[c['id']]=qr;completed.append(proof)
                writer.event(out/'input_progress.jsonl',event='FIRST_NEW_STAR_INPUT_QA_ACCEPTED',proof=proof)
            del source_vision,views,template_tokens
        require(len(crop_proofs)==1549 and len(completed)==5164 and len(input_refs)==6020,'All actual new items complete, none silently skipped')
        targets=read(bound(reg['original_targets']))
        schedule=math68.compile_schedule(plan,targets['sources'],input_refs,policy.geometry_features)
        entries=[dict(id=c['id'],source_id=c['source_id'],source_sha256=c['source_sha256'],input=input_refs[c['id']]) for c in plan['cases']]
        prepared=dict(schema=math68.SCHEMA,train_schedule=schedule,train_target_RMS=math68.TARGET_RMS,
            class_token_ids=plan['class_token_ids'],train_inputs=entries,pair_index=plan['pair_index'],source_catalog=catalog_ref,
            train_sources=602,train_unordered_pairs=3010,train_micro=3200,screen_inputs=copy.deepcopy(old55['screen_inputs']),
            screen_prepared=old55['screen_prepared'],screen_input_acceptance=old55['screen_input_acceptance'],
            old55_progress=reg['old55_progress'],old55_adapter_weights=reg['old55_adapter_weights'],old55_value_weights=reg['old55_value_weights'],
            old55_completion=reg['old55_completion'],old55_STOP=reg['old55_STOP'],recipe=math68.RECIPE,
            original55_quality='STOP',production_admitted=False)
        _,schedule_sha,proof=math68.validate_schedule(prepared);prepared['schedule_sha256']=schedule_sha
        budget();require(not torch.cuda.is_initialized(),'No CPU preparation CUDA initialization')
        pr=writer.json(out/'prepared.json',prepared)
        writer.json(out/'input_acceptance.json',dict(status=math68.GATE,registration=ref(rp),prepared=pr,
            schedule_sha256=schedule_sha,proof=proof,adopted_inputs=856,first_new_combinations=5164,new_crop_count=1549,
            first_new_crop_QA=crop_proofs,first_new_input_QA=completed,new_original_decodes=0,old_source_processor_repeated=0,
            new_bytes_before_acceptance=writer.bytes,elapsed_seconds=time.monotonic()-started,GPU_admitted=False,old55_quality='STOP'))
        print('UTILITY68_CONNECTED_STAR_CPU_COMPLETE',proof,flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(utc=utc(),error=repr(error),traceback=traceback.format_exc(),
            completed_first_QA=completed,completed_crop_QA=crop_proofs,preserve_all_success=True,automatic_retry=False));raise


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
