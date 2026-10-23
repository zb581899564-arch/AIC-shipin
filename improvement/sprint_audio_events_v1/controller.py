"""Single finite A0 chain; no production, retries, training or network changes."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback
from common import ROOT, WORK, PY, RUN, WRAPPER, LEDGER, read, write, checked, reference

CODE = Path(__file__).resolve().parent
RESOURCE = RUN/'controller'


def cpu(name, script):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2',
        MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    env.pop('PYTHONPATH', None)
    with (ROOT/(name+'.log')).open('x') as log:
        result = subprocess.run([str(PY), '-u', '-B', str(CODE/script)], cwd=ROOT,
            env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    write(ROOT/(name+'_terminal.json'), dict(exit_code=result.returncode))
    if result.returncode:
        raise RuntimeError('Actual first CPU phase failed: '+name)


def resources(name, estimate):
    query = ['nvidia-smi', '--query-gpu=memory.free,memory.used,utilization.gpu', '--format=csv,noheader,nounits']
    gpu = subprocess.check_output(query, text=True).strip()
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory',
        '--format=csv,noheader,nounits'], text=True).strip()
    tasks = []
    for line in apps.splitlines():
        p = Path('/proc')/line.split(',')[0].strip()
        if p.exists():
            tasks.append(dict(pid=p.name, argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),
                stat=(p/'stat').read_text()))
    resource = dict(host=socket.gethostname(), gpu=gpu, actual_GPU_processes=tasks,
        memory_available=[line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')],
        disk_free=shutil.disk_usage(ROOT).free, this_job_model_activation_estimate=estimate,
        this_job_persistent_output_budget=134217728, CPU_threads=2,
        reason='Serial single-excerpt model; adopted prior actual TIME peak and retained inputs, no external process interruption')
    write(ROOT/(name+'_resources.json'), resource)
    if resource['host'] != 'inspur-NP5570M5' or int(gpu.split(',')[0])*1024**2 < estimate or resource['disk_free'] < resource['this_job_persistent_output_budget']:
        raise ValueError('Current capacity cannot hold this registered job')
    return resource


def gpu(name, script, seconds, estimate):
    resource = resources(name, estimate)
    if (RESOURCE/(name+'.resource.json')).exists():
        raise FileExistsError('Unique model task already has terminal state')
    command = [str(PY), '-B', str(WRAPPER), '--name', name, '--max-seconds', str(seconds),
        '--planned-output-bytes', '134217728', '--capacity-reason', json.dumps(resource),
        '--queue-seconds', '0', '--', str(PY), '-u', '-B', str(CODE/script)]
    with (ROOT/(name+'.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='0',
            OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        write(ROOT/(name+'_launch.json'), dict(pid=process.pid, argv=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
        code = process.wait()
    record = read(RESOURCE/(name+'.resource.json'))
    ledger = [row for row in map(json.loads, LEDGER.read_text().splitlines()) if row.get('name') == name]
    write(ROOT/(name+'_terminal.json'), dict(exit_code=code, resource_ref=reference(RESOURCE/(name+'.resource.json')),
        unique_ledger_equal=ledger == [record]))
    if code or record['status'] != 'completed' or record['exit_code'] != 0 or ledger != [record]:
        raise ValueError('Actual GPU failure or terminal/ledger mismatch: '+name)
    return record


def main():
    write(ROOT/'controller_claim.json', dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat()))
    protected = reference(WORK/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    if protected['bytes'] != 384630 or protected['sha256'] != 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3':
        raise ValueError('Protected40.47 differs')
    if reference(WRAPPER)['sha256'] != '9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
        raise ValueError('Shared wrapper differs')
    cpu('first_pann_CPU', 'inputs.py')
    write(ROOT/'source_input_lock.json', dict(protocol=reference(ROOT/'protocol.json'), baseline=protected,
        code={p.name:reference(p) for p in sorted(CODE.glob('*.py'))},
        inputs=reference(ROOT/'input_acceptance.json'), model=reference(ROOT/'model_cpu_acceptance.json'),
        author_source=reference(ROOT/'author_source_acceptance.json'), wrapper=reference(WRAPPER)))
    count = read(ROOT/'model_cpu_acceptance.json')['actual_parameters']
    event = gpu('pann_timed_events8_20261021_v1', 'events.py', 180, count*4 + 32000*30*4*256)
    cpu('independent_events', 'event_review.py')
    cpu('first_augmented_inputs', 'text_inputs.py')
    write(ROOT/'TIME_input_lock.json', dict(original_lock=reference(ROOT/'source_input_lock.json'),
        actual_first16_inputs=reference(ROOT/'text_input_acceptance.json'),
        event_independent_QA=reference(ROOT/'first_event_output_acceptance.json')))
    temporal = gpu('pann_audio_correct_shift_TIME16_20261021_v1', 'time_calls.py', 1800,
        8782459120*2 + 65536*4096*2*8 + 2*1024**3)
    cpu('independent_TIME_review', 'review.py')
    if reference(protected['path']) != protected:
        raise ValueError('Protected40.47 changed')
    for entry in read(ROOT/'source_input_lock.json')['code'].values():
        checked(entry)
    result = dict(status=read(ROOT/'review.json')['status'], review_ref=reference(ROOT/'review.json'),
        independent_qa=reference(ROOT/'independent_output_qa.json'), GPU_charged_seconds=event['charged_seconds']+temporal['charged_seconds'],
        model_forwards=dict(PANN=8, original_TIME=16), new_updates=0, new_ZIP=0,
        original40_47_unchanged=True, automatic_production=False,
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(ROOT/'completion.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT/'controller_failure.json', dict(status='ACTUAL_FAILURE_SUCCESS_AND_RAW_PRESERVED',
            traceback=traceback.format_exc(), no_automatic_retry=True))
        raise
