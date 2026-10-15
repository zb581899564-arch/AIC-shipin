from new5_common import SOURCE_COUNT
"""Deferred original B dependencies and immutable external-run contracts."""
import datetime
import hashlib
import json
import os
import sys
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path

BASE = Path('/home/inspur/aic_video_work/duration_guard_iteration_20261013_v1')
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
LEGACY = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')
GPU = BASE/'new5_gpu_01'
REPLAY = BASE/'new5_replay_01'
NAME = 'duration_guard_reserved5_original_b_native64_20261013_v1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        f.flush()
        os.fsync(f.fileno())


def runtime():
    sys.path.insert(0, str(LEGACY))
    import runtime as original
    if Path(original.__file__).resolve() != LEGACY/'runtime.py':
        raise ValueError('Original B runtime resolved to another module')
    return original


def inputs():
    acceptance = read(BASE/'native_input_acceptance.json')
    complete = read(BASE/'processor_01/completion.json')
    reg = read(BASE/'new5_source_registration_01.json')
    if (acceptance['status'] != 'PASS_ALL_REGISTERED_HUMAN_NATIVE_INPUTS' or
            acceptance['registered_sources'] != SOURCE_COUNT or acceptance['accepted_sources'] != SOURCE_COUNT or
            acceptance['frame_mapping_failures'] != 0 or not acceptance['known_source_separation_pass'] or
            acceptance['new_optimizer_updates'] != 0 or
            acceptance['registration_sha256'] != sha(BASE/'new5_source_registration_01.json') or
            acceptance['evaluation_policy_sha256'] != sha(BASE/'EVALUATION_POLICY.md') or
            acceptance['mapping_contract_sha256'] != sha(BASE/'NATIVE_MAPPING_CONTRACT_V3.md') or
            acceptance['processor_completion_sha256'] != sha(BASE/'processor_01/completion.json') or
            complete['status'] != 'PASS_ALL_REGISTERED_CPU_NATIVE64_PROCESSOR_INPUTS' or
            complete['accepted_sources'] != SOURCE_COUNT or not complete['CPU_only'] or complete['CUDA_initialized']):
        raise ValueError('All registered actual CPU inputs must pass before B evaluation')
    proofs = complete['proofs']
    if (len(proofs) != acceptance['accepted_windows'] or len({p['case_id'] for p in proofs}) != len(proofs) or
            {p['source_name'] for p in proofs} != {row['source_name'] for row in reg['rows']}):
        raise ValueError('Actual reserved-five-source window denominator changed')
    rows = []
    for entry in proofs:
        if sha(entry['proof_path']) != entry['proof_sha256']:
            raise ValueError('Accepted actual CPU proof changed')
        proof = read(entry['proof_path'])
        if proof['bindings'] != complete['bindings'] or proof['input_tokens'] > 16384:
            raise ValueError('Actual CPU proof binding/budget changed')
        if sha(proof['input_path']) != proof['input_sha256']:
            raise ValueError('Accepted input metadata changed')
        meta = read(proof['input_path'])
        if (meta['case_id'] != entry['case_id'] or meta['source_name'] != entry['source_name'] or
                meta['reference_available_to_inference'] or meta['audio_observed'] or
                len(meta['source_frame_ordinals']) != 64):
            raise ValueError('Original visual native64 request changed')
        rows.append((entry, proof, meta))
    return acceptance, complete, rows


def verify_lock():
    path = BASE/'new5_source_lock_01.json'
    lock = read(path)
    if (lock['registered_sources'] != SOURCE_COUNT or lock['model_parameters'] != 8782459120 or
            lock['optimizer_updates'] != 0 or lock['unique_gpu_name'] != NAME):
        raise ValueError('New external source lock scope changed')
    for path, digest in lock['files'].items():
        if sha(path) != digest:
            raise ValueError('Frozen source/input/code changed: '+path)
    return lock


def ranges(segments, points, origin):
    points = [F(p) for p in points]
    result = []
    for first, last in segments:
        a, b = bisect_left(points, F(str(first))+origin), bisect_left(points, F(str(last))+origin)
        if not 0 <= a < b <= len(points):
            raise ValueError('Positive model interval has no actual native source frame')
        result.append([a, b])
    return result


def resource_terminal():
    path = RUN/('controller/'+NAME+'.resource.json')
    value = read(path)
    matching = [json.loads(line) for line in (Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')).read_text().splitlines()
                if line.strip() and json.loads(line)['name'] == NAME]
    if matching != [value] or value['status'] != 'completed' or value['exit_code'] != 0:
        raise ValueError('Unique actual GPU terminal does not agree with the shared ledger')
    return value, sha(path)
