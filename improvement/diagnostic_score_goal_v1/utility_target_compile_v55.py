"""One new CPU target compilation, adopting successful31/44 input QA.

No media/tensor/processor/model reads. Old labels and evaluation remain intact.
Only this compiler/final CPU review read original human targets; GPU inputs
carry train gains but contain no development references.
"""
import argparse
from collections import Counter
import copy
import datetime as dt
import importlib.util
import math
import os
from pathlib import Path
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import bound, read, ref, require, save, utc


def module(reference, name):
    spec = importlib.util.spec_from_file_location(name, bound(reference))
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result; spec.loader.exec_module(result)
    return result


def compile_targets(old, plan, catalog, targets, gain, requests, geometry):
    require(plan['GT_used_for_input_or_pair_choice'] is False, 'Original label-free pair ownership')
    sources = {s['source_id']:s for s in catalog['sources']}
    labels = {s['source_id']:s for s in targets['sources']}
    train = {k:s for k,s in sources.items() if s['role']=='train'}
    screen = {k:s for k,s in sources.items() if s['role']=='screen'}
    require(len(train)==602 and len(screen)==20 and len(labels)==622, 'Original602/20 source scope')
    entries = {e['id']:e for e in gain['train_inputs']}
    cases = {c['id']:c for c in plan['cases']}
    require(len(entries)==len(requests)==2408 and len(gain['pair_index'])==1204, 'Exact accepted2408 ordered inputs')
    lookup={}
    for entry in entries.values():
        q=requests[entry['id']]; sid=q['source_id']; s=train[sid]
        a,b=q['candidate_indices']
        require(q['id']==entry['id'] and q['source_sha256']==entry['source_sha256']==s['source_sha256']
            and q['role']=='train' and q['boxes']==[s['pool'][a],s['pool'][b]]
            and q['reference_or_target_in_prompt'] is False, 'Adopted request source/box/label-free identity')
        key=(sid,a,b); require(key not in lookup,'Duplicate ordered input')
        lookup[key]=entry
    canonical={}
    for pair in gain['pair_index']:
        sid,a,b=pair['source_id'],pair['a'],pair['b']; s=train[sid]; y=labels[sid]
        require(a<b and [a,b] in plan['chosen_train_pairs'][sid]
            and y['source_sha256']==s['source_sha256'] and y['role']=='train'
            and y['reference_modified'] is False and y['baseline_index']==0, 'Unmodified original train target')
        require(lookup[sid,a,b]['id']==pair['first_id'] and lookup[sid,b,a]['id']==pair['reverse_id'],
            'Both opposite-order owners must be actual accepted inputs')
        delta=[float(v) for v in geometry(s['pool'][b],s['width'],s['height'])[1:12]
            -geometry(s['pool'][a],s['width'],s['height'])[1:12]]
        target=float(y['candidate_ious'][b])-float(y['candidate_ious'][a])
        require(math.isfinite(target) and -1<=target<=1 and all(map(math.isfinite,delta)), 'Finite signed IoU/geometry')
        canonical[sid,a,b]=(target,delta)
    require(len(canonical)==1204, 'Every unique pair compiled once')
    rows=[]; counts=Counter()
    for oldrow,p in zip(old['train_schedule'],plan['train_schedule']):
        c=cases[p['case_id']]; sid=oldrow['source_id']; a,b=c['a'],c['b']
        require(oldrow['id']==p['id'] and c['source_id']==sid and oldrow['input']==lookup[sid,a,b]['input'],
            'Original2000 order/input changed')
        key=(sid,min(a,b),max(a,b)); target,delta=canonical[key]; sign=1 if a<b else -1
        forward,reverse=lookup[sid,a,b],lookup[sid,b,a]
        rows.append(dict(id=oldrow['id'],source_id=sid,source_sha256=train[sid]['source_sha256'],a=a,b=b,
            unordered_pair=list(key[1:]),forward=copy.deepcopy(forward),reverse=copy.deepcopy(reverse),
            forward_id=forward['id'],reverse_id=reverse['id'],target=sign*target,
            geometry_delta11=[sign*v for v in delta]))
        counts[key]+=1
    require(len(rows)==2000 and set(counts)==set(canonical), 'Exact original draw support/order')
    for row in rows:row['draw_weight']=2000/(1204*counts[(row['source_id'],*row['unordered_pair'])])
    rms=math.sqrt(math.fsum(y*y for y,_ in canonical.values())/1204)
    require(rms>0,'Nonzero original train target RMS')
    train_catalog=dict(sources=[{k:copy.deepcopy(s[k]) for k in ('source_id','source_sha256','role','width','height','pool')}
        for s in train.values()],GT_included=False)
    dev=[]
    for sid,s in screen.items():
        y=labels[sid]
        require(s['original_BASE_observed'] is True and y['source_sha256']==s['source_sha256']
            and y['reference_modified'] is False and y['role']=='screen','Original observed BASE and screen reference')
        dev.append({k:copy.deepcopy(s[k]) for k in ('source_id','source_sha256','role','width','height','pool','baseline_box','original_BASE_observed')}
            | {k:copy.deepcopy(y[k]) for k in ('candidate_ious','baseline_index','reference_modified','original_reference_xywh')})
    return dict(schema='UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55',train_schedule=rows,screen_inputs=copy.deepcopy(old['screen_inputs']),
        train_target_RMS=rms,class_token_ids=copy.deepcopy(old['class_token_ids']),train_sources=602,
        train_unordered_pairs=1204,train_micro=2000,screen_sources=20,screen_GT_included=False),train_catalog,dev


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only target compiler')
    started=time.monotonic(); regpath=root/'utility_value_CPU_registration_55.json'; reg=read(regpath)
    require(reg['schema']=='UTILITY_VALUE_CPU_TARGET_COMPILATION_V55' and bound(reg['preparation_code'])==Path(__file__).resolve(),
        'Explicit new-purpose target compiler')
    require(reg['max_seconds']==900,'Fixed target-only CPU budget')
    out=root/'utility_value_inputs_55';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),registration=ref(regpath),new_tensor_preparation=0,new_decode=0,model_calls=0))
    try:
        original=read(bound(reg['old_prepared'])); gain=read(bound(reg['gain_prepared']))
        gate=read(bound(reg['gain_input_acceptance'])); oldgate=read(bound(reg['old_input_acceptance']))
        require(gate['status']=='PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA'
            and gate['prepared']==reg['gain_prepared'] and oldgate['status']=='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA'
            and oldgate['prepared']==reg['old_prepared'], 'Actual successful input QA adopted, never repeated')
        requests={e['id']:read(bound(e['input'])) for e in gain['train_inputs']}
        policy=module(reg['geometry_code'],'_utility55_geometry')
        prepared,catalog,dev=compile_targets(original,read(bound(reg['old_case_plan'])),read(bound(reg['old_catalog'])),
            read(bound(reg['original_targets'])),gain,requests,policy.geometry_features)
        mathmod=module(reg['math_code'],'_utility55_target_math');_,schedule_sha,proof=mathmod.validate_schedule(prepared)
        save(out/'train_source_catalog.json',catalog)
        save(out/'screen_sources_and_CPU_targets.json',dict(status='ORIGINAL_SCREEN20_CPU_REFERENCE_ONLY_V55',sources=dev,
            original_targets=reg['original_targets'],source_catalog=reg['old_catalog'],historical_not_blind=True))
        prepared.update(source_catalog=ref(out/'train_source_catalog.json'),screen_prepared=reg['old_prepared'],
            screen_input_acceptance=reg['old_input_acceptance'],schedule_sha256=schedule_sha)
        require(time.monotonic()-started<900 and dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),
            'CPU budget/deadline')
        save(out/'prepared.json',prepared)
        save(out/'input_acceptance.json',dict(status='PASS_UTILITY55_TRAIN_TARGETS_AND_ADOPTED_INPUTS_CPU',registration=ref(regpath),
            prepared=ref(out/'prepared.json'),adopted_gain_input_acceptance=reg['gain_input_acceptance'],
            adopted_screen_input_acceptance=reg['old_input_acceptance'],new_tensor_preparation=0,new_processor_calls=0,new_decode=0,
            new_GPU_calls=0,proof=proof,schedule_sha256=schedule_sha,elapsed_seconds=time.monotonic()-started,
            targets_in_development_GPU_inputs=False,GPU_admitted=False))
        print('UTILITY55_CPU_TARGETS_COMPLETE',proof,flush=True)
    except BaseException as e:
        save(out/'failure.json',dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),preserve_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
