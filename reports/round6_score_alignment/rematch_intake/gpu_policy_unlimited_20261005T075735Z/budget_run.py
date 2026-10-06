"""Serialize owned GPU jobs and conservatively charge their entire wall time."""
import argparse
import datetime as dt
import fcntl
import json
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()



def load_resource_policy(path):
    """Missing policy preserves the historical cap; unlimited must be explicit."""
    if not path.exists():
        return dict(gpu_time_mode='FINITE', max_total_gpu_seconds=86400,
                    policy_sha256=None, policy_source='legacy_default')
    raw = path.read_bytes()
    policy = json.loads(raw)
    if not isinstance(policy, dict) or policy.get('schema_version') != 1:
        raise ValueError('invalid resource policy schema')
    if 'max_total_gpu_seconds' not in policy:
        raise ValueError('missing cumulative GPU limit')
    mode = policy.get('gpu_time_mode')
    cap = policy['max_total_gpu_seconds']
    if mode == 'UNLIMITED':
        if cap is not None:
            raise ValueError('unlimited policy requires a null limit')
    elif mode == 'FINITE':
        if type(cap) is not int or cap <= 0:
            raise ValueError('finite policy requires a positive integer limit')
    else:
        raise ValueError('unknown GPU time mode')
    return dict(gpu_time_mode=mode, max_total_gpu_seconds=cap,
                policy_sha256=hashlib.sha256(raw).hexdigest(),
                policy_source=str(path))


def check_gpu_reservation(charged, max_seconds, teardown_reserve, policy):
    if type(max_seconds) is not int or max_seconds <= 0:
        raise ValueError('invalid job wall time')
    cap = policy['max_total_gpu_seconds']
    if cap is not None and charged + max_seconds + teardown_reserve > cap:
        raise RuntimeError(
            f'GPU reservation exceeds budget: {charged}+{max_seconds}+{teardown_reserve}>{cap}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--max-seconds', type=int, required=True)
    ap.add_argument('command', nargs=argparse.REMAINDER)
    args = ap.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.max_seconds <= 0 or not args.name.replace('_','').replace('-','').isalnum():
        raise ValueError('invalid job specification')
    CAMPAIGN.mkdir(exist_ok=True)
    lock = (CAMPAIGN / 'gpu.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (CAMPAIGN / 'active_gpu_job.json').exists():
        raise RuntimeError('unreconciled active job; supervisor must verify its process and budget')
    baseline = json.loads((CAMPAIGN / 'baseline_lock.json').read_text())
    ledger = CAMPAIGN / 'gpu_ledger.jsonl'
    records = [json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
    if any(x['name'] == args.name for x in records):
        raise RuntimeError('job name already exists; preserve prior evidence')
    # The initial two hours are a deliberately conservative charge, recorded
    # separately from measured job wall times.
    charged = 7200 + sum(x['charged_seconds'] for x in records)
    teardown_reserve = 120
    policy = load_resource_policy(ROOT / 'resource_policy.json')
    check_gpu_reservation(charged, args.max_seconds, teardown_reserve, policy)
    processes = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'], text=True).strip()
    if processes:
        raise RuntimeError('GPU already has a compute process: ' + processes)
    def disk_check():
        free = shutil.disk_usage(ROOT).free
        usage = int(subprocess.check_output(['du','-s','-B1',str(ROOT)], text=True).split()[0])
        if free < 80*2**30 or usage > 80*2**30:
            raise RuntimeError(f'disk boundary: free={free}, work_bytes={usage}')
        return {'free_bytes': free, 'work_bytes': usage}
    before = disk_check()
    started = time.monotonic()
    record = dict(name=args.name, command=command, started_utc=utc(), runner_pid=os.getpid(),
                  reserved_seconds=args.max_seconds, teardown_reserve_seconds=teardown_reserve,
                  prior_charged_seconds=charged, disk_before=before,
                  gpu_time_mode=policy['gpu_time_mode'],
                  max_total_gpu_seconds=policy['max_total_gpu_seconds'],
                  resource_policy_sha256=policy['policy_sha256'])
    logfile = CAMPAIGN / (args.name + '.log')
    with logfile.open('x') as log:
        env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                   PYTHONUNBUFFERED='1', OMP_NUM_THREADS='4', PYTHONPATH=str(ROOT))
        proc = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        record['child_pid'] = proc.pid
        write(CAMPAIGN / 'active_gpu_job.json', record)
        reason = None
        peak_mib = None
        try:
            while proc.poll() is None:
                elapsed = time.monotonic()-started
                if elapsed >= args.max_seconds:
                    raise TimeoutError('reserved wall time reached')
                disk = disk_check()
                try:
                    mem = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'], text=True)
                    for line in mem.splitlines():
                        pid, used = line.split(',')
                        if int(pid.strip()) == proc.pid:
                            peak_mib = max(peak_mib or 0, int(used.strip()))
                except (ValueError, subprocess.SubprocessError):
                    pass
                write(CAMPAIGN / 'active_gpu_job.json', dict(record, elapsed_seconds=elapsed,
                      last_checked_utc=utc(), sampled_peak_memory_mib=peak_mib, disk_current=disk))
                time.sleep(min(30, max(1, args.max_seconds-elapsed)))
        except BaseException as exc:
            reason = str(exc)
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
        record.update(finished_utc=utc(), charged_seconds=time.monotonic()-started,
                      exit_code=proc.returncode, stop_reason=reason, sampled_peak_memory_mib=peak_mib,
                      status='completed' if proc.returncode == 0 and reason is None else 'failed')
        with ledger.open('a') as out:
            out.write(json.dumps(record)+'\n')
            out.flush()
            os.fsync(out.fileno())
        write(CAMPAIGN / (args.name+'.resource.json'), record)
        (CAMPAIGN / 'active_gpu_job.json').unlink()
        print(json.dumps(record))
        raise SystemExit(0 if record['status']=='completed' else 1)


if __name__ == '__main__':
    main()
