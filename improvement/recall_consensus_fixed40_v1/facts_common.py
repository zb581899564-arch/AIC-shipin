"""Frozen same-B helpers for the independent nine-source fixed-fact execution.

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
FACTS_ROOT = MAIN_ROOT/'fixed40_01'
EXISTING_MEDIA_ROOT = Path('/home/inspur/aic_video_data/videos')
RUN = HOME_ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CONFIG = RUN/'b_score_aligned_package_v4/config.json'
RUNTIME = HOME_ROOT/'temporal_refinement_pilot_20261011/dev_01/runtime.py'
CV_CODE = HOME_ROOT/'twenty_hour_five_20261014_v1/candidate_verify_v2/code'
MODEL_PARAMETERS = 8782459120
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
ADAPTER_SHA = '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
PROMPT_SHA = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'
CACHE_FORMAT = 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'
ADMISSION_STATUS = 'PASS_INDEPENDENT_CONSENSUS_FIXED40_GPU_ADMISSION'
CPU_STATUS = 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION'
REGISTRATION_SCHEMA = 'RECALL_CONSENSUS_FIXED40_EXECUTION_REGISTRATION_V1'
REGISTRATION_STATUS = 'REGISTERED_CONSENSUS_FIXED40_AFTER_FRESH_CONFIRM_PASS'
SOURCE_COUNT = 9
INPUT_COUNT = 17
VERIFY_MAX_CALLS = 120
GPU_BUDGET = dict(B0_max_seconds=1800, VERIFY_max_seconds=2400,
                  max_B0_actual_calls=INPUT_COUNT, max_VERIFY_actual_calls=VERIFY_MAX_CALLS)
JOB_NAMES = dict(B0='recall_consensus_fixed40_b0_20261015_v1', VERIFY='recall_consensus_fixed40_verify_20261015_v1')
PROTOCOL_SHA = 'd71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236'
CANDIDATE = 'TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION'
CONDITIONS = ('full_group', 'macro_F1_not_lower', 'macro_recall_gain', 'every_source_loss_within_gate',
              'macro_precision_not_lower', 'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources')
FRESH_JOBS = dict(B0='recall_consensus_fresh4_b0_20261015_v2', VERIFY='recall_consensus_fresh4_verify_20261015_v2')


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
    require(path == FACTS_ROOT.resolve(), 'Only the independent consensus fixed40 root is admitted')
    return path


def checked(path, digest=None):
    path = Path(path).resolve()
    require((path.is_relative_to(HOME_ROOT) or (path.is_relative_to(EXISTING_MEDIA_ROOT) and digest is not None)) and
            path.is_file(), 'Missing or escaped admitted read-only evidence: '+str(path))
    if digest is not None:
        require(sha(path) == digest, 'Frozen evidence changed: '+str(path))
    return path


def code_files():
    return {str((Path(__file__).parent/name).resolve()): sha(Path(__file__).parent/name)
            for name in ('facts_common.py', 'facts_infer.py', 'facts_verify.py', 'facts_chain.py', 'facts_prepare.py', 'facts_admit.py', 'source_audit.py', 'facts_veto.py')}


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


def check_protocol(protocol):
    require(protocol['schema'] == 'RECALL_CONSENSUS_TWO_VIEW_SMALL_PILOT_V1' and
        protocol['candidate'] == CANDIDATE and protocol['model_parameters'] == MODEL_PARAMETERS and
        protocol['optimizer_updates'] == 0 and protocol['development_source_count'] == 8 and
        protocol['old_confirmation_is_exposed_development'] is True and protocol['fresh_confirmation_source_count'] == 4 and
        F(protocol['view_seconds']) == 15 and F(protocol['stride_seconds']) == F(15, 2) and protocol['support_count'] == 2 and
        protocol['new_segment_padding'] == 'NONE' and protocol['threshold_search'] is False and
        protocol['original_baseline_all_frames_boxes_and_params_retained'] is True and
        protocol['production_before_fresh_confirmation_and_fixed_facts_pass'] is False,
        'The original consensus2 protocol and protected baseline must remain unchanged')


def validate_runtime(runtime):
    require(runtime['native_frames'] == 64 and runtime['max_input_tokens'] == 16384 and runtime['max_output_tokens'] == 256 and
        F(runtime['baseline_window_seconds']) == 30 and F(runtime['candidate_window_seconds']) == 15 and
        F(runtime['candidate_stride_seconds']) == F(15, 2) and runtime['B0_prompt_sha256'] == PROMPT_SHA and
        runtime['grammar_allow_empty'] is True and runtime['model_parameters'] == MODEL_PARAMETERS and
        runtime['enabled_TIME_layers'] == 144 and runtime['base_sha256'] == BASE_SHA and runtime['adapter_sha256'] == ADAPTER_SHA,
        'Original native64 B0/TIME/prompt/grammar/token identity changed')


def validate_phase_results(protocol, development, confirmation):
    """Pure phase guard; old failed single-view confirmation is never a prerequisite."""
    check_protocol(protocol)
    for result, count, expected in (
        (development, 8, 'PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM'),
        (confirmation, 4, 'PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40')):
        require(result['status'] == expected and result['candidate'] == CANDIDATE and
            len(result['cases']) == count and len({row['video_id'] for row in result['cases']}) == count and
            set(result['conditions']) == set(CONDITIONS) and all(result['conditions'][key] is True for key in CONDITIONS) and
            result['production_admitted'] is False, 'Complete real consensus development and first fresh confirmation must pass every original gate')
    require(development['protocol_sha256'] == PROTOCOL_SHA and development['prior_failure_and_gates_unchanged'] is True and
            confirmation['bindings']['protocol_sha256'] == PROTOCOL_SHA and confirmation['prior_failed_gates_changed'] is False,
            'Original scientific failures or protocol identity changed')
    require({row['video_id'] for row in development['cases']}.isdisjoint(
            row['video_id'] for row in confirmation['cases']), 'Exposed development sources cannot be the fresh confirmation')


def confirmation_metadata_closure(main_root):
    """Read only small prior execution metadata; never reload tensors or repeat QA.

    This helper is also available to registration construction after a real
    fresh PASS. It returns the exact metadata files which must be SHA-locked.
    The shared append-only ledger is checked by row equality, never file-locked.
    """
    main_root = Path(main_root).resolve()
    require(main_root == MAIN_ROOT.resolve(), 'Wrong consensus parent evidence root')
    files = {}

    def add(path, digest=None):
        path = checked(path, digest)
        actual = sha(path)
        require(str(path) not in files or files[str(path)] == actual, 'Conflicting prior metadata reference')
        files[str(path)] = actual
        return path

    protocol_path = add(main_root/'protocol.json', PROTOCOL_SHA)
    protocol = read(protocol_path)
    development = read(add(main_root/'development_01/result.json'))
    comparison_path = add(main_root/'confirm/comparison_01/result.json')
    comparison = read(comparison_path)
    validate_phase_results(protocol, development, comparison)
    original_path = add(main_root/'fresh_confirm_registration.json')
    recovery_path = add(main_root/'fresh_recovery_registration_02.json')
    recovery = read(recovery_path)
    require(recovery['schema'] == 'RECALL_CONSENSUS_FRESH_RECOVERY_EXECUTION_V2' and
            recovery['status'] == 'REGISTERED_EXPLICIT_FIRST_INPUT_CAPACITY_RECOVERY' and
            recovery['original_registration_ref'] == dict(path=str(original_path), sha256=sha(original_path)),
            'Actual explicit fresh recovery/original registration binding changed')
    validate_runtime(recovery['runtime'])
    add(main_root/'USER_AUTHORIZATION.json', recovery['authorization_ref']['sha256'])
    selected_path = add(main_root/'selection_before_fresh_confirmation.json', recovery['development_selection_ref']['sha256'])
    selected = read(selected_path)
    require(selected['status'] == 'FROZEN_CONSENSUS2_AFTER_DEV_PASS' and selected['candidate'] == CANDIDATE and
            selected['protocol_sha256'] == PROTOCOL_SHA and selected['result_sha256'] == sha(main_root/'development_01/result.json') and
            selected['fresh_confirm_metrics_examined'] is False,
            'The original pre-confirmation rule freeze changed')
    cpu_path = add(main_root/'cpu_acceptance_confirm_v2.json', comparison['bindings']['cpu_acceptance_sha256'])
    cpu = read(cpu_path)
    require(cpu['status'] == CPU_STATUS and cpu['source_count'] == 4 and
            cpu['expected_input_count'] == len(cpu['entries']) and 0 < len(cpu['entries']) <= 48 and
            len({entry['case_id'] for entry in cpu['entries']}) == len(cpu['entries']) and
            cpu['registration_sha256'] == sha(recovery_path), 'Actual complete fresh CPU acceptance required')
    pointer_path = add(main_root/'reference_completion_confirm.json')
    pointer = read(pointer_path)
    media_path = add(pointer['path'], pointer['sha256'])
    media = read(media_path)
    require(media['status'] == 'PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU' and media['group'] == 'confirm' and
            len(media['accepted']) == 4 and media['registration_sha256'] == sha(original_path) and
            {row['video_id'] for row in media['accepted']} == {row['video_id'] for row in comparison['cases']} ==
            {entry['source_name'] for entry in cpu['entries']}, 'Original successful fresh media/source authority changed')
    export_path = add(main_root/'confirm/VERIFY/verification_export.json', comparison['bindings']['verification_export_sha256'])
    exported = read(export_path)
    require(exported['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY' and exported['events'],
            'Real fresh PASS requires the complete actual VERIFY decisions')
    chain_path = add(main_root/'confirm/chain_02/completion.json')
    chain = read(chain_path)
    require(chain['status'] == 'PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40' and chain['group'] == 'confirm' and
            chain['registration_sha256'] == sha(recovery_path) and chain['original_registration_sha256'] == sha(original_path) and
            chain['comparison_ref'] == dict(path=str(comparison_path), sha256=sha(comparison_path)) and
            chain['production_admitted'] is False and chain['no_fixed40_426_or_package_started'] is True and
            chain['successful_calls_or_QA_repeated'] is False, 'Actual unique recovery chain must naturally complete fresh PASS')
    require(comparison['bindings']['registration_sha256'] == sha(recovery_path) and
            comparison['bindings']['original_registration_sha256'] == sha(original_path) and
            comparison['bindings']['reference_completion_sha256'] == sha(media_path), 'Fresh comparison provenance changed')
    for stage in ('B0', 'VERIFY'):
        receipt = chain[stage]
        count = receipt['calls']
        maximum = 48 if stage == 'B0' else 240
        require(type(count) is int and 0 < count <= maximum, 'Actual fresh stage denominator required')
        stage_root = main_root/'confirm'/stage
        gate_path = add(receipt['admission_ref']['path'], receipt['admission_ref']['sha256'])
        require(gate_path == main_root/('gpu_admission_confirm_'+stage+'_v2.json'), 'Wrong fresh stage admission')
        gate = read(gate_path)
        require(gate['status'] == 'PASS_INDEPENDENT_CONSENSUS_RECOVERY_GPU_ADMISSION_V2' and
                gate['group'] == 'confirm' and gate['stage'] == stage and gate['expected_input_count'] == count and
                gate['gpu_job_name'] == FRESH_JOBS[stage] and gate['model_parameters'] == MODEL_PARAMETERS and
                gate['optimizer_updates'] == 0 and gate['registration_sha256'] == sha(recovery_path) and
                gate['original_registration_sha256'] == sha(original_path) and gate['protocol_sha256'] == PROTOCOL_SHA and
                gate['selection_sha256'] == sha(selected_path) and gate['result_sha256'] == sha(main_root/'development_01/result.json') and
                gate['authorization_sha256'] == recovery['authorization_ref']['sha256'] and
                gate['max_seconds'] == (1800 if stage == 'B0' else 2400), 'Actual fresh job/model/budget identity changed')
        terminal_value, terminal_sha = terminal(gate)
        resource_path = add(receipt['resource_ref']['path'], receipt['resource_ref']['sha256'])
        require(resource_path == RUN/'controller'/(FRESH_JOBS[stage]+'.resource.json') and
                terminal_sha == sha(resource_path) and receipt['resource'] == terminal_value,
                'Actual unique natural resource/ledger/charged receipt changed')
        source_lock_path = add(gate['source_lock_path'], gate['source_lock_sha256'])  # Metadata manifest only; no tensor reads.
        stage_cpu_path = add(gate['cpu_acceptance_path'], gate['cpu_acceptance_sha256'])
        require(source_lock_path == main_root/('source_lock_confirm_'+stage+'_v2.json') and
                stage_cpu_path == (cpu_path if stage == 'B0' else stage_root/'cpu_01/completion.json'),
                'Actual fresh source/CPU phase paths changed')
        stage_cpu = read(stage_cpu_path)
        complete_path = add(receipt['gpu_completion_ref']['path'], receipt['gpu_completion_ref']['sha256'])
        qa_path = add(receipt['first_QA_completion_ref']['path'], receipt['first_QA_completion_ref']['sha256'])
        require(complete_path == stage_root/'gpu_01/completion.json' and qa_path == stage_root/'replay_01/completion.json',
                'Fresh stage completion or first QA escaped its actual output')
        complete, qa = read(complete_path), read(qa_path)
        require(complete['status'] == 'PASS_ALL_RECALL_'+stage+'_CALLS_NOT_QUALITY' and complete['group'] == 'confirm' and
                complete['calls'] == len(complete['entries']) == count and complete['admission_sha256'] == sha(gate_path) and
                complete['model_parameters'] == MODEL_PARAMETERS and complete['new_optimizer_updates'] == 0,
                'Actual complete successful fresh model calls required')
        identity_path = add(stage_root/'gpu_01/model_identity.json', complete['model_identity_sha256'])
        verify_identity(read(identity_path)['identity'])
        journal_path = add(stage_root/'gpu_01/attempts.jsonl', complete['attempts_sha256'])
        journal = rows(journal_path)
        done_by_id = {row['case_id']: row for row in complete['entries']}
        qa_by_id = {row['case_id']: row for row in qa['proofs']}
        cpu_by_id = {row['case_id']: row for row in stage_cpu['entries']}
        require(len(journal) == 2*count and len(done_by_id) == len(qa_by_id) == len(cpu_by_id) == count and
                list(done_by_id) == list(cpu_by_id) and set(done_by_id) == set(qa_by_id) and
                qa['status'] == 'PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and
                qa['group'] == 'confirm' and qa['calls'] == len(qa['proofs']) == count and qa['CPU_only'] is True and qa['CUDA_initialized'] is False and
                qa['new_model_calls'] == 0 and qa['gpu_completion_sha256'] == sha(complete_path) and
                qa['resource_terminal_sha256'] == terminal_sha, 'Complete unique first fresh QA/call denominator required')
        for index, (case, entry) in enumerate(done_by_id.items(), 1):
            first, last = journal[2*(index-1):2*index]
            require(first['event'] == 'BEGIN' and last['event'] == 'ACCEPTED' and
                    first['case_id'] == last['case_id'] == case and first['call_id'] == last['call_id'] == index and
                    last['done_path'] == entry['done_path'] and last['done_sha256'] == entry['done_sha256'],
                    'Actual first fresh call journal must be unique and ordered')
            done_path = add(entry['done_path'], entry['done_sha256'])
            done = read(done_path)
            proof_path = add(qa_by_id[case]['proof_path'], qa_by_id[case]['proof_sha256'])
            proof = read(proof_path)
            raw_path = add(done['raw_path'], done['raw_sha256'])
            request_path = add(done_path.parent/'request.json', done['request_sha256'])
            raw, request = read(raw_path), read(request_path)
            expected_qa = ('PASS_INDEPENDENT_RECALL_B0_TENSOR_TOKEN_GRAMMAR_PARSER_NATIVE_REPLAY' if stage == 'B0' else
                           'PASS_INDEPENDENT_RECALL_VERIFY_TOKEN_RAW_GRAMMAR_NATIVE_REPLAY')
            require(done_path == stage_root/'gpu_01'/case/'done.json' and raw_path == done_path.parent/'raw.json' and
                    done['case_id'] == proof['case_id'] == case and proof['done_sha256'] == entry['done_sha256'] and
                    proof['status'] == expected_qa and proof['raw_sha256'] == done['raw_sha256'] and
                    proof['CPU_only'] is True and proof['new_model_calls'] == 0 and
                    raw['actual_model_call'] is True and raw['adapter_disabled_layers'] == [False]*144 and
                    raw['input_evidence'] == request['input_evidence'] == done['input_evidence'] and
                    request['CPU_proof_sha256'] == cpu_by_id[case]['proof_sha256'] and
                    request['input_sha256'] == cpu_by_id[case]['input_sha256'],
                    'Original first QA metadata does not bind the actual fresh output')
            add(cpu_by_id[case]['input_path'], cpu_by_id[case]['input_sha256'])
            add(cpu_by_id[case]['proof_path'], cpu_by_id[case]['proof_sha256'])
        if stage == 'B0':
            require(count == len(cpu['entries']) and sha(qa_path) == comparison['bindings']['first_B0_QA_sha256'],
                    'Actual first B0 QA differs from the scientific fresh comparison')
        else:
            require(count == len(exported['events']) and sha(qa_path) == exported['independent_replay_completion_sha256'],
                    'Actual first VERIFY QA differs from the complete decision export')
    return files


def registration(root):
    """Validate frozen phase/identity/code evidence without reading fact labels."""
    root = root_path(root)
    path = root/'registration.json'
    reg = read(path)
    require(reg['schema'] == REGISTRATION_SCHEMA and reg['status'] == REGISTRATION_STATUS and
            reg['group'] == 'facts' and reg['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and
            reg['source_count'] == SOURCE_COUNT and reg['unique_input_count'] == INPUT_COUNT and
            reg['model_parameters'] == MODEL_PARAMETERS and reg['optimizer_updates'] == 0,
            'Frozen real nine-source/seventeen-input fixed40 registration required')
    require(all(reg['gpu_budget'][key] == value for key, value in GPU_BUDGET.items()) and
            reg['model_identity']['base_sha256'] == BASE_SHA and reg['model_identity']['adapter_sha256'] == ADAPTER_SHA and
            reg['model_identity']['enabled_TIME_layers'] == 144,
            'Original weights/adapter and bounded stage budgets changed')
    expires = dt.datetime.fromisoformat(reg['deadline'].replace('Z', '+00:00'))
    require(expires.tzinfo is not None, 'Explicit registered deadline required; no old campaign deadline is inherited')
    files, implementation = reg['required_files'], reg['required_code_files']
    required = set(code_files()) | runtime_dependencies() | processor_assets() | {str(CONFIG)}
    required.update(str(CV_CODE/name) for name in ('cv_contract.py', 'cv_grammar.py', 'cv_tokens.py'))
    require(required <= set(files) and set(code_files()) <= set(implementation) and
            all(files.get(filename) == digest for filename, digest in implementation.items()),
            'Complete new implementation, original runtime/config/processor phase closure required')
    for filename, digest in files.items():
        require(Path(filename).is_absolute() and isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest),
                'Phase closure requires absolute paths and explicit lowercase SHA256; no missing digest bypass')
        checked(filename, digest)
    refs = {}
    canonical = dict(main_protocol_ref=root.parent/'protocol.json',
        authorization_ref=root.parent/'USER_AUTHORIZATION.json',
        dev_result_ref=root.parent/'development_01/result.json',
        selection_ref=root.parent/'selection_before_fresh_confirmation.json',
        confirm_result_ref=root.parent/'confirm/comparison_01/result.json',
        confirm_chain_completion_ref=root.parent/'confirm/chain_02/completion.json',
        fresh_recovery_registration_ref=root.parent/'fresh_recovery_registration_02.json',
        original_fresh_registration_ref=root.parent/'fresh_confirm_registration.json')
    for name in (*canonical, 'source_plan_ref', 'reference_ref', 'consensus_implementation_ref', 'merge_implementation_ref'):
        ref = reg[name]
        require(isinstance(ref['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', ref['sha256']), 'Explicit consensus phase/reference SHA256 required')
        refs[name] = locked_ref(ref['path'], ref['sha256'], files)
        if name in canonical:
            require(refs[name] == canonical[name].resolve(), 'Wrong prior consensus/fresh phase: '+name)
    require(refs['source_plan_ref'].is_relative_to(root), 'New fixed source plan escaped the independent facts root')
    require(reg['main_protocol_ref']['sha256'] == PROTOCOL_SHA, 'Only the frozen consensus2 protocol is admitted')
    protocol = read(refs['main_protocol_ref'])
    check_protocol(protocol)
    validate_runtime(reg['runtime'])
    require(reg['runtime'] == read(refs['fresh_recovery_registration_ref'])['runtime'], 'Fixed facts changed the successful fresh runtime')
    require(sha(refs['consensus_implementation_ref']) == protocol['code_sha256']['consensus.py'],
            'Facts must retain the exact pre-development consensus implementation')
    authorization = read(refs['authorization_ref'])
    require(isinstance(authorization, dict) and bool(authorization), 'Actual human authorization receipt is missing')
    validate_phase_results(protocol, read(refs['dev_result_ref']), read(refs['confirm_result_ref']))
    prior_metadata = confirmation_metadata_closure(root.parent)
    require(all(files.get(filename) == digest for filename, digest in prior_metadata.items()),
            'The complete actual fresh chain/model/first-QA/resource metadata must be frozen without reprocessing tensors')
    plan = read(refs['source_plan_ref'])
    require(all(plan[key] == reg[key] for key in ('scope', 'sources', 'views')) and
            len(reg['sources']) == SOURCE_COUNT and len(reg['views']) == INPUT_COUNT and
            len({view['case_id'] for view in reg['views']}) == INPUT_COUNT,
            'Source-audit frozen plan/registration denominator differs')
    return reg


def admission(root, group, stage, cpu_path=None, lock_path=None):
    require(group == 'facts' and stage in ('B0', 'VERIFY'), 'Explicit group/stage required')
    path = root/('gpu_admission_'+group+'_'+stage+'.json')
    value = read(path)
    reg = registration(root)
    default_cpu = root/('cpu_acceptance_'+group+'.json') if stage == 'B0' else root/group/'VERIFY/cpu_01/completion.json'
    cpu_path = Path(cpu_path or default_cpu).resolve()
    lock_path = Path(lock_path or root/('source_lock_'+group+'_'+stage+'.json')).resolve()
    require(value['status'] == ADMISSION_STATUS and value['group'] == group and value['stage'] == stage,
            'Independent admission group/stage/status changed')
    require(value['registration_path'] == str(root/'registration.json') and
            value['registration_sha256'] == sha(root/'registration.json') and
            value['deadline'] == reg['deadline'] and value['gpu_job_name'] == JOB_NAMES[stage],
            'Stage admission must bind this immutable fixed40 registration and unique job')
    require(value['model_parameters'] == MODEL_PARAMETERS and value['optimizer_updates'] == 0 and
            value['reference_available_to_inference'] is False and value['source_scope'] == 'EXTERNAL_NONTEST_ONLY',
            'Original same-B/no-reference/external-nontest scope changed')
    require(type(value['expected_input_count']) is int and value['expected_input_count'] >= 0 and
            (stage == 'VERIFY' or value['expected_input_count'] > 0), 'Exact stage input denominator required')
    require((stage == 'B0' and value['expected_input_count'] == INPUT_COUNT) or
            (stage == 'VERIFY' and value['expected_input_count'] <= VERIFY_MAX_CALLS), 'Fixed real stage-call budget exceeded')
    safe_id(value['gpu_job_name'])
    require(Path(value['cpu_acceptance_path']).resolve() == cpu_path and
            Path(value['source_lock_path']).resolve() == lock_path,
            'CLI CPU/lock path disagrees with independent admission')
    checked(cpu_path, value['cpu_acceptance_sha256'])
    checked(lock_path, value['source_lock_sha256'])
    required = set(reg['required_files']) | {str(root/'registration.json'), str(cpu_path)}
    if stage == 'VERIFY':
        required.update(str(CV_CODE/name) for name in ('cv_contract.py', 'cv_grammar.py', 'cv_tokens.py'))
    files = validate_lock(lock_path, required)
    cpu = read(cpu_path)
    require(cpu['group'] == group and cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and
            cpu['new_model_calls'] == 0 and cpu['new_optimizer_updates'] == 0,
            'Complete actual CPU group acceptance required')
    return value, cpu, files, path, cpu_path, lock_path


def locked_ref(path, digest, files):
    path = checked(path, digest)
    require(files.get(str(path)) == digest, 'Evidence hash is absent/different in source lock: '+str(path))
    return path


def accepted_b0(root, group, cpu_path=None, lock_path=None):
    gate, cpu, files, gate_path, cpu_path, lock_path = admission(root, group, 'B0', cpu_path, lock_path)
    require(cpu['status'] == CPU_STATUS and cpu['source_count'] == SOURCE_COUNT and
            cpu['expected_input_count'] == len(cpu['entries']) == gate['expected_input_count'] == INPUT_COUNT,
            'Complete actual nine-source/seventeen native64 CPU acceptance required')
    accepted = []
    views = {view['case_id']: view for view in read(root/'registration.json')['views']}
    for entry in cpu['entries']:
        case = safe_id(entry['case_id'])
        require(case in views, 'Actual CPU input is not one of the seventeen frozen source-grid views')
        view = views[case]
        require(entry.get('group', group) == group, 'Cross-group CPU input')
        proof = read(locked_ref(entry['proof_path'], entry['proof_sha256'], files))
        meta = read(locked_ref(entry['input_path'], entry['input_sha256'], files))
        require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and proof['CPU_only'] is True and
                proof['case_id'] == meta['case_id'] == case and proof['source_name'] == meta['source_name'], 'Actual original native64 proof identity changed')
        require(proof['input_evidence_origin'] == 'NEW_CONSENSUS_FIXED40_PRIMARY_ENCODE' and
                proof['first_independent_input_replay_pending'] is True and not proof.get('pre_GPU_first_input_replay_done') and
                Path(entry['input_path']).resolve().is_relative_to(root/'inputs_01') and
                Path(entry['proof_path']).resolve().is_relative_to(root/'inputs_01') and
                Path(proof['encoded_tensor_path']).resolve().is_relative_to(root/'inputs_01'),
                'Only new consensus fixed40 inputs awaiting their first actual independent QA are admitted')
        require(proof['input_sha256'] == entry['input_sha256'] and proof['encoded_tensor_format'] == CACHE_FORMAT and
                type(proof['input_tokens']) is int and 0 < proof['input_tokens'] <= 16384 and
                proof['input_evidence']['physical_frames'] == 64 and
                proof['input_evidence']['prompt_sha256'] == PROMPT_SHA, 'Original prompt/input/cache budget changed')
        require(meta['audio_observed'] is False and meta['reference_available_to_inference'] is False and
                meta['window_role'] == 'overlap' and meta['view_roles'] == ['overlap'],
                'Only fixed full-source-grid overlap views; no new baseline input is authorized')
        require(meta['fixed_case_id'] == view['fixed_case_id'] and meta['source_name'] == view['source_name'] and
                meta['source_sha256'] == view['source_sha256'] and meta['original_clock_sha256'] == view['source_clock_sha256'] and
                F(meta['window_start']) == F(view['window_start']) and F(meta['window_end']) == F(view['window_end']) and
                meta['source_frame_ordinals'] == view['source_frame_ordinals'] and
                list(map(F, meta['sample_exact_pts'])) == list(map(F, view['sample_exact_pts'])),
                'Actual original source-clock/native64/grid view differs from frozen registration')
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
        locked_ref(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'], files)
        accepted.append((entry, proof, meta))
    require(len({row[0]['case_id'] for row in accepted}) == len(accepted), 'Duplicate accepted CPU case')
    require({row[0]['case_id'] for row in accepted} == set(views), 'Incomplete registered seventeen-view CPU denominator')
    require(len({row[2]['source_name'] for row in accepted}) == SOURCE_COUNT,
            'Actual source denominator must be nine distinct frozen identities')
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
    name = '_fixed40_original_b_runtime'
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
    require(complete['status'] == 'PASS_ALL_FIXED40_'+stage+'_CALLS_NOT_QUALITY' and
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
