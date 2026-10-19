"""Conditional direct-box CPU QA/evaluation and exact native spatial overlays.

No model/processor/media decoder calls; official sources never enter human evaluation.
The frozen84 decoder and qualification gates remain unchanged.
"""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback
import zipfile
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_math_v84 as math84
import direct_box_review_v84 as review84
import direct_box_math_preclamp_v105 as math105
import direct_box_math_recovery_v93 as frozen_math93
import direct_box_review_preclamp_v105 as review105
import direct_box_review_recovery_v93 as frozen_review93

WORK=review84.WORK
ARMS=review84.ARMS
BASELINE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
NATIVE_PASS='PASS_DIRECT_BOX105_NATIVE20_QUALIFIED_ARMS'
CONFIRM_PASS='PASS_DIRECT_BOX106_CONFIRM19_QUALIFIED_ARMS'
FORMAL_QA='PASS_DIRECT_BOX109_FORMAL_FIRST_RAW_HEAD_PTS_CPU_QA'



def json_primitives(value):
    """Convert NumPy containers/scalars without stringifying unknown objects."""
    if isinstance(value,np.ndarray):return json_primitives(value.tolist())
    if isinstance(value,np.bool_):return bool(value)
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,np.floating):return float(value)
    if isinstance(value,np.str_):return str(value)
    if isinstance(value,np.generic):
        converted=value.item()
        if isinstance(converted,np.generic):raise TypeError('Unsupported NumPy JSON scalar: '+type(value).__name__)
        return json_primitives(converted)
    if value is None or type(value) in (str,bool,int,float):return value
    if isinstance(value,(list,tuple)):return [json_primitives(v) for v in value]
    if isinstance(value,dict):
        result={}
        for key,item in value.items():
            converted=json_primitives(key)
            if converted is not None and type(converted) not in (str,bool,int,float):
                raise TypeError('Unsupported JSON mapping key: '+type(key).__name__)
            result[converted]=json_primitives(item)
        return result
    raise TypeError('Unsupported JSON value: '+type(value).__name__)


def save(path,value):
    # The original exclusive/fsync writer still enforces allow_nan=False.
    return review84.save(path,json_primitives(value))


def require(value,message):
    if not value:raise ValueError(message)


def validate_qualification(reg,quality,*,phase,confirm=None):
    require(phase in ('confirm19','formal') and reg['phase']==phase,'One explicit readonly direct-box phase')
    weights=('training_completion','adapter_weights','head_weights')
    require(quality['status']==NATIVE_PASS and quality['fixed_final_checkpoint'] is True
        and quality['new_updates']==778 and quality['total_adopted_plus_new_updates']==798
        and quality['hidden_transform']==math105.RECIPE['hidden_transform']
        and all(quality[k]==reg[k] for k in weights) and 0<len(quality['admitted_arm_names'])<=2
        and set(quality['arms'])==set(ARMS)
        and quality['admitted_arm_names']==[a for a in ARMS if quality['arms'][a]['quality']['admitted'] is True],
        'Actual fixed778-new native20 qualified arms; no failed93/84/55/70 admission')
    allowed=list(quality['admitted_arm_names'])
    if phase=='formal':
        require(confirm is not None and confirm['status']==CONFIRM_PASS
            and confirm['fixed_final_checkpoint'] is True and confirm['native20_quality_result']==reg['native20_quality_result']
            and all(confirm[k]==reg[k] for k in weights) and confirm['frozen_admitted_arm_names']==allowed
            and 0<len(confirm['admitted_arm_names'])<=len(allowed)
            and set(confirm['arms'])==set(allowed)
            and confirm['admitted_arm_names']==[a for a in allowed if confirm['arms'][a]['quality']['admitted'] is True],
            'Actual same19 independently qualified arm subset, same778-new model')
        allowed=[a for a in allowed if a in confirm['admitted_arm_names']]
    require(reg['admitted_arm_names']==allowed and len(set(allowed))==len(allowed),'Exact pre-frozen eligible arms, no new coefficient/arm selection')
    return allowed


def controls19(sources,targets,*,beta70,rms47,beta47,beta33,geometry_features):
    require(len(sources)==len(targets)==19 and len({s['source_id'] for s in sources})==19,'Exact original historical19')
    labels={t['source_id']:t for t in targets};ids=[s['source_id'] for s in sources]
    require(set(labels)==set(ids),'Same19 controls and unchanged human target source set')
    b70=np.asarray(beta70,np.float64);rms=np.asarray(rms47,np.float64);b47=np.asarray(beta47,np.float64);b33=np.asarray(beta33,np.float64)
    require(b70.shape==b47.shape==(11,) and rms.shape==(14,) and b33.shape==(13,)
        and all(bool(np.isfinite(a).all()) for a in (b70,rms,b47,b33)) and bool((rms>0).all()),'Frozen finite existing control coefficients only')
    rows={name:[] for name in review84.CONTROLS}
    for source in sources:
        sid=source['source_id'];target=labels[sid];W,H=source['width'],source['height'];pool=source['pool']
        require(target['reference_modified'] is False and target['source_sha256']==source['source_sha256']
            and target['width']==W and target['height']==H
            and source['original_BASE_observed'] is True and pool[0]==source['baseline_box'],'Actual original19 observed BASE/target identity')
        geometry=np.stack([geometry_features(b,W,H) for b in pool]);require(geometry.shape==(len(pool),13),'Original geometry13 for same native pool')
        delta=(geometry-geometry[0])[:,1:12]
        values=(delta@b70,(delta/rms[3:])@b47,geometry@b33-(geometry@b33)[0])
        for name,gains in zip(review84.CONTROLS,values):
            require(bool(np.isfinite(gains).all()) and gains[0]==0.,'Geometry score differences preserve B0 zero')
            chosen=int(np.argmax(gains));iou=math84.crop_iou(pool[chosen],target['original_reference_xywh'],W,H)
            rows[name].append(dict(source_id=sid,source_sha256=source['source_sha256'],selected_index=chosen,
                selected_native_box=pool[chosen],selected_iou=iou))
    controls={name:dict(source_ids=ids,mean_iou=float(np.mean([r['selected_iou'] for r in rows[name]]))) for name in rows}
    return controls,dict(rows=rows,new_forward=0,new_fit=0,scope='SAME_HISTORICAL19_ONLY',GT_used_for_geometry_choice=False)


def exact_key(request,adapter_weights,head_weights):
    require(set(request['input_signature'])=={'input_ids','attention_mask','pixel_values','image_grid_thw'},'Exact source-only F4 signatures')
    value={k:request[k] for k in ('source_id','source_sha256','width','height','input_signature','image_grid_thw')}
    value.update(adapter_weights=adapter_weights,head_weights=head_weights)
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def accepted_raw_index(acceptance_refs,*,training_completion,adapter_weights,head_weights,load_json,bind):
    """Adopt prior first QA by refs/scalars; never load old hidden/head tensors."""
    require(isinstance(acceptance_refs,list),'Explicit prior first-QA refs, possibly none')
    result={}
    for ar in acceptance_refs:
        accepted=load_json(ar)
        require(accepted['status'] in ('PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA',
            'PASS_DIRECT_BOX109_CONFIRM19_FIRST_RAW_HEAD_CPU_QA',FORMAL_QA)
            and accepted['training_completion']==training_completion and accepted['adapter_weights']==adapter_weights
            and accepted['head_weights']==head_weights,'Only same complete778-new/head/adapter previously first-QAd outputs')
        for p in accepted['predictions']:
            request=load_json(p['input']);receipt=load_json(p['receipt'])
            require(all(p[k]==request[k]==receipt[k] for k in ('id','source_id','source_sha256'))
                and receipt['input']==p['input'] and receipt['raw_hidden']==p['raw_hidden'] and receipt['raw_head']==p['raw_head']
                and receipt['adapter_weights']==adapter_weights and receipt['head_weights']==head_weights
                and receipt['input_signature']==request['input_signature'] and receipt['image_grid_thw']==request['image_grid_thw']
                and receipt['hidden_transform']==p['hidden_transform']==math105.RECIPE['hidden_transform'],
                'Prior raw ownership/request/signature/expected weights')
            key=exact_key(request,adapter_weights,head_weights)
            gpu=np.asarray(p['GPU_head_raw'],np.float64);cpu=np.asarray(p['CPU_head_raw64'],np.float64)
            require(gpu.shape==cpu.shape==(3,) and bool(np.isfinite(gpu).all()) and bool(np.isfinite(cpu).all())
                and bool(np.all(np.abs(gpu-cpu)<=review84.ATOL+review84.RTOL*np.abs(cpu))), 'Persisted successful CPU64 first-head QA evidence')
            bind(p['raw_hidden']);bind(p['raw_head'])
            candidate=dict(input=p['input'],receipt=p['receipt'],raw_hidden=p['raw_hidden'],raw_head=p['raw_head'],
                acceptance=ar,model_role=receipt['model_role'],GPU_head_raw=gpu.tolist(),CPU_head_raw64=cpu.tolist(),
                maximum_absolute_linear_error=float(np.max(np.abs(gpu-cpu))))
            if key in result:
                require(all(result[key][k]==candidate[k] for k in ('raw_hidden','raw_head','GPU_head_raw','CPU_head_raw64')),
                    'Conflicting exact successful raw cannot be chosen after seeing results')
            result.setdefault(key,candidate)
    return result


def adopted_geometry(prior,source,geometry):
    gpu=prior['GPU_head_raw'];W,H=source['width'],source['height']
    direct=review84.independent_native(gpu,W,H);require(geometry.legal(direct,W,H),'Adopted same-model raw strict native legality')
    base=source['pool'][0];require(base==source['baseline_box'] and source['original_BASE_observed'] is True
        and geometry.legal(base,W,H),'Adopted raw still uses original immutable B0')
    half=math84.blend_native(base,direct,W,H);require(geometry.legal(half,W,H),'Adopted raw fixed HALF geometry')
    return dict(CPU_head_raw64=prior['CPU_head_raw64'],GPU_head_raw=gpu,
        maximum_absolute_linear_error=prior['maximum_absolute_linear_error'],continuous_xyw64=math84.decode_numpy(gpu,W,H).tolist(),
        native_boxes=dict(DIRECT=direct,ANCHORED_HALF=half),independent_native_geometry=True,
        head_atol=review84.ATOL,head_rtol=review84.RTOL,prior_raw_first_QA_adopted=True,
        hidden_transform=math105.RECIPE['hidden_transform'],raw_hidden_is_original_unnormalized=True)


def source_baseline(source):
    """A formal source has one observed B0, without manufacturing a new pool."""
    result=copy.deepcopy(source)
    require(source['original_BASE_observed'] is True,'Original B0 observation proof')
    if 'pool' in source:require(source['pool'] and source['pool'][0]==source['baseline_box'],'Observed first native candidate is original B0')
    else:result['pool']=[list(source['baseline_box'])]
    return result


def review_raw_scope(completion,expected,sources,head_state,reg,*,registration_ref,load_json,load_tensor,load_events,geometry,external):
    phase=reg['phase'];count=reg['expected_inputs'];role='DIRECT_BOX105_'+phase
    require(phase in ('confirm19','formal') and count==len(expected)==len(sources)>0
        and (phase!='confirm19' or count==19),'Exact real19 or actual formal observation scope')
    owner={s['source_id']:source_baseline(s) for s in sources}
    require(len(owner)==len(sources) and len({e['id'] for e in expected})==count
        and (phase!='confirm19' or len({s['source_sha256'] for s in sources})==19),'Unique owners; formal may share video SHA across distinct frame owners')
    require(completion['status']=='COMPLETE_DIRECT_BOX107_'+phase.upper()+'_RAW_NOT_QUALITY'
        and completion['model_role']==role and completion['phase']==phase
        and completion['GPU_registration']==registration_ref and completion['input_prepared']==reg['prepared']
        and completion['CPU_registration']==reg['CPU_registration'] and completion['input_acceptance']==reg['input_acceptance']
        and completion['training_completion']==reg['training_completion']
        and completion['adapter_weights']==reg['adapter_weights'] and completion['head_weights']==reg['head_weights']
        and completion['admitted_arm_names']==reg['admitted_arm_names'] and completion['hidden_transform']==math105.RECIPE['hidden_transform']
        and completion['expected_inputs']==completion['sources']==len(completion['entries'])==count,
        'Complete new readonly107 scope/input/model/weight identity')
    if phase=='formal':
        require(completion['official_source_count']==reg['official_source_count']==426
            and completion['affected_video_count']==reg['affected_video_count']
            and completion['affected_video_ids']==sorted(reg['affected_video_ids'])
            and reg['expected_affected_videos']==reg['affected_video_count']==len(reg['affected_video_ids'])
            and set(reg['affected_video_ids'])=={s['video_id'] for s in sources},'Whole426 with actual virtual observation count')
    events=load_events(completion['attempts']);offset=0;previous={};seen={};raw_owners={};predictions=[];new=internal=adopted=0
    for expected_row,record in zip(expected,completion['entries']):
        require(all(record[k]==expected_row[k] for k in ('id','source_id','source_sha256','input')),'Exact ordered accepted owner/input')
        request=load_json(record['input']);receipt=load_json(record['receipt']);source=owner[record['source_id']]
        require(all(request[k]==source[k]==receipt[k] for k in ('source_id','source_sha256','width','height'))
            and all(receipt[k]==record[k] for k in ('id','source_id','source_sha256','input'))
            and request['id']==record['id'] and receipt['model_role']==role
            and request['role']==receipt['role']==('confirm' if phase=='confirm19' else 'formal') and receipt['phase']==phase
            and receipt['input_signature']==request['input_signature'] and receipt['image_grid_thw']==request['image_grid_thw']
            and len(request['image_grid_thw'])==1 and request['reference_or_target_in_prompt'] is False
            and receipt['screen_reference_read'] is False and receipt['no_LM_generation'] is True
            and receipt['raw_dtype']=='torch.float32' and receipt['hidden_dimension']==4096 and receipt['head_dimension']==3
            and receipt['hidden_transform']==math105.RECIPE['hidden_transform']
            and all(receipt[k] is False for k in ('original_TIME_loaded','old_PAIR_loaded','old_CROP_loaded','old_UTILITY_loaded'))
            and not any(k in request for k in ('target','labels','candidate_ious','original_reference_xywh')),
            'Readonly one-source request/receipt role, F4, grid and original dimensions, no GT')
        require(receipt['adapter_weights']==reg['adapter_weights'] and receipt['head_weights']==reg['head_weights'],'Exact saved778-new weights')
        if phase=='formal':
            native={k:source[k] for k in ('video_id','native_ordinal','native_pts_exact','observation_index')}
            require(receipt['native_binding']==native and all(request[k]==v for k,v in native.items()),'Source/request/raw exact native frame ownership')
        else:require(receipt['native_binding']=={},'Historical19 cannot acquire official native ownership')
        key=exact_key(request,reg['adapter_weights'],reg['head_weights'])
        flags=[receipt[k] for k in ('actual_new_forward','internal_alias','external_alias')]
        require(all(type(f) is bool for f in flags) and sum(flags)==1,'Exclusive actual new/internal/external raw disposition')
        if receipt['actual_new_forward']:
            require(key not in seen and key not in external and receipt['alias_of'] is None
                and all(receipt[k] is None for k in ('adopted_from_acceptance','adopted_receipt','adopted_input','adopted_model_role')),
                'Never repeat successful exact raw or label new raw as adopted')
            actual=review105.validate_raw(load_tensor(receipt['raw_hidden']),load_tensor(receipt['raw_head']),receipt,head_state,source,
                adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],geometry=geometry)
            names=['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT'];new+=1
        elif receipt['external_alias']:
            old=external[key]
            require(receipt['alias_of'] is None and receipt['adopted_receipt']==old['receipt'] and receipt['adopted_from_acceptance']==old['acceptance']
                and receipt['adopted_model_role']==old['model_role'] and receipt['adopted_input']==old['input']
                and receipt['raw_hidden']==old['raw_hidden'] and receipt['raw_head']==old['raw_head'],'Only exact previously first-QAd raw adoption')
            actual=adopted_geometry(old,source,geometry);names=['ADOPTED_PREVIOUSLY_QA_RAW','ACCEPTED_NEW_ROLE_RESULT'];adopted+=1
        else:
            old=previous[receipt['alias_of']['path']]
            require(old['key']==key and receipt['alias_of']==old['receipt'] and receipt['raw_hidden']==old['raw_hidden']
                and receipt['raw_head']==old['raw_head']
                and all(receipt[k] is None for k in ('adopted_from_acceptance','adopted_receipt','adopted_input','adopted_model_role')),
                'Only earlier exact same-role/source/request/weights raw alias')
            actual=adopted_geometry(old,source,geometry);names=['ACCEPTED_NEW_ROLE_RESULT'];internal+=1
        decoded=np.asarray(receipt['decoded_xyw'],np.float64)
        rawkey=json.dumps([receipt['raw_hidden'],receipt['raw_head']],sort_keys=True)
        require(rawkey not in raw_owners or raw_owners[rawkey]==key,'A different source/input cannot be labelled with another owner raw pair')
        raw_owners[rawkey]=key
        require(decoded.shape==(3,) and bool(np.isfinite(decoded).all())
            and bool(np.all(np.abs(decoded-np.asarray(actual['continuous_xyw64']))<=1e-5*max(source['width'],source['height']))),
            'Every adopted or fresh continuous geometry matches its persisted successful raw')
        block=events[offset:offset+len(names)];offset+=len(names)
        require([e['event'] for e in block]==names and all(e['id']==record['id'] and e['model_role']==role for e in block)
            and block[-1]['receipt']==record['receipt'] and block[-1]['alias'] is (not receipt['actual_new_forward'])
            and block[-1]['internal_alias'] is receipt['internal_alias'] and block[-1]['external_alias'] is receipt['external_alias'],
            'Exact source/role raw-first/adopted event journal')
        if receipt['actual_new_forward']:
            require(block[0]['input']==record['input'] and block[1]['raw_hidden']==receipt['raw_hidden']
                and block[1]['raw_head']==receipt['raw_head'],'Raw hidden/head were persisted before acceptance')
        elif receipt['external_alias']:
            require(block[0]['adopted_from_acceptance']==receipt['adopted_from_acceptance']
                and block[0]['adopted_receipt']==receipt['adopted_receipt'] and block[0]['raw_hidden']==receipt['raw_hidden']
                and block[0]['raw_head']==receipt['raw_head'] and block[0]['adopted_input']==receipt['adopted_input'],
                'External-adoption journal binds actual prior first QA/input and both raw artifacts')
        prediction=dict(**record,raw_hidden=receipt['raw_hidden'],raw_head=receipt['raw_head'],
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],**actual)
        predictions.append(prediction);seen[key]=True;previous[record['receipt']['path']]=dict(prediction,key=key)
    require(offset==len(events) and new+internal+adopted==count
        and completion['actual_forward_calls']==new and completion['internal_aliases']==completion['aliases']==internal and completion['external_adopted']==adopted,
        'Actual complete new/internal/external counts; no input or raw replay masked')
    return dict(status='PASS_DIRECT_BOX109_CONFIRM19_FIRST_RAW_HEAD_CPU_QA' if phase=='confirm19' else FORMAL_QA,
        phase=phase,registration=registration_ref,training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],
        head_weights=reg['head_weights'],predictions=predictions,actual_new_forwards=new,internal_aliases=internal,external_adopted=adopted,
        model_calls=0,quality_established=False,prior_raw_first_QA_repeated=False)


def exact_overlay(base,sources,predictions,*,arm,clocks,geometry):
    """Independent native PTS/time/9:16/D-outside protection, no interpolation."""
    require(arm in ARMS and len(base)==426 and {r['video_id'] for r in base}=={str(i) for i in range(426)},'Complete protected426 baseline')
    result=copy.deepcopy(base);byvideo={r['video_id']:r for r in result};before={};locations={}
    for record in result:
        last=-1
        for row in record['predictions']:
            n=row['frame'];require(type(n) is int and n>last,'Original ordered unique native frame ordinals');last=n
            key=(record['video_id'],n);require(key not in before,'One protected native frame owner')
            before[key]=copy.deepcopy(row['bboxes']);locations[key]=row
    require(len(before)==123506,'Exact original40.47 time set')
    pred={p['source_id']:p for p in predictions};require(len(pred)==len(predictions)==len(sources)
        and set(pred)=={s['source_id'] for s in sources},'Exactly the accepted D raw/source owners')
    changed=[];seen=set()
    for source in sources:
        sid=source['source_id'];vid=source['video_id'];n=source['native_ordinal'];key=(vid,n);p=pred[sid]
        require(type(n) is int and n>=0 and sid=='official:%s:native:%d'%(vid,n)
            and key not in seen and key in locations and byvideo[vid]['targetRatioWH']==[16,9]
            and source['targetRatioWH']==[16,9] and type(source['observation_index']) is int
            and source['observation_index']>=0 and source['observation_index']%2==0,'Exact even-observation D intersects protected selected native16 frames')
        seen.add(key);clock=clocks[vid]
        require(clock['video_id']==vid and clock['source_sha256']==source['source_sha256']==p['source_sha256']
            and 0<=n<clock['n_frames'] and len(clock['normalized_exact_pts'])==clock['n_frames']
            and Fraction(source['native_pts_exact'])==Fraction(clock['normalized_exact_pts'][n]),'Exact same-source native PTS, never nominal FPS/nearest interpolation')
        require(source['baseline_box']==before[key] and source_baseline(source)['pool'][0]==before[key]
            and geometry.legal(before[key],source['width'],source['height']),'Read-only original B0 box at the exact D owner')
        box=p['native_boxes'][arm];require(geometry.legal(box,source['width'],source['height']),'Independent strict native output legality')
        locations[key]['bboxes']=list(box)
        if box!=before[key]:changed.append(dict(video_id=vid,native_ordinal=n,source_id=sid,source_sha256=source['source_sha256'],
            native_pts_exact=source['native_pts_exact'],old_box=before[key],box_xyw=list(box),arm=arm))
    after={(r['video_id'],p['frame']):p['bboxes'] for r in result for p in r['predictions']}
    require(after.keys()==before.keys() and len(after)==123506,'All original times, no deletion/addition')
    require(all(after[k]==v for k,v in before.items() if k not in seen),'Every D-outside original box preserved')
    require(all(after[k]==v for k,v in before.items() if byvideo[k[0]]['targetRatioWH']==[9,16]),'All9:16 original boxes preserved')
    require({k for k in after if after[k]!=before[k]}=={(r['video_id'],r['native_ordinal']) for r in changed},'Exact distinct spatial-only changes')
    return result,dict(status='PASS_DIRECT_BOX109_EXACT_NATIVE_SPATIAL_OVERLAY_ENGINEERING_ONLY',arm=arm,official_sources=426,
        native_frames=123506,added=0,removed=0,changed_boxes=len(changed),changed_video_sources=len({r['video_id'] for r in changed}),
        all_times_preserved=True,all_9_16_preserved=True,all_D_outside_preserved=True,new_interpolation=False,changes=changed)


def validate_scope_inputs(reg,prepared,gate,catalog):
    phase=reg['phase'];entries=prepared['inference_inputs'];sources=catalog['sources'];count=reg['expected_inputs']
    require(prepared['schema']==reg['prepared_schema']=='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106'
        and prepared['phase']==gate['phase']==phase and gate['status']==reg['input_acceptance_status']=='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA'
        and gate['prepared']==reg['prepared'] and gate['registration']==reg['CPU_registration']
        and gate['new_original_decode']==gate['old_source_processor_repeated']==gate['model_calls']==0,'Actual registered106 complete first input QA')
    require(prepared['execution_entries']==entries and prepared['adopted_success']=={}
        and prepared['sources']==gate['sources']==gate['inputs']==reg['expected_sources']==count==len(sources)==len(entries)
        and len({s['source_id'] for s in sources})==count and len({e['id'] for e in entries})==count
        and [e['source_id'] for e in entries]==[s['source_id'] for s in sources]
        and all(prepared[k]==reg[k] for k in ('training_completion','adapter_weights','head_weights','admitted_arm_names')),
        'Exact106 ordered source-only owner inventory/model/qualified arms')
    if phase=='confirm19':
        require(count==19 and len({s['source_sha256'] for s in sources})==19
            and set(reg['expected_source_ids'])=={s['source_id'] for s in sources}
            and all(s['source_id']!='gnmc:test:006575.jpeg' and s['role']=='confirm' and s.get('pool') for s in sources)
            and prepared['CPU_targets'] is not None,'Only successful original19 with original B0/pools; missing source excluded')
    else:
        require(prepared['CPU_targets'] is None and prepared['official_source_count']==gate['official_source_count']==reg['official_source_count']==426
            and prepared['affected_video_count']==gate['affected_video_count']==reg['affected_video_count']
            and prepared['selection']==reg['selection']=='OBS_INDEX_EVEN' and prepared['protected_baseline']==reg['protected_baseline']
            and len({s['video_id'] for s in sources})==reg['affected_video_count'],'Formal exact virtual observation scope and no GT')
    return entries,sources


def validate_formal_domain(domain,sources,reg):
    selected=domain['selected_D'];all_d=domain['all_D']
    require(domain['selection']=='OBS_INDEX_EVEN' and domain['protected_baseline_sha256']==BASELINE_SHA
        and domain['selected_D_sha256']==review84.digest(selected) and domain['all_D_sha256']==review84.digest(all_d)
        and domain['selected_D_count']==len(selected)==len(sources)==reg['expected_inputs']
        and domain['all_D_count']==len(all_d) and selected==sources
        and domain['official_source_count']==426 and domain['affected_video_count']==reg['affected_video_count']
        and domain['pilot_source_ids']==[s['source_id'] for s in sources[:32]]
        and domain['remaining_source_ids']==[s['source_id'] for s in sources[32:]],'Immutable complete106 domain/order/digests; no scope enlargement')
    identity=lambda s:tuple(s[k] for k in ('video_id','source_sha256','native_ordinal','observation_index','native_pts_exact'))
    full={identity(s) for s in all_d}
    require(len(full)==len(all_d) and len({identity(s) for s in selected})==len(selected)
        and {identity(s) for s in selected}=={identity(s) for s in all_d if s['observation_index']%2==0},
        'Even original observation indices applied before protected native16 intersection')


def validate_model_terminal(reg,registration_ref,trained,integrity,completion_ref):
    require(trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY' and trained['GPU_registration']==reg['frozen_GPU105_registration']
        and trained['completed_updates']==778 and trained['successful_micro']==trained['actual_training_forwards']==3112
        and trained['original_successful_updates']==20 and trained['original_successful_forwards']==88
        and trained['total_adopted_plus_new_updates']==798 and trained['optimizer_reset'] is True
        and trained['hidden_transform']==math105.RECIPE['hidden_transform'] and trained['recipe']==math105.RECIPE
        and trained['adapter_reload_all288_exact'] is True and trained['head_reload_all2_exact'] is True
        and trained['adapter_weights']==reg['adapter_weights'] and trained['head_weights']==reg['head_weights'],
        'Only real complete778-new preclamp direct-box final, never failed93/84/STAR1300/55')
    require(integrity['status']=='PASS_DIRECT_BOX107_READONLY_MODEL_BYTE_IDENTITY' and integrity['registration']==registration_ref
        and integrity['training_completion']==reg['training_completion'] and integrity['completion']==completion_ref
        and all(integrity[k] is True for k in ('adapter_all288_exact','head_all2_exact','all_weights_frozen','no_training'))
        and integrity['targets_read'] is False and integrity['inventory']==trained['inventory']
        and integrity['base_fingerprint']==trained['base_fingerprint']
        and integrity['inventory']['pipeline']==math105.PIPELINE and integrity['inventory']['resident']==math105.PHYSICAL,
        'Actual readonly107 final byte identity; raw completion alone is insufficient')


def _read(reference):return review84.read(review84.bound(reference))


def _events(reference):return [json.loads(s) for s in review84.bound(reference).read_text().splitlines() if s]


def _summary(actual):
    return {k:actual[k] for k in ('status','admitted_arm_names','training_completion','adapter_weights','head_weights')}


def validate_summary(summary,actual,result_ref):
    fields=set(_summary(actual))
    require(isinstance(summary,dict) and fields<=set(summary)<=fields|{'result'}
        and all(summary[k]==actual[k] for k in fields)
        and ('result' not in summary or summary['result']==result_ref),'Minimal GPU qualification summary must match the actual CPU result')


def validate_first_input_proofs(gate,expected,load_json):
    require(len(gate['first_QA'])==len(expected),'Complete original first-input QA inventory')
    for reference,entry in zip(gate['first_QA'],expected):
        proof=load_json(reference)
        require(proof['request']==entry['input'] and proof['compressed_four_tensor_roundtrip'] is True
            and proof['old_source_processor_repeated'] is False and proof['new_original_decode']==0,'Adopt actual lossless source-only first input proof without tensor/processor replay')


def _run(root,phase,registration):
    import torch
    torch.set_num_threads(2)
    reg=review84.read(registration);registration_ref=review84.ref(registration)
    require(reg['schema']=='FROZEN_DIRECT_BOX107_L2_SINGLE_IMAGE_INFERENCE' and reg['phase']==phase and reg['inference_admitted'] is True
        and review84.bound(reg['conditional_review_code'])==Path(__file__).resolve()
        and review84.bound(reg['frozen_review84_code'])==Path(review84.__file__).resolve()
        and review84.bound(reg['frozen_math84_code'])==Path(math84.__file__).resolve()
        and review84.bound(reg['frozen_review105_code'])==Path(review105.__file__).resolve()
        and review84.bound(reg['frozen_review93_code'])==Path(frozen_review93.__file__).resolve()
        and review84.bound(reg['frozen_math93_code'])==Path(frozen_math93.__file__).resolve()
        and review84.bound(reg['math_code'])==Path(math105.__file__).resolve(),'Actual registered109/frozen105 CPU replay and frozen93/84 dependency code')
    for key in ('GPU_code','frozen_GPU105_code','frozen_GPU105_registration','CPU_registration','preparation_code','geometry_code'):
        review84.bound(reg[key])
    native=_read(reg['native20_quality_result']);confirm=_read(reg['confirm19_quality_result']) if phase=='formal' else None
    arms=validate_qualification(reg,native,phase=phase,confirm=confirm)
    validate_summary(reg['native20_quality_summary'],native,reg['native20_quality_result'])
    if phase=='formal':validate_summary(reg['confirm19_quality_summary'],confirm,reg['confirm19_quality_result'])
    trained=_read(reg['training_completion']);prior=_read(native['output_acceptance'])
    require(prior['status']=='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA'
        and prior['registration']==reg['frozen_GPU105_registration'] and prior['completion']==trained['TRAINED_completion']
        and prior['training_completion']==reg['training_completion']
        and all(prior[k]==reg[k] for k in ('adapter_weights','head_weights')),'Adopt successful native20 first QA, do not repeat778-new checkpoint QA')
    prepared=_read(reg['prepared']);gate=_read(reg['input_acceptance']);catalog=_read(prepared['source_catalog'])
    require(review84.bound(reg['CPU_registration'])==root/('direct_box_scope_CPU_registration_106_'+phase+'.json')
        and review84.bound(reg['prepared'])==root/'direct_box_scope_inputs_106'/phase/'prepared.json'
        and review84.bound(reg['input_acceptance'])==root/'direct_box_scope_inputs_106'/phase/'input_acceptance.json',
        'Exact independent106 scope namespace; no latest-version search or old gate')
    cpu=_read(reg['CPU_registration'])
    require(cpu['preparation_code']==reg['preparation_code'] and cpu['phase']==phase and cpu['source_catalog']==prepared['source_catalog'],
        'Actual CPU106 registration/source catalog/compiler matches accepted input scope')
    expected,sources=validate_scope_inputs(reg,prepared,gate,catalog)
    validate_first_input_proofs(gate,expected,_read)
    original105=_read(reg['frozen_GPU105_registration'])
    require(original105['GPU_code']==reg['frozen_GPU105_code'] and original105['math_code']==reg['math_code']
        and original105['frozen_math84_code']==reg['frozen_math84_code'] and original105['frozen_math93_code']==reg['frozen_math93_code']
        and original105['review_code']==reg['frozen_review105_code'] and trained['original93_progress']==original105['original93_progress'],
        'Exact105 model/loss/normalization and committed93 ancestry')
    out=Path(reg['output_directory']).resolve()
    require(out==root/'direct_box_inference_107'/phase,'Exact readonly107 namespace')
    completion_ref=review84.ref(out/'completion.json');completion=_read(completion_ref);integrity_ref=review84.ref(out/'model_integrity.json')
    validate_model_terminal(reg,registration_ref,trained,_read(integrity_ref),completion_ref)
    resource_path=review84.RUN/'controller'/(reg['GPU_job']+'.resource.json');resource=review84.read(resource_path)
    ledger=[r for r in _events(review84.ref(WORK/'improvement_round1/gpu_ledger.jsonl')) if r.get('name')==reg['GPU_job']]
    require(ledger==[resource] and resource['status']=='completed' and resource['exit_code']==0,'Unique shared GPU job naturally completed/exit0')
    geometry=review84.module(reg['geometry_code'],'_direct_box109_original_geometry')
    head=torch.load(review84.bound(reg['head_weights']),map_location='cpu',weights_only=True);review84.validate_head(head)
    external=accepted_raw_index(reg['adopted_output_acceptances'],training_completion=reg['training_completion'],
        adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],load_json=_read,bind=review84.bound)
    accepted=review_raw_scope(completion,expected,sources,head,reg,registration_ref=registration_ref,load_json=_read,
        load_tensor=lambda r:torch.load(review84.bound(r),map_location='cpu',weights_only=True),load_events=_events,geometry=geometry,external=external)
    accepted.update(completion=completion_ref,input_prepared=reg['prepared'],input_acceptance=reg['input_acceptance'],
        resource=review84.ref(resource_path),model_integrity=integrity_ref,native20_quality_result=reg['native20_quality_result'],
        admitted_arm_names=arms,automatic_next_phase=False)
    qa_path=root/('direct_box_'+phase+'_output_acceptance_109.json')
    if phase=='confirm19':
        # The first original19 GT open follows a persisted, successful raw/head QA.
        save(qa_path,accepted)
        targets=_read(prepared['CPU_targets']);old=_read(reg['old_control_result70'])
        require(reg['old_control_result70']==native['control_result70'],'Same pre-existing70 control identity, no new fit/20 calibration')
        value=torch.load(review84.bound(old['value_weights']),map_location='cpu',weights_only=True)
        require(set(value)=={'weight','geometry_beta'} and tuple(value['geometry_beta'].shape)==(11,),'Frozen existing70 beta11')
        with np.load(review84.bound(old['old_gain_state']),allow_pickle=False) as f:rms47=f['RMS'].copy();beta47=f['GEOM11_beta'].copy()
        original33=_read(old['original_geometry_control'])
        with np.load(review84.bound(original33['coefficients']),allow_pickle=False) as f:beta33=f['beta'].copy()
        policy=review84.module(reg['policy_code'],'_direct_box109_original_geometry13')
        controls,controlproof=controls19(sources,targets['sources'],beta70=value['geometry_beta'].double().numpy(),rms47=rms47,
            beta47=beta47,beta33=beta33,geometry_features=policy.geometry_features)
        result=review84.evaluate_scope(sources,targets['sources'],accepted['predictions'],controls,scope='confirm19',arm_names=arms)
        for arm,report in result['arms'].items():report['status']=('PASS_' if report['quality']['admitted'] else 'STOP_')+'DIRECT_BOX106_'+arm+'_CONFIRM19'
        result.update(status=CONFIRM_PASS if result['admitted_arm_names'] else 'STOP_DIRECT_BOX106_CONFIRM19_REJECTED',
            registration=registration_ref,training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
            frozen_admitted_arm_names=arms,fixed_final_checkpoint=True,native20_quality_result=reg['native20_quality_result'],
            hidden_transform=math105.RECIPE['hidden_transform'],new_updates=778,total_adopted_plus_new_updates=798,
            output_acceptance=review84.ref(qa_path),CPU_targets=prepared['CPU_targets'],control_result70=reg['old_control_result70'],
            control_proof=controlproof,controls=controls,new_model_calls=0,new_fit=0,automatic_production=False)
        comparison=root/'direct_box_comparison_109_confirm19';comparison.mkdir(exist_ok=False);save(comparison/'result.json',result)
    else:
        require(reg['production_admitted'] is True and reg['whole426_preserved'] is True and reg['time_selection_unchanged'] is True
            and reg['selection']=='OBS_INDEX_EVEN','Explicit full spatial-only production admission')
        domain=_read(prepared['domain']);validate_formal_domain(domain,sources,reg)
        baseline=review84.bound(reg['protected_baseline']);require(reg['protected_baseline']['sha256']==BASELINE_SHA,'Protected original40.47 package identity')
        with zipfile.ZipFile(baseline) as z:
            require(z.testzip() is None and z.namelist()==['predictions.jsonl'],'Original protected baseline ZIP CRC/member')
            base=[json.loads(s) for s in z.read('predictions.jsonl').splitlines() if s]
        clocks={};clock_refs={}
        for source in sources:
            vid=source['video_id']
            if vid not in clocks:
                clocks[vid]=_read(source['clock']);clock_refs[vid]=source['clock']
                points=clocks[vid]['normalized_exact_pts']
                require(Fraction(points[0])==0 and all(Fraction(a)<Fraction(b) for a,b in zip(points,points[1:])),'Actual source clock has strict exact native PTS')
            require(source['clock']==clock_refs[vid],'One exact accepted native clock per video')
            require(review84.ref(review84.bound(source['clock']))==source['clock'],'Exact registered native clock')
        overlay_out=root/'direct_box_formal_overlay_109';overlay_out.mkdir(exist_ok=False);proofs={}
        for arm in arms:
            rows,proof=exact_overlay(base,sources,accepted['predictions'],arm=arm,clocks=clocks,geometry=geometry)
            prediction_path=overlay_out/(arm+'_predictions.jsonl')
            with prediction_path.open('x',encoding='utf-8') as f:
                for row in rows:f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
                f.flush();os.fsync(f.fileno())
            proof.update(registration=registration_ref,training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
                protected_baseline=reg['protected_baseline'],domain=prepared['domain'],raw_completion=completion_ref,predictions=review84.ref(prediction_path),
                package_created=False,quality_on_official_unknown=True)
            proof_path=overlay_out/(arm+'_proof.json');save(proof_path,proof);proofs[arm]=review84.ref(proof_path)
        accepted.update(confirm19_quality_result=reg['confirm19_quality_result'],domain=prepared['domain'],protected_baseline=reg['protected_baseline'],
            official_source_count=426,affected_video_count=reg['affected_video_count'],arm_overlays=proofs,all_times_preserved=True,
            all_9_16_preserved=True,all_D_outside_preserved=True,package_created=False,official_quality_established=False)
        save(qa_path,accepted)


def run(root,phase,registration):
    root=Path(root).resolve();registration=Path(registration).resolve()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and root.is_relative_to(WORK) and phase in ('confirm19','formal')
        and registration==root/('direct_box_inference_registration_107_'+phase+'.json'),'One explicit CPU-only109 review within authorized Linux root')
    # No entry/output mutation until model/scope admissions and actual inputs are checked.
    try:_run(root,phase,registration)
    except BaseException as error:
        failure=root/('direct_box_'+phase+'_review_failure_109.json')
        if not failure.exists():save(failure,dict(phase=phase,error=repr(error),traceback=traceback.format_exc(),
            preserve_all_success=True,automatic_retry=False,automatic_next_phase=False,model_calls=0,failure_is_not_empty=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['confirm19','formal'],required=True)
    p.add_argument('--registration',type=Path,required=True);a=p.parse_args();run(a.root,a.phase,a.registration)
