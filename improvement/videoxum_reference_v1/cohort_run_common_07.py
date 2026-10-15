"""Independent20-source run contracts; no legacy5-source paths or denominator."""
import json
import os
import sys
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path

from stage_common_04 import BASE, RUN, LEGACY, read, save, sha, utc, check_file

SOURCE_COUNT=20
GPU=BASE/'cohort_gpu_07'
REPLAY=BASE/'cohort_replay_07'
NAME='videoxum20_original_b_native64_20261013_v1'
LOCK=BASE/'cohort_source_lock_07.json'
ACCEPTANCE=BASE/'cohort_input_acceptance_07.json'


def append(path,value):
    with Path(path).open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n')
        stream.flush();os.fsync(stream.fileno())


def runtime():
    sys.path.insert(0,str(LEGACY))
    import runtime as original
    if Path(original.__file__).resolve()!=LEGACY/'runtime.py':
        raise ValueError('Unexpected original B runtime')
    return original


def inputs():
    admission=read(ACCEPTANCE)
    if (admission['status']!='PASS_INDEPENDENT_EFFECTIVE20_ACTUAL_CPU_INPUTS_BEFORE_B' or
        admission['registered_sources']!=20 or admission['accepted_sources']!=20 or
        admission['new_model_calls'] or admission['new_optimizer_updates'] or
        admission['cohort_completion_sha256']!=sha(BASE/'direct_cohort_06/completion.json')):
        raise ValueError('All20 actual native CPU input acceptance required')
    rows=[]
    for entry in admission['proofs']:
        proof=read(check_file(entry['proof_path'],entry['proof_sha256']))
        meta=read(check_file(proof['input_path'],proof['input_sha256']))
        check_file(meta['frame_array_path'],meta['frame_array_sha256'])
        if (proof['status']!='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' or not proof['CPU_only'] or
            proof['case_id']!=entry['case_id'] or proof['source_name']!=entry['source_name'] or
            proof['input_tokens']>16384 or proof['input_evidence']['physical_frames']!=64 or
            meta['case_id']!=entry['case_id'] or meta['source_name']!=entry['source_name'] or
            meta['reference_available_to_inference'] or meta['audio_observed'] or
            len(set(meta['source_frame_ordinals']))!=64 or len(meta['sample_exact_pts'])!=64 or
            proof['runtime_identity_sha256']!=admission['runtime_identity_sha256']):
            raise ValueError('Accepted original-B input identity/budget changed')
        rows.append((entry,proof,meta))
    if (len(rows)!=admission['accepted_windows'] or len({x[0]['case_id'] for x in rows})!=len(rows) or
        len({x[0]['source_name'] for x in rows})!=20):
        raise ValueError('Actual20-source/window denominator changed')
    complete=dict(bindings={'original_b_processor_runtime':admission['runtime_identity']})
    return admission,complete,rows


def verify_lock():
    lock=read(LOCK)
    if (lock['registered_sources']!=20 or lock['model_parameters']!=8782459120 or
        lock['optimizer_updates'] or lock['unique_gpu_name']!=NAME):
        raise ValueError('Independent original-B20 source lock scope changed')
    for path,digest in lock['files'].items():check_file(path,digest)
    return lock


def ranges(segments,points,origin):
    points=[F(p) for p in points];result=[]
    for first,last in segments:
        a,b=bisect_left(points,F(str(first))+origin),bisect_left(points,F(str(last))+origin)
        if not 0<=a<b<=len(points):raise ValueError('Positive model interval has no original native frame')
        result.append([a,b])
    return result


def resource_terminal():
    path=RUN/('controller/'+NAME+'.resource.json');value=read(path)
    matching=[json.loads(line) for line in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line)['name']==NAME]
    if matching!=[value] or value['status']!='completed' or value['exit_code']!=0:
        raise ValueError('Unique new GPU resource terminal differs from the shared ledger')
    return value,sha(path)
