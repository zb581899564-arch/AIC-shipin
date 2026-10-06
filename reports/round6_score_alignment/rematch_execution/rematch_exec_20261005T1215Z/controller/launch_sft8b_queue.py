"""Exclusive detached launch of the registered SFT smoke queue, never a GPU job."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL, HERE = RUN/'controller', RUN/'temporal_sft8b_v1'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-lock-sha256', required=True)
    args = parser.parse_args()
    lock_path = HERE/'smoke_source_lock.json'
    require(sha(lock_path) == args.expected_lock_sha256, 'unregistered SFT source lock')
    lock = json.loads(lock_path.read_text())
    require(sha(__file__) == lock['queue_launcher_sha256'], 'queue launcher changed')
    queue = CTRL/'queue_sft8b_after_a.py'
    require(sha(queue) == lock['queue_helper_sha256'], 'queue helper changed')
    for name, digest in lock['files'].items():
        require(sha(HERE/name) == digest, 'SFT source/input changed: '+name)
    for name in ('sft8b_queue.launch.json', 'sft8b_queue.registration.json', 'sft8b_queue_completion.json'):
        require(not (CTRL/name).exists(), 'existing queue evidence: '+name+'; no duplicate launch')
    reservation = CTRL/'sft8b_queue.launch_registration.json'
    with reservation.open('x') as handle:
        json.dump({'launcher_pid': os.getpid(), 'source_lock_sha256': args.expected_lock_sha256}, handle)
    command = [sys.executable, '-B', '-u', str(queue), '--expected-lock-sha256', args.expected_lock_sha256]
    with (CTRL/'sft8b_queue.background.log').open('xb') as log:
        child = subprocess.Popen(command, cwd=str(HERE), stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = {'stage': 'DETACHED_SFT_SMOKE_QUEUE_LAUNCHED', 'pid': child.pid,
               'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'source_lock_sha256': args.expected_lock_sha256, 'command': command,
               'training_started': False, 'formal_c_bce_admitted': False,
               'full_training_started': False, 'uploaded': False}
    with (CTRL/'sft8b_queue.launch.json').open('x') as handle:
        handle.write(json.dumps(receipt, indent=2)+'\n')
    for _ in range(100):
        if (CTRL/'sft8b_queue.registration.json').exists():
            break
        require(child.poll() is None, 'detached queue exited before registration; see background log')
        time.sleep(.1)
    require((CTRL/'sft8b_queue.registration.json').exists(), 'queue registration handshake timed out')
    require(child.poll() is None or (CTRL/'sft8b_queue_completion.json').exists(), 'queue exited without completion')
    print(json.dumps(receipt), flush=True)
