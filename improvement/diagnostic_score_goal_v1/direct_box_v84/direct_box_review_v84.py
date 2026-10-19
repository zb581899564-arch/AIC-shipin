"""Independent CPU raw/head/native QA and separately qualified direct-box arms.

No decoder, image processor, model, training, parameter selection or GPU work.
Human targets are opened only after complete first raw QA has been persisted.
"""
from __future__ import annotations
import argparse
import datetime as dt
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_math_v84 as math84

WORK=Path('/home/inspur/aic_video_work')
RUN=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ATOL=RTOL=1e-5
ARMS=('DIRECT','ANCHORED_HALF')
CONTROLS=('OLD70_BETA_GEOMETRY','OLD47_GEOM11','OLD33_GEOM13')
ROLE='DIRECT_BOX_TRAINED_screen'


def require(value,message):
    if not value:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(8<<20),b''):h.update(part)
    return h.hexdigest()


def ref(path):return dict(path=str(Path(path).resolve()),sha256=sha(path))


def bound(r):
    p=Path(r['path']).resolve();require(set(r)=={'path','sha256'} and p.is_relative_to(WORK)
        and p.is_file() and sha(p)==r['sha256'],'Exact independently bound CPU review artifact: '+str(p));return p


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def module(r,name):
    p=bound(r);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def validate_head(state):
    import torch
    require(isinstance(state,dict) and set(state)=={'weight','bias'},'Exactly new direct head weight and bias, no old value/beta')
    require(all(isinstance(v,torch.Tensor) and v.device.type=='cpu' and v.dtype==torch.float32
        and not v.requires_grad and bool(torch.isfinite(v).all()) for v in state.values())
        and tuple(state['weight'].shape)==(3,4096) and tuple(state['bias'].shape)==(3,), 'Finite persisted CPU F32 direct head3+three biases')
    return {k:v.double().numpy().copy() for k,v in state.items()}


def independent_native(raw,width,height):
    """Scalar CPU64 rederivation, separate from GPU and math84 decoder code."""
    W,H=math84.dimensions(width,height);dx,dy,dw=map(float,raw)
    require(all(map(math.isfinite,(dx,dy,dw))),'Finite raw3 for independent geometry')
    cap=min(W,16*H/9);w=min(cap,max(1.,cap+dw*W));x=min(W-w,max(0.,(W-w)/2+dx*W))
    y=min(H-9*w/16,max(0.,(H-9*w/16)/2+dy*H))
    def rounded(value):
        f=Fraction(str(float(value)));q,r=divmod(f.numerator,f.denominator);return q+int(2*r>f.denominator)
    iw=min(min(W,16*H//9),max(1,rounded(w)));ix=min(W-iw,max(0,rounded(x)))
    iy=min((16*H-9*iw)//16,max(0,rounded(y)))
    return [ix,iy,iw]


def validate_raw(hidden,raw_head,receipt,head_state,source,*,adapter_weights,head_weights,geometry):
    import torch
    require(isinstance(hidden,torch.Tensor) and hidden.device.type=='cpu' and hidden.dtype==torch.float32
        and tuple(hidden.shape)==(4096,) and not hidden.requires_grad and bool(torch.isfinite(hidden).all()),'Actual persisted finite F32 CPU hidden4096')
    require(isinstance(raw_head,torch.Tensor) and raw_head.device.type=='cpu' and raw_head.dtype==torch.float32
        and tuple(raw_head.shape)==(3,) and not raw_head.requires_grad and bool(torch.isfinite(raw_head).all()),'Actual persisted finite F32 CPU head_raw3')
    require(receipt['adapter_weights']==adapter_weights and receipt['head_weights']==head_weights
        and all(receipt[k]==source[k] for k in ('source_id','source_sha256','width','height')),
        'Actual expected adapter/head SHA and source/dimensions identity')
    weights=validate_head(head_state);cpu=weights['weight']@hidden.double().numpy()+weights['bias'];gpu=raw_head.double().numpy()
    require(bool(np.all(np.abs(cpu-gpu)<=ATOL+RTOL*np.abs(cpu))),'Independent CPU64 linear replay differs from persisted raw_head')
    W,H=source['width'],source['height'];decoded=math84.decode_numpy(gpu,W,H)
    actual=np.asarray(receipt['decoded_xyw'],dtype=np.float64)
    require(actual.shape==(3,) and bool(np.isfinite(actual).all())
        and bool(np.all(np.abs(actual-decoded)<=1e-5*max(W,H))), 'GPU continuous geometry differs from independent raw_head decoder')
    native=independent_native(gpu,W,H)
    require(native==math84.decode_native(gpu,W,H) and geometry.legal(native,W,H),'Independent native half-down geometry/legality')
    base=source['pool'][0]
    require(base==source['baseline_box'] and source['original_BASE_observed'] is True and geometry.legal(base,W,H),
        'Original observed B0, never rename zero-head geometry as baseline')
    half=math84.blend_native(base,native,W,H);require(geometry.legal(half,W,H),'Independent original geometry validates HALF')
    return dict(CPU_head_raw64=cpu.tolist(),GPU_head_raw=gpu.tolist(),maximum_absolute_linear_error=float(np.max(np.abs(cpu-gpu))),
        continuous_xyw64=decoded.tolist(),native_boxes=dict(DIRECT=native,ANCHORED_HALF=half),
        independent_native_geometry=True,head_atol=ATOL,head_rtol=RTOL)


def review_scope(completion,expected,sources,head_state,*,GPU_registration,input_prepared,
                 adapter_weights,head_weights,load_json,load_tensor,geometry,load_events):
    require(completion['status']=='COMPLETE_DIRECT_BOX20_RAW_OUTPUTS_NOT_QUALITY' and completion['model_role']==ROLE
        and completion['expected_inputs']==completion['sources']==len(expected)==20
        and completion['GPU_registration']==GPU_registration and completion['input_prepared']==input_prepared
        and completion['adapter_weights']==adapter_weights and completion['head_weights']==head_weights
        and completion['screen_reference_read'] is False,'Actual completed new20 source-only raw outputs')
    owner={s['source_id']:s for s in sources}
    require(len(owner)==len(sources)==20 and len({s['source_sha256'] for s in sources})==20
        and len({e['id'] for e in expected})==20 and len(completion['entries'])==20,
        'Exact20 unique source/hash/request identities, no duplicate-weighted evaluation')
    events=load_events(completion['attempts']);predictions=[];raw_refs=set()
    for index,(entry,record) in enumerate(zip(expected,completion['entries'])):
        require(all(entry[k]==record[k] for k in ('id','source_id','source_sha256','input')),'Actual saved ordered source/output ownership')
        request=load_json(entry['input']);receipt=load_json(record['receipt']);source=owner[entry['source_id']]
        require(all(receipt[k]==record[k] for k in ('id','source_id','source_sha256','input'))
            and all(request[k]==source[k] for k in ('source_id','source_sha256','width','height'))
            and request['id']==entry['id'] and request['role']==receipt['role']=='screen' and receipt['model_role']==ROLE
            and request['reference_or_target_in_prompt'] is False and receipt['input_signature']==request['input_signature']
            and set(request['input_signature'])=={'input_ids','attention_mask','pixel_values','image_grid_thw'}
            and receipt['image_grid_thw']==request['image_grid_thw'] and len(request['image_grid_thw'])==1
            and not any(k in request for k in ('labels','target','candidate_ious','original_reference_xywh')),
            'Actual label-free full-source request, original role/signature/grid/source metadata')
        require(receipt['actual_new_forward'] is True and receipt['alias_of'] is None,
            'Unique20 owners each require own first forward; cannot replay old or conflicting-role raw')
        raw_key=json.dumps([receipt['raw_hidden'],receipt['raw_head']],sort_keys=True)
        require(raw_key not in raw_refs,'Repeated raw pair cannot be labelled a new source forward');raw_refs.add(raw_key)
        actual=validate_raw(load_tensor(receipt['raw_hidden']),load_tensor(receipt['raw_head']),receipt,head_state,source,
            adapter_weights=adapter_weights,head_weights=head_weights,geometry=geometry)
        block=events[3*index:3*index+3]
        require([e['event'] for e in block]==['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT']
            and all(e['id']==entry['id'] and e['model_role']==ROLE for e in block)
            and block[0]['input']==entry['input'] and block[1]['raw_hidden']==receipt['raw_hidden']
            and block[1]['raw_head']==receipt['raw_head'] and block[2]['receipt']==record['receipt'] and block[2]['alias'] is False,
            'Actual raw-first journal binds persisted hidden/head before accepted geometry')
        predictions.append(dict(**record,raw_hidden=receipt['raw_hidden'],raw_head=receipt['raw_head'],
            adapter_weights=adapter_weights,head_weights=head_weights,**actual))
    require(len(events)==60 and completion['actual_forward_calls']==20 and completion['aliases']==0,
        'Actual20 first source forwards and exact journal, no old QA repetition')
    return dict(status='PASS_DIRECT_BOX84_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA',predictions=predictions,
        actual_new_forwards=20,aliases=0,maximum_absolute_linear_error=max(p['maximum_absolute_linear_error'] for p in predictions),
        adapter_weights=adapter_weights,head_weights=head_weights,quality_established=False,model_calls=0)


def controls_from_utility70(result,expected_ids):
    ids=set(expected_ids);require(len(ids)==len(expected_ids)==20,'Controls70 only for exact historical20, never substitute into19')
    evaluation=result['evaluation'];controls={}
    for name,arm in zip(CONTROLS,('UTILITY_BETA_GEOMETRY','OLD47_GEOM11','OLD33_GEOM13')):
        rows=evaluation['selected'][arm]
        require(len(rows)==20 and {r['source_id'] for r in rows}==ids,'Same original20 control source ownership')
        values=[float(r['selected_iou']) for r in rows]
        require(all(math.isfinite(v) and 0<=v<=1 for v in values),'Actual finite persisted geometry controls')
        mean=float(np.mean(values));require(math.isclose(mean,evaluation['summaries'][arm]['mean_selected_iou'],abs_tol=1e-12,rel_tol=0.),
            'Recomputed mean must match actual persisted control summary')
        controls[name]=dict(source_ids=[r['source_id'] for r in rows],mean_iou=mean)
    return controls


def evaluate_scope(sources,targets,predictions,controls,*,scope='native20',arm_names=None):
    require(scope in ('native20','confirm19'),'Explicit historical static20 or19 only')
    expected=20 if scope=='native20' else 19
    if scope=='native20':
        require(arm_names is None or tuple(arm_names)==ARMS,'Both pre-registered development arms, no after-score subset')
        selected_arms=ARMS
    else:
        require(arm_names is not None and 0<len(arm_names)<=2 and len(set(arm_names))==len(arm_names)
            and all(a in ARMS for a in arm_names),'19 requires explicit previously admitted frozen arm names')
        selected_arms=tuple(arm_names)
    owners={s['source_id']:s for s in sources};labels={t['source_id']:t for t in targets};pred={p['source_id']:p for p in predictions}
    require(len(owners)==len(sources)==len(labels)==len(targets)==len(pred)==len(predictions)==expected
        and set(owners)==set(labels)==set(pred) and len({s['source_sha256'] for s in sources})==expected,
        'Exact unweighted fixed source scope and original targets')
    require(set(controls)==set(CONTROLS),'Exactly three frozen geometry controls')
    for control in controls.values():
        require(len(control['source_ids'])==expected and set(control['source_ids'])==set(owners)
            and math.isfinite(control['mean_iou']) and 0<=control['mean_iou']<=1,'Same-scope actual controls; no20 mean on19')
    reports={}
    for arm in selected_arms:
        rows=[]
        for sid,source in owners.items():
            t,p=labels[sid],pred[sid];W,H=source['width'],source['height']
            require(t['source_sha256']==p['source_sha256']==source['source_sha256'] and t['reference_modified'] is False
                and t['width']==W and t['height']==H,
                'Prediction/original human target/sourceSHA identity')
            reference=math84.target_xywh(t['original_reference_xywh'],W,H)
            base=source['pool'][0];require(base==source['baseline_box'] and source['original_BASE_observed'] is True,'Observed original B0 remains baseline')
            box=p['native_boxes'][arm];old=math84.crop_iou(base,reference,W,H);new=math84.crop_iou(box,reference,W,H)
            rows.append(dict(source_id=sid,baseline_iou=old,selected_iou=new,gain=new-old,baseline_box=base,native_box=box,changed=box!=base))
        mean=float(np.mean([r['selected_iou'] for r in rows]));old_mean=float(np.mean([r['baseline_iou'] for r in rows]))
        summary=dict(sources=expected,mean_selected_iou=mean,mean_baseline_iou=old_mean,mean_gain=mean-old_mean,
            improved=sum(r['gain']>0 for r in rows),worst_loss=max(0.,max(-r['gain'] for r in rows)),
            changed=sum(r['changed'] for r in rows),invalid=0)
        checks=dict(exact_sources=summary['sources']==expected,minimum_gain=summary['mean_gain']>=.01,
            at_least5_improved=summary['improved']>=5,worst_loss_at_most_point1=summary['worst_loss']<=.1,
            actual_change=summary['changed']>0,invalid0=True)
        for name in CONTROLS:checks['beats_'+name]=mean>controls[name]['mean_iou']
        admitted=all(checks.values())
        reports[arm]=dict(status=('PASS_' if admitted else 'STOP_')+'DIRECT_BOX84_'+arm+'_'+scope.upper(),
            summary=summary,quality=dict(admitted=admitted,checks=checks),rows=rows)
    admitted=[a for a in selected_arms if reports[a]['quality']['admitted']]
    return dict(status=('PASS_' if admitted else 'STOP_')+'DIRECT_BOX84_'+scope.upper()+'_QUALIFIED_ARMS',
        mechanism='SOURCE_ONLY_DIRECT_BOX_GRADIENT',scope=scope,arms=reports,admitted_arm_names=admitted,
        frozen_output_arms=list(selected_arms),historical_not_blind=True,static_not_official_joint_quality=True,
        pair_selfzero_applicable=False,original55_and70_STOPs_unchanged=True,production_admitted=False)


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_training(done,progress,initial,reg,registration_ref,*,stage,cfg):
    import re
    import torch
    step=4 if stage=='pilot' else 800
    require(done['status']==('COMPLETE_DIRECT_BOX4_ENGINEERING_NO_DEV_MODEL' if stage=='pilot' else 'COMPLETE_DIRECT_BOX800_NOT_QUALITY')
        and done['GPU_registration']==registration_ref and done['completed_updates']==step
        and done['successful_micro']==done['actual_training_forwards']==4*step
        and done['actual_training_forwards_this_phase']==(16 if stage=='pilot' else 3184)
        and done['recipe']==reg['recipe']==math84.RECIPE
        and done['train_schedule_reference']==reg['prepared'] and done['train_targets_reference']==reg['train_targets']
        and all(done[k] is False for k in ('original_TIME_loaded','old_PAIR_loaded','old_CROP_loaded','old_UTILITY_loaded','screen_reference_read')),
        'Actual fixed direct-box stage counts/fresh BASE-only physical model/training refs')
    inv=done['inventory'];expected=dict(base=math84.BASE,direct_box_lora=math84.LORA,head=math84.HEAD_PARAMETERS,
        trainable=math84.LORA+math84.HEAD_PARAMETERS,resident=math84.PHYSICAL,pipeline=math84.PIPELINE,
        actual_lora_matrices=288,actual_language_targets=144,head_tensors=2,adapter='direct_box',
        original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False,
        original_TIME_counted=15335424,semantic_counted=98329)
    require(all(inv[k]==v for k,v in expected.items()) and done['base_fingerprint']['parameters']==math84.BASE
        and done['base_fingerprint']['sha256']==cfg['expected_base_sha256'],'Actual8790237452 pipeline,8774803699 physical and original BASE fingerprint')
    require(progress['schema']=='DIRECT_BOX_COMPLETE_UPDATE_PROGRESS_V84' and progress['step']==step
        and progress['micro']==progress['logical_training_forwards']==4*step
        and progress['recipe']==math84.RECIPE and progress['no_base_tensors_saved'] is True
        and progress['schedule_sha256']==done['schedule_sha256']
        and progress['train_schedule_reference']==reg['prepared'] and progress['train_targets_reference']==reg['train_targets'],
        'Actual complete optimizer/RNG update checkpoint, not a model-only snapshot')
    validate_head(progress['head_state_dict']);initial_head=validate_head(initial['head_state_dict'])
    require(not np.count_nonzero(initial_head['weight']) and not np.count_nonzero(initial_head['bias']), 'Fresh head all-zero weight AND bias initialization')
    adapter=progress['adapter_state_dict'];require(len(adapter)==len(initial['adapter_state_dict'])==288 and set(adapter)==set(initial['adapter_state_dict']),
        'All288 initial/final new adapter matrices')
    pattern=re.compile(r'language_model\.layers\.\d+\.self_attn\.(?:q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.weight$')
    groups={'A':[],'B':[]}
    for name,value in adapter.items():
        match=pattern.search(name)
        require(match is not None and isinstance(value,torch.Tensor) and value.device.type=='cpu' and value.ndim==2
            and bool(torch.isfinite(value).all()) and value.shape[0 if match[1]=='A' else 1]==8,'Actual rank8 language adapter matrix')
        groups[match[1]].append(name)
    require(len(groups['A'])==len(groups['B'])==144 and sum(v.numel() for v in adapter.values())==math84.LORA,
        'Exact new language LoRA size/targets')
    require(all(not bool(torch.count_nonzero(initial['adapter_state_dict'][n])) for n in groups['B'])
        and all(bool(torch.count_nonzero(initial['adapter_state_dict'][n])) for n in groups['A']),
        'Fresh PEFT initialization has zero B and nonzero A; never inherit a failed adapter')
    names=progress['optimizer_parameter_names_by_group'];optimizer=progress['optimizer_state_dict'];pg=optimizer['param_groups']
    require(len(names)==2 and set(names[0])==set(adapter) and names[1]==['head.weight','head.bias']
        and progress['optimizer_parameter_names_sha256']==done['optimizer_parameter_names_sha256']==digest(names)
        and done['optimizer_parameter_names_by_group']==names and len(pg)==2 and len(pg[0]['params'])==288 and len(pg[1]['params'])==2
        and len(optimizer['state'])==290,'Both Adam groups and exact parameter-name ownership')
    for index,g in enumerate(pg):
        require(g['lr']==([5e-5,.001][index]) and tuple(g['betas'])==(.9,.999) and g['eps']==1e-8 and g['weight_decay']==0.,'Unchanged fixed AdamW recipe')
        for param,name in zip(g['params'],names[index]):
            state=optimizer['state'][param]
            expected_shape=adapter[name].shape if index==0 else progress['head_state_dict'][name.split('.')[1]].shape
            require(float(state['step'])==step and all(state[k].shape==expected_shape and bool(torch.isfinite(state[k]).all())
                for k in ('exp_avg','exp_avg_sq')),'Complete finite correctly shaped Adam moments at exact global step')
    require(isinstance(progress['torch_rng_state'],torch.Tensor) and progress['torch_rng_state'].dtype==torch.uint8
        and len(progress['torch_cuda_rng_state_all'])>0 and all(v.dtype==torch.uint8 for v in progress['torch_cuda_rng_state_all'])
        and set(progress['numpy_rng_state'])=={'name','keys','position','has_gauss','cached_gaussian'}
        and isinstance(progress['python_rng_state'],tuple),'Complete torch/CUDA/numpy/python RNG state')
    changed={g:sum(not torch.equal(adapter[n],initial['adapter_state_dict'][n]) for n in values) for g,values in groups.items()}
    require(changed['A']>0 and changed['B']>0 and done['actual_lora_A_changed'] is True and done['actual_lora_B_changed'] is True
        and not np.array_equal(progress['head_state_dict']['weight'].numpy(),initial_head['weight'])
        and not np.array_equal(progress['head_state_dict']['bias'].numpy(),initial_head['bias']), 'Both adapter sides and biased3 head actually changed')
    return dict(global_updates=step,micro=4*step,training_forwards=4*step,progress=done['progress'],head_zero_init_verified=True,
        changed_adapter_A=changed['A'],changed_adapter_B=changed['B'],all290_optimizer_states_verified=True,
        actual_all_parameters=math84.PIPELINE,physical_parameters=math84.PHYSICAL)


def validate_training_journals(updates,micros,schedule,targets,*,stage):
    import torch
    first,last=(1,4) if stage=='pilot' else (5,800)
    require(len(updates)==last-first+1 and len(micros)==12*(last-first+1),'Complete update/micro journals, one source forward per micro')
    for i,step in enumerate(range(first,last+1)):
        u=updates[i];require(u['event']=='SUCCESSFUL_UPDATE_PERSISTED' and u['step']==step and u['micro']==step*4,'Contiguous complete optimizer steps')
        groups=u['grad_groups'];require(set(groups)=={'LoRA_A','LoRA_B','HEAD_WEIGHT','HEAD_BIAS'},'Four real gradient groups')
        for name,g in groups.items():
            require(g['tensors']==(144 if name.startswith('LoRA_') else 1)
                and type(g['nonzero_tensors']) is int and 0<=g['nonzero_tensors']<=g['tensors']
                and g['finite'] is True and math.isfinite(g['preclip_norm']) and g['preclip_norm']>=0,'Actual finite group gradients')
            if step==1 and name in ('LoRA_A','LoRA_B'):
                require(g['nonzero_tensors']==0 and g['preclip_norm']==0.,'Zero head mathematically forces first-step LoRA zero')
            elif step<=4 and ((step==1 and name in ('HEAD_WEIGHT','HEAD_BIAS'))
                    or (step>=2 and name=='LoRA_B') or (step>=3 and name=='LoRA_A')):
                require(g['nonzero_tensors']>0 and g['preclip_norm']>0.,'Expected real head/B/A gradient at this step')
        require(math.isfinite(u['combined_preclip_gradient_norm']) and u['combined_preclip_gradient_norm']>0,'Actual combined gradient norm')
    for j,micro in enumerate(range((first-1)*4,last*4)):
        begin,value,backward=micros[j*3:j*3+3];s=schedule[micro];t=targets[s['source_id']]
        require([e['event'] for e in (begin,value,backward)]==['BEGIN_TRAIN_MICRO','TRAIN_RAW_LOSS','TRAIN_BACKWARD_COMPLETE']
            and all(e['step']==micro//4+1 and e['micro']==micro and e['id']==s['id'] for e in (begin,value,backward))
            and value['source_id']==begin['source_id']==s['source_id'] and value['input_id']==s['input_id']
            and value['target_xywh']==t['original_reference_xywh'] and value['draw_weight']==s['draw_weight']
            and value['width']==t['width'] and value['height']==t['height'] and value['hidden_retained_real_gradient'] is True,
            'Exact original target/source-equal draw used in real differentiable forward')
        total,components=math84.loss(torch.tensor(value['raw_head'],dtype=torch.float64),value['target_xywh'],value['width'],value['height'])
        require(math.isclose(float(total),value['unweighted_loss'],abs_tol=1e-5,rel_tol=1e-5)
            and math.isclose(float(total)*s['draw_weight'],value['loss'],abs_tol=1e-5,rel_tol=1e-5)
            and all(math.isclose(float(v),value['components'][k],abs_tol=1e-5,rel_tol=1e-5) for k,v in components.items()),
            'Independent CPU64 loss/components/source weighting replay')
    return dict(gradient_groups_verified=True,step1_lora_zero_expected_verified=stage=='pilot',
        verified_updates=last-first+1,verified_micro=(last-first+1)*4,first_step=first,last_step=last)


def _run_review(root,registration,stage):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Independent CPU84 review masks CUDA')
    import torch
    torch.set_num_threads(2);root=Path(root).resolve();rp=Path(registration).resolve()
    require(root.is_relative_to(WORK) and rp==(root/'direct_box_GPU_registration_84.json').resolve(),'Explicit exact84 GPU registration')
    reg=read(rp);require(bound(reg['review_code'])==Path(__file__).resolve() and bound(reg['math_code'])==Path(math84.__file__).resolve()
        and reg['recipe']==math84.RECIPE,'Exact independently registered84 math/review code')
    prepared=read(bound(reg['prepared']));gate=read(bound(reg['input_acceptance']))
    require(gate['status']=='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA' and gate['prepared']==reg['prepared']
        and gate['registration']==reg['CPU_registration'],'Actual complete first source-only622 input QA')
    admission=reg if stage=='pilot' else read(root/'direct_box_remaining_admission_84.json')
    done_path=root/'direct_box_model_84'/('pilot_completion.json' if stage=='pilot' else 'completion.json');done=read(done_path)
    if stage=='final':
        prior=read(bound(admission['pilot_output_acceptance']))
        require(prior['status']=='PASS_DIRECT_BOX84_PILOT4_FIRST_ENGINEERING_QA' and prior['registration']==ref(rp)
            and prior['pilot_completion']==admission['pilot_completion'] and prior['engineering']['progress']==admission['immutable_pilot_progress']
            and done['remaining_admission']==ref(root/'direct_box_remaining_admission_84.json'),'Adopt actual complete pilot QA/progress, no repeat')
    progress=torch.load(bound(done['progress']),map_location='cpu',weights_only=True)
    initial=torch.load(bound(done['initial_trainables']),map_location='cpu',weights_only=True)
    cfg=read(bound(reg['model_config']));engineering=validate_training(done,progress,initial,reg,ref(rp),stage=stage,cfg=cfg)
    target_doc=read(bound(reg['train_targets']));targets={t['source_id']:t for t in target_doc['sources']}
    require(len(targets)==len(target_doc['sources'])==602 and all(t['role']=='train' and t['reference_modified'] is False for t in targets.values()),'Only original602 TRAIN targets in loss replay')
    def events(r):return [json.loads(s) for s in bound(r).read_text().splitlines() if s]
    engineering.update(validate_training_journals(events(done['update_journal']),events(done['micro_journal']),prepared['train_schedule'],targets,stage=stage))
    if stage=='final':
        engineering['step1_lora_zero_expected_verified']=prior['engineering']['step1_lora_zero_expected_verified']
        engineering['adopted_pilot_output_acceptance']=admission['pilot_output_acceptance']
    resource_path=RUN/'controller'/(admission['GPU_job']+'.resource.json');resource=read(resource_path)
    ledger=[json.loads(s) for s in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s and json.loads(s).get('name')==admission['GPU_job']]
    require(ledger==[resource] and resource['status']=='completed' and resource['exit_code']==0,'Actual unique naturally completed shared GPU job')
    out=root/('direct_box_pilot_CPU_QA_84' if stage=='pilot' else 'direct_box_final_CPU_QA_84');out.mkdir(exist_ok=False)
    save(out/'resource_receipt.json',dict(resource=ref(resource_path),record=resource,unique_ledger_entries=1))
    try:
        if stage=='pilot':
            require(done['dev_model_forwards']==0,'Pilot cannot observe development model outputs')
            save(root/'direct_box_pilot_output_acceptance_84.json',dict(status='PASS_DIRECT_BOX84_PILOT4_FIRST_ENGINEERING_QA',
                registration=ref(rp),pilot_completion=ref(done_path),engineering=engineering,resource=ref(out/'resource_receipt.json'),
                quality_established=False,model_calls=0,automatic_remaining=False));return
        require(done['adapter_reload_all288_exact'] is True and done['head_reload_all2_exact'] is True,'Actual complete final artifact save/reload')
        head=torch.load(bound(done['head_weights']),map_location='cpu',weights_only=True);validate_head(head)
        require(all(torch.equal(head[k],progress['head_state_dict'][k]) for k in ('weight','bias')),'Expected head SHA exactly matches complete800 checkpoint')
        from safetensors.torch import load_file
        adapter=load_file(str(bound(done['adapter_weights'])),device='cpu')
        require(set(adapter)==set(progress['adapter_state_dict']) and all(torch.equal(adapter[k],progress['adapter_state_dict'][k]) for k in adapter),'All288 actual adapter weights match checkpoint and screen expected SHA')
        original=read(bound(reg['original_screen_catalog']));sources=[s for s in original['sources'] if s['role']=='screen']
        geometry=module(reg['geometry_code'],'_direct_box84_independent_original_geometry')
        completion=read(bound(done['TRAINED_completion']))
        acceptance=review_scope(completion,prepared['screen_inputs'],sources,head,GPU_registration=ref(rp),input_prepared=reg['prepared'],
            adapter_weights=done['adapter_weights'],head_weights=done['head_weights'],load_json=lambda r:read(bound(r)),
            load_tensor=lambda r:torch.load(bound(r),map_location='cpu',weights_only=True),geometry=geometry,load_events=events)
        acceptance.update(registration=ref(rp),training_completion=ref(done_path),completion=done['TRAINED_completion'],resource=ref(out/'resource_receipt.json'),engineering=engineering)
        acceptance_path=root/'direct_box_final_output_acceptance_84.json';save(acceptance_path,acceptance)
        # The first screen GT access occurs only after all raw/head/native QA.
        require(reg['screen_CPU_targets']==prepared['screen_CPU_targets'],'Explicit CPU-only original screen target ref')
        targets20=read(bound(reg['screen_CPU_targets']))
        old=read(bound(reg['old_control_result70']));require(old['source_catalog']==reg['original_screen_catalog'],'Controls70 use same original source catalog')
        controls=controls_from_utility70(old,[s['source_id'] for s in sources])
        result=evaluate_scope(sources,targets20['sources'],acceptance['predictions'],controls)
        result.update(registration=ref(rp),training_completion=ref(done_path),output_acceptance=ref(acceptance_path),
            adapter_weights=done['adapter_weights'],head_weights=done['head_weights'],fixed_final_checkpoint=True,
            control_result70=reg['old_control_result70'],CPU_targets=reg['screen_CPU_targets'],new_model_calls=0,
            automatic_confirm=False,automatic_production=False)
        comparison=root/'direct_box_comparison_84';comparison.mkdir(exist_ok=False);save(comparison/'result.json',result)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,
            automatic_retry=False,model_calls=0,failure_is_not_empty=True));raise


def run(root,registration,stage):
    root=Path(root).resolve();rp=Path(registration).resolve()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and root.is_relative_to(WORK)
        and rp==(root/'direct_box_GPU_registration_84.json').resolve() and stage in ('pilot','final'),
        'One explicit independent CPU review stage inside authorized root')
    save(root/('direct_box_review_'+stage+'_entry_84.json'),dict(stage=stage,registration=ref(rp),
        review_code=ref(Path(__file__)),model_calls=0,automatic_next_stage=False))
    try:_run_review(root,rp,stage)
    except BaseException as error:
        save(root/('direct_box_review_'+stage+'_failure_84.json'),dict(stage=stage,error=repr(error),
            traceback=traceback.format_exc(),model_calls=0,preserve_all_success=True,automatic_retry=False,failure_is_not_empty=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['pilot','final'],required=True)
    p.add_argument('--registration',type=Path,required=True);a=p.parse_args();run(a.root,a.registration,a.stage)
