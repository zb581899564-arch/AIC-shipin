"""Frozen same-B helpers for the separately admitted recall pilot.

This module performs no acquisition, launcher, retry or quality evaluation.
Heavy dependencies are imported only in explicitly invoked Linux stages.
"""
from bisect import bisect_left
import datetime as dt
from fractions import Fraction as F
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import sys

HOME_ROOT = Path('/home/inspur/aic_video_work')
RUN = HOME_ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CONFIG = RUN/'b_score_aligned_package_v4/config.json'
RUNTIME = HOME_ROOT/'temporal_refinement_pilot_20261011/dev_01/runtime.py'
CV_CODE = HOME_ROOT/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'
MODEL_PARAMETERS = 8782459120
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
ADAPTER_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
PROMPT_SHA = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'
CACHE_FORMAT = 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'
ADMISSION_STATUS = 'PASS_POSITIVE_FIRST_FRESH_STAGE_GPU_ADMISSION_V1'
CPU_STATUS = 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_id(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', value), 'Safe stable input identity required')
    require(value not in ('.', '..'), 'Input identity escaped output directory')
    return value


def host(cpu=False):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux', 'Actual execution requires existing Linux host')
    if cpu:
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only this CPU process must hide CUDA')
    else:
        require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'GPU parent must retain an explicit actual CUDA index')


def root_path(value):
    path = Path(value).resolve()
    require(path.is_relative_to(HOME_ROOT) and path != HOME_ROOT, 'Independent output root must remain under Linux project root')
    return path


def checked(path, digest=None):
    path = Path(path).resolve()
    require(path.is_relative_to(HOME_ROOT) and path.is_file(), 'Missing or escaped admitted evidence: '+str(path))
    if digest is not None:
        require(sha(path) == digest, 'Frozen evidence changed: '+str(path))
    return path


def runtime_dependencies():
    """Local implementation only; model weight directories are not scanned."""
    directories = (CONFIG.parent, RUN/'balanced_two_window_risk_v3',
                   RUN/'baseline_a_pts_v1', RUN/'baseline_a_pts_v1/vendor', RUN/'temporal_sft8b_v1')
    return {str(path.resolve()) for directory in directories for path in directory.glob('*.py')} | {str(RUNTIME)}


def validate_lock(path, required=()):
    value = read(path)
    files = value['files']
    require(isinstance(files, dict) and files, 'Nonempty explicit source/code lock required')
    require(set(map(str, required)) <= set(files), 'Actual dependency is missing from source lock')
    for filename, digest in files.items():
        require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest), 'Explicit SHA256 required')
        checked(filename, digest)
    return files


def processor_assets():
    directory = Path(read(CONFIG)['model_dir'])
    assets = {str(path.resolve()) for path in directory.iterdir()
              if path.is_file() and path.suffix in ('.json', '.txt', '.jinja')}
    require(assets, 'Existing local original processor assets missing')
    return assets


def locked_ref(path, digest, files):
    path = checked(path, digest)
    require(files.get(str(path)) == digest, 'Evidence hash is absent/different in source lock: '+str(path))
    return path


def validate_native(meta):
    points = list(map(F, meta['all_source_exact_pts']))
    end = F(meta['physical_end_exact'])
    lo, hi = F(meta['window_start']), F(meta['window_end'])
    ordinals, samples = meta['source_frame_ordinals'], list(map(F, meta['sample_exact_pts']))
    require(len(points) == meta['source_total_frames'] and points and points[0] == 0 and
            all(a < b for a, b in zip(points, points[1:])) and end > points[-1] and 0 <= lo < hi <= end and hi-lo <= 30,
            'Complete original clock/window is invalid')
    require(len(ordinals) == len(samples) == len(meta['pixel_sha256']) == 64 and len(set(ordinals)) == 64 and
            all(type(i) is int and 0 <= i < len(points) for i in ordinals) and
            all(a < b for a, b in zip(ordinals, ordinals[1:])) and
            samples == [points[i] for i in ordinals] and all(lo <= p < hi for p in samples),
            '64 distinct accepted native-frame samples required')


def native_ranges(segments, meta):
    validate_native(meta)
    points = list(map(F, meta['all_source_exact_pts']))
    lo, hi = F(meta['window_start']), F(meta['window_end'])
    result = []
    for first, last in segments:
        first, last = F(str(first)), F(str(last))
        require(0 <= first < last <= hi-lo, 'Parser segment escaped original window')
        a, b = bisect_left(points, lo+first), bisect_left(points, lo+last)
        require(a < b and list(range(a, b)) == [i for i, p in enumerate(points) if lo+first <= p < lo+last], 'Exact positive native membership differs')
        result.append([a, b])
    return result


def runtime_only():
    expected = dict(common=CONFIG.parent/'common.py', engine=CONFIG.parent/'engine.py',
                    contracts=CONFIG.parent/'contracts.py', constrained_json=CONFIG.parent/'constrained_json.py',
                    bw_video=RUN/'balanced_two_window_risk_v3/bw_video.py',
                    exact_pts=RUN/'baseline_a_pts_v1/exact_pts.py', native_frames=RUN/'baseline_a_pts_v1/native_frames.py')
    for name, path in expected.items():
        existing = sys.modules.get(name)
        require(existing is None or Path(existing.__file__).resolve() == path.resolve(), 'Frozen B dependency shadowed: '+name)
    name = '_recall_original_b_runtime'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, RUNTIME)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    runtime = sys.modules[name]
    # Import the exact grammar even if engine has not yet needed it.
    __import__('constrained_json')
    for name, path in expected.items():
        require(Path(sys.modules[name].__file__).resolve() == path.resolve(), 'Frozen B dependency resolved incorrectly: '+name)
    require(hashlib.sha256(runtime.EMPTY_PROMPT.encode()).hexdigest() == PROMPT_SHA, 'Original EMPTY_PROMPT changed')
    return runtime


def cv_modules():
    for name in ('cv_contract', 'cv_grammar', 'cv_tokens'):
        path = CV_CODE/(name+'.py')
        existing = sys.modules.get(name)
        require(existing is None or Path(existing.__file__).resolve() == path.resolve(), 'Frozen VERIFY dependency shadowed')
    sys.path.insert(0, str(CV_CODE))
    import cv_contract, cv_grammar, cv_tokens
    return cv_contract, cv_grammar, cv_tokens


def cpu_processor():
    host(cpu=True)
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    require(not torch.cuda.is_initialized(), 'CPU stage initialized CUDA')
    runtime = runtime_only()
    processor = AutoProcessor.from_pretrained(read(CONFIG)['model_dir'], local_files_only=True, min_pixels=131072, max_pixels=131072)
    return runtime, processor


def save_cache(path, encoded):
    import torch
    path = Path(path)
    require(path.suffixes[-2:] == ['.pt', '.gz'] and encoded and
            all(isinstance(t, torch.Tensor) and t.device.type == 'cpu' for t in encoded.values()), 'Only lossless CPU .pt.gz tensor dict allowed')
    with path.open('xb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=1, mtime=0) as cache:
            torch.save(dict(encoded), cache)
        raw.flush()
        os.fsync(raw.fileno())


def load_cache(path):
    import torch
    require(Path(path).suffixes[-2:] == ['.pt', '.gz'], 'Explicit lossless .pt.gz cache required')
    with Path(path).open('rb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='rb') as cache:
            encoded = torch.load(cache, map_location='cpu', weights_only=True)
            cache.seek(0, os.SEEK_END)
    require(encoded and all(isinstance(t, torch.Tensor) and t.device.type == 'cpu' for t in encoded.values()), 'Cache is not an actual CPU tensor dict')
    return encoded


def verify_model(model, identity):
    verify_identity(identity)
    require(model.active_adapter == 'default', 'Original TIME adapter selection changed')
    enabled_layers(model)


def verify_identity(identity):
    require(identity['logical_parameters'] == MODEL_PARAMETERS and identity['base']['parameters'] == 8767123696 and
            identity['base']['sha256'] == BASE_SHA and identity['adapter']['sha256'] == ADAPTER_SHA and
            identity['adapter']['tensors'] == 288 and identity['adapter']['actual_saved_values_equal'] is True and
            identity['adapter']['adapter_enabled'] is True, 'Actual original B/TIME adapter identity changed')


def enabled_layers(model):
    disabled = [bool(m.disable_adapters) for m in model.modules() if hasattr(m, 'disable_adapters') and hasattr(m, 'lora_A')]
    require(disabled == [False]*144 and not any(p.requires_grad for p in model.parameters()), 'All 144 original TIME LoRA layers must remain enabled/frozen')
    return disabled


def eos_ids(model):
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    require(eos and all(type(i) is int and i >= 0 for i in eos), 'Actual explicit EOS tokens required')
    return eos


def deadline(gate):
    expires = dt.datetime.fromisoformat(gate['deadline'].replace('Z', '+00:00'))
    require(expires.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < expires, 'No new job after registered deadline')


def gpu_reservation(gate):
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    require(read(HOME_ROOT/'improvement_round1/active_gpu_job.json')['name'] == gate['gpu_job_name'], 'Shared reservation belongs to another GPU job')


def terminal(gate):
    path = RUN/'controller'/(gate['gpu_job_name']+'.resource.json')
    value = read(path)
    matches = [r for r in rows(HOME_ROOT/'improvement_round1/gpu_ledger.jsonl') if r['name'] == gate['gpu_job_name']]
    require(matches == [value] and value['status'] == 'completed' and value['exit_code'] == 0, 'Unique natural completed/exit0 resource differs from shared ledger')
    return value, sha(path)


def output_tokens(raw, done=None):
    ids, scores = raw['output_token_ids'], raw['selected_token_scores']
    require(0 < len(ids) == len(scores) == raw['generated_score_count'] == raw['output_tokens'] <= 256 and
            all(type(i) is int and i >= 0 for i in ids) and
            all(type(s) in (float, int) and math.isfinite(s) for s in scores) and
            raw['adapter_disabled_layers'] == [False]*144 and raw['actual_model_call'] is True,
            'Actual output IDs/scores/adapter denominator differs')
    if done is not None:
        require(done['output_tokens'] == len(ids), 'Accepted output token denominator changed')
    return ids


def completed_job(out, gate, gate_path, count, stage):
    complete = read(out/'completion.json')
    require(complete['status'] == 'PASS_ALL_RECALL_'+stage+'_CALLS_NOT_QUALITY' and
            complete['group'] == gate['group'] and complete['calls'] == count and len(complete['entries']) == count and
            complete['attempts_sha256'] == sha(out/'attempts.jsonl') and
            complete['admission_sha256'] == sha(gate_path) and
            complete['model_identity_sha256'] == sha(out/'model_identity.json'), 'Actual complete unique model execution changed')
    verify_identity(read(out/'model_identity.json')['identity'])
    journal = rows(out/'attempts.jsonl')
    require(len(journal) == 2*count, 'Unique actual BEGIN/ACCEPTED denominator failed')
    by_id = {e['case_id']: e for e in complete['entries']}
    require(len(by_id) == count, 'Duplicate/missing accepted model case')
    for index, case in enumerate(by_id, 1):
        begun, accepted = journal[2*(index-1):2*index]
        require(begun['event'] == 'BEGIN' and accepted['event'] == 'ACCEPTED' and
                begun['call_id'] == accepted['call_id'] == index and begun['case_id'] == accepted['case_id'] == case and
                accepted['done_sha256'] == by_id[case]['done_sha256'] and accepted['done_path'] == by_id[case]['done_path'], 'Ordered actual model call journal differs')
    return complete, by_id


from fresh_registration import (code_files, registration, admission, accepted_b0)
