"""Control-only helpers and immutable bootstrap. No pixels/GT/model loader."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

from pc_contract import SCHEMA,require

HOME=Path('/home/inspur/aic_video_work');CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
BASE=CAMPAIGN/'temporal_production_control_v5';INPUT=CAMPAIGN/'temporal_production_inputs_v5'
RUNTIME=CAMPAIGN/'temporal_production_runtime_v5'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ORIGINAL_CONTROL=CAMPAIGN/'temporal_production_control_v4'
IMPORT_DIRECTORIES=tuple(RUN/name for name in ('b_score_aligned_package_v4','baseline_a_pts_v1',
    'baseline_a_pts_v1/vendor','balanced_two_window_risk_v3','temporal_sft8b_v1','resource_unlimited_v1_20261007'))


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())


def append(path,row):
    with Path(path).open('a',encoding='utf-8') as stream:stream.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())


def rows(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def bound(ref,roots):
    path=Path(ref['path']).resolve();require(any(path.is_relative_to(root) for root in roots) and path.is_file() and sha(path)==ref['sha256'],
        'Frozen bootstrap path/SHA changed or escaped');return path


def official_rule_leaf(ref):
    inherited=CAMPAIGN/'temporal_production_inputs_v4/bindings/official_rules.json'
    if Path(ref['path']).resolve()==inherited:
        require(ref['sha256']=='b3dc2b7c080145efa3d72f413f4bb6fa8081f55b00bda97000fe83ed8284945b' and
            inherited.is_file() and sha(inherited)==ref['sha256'],
            'Only the exact successful original official-rule leaf may be inherited')
        return inherited
    return bound(ref,(BASE,INPUT,RUNTIME))


def module(name,path):
    path=Path(path).resolve()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path,'Control import namespace shadowed');return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value


def import_environment_recovery(reg):
    """Read immutable pre-import failure evidence; never imports a runtime/model."""
    original_path=bound(reg['original_control_registration_ref'],(ORIGINAL_CONTROL,))
    require(original_path==ORIGINAL_CONTROL/'registration.json','Only the actual original CONTROL4 registration may be inherited')
    original=read(original_path)
    changed={'schema','required_code_files','main_execution_admission_path','final_main_execution_admission_required_status'}
    require(original['schema']=='TEMPORAL_PRODUCTION_CONTROL_V4' and
        all(reg[key]==value for key,value in original.items() if key not in changed),
        'Environment recovery cannot change graph/batches/roles/budgets/cache/input/runtime semantics')
    require(all(reg['required_code_files'].get(key)==value for key,value in original['required_code_files'].items()),
        'Every original frozen code SHA must remain in the new control map')
    ref=reg['explicit_import_environment_recovery_ref'];path=bound(ref,(BASE,))
    require(path==BASE/'import_environment_recovery_01.json','Independent explicit import recovery receipt required')
    value=read(path)
    expected=dict(PYTHONPATH=os.pathsep.join(map(str,IMPORT_DIRECTORIES)),PYTHONDONTWRITEBYTECODE='1',AIC_WORK_ROOT=str(HOME))
    require(value['schema']=='FROZEN_IMPORT_ENVIRONMENT_RECOVERY_V1' and
        value['original_control_registration_ref']==reg['original_control_registration_ref'] and
        value['explicit_child_environment']==reg['explicit_child_environment']==expected and
        value['source_decode_calls_before_recovery']==value['processor_calls_before_recovery']==value['model_calls_before_recovery']==0 and
        value['old_failure_promoted_to_success'] is False and value['metadata_or_successful_preparation_repeated'] is False,
        'Only the frozen explicit original-helper lookup environment may change')
    failure_path=bound(value['original_control_failure_ref'],(ORIGINAL_CONTROL/'run_01',))
    journal_path=bound(value['original_controller_journal_ref'],(ORIGINAL_CONTROL/'run_01',))
    failure=read(failure_path);journal=rows(journal_path)
    require(failure_path==ORIGINAL_CONTROL/'run_01/failure.json' and
        failure['status']=='FAILED_CONTROL_PRESERVE_ALL_ATTEMPTS_SUCCESS_RAW_COSTS' and
        failure['journal_sha256']==value['original_controller_journal_ref']['sha256'] and
        not (ORIGINAL_CONTROL/'run_01/completion.json').exists(),'Original actual failed terminal/journal must remain failed')
    begins=[row for row in journal if row['event']=='BEGIN'];ends=[row for row in journal if row['event']=='FAILED']
    ids=value['old_failed_source_ids']
    require(len(journal)==20 and len(begins)==len(ends)==len(ids)==10 and len(set(ids))==10 and
        [row['item'] for row in begins]==ids and len({row['item'] for row in ends})==10 and
        {row['item'] for row in ends}==set(ids) and
        all(row['phase']=='SOURCE_PREPARE' for row in journal) and all(row['exit_code']==1 for row in ends),
        'This explicit recovery only covers the ten actual pre-import SOURCE failures, with no successful stage')
    require(all(next(i for i,row in enumerate(journal) if row['item']==sid and row['event']=='BEGIN')<
        next(i for i,row in enumerate(journal) if row['item']==sid and row['event']=='FAILED') for sid in ids),
        'Every unique failed source must follow its own original BEGIN; concurrent completion order is not a scientific gate')
    require(set(value['old_failed_source_log_refs'])==set(ids),'Every old failed source log must be retained')
    for row in ends:
        log_ref=value['old_failed_source_log_refs'][row['item']]
        log=bound(log_ref,(ORIGINAL_CONTROL/'run_01/logs',))
        require(log_ref==dict(path=row['log_path'],sha256=row['log_sha256']) and
            "ModuleNotFoundError: No module named 'exact_pts'" in log.read_text(),
            'Old failure is not the frozen missing exact_pts import; no broad retry')
    diagnosis=read(bound(value['no_source_artifacts_diagnosis_ref'],(ORIGINAL_CONTROL/'run_01',)))
    require(value['no_source_artifacts_counts']=={key:0 for key in value['no_source_artifacts_counts']} and
        value['no_source_artifacts_counts']==diagnosis['narrow_top_proofs_counts'] and
        diagnosis['actual_source_decode_evidence_files']==diagnosis['CPU_input_proofs']==diagnosis['new_decoder_processor_model_calls']==0 and
        diagnosis['controller_failure_ref']==value['original_control_failure_ref'] and
        value['no_source_artifacts_counts'] and diagnosis==value['no_source_artifacts_diagnosis_exact'],
        'The original zero-source-artifact diagnostic must stay byte-bound and unchanged')
    for module_name,owner in value['actual_module_owner_refs'].items():
        owner_path=bound(owner,(RUN,HOME/'temporal_refinement_pilot_20261011/dev_01'))
        require(owner_path.parent in IMPORT_DIRECTORIES or module_name=='original_runtime',
            'Helper escaped the exact declared original import owners')
        require(reg['required_code_files'].get(str(owner_path))==owner['sha256'],
            'Actual helper owner SHA must be frozen, including explicitly recovered transitive helpers')
    return value


def load(registration_path):
    global INPUT,RUNTIME
    registration_path=Path(registration_path).resolve();require(registration_path.is_relative_to(BASE),'New independent control root required')
    reg=read(registration_path)
    INPUT=CAMPAIGN/reg['input_root_name'];RUNTIME=CAMPAIGN/reg['runtime_root_name']
    require(INPUT.parent==RUNTIME.parent==CAMPAIGN and INPUT.name=='temporal_production_inputs_v5' and
        RUNTIME.name=='temporal_production_runtime_v5','Explicit independent input v3/runtime v3 roots required')
    require(reg['schema']==SCHEMA and reg['training'] is False and reg['test_GT_read'] is False and reg['old_successes_modified'] is False and
        reg['whole_graph_batches_and_roles_frozen_before_first_model'] is True and reg['main_controller_execution_approved'] is True,
        'Main frozen prospective execution bootstrap/admission required')
    for name,digest in reg['required_code_files'].items():require(sha(name)==digest,'Frozen control/library code changed')
    for path in Path(__file__).parent.glob('*.py'):require(reg['required_code_files'].get(str(path.resolve()))==sha(path),'All control files must be frozen')
    recovery=import_environment_recovery(reg)
    official_rule_leaf(reg['current_official_rule_ref'])
    cpu_envelope=read(bound(reg['CPU_resource_envelope_ref'],(BASE,CAMPAIGN)))
    gpu_envelope=read(bound(reg['GPU_host_resource_envelope_ref'],(BASE,CAMPAIGN)))
    bound(cpu_envelope['actual_proof_ref'],(CAMPAIGN,RUN))
    bound(gpu_envelope['maximum_shard_manifest_ref'],(CAMPAIGN,RUN))
    require(cpu_envelope['actual_peak_rss_kib']>0 and reg['CPU_process_overhead_bound_bytes']>=cpu_envelope['conservative_overhead_bound_bytes']>=
        cpu_envelope['actual_peak_rss_kib']*1024,'CPU overhead envelope is not backed by a positive actual process peak')
    from pc_contract import gpu_host_envelope
    gpu_host_envelope(gpu_envelope,reg['GPU_host_resource_bound']['memory_bytes'])
    if gpu_envelope['status']=='OBSERVATION_UNAVAILABLE_WITH_CODE_BOUNDED_ENVELOPE':
        for key in ('CPU_resource_envelope_ref','model_identity_ref','existing_loader_code_ref',
                    'model_architecture_metadata_ref','maximum_actual_logical_prefill_tensor_ref'):
            bound(gpu_envelope[key],(CAMPAIGN,RUN))
        for row in gpu_envelope['existing_resource_or_snapshot_metadata']:
            if row['present']:bound(row['ref'],(CAMPAIGN,RUN))
    else:bound(gpu_envelope['observed_peak_proof_ref'],(CAMPAIGN,RUN))
    admission_path=Path(reg['main_execution_admission_path']).resolve()
    require(admission_path.is_relative_to(BASE) and admission_path.is_file(),'Main execution admission root required')
    admission=read(admission_path)
    require(admission['status']=='PASS_MAIN_CONTROLLED_PRODUCTION_BOOTSTRAP_AND_EXECUTION' and admission['registration_sha256']==sha(registration_path) and
        admission['allow_controller_issue_batch_gpu_admission'] is True and
        admission['explicit_import_environment_recovery_ref']==reg['explicit_import_environment_recovery_ref'] and
        admission['original_control_failure_ref']==recovery['original_control_failure_ref'] and
        admission['old_failed_source_ids']==recovery['old_failed_source_ids'] and
        admission['recovery_scope']=='IMPORT_ENVIRONMENT_ONLY_NO_SUCCESSFUL_STAGE_REPLAY',
        'Root has not granted this exact concrete import-environment recovery')
    runtime_protocol=bound(reg['runtime_protocol_ref'],(RUNTIME,))
    require(read(runtime_protocol)['input_root']==str(INPUT),'Runtime/input version/root configuration differs')
    index_path=bound(reg['frozen_batch_index_ref'],(ORIGINAL_CONTROL,))
    require(index_path==ORIGINAL_CONTROL/'batch_index.json','Only the original successful immutable batch-index leaf may be reused')
    index=read(index_path)
    batches=[read(bound(ref,(RUNTIME,))) for ref in index['batch_refs']]
    for batch in batches:
        bound(batch['actual_GPU_budget_ref'],(CAMPAIGN/'temporal_production_bootstrap_v2',))
    sys.path.insert(0,str(RUNTIME/'code'));runtime_io=module('pr_io',RUNTIME/'code/pr_io.py')
    first_real=next(batch for batch in batches if batch['request_ids'])
    context=runtime_io.load(runtime_protocol,first_real['batch_id'],require_admission=False)
    require(reg['global_graph_sha256']==index['global_graph_sha256']==context['protocol']['full_plan_ref']['sha256'],
        'Whole global request graph differs from original root bootstrap')
    require(context['lib']['input_reg']['cache_library_directory']==reg['cache_library_directory'] and
        Path(reg['cache_library_directory']).name=='code' and Path(reg['cache_library_directory']).parent.name==reg['cache_version_root_name'],
        'Explicit new cache version/root differs; no implicit old-cache upgrade')
    require(reg['cache_version_root_name']=='production_stream_cache_v2' and
        context['store'].policy['process_lock_backend']=='LINUX_PERSISTENT_FLOCK_V2','New parallel cache v2 persistent flock policy required')
    return dict(reg=reg,registration_path=registration_path,runtime_protocol=runtime_protocol,index=index,batches=batches,
        runtime_io=runtime_io,context=context,plan=context['plan'],lib=context['lib'],store=context['store'])


def host(parent=False):
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5','Linux actual control host required')
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')) if parent else os.environ.get('CUDA_VISIBLE_DEVICES')=='',
        'Parent CUDA nonempty; CPU child alone hides CUDA')


def before_new_operation(reg):
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline'].replace('Z','+00:00')),
        'Deadline reached: no new source/processor/job; existing jobs must finish naturally')


def snapshot(cache_root):
    import shutil
    mem={line.split(':')[0]:int(line.split(':')[1].split()[0])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    return dict(utc=utc(),mem_available_bytes=mem['MemAvailable'],disk_available_bytes=shutil.disk_usage(cache_root).free,
        affinity_cpus=len(os.sched_getaffinity(0)),load_1min=os.getloadavg()[0])
