"""One-shot development launch; no autonomous confirmation/production admission."""
from datetime import datetime, timezone
import json
import os
import shutil
import socket
import subprocess
import time
import traceback
from common import ROOT, WORK, PY, WRAPPER, RESOURCE, LEDGER, read, write, ref


def run(name, script, args=(), gpu_seconds=None):
    command = [str(PY), '-u', '-B', str(ROOT / 'code' / script), *args]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu_seconds else '',
        PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    if gpu_seconds:
        job = 'subject_extent_external20_dev_20261024_v1'
        if (RESOURCE / (job + '.resource.json')).exists():
            raise FileExistsError('Unique GPU job already has a record')
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                       '--format=csv,noheader,nounits'], text=True).strip()
        mem = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True)
        # Estimate from actual frozen model bytes and this single image token budget.
        needed = 8767123696 * 2 + 4096 * 8192 * 4 * 4
        capacity = dict(host=socket.gethostname(), apps=apps, gpu_free_bytes=int(mem.strip()) * 1024**2,
                        estimated_peak_bytes=needed, planned_output_bytes=200 << 20,
                        disk_free=shutil.disk_usage(ROOT).free,
                        memory_available=[s for s in open('/proc/meminfo') if s.startswith('MemAvailable:')])
        write(ROOT / 'dev_live_resource.json', capacity)
        if apps or capacity['host'] != 'inspur-NP5570M5' or capacity['gpu_free_bytes'] < needed or capacity['disk_free'] < capacity['planned_output_bytes']:
            raise ValueError('Current shared resources cannot hold the declared pilot; no outsiders changed')
        command = [str(PY), '-B', str(WRAPPER), '--name', job, '--max-seconds', str(gpu_seconds),
            '--planned-output-bytes', str(200 << 20), '--capacity-reason', json.dumps(capacity),
            '--queue-seconds', '0', '--'] + command
    started = time.monotonic()
    with (ROOT / (name + '.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT)
        ticks = open('/proc/' + str(process.pid) + '/stat').read().rsplit(')', 1)[1].split()[19]
        write(ROOT / (name + '_launch.json'), dict(pid=process.pid, start_ticks=ticks, argv=command))
        code = process.wait()
    write(ROOT / (name + '_terminal.json'), dict(exit_code=code, seconds=time.monotonic()-started))
    if code:
        raise RuntimeError(name + ' naturally failed; successful operations are not retried')
    if gpu_seconds:
        record = read(RESOURCE / (job + '.resource.json'))
        matches = [json.loads(s) for s in LEDGER.read_text().splitlines() if json.loads(s).get('name') == job]
        if record['status'] != 'completed' or record['exit_code'] != 0 or matches != [record]:
            raise ValueError('GPU natural terminal/unique ledger mismatch')
        write(ROOT / 'dev_unique_gpu_receipt.json', record)


def main():
    write(ROOT / 'controller_claim.json', dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat()))
    try:
        run('registration', 'prepare.py', ['register'])
        run('dev_inputs', 'prepare.py', ['dev'])
        run('dev_gpu', 'infer.py', ['dev'], gpu_seconds=900)
        run('dev_review', 'evaluate.py', ['dev'])
        result = read(ROOT / 'dev_result.json')
        write(ROOT / 'completion.json', dict(status=result['status'], result=ref(ROOT / 'dev_result.json'),
            actual_new_answers=20, adopted_old_baselines=20, confirmation_started=False,
            production_admitted=False, baseline_4048_unchanged=True))
    except Exception:
        write(ROOT / 'failure.json', dict(traceback=traceback.format_exc(),
            successful_inputs_raw_cost_preserved=True, implicit_retry=False))
        raise


if __name__ == '__main__':
    main()
