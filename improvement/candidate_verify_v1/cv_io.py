"""Independent external VERIFY IO; original media is never opened here."""
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

from cv_contract import MODEL_PARAMETERS

HOME_ROOT = Path('/home/inspur/aic_video_work')
BASE = HOME_ROOT/'twenty_hour_five_20261014_v1/candidate_verify_v1'
RUN = HOME_ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
LEGACY = HOME_ROOT/'temporal_refinement_pilot_20261011/dev_01'
EXTERNAL_ROOTS = tuple(HOME_ROOT/name for name in (
    'human_reference_iteration_20261013_v1', 'duration_guard_iteration_20261013_v1',
    'videoxum_reference_iteration_20261013_v1', 'sparse_context_iteration_20261013_v1')) + (
        HOME_ROOT/'twenty_hour_five_20261014_v1/charades_boundary_v1',)
EXTERNAL_ROOTS += (HOME_ROOT/'twenty_hour_five_20261014_v1/charades_boundary_v2',)
TENSOR_CACHE_FORMAT = 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'


class MissingOriginalCacheError(ValueError):
    """Report to main; never silently re-decode/re-encode original evidence."""


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


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


def check_host(cpu=False):
    if socket.gethostname() != 'inspur-NP5570M5' or sys.platform != 'linux':
        raise ValueError('Real VERIFY execution is confined to the existing Linux host')
    if cpu and os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Only this CPU child must explicitly hide CUDA')
    if not cpu and os.environ.get('CUDA_VISIBLE_DEVICES') == '':
        raise ValueError('GPU child/parent CUDA visibility was incorrectly cleared')


def checked(ref, roots=EXTERNAL_ROOTS):
    path = Path(ref['path']).resolve()
    if not any(path.is_relative_to(Path(root).resolve()) for root in roots):
        raise ValueError('VERIFY evidence escaped its explicitly allowed external roots')
    if not path.is_file():
        raise MissingOriginalCacheError('Missing original accepted evidence/cache: '+str(path))
    if sha(path) != ref['sha256']:
        raise ValueError('Frozen VERIFY source/evidence changed: '+str(path))
    return path


def code_files():
    return {str(path.resolve()): sha(path) for path in sorted(Path(__file__).parent.glob('*.py'))}


def save_tensor_cache(path, encoded):
    """Copied lossless gzip helper; save prompt token tensors only here."""
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
        raise ValueError('Decoded cache is not an accepted CPU tensor dict')
    return encoded


def runtime_only():
    original_common = RUN/'b_score_aligned_package_v4/common.py'
    existing = sys.modules.get('common')
    if existing is not None and Path(existing.__file__).resolve() != original_common.resolve():
        raise ValueError('Unrelated common module shadows the frozen B runtime; stop')
    name = '_candidate_verify_original_b_runtime'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, LEGACY/'runtime.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    runtime = sys.modules[name]
    expected = dict(engine=RUN/'b_score_aligned_package_v4/engine.py',
        contracts=RUN/'b_score_aligned_package_v4/contracts.py',
        bw_video=RUN/'balanced_two_window_risk_v3/bw_video.py',
        exact_pts=RUN/'baseline_a_pts_v1/exact_pts.py',
        native_frames=RUN/'baseline_a_pts_v1/native_frames.py')
    for name, path in expected.items():
        if Path(sys.modules[name].__file__).resolve() != path.resolve():
            raise ValueError('Frozen B dependency was shadowed: '+name)
    files = {str(LEGACY/'runtime.py'): sha(LEGACY/'runtime.py')}
    files.update({str(path): sha(path) for path in expected.values()})
    return runtime, files


def cpu_processor():
    check_host(cpu=True)
    import torch
    import transformers
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    if torch.cuda.is_initialized():
        raise ValueError('CPU token preparation initialized CUDA')
    runtime, files = runtime_only()
    config_path = RUN/'b_score_aligned_package_v4/config.json'
    model_dir = Path(read(config_path)['model_dir'])
    assets = {str(path): sha(path) for path in sorted(model_dir.iterdir())
              if path.is_file() and path.suffix in ('.json', '.txt', '.jinja')}
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    return runtime, processor, dict(runtime_files=files, processor_assets=assets,
        original_config_sha256=sha(config_path), torch_version=torch.__version__,
        transformers_version=transformers.__version__, vision_processor_calls=0)


def model_identity(identity):
    if (identity['logical_parameters'] != MODEL_PARAMETERS or identity['base']['parameters'] != 8767123696 or
            identity['base']['sha256'] != '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59' or
            identity['adapter']['sha256'] != '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23' or
            identity['adapter']['tensors'] != 288 or not identity['adapter']['actual_saved_values_equal'] or
            not identity['adapter']['adapter_enabled']):
        raise ValueError('Actual original B/time-adapter identity changed')


def registration():
    path = BASE/'registration.json'
    value = read(path)
    if (value['schema'] != 'CANDIDATE_VERIFY_V1' or
            value['status'] != 'FROZEN_EXTERNAL_ORIGINAL_B0_CANDIDATE_VERIFY' or
            value['source_scope'] != 'EXTERNAL_NONTEST_ONLY' or value['model_parameters'] != MODEL_PARAMETERS or
            value['new_optimizer_updates'] != 0 or not value['selection_frozen_before_verify_answers'] or
            value['actual_model_call_budget'] != len(value['events']) or not value['events'] or
            value['new_media_decode_admitted'] is not False or value['new_vision_processor_admitted'] is not False):
        raise ValueError('Only the frozen independent external cache-reuse protocol is supported')
    for key in ('protocol', 'official_rule_check'):
        checked(dict(path=value[key+'_path'], sha256=value[key+'_sha256']), roots=(BASE,))
    for filename, digest in value['required_files'].items():
        checked(dict(path=filename, sha256=digest), roots=(BASE, Path(__file__).parent, RUN, LEGACY, *EXTERNAL_ROOTS))
    return value, sha(path)


def admitted():
    reg, reg_sha = registration()
    admission = read(BASE/'gpu_admission.json')
    cpu = read(BASE/'cpu_01/completion.json')
    if (admission['status'] != 'PASS_INDEPENDENT_VERIFY_GPU_ADMISSION' or
            admission['registration_sha256'] != reg_sha or
            admission['cpu_completion_sha256'] != sha(BASE/'cpu_01/completion.json') or
            admission['actual_model_call_budget'] != len(cpu['proofs']) or
            len(cpu['proofs']) != reg['actual_model_call_budget'] or
            cpu['status'] != 'PASS_ALL_EXTERNAL_VERIFY_TOKEN_INPUTS_NOT_GPU_ADMISSION' or
            cpu['CPU_only'] is not True or cpu['CUDA_initialized'] is not False or
            cpu['new_model_calls'] != 0 or cpu['new_optimizer_updates'] != 0 or
            cpu['new_media_decodes'] != 0 or cpu['vision_processor_calls'] != 0 or
            cpu['bindings']['code_files'] != code_files()):
        raise ValueError('Actual complete new token inputs require main independent GPU admission')
    locked = admission['source_input_lock_files']
    for filename, digest in locked.items():
        checked(dict(path=filename, sha256=digest), roots=(BASE, Path(__file__).parent, RUN, LEGACY, *EXTERNAL_ROOTS))
    rows, required = [], {str(BASE/'cpu_01/completion.json'), str(BASE/'plan_01/requests.json'),
                          str(BASE/'registration.json'), reg['protocol_path'], reg['official_rule_check_path']}
    required.update(code_files())
    for entry in cpu['proofs']:
        proof = read(checked(dict(path=entry['proof_path'], sha256=entry['proof_sha256']), roots=(BASE,)))
        req = read(checked(dict(path=proof['input_path'], sha256=proof['input_sha256']), roots=(BASE,)))
        if (proof['request_id'] != entry['request_id'] or proof['bindings'] != cpu['bindings'] or
                proof['status'] != 'PASS_CPU_VERIFY_PROMPT_TOKENS_UNCHANGED_ORIGINAL_VISION' or
                proof['token_cache_format'] != TENSOR_CACHE_FORMAT or
                proof['CPU_only'] is not True or proof['CUDA_initialized'] is not False or
                proof['new_model_calls'] != 0 or proof['new_optimizer_updates'] != 0 or
                proof['vision_processor_calls'] != 0 or proof['new_media_decodes'] != 0 or
                req['reference_labels_read'] is not False or req['audio_observed'] is not False):
            raise ValueError('Actual accepted VERIFY input identity changed')
        required.update((entry['proof_path'], proof['input_path'], proof['token_cache_path'], proof['original_vision_cache_path']))
        required.update(ref['path'] for ref in req['original_evidence'].values())
        rows.append((entry, proof, req))
    if not required <= set(locked) or len({entry['request_id'] for entry, _, _ in rows}) != len(rows):
        raise ValueError('Complete unique VERIFY input file lock denominator failed')
    return reg, admission, cpu, rows


def resource_terminal(name):
    path = RUN/'controller'/(name+'.resource.json')
    resource = read(path)
    ledger = HOME_ROOT/'improvement_round1/gpu_ledger.jsonl'
    matches = [json.loads(line) for line in ledger.read_text().splitlines()
               if line.strip() and json.loads(line)['name'] == name]
    if matches != [resource] or resource['status'] != 'completed' or resource['exit_code'] != 0:
        raise ValueError('Unique VERIFY completed/exit0 resource disagrees with shared ledger')
    return resource, sha(path)
