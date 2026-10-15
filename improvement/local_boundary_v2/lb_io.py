"""Deferred immutable Linux-only runtime IO for local-boundary experiments."""
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

from lb_contract import MODEL_PARAMETERS

ROOT = Path('/home/inspur/aic_video_work')
EXPECTED_BASE = ROOT/'twenty_hour_five_20261014_v1/local_boundary_v2'
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
LEGACY = ROOT/'temporal_refinement_pilot_20261011/dev_01'
EXTERNAL_ROOTS = tuple(ROOT/name for name in (
    'human_reference_iteration_20261013_v1', 'duration_guard_iteration_20261013_v1',
    'videoxum_reference_iteration_20261013_v1', 'sparse_context_iteration_20261013_v1')) + (
        ROOT/'twenty_hour_five_20261014_v1/charades_boundary_v1',)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


TENSOR_CACHE_FORMAT = 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'


def save_tensor_cache(path, encoded):
    """Lossless compression only; never cast, normalize or alter tensor bytes."""
    import torch
    path = Path(path)
    if path.suffixes[-2:] != ['.pt', '.gz']:
        raise ValueError('Explicit .pt.gz lossless CPU tensor cache required')
    if not encoded or any(not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                          for value in encoded.values()):
        raise ValueError('Only original CPU tensors may enter the accepted cache')
    with path.open('xb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=1, mtime=0) as cache:
            torch.save(dict(encoded), cache)
        raw.flush()
        os.fsync(raw.fileno())


def load_tensor_cache(path):
    """Read gzip plus its CRC and restore original tensors without conversion."""
    import torch
    path = Path(path)
    if path.suffixes[-2:] != ['.pt', '.gz']:
        raise ValueError('Explicit .pt.gz lossless CPU tensor cache required')
    with path.open('rb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='rb') as cache:
            encoded = torch.load(cache, map_location='cpu', weights_only=True)
            cache.seek(0, os.SEEK_END)
    if not encoded or any(not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                          for value in encoded.values()):
        raise ValueError('Decoded cache is not the accepted original CPU tensor dict')
    return encoded


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def host(cpu=False):
    if socket.gethostname() != 'inspur-NP5570M5' or sys.platform != 'linux':
        raise ValueError('Research preparation/execution remains on the verified Linux host')
    if cpu and os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Only this CPU child must have CUDA_VISIBLE_DEVICES empty')
    if not cpu and os.environ.get('CUDA_VISIBLE_DEVICES') == '':
        raise ValueError('GPU child/parent CUDA visibility was incorrectly cleared')


def base_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve()) or any(path.is_relative_to(p.resolve()) for p in EXTERNAL_ROOTS):
        raise ValueError('New output must be an independent Linux directory')
    if path != EXPECTED_BASE.resolve():
        raise ValueError('Revision03 output must use its independent local_boundary_v2 root')
    return path


def checked_ref(ref, roots=EXTERNAL_ROOTS):
    path = Path(ref['path']).resolve()
    if not any(path.is_relative_to(Path(root).resolve()) for root in roots):
        raise ValueError('Evidence path escaped the explicitly accepted external roots')
    if sha(path) != ref['sha256']:
        raise ValueError('Frozen evidence changed: '+str(path))
    return path


def extract_clock(value, keys):
    if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys):
        raise ValueError('Explicit clock object keys required')
    for key in keys:
        value = value[key]
    return value


def own_code_files():
    return {str(p.resolve()): sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))}


def checked_required(registration, base):
    for path, digest in registration['required_files'].items():
        checked_ref(dict(path=path, sha256=digest), roots=(base, Path(__file__).parent, RUN))
    if registration['model_parameters'] != MODEL_PARAMETERS or registration['optimizer_updates'] != 0:
        raise ValueError('Same original B/zero optimizer scope changed')
    for name in ('protocol', 'official_rule_check'):
        path = checked_ref(dict(path=registration[name+'_path'],
            sha256=registration[name+'_sha256']), roots=(base,))
        if registration['required_files'].get(str(path)) != registration[name+'_sha256']:
            raise ValueError('Protocol/current official-rule receipt is missing from the required file lock')


def legacy_runtime():
    # Load only runtime.py under a unique name. Its intentionally original engine/
    # exact_pts imports retain their frozen paths and are checked below.
    name = '_local_boundary_v2_original_b_runtime'
    if name in sys.modules:
        runtime = sys.modules[name]
    else:
        spec = importlib.util.spec_from_file_location(name, LEGACY/'runtime.py')
        runtime = importlib.util.module_from_spec(spec)
        sys.modules[name] = runtime
        spec.loader.exec_module(runtime)
    if Path(runtime.__file__).resolve() != (LEGACY/'runtime.py').resolve():
        raise ValueError('Original B runtime path changed')
    expected = dict(engine=RUN/'b_score_aligned_package_v4/engine.py',
        contracts=RUN/'b_score_aligned_package_v4/contracts.py',
        bw_video=RUN/'balanced_two_window_risk_v3/bw_video.py',
        exact_pts=RUN/'baseline_a_pts_v1/exact_pts.py',
        native_frames=RUN/'baseline_a_pts_v1/native_frames.py')
    for name, path in expected.items():
        if Path(sys.modules[name].__file__).resolve() != path.resolve():
            raise ValueError('Original dependency unexpectedly shadowed: '+name)
    files = {str(LEGACY/'runtime.py'): sha(LEGACY/'runtime.py')}
    files.update({str(path): sha(path) for path in expected.values()})
    return runtime, files


def cpu_runtime():
    host(cpu=True)
    import torch
    import transformers
    if torch.cuda.is_initialized():
        raise ValueError('CPU-only child initialized CUDA')
    runtime, files = legacy_runtime()
    config = RUN/'b_score_aligned_package_v4/config.json'
    model_dir = Path(read(config)['model_dir'])
    assets = {str(p): sha(p) for p in sorted(model_dir.iterdir())
              if p.is_file() and p.suffix in ('.json', '.txt', '.jinja')}
    if not assets:
        raise ValueError('Existing local original processor/tokenizer assets missing')
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    return runtime, processor, dict(runtime_files=files, processor_assets=assets,
        original_config_sha256=sha(config), torch_version=torch.__version__,
        transformers_version=transformers.__version__)


def verify_model(model, identity):
    if (identity['logical_parameters'] != MODEL_PARAMETERS or
            identity['base']['parameters'] != 8767123696 or
            identity['base']['sha256'] != '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' or
            identity['adapter']['sha256'] != '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23' or
            identity['adapter']['tensors'] != 288 or
            not identity['adapter']['actual_saved_values_equal'] or
            not identity['adapter']['adapter_enabled'] or model.active_adapter != 'default'):
        raise ValueError('Actual original trained B model/adapter identity changed')


def terminal_resource(name):
    path = RUN/'controller'/(name+'.resource.json')
    resource = read(path)
    ledger = ROOT/'improvement_round1/gpu_ledger.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    matches = [r for r in rows if r['name'] == name]
    if matches != [resource] or resource['status'] != 'completed' or resource['exit_code'] != 0:
        raise ValueError('Unique completed GPU terminal does not agree with shared ledger')
    return resource, sha(path)


def admitted_inputs(base):
    """Main agent independently freezes/admit CPU inputs before this can run."""
    base = base_path(base)
    admission_path = base/'gpu_admission.json'
    admission = read(admission_path)
    cpu_path = base/'cpu_01/completion.json'
    cpu = read(cpu_path)
    plan = read(base/'plan_01/completion.json')
    registration = read(plan['registration_path'])
    if (admission['status'] != 'PASS_INDEPENDENT_LOCAL_BOUNDARY_GPU_ADMISSION' or
            admission['cpu_completion_sha256'] != sha(cpu_path) or
            admission['registration_sha256'] != plan['registration_sha256'] or
            admission['actual_model_call_budget'] != cpu['requests'] or
            admission['actual_model_call_budget'] != registration['actual_model_call_budget'] or
            admission['model_parameters'] != MODEL_PARAMETERS or admission['optimizer_updates'] != 0 or
            admission['original_successful_stages_reused'] is not True or
            cpu['status'] != 'PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION' or
            cpu['CPU_only'] is not True or cpu['CUDA_initialized'] is not False or
            cpu['new_model_calls'] != 0 or cpu['new_optimizer_updates'] != 0 or
            cpu['bindings']['own_code_files'] != own_code_files() or
            sha(plan['registration_path']) != plan['registration_sha256']):
        raise ValueError('Independent actual CPU input/source/runtime GPU admission missing/changed')
    checked_required(registration, base)
    lock = admission['source_input_lock_files']
    roots = (base, Path(__file__).parent, RUN, LEGACY, *EXTERNAL_ROOTS)
    for path, digest in lock.items():
        checked_ref(dict(path=path, sha256=digest), roots=roots)
    required = {str(cpu_path), str(base/'plan_01/completion.json'), str(base/'plan_01/events.json'),
                str(base/'plan_01/requests.json'), plan['registration_path']}
    rows = []
    for entry in cpu['proofs']:
        proof_path = checked_ref(dict(path=entry['proof_path'], sha256=entry['proof_sha256']), roots=(base,))
        proof = read(proof_path)
        meta_path = checked_ref(dict(path=proof['input_path'], sha256=proof['input_sha256']), roots=(base,))
        meta = read(meta_path)
        required.update((str(proof_path), str(meta_path), meta['frame_array_path'], proof['encoded_tensor_path']))
        if (proof['bindings'] != cpu['bindings'] or proof['request_id'] != entry['request_id'] or
                proof['input_sha256'] != entry['input_sha256'] or meta['request_id'] != entry['request_id'] or
                proof['encoded_tensor_format'] != TENSOR_CACHE_FORMAT or
                proof['encoded_tensor_compression_level'] != 1 or
                meta['reference_available_to_inference'] is not False or meta['audio_observed'] is not False or
                proof['new_model_calls'] != 0 or proof['new_optimizer_updates'] != 0 or
                not proof['status'].startswith('PASS_CPU_LOCAL_BOUNDARY_')):
            raise ValueError('Actual accepted CPU request/input evidence differs')
        rows.append((entry, proof, meta))
    if (len(rows) != cpu['requests'] or len({r[0]['request_id'] for r in rows}) != len(rows) or
            not required <= set(lock)):
        raise ValueError('Unique complete actual request/file lock denominator failed')
    return admission, cpu, rows
