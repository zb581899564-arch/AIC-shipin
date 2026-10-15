"""Explicit first positive-recipe confirmation authority; no old consensus gates."""
from fractions import Fraction as F
import importlib.util
import os
from pathlib import Path
import re
import sys

# Import lazily to keep generated model_common's helper re-exports acyclic.
def common():
    import model_common
    return model_common


def code_files():
    io = common()
    return {str(path.resolve()): io.sha(path) for path in Path(__file__).parent.glob('*.py')}


REGISTRATION_NAME = 'positive_fresh_recovery_registration_v2.json'


def registration(root, group='confirm'):
    io = common(); io.require(group == 'confirm', 'Fresh code supports only first confirmation')
    reg = io.read(root/REGISTRATION_NAME)
    io.require(reg['status'] == 'REGISTERED_POSITIVE_FIRST_FRESH_REMAINING_RECOVERY_V2' and reg['group'] == group and
        reg['model_parameters'] == io.MODEL_PARAMETERS and reg['optimizer_updates'] == 0 and
        reg['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and reg['reference_available_to_inference'] is False and
        reg['production_admitted'] is False, 'Explicit new same-model first-confirmation authority required')
    refs = ('protocol_ref', 'authorization_ref', 'development_registration_ref', 'dev_selection_ref',
            'dev_result_ref', 'source_registration_ref', 'reference_completion_ref')
    for key in refs:
        io.checked(reg[key]['path'], reg[key]['sha256'])
    protocol = io.read(reg['protocol_ref']['path']); selection = io.read(reg['dev_selection_ref']['path']); result = io.read(reg['dev_result_ref']['path'])
    io.require(protocol['candidate'] == 'OLD_EXPLICIT_KEEP_PLUS_POSITIVE_EVIDENCE_NEW_ADMISSION' and
        selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and selection['confirm_metrics_examined'] is False and
        selection['protocol_sha256'] == reg['protocol_ref']['sha256'] and selection['result_ref'] == reg['dev_result_ref'] and
        result['status'] == 'PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION' and result['group'] == 'dev' and
        len(result['cases']) == 4 and len(result['conditions']) == 8 and all(v is True for v in result['conditions'].values()) and
        result['bindings']['protocol_ref'] == reg['protocol_ref'] and
        result['bindings']['registration_ref'] == reg['development_registration_ref'],
        'Actual complete development PASS and frozen unchanged recipe required before first fresh work')
    expected_gates = dict(macro_paired_all_rater_duration_F1_delta_min='0', per_source_F1_delta_min='-1/100',
        macro_all_rater_recall_delta_min='1/100', macro_all_rater_precision_delta_min='0')
    io.require(all(F(protocol['quality_gates'][k]) == F(v) for k, v in expected_gates.items()) and
        protocol['quality_gates']['minimum_sources_with_real_new_native_frames'] == 2,
        'Same frozen eight scientific gates required, no fresh retuning')
    required = reg['required_files']
    io.require(set(code_files()) <= set(required) and all(required[name] == digest for name, digest in code_files().items()),
               'Every new implementation file must be frozen before CPU work')
    required_runtime = io.runtime_dependencies() | io.processor_assets() | {str(io.CONFIG), str(io.RUNTIME)}
    required_runtime.update(str(io.CV_CODE/name) for name in ('cv_contract.py', 'cv_tokens.py', 'cv_grammar.py'))
    io.require(required_runtime <= set(required), 'Complete exact original model/runtime/processor metadata closure required')
    for name, digest in required.items():
        io.checked(name, digest)
    for stage, maxcalls, seconds in (('B0', 48, 1800), ('VERIFY', 240, 2400), ('POSITIVE', 80, 1200)):
        budget = reg['gpu_budget'][stage]
        io.require(budget['max_actual_calls'] == maxcalls and budget['max_seconds'] == seconds and
            re.fullmatch('[A-Za-z0-9_.-]{1,100}', budget['gpu_job_name']), 'Exact fresh stage budgets and unique job identity required')
    io.require(Path(__file__).resolve().parent == root/'recovery_v2/code', 'Only separately frozen recovery_v2/code may execute')
    validate_remaining_recovery(root, reg)
    return reg


def checked_ref(value):
    return common().checked(value['path'], value['sha256'])


def validate_recovery_documents(original, reg, primary, failure, diagnosis):
    """Pure exact authority/provenance gate; no primary operation is repeated."""
    io = common()
    io.require(original['status'] == 'REGISTERED_POSITIVE_FIRST_FRESH_CONFIRM_V1' and
        reg['status'] == 'REGISTERED_POSITIVE_FIRST_FRESH_REMAINING_RECOVERY_V2', 'Explicit original/new recovery registrations required')
    immutable = ('group', 'protocol_ref', 'authorization_ref', 'development_registration_ref', 'dev_selection_ref',
        'dev_result_ref', 'source_registration_ref', 'reference_completion_ref', 'frozen_positive_code_dir',
        'capacity_contract', 'deadline', 'model_parameters', 'optimizer_updates', 'source_scope',
        'reference_available_to_inference', 'production_admitted')
    io.require(all(reg[key] == original[key] for key in immutable), 'Recovery must not change scientific/source/quality/runtime/expiry authority')
    for stage in ('B0', 'VERIFY', 'POSITIVE'):
        old, new = original['gpu_budget'][stage], reg['gpu_budget'][stage]
        io.require(old['max_actual_calls'] == new['max_actual_calls'] and old['max_seconds'] == new['max_seconds'] and
            old['gpu_job_name'] != new['gpu_job_name'] and new['gpu_job_name'].endswith('_20261015_v2'),
            'Only the unique never-started GPU job name changes; registered budgets stay fixed')
    io.require(primary['status'] == 'PASS_POSITIVE_FIRST_FRESH_NATIVE64_PRIMARY_INPUTS_NOT_GPU_ADMISSION' and
        primary['group'] == 'confirm' and primary['CPU_only'] is True and primary['CUDA_initialized'] is False and
        primary['actual_input_count'] == len(primary['entries']) == 28 and len(primary['sources']) == 4 and
        primary['primary_encode_calls_started'] == primary['primary_encode_calls_returned'] ==
        primary['actual_new_processor_encodes'] == 28 and primary['actual_new_RGB_decode_passes'] == 4 and
        primary['first_independent_input_replays_already_completed'] == primary['new_model_calls'] ==
        primary['new_optimizer_updates'] == primary['original_clock_measurements_repeated'] == 0,
        'Only the exact 28 successful primary inputs/four RGB sources with zero first input QA can be adopted')
    io.require(failure['stage'] == 'FIRST_ALL_NATIVE_INPUT_QA_PRE_GPU' and
        "first_input_qa" in failure['error'] and failure['preserve_all_raw_and_success'] is True and
        failure['no_automatic_resume'] is True and failure['production_admitted'] is False,
        'The retained original chain must fail before its first actual input-QA work')
    io.require(diagnosis['error'] == 'ROLE_ORDER_VS_SOURCE_GROUPED_COMPLETE_INPUT_ENTRY_ORDER' and
        diagnosis['actual_primary_completion_status'] == primary['status'] and diagnosis['actual_input_count'] == 28 and
        diagnosis['original_view_plan_contents_unchanged'] is True and
        diagnosis['complete_expected_source_grouped_order_matches'] is True and
        diagnosis['all_case_metadata_native_view_identity_matches'] is True and
        diagnosis['input_QA_output_directory_exists'] is False and diagnosis['input_QA_evidence_count'] == 0 and
        diagnosis['B0_gpu_output_directory_exists'] is False and
        diagnosis['complete_primary_encode_calls_started'] == diagnosis['complete_primary_encode_calls_returned'] == 28 and
        diagnosis['original_chain_failure'] == failure,
        'Explicit read-only diagnosis must identify only source-group entry order, not changed native plan')


def validate_remaining_recovery(root, reg):
    io = common(); required = reg['required_files']
    refs = dict(original_registration_ref=root/'positive_fresh_registration.json',
        original_chain_failure_ref=root/'confirm/chain_01/failure.json',
        primary_completion_ref=root/'confirm/inputs_01/completion.json',
        source_clocks_ref=root/'confirm/source_clocks.json', view_plan_ref=root/'confirm/view_plan.json')
    for key, expected in refs.items():
        io.require(checked_ref(reg[key]) == expected and required.get(str(expected)) == reg[key]['sha256'],
                   'Exact immutable remaining-recovery evidence required: '+key)
    diagnosis_path = checked_ref(reg['diagnosis_ref'])
    io.require(diagnosis_path.is_relative_to(root) and required.get(str(diagnosis_path)) == reg['diagnosis_ref']['sha256'],
               'New independent diagnosis must be frozen under the original fresh root')
    original = io.read(reg['original_registration_ref']['path'])
    primary = io.read(reg['primary_completion_ref']['path'])
    diagnosis = io.read(diagnosis_path)
    validate_recovery_documents(original, reg, primary, io.read(reg['original_chain_failure_ref']['path']), diagnosis)
    for name, digest in diagnosis['bindings'].items():
        io.require(required.get(name) == digest, 'Read-only pre-recovery diagnosis dependency must remain exact in new closure')
        io.checked(name, digest)
    io.require(primary['registration_sha256'] == reg['original_registration_ref']['sha256'] and
        primary['protocol_sha256'] == reg['protocol_ref']['sha256'] and
        primary['original_registration_sha256'] == reg['source_registration_ref']['sha256'],
        'The successful original primary completion must bind its original registration and unchanged source/protocol')
    io.require(set(original['required_files']) <= set(required) and
        all(required[name] == digest for name, digest in original['required_files'].items()),
        'Every original frozen implementation/source dependency must remain in recovery closure unchanged')
    old_codes = reg['original_code_files']
    expected = {str(path.resolve()) for path in (root/'code').glob('*.py')}
    io.require(expected and set(old_codes) == expected, 'Explicit complete original code closure required')
    for name, digest in old_codes.items():
        io.require(required.get(name) == digest, 'Original failed/successful code must remain frozen in new closure')
        io.checked(name, digest)
    # The successful primary closure and actual plan are immutable inputs;
    # signature/bit QA is still genuinely new and must run below on CPU.
    closure_path = root/'confirm/inputs_01/implementation_closure.json'
    io.require(required.get(str(closure_path)) == primary['implementation_closure_sha256'], 'Successful primary implementation closure must be explicitly adopted')
    io.checked(closure_path, primary['implementation_closure_sha256'])
    for name, digest in io.read(closure_path)['files'].items():
        io.require(required.get(name) == digest, 'Original successful primary dependency missing from new recovery closure')
    io.require(primary['source_clocks_path'] == reg['source_clocks_ref']['path'] and
        primary['source_clocks_sha256'] == reg['source_clocks_ref']['sha256'] and
        primary['view_plan_path'] == reg['view_plan_ref']['path'] and primary['view_plan_sha256'] == reg['view_plan_ref']['sha256'] and
        primary['reference_completion_path'] == reg['reference_completion_ref']['path'] and
        primary['reference_completion_sha256'] == reg['reference_completion_ref']['sha256'],
        'Successful primary source/plan/reference receipts cannot be replaced during recovery')


def validate_source_grouped_order(plan, entries, source_order):
    """Pure producer-order equality; never mutate or reorder successful entries.

    unique_view_plan is role-major, while the successful primary producer loops
    accepted sources first and filters original plan order within each source.
    """
    io = common(); views = plan['unique_views']
    io.require(len(source_order) == len(set(source_order)) == 4 and
        len(views) == len(entries) == plan['actual_input_count'] and
        len({v['case_id'] for v in views}) == len(views) and
        len({e['case_id'] for e in entries}) == len(entries) and
        {v['source_name'] for v in views} == set(source_order),
        'Exactly four sources and complete unique successful input/view identities required')
    expected = [view for name in source_order for view in views if view['source_name'] == name]
    io.require([(e['case_id'], e['source_name']) for e in entries] ==
        [(v['case_id'], v['source_name']) for v in expected],
        'Successful primary entries must retain original source order and plan order within each source')
    return [view['case_id'] for view in expected]


def first_remaining_launch(root, positive_root, reg):
    """One-time absence check; later registered stages may see their own success."""
    io = common(); validate_remaining_recovery(root, reg)
    absent = (root/'confirm/B0/input_qa_01', root/'cpu_acceptance_confirm.json',
        root/'source_lock_confirm_B0.json', root/'source_lock_confirm_VERIFY.json',
        root/'confirm/B0/gpu_01', root/'confirm/B0/replay_01', root/'confirm/VERIFY',
        root/'gpu_admission_confirm_B0.json', root/'gpu_admission_confirm_VERIFY.json',
        positive_root/'registration_confirm.json', positive_root/'confirm/POSITIVE',
        positive_root/'gpu_admission_confirm_POSITIVE.json', positive_root/'confirm/comparison_01')
    io.require(not any(path.exists() for path in absent), 'A first QA/model/admission already exists; cannot automatically repeat remaining work')
    for source in (io.read(reg['original_registration_ref']['path']), reg):
        for budget in source['gpu_budget'].values():
            io.require(not (io.RUN/'controller'/(budget['gpu_job_name']+'.resource.json')).exists(),
                       'An original/new GPU job already has terminal evidence; unsupported recovery')
    io.require(not (root/'confirm/B0/input_qa_01').exists(), 'First input QA must truly be unstarted')


def media_files(root, reg):
    """Read source IDs/byte/clock metadata; never annotation/reference labels."""
    io = common(); registry_path = checked_ref(reg['source_registration_ref']); registry = io.read(registry_path)
    complete_path = checked_ref(reg['reference_completion_ref']); complete = io.read(complete_path)
    io.require(registry_path == root/'media_registration.json' and complete_path == root/'reference_01/completion.json' and
        registry['schema'] == 'POSITIVE_FRESH_MEDIA_REGISTRATION_V1' and
        registry['status'] == 'REGISTERED_POSITIVE_FIRST_FRESH_MEDIA_NATIVE' and registry['group'] == 'confirm',
        'Only the exact new positive first-fresh source registration and completed stage may be adopted')
    io.require(complete['status'] == 'PASS_POSITIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU' and
        complete['group'] == 'confirm' and len(complete['accepted']) == 4 and
        complete['source_registration_ref'] == reg['source_registration_ref'] and
        complete['dev_selection_ref'] == reg['dev_selection_ref'] and complete['dev_result_ref'] == reg['dev_result_ref'],
        'Actual completed source stage must bind this actual passing dev and new source registration')
    files = dict(reg['required_files'])
    def add(path, digest=None):
        path = io.checked(path, digest); actual = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == actual, 'Frozen source/reference metadata changed')
        files[str(path)] = actual
        return path
    add(root/REGISTRATION_NAME); add(root/'positive_fresh_registration.json'); add(registry_path); add(complete_path)
    known = io.read(add(registry['known_exclusions_ref']['path'], registry['known_exclusions_ref']['sha256']))
    excluded = {value if value.startswith('v_') else 'v_'+value for value in known['youtube_ids']}
    candidates_ref = registry['source_candidates_ref']; add(candidates_ref['path'], candidates_ref['sha256'])
    candidates = io.read(candidates_ref['path'])
    io.require(registry['selection'] == candidates['selection'] and
        registry['ordered_engineering_reserves'] == candidates['ordered_engineering_reserves'],
        'Original pre-exposure source order and engineering-reserve order must remain exact')
    excluded.update(candidates['exclusions']['all_old_conservative_plus_acquired_IDs'])
    if 'old_exposed_and_reserved_ids' in registry:
        excluded.update(registry['old_exposed_and_reserved_ids'])
    known_bytes = set(known['known_media_sha256'])
    for ref in registry['prior_media_receipts']:
        known_bytes.add(io.read(add(ref['path'], ref['sha256']))['sha256'])
    # Bind author annotation bytes, but inference preparation never opens it.
    add(registry['annotation_file_ref']['path'], registry['annotation_file_ref']['sha256'])
    allowed = {row['video_id'] for row in registry['selection']+registry['ordered_engineering_reserves']}
    seen_ids, seen_bytes = set(), set()
    for row in complete['accepted']:
        vid, media = row['video_id'], row['media']; digest = media['sha256']
        io.require(vid in allowed and vid not in excluded and vid not in seen_ids and
            digest not in seen_bytes and digest not in known_bytes and row['group'] == media['group'] == 'confirm' and
            media['video_id'] == vid and media['known_ID_and_byte_separation'] is True,
            'New media ID/byte separation failed; no alternate source based on model or quality')
        seen_ids.add(vid); seen_bytes.add(digest)
        path = add(media['path'], digest)
        io.require(path.is_relative_to(complete_path.parent) and path.stat().st_size == media['bytes'], 'Actual media escaped completed source stage')
        for pathkey, shakey in (('clock_path', 'clock_sha256'), ('reference_path', 'reference_sha256')):
            io.require(add(row[pathkey], row[shakey]).is_relative_to(complete_path.parent), 'Clock/reference escaped source stage')
        for name in ('media_receipt.json', 'route.json'):
            add(path.parent/name)
    return files, complete


def input_QA(root, stage):
    io = common(); path = root/'confirm'/stage/'input_qa_01/completion.json'
    value = io.read(path)
    expected = 'PASS_FIRST_INDEPENDENT_FRESH_'+stage+'_INPUT_QA_PRE_GPU'
    io.require(value['status'] == expected and value['group'] == 'confirm' and value['CPU_only'] is True and
        value['CUDA_initialized'] is False and value['new_model_calls'] == 0 and len(value['proofs']) == value['calls'],
        'Entire first independent actual input QA required before '+stage+' GPU')
    return path, value


def verify_input_QA(root, case, entry, req, proof):
    io = common(); _, complete = input_QA(root, 'VERIFY')
    rows = {row['case_id']: row for row in complete['proofs']}
    io.require(case in rows and len(rows) == len(complete['proofs']), 'First VERIFY input-QA denominator differs')
    first = io.read(checked_ref(rows[case]['proof_ref']))
    io.require(first['status'] == 'PASS_FIRST_INDEPENDENT_FRESH_VERIFY_INPUT_QA_PRE_GPU' and
        first['input_sha256'] == entry['input_sha256'] and first['proof_sha256'] == entry['proof_sha256'] and
        first['input_evidence'] == proof['input_evidence'] == req['input_evidence'], 'First VERIFY input QA exact actual request/cache binding differs')
    return first


def admission(root, group, stage, cpu_path=None, lock_path=None):
    io = common(); reg = registration(root, group)
    io.require(stage in ('B0', 'VERIFY'), 'Only first fresh B0/conservative VERIFY use this namespace')
    gate_path = root/('gpu_admission_confirm_'+stage+'.json'); gate = io.read(gate_path)
    actual_cpu = root/'cpu_acceptance_confirm.json' if stage == 'B0' else root/'confirm/VERIFY/cpu_01/completion.json'
    actual_lock = root/('source_lock_confirm_'+stage+'.json')
    io.require(cpu_path is None or Path(cpu_path).resolve() == actual_cpu, 'CLI actual CPU receipt differs')
    io.require(lock_path is None or Path(lock_path).resolve() == actual_lock, 'CLI actual source lock differs')
    io.require(gate['status'] == io.ADMISSION_STATUS and gate['group'] == group and gate['stage'] == stage and
        gate['cpu_acceptance_path'] == str(actual_cpu) and gate['cpu_acceptance_sha256'] == io.sha(actual_cpu) and
        gate['source_lock_path'] == str(actual_lock) and gate['source_lock_sha256'] == io.sha(actual_lock) and
        gate['fresh_registration_sha256'] == io.sha(root/REGISTRATION_NAME) and
        gate['model_parameters'] == io.MODEL_PARAMETERS and gate['reference_available_to_inference'] is False and
        gate['production_admitted'] is False, 'New explicit first fresh input/source/GPU admission required')
    qa_path, qa = input_QA(root, stage)
    io.require(gate['first_input_QA_sha256'] == io.sha(qa_path), 'GPU admission must follow actual first independent input QA')
    files = io.validate_lock(actual_lock, set(code_files()) | set(reg['required_files']) | {str(actual_cpu), str(qa_path)})
    cpu = io.read(actual_cpu)
    io.require(cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and cpu['new_model_calls'] == cpu['new_optimizer_updates'] == 0 and
        gate['expected_input_count'] == len(cpu['entries']) == qa['calls'] <= reg['gpu_budget'][stage]['max_actual_calls'],
        'Complete unique all-input QA/call denominator required')
    return gate, cpu, files, gate_path, actual_cpu, actual_lock


def accepted_b0(root, group, cpu_path=None, lock_path=None):
    io = common(); gate, cpu, files, gate_path, cpu_path, lock_path = admission(root, group, 'B0', cpu_path, lock_path)
    io.require(cpu['status'] == io.CPU_STATUS and cpu['source_count'] == 4 and
        cpu['all_first_independent_inputs_completed_pre_GPU'] is True, 'All four-source B0 inputs independently verified before GPU')
    values = []
    runtime = io.runtime_only()
    for entry in cpu['entries']:
        proof = io.read(io.locked_ref(entry['proof_path'], entry['proof_sha256'], files))
        meta = io.read(io.locked_ref(entry['input_path'], entry['input_sha256'], files)); io.validate_native(meta)
        first = io.read(io.locked_ref(proof['first_input_QA_path'], proof['first_input_QA_sha256'], files))
        io.require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and
            first['status'] == 'PASS_FIRST_INDEPENDENT_FRESH_B0_INPUT_QA_PRE_GPU' and
            proof['input_evidence'] == first['input_evidence'] and proof['input_sha256'] == entry['input_sha256'] and
            proof['case_id'] == first['case_id'] == meta['case_id'] == entry['case_id'] and
            proof['CPU_only'] is True and proof['CUDA_initialized'] is False and
            meta['audio_observed'] is False and meta['reference_available_to_inference'] is False and
            meta['reference_labels_used_for_sampling'] is False,
            'Actual pre-GPU first independent B0 input evidence required')
        encoded = io.load_cache(io.locked_ref(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'], files))
        io.require(runtime.tensor_signature(encoded) == proof['input_evidence']['tensor_signature'] and
                   0 < int(encoded['input_ids'].shape[1]) == proof['input_tokens'] <= 16384, 'Accepted actual original cache changed')
        values.append((entry, proof, meta)); del encoded
    io.require(len({e['case_id'] for e, _, _ in values}) == len(values) and len({m['source_name'] for _, _, m in values}) == 4,
               'Complete unique four-source real input denominator required')
    return gate, cpu, files, values, gate_path, cpu_path, lock_path
