"""Only newly introduced adoption/remaining scheduling invariants."""
from handoff import adoption_table


def run():
    expected={('SOURCE_PREPARE','S0'),('SOURCE_PREPARE','S1'),('GPU_WRAPPER','B0')}
    original=[dict(event='BEGIN',phase='SOURCE_PREPARE',item='S0'),
        dict(event='COMPLETE',phase='SOURCE_PREPARE',item='S0',exit_code=0),
        dict(event='BEGIN',phase='GPU_WRAPPER',item='B0')]
    adopted=[dict(phase=phase,item=item,exit_code=0,actual_new_calls=0,
        successful_original_operation_repeated=False) for phase,item in
        [('SOURCE_PREPARE','S0'),('GPU_WRAPPER','B0')]]
    completed=adoption_table(original,adopted,expected)
    assert expected-completed=={('SOURCE_PREPARE','S1')}
    bad=[(original,adopted[:-1]),(original,adopted+[adopted[0]]),
         (original+[original[0]],adopted),
         (original+[dict(event='FAILED',phase='GPU_WRAPPER',item='B0',exit_code=1)],adopted),
         (original,[dict(adopted[0],actual_new_calls=1),adopted[1]]),
         ([dict(event='COMPLETE',phase='SOURCE_PREPARE',item='S0',exit_code=0)],adopted[:1])]
    for journal,table in bad:
        try:adoption_table(journal,table,expected)
        except ValueError:pass
        else:raise AssertionError('Invalid new adoption accepted')
    return dict(status='PASS_NEW_HANDOFF_ADOPTION_AND_REMAINING_ONLY_CASES',checks=7,
        old_successful_pure_suites_repeated=False,new_source_decodes=0,new_processor_encodes=0,new_model_calls=0)
