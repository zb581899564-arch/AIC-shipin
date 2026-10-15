"""Read-only, phase-specific adoption of the actual CONTROL5 stop prefix."""
import json
from pathlib import Path
import types

SCHEMA = 'CONTROLLED_REMAINING_HANDOFF_V1'
CONTROL = 'TEMPORAL_PRODUCTION_CONTROL_V6'


def require(ok, why):
    if not ok: raise ValueError(why)


def operation_table(plan, batches):
    expected = {('SOURCE_PREPARE', row['source_id']) for row in plan['sources']}
    for batch in batches:
        if batch.get('cpu_only_empty_batch') is True: continue
        expected |= {(phase, batch['batch_id']) for phase in
                     ('BATCH_INPUT_ADMIT', 'GPU_WRAPPER', 'TERMINAL_CAPTURE', 'OUTPUT_REPLAY', 'LEASE_CLOSE')}
        expected |= {('FIRST_INPUT_REPLAY', rid) for rid in batch['request_ids']}
    return expected


def adoption_table(old_rows, adopted, expected):
    """Pure uniqueness/causal pairing; receipt bytes are checked separately."""
    claims = {}; completed = set()
    for row in old_rows:
        key = (row['phase'], row['item']); require(key in expected, 'Old phase outside frozen graph')
        if row['event'] == 'BEGIN':
            require(key not in claims, 'Old BEGIN repeated'); claims[key] = row
        elif row['event'] == 'COMPLETE':
            require(key in claims and key not in completed and row['exit_code'] == 0,
                    'Old completion orphan, duplicate or failed'); completed.add(key)
        elif row['event'] == 'REUSE':
            require(key not in claims and row['exit_code'] == 0 and row['actual_new_calls'] == 0,
                    'Original reuse is not a distinct successful claim'); claims[key] = row; completed.add(key)
        else: raise ValueError('True failure cannot be silently adopted')
    keys = [(row['phase'], row['item']) for row in adopted]
    require(len(keys) == len(set(keys)) and set(keys) == set(claims),
            'Every old claim must have one real terminal; no uncertain BEGIN may rerun')
    require(all(type(row['exit_code']) is int and row['exit_code'] == 0 and row['actual_new_calls'] == 0 and
                row['successful_original_operation_repeated'] is False for row in adopted), 'Adoption is read-only success reuse')
    return set(keys)


def old_parent_exclusive(value):
    """No signals. A main-held old parent must remain stopped or absent."""
    parent = value['original_parent']; pid = parent['pid']; root = Path('/proc')/str(pid)
    if not root.exists():
        require(value['old_parent_disposition'] == 'MAIN_RELINQUISHED_AFTER_ALL_OWNED_CHILDREN_NATURAL_TERMINAL',
                'Unexplained old parent disappearance')
        return
    stat = (root/'stat').read_text(); tail = stat[stat.rfind(')')+2:].split()
    require(tail[0] in ('T', 't') and tail[19] == str(parent['start_ticks']),
            'Old scheduler resumed or its PID was reused')
    argv = (root/'cmdline').read_bytes().split(b'\0')[:-1]
    require([arg.decode() for arg in argv] == parent['argv'], 'Owned old parent argv changed')
    children = set()
    for thread in (root/'task').iterdir():
        try: children.update((thread/'children').read_text().split())
        except FileNotFoundError: continue
    frozen = {str(row['pid']): row for row in value['owned_child_terminals']}
    for child in children:
        require(child in frozen, 'Unaccounted old direct child blocks new scheduling')
        child_root = Path('/proc')/child
        if child_root.exists():
            text = (child_root/'stat').read_text(); fields = text[text.rfind(')')+2:].split()
            require(fields[0] == 'Z' and fields[19] == str(frozen[child]['start_ticks']) and
                    int(fields[49]) == 0, 'Begun old child must have naturally exited 0, never be stopped/killed')


def receipt(ctx, io, phase, item, row):
    store = ctx['store']; ref = row['receipt_ref']; path = io.bound(ref, (io.CAMPAIGN, io.RUN, io.HOME/'improvement_round1'))
    value = io.read(path)
    batch = next((b for b in ctx['batches'] if b['batch_id'] == item), None)
    if phase == 'SOURCE_PREPARE':
        source = next(s for s in ctx['plan']['sources'] if s['source_id'] == item)
        wanted = [r['request_id'] for r in ctx['plan']['requests'] if r['source_id'] == item and r['execution'] == 'MODEL']
        require(path == store.path('permanent/proofs/source_'+item+'_completion.json', 'permanent') and
                value['status'] == 'PASS_COMPLETE_SOURCE_NEW_INPUTS_NOT_GPU_OR_QUALITY' and
                value['source_id'] == item and [entry['consumer'] for entry in value['consumers']] == wanted,
                'Source adoption lacks full actual completion')
        store.checked_ref(value['new_clock_ref'])
        for entry in value['consumers']:
            consumer = entry['consumer']; expected_proof = store.ref('permanent/proofs/'+consumer+'_CPU_input.json')
            require(entry['CPU_input_proof_ref'] == expected_proof, 'Source completion CPU proof binding changed')
            proof = io.read(store.checked_ref(entry['CPU_input_proof_ref']))
            require(entry['input_manifest_ref'] == proof['input_manifest_ref'] and
                    entry['lease_id'] == next(row['lease_id'] for row in ctx['plan']['requests'] if row['request_id'] == consumer),
                    'Source completion manifest/lease binding changed')
            manifest = io.read(store.checked_ref(entry['input_manifest_ref']))
            for payload in (manifest['private_ref'], manifest['visual_ref']):
                if payload: store.checked_ref(payload)
        return
    if phase == 'FIRST_INPUT_REPLAY':
        require(path == store.path('permanent/proofs/'+item+'_first_input_replay.json', 'permanent') and
                value['status'] == 'PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE' and
                value['consumer'] == item and value['first_independent_input_replay'] is True and
                value['actual_first_independent_processor_encodes'] == 1 and value['new_model_calls'] == 0,
                'First successful input replay cannot be guessed or repeated')
        for key in ('input_manifest_ref', 'CPU_input_proof_ref', 'resource_ref', 'ledger_ref'): store.checked_ref(value[key])
        return
    require(batch is not None, 'Unfrozen batch phase')
    root = io.RUNTIME/'runs'/item
    if phase == 'BATCH_INPUT_ADMIT':
        require(path == root/'input_admission.json' and value['status'] == 'PASS_COMPLETE_FIXED_BATCH_INPUTS_NOT_GPU_PERMISSION',
                'Actual original batch input admission missing')
    elif phase == 'GPU_WRAPPER':
        require(value['status'] == 'completed' and type(value['exit_code']) is int and value['exit_code'] == 0 and
                value['name'] == batch['gpu_job_name'], 'Begun model call must have natural successful terminal')
        ledger = io.rows(io.bound(row['unique_ledger_snapshot_ref'], (io.CAMPAIGN, io.HOME/'improvement_round1')))
        require([record for record in ledger if record.get('name') == value['name']] == [value], 'Unique actual GPU ledger required')
        pointer = io.read(root/'gpu_completion_pointer.json'); complete = io.read(store.checked_ref(pointer['completion_ref']))
        require(complete['status'] == 'PASS_COMPLETE_PRODUCTION_BATCH_NOT_QUALITY' and
                complete['actual_model_calls'] == len(batch['request_ids']) and complete['batch_id'] == item,
                'GPU adoption requires all original actual outputs; never replay inference')
    elif phase == 'TERMINAL_CAPTURE':
        require(path == root/'terminal_pointer.json', 'Original terminal pointer required')
        for key in ('resource_ref', 'ledger_ref', 'origin_binding_ref', 'batch_completion_ref'): store.checked_ref(value[key])
    elif phase == 'OUTPUT_REPLAY':
        pointer = io.read(root/'output_replay_pointer.json')
        require(path == store.checked_ref(pointer['completion_ref']) and
                value['status'] == 'PASS_COMPLETE_BATCH_OUTPUT_REPLAY_NOT_QUALITY' and
                [entry['consumer'] for entry in value['proofs']] == batch['request_ids'], 'Actual complete first output QA required')
        for entry in value['proofs']: store.checked_ref(entry['proof_ref'])
    elif phase == 'LEASE_CLOSE':
        pointer = io.read(root/'closure_pointer.json')
        require(path == store.checked_ref(pointer['completion_ref']) and
                value['status'] == 'PASS_BATCH_CONSUMER_CLOSURE_NEW_RGB_RELEASE_NOT_QUALITY' and
                value['accepted_consumers'] == batch['request_ids'], 'Actual complete original close required')
    else: raise ValueError('Unknown adoption phase')


def load_context(io, registration_path, child=False):
    path = Path(registration_path).resolve(); require(path.is_relative_to(io.BASE), 'New CONTROL6 root required')
    reg = io.read(path)
    require(reg['schema'] == CONTROL and reg['original_graph_membership_and_roles_unchanged'] is True and
            reg['remaining_only_execution'] is True and reg['no_project_init_or_rebatch'] is True and
            reg['training'] is False and reg['test_GT_read'] is False and reg['old_successes_modified'] is False,
            'Explicit remaining-only immutable graph registration required')
    original_path = io.bound(reg['original_control_registration_ref'], (io.CAMPAIGN/'temporal_production_control_v5',))
    require(original_path == io.CAMPAIGN/'temporal_production_control_v5/registration.json', 'Only actual CONTROL5 may be adopted')
    original = io.read(original_path)
    changed = {'schema', 'required_code_files', 'main_execution_admission_path', 'final_main_execution_admission_required_status',
               'original_control_registration_ref'}
    require(all(reg[key] == value for key, value in original.items() if key not in changed),
            'Remaining handoff cannot change original roles, graph, batches, timing, memory or GPU budget')
    require(all(reg['required_code_files'].get(key) == digest for key, digest in original['required_code_files'].items()),
            'Every original actual frozen code SHA must remain')
    for filename, digest in reg['required_code_files'].items(): require(io.sha(filename) == digest, 'Actual old/new code changed')
    for filename in Path(__file__).parent.glob('*.py'):
        require(reg['required_code_files'].get(str(filename.resolve())) == io.sha(filename), 'All new actual controller files must be registered')
    old_io_path = io.bound(reg['original_control_io_ref'], (original_path.parent/'code',))
    old_io = io.module('_pc6_frozen_original_control_io', old_io_path)
    # Original module is untouched; this explicit isolated function namespace
    # preserves its CONTROL5 schema while the new process imports CONTROL6 math.
    isolated_globals = dict(old_io.load.__globals__, SCHEMA='TEMPORAL_PRODUCTION_CONTROL_V5')
    old_load = types.FunctionType(old_io.load.__code__, isolated_globals, old_io.load.__name__, old_io.load.__defaults__)
    ctx = old_load(original_path)
    require(ctx['reg'] == original and ctx['reg']['global_graph_sha256'] == reg['global_graph_sha256'], 'Original context differs')
    handoff_ref = reg['quiescent_handoff_ref']; stop = io.read(io.bound(handoff_ref, (io.CAMPAIGN/'prospective_cache_handoff_01',)))
    require(stop['schema'] == SCHEMA and stop['status'] == 'MAIN_CONTROLLED_HANDOFF_STOP' and
            stop['original_control_registration_ref'] == reg['original_control_registration_ref'] and
            stop['all_begun_owned_children_naturally_terminal'] is True and stop['active_old_writer_count'] == 0 and
            stop['old_parent_scheduling_stopped'] is True and stop['old_failure_promoted_to_success'] is False and
            stop['global_graph_sha256'] == reg['global_graph_sha256'], 'Parent hold is not a complete quiescent handoff')
    journal_path = io.bound(stop['old_controller_journal_ref'], (original_path.parent/'run_01',))
    require(journal_path == original_path.parent/'run_01/journal.jsonl' and
            not (original_path.parent/'run_01/completion.json').exists() and
            not (original_path.parent/'run_01/failure.json').exists(), 'Controlled stop cannot invent FAILED/natural completion')
    old_rows = io.rows(journal_path); adopted = stop['adopted_operations']
    adoption_table(old_rows, adopted, operation_table(ctx['plan'], ctx['batches']))
    old_parent_exclusive(stop)
    for row in stop['owned_child_terminals']:
        require(row['natural_exit_observed'] is True and type(row['exit_code']) is int and row['exit_code'] == 0 and
                row['signal_sent_to_child'] is False, 'All begun owned children must finish naturally')
        io.bound(row['terminal_observation_ref'], (io.CAMPAIGN/'prospective_cache_handoff_01',))
    if child:
        validation_path=io.BASE/'run_01/parent_handoff_validation.json'
        claim=io.read(io.BASE/'run_01/launch_claim.json')
        require(claim['parent_handoff_validation_ref']==dict(path=str(validation_path),sha256=io.sha(validation_path)),
                'First QA child needs the immutable actual parent validation receipt')
        validation=io.read(validation_path)
        require(validation['status']=='PASS_PARENT_FULL_ADOPTION_AND_IMMUTABLE_GRAPH_VALIDATION' and
                validation['registration_sha256']==io.sha(path) and validation['quiescent_handoff_ref']==handoff_ref and
                validation['global_graph_sha256']==reg['global_graph_sha256'] and
                validation['adopted_operations']==adopted and validation['required_code_files']==reg['required_code_files'] and
                validation['all_adopted_canonical_payloads_actual_SHA_verified'] is True and
                validation['first_normal_processor_replay_not_replaced'] is True,
                'Typed child context cannot replace actual full parent adoption validation')
    for row in adopted:
        require(row['exit_code'] == 0 and row['actual_new_calls'] == 0 and row['successful_original_operation_repeated'] is False,
                'Adoption must retain a real completed operation without executing it')
        if child:
            # Recheck the original small proof bytes, not every other consumer's
            # canonical tensor payload. This child's own INPUT5 replay still
            # performs ordinary processor + full tensor byte equality once.
            io.bound(row['receipt_ref'],(io.CAMPAIGN,io.RUN,io.HOME/'improvement_round1'))
        else:receipt(ctx, io, row['phase'], row['item'], row)
    admission_path = Path(reg['main_execution_admission_path']).resolve()
    require(admission_path.is_relative_to(io.BASE), 'Main CONTROL6 admission root required')
    admission = io.read(admission_path)
    require(admission['status'] == 'MAIN_APPROVED_CONTROLLED_REMAINING_PRODUCTION_V6' and
            admission['registration_sha256'] == io.sha(path) and admission['quiescent_handoff_ref'] == handoff_ref and
            admission['original_control_registration_ref'] == reg['original_control_registration_ref'] and
            admission['allow_remaining_original_gpu_jobs_once'] is True and
            admission['allow_project_init_or_rebatch'] is False, 'Main has not authorized this exact remaining handoff')
    for code_key in ('prospective_source_phase_code_ref', 'prospective_close_phase_code_ref', 'prospective_backend_code_ref'):
        target = io.bound(reg[code_key], (io.CAMPAIGN,))
        require(reg['required_code_files'].get(str(target)) == reg[code_key]['sha256'], 'Every actual callback must be in full code closure')
    for admission_key in ('prospective_source_phase_admission_path', 'prospective_close_phase_admission_path', 'prospective_backend_admission_path'):
        leaf = Path(reg[admission_key]).resolve(); require(leaf.is_relative_to(io.BASE), 'Actual prospective admission root required')
        value = io.read(leaf)
        require(value['controller_registration_ref'] == dict(path=str(path), sha256=io.sha(path)) and
                value['quiescent_handoff_ref'] == handoff_ref, 'Callback approval must bind the actual new registration and quiescent receipt')
    ctx.update(reg=reg, registration_path=path, handoff=stop, handoff_ref=handoff_ref, adopted=adopted)
    return ctx
