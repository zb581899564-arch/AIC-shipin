"""Unique chain: wait accepted inputs -> independent QA -> remaining93 -> review."""
import os
from pathlib import Path
import subprocess
import time
import traceback
from pilot_context30 import ROOT, WORK, OUT, CODE, RUN, PY, WRAPPER, JOB, identity, read, save

def wait_inputs():
    launch = read(ROOT / 'pilot_inputs27_launch.json')
    deadline = time.monotonic() + 5400
    while not (ROOT / 'pilot_inputs27/completion.json').exists():
        if (ROOT / 'pilot_inputs27/failure.json').exists():
            raise RuntimeError('Actual input27 failure; successful journal retained, no restart')
        stat = Path('/proc') / str(launch['pid']) / 'stat'
        if not stat.exists() or stat.read_text().rsplit(')', 1)[1].split()[19] != launch['start_ticks']:
            raise RuntimeError('Input handle missing without complete terminal; inspect, never relaunch here')
        if time.monotonic() > deadline:
            raise TimeoutError('Registered input wait elapsed; do not stop or restart live input job')
        time.sleep(5)


def execute(mode, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / {'inputs': 'pilot_input_qa29.py', 'gpu': 'pilot_gpu30.py', 'review': 'pilot_review30.py'}[mode])]
    if GPU:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute exists; accepted inputs retained')
        save(OUT / 'resource_admission.json', dict(apps=apps, GPU=subprocess.check_output(['nvidia-smi'], text=True),
            RAM=subprocess.check_output(['free', '-b'], text=True), disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '1800',
            '--planned-output-bytes', '10000000', '--capacity-reason',
            'First remaining93 original TIME controls, adopt4; complete independent native inputs, zero training or test data; measured first4 gen23.4s and21.4GB peak',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (mode + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (mode + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = process.wait()
    save(OUT / (mode + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual remaining control stage failed: ' + mode)


def main():
    OUT.mkdir()
    save(OUT / 'registration.json', dict(purpose='Complete original coarse TIME whole-source anchors before policy pilot',
        fixed_cohort=identity(ROOT / 'pilot_profile21/registration.json'),
        adopt4=identity(ROOT / 'pilot_cost25/completion.json'), actual_new_GPU_calls=93,
        GPU_seconds_max=1800, input_wait_max_seconds=5400, no_training_or_package=True,
        no_complete40_47_baseline_claim=True, no_automatic_retries=True))
    wait_inputs()
    execute('inputs')
    names = ['pilot_control30.py', 'pilot_context30.py', 'pilot_gpu30.py', 'pilot_review30.py', 'pilot_input_qa29.py', 'coarse_call25.py', 'prompt_contract13.py',
             'native_sets.py', 'preference_reward.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        inputs=identity(ROOT / 'pilot_input_qa29/completion.json'), wrapper=identity(WRAPPER)))
    execute('gpu', True)
    execute('review')
    import json
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [resource]:
        raise ValueError('Unique natural full-control GPU terminal or cost differs')
    save(OUT / 'completion.json', dict(state='WHOLE97_ORIGINAL_COARSE_CONTROLS_COMPLETE',
        review=identity(OUT / 'independent_CPU_audit.json'), GPU_seconds=resource['charged_seconds'],
        first_GPU_calls=93, adopted_GPU_calls=4, training_updates=0, new_ZIP=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure_controller.json', dict(traceback=traceback.format_exc(),
                 keep_all_successes=True, no_automatic_relaunch=True))
        raise
