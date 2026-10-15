"""New relative-deletion fresh input authority; old stage mechanics unchanged."""
from fractions import Fraction as F
from pathlib import Path
import re

ROOT = Path('/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1')
MEDIA_PASS = 'PASS_MIDNIGHT_PAIR_SHORT_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'


def common():
    import model_common
    return model_common


def code_files():
    io = common()
    return {str(path.resolve()): io.sha(path) for path in Path(__file__).parent.glob('*.py')}


def checked_ref(value):
    return common().checked(value['path'], value['sha256'])


def registration(root, group='confirm'):
    io = common(); root = Path(root).resolve()
    io.require(root == ROOT and Path(__file__).resolve().parent == root/'code' and group == 'confirm',
               'Exact independent relative-confirm code/root required')
    reg = io.read(root/'positive_fresh_registration.json')
    io.require(reg['status'] == 'REGISTERED_MIDNIGHT_PAIR_SHORT_FRESH_INPUTS_V1'
        and reg['group'] == group and reg['model_parameters'] == io.MODEL_PARAMETERS and reg['optimizer_updates'] == 0
        and reg['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and reg['reference_available_to_inference'] is False
        and reg['production_admitted'] is False, 'New external same-model relative-deletion input authority required')
    for key in ('protocol_ref', 'authorization_ref', 'dev_selection_ref', 'dev_result_ref',
                'source_registration_ref', 'source_candidates_ref', 'reference_completion_ref'):
        checked_ref(reg[key])
    from reference_common import validate_gates
    validate_gates(io.read(reg['protocol_ref']['path']))
    selection = io.read(reg['dev_selection_ref']['path']); result = io.read(reg['dev_result_ref']['path'])
    io.require(selection['schema'] == 'MIDNIGHT_DELETE_DEV_SELECTION_V1' and selection['selected_policies'] == ['PAIR_ONLY']
        and selection['confirm_metrics_examined_scope'] == 'THIS_NEW_SHORT_COHORT_ONLY'
        and selection['prior_confirm_metrics_examined'] is True and selection['old_confirm_result_unchanged'] is True
        and selection['protocol_ref'] == result['bindings']['protocol_ref'] == reg['protocol_ref']
        and selection['result_ref'] == reg['dev_result_ref'] and selection['confirm_metrics_examined'] is False
        and selection['passed_arms'] == result['passed_arms'] and any(selection['passed_arms'].values())
        and result['group'] == 'dev', 'Actual passing new relative development, never old no-change or ROLE PASS, required')
    required = reg['required_files']; own = code_files()
    io.require(set(own) <= set(required) and all(required[path] == digest for path, digest in own.items()),
               'Freeze the complete new CPU/B0/VERIFY implementation')
    io.require(io.runtime_dependencies() | io.processor_assets() | {str(io.CONFIG), str(io.RUNTIME)} <= set(required),
               'Original same-B model/runtime/processor asset closure must be frozen')
    for path, digest in required.items():
        io.checked(path, digest)
    for stage in ('B0', 'VERIFY'):
        budget = reg['gpu_budget'][stage]
        io.require(type(budget['max_actual_calls']) is int and 0 < budget['max_actual_calls'] <= 80
            and type(budget['max_seconds']) is int and 0 < budget['max_seconds'] <= 2400
            and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', budget['gpu_job_name']), 'Unique bounded new stage budget required')
    return reg


def media_files(root, reg):
    io = common(); root = Path(root).resolve(); files = dict(reg['required_files'])
    def add(path, digest=None):
        path = io.checked(path, digest); value = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == value, 'Changed previously frozen fresh source metadata')
        files[str(path)] = value
        return path
    add(root/'positive_fresh_registration.json')
    media_reg_path = add(reg['source_registration_ref']['path'], reg['source_registration_ref']['sha256'])
    media_reg = io.read(media_reg_path)
    candidates = io.read(add(reg['source_candidates_ref']['path'], reg['source_candidates_ref']['sha256']))
    complete_path = add(reg['reference_completion_ref']['path'], reg['reference_completion_ref']['sha256'])
    complete = io.read(complete_path)
    io.require(media_reg_path == root/'media_registration.json' and complete_path == root/'reference_01/completion.json'
        and media_reg['schema'] == 'MIDNIGHT_PAIR_SHORT_MEDIA_REGISTRATION_V1'
        and complete['status'] == MEDIA_PASS and complete['group'] == 'confirm' and len(complete['accepted']) == 4
        and complete['source_registration_ref'] == reg['source_registration_ref']
        and complete['source_candidates_ref'] == reg['source_candidates_ref']
        and complete['protocol_ref'] == media_reg['protocol_ref'] == reg['protocol_ref']
        and complete['dev_selection_ref'] == reg['dev_selection_ref']
        and media_reg['development_selection_ref'] == reg['dev_selection_ref'], 'Actual new native/media stage must bind the exact passing relative development')
    allowed = {row['video_id'] for row in candidates['selection']+candidates['ordered_engineering_reserves']}
    excluded = set(candidates['protected_source_ids']); prohibited = set(candidates['prohibited_media_sha256'])
    known_ref = candidates['known_exclusions_ref']; known = io.read(add(known_ref['path'], known_ref['sha256']))
    io.require(set(known['known_media_sha256']) <= prohibited and
        {name if name.startswith('v_') else 'v_'+name for name in known['youtube_ids']} <= excluded,
        'Original training/test and known media isolation cannot be dropped')
    for value in candidates['prior26_media_receipts']:
        prior = io.read(add(value['path'], value['sha256']))
        io.require(prior['video_id'] in excluded and prior['sha256'] in prohibited, 'Recent actual acquired identity/bytes missing from exclusion')
    seen_names, seen_bytes = set(), set()
    for row in complete['accepted']:
        name, media = row['video_id'], row['media']
        io.require(name in allowed and name not in excluded and name not in seen_names
            and media['sha256'] not in prohibited and media['sha256'] not in seen_bytes
            and row['group'] == media['group'] == 'confirm' and media['video_id'] == name
            and media['known_ID_and_byte_separation'] is True, 'Actual first fresh ID/byte separation failed')
        seen_names.add(name); seen_bytes.add(media['sha256'])
        path = add(media['path'], media['sha256'])
        io.require(path.is_relative_to(complete_path.parent) and path.stat().st_size == media['bytes'], 'Actual new media escaped source stage or changed size')
        for pkey, skey in (('clock_path', 'clock_sha256'), ('reference_path', 'reference_sha256')):
            io.require(add(row[pkey], row[skey]).is_relative_to(complete_path.parent), 'Original clock/reference escaped actual source stage')
        add(path.parent/'media_receipt.json'); add(path.parent/'route.json')
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
        gate['fresh_registration_sha256'] == io.sha(root/'positive_fresh_registration.json') and
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


