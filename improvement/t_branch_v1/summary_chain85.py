"""Unique first217 fit perception after actual AV gates; never automatically train."""
import os
from pathlib import Path
import json
import shutil
import subprocess
import time
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'summary_caption85'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
CODE = Path(__file__).parent
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_first_fit_neutral_AV_content217_20261022_v85'


def actual_AV_terminal():
    launch = read(ROOT / 'summary_av83_launch.json'); deadline = time.monotonic() + 2400
    while True:
        complete, failure = ROOT / 'summary_av83/completion.json', ROOT / 'summary_av83/failure.json'
        if failure.exists() or (ROOT / 'summary_av83_dependency_failure.json').exists():
            raise RuntimeError('Upstream AV failed; never restart or repeat it here')
        if complete.exists():
            value = read(complete)
            if value['state'] != 'FIRST_ALL217_FIT_AV_INPUTS_PASS_NOT_TRAINING_ADMISSION':
                raise ValueError('Actual217 complete AV terminal differs')
            return value
        proc = Path('/proc') / str(launch['pid'])
        if not proc.exists():
            raise RuntimeError('Actual AV handle missing without terminal; inspect, never re-launch')
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[19] != launch['start_ticks'] or stat[0] == 'Z' or time.monotonic() > deadline:
            raise RuntimeError('AV identity/wait bound differs; preserve all successful inputs')
        time.sleep(3)


def run(script, phase, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '3000',
            '--planned-output-bytes', '30000000', '--capacity-reason',
            'First217 fit-only BASE neutral observations and streamed independent CPU QA; original217 visual/AV inputs all accepted; one bounded temporary full score matrix; no training or new media',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '',
                OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First fit event phase failed; keep all successes: ' + phase)


def main():
    av = actual_AV_terminal(); OUT.mkdir()
    protocol = read(CODE / 'summary_protocol85.json')
    baseline = read(ROOT / 'summary_baseline86/completion.json')
    if baseline['state'] != 'FIRST_TWO_BASE_CONTENT_GOALS_AND_CPU_PASS_NOT_TIME_QUALITY':
        raise ValueError('Actual first2 BASE goals/CPU/cost gate missing')
    charged = baseline['profile_development_GPU_seconds']
    if charged + 3000 + 1000 + 2000 > protocol['profile_development_GPU_seconds_max_including_fit_and_all_failures']:
        raise ValueError('Fixed profile cannot fund fit/training/first development phases')
    if baseline['all_goal_GPU_seconds'] + 3000 > protocol['Goal_all_GPU_seconds_max']:
        raise ValueError('Original total Goal budget exceeded')
    if sum(map(len, av['accepted'].values())) != 217 or set(av['accepted']) != set(protocol['fit_sources']):
        raise ValueError('Actual complete217 fit AV identities differ')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip() or shutil.disk_usage(ROOT).free < 30000000:
        raise RuntimeError('Actual external GPU work or proposed output capacity conflicts with first phase')
    if shutil.disk_usage('/dev/shm').free < 128 * 151936 * 4:
        raise RuntimeError('Actual temporary score matrix cannot fit')
    names = ['summary_chain85.py', 'summary_caption85_gpu.py', 'summary_caption85_cpu.py',
        'summary_score86.py', 'summary_content85_common.py', 'summary_protocol85.json',
        'summary_text_inputs87.py', 'event_memory69_common.py', 'coarse_call25.py',
        't_io.py', 't_runtime39.py', 'causal_policy32.py']
    save(OUT / 'source_input_lock.json', dict(code={n: identity(CODE / n) for n in names},
        complete_AV_inputs=identity(ROOT / 'summary_av83/completion.json'),
        target_contract=identity(ROOT / 'summary_contract85/completion.json'),
        actual_original2_BASE_goals=identity(ROOT / 'summary_baseline86/completion.json'),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        wrapper=identity(WRAPPER), actual_GPU_apps_at_admission=apps, new_training_admitted=False))
    run('summary_caption85_gpu.py', 'GPU', GPU=True)
    record = read(RUN / 'controller' / (JOB + '.resource.json'))
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [r for r in rows if r.get('name') == JOB] != [record]:
        raise ValueError('Actual first217 event natural GPU terminal/unique ledger differs')
    run('summary_text_inputs87.py', 'first_text_CPU')
    result = read(ROOT / 'summary_text_inputs87/completion.json')
    save(OUT / 'completion.json', dict(state='FIRST217_FIT_EVENTS_AND86_CONTENT_INPUTS_PASS_NOT_TRAINING_ADMISSION',
        first_events=217, first_output_CPU=217, actual_original_reviews=result['actual_review_count'],
        actual_training_inputs=identity(ROOT / 'summary_text_inputs87/completion.json'),
        actual_events=identity(OUT / 'GPU_completion.json'), GPU_seconds=record['charged_seconds'],
        all_goal_GPU_seconds=baseline['all_goal_GPU_seconds'] + record['charged_seconds'],
        profile_development_GPU_seconds=charged + record['charged_seconds'],
        new_training=0, new_packages=0, confirmation_read=False,
        next='Exact live new-adapter parameter/gradient/save-reload and measured remaining full-cost gate before the fixed10-update content-supervision training; no automatic training or426.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_and_fees=True))
        else:
            save(ROOT / 'summary_chain85_dependency_failure.json', dict(traceback=traceback.format_exc(), no_upstream_restart=True))
        raise
