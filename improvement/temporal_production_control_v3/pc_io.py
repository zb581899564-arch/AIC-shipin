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
BASE=CAMPAIGN/'temporal_production_control_v3';INPUT=CAMPAIGN/'temporal_production_inputs_v4'
RUNTIME=CAMPAIGN/'temporal_production_runtime_v4'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


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


def module(name,path):
    path=Path(path).resolve()
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path,'Control import namespace shadowed');return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value


def load(registration_path):
    global INPUT,RUNTIME
    registration_path=Path(registration_path).resolve();require(registration_path.is_relative_to(BASE),'New independent control root required')
    reg=read(registration_path)
    INPUT=CAMPAIGN/reg['input_root_name'];RUNTIME=CAMPAIGN/reg['runtime_root_name']
    require(INPUT.parent==RUNTIME.parent==CAMPAIGN and INPUT.name=='temporal_production_inputs_v4' and
        RUNTIME.name=='temporal_production_runtime_v4','Explicit independent input v3/runtime v3 roots required')
    require(reg['schema']==SCHEMA and reg['training'] is False and reg['test_GT_read'] is False and reg['old_successes_modified'] is False and
        reg['whole_graph_batches_and_roles_frozen_before_first_model'] is True and reg['main_controller_execution_approved'] is True,
        'Main frozen prospective execution bootstrap/admission required')
    for name,digest in reg['required_code_files'].items():require(sha(name)==digest,'Frozen control/library code changed')
    for path in Path(__file__).parent.glob('*.py'):require(reg['required_code_files'].get(str(path.resolve()))==sha(path),'All control files must be frozen')
    bound(reg['current_official_rule_ref'],(BASE,INPUT,RUNTIME))
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
        admission['allow_controller_issue_batch_gpu_admission'] is True,'Root has not granted concrete automatic batch execution')
    runtime_protocol=bound(reg['runtime_protocol_ref'],(RUNTIME,))
    require(read(runtime_protocol)['input_root']==str(INPUT),'Runtime/input version/root configuration differs')
    index=read(bound(reg['frozen_batch_index_ref'],(BASE,)))
    batches=[read(bound(ref,(RUNTIME,))) for ref in index['batch_refs']]
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
