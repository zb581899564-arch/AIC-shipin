"""Actual CONTROL6 -> controlled STOP5 -> failed4 -> successful BOOT2 binding.

No producer, tensor, decoder, model, controller or package is invoked here.
"""
from pathlib import Path


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def comparable(ref):
    return dict(path=ref['path'], sha256=ref['sha256'])


def validate_continuation(closure, documents, refs, production, controller, control_root, old_root, boot_root):
    control = documents['control_registration']
    old_ref = control['original_control_registration_ref']
    require(Path(old_ref['path']).resolve() == old_root/'registration.json', 'Only the real original CONTROL5 may be adopted')
    original = closure.load(old_ref)
    old4_ref = original['original_control_registration_ref']
    require(Path(old4_ref['path']).resolve() == old_root.parent/'temporal_production_control_v4/registration.json' and
            comparable(old4_ref) == comparable(documents['bootstrap_completion']['control_registration_ref']),
            'Successful BOOT2 remains bound to original CONTROL4 through CONTROL5')
    closure.load(old4_ref)
    environment = original['explicit_import_environment_recovery_ref']
    require(Path(environment['path']).resolve() == old_root/'import_environment_recovery_01.json',
            'CONTROL5 original environment-only recovery identity changed')
    closure.load(environment)
    stop_ref = control['quiescent_handoff_ref']
    stop = closure.load(stop_ref)
    require(Path(stop_ref['path']).resolve().is_relative_to(control_root.parent/'prospective_cache_handoff_01') and
            stop['schema'] == 'CONTROLLED_REMAINING_HANDOFF_V1' and stop['status'] == 'MAIN_CONTROLLED_HANDOFF_STOP' and
            comparable(stop['original_control_registration_ref']) == comparable(old_ref) and
            stop['all_begun_owned_children_naturally_terminal'] is True and stop['active_old_writer_count'] == 0 and
            stop['old_parent_scheduling_stopped'] is True and stop['old_failure_promoted_to_success'] is False and
            stop['global_graph_sha256'] == refs['full_plan']['sha256'] and
            not (old_root/'run_01/completion.json').exists() and not (old_root/'run_01/failure.json').exists(),
            'A controlled STOP is neither failure nor natural completion; parent hold alone is insufficient')
    journal_ref = stop['old_controller_journal_ref']
    require(Path(journal_ref['path']).resolve() == old_root/'run_01/journal.jsonl', 'Original STOP journal owner changed')
    closure.add(journal_ref)
    import json
    rows = [json.loads(line) for line in Path(journal_ref['path']).read_text().splitlines() if line]
    begins = {(row['phase'], row['item']) for row in rows if row['event'] == 'BEGIN'}
    finishes = [row for row in rows if row['event'] == 'COMPLETE']
    completed = {(row['phase'], row['item']) for row in finishes}
    adopted = stop['adopted_operations']
    require(len(completed) == len(finishes) and begins == completed and
            all(row['exit_code'] == 0 for row in finishes) and not any(row['event'] == 'FAILED' for row in rows) and
            len(adopted) == len(completed) and {(row['phase'], row['item']) for row in adopted} == completed,
            'Every original begun operation must have one real complete terminal and exact adoption')
    source_reuse = {}
    for row in adopted:
        require(row['exit_code'] == 0 and row['actual_new_calls'] == 0 and
                row['successful_original_operation_repeated'] is False,
                'Old operation adoption must not execute it again')
        closure.reference(row['receipt_ref'])
        if row['phase'] == 'SOURCE_PREPARE':
            source_reuse[row['item']] = closure.absolute(row['receipt_ref'])
    for row in stop['owned_child_terminals']:
        require(row['natural_exit_observed'] is True and type(row['exit_code']) is int and row['exit_code'] == 0 and
                row['signal_sent_to_child'] is False, 'A begun child cannot be converted into a successful stop')
        closure.reference(row['terminal_observation_ref'])
    require(comparable(production['original_control_registration_ref']) == comparable(old_ref) and
            comparable(production['quiescent_handoff_ref']) == comparable(stop_ref) and
            comparable(controller['quiescent_handoff_ref']) == comparable(stop_ref) and
            production['controlled_stop_is_not_failed_or_natural_completion'] is True and
            production['old_successful_operations_repeated'] == controller['old_successful_operations_repeated'] == 0 and
            production['original_graph_project_init_or_rebatch_repeated'] is False,
            'The accepted global/controller export must retain the exact STOP provenance')
    reg_ref = comparable(refs['control_registration'])
    for name in ('source_phase', 'close_phase', 'backend'):
        code_key = 'prospective_'+name+'_code_ref'
        export_key = 'actual_'+code_key
        admission_key = 'prospective_'+name+'_admission_ref'
        require(production[export_key] == control[code_key] == controller[export_key], 'Actual new callback code differs')
        closure.reference(control[code_key])
        leaf_ref = production[admission_key]
        require(Path(leaf_ref['path']).resolve() == Path(control['prospective_'+name+'_admission_path']).resolve() and
                Path(leaf_ref['path']).resolve().is_relative_to(control_root), 'Actual callback admission owner changed')
        leaf = closure.load(leaf_ref)
        require(comparable(leaf['controller_registration_ref']) == reg_ref and
                comparable(leaf['quiescent_handoff_ref']) == comparable(stop_ref), 'Callback admission is not bound to this new controller/STOP')
    return dict(source_reuse=source_reuse, original_control_registration_ref=old_ref, quiescent_handoff_ref=stop_ref)


def validate_producer(closure, bindings, production, continuation, input_root):
    complete_ref = bindings['source_CPU_completion_ref']
    complete = closure.load(complete_ref)
    declared = complete.get('prospective_producer_provenance')
    require(bindings['actual_producer_provenance'] == declared, 'A source actual writer was invented or omitted by aggregation')
    if declared is None:
        require(continuation['source_reuse'].get(complete['source_id']) == closure.absolute(complete_ref),
                'An old SOURCE writer must be one of the actual STOP-adopted exact successes')
        return
    require(comparable(declared['prospective_phase_ref']) == comparable(production['actual_prospective_source_phase_code_ref']) and
            comparable(declared['prospective_backend_ref']) == comparable(production['prospective_backend_admission_ref']) and
            comparable(declared['prospective_backend_code_ref']) == comparable(production['actual_prospective_backend_code_ref']) and
            comparable(declared['prospective_source_phase_admission_ref']) == comparable(production['prospective_source_phase_admission_ref']) and
            declared['actual_source_writer_execution_kind'] == 'EXPLICIT_FUNCTION_GLOBALS_COPY_UNCHANGED_FROZEN_BYTECODE' and
            declared['original_source_math_bytecode_unchanged'] is True and
            Path(declared['original_preparation_code_ref']['path']).resolve() == input_root/'code/prepare_source.py',
            'The source writer must distinguish actual new phase/backend from unchanged old preparation')
    closure.walk(declared)
    for ref in complete['structural_producer_provenance_refs'].values():
        closure.load(ref)
