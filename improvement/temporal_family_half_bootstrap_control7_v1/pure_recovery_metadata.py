"""New HALF C7 production metadata cases; no renderer or real evidence IO."""
from half_bind_contract import production_gate,PARAMETERS


def rejected(call):
    try:call()
    except (ValueError,KeyError):return
    raise AssertionError('Invalid recovery accepted')


def run():
    ref=dict(path='/synthetic/global.json',sha256='a'*64)
    production=dict(status='PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS',
        engineering_failed_requests=0,missing_requests=0,physical_model_parameters=PARAMETERS,optimizer_updates=0,
        test_GT_or_annotation_read=False,native_clock_matches_original_full_PTS=True,scientific_quality_claim=False,
        old_scientific_failed_gates_changed=False,old_packet_FAIL_reclassified=False,global_refiner_role='TIME_ENABLED',
        global_VERIFY_role='TIME_ENABLED',actual_unique_MODEL_ids=[str(i) for i in range(1992)],
        actual_unique_MODEL_proofs=[dict(consumer=str(i)) for i in range(1992)],
        accepted_endpoint_request_ids=[str(i) for i in range(1330)],accepted_verification_event_ids=[str(i) for i in range(665)],
        actual_source_ids=[str(i) for i in range(426)],native_clock_original_bindings={str(i):{} for i in range(426)})
    controller=dict(status='PASS_CONTROL7_REMAINING_AGGREGATE_RECOVERY_NO_NEW_MODEL_OR_QA_NOT_QUALITY',
        global_completion_path=ref['path'],global_completion_sha256=ref['sha256'],
        coverage=dict(source_count=426,actual_model_calls=1992,logical_requests=1995,batches=49),
        actual_total_model_calls_in_original_graph=1992,actual_new_model_calls=1959,old_successful_operations_repeated=0,
        actual_new_model_calls_in_recovery=0,actual_first_QA_calls_in_recovery=0,old_control6_failure_not_reclassified=True)
    for key in ('old_control6_failure_ref','old_control6_journal_ref','recovery_registration_ref','aggregate_natural_terminal_ref'):
        controller[key]=dict(path='/synthetic/'+key+'.json',sha256='b'*64)
    technical=dict(status='TECHNICAL_PACKAGE_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM',source_count=426,
        window_count=521,event_count=665,nominal_requests=1995,actual_MODEL_proofs=1992,structural_no_MODEL_proofs=3,
        production_completion_ref=ref,package_admission_created=False,model_calls=0,new_ZIPs=0)
    production_gate(production,controller,technical,ref)
    for key,value in [('actual_new_model_calls_in_recovery',1),('actual_first_QA_calls_in_recovery',1),
        ('old_control6_failure_not_reclassified',False),('actual_new_model_calls',0)]:
        bad=dict(controller);bad[key]=value;rejected(lambda:production_gate(production,bad,technical,ref))
    print('PASS_NEW_HALF_CONTROL7_RECOVERY_METADATA_CASES')

if __name__=='__main__':run()
