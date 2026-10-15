"""Frozen same-B helpers for the first independent consensus confirmation.

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
MAIN_ROOT = HOME_ROOT/'recall_consensus_verify40_46_20261015_v1'
RUN = HOME_ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CONFIG = RUN/'b_score_aligned_package_v4/config.json'
RUNTIME = HOME_ROOT/'temporal_refinement_pilot_20261011/dev_01/runtime.py'
CV_CODE = HOME_ROOT/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'
MODEL_PARAMETERS = 8782459120
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
ADAPTER_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
PROMPT_SHA = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'
CACHE_FORMAT = 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'
ADMISSION_STATUS = 'PASS_INDEPENDENT_CONSENSUS_FRESH_GPU_ADMISSION'
CPU_STATUS = 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION'
PROTOCOL_SHA = 'd71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236'
CANDIDATE = 'TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION'
BASELINE_SHA = '86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'
JOBS = dict(B0='recall_consensus_fresh4_b0_20261015_v1',
            VERIFY='recall_consensus_fresh4_verify_20261015_v1')
CONDITIONS = ('full_group', 'macro_F1_not_lower', 'macro_recall_gain',
              'every_source_loss_within_gate', 'macro_precision_not_lower',
              'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources')


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
    require(path == MAIN_ROOT.resolve(), 'Only the independent consensus fresh root is admitted')
    return path


def checked(path, digest=None):
    path = Path(path).resolve()
    require(path.is_relative_to(HOME_ROOT) and path.is_file(), 'Missing or escaped admitted evidence: '+str(path))
    if digest is not None:
        require(sha(path) == digest, 'Frozen evidence changed: '+str(path))
    return path


def code_files():
    return {str((Path(__file__).parent/name).resolve()): sha(Path(__file__).parent/name)
            for name in ('model_common.py', 'pilot_runtime.py', 'pilot_verify.py', 'pilot_chain_fresh.py',
                         'prepare_fresh_inputs.py', 'admit_fresh_inputs.py', 'stage_io.py', 'overlap_plan.py',
                         'consensus.py', 'evaluate_development.py', 'evaluate_confirmation.py')}


def check_protocol(protocol):
    """The CPU development protocol is immutable; execution budgets live separately."""
    require(protocol['schema'] == 'RECALL_CONSENSUS_TWO_VIEW_SMALL_PILOT_V1' and
            protocol['candidate'] == CANDIDATE and protocol['baseline_zip_sha256'] == BASELINE_SHA and
            protocol['development_source_count'] == 8 and protocol['old_confirmation_is_exposed_development'] is True and
            protocol['fresh_confirmation_source_count'] == 4 and F(protocol['view_seconds']) == 15 and
            F(protocol['stride_seconds']) == F(15, 2) and protocol['support_count'] == 2 and
            protocol['threshold_search'] is False and protocol['new_segment_padding'] == 'NONE' and
            protocol['original_baseline_all_frames_boxes_and_params_retained'] is True and
            protocol['model_parameters'] == MODEL_PARAMETERS and protocol['optimizer_updates'] == 0 and
            protocol['production_before_fresh_confirmation_and_fixed_facts_pass'] is False,
            'The original frozen consensus2 development protocol changed')


def validate_fresh_development(protocol, selected, result, protocol_sha, result_sha):
    """Pure guard usable without processors, tensors or remote execution."""
    check_protocol(protocol)
    require(protocol_sha == PROTOCOL_SHA and selected.get('status') == 'FROZEN_CONSENSUS2_AFTER_DEV_PASS' and
            selected.get('candidate') == CANDIDATE and selected.get('protocol_sha256') == protocol_sha and
            selected.get('result_sha256') == result_sha and selected.get('fresh_confirm_metrics_examined') is False,
            'Exact unexamined fresh confirmation selection and original protocol are required')
    require(result.get('status') == 'PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM' and
            result.get('candidate') == CANDIDATE and result.get('protocol_sha256') == protocol_sha and
            isinstance(result.get('cases'), list) and len(result['cases']) == 8 and
            isinstance(result.get('conditions'), dict) and set(result['conditions']) == set(CONDITIONS) and
            all(result['conditions'][key] is True for key in CONDITIONS) and
            result.get('prior_failure_and_gates_unchanged') is True and result.get('production_admitted') is False,
            'Actual eight-source exposed development PASS with every original gate is required')


def validate_runtime_registration(registration):
    runtime, budget = registration['runtime'], registration['gpu_budget']
    require(runtime['native_frames'] == 64 and runtime['max_input_tokens'] == 16384 and
            runtime['max_output_tokens'] == 256 and F(runtime['baseline_window_seconds']) == 30 and
            F(runtime['candidate_window_seconds']) == 15 and F(runtime['candidate_stride_seconds']) == F(15, 2) and
            runtime['B0_prompt_sha256'] == PROMPT_SHA and runtime['grammar_allow_empty'] is True and
            runtime['model_parameters'] == MODEL_PARAMETERS and runtime['enabled_TIME_layers'] == 144 and
            runtime['base_sha256'] == BASE_SHA and runtime['adapter_sha256'] == ADAPTER_SHA,
            'Original native64 B0/TIME/token/grammar identity changed')
    require(budget == dict(confirm_B0_max_seconds=1800, confirm_VERIFY_max_seconds=2400,
                           per_group_max_B0_actual_calls=48, per_group_max_VERIFY_actual_calls=240),
            'Registered independent stage budgets changed')
    expires = dt.datetime.fromisoformat(registration['deadline'].replace('Z', '+00:00'))
    require(expires.tzinfo is not None, 'Explicit timezone-aware fresh execution deadline required')


def fresh_gate(root, group):
    root = root_path(root)
    require(group == 'confirm', 'Only the new first fresh confirmation group is admitted')
    registration_path = checked(root/'fresh_confirm_registration.json')
    registration = read(registration_path)
    require(registration['schema'] == 'RECALL_CONSENSUS_FRESH4_REFERENCE_REGISTRATION_V1' and
            registration['status'] == 'REGISTERED_FIRST_FRESH_CONFIRM_MEDIA_NATIVE_REFERENCE' and
            registration['group'] == group, 'Exact first fresh media/execution registration required')
    validate_runtime_registration(registration)
    files, required_code = registration['required_files'], registration['required_code_files']
    require(isinstance(files, dict) and files and isinstance(required_code, dict) and
            set(code_files()) <= set(required_code) <= set(files), 'Complete new implementation closure required')
    for filename, digest in files.items():
        require(Path(filename).is_absolute() and isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest),
                'Every explicit registered file requires an absolute path and SHA256')
        checked(filename, digest)
    require(all(files[name] == digest for name, digest in required_code.items()) and
            all(required_code[name] == digest for name, digest in code_files().items()),
            'Current new code differs from the first frozen registration')
    canonical = dict(protocol_ref=root/'protocol.json', authorization_ref=root/'USER_AUTHORIZATION.json',
                     development_selection_ref=root/'selection_before_fresh_confirmation.json',
                     development_result_ref=root/'development_01/result.json')
    paths = {}
    for key, expected in canonical.items():
        ref = registration[key]
        require(isinstance(ref, dict) and isinstance(ref.get('sha256'), str) and
                re.fullmatch(r'[0-9a-f]{64}', ref['sha256']), 'Explicit fresh gate reference SHA required: '+key)
        actual = locked_ref(ref['path'], ref['sha256'], files)
        require(actual == expected.resolve(), 'Fresh gate references a different root/stage: '+key)
        paths[key] = actual
    protocol, selected, result = (read(paths[key]) for key in
        ('protocol_ref', 'development_selection_ref', 'development_result_ref'))
    validate_fresh_development(protocol, selected, result, sha(paths['protocol_ref']), sha(paths['development_result_ref']))
    return dict(selection_path=str(paths['development_selection_ref']), selection_sha256=sha(paths['development_selection_ref']),
                result_path=str(paths['development_result_ref']), result_sha256=sha(paths['development_result_ref']),
                protocol_sha256=sha(paths['protocol_ref']), authorization_sha256=sha(paths['authorization_ref']),
                registration_path=str(registration_path), registration_sha256=sha(registration_path),
                registration=registration, runtime=registration['runtime'], gpu_budget=registration['gpu_budget'], files=files)


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


def admission(root, group, stage, cpu_path=None, lock_path=None):
    fresh = fresh_gate(root, group)
    require(stage in ('B0', 'VERIFY'), 'Explicit fresh stage required')
    path = root/('gpu_admission_'+group+'_'+stage+'.json')
    value = read(path)
    default_cpu = root/('cpu_acceptance_'+group+'.json') if stage == 'B0' else root/group/'VERIFY/cpu_01/completion.json'
    cpu_path = Path(cpu_path or default_cpu).resolve()
    lock_path = Path(lock_path or root/('source_lock_'+group+'_'+stage+'.json')).resolve()
    require(value['status'] == ADMISSION_STATUS and value['group'] == group and value['stage'] == stage,
            'Independent admission group/stage/status changed')
    require(value['gpu_job_name'] == JOBS[stage] and value['deadline'] == fresh['registration']['deadline'] and
            value['max_seconds'] == fresh['gpu_budget']['confirm_'+stage+'_max_seconds'] and
            all(value[key] == fresh[key] for key in ('protocol_sha256', 'authorization_sha256',
                'selection_sha256', 'result_sha256', 'registration_sha256')),
            'Fresh source/selection/protocol/unique-job/deadline binding changed')
    require(value['model_parameters'] == MODEL_PARAMETERS and value['optimizer_updates'] == 0 and
            value['reference_available_to_inference'] is False and value['source_scope'] == 'EXTERNAL_NONTEST_ONLY',
            'Original same-B/no-reference/external-nontest scope changed')
    require(type(value['expected_input_count']) is int and value['expected_input_count'] >= 0 and
            value['expected_input_count'] <= fresh['gpu_budget']['per_group_max_'+stage+'_actual_calls'] and
            value['expected_input_count'] > 0, 'Exact nonempty stage input denominator and fixed budget required')
    safe_id(value['gpu_job_name'])
    require(Path(value['cpu_acceptance_path']).resolve() == cpu_path and
            Path(value['source_lock_path']).resolve() == lock_path,
            'CLI CPU/lock path disagrees with independent admission')
    checked(cpu_path, value['cpu_acceptance_sha256'])
    checked(lock_path, value['source_lock_sha256'])
    required = (set(code_files()) | runtime_dependencies() | processor_assets() | set(fresh['files']) |
                {str(CONFIG), str(cpu_path), fresh['registration_path'], str(root/'reference_completion_confirm.json')})
    required.update(str(CV_CODE/name) for name in ('cv_contract.py', 'cv_grammar.py', 'cv_tokens.py'))
    files = validate_lock(lock_path, required)
    require(all(files[name] == digest for name, digest in fresh['files'].items()), 'Registered fresh files disagree with phase source lock')
    pointer = read(locked_ref(root/'reference_completion_confirm.json', value['reference_pointer_sha256'], files))
    completion = read(locked_ref(pointer['path'], pointer['sha256'], files))
    require(completion['group'] == group and completion['registration_sha256'] == fresh['registration_sha256'] and
            value['reference_completion_sha256'] == pointer['sha256'], 'First fresh native media completion binding changed')
    cpu = read(cpu_path)
    require(cpu['group'] == group and cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and
            cpu['new_model_calls'] == 0 and cpu['new_optimizer_updates'] == 0,
            'Complete actual CPU group acceptance required')
    if stage == 'B0':
        require(cpu['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and cpu['source_count'] == 4 and
                cpu['inherited_primary_caches'] == cpu['completed_first_independent_input_replays'] == 0 and
                cpu['registration_sha256'] == fresh['registration_sha256'] and cpu['protocol_sha256'] == fresh['protocol_sha256'] and
                cpu['selection_sha256'] == fresh['selection_sha256'] and cpu['development_result_sha256'] == fresh['result_sha256'],
                'Fresh-only four-source CPU acceptance and frozen development provenance required')
    return value, cpu, files, path, cpu_path, lock_path


def locked_ref(path, digest, files):
    path = checked(path, digest)
    require(files.get(str(path)) == digest, 'Evidence hash is absent/different in source lock: '+str(path))
    return path


def accepted_b0(root, group, cpu_path=None, lock_path=None):
    gate, cpu, files, gate_path, cpu_path, lock_path = admission(root, group, 'B0', cpu_path, lock_path)
    require(cpu['status'] == CPU_STATUS and len(cpu['entries']) == gate['expected_input_count'], 'Complete actual native64 CPU acceptance required')
    accepted = []
    for entry in cpu['entries']:
        case = safe_id(entry['case_id'])
        require(entry.get('group', group) == group, 'Cross-group CPU input')
        input_root = root/group/'inputs_01'
        require(Path(entry['input_path']).resolve().is_relative_to(input_root) and
                Path(entry['proof_path']).resolve().is_relative_to(input_root),
                'Fresh confirmation cannot inherit old input metadata or CPU proofs')
        proof = read(locked_ref(entry['proof_path'], entry['proof_sha256'], files))
        meta = read(locked_ref(entry['input_path'], entry['input_sha256'], files))
        require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and proof['CPU_only'] is True and
                proof['case_id'] == meta['case_id'] == case and proof['source_name'] == meta['source_name'], 'Actual original native64 proof identity changed')
        require(proof['group'] == meta['group'] == group and proof['CUDA_initialized'] is False and
                proof['input_evidence_origin'] == 'NEW_FRESH_CONSENSUS_CONFIRM_PRIMARY_ENCODE' and
                proof['first_independent_input_replay_pending'] is True and not proof.get('pre_GPU_first_input_replay_done') and
                Path(proof['encoded_tensor_path']).resolve().is_relative_to(input_root),
                'Only a new primary cache awaiting its first independent post-B0 input replay is admitted')
        require(proof['input_sha256'] == entry['input_sha256'] and proof['encoded_tensor_format'] == CACHE_FORMAT and
                type(proof['input_tokens']) is int and 0 < proof['input_tokens'] <= 16384 and
                proof['input_evidence']['physical_frames'] == 64 and
                proof['input_evidence']['prompt_sha256'] == PROMPT_SHA, 'Original prompt/input/cache budget changed')
        require(meta['audio_observed'] is False and meta['reference_available_to_inference'] is False and
                meta['window_role'] in ('baseline', 'overlap'), 'Explicit visual-only baseline/overlap input role required')
        view_roles = meta.get('view_roles', [meta['window_role']])
        require(view_roles and len(view_roles) == len(set(view_roles)) and
                set(view_roles) <= {'baseline', 'overlap'} and meta['window_role'] in view_roles,
                'Explicit actual-view role aliases are invalid')
        validate_native(meta)
        evidence = proof['input_evidence']
        require(evidence['case_id'] == case and evidence['source_sha256'] == meta['source_sha256'] and
                evidence['source_start'] == meta['window_start'] and
                evidence['source_frame_ordinals'] == meta['source_frame_ordinals'] and
                evidence['sample_exact_pts'] == meta['sample_exact_pts'] and evidence['pixel_sha256'] == meta['pixel_sha256'],
                'Native CPU proof/sample/source evidence disagrees with actual metadata')
        locked_ref(meta['source_path'], meta['source_sha256'], files)
        locked_ref(meta['frame_array_path'], meta['frame_array_sha256'], files)
        evidence_path = locked_ref(proof['input_evidence_path'], proof['input_evidence_sha256'], files)
        require(read(evidence_path) == evidence, 'Retained primary encode evidence changed or was not saved')
        locked_ref(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'], files)
        accepted.append((entry, proof, meta))
    require(len({row[0]['case_id'] for row in accepted}) == len(accepted), 'Duplicate accepted CPU case')
    require(len({row[2]['source_name'] for row in accepted}) == 4 and
            cpu['expected_input_count'] == len(accepted), 'Exactly four fresh sources and the actual view denominator required')
    # Inspect every actual lossless CPU cache before any model load/call; do not
    # discover an unaccepted later cache after earlier calls have already begun.
    runtime = runtime_only()
    for _, proof, _ in accepted:
        encoded = load_cache(proof['encoded_tensor_path'])
        require(runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'] and
                int(encoded['input_ids'].shape[1]) == proof['input_tokens'], 'Complete actual B0 cache admission differs')
        del encoded
    return gate, cpu, files, accepted, gate_path, cpu_path, lock_path


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
    name = '_consensus_fresh_original_b_runtime'
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
