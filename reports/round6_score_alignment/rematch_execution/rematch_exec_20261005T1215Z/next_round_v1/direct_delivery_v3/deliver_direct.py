"""Restore only the vanished Windows delivery waiter; leave Linux Z intact."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
REMOTE = '/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1'
REMOTE_PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
FILES = ('candidate_Z_8B.zip', 'predictions.jsonl', 'provenance.jsonl',
         'selected.jsonl', 'metadata.json', 'package.stage.json',
         'independent_validation.json', 'spatial.stage.json')


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(name, value):
    path = HERE / name
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def verify_sources():
    lock = json.loads((HERE / 'source_lock.json').read_text(encoding='utf-8'))
    for row in lock['files']:
        path = RUN / row['path']
        if path.stat().st_size != row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('delivery source binding mismatch: ' + row['path'])


def state():
    code = "from pathlib import Path\nimport json\np=Path(" + repr(REMOTE + '/completion.json') + ")\nprint(json.dumps(json.loads(p.read_text()) if p.exists() else None))\n"
    result = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'aic-inspur-home', REMOTE_PY + ' -B -'],
        input=code, text=True, encoding='utf-8', stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=45)
    if result.returncode:
        raise RuntimeError('direct SSH state query failed')
    return json.loads(result.stdout)


def main():
    verify_sources()
    if '--preflight' in sys.argv:
        result = state()
        print(json.dumps({'status': 'PASS_BOUND_SOURCES_AND_LIVE_DIRECT_QUERY',
                          'remote_completion_present': result is not None, 'Mac_used': False}))
        return
    import msvcrt
    lock = (HERE / 'delivery.lock').open('a+b')
    lock.seek(0)
    if not lock.read(1):
        lock.write(b'1'); lock.flush()
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    with (HERE / 'delivery_registration.json').open('x', encoding='utf-8') as registration:
        json.dump({'pid': os.getpid(), 'utc': utc(), 'Mac_used': False,
                   'route': 'DIRECT_WINDOWS_LINUX', 'uploaded': False}, registration)
    start = time.monotonic()
    failures = 0
    try:
        while time.monotonic() - start < 3 * 86400:
            try:
                completion = state()
                failures = 0
            except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError):
                failures += 1
                if failures >= 10:
                    raise RuntimeError('direct SSH queries exhausted bounded retries')
                write('delivery_progress.json', {'status': 'WAITING_DIRECT_SSH_RETRY', 'utc': utc(),
                                                'pid': os.getpid(), 'consecutive_failures': failures})
                time.sleep(30)
                continue
            if completion is not None:
                write('completion.json', completion)
                if completion.get('stage') != 'PASS_COMPLETE_426_Z8B_READY_FOR_DELIVERY':
                    raise RuntimeError('remote pipeline completed without a valid deliverable')
                break
            write('delivery_progress.json', {'status': 'WAITING_FROZEN_Z_COMPLETION', 'utc': utc(),
                                            'pid': os.getpid(), 'Mac_used': False, 'uploaded': False})
            time.sleep(30)
        else:
            raise TimeoutError('registered delivery wait expired')
        verify_sources()
        delivery = HERE / 'delivery_01'
        delivery.mkdir(exist_ok=False)
        for name in FILES:
            write('delivery_progress.json', {'status': 'COPYING_COMPLETED_Z_ARTIFACTS', 'utc': utc(),
                                            'pid': os.getpid(), 'file': name, 'Mac_used': False})
            subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                            'aic-inspur-home:' + REMOTE + '/rematch_01/' + name,
                            str(delivery / name)], check=True, timeout=600)
        subprocess.run([sys.executable, '-B', str(HERE / 'verify_delivery.py'), str(delivery)],
                       check=True, timeout=600)
        write('delivery_completion.json', {'status': 'PASS_LOCAL_UPLOADABLE_Z8B_PACKAGE', 'utc': utc(),
                                          'candidate': str(delivery / 'candidate_Z_8B.zip'),
                                          'sha256': completion['candidate_sha256'],
                                          'bytes': completion['candidate_bytes'], 'videos': 426,
                                          'Mac_used': False, 'uploaded': False})
    except Exception as error:
        write('delivery_stop.json', {'status': 'STOP_DELIVERY', 'utc': utc(),
                                    'reason': str(error), 'uploaded': False})
        raise


if __name__ == '__main__':
    main()
