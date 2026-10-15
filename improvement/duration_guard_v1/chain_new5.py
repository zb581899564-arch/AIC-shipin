"""Unique new5 original-B controller after all actual CPU inputs; independent replay."""
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path
import new5_run_common as r

OUT=r.BASE/'new5_chain_01'


def state(stage,**extra):
    value=dict(stage=stage,utc=r.utc(),**extra)
    path=OUT/'state.json.pending'
    path.write_text(__import__('json').dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    path.replace(OUT/'state.json')
    print(__import__('json').dumps(value),flush=True)


def run(stage,argv,gpu=False):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1',PYTHONNOUSERSITE='1',HF_HOME=str(r.RUN/'cache/hf'),
        XDG_CACHE_HOME=str(r.RUN/'cache'),TMPDIR=str(r.RUN/'tmp'),TORCH_HOME=str(r.RUN/'cache/torch'))
    if not gpu:
        env['CUDA_VISIBLE_DEVICES']=''
    with (OUT/(stage+'.log')).open('xb') as log:
        child=subprocess.Popen(argv,cwd=r.BASE/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        state(stage+'_RUNNING',argv=argv,child_pid=child.pid,actual_disk_free_bytes=shutil.disk_usage(r.BASE).free,
            actual_memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
        code=child.wait()
    r.save(OUT/(stage+'.terminal.json'),dict(argv=argv,exit_code=code,utc=r.utc()))
    if code:
        raise RuntimeError(stage+' actually failed; preserve all successful work and do not retry this chain')


def freeze_source_lock(registration):
    acceptance,complete,inputs=r.inputs()
    required=[r.BASE/'native_input_acceptance.json',r.BASE/'processor_01/completion.json',
        r.BASE/'rgb_01/inputs.json',r.BASE/'rgb_01/completion.json',r.BASE/'mapping_01/completion.json',
        r.BASE/'source_isolation_acceptance.json',r.BASE/'media_01/completion.json',r.BASE/'media_01/launch_claim.json',
        r.BASE/'new5_source_registration_01.json',r.BASE/'new5_route_authorization_01.json',
        r.BASE/'new5_cpu_registration_02.json',r.BASE/'new5_inference_registration_02.json',
        r.BASE/'NATIVE_MAPPING_CONTRACT_V3.md',r.BASE/'EVALUATION_POLICY.md',r.BASE/'PROTOCOL.md',
        r.BASE/'screen_selection_before_new5_confirm.json',r.BASE/'known_identity_snapshot_01.json',
        r.BASE/'actual_gpu_budget_01.json',r.RUN/'b_score_aligned_package_v4/config.json']
    files=dict(registration['implementation_files'])
    for path,expected in r.read(r.BASE/'new5_cpu_registration_02.json')['frozen_files'].items():
        if r.sha(path)!=expected:
            raise ValueError('Frozen new5 CPU implementation/evidence changed')
        files[path]=expected
    for group in ['runtime_files','processor_assets']:
        for path,digest in complete['bindings']['original_b_processor_runtime'][group].items():
            if r.sha(path)!=digest:
                raise ValueError('Original accepted B runtime or processor changed')
            files[path]=digest
    mapping=r.read(r.BASE/'mapping_01/completion.json')
    for item in mapping['rows']:
        path=Path(item['bundle_path'])
        if r.sha(path)!=item['bundle_sha256']:
            raise ValueError('Accepted new5 mapping bundle changed')
        bundle=r.read(path)
        required += [path,Path(bundle['clock']['source_path']),Path(bundle['decode_provenance']['path'])]
    for entry,proof,meta in inputs:
        required += [Path(entry['proof_path']),Path(proof['input_path']),Path(meta['frame_array_path'])]
    for folder in [r.RUN/'b_score_aligned_package_v4',r.RUN/'baseline_a_pts_v1',r.RUN/'baseline_a_pts_v1/vendor',
            r.RUN/'balanced_two_window_risk_v3',r.RUN/'temporal_sft8b_v1']:
        required += list(folder.glob('*.py'))
    config=r.read(r.RUN/'b_score_aligned_package_v4/config.json')
    for folder in [Path(config['model_dir']),Path(config['b_adapter'])]:
        required += [p for p in folder.iterdir() if p.is_file() and p.suffix in ('.safetensors','.json','.txt','.jinja')]
    required += list((r.RUN/'resource_unlimited_v1_20261007').glob('*.py'))
    for path in set(required):
        digest=r.sha(path)
        if str(path) in files and files[str(path)]!=digest:
            raise ValueError('New source-lock identity conflict: '+str(path))
        files[str(path)]=digest
    r.save(r.BASE/'new5_source_lock_01.json',dict(status='FROZEN_ALL_ACTUAL_RESERVED5_NATIVE_INPUTS_AND_ORIGINAL_B',
        files=files,registered_sources=r.SOURCE_COUNT,windows=len(inputs),model_parameters=8782459120,
        optimizer_updates=0,unique_gpu_name=r.NAME,utc=r.utc(),human_reference_labels_not_in_inference=True))
    return len(inputs),len(files)


def main():
    if socket.gethostname()!='inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') in (None,''):
        raise ValueError('Controller requires verified host and nonempty actual GPU index')
    registration=r.read(r.BASE/'new5_inference_registration_02.json')
    if (registration['unique_gpu_name']!=r.NAME or registration['sources']!=r.SOURCE_COUNT or
            registration['new_optimizer_updates'] or not registration['original_B_native64_once']):
        raise ValueError('Independent original-B five-source inference registration changed')
    for path,digest in registration['implementation_files'].items():
        if r.sha(path)!=digest:
            raise ValueError('Registered new5 implementation changed before launch')
    OUT.mkdir(exist_ok=False)
    r.save(OUT/'launch_claim.json',dict(pid=os.getpid(),script_sha256=r.sha(__file__),
        registration_sha256=r.sha(r.BASE/'new5_inference_registration_02.json'),utc=r.utc()))
    try:
        state('WAIT_EXISTING_NEW5_CPU_CHAIN_NO_PREPARE_RESTART')
        while not (r.BASE/'cpu_chain_01/completion.json').exists():
            if (r.BASE/'cpu_chain_01/failure.json').exists():
                raise ValueError('New5 CPU preparation actually failed; no GPU admission')
            time.sleep(15)
        _,_,inputs=r.inputs()
        # Prior cost includes load/identity work; allow it once plus observed per-window work, doubled for uncertainty.
        previous=registration['prior_original_B_cost_seconds']
        max_seconds=math.ceil(2*(previous+previous*len(inputs)/registration['prior_original_B_windows']))
        budget=dict(registered_windows=len(inputs),max_gpu_seconds=max_seconds,prior_full_job_seconds=previous,
            formula='ceil(2*(prior_full_job_seconds + prior_full_job_seconds*new_windows/prior_windows))',
            observed_prior_peak_memory_mib=registration['prior_original_B_peak_memory_mib'],
            prior_unique_resource_sha256=registration['prior_unique_resource_sha256'],new_optimizer_updates=0)
        r.save(r.BASE/'actual_gpu_budget_01.json',budget)
        state('FREEZE_ALL_ACTUAL_NEW5_INPUTS_AND_ORIGINAL_CODE',**budget)
        windows,count=freeze_source_lock(registration)
        state('NEW5_INPUTS_FROZEN',windows=windows,files=count,source_lock_sha256=r.sha(r.BASE/'new5_source_lock_01.json'))
        command=[sys.executable,'-B',str(r.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name',r.NAME,'--max-seconds',str(max_seconds),'--queue-seconds',str(registration['queue_seconds']),
            '--planned-output-bytes',str((64<<20)+(32<<10)*windows),'--capacity-reason',
            'Reserved-five original media/mappings and every actual native64 CPU input accepted; same B8B with prior measured 22414MiB peak; shared external-compute lock and current actual outputs, no fixed resource thresholds',
            '--',sys.executable,'-B',str(r.BASE/'code/infer_new5.py')]
        run('NEW5_B_GPU_WRAPPER',command,gpu=True)
        resource,resource_sha=r.resource_terminal()
        state('ALL_NEW5_REAL_MODEL_CALLS_COMPLETE',charged_seconds=resource['charged_seconds'],resource_terminal_sha256=resource_sha)
        run('INDEPENDENT_CPU_REPLAY_EXPORT',[sys.executable,'-B',str(r.BASE/'code/replay_new5.py')])
        r.save(OUT/'completion.json',dict(status='PASS_RESERVED5_B_EXPORT_PENDING_FROZEN_CONFIRM_COMPARISON',
            registered_sources=r.SOURCE_COUNT,windows=windows,developer_export_acceptance_sha256=r.sha(r.BASE/'developer_export_acceptance.json'),
            prediction_export_sha256=r.sha(r.BASE/'developer_prediction_export.json'),resource_terminal_sha256=resource_sha,
            charged_seconds=resource['charged_seconds'],new_optimizer_updates=0,candidate_package_admitted=False,utc=r.utc()))
        state('NEW5_EXPORT_COMPLETE_PENDING_FROZEN_HUMAN_CONFIRMATION')
    except BaseException as error:
        r.save(OUT/'failure.json',dict(status='FAILED_NEW5_CHAIN_KEEP_ALL_RAW_SUCCESS_AND_COST',error=repr(error),traceback=traceback.format_exc(),utc=r.utc()))
        state('FAILED_PRESERVE_NO_SAME_CHAIN_RESTART',error=repr(error))
        raise


if __name__=='__main__':
    main()
