"""Registered original-B20 controller; wait existing CPU cohort, never redo it."""
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path

import cohort_run_common_07 as r

OUT=r.BASE/'cohort_chain_07'


def state(stage,**extra):
    value=dict(stage=stage,utc=r.utc(),**extra)
    p=OUT/'state.json.pending';p.write_text(__import__('json').dumps(value,indent=2),encoding='utf-8');p.replace(OUT/'state.json')
    print(__import__('json').dumps(value),flush=True)


def run(stage,argv,gpu=False):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1',PYTHONNOUSERSITE='1',HF_HOME=str(r.RUN/'cache/hf'),
        XDG_CACHE_HOME=str(r.RUN/'cache'),TMPDIR=str(r.RUN/'tmp'),TORCH_HOME=str(r.RUN/'cache/torch'))
    if not gpu:env['CUDA_VISIBLE_DEVICES']=''
    with (OUT/(stage+'.log')).open('xb') as log:
        p=subprocess.Popen(argv,cwd=r.BASE/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        state(stage+'_RUNNING',argv=argv,child_pid=p.pid,disk_free_bytes=shutil.disk_usage(r.BASE).free,
            current_memory_available=[x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')])
        code=p.wait()
    r.save(OUT/(stage+'.terminal.json'),dict(argv=argv,exit_code=code,utc=r.utc()))
    if code:raise RuntimeError(stage+' failed; preserve successful work, no same-chain restart')


def freeze(reg):
    admission,_,rows=r.inputs()
    files={}
    def include(path,digest=None):
        path=Path(path);actual=r.sha(path)
        if digest and actual!=digest:raise ValueError('Registered source/input/code changed: '+str(path))
        if str(path) in files and files[str(path)]!=actual:raise ValueError('Source-lock identity conflict')
        files[str(path)]=actual
    for path,digest in reg['implementation_files'].items():include(path,digest)
    include(r.ACCEPTANCE);include(r.BASE/'direct_cohort_06/completion.json')
    include(r.BASE/'cohort_inference_registration_07.json');include(r.BASE/'cohort_gpu_budget_07.json')
    for group in ('runtime_files','processor_assets'):
        for path,digest in admission['runtime_identity'][group].items():include(path,digest)
    for source in admission['sources']:
        include(source['native_clock_path'],source['native_clock_sha256'])
        include(Path(source['native_clock_path']).with_name('mapping.json'))
    for entry,proof,meta in rows:
        include(entry['proof_path'],entry['proof_sha256']);include(proof['input_path'],proof['input_sha256'])
        include(meta['source_path'],meta['source_sha256']);include(meta['frame_array_path'],meta['frame_array_sha256'])
    config_path=r.RUN/'b_score_aligned_package_v4/config.json';include(config_path)
    config=r.read(config_path)
    for key in ('model_dir','b_adapter'):
        for path in Path(config[key]).iterdir():
            if path.is_file() and path.suffix in ('.safetensors','.json','.txt','.jinja'):include(path)
    for folder in ('b_score_aligned_package_v4','baseline_a_pts_v1','baseline_a_pts_v1/vendor',
                   'balanced_two_window_risk_v3','temporal_sft8b_v1','resource_unlimited_v1_20261007'):
        for path in (r.RUN/folder).glob('*.py'):include(path)
    r.save(r.LOCK,dict(status='FROZEN_ACTUAL20_NATIVE_INPUTS_ORIGINAL_B_CODE_AND_WEIGHTS',files=files,
        registered_sources=20,windows=len(rows),model_parameters=8782459120,optimizer_updates=0,
        unique_gpu_name=r.NAME,utc=r.utc(),human_reference_labels_not_in_inference=True))
    return len(rows),len(files)


def main():
    if socket.gethostname()!='inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') in (None,''):
        raise ValueError('Parent chain requires current actual nonempty GPU index')
    reg=r.read(r.BASE/'cohort_inference_registration_07.json')
    if reg['unique_gpu_name']!=r.NAME or reg['sources']!=20 or reg['new_optimizer_updates']:
        raise ValueError('New20 original-B inference scope changed')
    for path,digest in reg['implementation_files'].items():r.check_file(path,digest)
    OUT.mkdir(exist_ok=False)
    r.save(OUT/'launch_claim.json',dict(pid=os.getpid(),utc=r.utc(),registration_sha256=r.sha(r.BASE/'cohort_inference_registration_07.json')))
    try:
        state('WAIT_UNIQUE_EXISTING_DIRECT_COHORT06_NO_PREPARE_RESTART')
        while not (r.BASE/'direct_cohort_06/completion.json').exists():
            if (r.BASE/'direct_cohort_06/failure.json').exists():raise ValueError('Existing CPU cohort actually failed; no GPU admission')
            time.sleep(15)
        run('INDEPENDENT_ALL20_INPUT_REVIEW',[sys.executable,'-B',str(r.BASE/'code/admit_cohort_inputs_07.py')])
        acceptance,_,inputs=r.inputs()
        prior=r.read(reg['prior_resource_path']);r.check_file(reg['prior_resource_path'],reg['prior_resource_sha256'])
        if prior['status']!='completed' or prior['exit_code'] or prior['name']!=reg['prior_gpu_name']:
            raise ValueError('Previous observed original-B cost is not an actual completed run')
        cost=prior['charged_seconds'];max_seconds=math.ceil(2*(cost+cost*len(inputs)/116))
        r.save(r.BASE/'cohort_gpu_budget_07.json',dict(windows=len(inputs),max_seconds=max_seconds,
            formula='ceil(2*(actual_previous_job_cost+actual_previous_job_cost*new_window_count/116))',
            prior_resource_sha256=reg['prior_resource_sha256'],prior_seconds=cost,optimizer_updates=0))
        state('FREEZE_SOURCE_CODE_INPUTS_AND_ORIGINAL_B_BEFORE_GPU',windows=len(inputs),max_seconds=max_seconds)
        windows,files=freeze(reg)
        state('ALL20_INPUTS_FROZEN_NOT_YET_MODEL_RESULTS',windows=windows,files=files,source_lock_sha256=r.sha(r.LOCK))
        wrapper=[sys.executable,'-B',str(r.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name',r.NAME,'--max-seconds',str(max_seconds),'--queue-seconds',str(reg['queue_seconds']),
            '--planned-output-bytes',str((64<<20)+(32<<10)*windows),'--capacity-reason',
            'All20 actual original native64 CPU inputs independently accepted, same B8782459120 and prior observed22414MiB peak; shared unique lock and dynamic current capacity, no fixed utilization limits',
            '--',sys.executable,'-B',str(r.BASE/'code/infer_cohort_07.py')]
        run('ORIGINAL_B_SHARED_GPU_WRAPPER',wrapper,gpu=True)
        resource,resource_sha=r.resource_terminal()
        state('ALL_ACTUAL_B_CALLS_COMPLETE',charged_seconds=resource['charged_seconds'],resource_sha256=resource_sha)
        run('INDEPENDENT_CPU_REPLAY_EXPORT',[sys.executable,'-B',str(r.BASE/'code/replay_cohort_07.py')])
        r.save(OUT/'completion.json',dict(status='PASS_B20_EXPORT_PENDING_FROZEN_SCREEN_AND_CONFIRM_NOT_PACKAGE',
            registered_sources=20,windows=windows,new_optimizer_updates=0,resource_terminal_sha256=resource_sha,
            charged_seconds=resource['charged_seconds'],developer_export_acceptance_sha256=r.sha(r.BASE/'developer_export_acceptance.json'),
            prediction_export_sha256=r.sha(r.BASE/'developer_prediction_export.json'),utc=r.utc(),candidate_package_admitted=False))
        state('B20_EXPORT_COMPLETE_PENDING_HUMAN_PROXY_COMPARISON')
    except BaseException:
        r.save(OUT/'failure.json',dict(status='FAILED_NEW20_CHAIN_KEEP_ALL_SUCCESS_RAW_AND_COST',utc=r.utc(),traceback=traceback.format_exc()))
        state('FAILED_NO_SAME_CHAIN_OR_SUCCESSFUL_MODEL_RESTART')
        raise


if __name__=='__main__':main()
