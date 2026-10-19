"""Independent CPU crop BASE/pilot4 or TRAINED/final500 engineering QA only.

No model/processor/evaluation-reference loading. TRAINED adopts the original BASE
acceptance and never repeats its successful raw QA or initial update validation.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys

_support=Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir(): sys.path.insert(0,str(_support))
from pair_common import read,save,sha,ref,bound,require,utc,signature

RECIPE=dict(updates=500,grad_accum=4,rank=8,alpha=16,dropout=0,lr=5e-5,weight_decay=0,grad_clip=1,seed=20261018)
BASE_PARAMETERS=8767123696
CROP_PARAMETERS=7667712
PIPELINE_PARAMETERS=8797892873
LORA=re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.weight$')


def _lines(reference):
    return [json.loads(line) for line in bound(reference).read_text(encoding='utf-8').splitlines() if line]


def _same_state(actual,expected,torch):
    return set(actual)==set(expected) and all(actual[k].dtype==v.dtype and actual[k].shape==v.shape and
        torch.equal(actual[k].contiguous().view(torch.uint8),v.contiguous().view(torch.uint8)) for k,v in expected.items())


def validate_adapter(state):
    import torch
    require(isinstance(state,dict) and len(state)==288,'Exactly288 independent crop matrices required')
    count=0; owners=set()
    for key,value in state.items():
        match=LORA.search(key)
        require(match is not None and int(match[1]) in range(36) and isinstance(value,torch.Tensor)
            and value.device.type=='cpu' and value.ndim==2 and value.is_floating_point() and bool(torch.isfinite(value).all()),
            'Finite CPU language-only crop matrix required')
        require((value.shape[0] if match[3]=='A' else value.shape[1])==8,'Actual saved crop rank differs')
        owners.add((int(match[1]),match[2],match[3])); count+=value.numel()
    require(len(owners)==288 and count==CROP_PARAMETERS,'Actual288 crop matrix/parameter inventory differs')
    return dict(matrices=288,parameters=count)


def validate_progress(state,step,schedule_sha,prepared_ref):
    """Validate actual CPU-loaded weights/Adam/RNG without initializing CUDA."""
    import numpy as np
    import torch
    require(state['schema']=='CROP_R8_COMPLETE_UPDATE_PROGRESS_V1' and state['step']==step and state['micro']==step*4
        and state['schedule_sha256']==schedule_sha and state['train_schedule_reference']==prepared_ref and state['recipe']==RECIPE
        and state['original_TIME_loaded'] is False and state['old_PAIR_loaded'] is False and state['no_base_tensors_saved'] is True,
        'Exact complete crop update/schedule/recipe progress required')
    inventory=validate_adapter(state['adapter_state_dict'])
    optimizer=state['optimizer_state_dict']; groups=optimizer['param_groups']
    require(len(groups)==1 and groups[0]['lr']==5e-5 and groups[0]['weight_decay']==0.,'Exact fixed AdamW parameter group required')
    ids=groups[0]['params']; moments=optimizer['state']
    require(len(ids)==len(set(ids))==288 and set(ids)==set(moments),'Exactly288 actual Adam parameter states required')
    for pid,weight in zip(ids,state['adapter_state_dict'].values()):
        moment=moments[pid]
        require(set(moment)=={'step','exp_avg','exp_avg_sq'},'Actual ordinary AdamW state keys differ')
        require(isinstance(moment['step'],torch.Tensor) and moment['step'].numel()==1
            and float(moment['step'])==step,'Every crop Adam state must be at the completed update')
        for key in ('exp_avg','exp_avg_sq'):
            value=moment[key]
            require(isinstance(value,torch.Tensor) and value.device.type=='cpu' and value.shape==weight.shape
                and value.dtype==weight.dtype and bool(torch.isfinite(value).all()),'Actual finite CPU Adam moments differ')
        require(bool((moment['exp_avg_sq']>=0).all()),'Negative Adam second moment is invalid')
    cpu_rng=state['torch_rng_state']; cuda_rng=state['torch_cuda_rng_state_all']
    require(isinstance(cpu_rng,torch.Tensor) and cpu_rng.device.type=='cpu' and cpu_rng.dtype==torch.uint8 and cpu_rng.ndim==1,
        'Saved CPU torch RNG must be actual byte state')
    torch.Generator(device='cpu').set_state(cpu_rng)
    require(isinstance(cuda_rng,list) and bool(cuda_rng) and all(isinstance(v,torch.Tensor) and v.device.type=='cpu'
        and v.dtype==torch.uint8 and v.ndim==1 and v.numel()>0 for v in cuda_rng),'Saved physical CUDA RNG byte states required')
    n=state['numpy_rng_state']; keys=n['keys']
    require(isinstance(keys,torch.Tensor) and keys.device.type=='cpu' and keys.dtype==torch.int64
        and tuple(keys.shape)==(624,) and bool(((keys>=0)&(keys<=2**32-1)).all()),'Actual numpy MT19937 saved keys required')
    np.random.RandomState().set_state((n['name'],keys.numpy().astype(np.uint32),n['position'],n['has_gauss'],n['cached_gaussian']))
    random.Random().setstate(state['python_rng_state'])
    return dict(**inventory,adam_states=288,step=step,micro=step*4,CPU_torch_RNG_valid=True,
        CUDA_RNG_states=len(cuda_rng),numpy_RNG_valid=True,python_RNG_valid=True,new_model_calls=0)


def validate_logs(updates,micros,schedule,first,last,progress_sha,class_ids,requests):
    require(len(updates)==last-first+1 and [r['step'] for r in updates]==list(range(first,last+1)),
        'Exactly contiguous successful update journal required')
    for row in updates:
        require(row['event']=='SUCCESSFUL_UPDATE_PERSISTED' and row['micro']==4*row['step']
            and math.isfinite(row['mean_micro_loss']) and math.isfinite(row['preclip_gradient_norm'])
            and row['preclip_gradient_norm']>0 and row['finite_gradient_matrices']==288
            and 0<row['nonzero_gradient_matrices']<=288 and isinstance(row['progress_sha256'],str),
            'Finite nonzero persisted crop gradient/update required')
    require(updates[-1]['progress_sha256']==progress_sha,'Last update must bind actual accepted progress bytes')
    expected=list(range((first-1)*4,last*4)); require(len(micros)==3*len(expected),'Exactly begin/loss/backward per actual micro required')
    for offset,micro in enumerate(expected):
        begin,loss,backward=micros[offset*3:offset*3+3]; row=schedule[micro]; request=requests[row['input']['path']]
        require([r['event'] for r in (begin,loss,backward)]==['BEGIN_TRAIN_MICRO','TRAIN_RAW_LOSS','TRAIN_BACKWARD_COMPLETE']
            and all(r['micro']==micro and r['step']==micro//4+1 and r['id']==row['id'] for r in (begin,loss,backward))
            and begin['source_id']==loss['source_id']==row['source_id']==request['source_id']
            and begin['request_id']==loss['request_id']==request['id'] and begin['input']==row['input']
            and loss['class_token_ids']==class_ids and math.isfinite(loss['loss']) and loss['softmax_scope']=='THREE_CLASSES_ONLY',
            'Actual supervised micro/source/request/class sequence differs')
    return dict(successful_updates=len(updates),successful_micro=len(expected),finite_gradient_matrices_each=288)


def validate_raw(raw,receipt,classes,vocabulary):
    import numpy as np
    import torch
    require(isinstance(raw,torch.Tensor) and raw.device.type=='cpu' and raw.dtype==torch.float32 and raw.ndim==1
        and len(raw)==vocabulary==receipt['full_vocabulary_size'] and bool(torch.isfinite(raw).all()),'Actual finite full-vocabulary raw required')
    require(classes==receipt['class_token_ids'] and len(classes)==len(set(classes))==3
        and all(type(k)is int and 0<=k<len(raw) for k in classes) and receipt['raw_dtype']=='torch.float32','Actual class token IDs/dtype differ')
    logits=raw[classes].double(); p=torch.softmax(logits,dim=0).numpy()
    require(np.array_equal(logits.numpy(),np.asarray(receipt['class_logits'],np.float64))
        and np.asarray(receipt['probabilities']).shape==(3,) and np.allclose(p,receipt['probabilities'],rtol=0,atol=5e-15)
        and int(np.argmax(p))==receipt['predicted_index'],'Independent raw class extraction/float64 softmax differs')
    return p.tolist()


def _alias_key(receipt):
    return json.dumps({k:receipt[k] for k in ('model_role','source_id','source_sha256','class_token_ids','input_signature')},sort_keys=True,separators=(',',':'))


def validate_alias(receipt,current_ref,previous,seen):
    key=_alias_key(receipt)
    require(type(receipt['actual_new_forward'])is bool,'Explicit actual-call flag required')
    if receipt['actual_new_forward']:
        require(receipt['alias_of']is None and key not in seen,'An already successful exact role/owner input cannot be rerun')
    else:
        require(isinstance(receipt['alias_of'],dict),'Alias needs exact original receipt reference')
        first=previous.get(receipt['alias_of']['path'])
        require(first is not None and first['reference']==receipt['alias_of'] and current_ref!=receipt['alias_of']
            and first['receipt']['actual_new_forward']is True and _alias_key(first['receipt'])==key and key in seen
            and first['receipt']['raw_logits']==receipt['raw_logits'],'Only exact earlier same-role/source/class/input raw may be reused')
    return key


def _inventory(row,cfg):
    inv=row['inventory']; base=row['base_fingerprint']
    require(base['parameters']==BASE_PARAMETERS and base['sha256']==cfg['expected_base_sha256']
        and inv['base']==BASE_PARAMETERS and inv['crop']==CROP_PARAMETERS and inv['resident']==8774791408
        and inv['conservative_pipeline']==PIPELINE_PARAMETERS and inv['original_TIME_counted']==15335424
        and inv['semantic_counted']==98329 and inv['old_PAIR_counted']==7667712 and inv['adapter']=='crop'
        and inv['actual_lora_matrices']==288 and inv['actual_language_targets']==144
        and inv['original_TIME_loaded']is False and inv['old_PAIR_loaded']is False,'Actual frozen BASE+crop-only inventory differs')


def run(root,stage):
    import numpy as np
    import torch
    torch.set_num_threads(2)
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent crop output QA must remain CPU-only')
    root=Path(root); reg_path=root/'crop_GPU_registration_32.json';reg=read(reg_path)
    require(stage in ('BASE','TRAINED') and reg['schema']=='CROP_PAIR_RENDER_LANGUAGE_PILOT_V32'
        and bound(reg['review_code'])==Path(__file__).resolve() and reg['recipe']==RECIPE,'Exact registered crop first-review code/recipe required')
    bound(reg['GPU_code']);bound(reg['preparation_code']);bound(reg['CPU_registration']);bound(reg['old_PAIR']);bound(reg['old_TIME'])
    gate=read(bound(reg['input_acceptance']));prepared=read(bound(gate['prepared']));cfg=read(bound(reg['model_config']))
    catalog=read(bound(prepared['source_catalog']));sources={r['source_id']:r for r in catalog['sources']}
    require(gate['status']=='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA' and gate['first_independent_pixels_text_native_QA']is True
        and gate['registration']==reg['CPU_registration'] and gate['train_micro']==2000
        and gate['screen_inputs']==reg['expected_screen_inputs']==len(prepared['screen_inputs'])
        and cfg['base_parameters']==BASE_PARAMETERS and cfg['b_adapter_sha256']==reg['old_TIME']['sha256'],'Original complete first input/model identity differs')
    schedule=prepared['train_schedule']; require(len(schedule)==2000 and len({r['id'] for r in schedule})==2000,'Exact2000 scheduled micro IDs required')
    draws=Counter(r['source_id']for r in schedule);screens={e['source_id']for e in prepared['screen_inputs']}
    require(len(draws)==602 and len(screens)==20 and not set(draws)&screens and max(draws.values())-min(draws.values())<=1,'602 source-balanced train/20screen identity split differs')
    for row in schedule:
        p=np.asarray(row['target']);require(p.shape==(3,)and np.isin(p,[0,1]).all()and p.sum()==1,'Only train-only onehot target3 required')
    digest=hashlib.sha256(json.dumps(schedule,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    role='BASE_screen'if stage=='BASE'else'TRAINED_screen';out=root/('crop_output_QA_32_BASE'if stage=='BASE'else'crop_output_QA_33_TRAINED')
    out.mkdir(exist_ok=False);save(out/'claim.json',dict(utc=utc(),stage=stage,registration=ref(reg_path),new_model_calls=0,no_eval_reference_read=True))
    try:
        model_dir=root/'crop_model_31';prior=None;admission=None
        if stage=='BASE':
            final_ref=ref(model_dir/'pilot_completion.json');done=read(bound(final_ref));first,last=1,4;progress_ref=done['progress']
            require(done['status']=='COMPLETE_FIXED4_CROP_ENGINEERING_NO_TRAINED_SCREEN'and done['completed_updates']==4 and done['successful_micro']==16
                and done['GPU_registration']==ref(reg_path)and done['final_quality_checkpoint_selected']is False,'Actual completed pilot4 required')
            require(bound(progress_ref)==(model_dir/'train/pilot_progress.pt').resolve(),'Immutable original step4 progress required')
            registration_ref=ref(reg_path)
        else:
            admission_path=root/'crop_remaining_admission_33.json';admission=read(admission_path);registration_ref=ref(admission_path)
            require(admission['schema']=='CROP_PAIR_REMAINING496_V33'and admission['original_pilot_registration']==ref(reg_path)
                and admission['GPU_code']==reg['GPU_code']and admission['input_acceptance']==reg['input_acceptance'],'Explicit exact remaining496 admission required')
            prior=read(bound(admission['BASE_output_acceptance']))
            require(prior['status']=='PASS_CROP_BASE_SCREEN_AND_PILOT4_FIRST_QA'and prior['registration']==ref(reg_path),
                'Adopt original successful BASE first QA; never rerun it')
            final_ref=ref(model_dir/'completion.json');done=read(bound(final_ref));first,last=5,500;progress_ref=done['progress']
            require(done['status']=='COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY'and done['completed_updates']==500 and done['successful_micro']==2000
                and done['pilot_updates']==4 and done['remaining_updates']==496 and done['actual_training_forwards']==2000
                and done['actual_training_forwards_this_phase']==1984 and done['adapter_reload_all288_exact']is True
                and done['pilot_completion']==prior['pilot_completion']==admission['pilot_completion']
                and done['BASE_completion']==prior['completion']==admission['BASE_completion']
                and done['remaining_admission']==registration_ref,'Exact final500 and adopted original pilot/BASE refs required')
        _inventory(done,cfg)
        require(done['screen_reference_read']is False and done['original_TIME_loaded']is False and done['old_PAIR_loaded']is False
            and done['schedule_sha256']==digest and done['train_schedule_reference']==gate['prepared']and done['train_source_draws']==dict(draws),
            'Actual completed stage/schedule/reference ownership differs')
        initial=read(model_dir/('pilot4_base_identity.json'if stage=='BASE'else'remaining496_base_identity.json'))
        require(initial['base']==done['base_fingerprint']and initial['original_TIME']==reg['old_TIME']and initial['old_PAIR']==reg['old_PAIR']
            and initial['original_TIME_loaded']is False and initial['old_PAIR_loaded']is False,'Frozen initial/final BASE/TIME/PAIR identity differs')
        progress=torch.load(bound(progress_ref),map_location='cpu',weights_only=True)
        engineering=validate_progress(progress,last,digest,gate['prepared']);engineering['progress']=progress_ref
        requests={row['input']['path']:read(bound(row['input']))for row in schedule[(first-1)*4:last*4]}
        require(all(r['source_sha256']==sources[r['source_id']]['source_sha256']and sources[r['source_id']]['role']=='train'
            and r['reference_or_target_in_prompt']is False for r in requests.values()),'Only original train-source label-free requests may supply supervised micro')
        engineering['phase_logs']=validate_logs(_lines(done['update_journal']),_lines(done['micro_journal']),schedule,first,last,
            progress_ref['sha256'],prepared['class_token_ids'],requests)
        engineering.update(base_fingerprint=done['base_fingerprint'],inventory=done['inventory'],prepared=gate['prepared'],schedule_sha256=digest,
            train_source_draws=dict(draws),original_TIME=reg['old_TIME'],old_PAIR=reg['old_PAIR'],no_eval_reference_read=True)
        if stage=='TRAINED':
            require(done['original_TIME_unchanged']is True and done['old_PAIR_unchanged']is True
                and admission['immutable_pilot_progress']==prior['engineering']['progress'],'Frozen old artifacts and original step4 progress adoption differ')
            from safetensors.torch import load_file
            weights=bound(done['adapter_weights']);require(weights.parent==(model_dir/'train/adapter/crop').resolve()
                and str(weights.parent)==done['adapter_directory'],'Only final500 independent crop artifact directory allowed')
            saved=load_file(str(weights),device='cpu');validate_adapter(saved)
            require(_same_state(saved,progress['adapter_state_dict'],torch),'Actual final500 saved288 matrices differ from final progress')
            engineering.update(adapter_weights=done['adapter_weights'],adapter_reload_all288_exact=True,adopted_BASE_acceptance=admission['BASE_output_acceptance'],
                total_successful_updates=500,total_successful_micro=2000,old_BASE_raw_QA_repeated=False)
        completion_ref=done['BASE_completion'if stage=='BASE'else'TRAINED_completion'];completion=read(bound(completion_ref))
        require(bound(completion_ref)==(model_dir/role/'completion.json').resolve()and completion['status']=='COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY'
            and completion['model_role']==role and len(completion['entries'])==completion['expected_inputs']==len(prepared['screen_inputs'])
            and completion['screen_reference_read']is False and completion['original_TIME_loaded']is False and completion['old_PAIR_loaded']is False,
            'Complete exact screen role before first raw QA required')
        predictions=[];seen=set();previous={};seen_inputs=set();raw_paths=set();calls=aliases=0;receipts=[]
        for row,entry in zip(completion['entries'],prepared['screen_inputs']):
            require(row['id']==entry['id']and row['id']not in seen and row['input']==entry['input'],'Exact one result per frozen screen input required')
            request=read(bound(row['input']));receipt=read(bound(row['receipt']))
            require(receipt['id']==request['id']==row['id']and receipt['source_id']==request['source_id']==entry['source_id']
                and receipt['source_sha256']==request['source_sha256']and receipt['input']==row['input']and receipt['model_role']==role
                and request['source_sha256']==sources[entry['source_id']]['source_sha256']and sources[entry['source_id']]['role']=='screen'
                and receipt['role']=='CROP_SCREEN_NO_GT'and receipt['class_token_ids']==request['class_token_ids']==prepared['class_token_ids']
                and receipt['input_signature']==request['input_signature']and receipt['screen_reference_read']is False
                and receipt['original_TIME_loaded']is False and receipt['old_PAIR_loaded']is False
                and request['reference_or_target_in_prompt']is False,'Actual screen source/input/weight-role/class identity differs')
            require(set(request['input_signature'])=={'input_ids','attention_mask','pixel_values','image_grid_thw'},'Exact four actual consumed input tensor signatures required')
            tokens=torch.load(bound(request['tokens']),map_location='cpu',weights_only=True)
            require(set(tokens)=={'input_ids','attention_mask'}and signature(tokens)=={k:request['input_signature'][k]for k in tokens}
                and tokens['input_ids'].dtype==tokens['attention_mask'].dtype==torch.int64 and tokens['input_ids'].shape==tokens['attention_mask'].shape
                and tokens['input_ids'].ndim==2 and tokens['input_ids'].shape[0]==1 and bool((tokens['attention_mask']==1).all()),'Actual prefix token binding differs')
            grid=torch.tensor(request['image_grid_thw'],dtype=torch.int64)
            require(tuple(grid.shape)==(3,3)and bool((grid>0).all())and bool((grid[:,0]==1).all())and bool((grid[:,1:]%2==0).all())
                and signature({'image_grid_thw':grid})['image_grid_thw']==request['input_signature']['image_grid_thw'],
                'Actual three-image grid tensor/signature differs')
            require(0<tokens['input_ids'].shape[1]<=4096 and request['text_evidence']['sequence_tokens']==tokens['input_ids'].shape[1]
                and request['text_evidence']['image_grid_thw']==grid.tolist(),'Actual accepted prefix/grid text evidence differs')
            raw=torch.load(bound(receipt['raw_logits']),map_location='cpu',weights_only=True)
            p=validate_raw(raw,receipt,request['class_token_ids'],completion['full_vocabulary_size'])
            key=validate_alias(receipt,row['receipt'],previous,seen_inputs)
            if receipt['actual_new_forward']:
                require(receipt['raw_logits']['path']not in raw_paths,'Actual new calls require distinct first raw paths')
                calls+=1;raw_paths.add(receipt['raw_logits']['path'])
            else:aliases+=1
            seen.add(row['id']);seen_inputs.add(key);previous[row['receipt']['path']]=dict(reference=row['receipt'],receipt=receipt);receipts.append(receipt)
            predictions.append(dict(id=row['id'],source_id=request['source_id'],source_sha256=request['source_sha256'],input=row['input'],receipt=row['receipt'],probabilities3=p))
        require(calls==completion['actual_forward_calls']and aliases==completion['aliases']and calls+aliases==len(predictions),'Actual first screen call/alias counts differ')
        journal_path=model_dir/role/'attempts.jsonl';events=[json.loads(line)for line in journal_path.read_text().splitlines()if line]
        begins=[e for e in events if e['event']=='BEGIN_NEW_ROLE_FORWARD'];persisted=[e for e in events if e['event']=='FIRST_RAW_PERSISTED'];accepted=[e for e in events if e['event']=='ACCEPTED_NEW_ROLE_RESULT']
        first_receipts={r['id']:r for r in receipts if r['actual_new_forward']}
        require(len(events)==2*calls+len(predictions)and all(e['model_role']==role for e in events)
            and len(begins)==len(persisted)==calls and {e['id']for e in begins}=={e['id']for e in persisted}==set(first_receipts)
            and all(e['raw_logits']==first_receipts[e['id']]['raw_logits']for e in persisted)
            and [e['id']for e in accepted]==[r['id']for r in completion['entries']]
            and all(e['receipt']==r['receipt']for e,r in zip(accepted,completion['entries'])),'Actual begin/persist/accept screen journal differs')
        require(not torch.cuda.is_initialized(),'First independent crop QA cannot initialize CUDA')
        save(root/('crop_BASE_output_acceptance_32.json'if stage=='BASE'else'crop_TRAINED_output_acceptance_33.json'),
            dict(status='PASS_CROP_BASE_SCREEN_AND_PILOT4_FIRST_QA'if stage=='BASE'else'PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA',
                completion=completion_ref,pilot_completion=final_ref if stage=='BASE'else done['pilot_completion'],
                training_completion=final_ref if stage=='TRAINED'else None,predictions=predictions,engineering=engineering,
                registration=registration_ref,original_GPU_registration=ref(reg_path),inputs=len(predictions),actual_new_forwards=calls,
                exact_input_aliases=aliases,attempts=ref(journal_path),new_model_calls=0,no_eval_reference_read=True,quality_established=False,
                automatic_confirm=False,production_prepare_approved=False))
    except BaseException as error:
        import traceback
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,no_automatic_retry=True,new_model_calls=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--stage',choices=('BASE','TRAINED'),required=True)
    args=parser.parse_args();run(args.root,args.stage)
