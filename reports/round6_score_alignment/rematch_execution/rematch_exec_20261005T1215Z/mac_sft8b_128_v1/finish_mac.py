"""One owned Mac job: byte-gated preparation, real probe, then fresh full SFT."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time
import traceback

from mac_contract import HERE,ROOT,SCOPE,verify_lock
from sft_contract import sha256,require
from phase_gate import validate_finished_phase

CTRL=HERE/'controller'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def write(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def read(path):return json.loads(path.read_text())
def occupied(path):
    value=subprocess.check_output(['/usr/bin/du','-sk',str(path)],text=True)
    return int(value.split()[0])*1024
def active_external(exclude=()):
    output=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,command='],text=True)
    found=[]
    for line in output.splitlines():
        fields=line.strip().split(None,2)
        if len(fields)!=3:continue
        pid,ppid,command=fields;pid=int(pid)
        if pid==os.getpid() or pid in exclude or str(HERE) in command:continue
        executable=command.split()[0].lower()
        probable_compute=('python' in executable or 'ollama' in executable or 'llama-server' in executable or
                          'mlx_lm' in command or 'mlx_vlm' in command or 'torchrun' in command)
        if probable_compute and not executable.startswith('/system/'):
            found.append(dict(pid=pid,command=command[:1000]))
    return found
def resources(planned,linux_snapshot):
    usage=shutil.disk_usage(HERE);work=occupied(ROOT)
    linux_upper=linux_snapshot['work_bytes']+linux_snapshot['remaining_registered_output_bytes']
    cap=80*2**30
    require(work+linux_upper+planned<=cap,'combined Windows-authorized 80 GiB project occupancy would be exceeded')
    require(usage.free>=planned,'disk cannot hold the registered remaining outputs')
    return dict(checked_utc=utc(),mac_workspace_bytes=work,mac_free_bytes=usage.free,
        linux_work_upper_bytes=linux_upper,combined_planned_peak_bytes=work+linux_upper+planned,
        combined_cap_bytes=cap,planned_remaining_output_bytes=planned,
        vm_stat=subprocess.check_output(['/usr/bin/vm_stat'],text=True),
        swap=subprocess.check_output(['/usr/sbin/sysctl','vm.swapusage'],text=True),
        external_compute=active_external())

def phase(phase_name,config,lock_sha,limit,linux_snapshot,planned,probe=None):
    resources_before=resources(planned,linux_snapshot)
    require(not resources_before['external_compute'],'external compute appeared before phase')
    admission=dict(authorized=True,scope=SCOPE,phase=phase_name,source_lock_sha256=lock_sha,
        config_sha256=sha256(HERE/'config.json'),max_seconds=limit,registered_utc=utc(),
        user_authorization_sha256=sha256(HERE/'authorization.json'),resources=resources_before,
        formal_c_bce_admitted=False,test_inference_admitted=False,upload_admitted=False,
        base_initialization='PINNED_BASE_NEW_LORA_NOT_PROBE_ADAPTER')
    if probe is not None:
        admission.update(probe_report_sha256=sha256(HERE/'probe_01/train_report.json'),
                         measured_probe_wall_seconds=probe['wall_seconds'],
                         measured_probe_peak_mps_mib=probe['peak_memory_allocated_mib'],
                         cost_formula=config['full_wall_bound_formula'])
    admission_path=CTRL/(phase_name+'_admission.json')
    with admission_path.open('x') as f:f.write(json.dumps(admission,ensure_ascii=False,indent=2)+'\n')
    command=[str(ROOT/'bin/run'),str(HERE/'env/bin/python'),'-B','-u',str(HERE/'train_mac.py'),
             '--config',str(HERE/'config.json'),'--admission',str(admission_path),
             '--lock',str(HERE/'source_lock.json'),'--expected-lock',lock_sha,'--phase',phase_name]
    environment=dict(os.environ);environment['PYTORCH_ENABLE_MPS_FALLBACK']='0'
    started=time.monotonic();reason=None
    with (CTRL/(phase_name+'_training.log')).open('xb') as log:
        child=subprocess.Popen(command,cwd=HERE,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            env=environment,start_new_session=True)
    active=dict(scope=SCOPE,phase=phase_name,runner_pid=os.getpid(),child_pid=child.pid,started_utc=utc(),
                max_seconds=limit,admission_sha256=sha256(admission_path),source_lock_sha256=lock_sha)
    write(CTRL/'active_training.json',active)
    try:
        while child.poll() is None:
            elapsed=time.monotonic()-started
            current=resources(planned,linux_snapshot)
            if current['external_compute']:reason='external compute conflict during owned phase'
            if elapsed>limit:reason='registered phase wall limit exceeded'
            state=dict(status='RUNNING_MAC_'+phase_name.upper(),**active,elapsed_seconds=elapsed,
                       current_resources=current)
            progress=HERE/('probe_01' if phase_name=='probe' else 'full_01')/'progress.json'
            if progress.exists():
                data=read(progress)
                state.update(trainer_status=data['status'],optimizer_steps=data['optimizer_steps'],
                    effective_batches=data['effective_batches'],peak_mps_driver_mib=data.get('peak_mps_driver_mib'))
            write(CTRL/'pipeline_latest.json',state)
            if reason:break
            time.sleep(15)
    except Exception as exc:
        reason=type(exc).__name__+': '+str(exc)
    finally:
        if reason and child.poll() is None:
            # Only this newly launched child process group; never any external process.
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL)
        exit_code=child.wait();seconds=time.monotonic()-started
        receipt=dict(**active,finished_utc=utc(),exit_code=exit_code,charged_seconds=seconds,
            cumulative_gpu_time_mode='UNLIMITED',linux_initial_7200_offset_unchanged=True,
            stopped_owned_child_reason=reason,resources_before=resources_before)
        write(CTRL/(phase_name+'_resource.json'),receipt)
        with (ROOT/'runs/aic_video_mac_gpu_ledger.jsonl').open('a') as ledger:
            ledger.write(json.dumps(receipt,ensure_ascii=False)+'\n')
        write(CTRL/'active_training.json',dict(status='FINISHED',**receipt))
    require(reason is None and exit_code==0,'Mac '+phase_name+' failed; no automatic retry/full continuation')
    report_path=HERE/('probe_01' if phase_name=='probe' else 'full_01')/'train_report.json'
    report=read(report_path)
    return validate_finished_phase(report,phase_name)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--expected-lock',required=True);args=parser.parse_args()
    verify_lock(HERE/'source_lock.json',args.expected_lock)
    CTRL.mkdir(exist_ok=True);(ROOT/'runs').mkdir(exist_ok=True)
    config=read(HERE/'config.json');linux=read(HERE/'linux_capacity_snapshot.json')
    lock_stream=(ROOT/'runs/aic_video_gpu.lock').open('a+')
    try:fcntl.flock(lock_stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        write(CTRL/'pipeline_completion.json',dict(status='STOP_MAC_SHARED_GPU_LOCK_BUSY',checked_utc=utc()));return 3
    completion=dict(scope=SCOPE,runner_pid=os.getpid(),source_lock_sha256=args.expected_lock,started_utc=utc(),
                    quality_claim=False,dev_evaluated=False,test_inference_started=False,uploaded=False)
    try:
        # Waiting has a separate transport bound; it is not counted as GPU execution.
        deadline=time.monotonic()+12*3600
        while True:
            asset=CTRL/'asset_http_completion.json'
            if asset.exists():
                require(read(asset)['status']=='PASS_MAC_PINNED_MODEL_AND_704_TRAIN_MEDIA_TRANSFER',
                        'asset transfer stopped; preserve partials and failure')
                break
            require(time.monotonic()<deadline,'asset wait exceeded owned transport deadline')
            state=dict(status='WAITING_REGISTERED_MAC_ASSET_TRANSFER',**completion)
            if (CTRL/'asset_http_progress.json').exists():state['transfer']=read(CTRL/'asset_http_progress.json')
            write(CTRL/'pipeline_latest.json',state);time.sleep(15)
        require(read(CTRL/'environment_completion.json')['status']=='PASS_TASK_SCOPED_MPS_ENVIRONMENT',
                'isolated environment installation incomplete')
        verify_lock(HERE/'source_lock.json',args.expected_lock)
        with (CTRL/'cpu_preflight.log').open('xb') as log:
            checked=subprocess.run([str(ROOT/'bin/run'),str(HERE/'env/bin/python'),'-B',
                str(HERE/'test_mac_cpu.py'),'--mac'],cwd=HERE,stdout=log,stderr=subprocess.STDOUT)
        require(checked.returncode==0,'real Mac codec/processor CPU preflight failed')
        write(CTRL/'cpu_preflight.json',dict(status='PASS_MAC_CPU_CONTRACTS',tests=8,
            real_codec_processor_test=True,log_sha256=sha256(CTRL/'cpu_preflight.log'),checked_utc=utc()))
        probe_planned=15335424*4+48*16384*32+134217728
        total_planned=config['planned_output_bytes']+probe_planned
        resource_deadline=time.monotonic()+6*3600
        while active_external():
            require(time.monotonic()<resource_deadline,'bounded wait for external Mac compute expired')
            write(CTRL/'pipeline_latest.json',dict(status='WAITING_MAC_EXTERNAL_COMPUTE',
                **completion,external_compute=active_external(),checked_utc=utc()));time.sleep(15)
        probe=phase('probe',config,args.expected_lock,config['probe_max_seconds'],linux,total_planned)
        # Fresh full initialization is enforced independently by train_mac, never a probe adapter.
        full_seconds=math.ceil(probe['wall_seconds']/48*3620*1.75+probe['wall_seconds'])
        require(full_seconds>0 and math.isfinite(full_seconds),'invalid measured full wall bound')
        full=phase('full',config,args.expected_lock,full_seconds,linux,config['planned_output_bytes'],probe)
        completion.update(status='PASS_MAC_SECOND_8B_FULL_TRAINING_ENGINEERING',
            full_training_completed=True,probe_report_sha256=sha256(HERE/'probe_01/train_report.json'),
            full_report_sha256=sha256(HERE/'full_01/train_report.json'),
            adapter_sha256=full['adapter_model_sha256'],quality_evaluation_pending=True)
    except Exception as exc:
        completion.update(status='STOP_MAC_PIPELINE',failure_type=type(exc).__name__,failure=str(exc),
                          traceback=traceback.format_exc(),full_training_completed=False)
    completion['finished_utc']=utc()
    write(CTRL/'pipeline_completion.json',completion);write(CTRL/'pipeline_latest.json',completion)
    fcntl.flock(lock_stream,fcntl.LOCK_UN);lock_stream.close()
    print(json.dumps(completion,ensure_ascii=False),flush=True)
    return 0 if completion['status'].startswith('PASS_') else 4

if __name__=='__main__':raise SystemExit(main())
