"""CPU-only first QA for explicit preclamp numerical recovery of failed93.

Original84/93 artifacts stay unchanged. Adopts twenty historical updates,
skips all88 successful original forwards, and audits only new105 work.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import sys
import traceback
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_math_v84 as frozen_math84
import direct_box_review_v84 as frozen_review84
import direct_box_math_preclamp_v105 as math105
import direct_box_math_recovery_v93 as frozen_math93

WORK=frozen_review84.WORK
ROLE='DIRECT_BOX105_TRAINED_screen'
PILOT='PASS_DIRECT_BOX105_PILOT4_FIRST_ENGINEERING_QA'
RAW_PASS='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA'

require=frozen_review84.require
read=frozen_review84.read
ref=frozen_review84.ref
bound=frozen_review84.bound
save=frozen_review84.save
digest=frozen_review84.digest


def tree_equal(a,b):
    import torch
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and a.dtype==b.dtype and a.shape==b.shape and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(tree_equal(a[k],b[k]) for k in a)
    if isinstance(a,(tuple,list)):return type(a) is type(b) and len(a)==len(b) and all(tree_equal(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def validate_warmstart(initial,original,reg):
    import torch
    require(original['schema']=='DIRECT_BOX_L2_RECOVERY_COMPLETE_UPDATE_PROGRESS_V93' and original['step']==19
        and original['micro']==original['logical_training_forwards']==76 and original['recipe']==frozen_math93.RECIPE
        and original['original_successful_updates']==1 and original['original_successful_forwards']==8,
        'Adopt only actual successful93 step19, never failed step20 or model-only checkpoint')
    require(tree_equal(initial['adapter_state_dict'],original['adapter_state_dict'])
        and tree_equal(initial['head_state_dict'],original['head_state_dict']),'Exact adopted288 adapter and head2 tensors')
    h=frozen_review84.validate_head(initial['head_state_dict'])
    require(bool(np.count_nonzero(h['weight'])) and bool(np.count_nonzero(h['bias'])),'Adopted step19 head is explicitly nonzero, not relabelled fresh zero')
    names=list(initial['adapter_state_dict']);require(len(names)==288,'All288 adopted LoRA matrices')
    groups={k:[n for n in names if '.lora_'+k+'.' in n] for k in ('A','B')}
    require(len(groups['A'])==len(groups['B'])==144
        and all(bool(torch.count_nonzero(initial['adapter_state_dict'][n])) for n in groups['A'])
        and all(bool(torch.count_nonzero(initial['adapter_state_dict'][n])) for n in groups['B']),
        'Actual successful93 step19 trained both LoRA A and B')
    for name in ('torch_rng_state','torch_cuda_rng_state_all','numpy_rng_state','python_rng_state'):
        require(tree_equal(initial[name],original[name]),'Exact original93 step19 RNG family: '+name)
    old_optimizer=original['optimizer_state_dict']
    require(len(old_optimizer['state'])==290 and [len(g['params']) for g in old_optimizer['param_groups']]==[288,2]
        and all(float(s['step'])==19. for s in old_optimizer['state'].values()),'Original93 all290 committed step19 Adam states exist; not reused')
    optimizer=initial['optimizer_state_dict'];pg=optimizer['param_groups']
    require(optimizer['state']=={} and len(pg)==2 and len(pg[0]['params'])==288 and len(pg[1]['params'])==2,
        'Actual new Adam groups have empty moments, not resumed old optimizer')
    return dict(adopted_original93_progress=reg['original93_progress'],adopted_original_updates=20,
        skipped_original_successful_forwards=88,all290_warmstart_tensors_exact=True,adopted_head_nonzero=True,
        all_four_RNG_families_exact=True,new_optimizer_initially_empty=True)


def validate_schedule(prepared,original):
    from collections import Counter
    rows=prepared['train_schedule'];old=original['train_schedule'];count=Counter(s['source_id'] for s in old[88:])
    require(len(old)==3200 and len(rows)==3112 and len(count)==602,'Exact remaining3112 source schedule and602 source identities')
    for index,(row,prior) in enumerate(zip(rows,old[88:])):
        require({k:v for k,v in row.items() if k not in ('draw_weight','original_micro')}=={k:v for k,v in prior.items() if k!='draw_weight'}
            and row['original_micro']==index+88
            and row['draw_weight']==3112/(602*count[row['source_id']]),'No old0..87 replay; exact original88..3199 ownership and new source-equal weights')
    require(prepared['train_inputs']==original['train_inputs'] and prepared['screen_inputs']==original['screen_inputs'],
        'Adopt original successful input compilation, no processor/decode repeat')
    return rows


def validate_training(done,progress,initial,original,reg,registration_ref,*,stage,cfg):
    import torch
    step=4 if stage=='pilot' else 778
    require(stage in ('pilot','final') and done['status']==('COMPLETE_DIRECT_BOX105_NEW4_ENGINEERING_NO_DEV_MODEL' if stage=='pilot' else 'COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY')
        and done['GPU_registration']==registration_ref and done['completed_updates']==step
        and done['successful_micro']==done['actual_training_forwards']==4*step
        and done['actual_training_forwards_this_phase']==(16 if stage=='pilot' else 3096)
        and done['recipe']==reg['recipe']==math105.RECIPE
        and done['train_schedule_reference']==reg['recovery_prepared'] and done['train_targets_reference']==reg['train_targets']
        and all(done[k] is False for k in ('original_TIME_loaded','old_PAIR_loaded','old_CROP_loaded','old_UTILITY_loaded','screen_reference_read')),
        'Actual new105 update/forward counts and unchanged source-only model scope')
    for value in (done,progress):
        require(value['original_successful_updates']==20 and value['original_successful_forwards']==88
            and value['original93_progress']==reg['original93_progress'] and value['optimizer_reset'] is True
            and value['hidden_transform']==math105.RECIPE['hidden_transform'],'Explicit original84 failure/adoption and numerical recovery identity')
    expected=dict(base=math105.BASE,direct_box_lora=math105.LORA,head=math105.HEAD_PARAMETERS,trainable=math105.LORA+math105.HEAD_PARAMETERS,
        resident=math105.PHYSICAL,pipeline=math105.PIPELINE,actual_lora_matrices=288,actual_language_targets=144,head_tensors=2,adapter='direct_box',
        original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False,original_TIME_counted=15335424,semantic_counted=98329)
    require(all(done['inventory'][k]==v for k,v in expected.items()) and done['base_fingerprint']['parameters']==math105.BASE
        and done['base_fingerprint']['sha256']==cfg['expected_base_sha256'],'Actual physical8774803699/pipeline8790237452 frozen BASE')
    require(progress['schema']=='DIRECT_BOX_PRECLAMP_COMPLETE_UPDATE_PROGRESS_V105' and progress['step']==step
        and progress['micro']==progress['logical_training_forwards']==4*step and progress['recipe']==math105.RECIPE
        and progress['no_base_tensors_saved'] is True and progress['schedule_sha256']==done['schedule_sha256']
        and progress['train_schedule_reference']==reg['recovery_prepared'] and progress['train_targets_reference']==reg['train_targets'],
        'Full105 checkpoint at exact new optimizer step, history20 kept separate')
    proof=validate_warmstart(initial,original,reg);frozen_review84.validate_head(progress['head_state_dict'])
    adapter=progress['adapter_state_dict'];require(set(adapter)==set(initial['adapter_state_dict']) and len(adapter)==288,'All288 new matrices saved')
    groups={'A':[],'B':[]};pattern=re.compile(r'language_model\.layers\.\d+\.self_attn\.(?:q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.weight$')
    for name,value in adapter.items():
        match=pattern.search(name)
        require(match is not None and isinstance(value,torch.Tensor) and value.device.type=='cpu' and value.ndim==2
            and bool(torch.isfinite(value).all()) and value.shape[0 if match[1]=='A' else 1]==8,'Actual rank8 language adapter')
        groups[match[1]].append(name)
    require(len(groups['A'])==len(groups['B'])==144 and sum(v.numel() for v in adapter.values())==math105.LORA,'Exact language target parameter inventory')
    names=progress['optimizer_parameter_names_by_group'];optimizer=progress['optimizer_state_dict'];pg=optimizer['param_groups']
    require(len(names)==2 and set(names[0])==set(adapter) and names[1]==['head.weight','head.bias']
        and progress['optimizer_parameter_names_sha256']==done['optimizer_parameter_names_sha256']==digest(names)
        and done['optimizer_parameter_names_by_group']==names and len(pg)==2 and len(pg[0]['params'])==288
        and len(pg[1]['params'])==2 and len(optimizer['state'])==290,'Exact all290 new Adam states and named ownership')
    for index,g in enumerate(pg):
        require(g['lr']==([5e-5,.001][index]) and tuple(g['betas'])==(.9,.999) and g['eps']==1e-8 and g['weight_decay']==0.,'Fixed105 optimizer parameters')
        for param,name in zip(g['params'],names[index]):
            s=optimizer['state'][param];shape=adapter[name].shape if index==0 else progress['head_state_dict'][name.split('.')[1]].shape
            require(float(s['step'])==step and all(s[k].shape==shape and bool(torch.isfinite(s[k]).all()) for k in ('exp_avg','exp_avg_sq')),
                'Adam moment steps count only new105 updates; complete finite moment shape')
    require(progress['torch_rng_state'].dtype==torch.uint8 and len(progress['torch_cuda_rng_state_all'])>0
        and all(v.dtype==torch.uint8 for v in progress['torch_cuda_rng_state_all'])
        and set(progress['numpy_rng_state'])=={'name','keys','position','has_gauss','cached_gaussian'}
        and isinstance(progress['python_rng_state'],tuple),'Complete final torch/CUDA/numpy/python RNG')
    changed={g:sum(not torch.equal(adapter[n],initial['adapter_state_dict'][n]) for n in ns) for g,ns in groups.items()}
    require(changed['A']>0 and changed['B']>0 and done['actual_lora_A_changed'] is True and done['actual_lora_B_changed'] is True
        and all(not torch.equal(progress['head_state_dict'][k],initial['head_state_dict'][k]) for k in ('weight','bias')),
        'New105 A/B/head weight and bias actually changed after exact warmstart')
    return dict(proof,global_updates=step,micro=4*step,training_forwards=4*step,progress=done['progress'],
        total_adopted_plus_new_updates=step+20,changed_adapter_A=changed['A'],changed_adapter_B=changed['B'],
        all290_optimizer_states_verified=True,actual_all_parameters=math105.PIPELINE,physical_parameters=math105.PHYSICAL)


def validate_training_journals(updates,micros,schedule,targets,*,stage):
    import torch
    first,last=(1,4) if stage=='pilot' else (5,778)
    require(len(updates)==last-first+1 and len(micros)==12*(last-first+1),'Exact complete new105 updates/micros')
    zero_steps=[];zero_groups={n:0 for n in ('LoRA_A','LoRA_B','HEAD_WEIGHT','HEAD_BIAS')}
    for i,step in enumerate(range(first,last+1)):
        row=updates[i];require(row['event']=='SUCCESSFUL_UPDATE_PERSISTED' and row['step']==step and row['micro']==4*step,'Contiguous new optimizer updates')
        groups=row['grad_groups'];require(set(groups)=={'LoRA_A','LoRA_B','HEAD_WEIGHT','HEAD_BIAS'},'Actual four gradient groups')
        for name,g in groups.items():
            require(g['tensors']==(144 if name.startswith('LoRA_') else 1) and type(g['nonzero_tensors']) is int
                and 0<=g['nonzero_tensors']<=g['tensors'] and g['finite'] is True and math.isfinite(g['preclip_norm']) and g['preclip_norm']>=0,'Finite real group gradients')
            if g['nonzero_tensors']==0:require(g['preclip_norm']==0.,'An all-zero gradient group has zero norm')
            if g['preclip_norm']==0.:zero_groups[name]+=1
            if step<=4:require(g['nonzero_tensors']>0 and g['preclip_norm']>0.,'New105 pilot A/B/head gradients must all be real')
        norm=row['combined_preclip_gradient_norm'];require(math.isfinite(norm) and norm>=0,'Actual total gradient finite and nonnegative')
        if norm==0.:zero_steps.append(step)
        if step<=4:require(norm>0,'New105 pilot total gradient must be real')
    for index,micro in enumerate(range((first-1)*4,last*4)):
        begin,value,backward=micros[index*3:index*3+3];s=schedule[micro];t=targets[s['source_id']]
        require([r['event'] for r in (begin,value,backward)]==['BEGIN_TRAIN_MICRO','TRAIN_RAW_LOSS','TRAIN_BACKWARD_COMPLETE']
            and all(r['step']==micro//4+1 and r['micro']==micro and r['id']==s['id'] for r in (begin,value,backward))
            and value['original_micro']==s['original_micro']==micro+88
            and value['source_id']==begin['source_id']==s['source_id'] and value['input_id']==s['input_id']
            and value['target_xywh']==t['original_reference_xywh'] and value['draw_weight']==s['draw_weight']
            and value['width']==t['width'] and value['height']==t['height'] and value['hidden_retained_real_gradient'] is True,
            'Actual new source-only loss uses unchanged GT and exact original88..3199 source draws')
        total,parts=math105.loss(torch.tensor(value['raw_head'],dtype=torch.float64),value['target_xywh'],value['width'],value['height'])
        require(math.isclose(float(total),value['unweighted_loss'],abs_tol=1e-5,rel_tol=1e-5)
            and math.isclose(float(total)*s['draw_weight'],value['loss'],abs_tol=1e-5,rel_tol=1e-5)
            and all(math.isclose(float(v),value['components'][k],abs_tol=1e-5,rel_tol=1e-5) for k,v in parts.items()),'CPU64 preclamp SmoothL1 plus frozen legal GIoU and source-equal replay')
    return dict(gradient_groups_verified=True,pilot_all_four_gradient_groups_nonzero_verified=stage=='pilot',
        finite_zero_gradient_updates=zero_steps,finite_zero_gradient_update_count=len(zero_steps),finite_zero_group_counts=zero_groups,
        verified_updates=last-first+1,verified_micro=4*(last-first+1),first_step=first,last_step=last)


def validate_raw(hidden,raw_head,receipt,head,source,*,adapter_weights,head_weights,geometry):
    import torch
    require(isinstance(hidden,torch.Tensor) and hidden.dtype==torch.float32 and hidden.device.type=='cpu'
        and tuple(hidden.shape)==(4096,) and not hidden.requires_grad,'Actual original unnormalized F32CPU hidden4096')
    normalized=math105.normalize_hidden(hidden)
    actual=frozen_review84.validate_raw(normalized,raw_head,receipt,head,source,adapter_weights=adapter_weights,head_weights=head_weights,geometry=geometry)
    actual.update(hidden_transform=math105.RECIPE['hidden_transform'],original_hidden_l2_norm=float(torch.linalg.vector_norm(hidden)),
        normalized_hidden_l2_norm=float(torch.linalg.vector_norm(normalized)),raw_hidden_is_original_unnormalized=True,
        CPU_normalization_dtype='torch.float32',CPU_linear_dtype='torch.float64')
    return actual


def review_scope(done,expected,sources,head,reg,registration_ref,*,load_json,load_tensor,load_events,geometry):
    require(done['status']=='COMPLETE_DIRECT_BOX105_NATIVE20_RAW_NOT_QUALITY' and done['model_role']==ROLE
        and done['expected_inputs']==done['sources']==len(expected)==20 and done['GPU_registration']==registration_ref
        and done['input_prepared']==reg['prepared'] and done['adapter_weights']==reg['adapter_weights'] and done['head_weights']==reg['head_weights']
        and done['screen_reference_read'] is False,'Actual final778 native20 source-only raw completion')
    owners={s['source_id']:s for s in sources};require(len(owners)==len(sources)==20 and len({s['source_sha256'] for s in sources})==20
        and len({e['id'] for e in expected})==len(done['entries'])==20,'Exact source20 unique unweighted owners')
    events=load_events(done['attempts']);predictions=[];raw_seen=set()
    for index,(entry,record) in enumerate(zip(expected,done['entries'])):
        require(all(entry[k]==record[k] for k in ('id','source_id','source_sha256','input')),'Exact native20 ordered input/output ownership')
        request=load_json(entry['input']);receipt=load_json(record['receipt']);source=owners[entry['source_id']]
        require(all(request[k]==source[k]==receipt[k] for k in ('source_id','source_sha256','width','height'))
            and all(receipt[k]==record[k] for k in ('id','source_id','source_sha256','input'))
            and request['id']==entry['id'] and request['role']==receipt['role']=='screen' and receipt['model_role']==ROLE
            and request['reference_or_target_in_prompt'] is False and receipt['input_signature']==request['input_signature']
            and set(request['input_signature'])=={'input_ids','attention_mask','pixel_values','image_grid_thw'}
            and receipt['image_grid_thw']==request['image_grid_thw'] and len(request['image_grid_thw'])==1
            and not any(k in request for k in ('labels','target','candidate_ious','original_reference_xywh'))
            and receipt['actual_new_forward'] is True and receipt['alias_of'] is None,'Original source-only screen F4 request, new105 role, one first forward')
        raw_key=json.dumps([receipt['raw_hidden'],receipt['raw_head']],sort_keys=True)
        require(raw_key not in raw_seen,'Unique source cannot reuse another owner raw');raw_seen.add(raw_key)
        actual=validate_raw(load_tensor(receipt['raw_hidden']),load_tensor(receipt['raw_head']),receipt,head,source,
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],geometry=geometry)
        block=events[3*index:3*index+3]
        require([r['event'] for r in block]==['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT']
            and all(r['id']==entry['id'] and r['model_role']==ROLE for r in block) and block[0]['input']==entry['input']
            and block[1]['raw_hidden']==receipt['raw_hidden'] and block[1]['raw_head']==receipt['raw_head']
            and block[2]['receipt']==record['receipt'] and block[2]['alias'] is False,'Actual original hidden and normalized-head raw persisted before postchecks')
        predictions.append(dict(**record,raw_hidden=receipt['raw_hidden'],raw_head=receipt['raw_head'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],**actual))
    require(len(events)==60 and done['actual_forward_calls']==20 and done['aliases']==0,'Exactly20 actual new105 native forwards')
    return dict(status=RAW_PASS,predictions=predictions,actual_new_forwards=20,aliases=0,
        maximum_absolute_linear_error=max(p['maximum_absolute_linear_error'] for p in predictions),
        adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],model_calls=0,quality_established=False)


def _read(reference):return read(bound(reference))


def _events(reference):return [json.loads(s) for s in bound(reference).read_text().splitlines() if s]


def _run(root,stage,registration):
    import torch
    torch.set_num_threads(2);reg=read(registration);registration_ref=ref(registration)
    require(bound(reg['review_code'])==Path(__file__).resolve() and bound(reg['math_code'])==Path(math105.__file__).resolve()
        and bound(reg['frozen_review84_code'])==Path(frozen_review84.__file__).resolve()
        and bound(reg['frozen_math84_code'])==Path(frozen_math84.__file__).resolve()
        and bound(reg['frozen_math93_code'])==Path(frozen_math93.__file__).resolve()
        and reg['recipe']==math105.RECIPE,'Exact independent105/frozen93/frozen84 CPU code and recipe')
    prepared=_read(reg['recovery_prepared']);original_prepared=_read(reg['prepared']);gate=_read(reg['input_acceptance'])
    require(prepared['schema']=='DIRECT_BOX_PRECLAMP_RECOVERY_SCHEDULE_V105' and gate['status']=='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA'
        and gate['prepared']==prepared['original_prepared']==reg['prepared'] and gate['registration']==reg['CPU_registration'],
        'Adopt only complete original622 first input QA; new105 schedule metadata, no repeated compilation')
    schedule=validate_schedule(prepared,original_prepared)
    require(prepared['schedule_sha256']==digest(schedule),'Exact frozen source-equal105 schedule digest')
    original=torch.load(bound(reg['original93_progress']),map_location='cpu',weights_only=True)
    oldreg=_read(reg['frozen_GPU93_registration']);failure=_read(reg['original93_failure'])
    require(oldreg['GPU_code']==reg['frozen_GPU93_code'] and oldreg['math_code']==reg['frozen_math93_code']
        and all(oldreg[k]==reg[k] for k in
        ('prepared','input_acceptance','CPU_registration','preparation_code','train_targets','model_config','original_GPU32','original_GPU18','old_TIME','old_PAIR','old_CROP'))
        and failure['completed_updates']==19 and failure['successful_micro']==failure['actual_training_forwards']==80
        and failure['last_progress']==reg['original93_progress'],'Actual failed93 ancestor:19 saved updates/80 consumed forwards plus inherited84 remain consumed')
    require(original['schedule_sha256']==_read(oldreg['recovery_prepared'])['schedule_sha256']
        and original['train_schedule_reference']==oldreg['recovery_prepared'] and original['train_targets_reference']==oldreg['train_targets']
        and original['original84_progress']==oldreg['original84_progress'],'Exact committed93 schedule/target/84 ancestry, no changed old recovery identity')
    diagnosis=_read(reg['projection_diagnosis104'])
    require(diagnosis['status']=='PASS_CPU104_PROJECTED_LOSS_FLAT_REGION_CONFIRMED' and diagnosis['math93_code']==reg['frozen_math93_code']
        and diagnosis['all_four_old_gradient_zero'] is True and diagnosis['all_four_have_better_legal_point'] is True,
        'Actual mathematical diagnosis retained, never relabel failed84/93 as PASS')
    out=root/'direct_box_model_105';done_path=out/('pilot_completion.json' if stage=='pilot' else 'completion.json');done=read(done_path)
    admission=reg if stage=='pilot' else read(root/'direct_box_remaining_admission_105.json')
    if stage=='final':
        prior=_read(admission['pilot_output_acceptance'])
        require(prior['status']==PILOT and prior['registration']==registration_ref and prior['pilot_completion']==admission['pilot_completion']
            and prior['engineering']['progress']==admission['immutable_pilot_progress'] and prior['engineering']['global_updates']==4
            and done['remaining_admission']==ref(root/'direct_box_remaining_admission_105.json'),'Actual accepted new4 pilot; no repeat pilot QA')
    progress=torch.load(bound(done['progress']),map_location='cpu',weights_only=True)
    initial=torch.load(bound(done['initial_trainables']),map_location='cpu',weights_only=True)
    engineering=validate_training(done,progress,initial,original,reg,registration_ref,stage=stage,cfg=_read(reg['model_config']))
    target_doc=_read(reg['train_targets']);targets={r['source_id']:r for r in target_doc['sources']}
    require(len(targets)==len(target_doc['sources'])==602 and all(r['role']=='train' and r['reference_modified'] is False for r in targets.values()),'Unchanged original602 TRAIN targets only')
    engineering.update(validate_training_journals(_events(done['update_journal']),_events(done['micro_journal']),schedule,targets,stage=stage))
    if stage=='final':
        engineering.update(pilot_all_four_gradient_groups_nonzero_verified=prior['engineering']['pilot_all_four_gradient_groups_nonzero_verified'],
            adopted_pilot_output_acceptance=admission['pilot_output_acceptance'])
    resource_path=frozen_review84.RUN/'controller'/(admission['GPU_job']+'.resource.json');resource=read(resource_path)
    ledger=[r for r in _events(ref(WORK/'improvement_round1/gpu_ledger.jsonl')) if r.get('name')==admission['GPU_job']]
    require(ledger==[resource] and resource['status']=='completed' and resource['exit_code']==0,'Unique new105 shared GPU job naturally completed/exit0')
    common=dict(registration=registration_ref,engineering=engineering,resource=ref(resource_path),quality_established=False,model_calls=0,
        original93_progress=reg['original93_progress'],original84_failure_preserved=True,original93_failure_preserved=True,automatic_remaining=False)
    if stage=='pilot':
        require(done['dev_model_forwards']==0,'No development model observation in new4 pilot')
        save(root/'direct_box_pilot_output_acceptance_105.json',dict(common,status=PILOT,pilot_completion=ref(done_path)));return
    require(done['adapter_reload_all288_exact'] is True and done['head_reload_all2_exact'] is True,'Actual final saved/reloaded all290 trainables')
    head=torch.load(bound(done['head_weights']),map_location='cpu',weights_only=True);frozen_review84.validate_head(head)
    require(tree_equal(head,progress['head_state_dict']),'Saved final head is exact full778 checkpoint')
    from safetensors.torch import load_file
    adapter=load_file(str(bound(done['adapter_weights'])),device='cpu')
    require(tree_equal(adapter,progress['adapter_state_dict']),'Saved all288 adapter tensors exact full778 checkpoint')
    sources=[s for s in _read(reg['original_screen_catalog'])['sources'] if s['role']=='screen']
    geometry=frozen_review84.module(reg['geometry_code'],'_direct_box105_original_geometry')
    accepted=review_scope(_read(done['TRAINED_completion']),prepared['screen_inputs'],sources,head,dict(reg,adapter_weights=done['adapter_weights'],head_weights=done['head_weights']),
        registration_ref,load_json=_read,load_tensor=lambda r:torch.load(bound(r),map_location='cpu',weights_only=True),load_events=_events,geometry=geometry)
    accepted.update(common,training_completion=ref(done_path),completion=done['TRAINED_completion'])
    acceptance_path=root/'direct_box_final_output_acceptance_105.json';save(acceptance_path,accepted)
    # The first native20 GT read is after complete new105 raw/head/native first QA.
    require(reg['screen_CPU_targets']==prepared['screen_CPU_targets'],'Original CPU-only native20 target ref')
    targets20=_read(reg['screen_CPU_targets']);old=_read(reg['old_control_result70'])
    require(old['source_catalog']==reg['original_screen_catalog'],'Same fixed original native20 control source catalog')
    controls=frozen_review84.controls_from_utility70(old,[s['source_id'] for s in sources])
    result=frozen_review84.evaluate_scope(sources,targets20['sources'],accepted['predictions'],controls)
    result['status']=('PASS_' if result['admitted_arm_names'] else 'STOP_')+'DIRECT_BOX105_NATIVE20_QUALIFIED_ARMS'
    for arm,report in result['arms'].items():report['status']=('PASS_' if report['quality']['admitted'] else 'STOP_')+'DIRECT_BOX105_'+arm+'_NATIVE20'
    result.update(registration=registration_ref,training_completion=ref(done_path),output_acceptance=ref(acceptance_path),
        adapter_weights=done['adapter_weights'],head_weights=done['head_weights'],fixed_final_checkpoint=True,new_updates=778,
        total_adopted_plus_new_updates=798,CPU_targets=reg['screen_CPU_targets'],control_result70=reg['old_control_result70'],new_model_calls=0,
        hidden_transform=math105.RECIPE['hidden_transform'],original84_failure_preserved=True,original93_failure_preserved=True,automatic_confirm=False,automatic_production=False)
    comparison=root/'direct_box_comparison_105';comparison.mkdir(exist_ok=False);save(comparison/'result.json',result)


def run(root,stage,registration):
    root=Path(root).resolve();registration=Path(registration).resolve()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and root.is_relative_to(WORK) and stage in ('pilot','final')
        and registration==root/'direct_box_GPU_registration_105.json','One explicit independent CPU-only105 review')
    try:_run(root,stage,registration)
    except BaseException as error:
        failure=root/('direct_box_review_'+stage+'_failure_105.json')
        if not failure.exists():save(failure,dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,
            original84_failure_preserved=True,original93_failure_preserved=True,automatic_retry=False,model_calls=0,failure_is_not_empty=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['pilot','final'],required=True)
    p.add_argument('--registration',type=Path,required=True);a=p.parse_args();run(a.root,a.stage,a.registration)
