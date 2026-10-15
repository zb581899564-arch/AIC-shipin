"""Generate one immutable prospective metadata graph/cache/batch bootstrap.

No source decoding/CPU encoding/GPU wrapper/model call, and no final permissions.
Only root-approved metadata build may call this once after actual code deployment.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import traceback

import pb_contract as c
import pb_io as io


def build(path):
    io.host();config=io.config(path);out=io.BASE/'bootstrap_run_01';out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json',dict(config_ref=io.ref(path),pid=os.getpid(),metadata_only=True,actual_model_calls=0))
    try:
        required=dict(config['required_code_files'])
        for root in (io.INPUT,io.RUNTIME,io.CONTROL):
            for file in (root/'code').glob('*.py'):
                c.require(required.get(str(file.resolve()))==io.sha(file),'All input/runtime/control code paths must be globally frozen')
        input_reg=copy.deepcopy(config['input_registration_template'])
        for key,name in (('official_rules_ref','official_rules.json'),('selected_uniform_development_role_ref','uniform_role_selection.json'),
                         ('reader_native_terminal_scope_ref','reader_native_terminal_scope.json')):
            input_reg[key]=io.retain(input_reg[key],io.INPUT/'bindings'/name)
        input_reg.update(required_code_files=required,metadata_initialization_approved=True)
        c.require(input_reg['cache_policy']['independent_replay_code_sha256']==required[str(io.RUNTIME/'code/replay_batch.py')] and
            input_reg['cache_policy']['process_lock_backend']=='LINUX_PERSISTENT_FLOCK_V2' and
            Path(input_reg['cache_library_directory'])==io.CAMPAIGN/'production_stream_cache_v2/code',
            'Exact new runtime/code/flock policy binding required')
        permission=Path(input_reg['actual_preparation_permission_path']).resolve()
        c.require(permission.is_relative_to(io.INPUT) and not permission.exists(),'Builder cannot pre-create/consume an actual source permission')
        registration=io.INPUT/'registration.json';io.save(registration,input_reg)
        sys.path.insert(0,str(io.INPUT/'code'))
        inputs=io.module('tp_io',io.INPUT/'code/tp_io.py');projection=io.module('_bootstrap_projection',io.INPUT/'code/project_legacy.py')
        inputs.host();projection.main(registration) # once, metadata only
        full_plan=io.INPUT/'plan_01/full_plan.json';plan=io.read(full_plan);plan['_file_sha256']=io.sha(full_plan)
        budget_template=io.read(io.bound(config['frozen_GPU_budget_ref']))
        budgets=c.actual_gpu_budget(budget_template,plan,config['frozen_GPU_budget_ref'],io.ref(full_plan))
        io.save(out/'actual_GPU_budget.json',budgets)
        reg=inputs.registration(registration)
        prep=io.module('_bootstrap_metadata_initializer',io.INPUT/'code/prepare_source.py')
        prep.initialize(reg,registration) # cpu=False metadata/cache journal creation; no processor or AV
        # Estimates may be generated externally from this exact freshly frozen graph.
        estimator=io.read(io.bound(config['source_storage_estimator_template_ref']))
        c.require(estimator['schema']=='PROSPECTIVE_SOURCE_STORAGE_ESTIMATOR_TEMPLATE_V1' and
            estimator['method'] in ('PC_SOURCE_BOUND_UNCOMPRESSED_CODE_ONLY','REPRESENTATIVE_LOSSLESS_RATIO_NONFIT_FORECAST') and
            estimator['forecast_fit_guaranteed'] is False and
            estimator['actual_batch_gate']=='UNCOMPRESSED_COMPLETE_SOURCE_BOUND_PLUS_RGB_STAGING_TRANSIENT_WITH_CURRENT_AVAILABLE_BYTES' and
            estimator['global_raw_fallback_forecast_may_be_NOT_FIT_THEORETICAL'] is True and
            estimator['actual_canonical_byte_growth_checked_before_each_source_input_write'] is True,
            'Only the explicitly reviewed deterministic code byte estimator/frozen profile forecast is allowed')
        sys.path.insert(0,str(io.CONTROL/'code'));pc=io.module('pc_contract',io.CONTROL/'code/pc_contract.py')
        gpu=io.read(io.bound(config['GPU_host_resource_envelope_ref']));cpu=io.read(io.bound(config['CPU_resource_envelope_ref']))
        gpu_bytes=config['GPU_host_resource_bound']['memory_bytes'];pc.gpu_host_envelope(gpu,gpu_bytes)
        c.require(config['CPU_process_overhead_bound_bytes']>=cpu['conservative_overhead_bound_bytes']>=cpu['actual_peak_rss_kib']*1024,
            'Actual existing CPU process envelope required')
        size=io.read(io.RUN/'b_score_aligned_package_v4/config.json')['video_size'];est=[]
        for source in plan['sources']:
            sid=source['source_id'];rows=[row for row in plan['requests'] if row['source_id']==sid]
            groups={key:value for key,value in plan['RGB_groups'].items() if value['source_id']==sid}
            bound=pc.source_bound(source,rows,groups,size)
            est.append(dict(source_id=sid,source_sha256=source['source_sha256'],logical_request_ids=[row['request_id'] for row in rows],
                permanent_bytes=bound['permanent_bytes'],staging_bytes=bound['staging_bytes'],transient_bytes=bound['transient_bytes'],
                memory_bytes=bound['memory_bytes']+config['CPU_process_overhead_bound_bytes']))
        estimates=dict(schema='FROZEN_SOURCE_STORAGE_ESTIMATES_FOR_PROSPECTIVE_INPUTS_V1',global_graph_sha256=plan['_file_sha256'],
            sources=est,predictions_or_reference_metrics_used=False,actual_first_production_storage_observed=False,
            estimate_kind='CONSERVATIVE_UNCOMPRESSED_CODE_BOUND',estimator_template_ref=config['source_storage_estimator_template_ref'])
        io.save(out/'source_storage_estimates.json',estimates)
        live=io.snapshot();io.save(out/'actual_capacity_snapshot.json',live)
        raw_total=sum(row.get('original_gzip_fallback_permanent_bound_bytes',row['permanent_bytes']) for row in est)
        forecast=dict(raw_uncompressed_canonical_code_estimate_bytes=raw_total,
            raw_theoretical_capacity_status='NOT_FIT_THEORETICAL' if raw_total>live['disk_available_bytes'] else 'WITHIN_CURRENT_BYTES_THEORETICAL_ONLY',
            forecast_fit_guaranteed=False,forecast_used_for_batch_membership_or_capacity_admission=False,
            all_global_raw_reserved_before_model=False,actual_permanent_growth_checked_per_batch=True)
        if estimator['method']=='REPRESENTATIVE_LOSSLESS_RATIO_NONFIT_FORECAST':
            ratio=io.read(io.bound(estimator['representative_ratio_ref']))
            c.require(ratio['schema']=='REPRESENTATIVE_EXACT_CACHE_STORAGE_RATIO_NONFIT_FORECAST_V1' and
                ratio['independent_exact_roundtrip_verified'] is True and ratio['forecast_fit_guaranteed'] is False and
                ratio['unsupported_dictionary_uses_original_gzip'] is True and
                all(type(ratio[k])is int and ratio[k]>0 for k in ('new_LUT_gzip_bytes','original_gzip_bytes','logical_tensor_bytes')),
                'Representative smoke ratio is a non-fit diagnostic, never per-source compression guarantee')
            # Root's immutable receipt binds the already verified successful probe.
            # No probe rerun or successful tensor/probe body reread here.
            probe=ratio['probe_ref']
            c.require(Path(probe['path']).resolve().is_relative_to(io.CAMPAIGN) and
                isinstance(probe['sha256'],str) and len(probe['sha256'])==64,'Original probe provenance ref required')
            from fractions import Fraction
            observed=Fraction(ratio['new_LUT_gzip_bytes'],ratio['logical_tensor_bytes'])
            forecast.update(representative_ratio_ref=estimator['representative_ratio_ref'],
                representative_LUT_gzip_per_logical_byte_exact=str(observed),
                representative_LUT_gzip_per_original_gzip_byte_exact=str(Fraction(ratio['new_LUT_gzip_bytes'],ratio['original_gzip_bytes'])),
                representative_global_nonfit_estimate_bytes=(raw_total*observed.numerator+observed.denominator-1)//observed.denominator,
                new_formal_tensor_codec_eligibility_observed=False)
        io.save(out/'global_storage_nonfit_forecast.json',forecast)
        grouped,capacity=c.group_sources(plan,estimates,live,gpu_bytes,config['QA_memory_bound_bytes'],config['metadata_output_bound_bytes'])
        capacity.update(snapshot_ref=io.ref(out/'actual_capacity_snapshot.json'),source_storage_estimates_ref=io.ref(out/'source_storage_estimates.json'))
        io.save(out/'capacity_grouping_receipt.json',capacity);capacity_ref=io.ref(out/'capacity_grouping_receipt.json')
        protocol=copy.deepcopy(config['runtime_protocol_template']);protocol.update(schema='TEMPORAL_PRODUCTION_RUNTIME_V4',
            input_root=str(io.INPUT),input_library_directory=str(io.INPUT/'code'),input_registration_ref=io.ref(registration),
            full_plan_ref=io.ref(full_plan),cache_initialization_ref=io.ref(io.INPUT/'cache_initialization.json'),
            selected_uniform_development_role_ref=input_reg['selected_uniform_development_role_ref'],
            endpoint_model_role=input_reg['endpoint_model_role'],verify_model_role='TIME_ENABLED',required_code_files=required,
            native_terminal_scope='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT',
            dual_coordinate_application='LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE')
        cache=inputs.libraries(reg)['cache'].LeaseStore(reg['cache_root'])
        protocol['cache_global_request_lock_ref']=cache.ref('permanent/proofs/global_source_request_lock.json')
        protocol_path=io.RUNTIME/'protocol.json';io.save(protocol_path,protocol)
        batches=[];batch_refs=[]
        for index,source_ids in enumerate(grouped):
            batch=c.batch_document(plan,source_ids,index,config['unique_gpu_job_prefix'],protocol['schema'],io.sha(protocol_path),
                budgets,capacity_ref,c.digest([s['source_id'] for s in plan['sources']]))
            batch['actual_GPU_budget_ref']=io.ref(out/'actual_GPU_budget.json')
            batch_path=io.RUNTIME/'batches'/(batch['batch_id']+'.json');io.save(batch_path,batch);batch_refs.append(io.ref(batch_path));batches.append(batch)
        pr=io.module('pr_contract',io.RUNTIME/'code/pr_contract.py');pc.full_coverage(plan,batches,pr.batch_membership)
        index_path=io.CONTROL/'batch_index.json';io.save(index_path,dict(global_graph_sha256=plan['_file_sha256'],batch_refs=batch_refs,
            source_order_sha256=c.digest([s['source_id'] for s in plan['sources']]),membership_results_used=False))
        control=copy.deepcopy(config['control_registration_template'])
        control.update(schema='TEMPORAL_PRODUCTION_CONTROL_V3',input_root_name=io.INPUT.name,runtime_root_name=io.RUNTIME.name,
            cache_version_root_name='production_stream_cache_v2',cache_library_directory=input_reg['cache_library_directory'],
            runtime_protocol_ref=io.ref(protocol_path),frozen_batch_index_ref=io.ref(index_path),global_graph_sha256=plan['_file_sha256'],
            required_code_files=required,current_official_rule_ref=input_reg['official_rules_ref'],
            CPU_resource_envelope_ref=config['CPU_resource_envelope_ref'],GPU_host_resource_envelope_ref=config['GPU_host_resource_envelope_ref'],
            CPU_process_overhead_bound_bytes=config['CPU_process_overhead_bound_bytes'],GPU_host_resource_bound=config['GPU_host_resource_bound'])
        admission=Path(control['main_execution_admission_path']).resolve()
        c.require(admission.is_relative_to(io.CONTROL) and not admission.exists(),'Final main controller admission must remain absent')
        control_path=io.CONTROL/'registration.json';io.save(control_path,control)
        io.save(out/'completion.json',dict(status='PASS_ONCE_METADATA_GRAPH_CACHE_BATCH_BOOTSTRAP_NOT_FORMAL_EXECUTION_ADMISSION',
            config_ref=io.ref(path),input_registration_ref=io.ref(registration),full_plan_ref=io.ref(full_plan),
            runtime_protocol_ref=io.ref(protocol_path),control_registration_ref=io.ref(control_path),batch_index_ref=io.ref(index_path),
            source_count=len(plan['sources']),logical_request_count=len(plan['requests']),actual_MODEL_budget=len(plan['consumers']),
            global_storage_nonfit_forecast_ref=io.ref(out/'global_storage_nonfit_forecast.json'),
            actual_GPU_budget_ref=io.ref(out/'actual_GPU_budget.json'),
            source_prepare_permission_created=False,controller_execution_admission_created=False,
            formal_media_decodes=0,processor_encodes=0,model_calls=0,old_success_files_modified=False,
            current_byte_estimate_may_STOP_actual_future_fit_still_required=True))
    except BaseException as error:
        io.save(out/'failure.json',dict(status='FAILED_METADATA_BOOTSTRAP_RETAIN_PARTIAL_NO_WHOLE_CHAIN_RETRY',
            error=repr(error),traceback=traceback.format_exc(),formal_media_decodes=0,processor_encodes=0,model_calls=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';build(args.config)
