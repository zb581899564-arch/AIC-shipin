"""Only new synthetic C7 terminal and old-failure journal mutation cases."""
from copy import deepcopy
from control7_recovery import controller_gate,old_journal_gate,STATUS


def rejected(call):
    try:call()
    except (ValueError,KeyError):return
    raise AssertionError('Invalid recovery accepted')


def run():
    ref=dict(path='/synthetic/global.json',sha256='a'*64)
    controller=dict(status=STATUS,global_completion_path=ref['path'],global_completion_sha256=ref['sha256'],
        coverage=dict(source_count=426,actual_model_calls=1992,logical_requests=1995,batches=49),
        actual_total_model_calls_in_original_graph=1992,actual_new_model_calls=1959,
        actual_new_model_calls_in_recovery=0,actual_first_QA_calls_in_recovery=0,
        old_successful_operations_repeated=0,old_control6_failure_not_reclassified=True)
    for key in ('old_control6_failure_ref','old_control6_journal_ref','recovery_registration_ref','aggregate_natural_terminal_ref'):
        controller[key]=dict(path='/synthetic/'+key+'.json',sha256='b'*64)
    controller_gate(controller,ref)
    for key,value in [('actual_new_model_calls_in_recovery',1),('actual_first_QA_calls_in_recovery',1),
        ('old_successful_operations_repeated',1),('old_control6_failure_not_reclassified',False),
        ('actual_new_model_calls',0),('status','PASS_CONTROLLER_ALL_BATCHES_NATURAL_TERMINALS_AND_FIRST_REPLAYS_NOT_QUALITY')]:
        bad=dict(controller);bad[key]=value;rejected(lambda:controller_gate(bad,ref))
    expected={('SOURCE_PREPARE','S0'),('GPU_WRAPPER','B0')}
    rows=[dict(event='REUSE',phase='SOURCE_PREPARE',item='S0',exit_code=0,actual_new_calls=0),
        dict(event='BEGIN',phase='GPU_WRAPPER',item='B0'),dict(event='COMPLETE',phase='GPU_WRAPPER',item='B0',exit_code=0),
        dict(event='BEGIN',phase='GLOBAL_AGGREGATE',item='ALL426'),
        dict(event='FAILED',phase='GLOBAL_AGGREGATE',item='ALL426',exit_code=1)]
    old_journal_gate(rows,expected)
    bad=deepcopy(rows);bad[-1].update(event='COMPLETE',exit_code=0);rejected(lambda:old_journal_gate(bad,expected))
    rejected(lambda:old_journal_gate(rows[:-2]+rows[-1:],expected))
    rejected(lambda:old_journal_gate(rows[:2]+rows[3:],expected))
    rejected(lambda:old_journal_gate(rows+[rows[0]],expected))
    print('PASS_NEW_CONTROL7_METADATA_TERMINAL_AND_FAILURE_PRESERVATION_CASES')

if __name__=='__main__':run()
