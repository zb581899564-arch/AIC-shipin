"""Explicit remaining19 recovery; original20 remains incomplete.

The first actual BASE generation was not persisted before a PEFT flag guard
failed. Its source stays UNAVAILABLE and is never called again. All remaining
inputs adopt the already successful20-source QA; no processor is repeated.
"""

import argparse

import hashlib

import os

from pathlib import Path

import sys

import time

import traceback

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'roi_code_06'),
              str(Path(__file__).resolve().parents[1]/'roi_relative_code_09')]

from roi_runtime import WORK,A,PYTHON,require,read,save,ref,bound,sha,utc,io_module,registration,check_pixels

from roi_pool import candidate_features

import crop_geometry as geom

from roi_ridge import ARMS,predict,choose

def config(root):
    registration(root)
    r=read(root/'roi_confirm_remaining19_registration_12.json')
    require(r['recovery_status']=='EXACT_REMAINING19_UNRECORDED_FIRST_CALL_EXCLUDED', 'Explicit remaining-only recovery')
    require(r['new_BASE_generations']==19 and r['new_vision_readouts']==19 and r['new_head_fits']==0,
            'Exact new confirmation budget')
    for n,h in r['new_code'].items():require(sha(root/'roi_confirm_recovery_code_12'/n)==h,'Frozen confirmation code changed')
    relative=read(bound(r['relative_model_registration']))
    for n,h in relative['new_code'].items():
        require(sha(root/'roi_relative_code_09'/n)==h,'Actual frozen relative predictor code changed')
    require(Path(sys.modules['roi_ridge'].__file__).resolve()==root/'roi_relative_code_09/roi_ridge.py',
            'Relative model implementation was shadowed')
    for reference in r['frozen_predictor'].values():bound(reference)
    admission=read(bound(r['admission']))
    require(admission['status']=='ADMIT_FIRST_FROZEN_RELATIVE_ROI_CONFIRM20_NOT_PRODUCTION','Actual prospective screen decision')
    return r

def infer(root):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Actual GPU child retains nonempty CUDA')
    reg=config(root);io=io_module(root);runtime=io.runtime_only()
    sys.path.insert(0,str(io.RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from contracts import parse_focus_norm
    verify_live_gpu_reservation()
    import numpy as np
    import torch
    torch.set_num_threads(2)
    gate=read(root/'roi_confirm_remaining19_inputs_12/input_acceptance.json')
    require(gate['status']=='PASS_ADOPTED_REMAINING19_FROM_ORIGINAL20_INPUT_QA','All actual first inputs before GPU')
    entries=read(bound(gate['prepared']))['entries']
    require(len(entries)==19 and entries==reg['remaining_input_refs'], 'Never re-run the unrecorded first generation')
    out=root/'roi_confirm_remaining19_GPU_12';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(pid=os.getpid(),utc=utc(),input_acceptance=ref(root/'roi_confirm_remaining19_inputs_12/input_acceptance.json')))
    cfg=io.read(io.CONFIG);model,processor,identity=runtime.b_engine.load_model(cfg);io.verify_model(model,identity)
    require(sum(p.numel() for p in model.parameters())==8782459120,'Actual complete base/TIME model inventory')
    native=model.get_base_model();core=native.model;success_base=[];success_vision=[]
    attempts=out/'attempts.jsonl';attempts.touch(exist_ok=False)
    def event(**value):
        with attempts.open('a') as f:f.write(__import__('json').dumps(dict(utc=utc(),**value))+'\n');f.flush();os.fsync(f.fileno())
    try:
        for i,reference in enumerate(entries):
            row=read(bound(reference));base=torch.load(bound(row['original_BASE_input']),map_location='cpu',weights_only=True)
            require(runtime.tensor_signature(base)==row['original_BASE_signature'],'Actual original BASE input changed')
            gpu={k:v.to('cuda') for k,v in base.items()};prefix=int(base['input_ids'].shape[1]);t0=time.monotonic()
            event(event='BEGIN_FIRST_ORIGINAL_BASE_CENTER',item_id=row['item_id'])
            from base_role import frozen_original_base
            with frozen_original_base(model),torch.inference_mode():
                generated=model.generate(**gpu,max_new_tokens=128,do_sample=False,num_beams=1,use_cache=True)
                torch.cuda.synchronize()
                ids=generated[0,prefix:].detach().cpu().tolist()
                raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                rp=out/('C%02d.base_raw.json'%i)
                save(rp,dict(item_id=row['item_id'],source=reference,raw=raw,output_token_ids=ids,prefix_tokens=prefix,
                     elapsed_seconds=time.monotonic()-t0,first_BASE_generation=True,actual_TIME_disabled_during_BASE=True,
                     raw_persisted_before_adapter_context_exit=True,
                     generation_config='Original128 greedy no-beam BASE behavior; unchanged prompt',labels_read=False))
                success_base.append(ref(rp))
            io.enabled_layers(model)
            center=parse_focus_norm(raw,row['width'],row['height'])
            require(center is not None and len(ids)>0,'Original strict center parser failed; preserve raw, no fallback')
            box=geom.place_crop(row['width'],row['height'],center)
            save(out/('C%02d.base.json'%i),dict(item_id=row['item_id'],source_sha256=row['source_sha256'],source=reference,
                 original_BASE_raw=ref(rp),center=center,original_BASE_box=box,candidate_boxes=geom.candidate_pool(row['width'],row['height'],box)))
            event(event='ACCEPTED_FIRST_ORIGINAL_BASE_CENTER',item_id=row['item_id'])
            del gpu,base,generated
        for i,reference in enumerate(entries):
            row=read(bound(reference));baseline=read(out/('C%02d.base.json'%i))
            vision=torch.load(bound(row['new_vision']),map_location='cpu',weights_only=True);mh,mw=check_pixels(vision)
            gpu={k:v.to('cuda') for k,v in vision.items()};t0=time.monotonic();event(event='BEGIN_FIRST_CONFIRM_VISION',item_id=row['item_id'])
            with torch.inference_mode():embeds,deep=core.get_image_features(**gpu)
            torch.cuda.synchronize()
            require(isinstance(embeds,tuple) and len(embeds)==1 and embeds[0].shape==(mh*mw,4096)
                    and torch.isfinite(embeds[0]).all(),'Actual confirm merged-token mapping')
            tokens=embeds[0].detach().cpu().contiguous()
            features=candidate_features(tokens.float().numpy().reshape(mh,mw,4096),baseline['candidate_boxes'],row['width'],row['height'])
            tp=out/('C%02d.tokens.pt'%i);fp=out/('C%02d.features.npy'%i);torch.save(tokens,tp)
            with fp.open('xb') as f:np.save(f,features,allow_pickle=False)
            result=dict(item_id=row['item_id'],source_sha256=row['source_sha256'],source=reference,
                 original_BASE=ref(out/('C%02d.base.json'%i)),tokens=ref(tp),features=ref(fp),merged_grid=[mh,mw],
                 elapsed_seconds=time.monotonic()-t0,labels_read=False,first_new_vision_readout=True)
            rp=out/('C%02d.result.json'%i);save(rp,result);success_vision.append(ref(rp))
            event(event='ACCEPTED_FIRST_CONFIRM_VISION',item_id=row['item_id'])
            del gpu,vision,embeds,deep,tokens,features
        require(len(success_base)==len(success_vision)==19 and io.enabled_layers(model)==[False]*144
                and runtime.b_engine.frozen_identity(model,cfg)==identity['base']
                and runtime.b_engine.adapter_identity(model,cfg)==identity['adapter'],'Complete actual frozen confirmation')
        save(out/'completion.json',dict(status='COMPLETE_REMAINING19_BASE_AND_VISION_ORIGINAL20_INCOMPLETE',
             base_calls=success_base,entries=success_vision,first_new_BASE_generations=19,first_new_vision_readouts=19,
             new_optimizer_updates=0,labels_read=False,model_identity=identity))
    except BaseException as e:
        save(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),successful_BASE=success_base,
             successful_vision=success_vision,preserve_all_success=True,do_not_repeat_success=True,failure_not_empty=True));raise

def output_qa(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent output check CPU only')
    reg=config(root);io=io_module(root);io.runtime_only()
    from contracts import parse_focus_norm
    from transformers import AutoTokenizer
    import torch
    import numpy as np
    tokenizer=AutoTokenizer.from_pretrained(io.read(io.CONFIG)['model_dir'],local_files_only=True)
    out=root/'roi_confirm_remaining19_GPU_12';done=read(out/'completion.json');seen=set()
    for reference in done['entries']:
        result=read(bound(reference));row=read(bound(result['source']));baseline=read(bound(result['original_BASE']));raw=read(bound(baseline['original_BASE_raw']))
        require(result['item_id']==row['item_id']==baseline['item_id']==raw['item_id']
                and baseline['source']==raw['source']==result['source']
                and 0<len(raw['output_token_ids'])<=128
                and raw['prefix_tokens']==row['original_BASE_signature']['input_ids']['shape'][1],
                'Independent raw generation/source/prefix binding')
        text=tokenizer.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        center=parse_focus_norm(text,row['width'],row['height'])
        require(text==raw['raw'] and center==baseline['center'] and geom.place_crop(row['width'],row['height'],center)==baseline['original_BASE_box'],
                'Independent original raw/parser/BASE geometry mismatch')
        boxes=geom.candidate_pool(row['width'],row['height'],baseline['original_BASE_box'])
        require(boxes==baseline['candidate_boxes'] and result['source_sha256']==row['source_sha256'] and row['item_id'] not in seen,
                'Independent fixed candidate/source identity')
        vision=torch.load(bound(row['new_vision']),map_location='cpu',weights_only=True)
        actual_grid=check_pixels(vision);mh,mw=result['merged_grid']
        require((mh,mw)==actual_grid,'Independent input-grid/output-grid source binding')
        tokens=torch.load(bound(result['tokens']),map_location='cpu',weights_only=True)
        require(tokens.shape==(mh*mw,4096) and torch.isfinite(tokens).all(),'Actual bound output token shape/finite')
        actual=np.load(bound(result['features']),allow_pickle=False)
        require(actual.dtype==np.float32,'Exact saved float32 ROI descriptor')
        expected=candidate_features(tokens.float().numpy().reshape(mh,mw,4096),boxes,row['width'],row['height'])
        require(np.array_equal(actual,expected),'Independent raw merged-token ROI pooling differs')
        seen.add(row['item_id'])
    require(len(seen)==19 and not torch.cuda.is_initialized(),'Complete first independent confirm outputs')
    save(root/'roi_confirm_remaining19_output_acceptance_12.json',dict(status='PASS_FIRST_REMAINING19_BASE_AND_ROI_QA_ORIGINAL20_INCOMPLETE',
         completion=ref(out/'completion.json'),actual_sources=19,new_model_calls=0,original_GT_read=False))

def evaluate(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only CPU reference comparison')
    reg=config(root);qa=read(root/'roi_confirm_remaining19_output_acceptance_12.json')
    require(qa['status']=='PASS_FIRST_REMAINING19_BASE_AND_ROI_QA_ORIGINAL20_INCOMPLETE','Actual complete confirm QA first')
    import numpy as np
    labels={x['item_id']:x for x in read(bound(reg['original_labels']))}
    with np.load(bound(reg['frozen_predictor']['projection']),allow_pickle=False) as f:state={k:f[k] for k in f.files}
    beta={arm:np.load(bound(reg['frozen_predictor'][arm]),allow_pickle=False) for arm in ARMS}
    output={arm:[] for arm in ARMS};done=read(bound(qa['completion']))
    for reference in done['entries']:
        result=read(bound(reference));row=read(bound(result['source']));baseline=read(bound(result['original_BASE']));human=labels[row['item_id']]
        require(human['role']=='confirm' and human['source_sha256']==row['source_sha256'],'Original confirm human/source scope')
        truth=human['reference_xywh'];geom.validate_reference(truth,row['width'],row['height'])
        require(geom.reference_from_normalized(human['original_normalized_xyxy'],row['width'],row['height'])==truth,'Unmodified float human reference')
        features=np.load(bound(result['features']),allow_pickle=False);boxes=baseline['candidate_boxes'];ious=[geom.crop_iou(b,truth) for b in boxes]
        for arm in ARMS:
            score=predict(state,beta[arm],features,arm);j=choose(score)
            output[arm].append(dict(item_id=row['item_id'],source_sha256=row['source_sha256'],candidate_boxes=boxes,
                 predicted_relative_IoU=score.tolist(),chosen_index=j,baseline_iou=ious[0],selected_iou=ious[j],
                 delta_iou=ious[j]-ious[0],real_box_changed=(boxes[j]!=boxes[0]),original_human_reference_xywh=truth))
    summary={}
    for arm,rows in output.items():
        summary[arm]=dict(mean_baseline_iou=float(np.mean([x['baseline_iou'] for x in rows])),
             mean_selected_iou=float(np.mean([x['selected_iou'] for x in rows])),mean_delta_iou=float(np.mean([x['delta_iou'] for x in rows])),
             changed_sources=sum(x['real_box_changed'] for x in rows),improved_sources=sum(x['delta_iou']>0 for x in rows),
             degraded_sources=sum(x['delta_iou']<0 for x in rows),worst_source_delta=min(x['delta_iou'] for x in rows))
    save(root/'roi_confirm_remaining19_result_12.json',dict(status='COMPLETE_REMAINING19_FROZEN_RESEARCH_ORIGINAL20_INCOMPLETE',
         summary=summary,sources=output,original_target_sources=20,actual_available_sources=19,
         unavailable_original_source=reg['unavailable_original_source'],original20_complete=False,historical_exposure=True,new_blind_sources=0,original_GT_changed=False,
         new_fitting=False,automatic_426=False,production_admitted=False,scope='File-level static native16 research; video/joint quality UNKNOWN'))

def inherit_inputs(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Adoption-only CPU process')
    reg=config(root)
    failure=read(bound(reg['original_GPU_failure']))
    require('All 144 original TIME LoRA' in failure['error'] and not failure['successful_BASE']
            and not failure['successful_vision'],'Exact prior first-call failure state')
    terminal=read(bound(reg['original_GPU_resource']))
    import json
    matches=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
             if line.strip() and json.loads(line).get('name')==terminal['name']]
    require(terminal['status']=='failed' and terminal['exit_code']==1 and matches==[terminal],
            'Natural failed prior GPU terminal/unique ledger')
    attempts=[json.loads(line) for line in bound(reg['original_attempts']).read_text().splitlines() if line.strip()]
    require(len(attempts)==1 and attempts[0]['event']=='BEGIN_FIRST_ORIGINAL_BASE_CENTER'
            and attempts[0]['item_id']==reg['unavailable_original_source']['item_id'],
            'Exact single unrecorded completed call; no other source was invoked')
    oldgate=read(bound(reg['original_input_acceptance']))
    require(oldgate['status']=='PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS','Actual old20 input QA')
    oldprepared=read(bound(oldgate['prepared']));entries=oldprepared['entries']
    require(len(entries)==20 and entries[0]==reg['unavailable_original_source']['input']
            and entries[1:]==reg['remaining_input_refs'],'Exact19 remaining calls, no unavailable call retry')
    for reference in entries[1:]:
        row=read(bound(reference));bound(row['original_BASE_input']);bound(row['new_vision'])
        require(row['item_id']!=reg['unavailable_original_source']['item_id'],'Unrecorded completed call must remain excluded')
    out=root/'roi_confirm_remaining19_inputs_12';out.mkdir(exist_ok=False)
    save(out/'prepared.json',dict(entries=entries[1:],original_prepared=oldgate['prepared'],original_target_count=20,
         exact_remaining_sources=19,unavailable_original_source=reg['unavailable_original_source'],         new_processor_calls=0,old_input_QA_repeated=False))
    save(out/'input_acceptance.json',dict(status='PASS_ADOPTED_REMAINING19_FROM_ORIGINAL20_INPUT_QA',
         prepared=ref(out/'prepared.json'),original_input_QA=reg['original_input_acceptance'],actual_sources=19,
         original20_complete=False,new_processor_calls=0,old_input_QA_repeated=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['inherit_inputs','infer','output_qa','evaluate'])
    p.add_argument('--root',type=Path,required=True);a=p.parse_args();globals()[a.mode](a.root)
