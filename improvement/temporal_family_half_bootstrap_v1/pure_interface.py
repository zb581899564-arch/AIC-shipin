"""New binding-only metadata cases; never imports/runs a renderer."""
import copy
from half_bind_contract import (PARAMETERS,ORIGINAL_ARMS,original_count,production_gate,
    lock_union,merge_history)


def expect_reject(call):
    try:call()
    except (ValueError,KeyError):return
    raise AssertionError('Invalid technical binding accepted')


def family(n):
    rows=[]
    for i in range(n):
        rows.append(dict(arm=ORIGINAL_ARMS[i],status='PASS_ENGINEERING_NEW_TEMPORAL_EXPLICIT_RISK_ZIP_NOT_OFFICIAL_SCORE',
            independent11strict=True,quality_pass_claimed=False,actual_parameters=PARAMETERS,records=426,
            model_calls_in_packaging=0,website_submitted=False,SHA256=('%064x'%(i+1)),member_SHA256=('%064x'%(i+11)),
            canonical_SHA256=('%064x'%(i+21))))
    return dict(status='COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_NEW_FAMILY_PACKAGES',packages=rows,
        actual_packages=n,required_goal_count=5,goal_complete_claimed=False)


def run():
    assert original_count(family(0))==0 and min(3,5-original_count(family(4)))==1
    assert original_count(family(5))==5  # bind's early branch has no target writes.
    bad=family(4);bad['actual_packages']=5;expect_reject(lambda:original_count(bad))
    bad=family(1);bad['status']='FAILED';expect_reject(lambda:original_count(bad))
    bad=family(2);bad['packages'][1]['canonical_SHA256']=bad['packages'][0]['canonical_SHA256']
    expect_reject(lambda:original_count(bad))
    ref=dict(path='/synthetic/global_completion.json',sha256='a'*64)
    production=dict(status='PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS',
        engineering_failed_requests=0,missing_requests=0,physical_model_parameters=PARAMETERS,optimizer_updates=0,
        test_GT_or_annotation_read=False,native_clock_matches_original_full_PTS=True,scientific_quality_claim=False,
        old_scientific_failed_gates_changed=False,old_packet_FAIL_reclassified=False,global_refiner_role='TIME_ENABLED',
        global_VERIFY_role='TIME_ENABLED',actual_unique_MODEL_ids=['M'+str(i) for i in range(1992)],
        actual_unique_MODEL_proofs=[{'consumer':'M'+str(i)} for i in range(1992)],
        accepted_endpoint_request_ids=['E'+str(i) for i in range(1330)],
        accepted_verification_event_ids=['V'+str(i) for i in range(665)],actual_source_ids=[str(i) for i in range(426)],
        native_clock_original_bindings={str(i):{} for i in range(426)})
    controller=dict(status='PASS_CONTROLLER_ALL_BATCHES_NATURAL_TERMINALS_AND_FIRST_REPLAYS_NOT_QUALITY',
        global_completion_path=ref['path'],global_completion_sha256=ref['sha256'],
        coverage=dict(source_count=426,actual_model_calls=1992,logical_requests=1995,batches=49),
        actual_total_model_calls_in_original_graph=1992,actual_new_model_calls=1900,old_successful_operations_repeated=0)
    technical=dict(status='TECHNICAL_PACKAGE_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM',source_count=426,
        window_count=521,event_count=665,nominal_requests=1995,actual_MODEL_proofs=1992,structural_no_MODEL_proofs=3,
        production_completion_ref=ref,package_admission_created=False,model_calls=0,new_ZIPs=0)
    production_gate(production,controller,technical,ref)
    bad=copy.deepcopy(production);bad['actual_unique_MODEL_ids'][1]=bad['actual_unique_MODEL_ids'][0]
    expect_reject(lambda:production_gate(bad,controller,technical,ref))
    bad=dict(controller,actual_total_model_calls_in_original_graph=1995)
    expect_reject(lambda:production_gate(production,bad,technical,ref))
    bad=dict(production,global_refiner_role='BASE_DISABLED')
    expect_reject(lambda:production_gate(bad,controller,technical,ref))
    assert lock_union({'/old':'a'*64},{'/new':'b'*64})=={'/old':'a'*64,'/new':'b'*64}
    expect_reject(lambda:lock_union({'/old':'a'*64},{'/old':'b'*64}))
    old=[dict(canonical_SHA256='a'*64)];new=[dict(canonical_SHA256='b'*64)]
    assert merge_history(old,new)==old+new
    expect_reject(lambda:merge_history(old,[dict(canonical_SHA256='a'*64)]))
    return dict(status='PASS_NEW_HALF_TECHNICAL_BINDING_INTERFACES',checks=13,
        synthetic_metadata_only=True,formal_raw_or_test_body_reads=0,source_or_cache_operations=0,
        model_calls=0,processor_calls=0,package_calls=0,package_admission_created=False,
        old_half_geometry_or_pipeline_checks_repeated=False)
