"""Unique remaining-only VERIFY and complete fixed content-summary dev review."""
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import traceback

from event_chain78 import measured_cost
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'summary_full93'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_content_summary_first_missing_VERIFY_20261022_v93'
FILES = ['summary_downstream93.py', 'summary_verify92_prepare.py', 'verify_adoption92.py',
         'summary_verify93_gpu.py', 'summary_full93_masks.py', 'summary_full94_review.py']


def await_native():
    launch = read(ROOT / 'summary_selection91_launch.json')
    deadline = time.monotonic() + 2100
    folder = ROOT / 'summary_selection91'
    while True:
        if (folder / 'failure.json').exists():
            raise RuntimeError('Actual native phase failed; do not repeat its successful calls')
        if (folder / 'completion.json').exists():
            value = read(folder / 'completion.json')
            if value['state'] != 'PASS_FIRST_ALL150_CONTENT_GOAL_NATIVE_OUTPUTS_NOT_FULL40_48_QUALITY':
                raise ValueError('Actual first150 native QA terminal differs')
            return value
        proc = Path('/proc') / str(launch['pid'])
        if not proc.exists():
            raise RuntimeError('Native parent absent without terminal; inspect before explicit recovery')
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[19] != str(launch['start_ticks']) or stat[0] == 'Z' or time.monotonic() > deadline:
            raise RuntimeError('Native dependency handle or bounded observation differs')
        time.sleep(5)


def run(script, phase, GPU_seconds=None, output_bytes=0):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU_seconds is not None:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB,
            '--max-seconds', str(GPU_seconds), '--planned-output-bytes', str(output_bytes),
            '--capacity-reason', 'First missing candidate VERIFY only; adopt all old successful VERIFY,365 BASE batches,head and current40.48 route; no RGB/media/processor/training replay',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU_seconds is not None else '',
                     OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual content-summary downstream failed; preserve successes: ' + phase)


def admission(native, cpu):
    protocol = read(CODE / 'summary_protocol85.json')
    remaining = min(1800, math.floor(protocol['profile_development_GPU_seconds_max_including_fit_and_all_failures']
                                    - native['profile_development_GPU_seconds']))
    calls = cpu['maximum_first_new_VERIFY_calls']; estimate = measured_cost(calls)
    if estimate['conservative_estimate'] > remaining or native['all_goal_GPU_seconds'] + remaining > 43200:
        raise ValueError('Actual measured first missing VERIFY cost exceeds fixed remaining budget')
    planned = calls * 131072 + 8388608
    if shutil.disk_usage(ROOT).free < planned:
        raise RuntimeError('Specific remaining VERIFY/proof artifacts do not fit actual root capacity')
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Host or protected CONTROL5 differs; do not signal it')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU compute appeared; preserve inputs without collision')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'summary_protocol85.json'),
        actual_native_terminal=identity(ROOT / 'summary_selection91/completion.json'),
        measured_cost=estimate, remaining_max_seconds=remaining, proposed_new_bytes=planned,
        actual_GPU_apps=apps, CPU=subprocess.check_output(
            ['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    return remaining, planned


def main():
    OUT.mkdir(); native = await_native()
    run('summary_verify92_prepare.py', 'first_VERIFY_input_CPU')
    cpu = read(ROOT / 'summary_verify_inputs92/completion.json')
    if cpu['state'] != 'ALL_CONTENT_GOAL_VERIFY_INPUTS_PASS':
        raise ValueError('Actual complete first/adopted VERIFY inputs absent')
    remaining, planned = admission(native, cpu)
    names = FILES + ['event_chain78.py', 'event_full79.py', 'summary_context90.py',
        't_io.py', 't_runtime39.py', 'reference_gpu19.py', 'reference_data18.py',
        'frozen_branch46.py', 'development_review48.py', 'development_verify46.py',
        'development_data46.py', 'preference_reward.py', 'joint_data44.py',
        'native_sets.py', 'prompt_contract13.py', 'summary_protocol85.json']
    save(OUT / 'source_input_lock.json', dict(registration=identity(OUT / 'registration.json'),
        actual_verify_CPU=identity(ROOT / 'summary_verify_inputs92/completion.json'),
        code={name: identity(CODE / name) for name in names}, wrapper=identity(WRAPPER),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        actual_frozen40_48_route=identity(ROOT / 'event_route77/CPU_completion.json')))
    charged = 0.
    if cpu['maximum_first_new_VERIFY_calls']:
        run('summary_verify93_gpu.py', 'GPU', remaining, planned)
        resource = read(RUN / 'controller' / (JOB + '.resource.json'))
        ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
        if (resource['status'] != 'completed' or resource['exit_code'] != 0
                or [row for row in ledger if row.get('name') == JOB] != [resource]):
            raise ValueError('Actual natural first missing VERIFY terminal/unique ledger differs')
        charged = resource['charged_seconds']
    else:
        save(OUT / 'GPU_completion.json', dict(state='ALL_VERIFY_ADOPTED_NO_NEW_GPU',
            outputs=cpu['adopted_successful_outputs'], first_new_keys=[], first_new_calls=0))
    run('summary_full94_review.py', 'first_full_source_CPU')
    review = read(OUT / 'review.json')
    save(OUT / 'completion.json', dict(state=review['state'], review=identity(OUT / 'review.json'),
        first_full_CPU=identity(OUT / 'independent_CPU_completion.json'),
        first_new_VERIFY_calls=cpu['maximum_first_new_VERIFY_calls'], GPU_seconds=charged,
        all_goal_GPU_seconds=native['all_goal_GPU_seconds'] + charged,
        profile_development_GPU_seconds=native['profile_development_GPU_seconds'] + charged,
        actual_parameters=8869330010, exact_current40_48_comparison=True,
        no_automatic_confirmation_or_production=True, new_training=0, new_packages=0,
        original40_47_and40_48_unchanged=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_raw_and_fees=True))
        raise
