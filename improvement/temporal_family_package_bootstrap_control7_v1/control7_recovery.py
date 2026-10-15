"""Metadata-only acceptance of the actual failed GLOBAL recovery. No execution."""
from pathlib import Path
import json

STATUS='PASS_CONTROL7_REMAINING_AGGREGATE_RECOVERY_NO_NEW_MODEL_OR_QA_NOT_QUALITY'
REFS=('old_control6_failure_ref','old_control6_journal_ref','recovery_registration_ref','aggregate_natural_terminal_ref')


def require(ok,why):
    if not ok: raise ValueError(why)


def comparable(ref):
    return dict(path=ref['path'],sha256=ref['sha256'])


def controller_gate(controller,production_ref):
    require(controller['status']==STATUS and
        controller['global_completion_path']==production_ref['path'] and
        controller['global_completion_sha256']==production_ref['sha256'] and
        controller['coverage']==dict(source_count=426,actual_model_calls=1992,logical_requests=1995,batches=49) and
        type(controller['actual_total_model_calls_in_original_graph']) is int and
        controller['actual_total_model_calls_in_original_graph']==1992 and
        type(controller['actual_new_model_calls']) is int and controller['actual_new_model_calls']==1959 and
        all(type(controller[key]) is int and controller[key]==0 for key in
            ('actual_new_model_calls_in_recovery','actual_first_QA_calls_in_recovery','old_successful_operations_repeated')) and
        controller['old_control6_failure_not_reclassified'] is True,
        'Only real aggregate-only CONTROL7 success may bind; old C6 new calls are not recovery calls')
    for key in REFS:
        ref=controller[key]
        require(isinstance(ref,dict) and isinstance(ref.get('path'),str) and
            isinstance(ref.get('sha256'),str) and len(ref['sha256'])==64,
            'Recovery evidence path and SHA required: '+key)


def old_journal_gate(rows,expected):
    global_rows=[row for row in rows if row['phase']=='GLOBAL_AGGREGATE']
    require(len(global_rows)==2 and
        [(row['event'],row['item']) for row in global_rows]==[('BEGIN','ALL426'),('FAILED','ALL426')] and
        type(global_rows[1]['exit_code']) is int and global_rows[1]['exit_code']!=0,
        'Original C6 must retain its one actual GLOBAL failure, never a fabricated completion')
    begun=set();completed=set()
    for row in rows:
        if row['phase']=='GLOBAL_AGGREGATE': continue
        key=row['phase'],row['item']
        require(key in expected,'Unknown upstream operation in original C6 journal')
        if row['event']=='BEGIN':
            require(key not in begun,'Upstream successful operation repeated');begun.add(key)
        elif row['event']=='COMPLETE':
            require(key in begun and key not in completed and type(row['exit_code']) is int and row['exit_code']==0,
                'Orphan, repeated, or failed upstream completion');completed.add(key)
        elif row['event']=='REUSE':
            require(key not in begun and key not in completed and type(row['exit_code']) is int and row['exit_code']==0 and
                type(row['actual_new_calls']) is int and row['actual_new_calls']==0,'Invalid old successful adoption')
            begun.add(key);completed.add(key)
        else: raise ValueError('C6 contains another failure or unresolved upstream operation')
    require(begun==completed==expected,'Original C6 upstream success denominator incomplete')


def validate_recovery(closure,controller,production,config,plan,journal,control,final):
    controller_gate(controller,config['production_completion_ref'])
    paths=dict(old_control6_failure_ref=control/'run_01/failure.json',
        old_control6_journal_ref=control/'run_01/journal.jsonl',
        recovery_registration_ref=final/'registration.json',
        aggregate_natural_terminal_ref=final/'run_01/aggregate_natural_terminal.json')
    for key,path in paths.items():
        require(Path(controller[key]['path']).resolve()==path,'Wrong actual recovery owner: '+key)
        closure.add(controller[key])
    require(not (control/'run_01/completion.json').exists(),'Original failed C6 cannot become naturally complete')
    failure=closure.load(controller['old_control6_failure_ref'])
    require(failure['status']=='FAILED_CONTROL_PRESERVE_ALL_ATTEMPTS_SUCCESS_RAW_COSTS' and
        failure['no_whole_chain_retry'] is True and failure['no_external_process_killed'] is True and
        failure['journal_sha256']==controller['old_control6_journal_ref']['sha256'],'Original C6 failure evidence changed')
    batches=production['batch_natural_terminals']
    require(len(batches)==len({row['batch_id'] for row in batches})==49,'Exactly 49 original natural batch terminals required')
    require(len(plan['sources'])==426 and len(plan['consumers'])==len(set(plan['consumers']))==1992,
        'Original complete source/model denominator differs')
    expected={('SOURCE_PREPARE',row['source_id']) for row in plan['sources']}
    expected|={(phase,row['batch_id']) for row in batches for phase in
        ('BATCH_INPUT_ADMIT','GPU_WRAPPER','TERMINAL_CAPTURE','OUTPUT_REPLAY','LEASE_CLOSE')}
    expected|={('FIRST_INPUT_REPLAY',rid) for rid in plan['consumers']}
    old_journal_gate(journal,expected)
    reg=closure.load(controller['recovery_registration_ref'])
    require(reg['schema']=='CONTROL7_REMAINING_AGGREGATE_METADATA_RECOVERY_V1' and
        comparable(reg['original_control6_registration_ref'])==comparable(config['production_refs']['control_registration']) and
        all(comparable(reg[key])==comparable(controller[key]) for key in
            ('old_control6_failure_ref','old_control6_journal_ref')) and
        reg['clock_ref_fix']=='EXACT_PATH_SHA_AND_OPTIONAL_ACTUAL_BYTE_IDENTITY_ONLY' and
        all(type(reg[key]) is int and reg[key]==0 for key in ('actual_new_model_calls_in_recovery',
            'actual_first_QA_calls_in_recovery','actual_new_source_preparation_calls')) and
        reg['original_graph_or_weights_or_raw_modified'] is False and reg['all_upstream_successes_reused'] is True,
        'Recovery must bind actual C6 failure and preserve all successful original operations')
    require(Path(reg['aggregate_writer_ref']['path']).resolve()==final/'code/aggregate.py' and
        Path(reg['aggregate_original_code_ref']['path']).resolve()==control/'code/aggregate.py',
        'Actual recovery and unchanged original writer identities required')
    closure.add(reg['aggregate_writer_ref']);closure.add(reg['aggregate_original_code_ref'])
    admission=closure.observe_json(final/'main_execution_admission.json')
    require(admission['status']=='MAIN_APPROVED_ONCE_FAILED_GLOBAL_METADATA_RECOVERY_NO_MODELS_OR_QA' and
        admission['registration_sha256']==controller['recovery_registration_ref']['sha256'],
        'Aggregate recovery needs its original actual execution admission')
    terminal=closure.load(controller['aggregate_natural_terminal_ref'])
    argv=terminal['argv']
    require(terminal['status']=='PASS_CONTROL7_AGGREGATE_REAL_NATURAL_EXIT0' and
        type(terminal['exit_code']) is int and terminal['exit_code']==0 and terminal['naturally_completed'] is True and
        terminal['process_was_killed_or_restarted'] is False and
        comparable(terminal['writer_ref'])==comparable(reg['aggregate_writer_ref']) and
        len(argv)==6 and argv[1:]==['-B','-u',str(final/'code/aggregate.py'),'--registration',str(control/'registration.json')],
        'Recovery requires its real natural exit0 and exact unchanged registration argv')
    new_rows=closure.observe_jsonl(final/'run_01/journal.jsonl')
    require(len(new_rows)==2 and [(row['event'],row['phase'],row['item']) for row in new_rows]==
        [('BEGIN','GLOBAL_RECOVERY','ALL426'),('COMPLETE','GLOBAL_RECOVERY','ALL426')] and
        type(new_rows[1]['exit_code']) is int and new_rows[1]['exit_code']==0 and new_rows[0]['argv']==argv and
        all(new_rows[0][key]==terminal[key] for key in ('pid','start_ticks')) and
        comparable(terminal['log_ref'])==dict(path=new_rows[1]['log_path'],sha256=new_rows[1]['log_sha256']),
        'New C7 journal can contain only this actual aggregate recovery, never upstream replays')
    closure.add(terminal['log_ref'])
    provenance=production['aggregate_recovery_provenance']
    require(comparable(provenance['recovery_registration_ref'])==comparable(controller['recovery_registration_ref']) and
        comparable(provenance['original_control6_failure_ref'])==comparable(controller['old_control6_failure_ref']) and
        comparable(provenance['original_control6_journal_ref'])==comparable(controller['old_control6_journal_ref']) and
        all(comparable(provenance[key])==comparable(reg[key]) for key in ('aggregate_writer_ref','identity_diagnosis_ref')) and
        all(type(provenance[key]) is int and provenance[key]==0 for key in
            ('actual_new_model_calls_in_recovery','actual_first_QA_calls_in_recovery')) and
        provenance['old_CONTROL6_failure_not_reclassified'] is True,'Global export recovery provenance differs')
