"""One explicit remaining-metadata recovery; never repeats the failed builder.

The original registration, three bindings, code and failure remain immutable.
The new, root-reviewed projection supplies project(reg)->dict only. This caller
creates the first plan and the previously unstarted tail, with actual provenance.
No media decoder, processor, model, GPU wrapper or final permission is invoked.
"""
import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import traceback

CAMPAIGN=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
ROOT=CAMPAIGN/'metadata_recovery_v1'
BOOTSTRAP=CAMPAIGN/'temporal_production_bootstrap_v1'
INPUT=CAMPAIGN/'temporal_production_inputs_v4'
RUNTIME=CAMPAIGN/'temporal_production_runtime_v4'
CONTROL=CAMPAIGN/'temporal_production_control_v3'
SCHEMA='EXPLICIT_REMAINING_METADATA_RECOVERY_V1'


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def bound(value,root):
    path=Path(value['path']).resolve()
    require(path.is_relative_to(root) and path.is_file() and sha(path)==value['sha256'],
        'Explicit recovery path/SHA changed or escaped')
    return path


def module(name,path):
    path=Path(path).resolve()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path,'Recovery module owner changed')
        return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


def preflight(path):
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5' and
        os.environ.get('CUDA_VISIBLE_DEVICES')=='','Recovery is a Linux CPU-only metadata child')
    path=Path(path).resolve();require(path.is_relative_to(ROOT),'Independent recovery protocol root required')
    protocol=read(path)
    require(protocol['schema']==SCHEMA and protocol['remaining_metadata_only'] is True and
        protocol['projection_interface_only'] is True and protocol['old_input_helpers_or_math_changed'] is False and
        protocol['old_head_bindings_or_registration_recreated'] is False and protocol['test_GT_read'] is False and
        protocol['formal_source_decode_calls_authorized']==protocol['processor_calls_authorized']==protocol['model_calls_authorized']==0,
        'Explicit remaining metadata scope only; helper/math changes need a separate root decision')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(protocol['deadline'].replace('Z','+00:00')),
        'Deadline: no new metadata recovery')
    required=protocol['required_code_files']
    for filename,digest in required.items():require(sha(filename)==digest,'Frozen original/recovery dependency changed')
    for file in Path(__file__).parent.glob('*.py'):
        require(required.get(str(file.resolve()))==sha(file),'Every actual recovery caller must be frozen')
    sys.path.insert(0,str(BOOTSTRAP/'code'))
    io=module('pb_io',BOOTSTRAP/'code/pb_io.py');c=module('pb_contract',BOOTSTRAP/'code/pb_contract.py')
    require(io.INPUT==INPUT and io.RUNTIME==RUNTIME and io.CONTROL==CONTROL,'Original explicit roots changed')
    config_path=bound(protocol['old_bootstrap_config_ref'],BOOTSTRAP)
    config=io.config(config_path)
    registration=bound(protocol['failed_input_registration_ref'],INPUT)
    input_reg=read(registration)
    require(input_reg['required_code_files']==config['required_code_files'],
        'The failed original registration/config code map changed')
    require(all(required.get(name)==digest for name,digest in config['required_code_files'].items()),
        'Recovery cannot replace any frozen original code SHA')
    old_projection=bound(protocol['old_failed_projection_ref'],INPUT/'code')
    require(old_projection==INPUT/'code/project_legacy.py' and
        config['required_code_files'].get(str(old_projection))==protocol['old_failed_projection_ref']['sha256'],
        'Original failed projection identity must remain frozen')
    failure_path=bound(protocol['old_failure_ref'],BOOTSTRAP/'bootstrap_run_01')
    require(failure_path==BOOTSTRAP/'bootstrap_run_01/failure.json' and
        not (BOOTSTRAP/'bootstrap_run_01/completion.json').exists(),'Original failed terminal must be retained')
    failure=read(failure_path)
    require(failure['status']=='FAILED_METADATA_BOOTSTRAP_RETAIN_PARTIAL_NO_WHOLE_CHAIN_RETRY' and
        failure['formal_media_decodes']==failure['processor_encodes']==failure['model_calls']==0,
        'Recovery only covers the actual metadata failure before formal work')
    expected={key:input_reg[key] for key in ('official_rules_ref','selected_uniform_development_role_ref',
        'reader_native_terminal_scope_ref')}
    require(protocol['reused_binding_refs']==expected,'Exactly the three original successful binding refs must be reused')
    for value in expected.values():bound(value,INPUT/'bindings')
    projection_path=bound(protocol['new_projection_ref'],CAMPAIGN)
    require(not projection_path.is_relative_to(INPUT/'code') and
        not projection_path.is_relative_to(BOOTSTRAP/'code') and projection_path!=old_projection and
        required.get(str(projection_path))==protocol['new_projection_ref']['sha256'] and
        protocol['new_projection_API']=='PURE_METADATA_PROJECT_REG_DICT_V1',
        'A separately reviewed new projection module is required; original code cannot be overwritten')
    admission_path=Path(protocol['recovery_admission_path']).resolve()
    require(admission_path.is_relative_to(ROOT) and admission_path.is_file(),'Main recovery admission is absent')
    admission=read(admission_path)
    require(admission['status']=='APPROVED_ONCE_REMAINING_METADATA_RECOVERY_NO_FORMAL_SOURCE_OR_GPU' and
        admission['recovery_protocol_sha256']==sha(path) and
        all(admission[key]==protocol[key] for key in ('old_bootstrap_config_ref','failed_input_registration_ref',
            'old_failure_ref','old_failed_projection_ref','new_projection_ref')) and
        admission['formal_source_decode_calls_authorized']==admission['processor_calls_authorized']==admission['model_calls_authorized']==0,
        'Root must admit this exact remaining recovery, old failure and new projection only')
    forbidden=(INPUT/'plan_01',INPUT/'cache_initialization.json',Path(input_reg['cache_root']),
        RUNTIME/'protocol.json',RUNTIME/'batches',RUNTIME/'bindings/capacity_grouping_receipt.json',
        CONTROL/'batch_index.json',CONTROL/'registration.json',BOOTSTRAP/'metadata_recovery_01',
        Path(input_reg['actual_preparation_permission_path']),
        Path(config['control_registration_template']['main_execution_admission_path']))
    require(all(not file.exists() for file in forbidden),
        'Previously started plan/cache/tail/formal permission exists; no automatic recovery or overwrite')
    sys.path.insert(0,str(INPUT/'code'))
    inputs=module('tp_io',INPUT/'code/tp_io.py')
    reg=inputs.registration(registration);inputs.metadata_permission(reg)
    return protocol,config,required,registration,input_reg,reg,io,c,inputs,projection_path,admission_path


def first_plan(protocol_path,protocol,registration,reg,io,projection_path,admission_path):
    projection=module('_explicit_recovery_new_projection',projection_path)
    require(callable(getattr(projection,'project',None)),'New pure projection must export project(reg)->dict')
    frozen=projection.project(reg)
    require(frozen['schema']==reg['schema'] and frozen['source_count']==426 and frozen['window_count']==521 and
        frozen['event_count']==665 and frozen['nominal_requests']==len(frozen['requests'])==1995 and
        frozen['new_model_calls']==frozen['new_media_decodes']==frozen['new_processor_encodes']==0 and
        frozen['request_membership_can_change_with_results'] is False,
        'Unchanged complete metadata graph and zero actual formal work required')
    recovery=dict(protocol_ref=io.ref(protocol_path),recovery_admission_ref=io.ref(admission_path),
        failed_registration_ref=protocol['failed_input_registration_ref'],old_failure_ref=protocol['old_failure_ref'],
        old_failed_projection_ref=protocol['old_failed_projection_ref'],actual_new_projection_ref=protocol['new_projection_ref'],
        original_registration_and_code_unchanged=True,original_projection_not_reclassified_as_success=True,
        formal_media_decodes=0,processor_encodes=0,model_calls=0)
    frozen['metadata_projection_recovery']=recovery
    target=INPUT/'plan_01';target.mkdir(exist_ok=False)
    io.save(target/'full_plan.json',frozen)
    io.save(target/'completion.json',dict(status='FROZEN_ALL_DUAL_COORDINATE_REQUESTS_NOT_DECODE_ADMISSION',
        schema=reg['schema'],registration_path=str(registration),registration_sha256=io.sha(registration),
        full_plan_sha256=io.sha(target/'full_plan.json'),actual_consumers=len(frozen['consumers']),
        nominal_requests=frozen['nominal_requests'],structural_unknown_requests=frozen['structural_unknown_requests'],
        metadata_projection_recovery=recovery,model_calls=0,processor_calls=0,media_decodes=0,
        old_packet_validation_failures_reclassified=False))


def remaining_metadata(config,required,registration,input_reg,reg,io,c,inputs,out):
    """The original, previously unstarted tail; all writes are create-x."""
    full_plan=io.INPUT/'plan_01/full_plan.json';plan=io.read(full_plan);plan['_file_sha256']=io.sha(full_plan)
    budget_template=io.read(io.bound(config['frozen_GPU_budget_ref']))
    budgets=c.actual_gpu_budget(budget_template,plan,config['frozen_GPU_budget_ref'],io.ref(full_plan))
    io.save(out/'actual_GPU_budget.json',budgets)
    prep=io.module('_explicit_recovery_metadata_initializer',io.INPUT/'code/prepare_source.py')
    prep.initialize(reg,registration) # Metadata only; cpu=False and no processor/AV.
    estimator=io.read(io.bound(config['source_storage_estimator_template_ref']))
    c.require(estimator['schema']=='PROSPECTIVE_SOURCE_STORAGE_ESTIMATOR_TEMPLATE_V1' and
        estimator['method'] in ('PC_SOURCE_BOUND_UNCOMPRESSED_CODE_ONLY','REPRESENTATIVE_LOSSLESS_RATIO_NONFIT_FORECAST') and
        estimator['forecast_fit_guaranteed'] is False and
        estimator['actual_batch_gate']=='UNCOMPRESSED_COMPLETE_SOURCE_BOUND_PLUS_RGB_STAGING_TRANSIENT_WITH_CURRENT_AVAILABLE_BYTES' and
        estimator['global_raw_fallback_forecast_may_be_NOT_FIT_THEORETICAL'] is True and
        estimator['actual_canonical_byte_growth_checked_before_each_source_input_write'] is True,
        'Only the previously frozen code bound/non-fit forecast is permitted')
    sys.path.insert(0,str(io.CONTROL/'code'));pc=io.module('pc_contract',io.CONTROL/'code/pc_contract.py')
    gpu=io.read(io.bound(config['GPU_host_resource_envelope_ref']));cpu=io.read(io.bound(config['CPU_resource_envelope_ref']))
    gpu_bytes=config['GPU_host_resource_bound']['memory_bytes'];pc.gpu_host_envelope(gpu,gpu_bytes)
    c.require(config['CPU_process_overhead_bound_bytes']>=cpu['conservative_overhead_bound_bytes']>=cpu['actual_peak_rss_kib']*1024,
        'Actual existing CPU process envelope required')
    size=io.read(io.RUN/'b_score_aligned_package_v4/config.json')['video_size'];est=[]
    for source in plan['sources']:
        sid=source['source_id'];rows=[row for row in plan['requests'] if row['source_id']==sid]
        groups={key:value for key,value in plan['RGB_groups'].items() if value['source_id']==sid}
        bound_value=pc.source_bound(source,rows,groups,size)
        est.append(dict(source_id=sid,source_sha256=source['source_sha256'],logical_request_ids=[row['request_id'] for row in rows],
            permanent_bytes=bound_value['permanent_bytes'],staging_bytes=bound_value['staging_bytes'],transient_bytes=bound_value['transient_bytes'],
            memory_bytes=bound_value['memory_bytes']+config['CPU_process_overhead_bound_bytes']))
    estimates=dict(schema='FROZEN_SOURCE_STORAGE_ESTIMATES_FOR_PROSPECTIVE_INPUTS_V1',global_graph_sha256=plan['_file_sha256'],
        sources=est,predictions_or_reference_metrics_used=False,actual_first_production_storage_observed=False,
        estimate_kind='CONSERVATIVE_UNCOMPRESSED_CODE_BOUND',estimator_template_ref=config['source_storage_estimator_template_ref'])
    io.save(out/'source_storage_estimates.json',estimates)
    live=io.snapshot();io.save(out/'actual_capacity_snapshot.json',live)
    raw_total=sum(row['permanent_bytes'] for row in est)
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
            'Representative smoke ratio is never a per-source fit guarantee')
        probe=ratio['probe_ref']
        c.require(Path(probe['path']).resolve().is_relative_to(io.CAMPAIGN) and len(probe['sha256'])==64,
            'Original successful probe ref required; no body reread or rerun')
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
    io.save(out/'capacity_grouping_receipt.json',capacity)
    capacity_ref=io.retain(io.ref(out/'capacity_grouping_receipt.json'),io.RUNTIME/'bindings/capacity_grouping_receipt.json')
    protocol=copy.deepcopy(config['runtime_protocol_template']);protocol.update(schema='TEMPORAL_PRODUCTION_RUNTIME_V4',
        input_root=str(io.INPUT),input_library_directory=str(io.INPUT/'code'),input_registration_ref=io.ref(registration),
        full_plan_ref=io.ref(full_plan),cache_initialization_ref=io.ref(io.INPUT/'cache_initialization.json'),
        selected_uniform_development_role_ref=input_reg['selected_uniform_development_role_ref'],
        endpoint_model_role=input_reg['endpoint_model_role'],verify_model_role='TIME_ENABLED',required_code_files=required,
        native_terminal_scope='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT',
        dual_coordinate_application='LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE',
        metadata_recovery_plan_completion_ref=io.ref(io.INPUT/'plan_01/completion.json'))
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
        CPU_process_overhead_bound_bytes=config['CPU_process_overhead_bound_bytes'],GPU_host_resource_bound=config['GPU_host_resource_bound'],
        metadata_recovery_plan_completion_ref=io.ref(io.INPUT/'plan_01/completion.json'))
    admission=Path(control['main_execution_admission_path']).resolve()
    c.require(admission.is_relative_to(io.CONTROL) and not admission.exists(),'Final main controller admission remains absent')
    control_path=io.CONTROL/'registration.json';io.save(control_path,control)
    return dict(input_registration_ref=io.ref(registration),full_plan_ref=io.ref(full_plan),
        metadata_recovery_plan_completion_ref=io.ref(io.INPUT/'plan_01/completion.json'),
        runtime_protocol_ref=io.ref(protocol_path),control_registration_ref=io.ref(control_path),batch_index_ref=io.ref(index_path),
        source_count=len(plan['sources']),logical_request_count=len(plan['requests']),actual_MODEL_budget=len(plan['consumers']),
        actual_GPU_budget_ref=io.ref(out/'actual_GPU_budget.json'),
        global_storage_nonfit_forecast_ref=io.ref(out/'global_storage_nonfit_forecast.json'))


def recover(path):
    p,config,required,registration,input_reg,reg,io,c,inputs,projection,admission=preflight(path)
    out=BOOTSTRAP/'metadata_recovery_01';out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json',dict(recovery_protocol_ref=io.ref(path),recovery_admission_ref=io.ref(admission),
        old_failure_ref=p['old_failure_ref'],failed_registration_ref=p['failed_input_registration_ref'],pid=os.getpid(),
        reused_binding_refs=p['reused_binding_refs'],old_failed_projection_ref=p['old_failed_projection_ref'],
        actual_new_projection_ref=p['new_projection_ref'],metadata_only=True,formal_media_decodes=0,processor_encodes=0,model_calls=0))
    try:
        first_plan(path,p,registration,reg,io,projection,admission)
        result=remaining_metadata(config,required,registration,input_reg,reg,io,c,inputs,out)
        io.save(out/'completion.json',dict(result,status='PASS_EXPLICIT_REMAINING_METADATA_RECOVERY_NOT_FORMAL_EXECUTION_ADMISSION',
            recovery_protocol_ref=io.ref(path),recovery_admission_ref=io.ref(admission),old_failure_ref=p['old_failure_ref'],
            failed_registration_ref=p['failed_input_registration_ref'],old_failed_projection_ref=p['old_failed_projection_ref'],
            actual_new_projection_ref=p['new_projection_ref'],old_binding_copies_and_registration_recreated=False,
            old_failure_or_code_modified=False,old_failed_projection_promoted_to_success=False,
            source_prepare_permission_created=False,controller_execution_admission_created=False,
            formal_media_decodes=0,processor_encodes=0,model_calls=0,
            future_main_source_permission_must_bind_this_completion_and_actual_new_projection=True))
    except BaseException as error:
        io.save(out/'failure.json',dict(status='FAILED_EXPLICIT_REMAINING_METADATA_RECOVERY_RETAIN_PARTIAL_NO_AUTORETRY',
            error=repr(error),traceback=traceback.format_exc(),old_failure_ref=p['old_failure_ref'],
            old_binding_copies_and_registration_recreated=False,formal_media_decodes=0,processor_encodes=0,model_calls=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--protocol',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';recover(args.protocol)
