"""Pure metadata freeze/capacity grouping. No source media, GT or model loader."""
import hashlib
import json
import re

SCHEMA='TEMPORAL_PRODUCTION_METADATA_BOOTSTRAP_V2'


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def actual_gpu_budget(template,plan,template_ref,full_plan_ref):
    """Derive once from the first frozen graph, before any model result."""
    actual=plan['consumers'];computed=[r['request_id'] for r in plan['requests'] if r['execution']=='MODEL']
    require(actual==computed and len(set(actual))==len(actual),'Exact frozen actual MODEL denominator/order required')
    if template.get('model_call_denominator_source')=='FIRST_FROZEN_PLAN_ACTUAL_MODEL_REQUESTS':
        maximum=template['maximum_nominal_calls']
        require(type(maximum)is int and maximum==1995 and len(plan['requests'])<=maximum and len(actual)<=maximum,
            'First plan actual/nominal calls exceed preregistered maximum; no fake maximum-as-actual budget')
    else:
        require(type(template['model_call_denominator'])is int and template['model_call_denominator']==len(actual),
            'Explicit integer GPU budget denominator differs from first frozen plan')
        maximum=template.get('maximum_nominal_calls',1995)
        require(type(maximum)is int and maximum<=1995 and len(actual)<=maximum,'Integer budget exceeds maximum registered calls')
    return dict(template,model_call_denominator=len(actual),maximum_nominal_calls=maximum,
        actual_model_request_ids=list(actual),budget_template_ref=template_ref,full_plan_ref=full_plan_ref,
        model_results_used_for_budget=False,derived_before_first_formal_model=True)


def group_sources(plan,estimates,snapshot,gpu_host_bytes,QA_memory_bytes,metadata_output_bytes):
    """Whole SOURCE order, two live batches, all future canonical estimates retained.

    Estimates are independently frozen metadata, never results or current predictions.
    Runtime still checks actual bytes before every operation; this is no fit guarantee.
    """
    require(estimates['schema']=='FROZEN_SOURCE_STORAGE_ESTIMATES_FOR_PROSPECTIVE_INPUTS_V1' and
        estimates['global_graph_sha256']==plan['_file_sha256'] and estimates['predictions_or_reference_metrics_used'] is False and
        estimates['actual_first_production_storage_observed'] is False and
        estimates['estimate_kind'] in ('CONSERVATIVE_CODE_BOUND_WITH_EXISTING_EXACT_CACHE_MEASUREMENTS',
                                    'CONSERVATIVE_UNCOMPRESSED_CODE_BOUND',
                                    'CODE_ESTIMATE_WITH_EXISTING_EXACT_CACHE_PROFILE_NO_STORAGE_GUARANTEE'),
        'A frozen, honestly typed prospective storage estimate is required')
    order=[s['source_id'] for s in plan['sources']];rows=estimates['sources']
    require([r['source_id'] for r in rows]==order and len(set(order))==len(order),'Storage estimates must cover every fixed source in order')
    total_permanent=0
    for source,row in zip(plan['sources'],rows):
        request_ids=[r['request_id'] for r in plan['requests'] if r['source_id']==source['source_id']]
        groups=[r for r in plan['RGB_groups'].values() if r['source_id']==source['source_id']]
        minimum_RGB=len(groups)*64*source['width']*source['height']*3
        require(row['source_sha256']==source['source_sha256'] and row['logical_request_ids']==request_ids and
            all(type(row[k])is int and row[k]>=0 for k in ('permanent_bytes','staging_bytes','transient_bytes','memory_bytes')) and
            row['memory_bytes']>0 and row['staging_bytes']>=minimum_RGB,
            'Full source identity/all roles/raw-RGB upper bound/actual integer byte estimate required')
        total_permanent+=row['permanent_bytes']
    require(all(type(x)is int and x>=0 for x in (gpu_host_bytes,QA_memory_bytes,metadata_output_bytes)) and gpu_host_bytes>0,
        'Typed byte envelopes required; no fixed GB/worker count')
    memory_budget=(snapshot['mem_available_bytes']-gpu_host_bytes-QA_memory_bytes)//2
    disk_budget=(snapshot['disk_available_bytes']-metadata_output_bytes)//2
    require(memory_budget>0 and disk_budget>0,'Current capacity cannot reserve two live complete-source batches')
    grouped=[];pending=[];mem=space=0
    for row in rows:
        live=row.get('original_gzip_fallback_permanent_bound_bytes',row['permanent_bytes'])+row['staging_bytes']+row['transient_bytes']
        require(row['memory_bytes']<=memory_budget and live<=disk_budget,
            'A complete source does not fit double-buffer capacity; no splitting/precision/member fallback')
        if pending and (mem+row['memory_bytes']>memory_budget or space+live>disk_budget):
            grouped.append(pending);pending=[];mem=space=0
        pending.append(row['source_id']);mem+=row['memory_bytes'];space+=live
    if pending:grouped.append(pending)
    require([sid for group in grouped for sid in group]==order,'Frozen source coverage/order changed')
    return grouped,dict(per_batch_memory_budget_bytes=memory_budget,per_batch_live_disk_budget_bytes=disk_budget,
        all_future_permanent_estimate_bytes=total_permanent,global_forecast_is_not_fit_guarantee=True,
        all_future_uncompressed_canonical_reserved_upfront=False,metadata_output_reserved_bytes=metadata_output_bytes,
        GPU_host_reserved_bytes=gpu_host_bytes,QA_memory_reserved_bytes=QA_memory_bytes,
        method='TWO_LIVE_WHOLE_SOURCE_CONTIGUOUS_BLOCKS_FROM_FROZEN_BYTE_ESTIMATES',
        actual_first_production_storage_observed=False,actual_future_capacity_checks_still_required=True)


def batch_document(plan,source_ids,index,prefix,runtime_schema,protocol_sha,budget,capacity_ref,source_order_sha):
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,70}',prefix) and '..' not in prefix,'Explicit unique safe GPU job prefix required')
    bid='B'+str(index).zfill(3);rows=[row for row in plan['requests'] if row['source_id'] in source_ids]
    actual=[row['request_id'] for row in rows if row['execution']=='MODEL']
    require(not rows or actual,'A structural-only source batch needs an explicit CPU-only structural protocol; no fake GPU0')
    value=dict(schema=runtime_schema,batch_id=bid,source_ids=source_ids,logical_request_ids=[row['request_id'] for row in rows],
        request_ids=actual,actual_model_call_budget=len(actual),global_graph_sha256=plan['_file_sha256'],
        protocol_sha256=protocol_sha,global_source_order_sha256=source_order_sha,capacity_receipt_ref=capacity_ref,
        membership_reason='FROZEN_SOURCE_ORDER_AND_ACTUAL_CAPACITY_ONLY',predictions_or_reference_metrics_used_for_membership=False,
        gpu_job_name=prefix+'_'+bid if actual else None,cpu_only_empty_batch=not rows)
    if actual:
        require(budget['model_call_denominator']==len(plan['consumers']) and budget['per_call_seconds']>0 and
            all(type(budget[k])is int and budget[k]>=0 for k in ('cold_load_seconds','queue_seconds','output_bytes_per_call','batch_fixed_output_bytes')),
            'Pre-frozen actual call denominator and conservative observed timing/output budget needed')
        import math
        value.update(gpu_max_seconds=budget['cold_load_seconds']+math.ceil(len(actual)*budget['per_call_seconds']),
            gpu_queue_seconds=budget['queue_seconds'],planned_GPU_output_bytes=budget['batch_fixed_output_bytes']+len(actual)*budget['output_bytes_per_call'])
    return value
