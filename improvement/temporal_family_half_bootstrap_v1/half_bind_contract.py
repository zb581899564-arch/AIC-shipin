"""Only technical metadata gates; no geometry or model implementation."""
import hashlib
import json
import re

SCHEMA='TEMPORAL_FAMILY_HALF_TECHNICAL_BOOTSTRAP_V1'
PARAMETERS=8782459120
ORIGINAL_ARMS=['START','END','BOTH','VERIFY','VERIFY_BOTH','SOURCE_START','SOURCE_END','SOURCE_BOTH']
HALF_ARMS=['HALF_START','HALF_END','HALF_BOTH']
HALF_PROTOCOL_SHA='7a6a14dbf309c19931ff7c514e865e1c2cd3929f77c560270e2ddc28bbbe5fce'
HALF_RENDERER_SHA='e6c371f3642aa37803f1b49ee905c9014beda83628eb65523acd709281fdafdc'
ORIGINAL_RENDERER_SHA='9a0369a1034b96e16a570ca4864032beeb606842b1fc897e833c492094c7962e'


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def valid_sha(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None


def original_count(family):
    packages=family['packages'];n=family['actual_packages']
    require(family['status']=='COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_NEW_FAMILY_PACKAGES' and
        type(n)is int and n==len(packages) and 0<=n<=5 and family['required_goal_count']==5 and
        family['goal_complete_claimed'] is False,'Original family needs its complete actual engineering terminal')
    arms=[row['arm'] for row in packages]
    require(len(set(arms))==len(arms) and all(arm in ORIGINAL_ARMS for arm in arms) and
        [ORIGINAL_ARMS.index(arm) for arm in arms]==sorted(ORIGINAL_ARMS.index(arm) for arm in arms),
        'Original published arms differ from the fixed priority')
    require(len({row['canonical_SHA256'] for row in packages})==n and all(
        row['status']=='PASS_ENGINEERING_NEW_TEMPORAL_EXPLICIT_RISK_ZIP_NOT_OFFICIAL_SCORE' and
        row['independent11strict'] is True and row['quality_pass_claimed'] is False and
        row['actual_parameters']==PARAMETERS and row['records']==426 and
        row['model_calls_in_packaging']==0 and row['website_submitted'] is False and
        all(valid_sha(row[key]) for key in ('SHA256','member_SHA256','canonical_SHA256'))
        for row in packages),'Original package canonical/strict/risk identity is incomplete')
    return n


def production_gate(production,controller,technical,production_ref):
    require(production['status']=='PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS' and
        production['engineering_failed_requests']==production['missing_requests']==0 and
        production['physical_model_parameters']==PARAMETERS and production['optimizer_updates']==0 and
        production['test_GT_or_annotation_read'] is False and production['native_clock_matches_original_full_PTS'] is True and
        production['scientific_quality_claim'] is False and production['old_scientific_failed_gates_changed'] is False and
        production['old_packet_FAIL_reclassified'] is False and
        production['global_refiner_role']==production['global_VERIFY_role']=='TIME_ENABLED',
        'Incomplete or scientifically reclassified production cannot bind HALF')
    require(controller['status']=='PASS_CONTROLLER_ALL_BATCHES_NATURAL_TERMINALS_AND_FIRST_REPLAYS_NOT_QUALITY' and
        controller['global_completion_path']==production_ref['path'] and
        controller['global_completion_sha256']==production_ref['sha256'] and
        controller['coverage']==dict(source_count=426,actual_model_calls=1992,logical_requests=1995,batches=49) and
        controller['actual_total_model_calls_in_original_graph']==1992 and
        type(controller['actual_new_model_calls'])is int and 0<=controller['actual_new_model_calls']<=1992 and
        controller['old_successful_operations_repeated']==0,'Actual full CONTROL6 natural completion is required')
    require(len(production['actual_unique_MODEL_ids'])==len(set(production['actual_unique_MODEL_ids']))==1992 and
        len(production['actual_unique_MODEL_proofs'])==1992 and
        {row['consumer'] for row in production['actual_unique_MODEL_proofs']}==set(production['actual_unique_MODEL_ids']) and
        len(production['accepted_endpoint_request_ids'])==len(set(production['accepted_endpoint_request_ids']))==1330 and
        len(production['accepted_verification_event_ids'])==len(set(production['accepted_verification_event_ids']))==665 and
        len(production['actual_source_ids'])==426 and set(production['actual_source_ids'])=={str(i) for i in range(426)} and
        set(production['native_clock_original_bindings'])==set(production['actual_source_ids']),
        'Source/request/endpoint/VERIFY engineering coverage differs')
    require(technical['status']=='TECHNICAL_PACKAGE_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM' and
        technical['source_count']==426 and technical['window_count']==521 and technical['event_count']==665 and
        technical['nominal_requests']==1995 and technical['actual_MODEL_proofs']==1992 and
        technical['structural_no_MODEL_proofs']==3 and technical['production_completion_ref']==production_ref and
        technical['package_admission_created'] is False and technical['model_calls']==technical['new_ZIPs']==0,
        'Original full evidence lock must have its complete accepted technical binding')


def protocol_gate(protocol):
    require(protocol['schema']=='BOUNDARY_RESIDUAL_HALF_RISK_V1' and protocol['alpha_exact']=='1/2' and
        protocol['arms']==protocol['publication_priority']==HALF_ARMS and protocol['publication_limit']==3 and
        protocol['campaign_new_ZIP_total_limit']==5 and protocol['endpoint_role']=='TIME_ENABLED' and
        protocol['verification_applied'] is False and protocol['model_requests_extra']==0 and
        protocol['original_graph_or_batch_or_model_roles_modified'] is False and
        protocol['raw_model_outputs_modified'] is False and
        protocol['test_GT_annotation_training_or_manual_test_edit'] is False and
        protocol['alpha_grid_or_priority_tuning_prohibited'] is True and protocol['scientific_quality_claim'] is False,
        'Original fixed HALF protocol cannot be changed or tuned by this binder')


def lock_union(original,extra):
    result=dict(original)
    for path,sha in extra.items():
        require(valid_sha(sha) and (path not in result or result[path]==sha),'Lock union conflict')
        result[path]=sha
    require(all(result[path]==sha for path,sha in original.items()),'Accepted old closure cannot lose an entry')
    return result


def merge_history(old_rows,family_rows):
    require(isinstance(old_rows,list) and old_rows,'Original frozen canonical history is required')
    result=list(old_rows);known={row['canonical_SHA256'] for row in old_rows}
    require(all(valid_sha(row['canonical_SHA256']) for row in old_rows),'Original historical canonical SHA missing')
    for row in family_rows:
        require(row['canonical_SHA256'] not in known,'Original actual package duplicates its retained historical canonical identity')
        known.add(row['canonical_SHA256']);result.append(row)
    return result
