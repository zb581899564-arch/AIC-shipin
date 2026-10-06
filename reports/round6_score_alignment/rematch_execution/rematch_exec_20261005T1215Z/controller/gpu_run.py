"""Current owned-job runner: common lock/ledger, measured capacity, no fixed free-disk line."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
RUN = ROOT / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
    temp.replace(path)

def disk():
    return dict(free_bytes=shutil.disk_usage(ROOT).free,
        work_bytes=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0]))

def compute():
    lines = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory',
                                   '--format=csv,noheader,nounits'],text=True).strip()
    return [line.strip() for line in lines.splitlines() if line.strip()]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--max-seconds', type=int, required=True)
    parser.add_argument('--planned-output-bytes',type=int,required=True)
    parser.add_argument('--capacity-reason',required=True)
    parser.add_argument('--queue-seconds',type=int,default=0)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1]==['--'] else args.command
    if not command or not args.name.replace('_','').replace('-','').isalnum() or args.max_seconds<=0 or args.planned_output_bytes<0:
        raise ValueError('invalid frozen job spec')
    policy_path=ROOT/'resource_policy.json'
    raw=policy_path.read_bytes()
    policy=json.loads(raw)
    if policy.get('gpu_time_mode')!='UNLIMITED' or policy.get('max_total_gpu_seconds') is not None:
        raise RuntimeError('current execution requires verified unlimited cumulative policy')
    ledger=CAMPAIGN/'gpu_ledger.jsonl'
    records=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    if any(r['name']==args.name for r in records):
        raise RuntimeError('preserve prior evidence: duplicate run name')
    queued=time.monotonic()
    lock=(CAMPAIGN/'gpu.lock').open('a')
    while True:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (CAMPAIGN/'active_gpu_job.json').exists():
                raise RuntimeError('unreconciled active job; never overwrite or kill it')
            active=compute()
            if not active:
                break
            fcntl.flock(lock,fcntl.LOCK_UN)
        except BlockingIOError:
            active=['project lock held']
        if time.monotonic()-queued>=args.queue_seconds:
            raise RuntimeError('GPU unavailable: '+str(active))
        write(RUN/'controller'/f'{args.name}.queue.json',dict(status='WAITING',checked_utc=utc(),compute=active))
        time.sleep(min(15,args.queue_seconds-(time.monotonic()-queued)))
    # Refresh ledger inside the lock, retaining the historical 7200s offset.
    records=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    before=disk()
    cap=policy['added_disk_budget_gib']*2**30
    if before['work_bytes']+args.planned_output_bytes>cap or before['free_bytes']<args.planned_output_bytes:
        raise RuntimeError('measured capacity insufficient for this job and the approved project occupancy boundary')
    started=time.monotonic()
    name=args.name
    log_path=RUN/'controller'/f'{name}.log'
    active_path=CAMPAIGN/'active_gpu_job.json'
    record=dict(name=name,command=command,started_utc=utc(),runner_pid=os.getpid(),
        reserved_seconds=args.max_seconds,teardown_reserve_seconds=120,
        prior_charged_seconds=7200+sum(r['charged_seconds'] for r in records),
        gpu_time_mode='UNLIMITED',max_total_gpu_seconds=None,resource_policy_sha256=hashlib.sha256(raw).hexdigest(),
        disk_before=before,planned_output_bytes=args.planned_output_bytes,capacity_reason=args.capacity_reason,
        resource_admission='live no-conflict check plus job output estimate; no fixed utilization/free-VRAM/free-disk gate',
        runner_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',
        PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',PYTHONFAULTHANDLER='1',HF_HOME=str(RUN/'cache/hf'),
        XDG_CACHE_HOME=str(RUN/'cache'),TMPDIR=str(RUN/'tmp'),PYTHONNOUSERSITE='1',
        CUDA_CACHE_PATH=str(RUN/'cache/cuda'),TORCH_HOME=str(RUN/'cache/torch'),
        TRITON_CACHE_DIR=str(RUN/'cache/triton'),TORCHINDUCTOR_CACHE_DIR=str(RUN/'cache/inductor'),
        PYTHONPATH=str(ROOT))
    (RUN/'tmp').mkdir(exist_ok=True)
    reason=None
    peak=None
    with log_path.open('x') as log:
        proc=subprocess.Popen(command,cwd=RUN,stdout=log,stderr=subprocess.STDOUT,env=env,
            stdin=subprocess.DEVNULL,start_new_session=True)
        record['child_pid']=proc.pid
        write(active_path,record)
        try:
            while proc.poll() is None:
                elapsed=time.monotonic()-started
                if elapsed>=args.max_seconds:
                    raise TimeoutError('frozen single-job wall-time reached')
                current=disk()
                if current['work_bytes']>cap:
                    raise RuntimeError('approved occupancy boundary exceeded')
                remaining=max(0,args.planned_output_bytes-max(0,current['work_bytes']-before['work_bytes']))
                if current['free_bytes']<remaining:
                    raise RuntimeError('capacity became insufficient for remaining predicted outputs')
                owned_memory = 0
                for line in compute():
                    pid,process,used=line.split(',',2)
                    if int(pid.strip())==proc.pid:
                        owned_memory += int(used.strip())
                    else:
                        try:
                            owned_child = os.getpgid(int(pid.strip())) == proc.pid
                        except ProcessLookupError:
                            owned_child = True
                        if not owned_child:
                            raise RuntimeError('new external compute conflict; stop only the owned job')
                        if owned_child:
                            owned_memory += int(used.strip())
                peak = max(peak or 0, owned_memory)
                write(active_path,dict(record,elapsed_seconds=elapsed,last_checked_utc=utc(),
                    sampled_peak_memory_mib=peak,disk_current=current))
                time.sleep(10)
        except BaseException as exc:
            reason=str(exc)
            # Only the explicitly launched owned process group is stopped.
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try:
                    proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait()
    record.update(finished_utc=utc(),charged_seconds=time.monotonic()-started,exit_code=proc.returncode,
        stop_reason=reason,sampled_peak_memory_mib=peak,
        status='completed' if proc.returncode==0 and reason is None else 'failed',disk_after=disk())
    with ledger.open('a') as handle:
        handle.write(json.dumps(record)+'\n')
        handle.flush()
        os.fsync(handle.fileno())
    write(RUN/'controller'/f'{name}.resource.json',record)
    # Do not remove an active marker if an unrelated writer replaced it.
    if json.loads(active_path.read_text()).get('child_pid')==proc.pid:
        active_path.unlink()
    print(json.dumps(record),flush=True)
    raise SystemExit(0 if record['status']=='completed' else 1)

if __name__=='__main__':
    main()
