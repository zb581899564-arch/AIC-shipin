"""Two first final-trained source goals, adopting86 inputs and BASE controls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'summary_goals89'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_final_content_summary_two_dev_goals_20261022_v89'


def main():
    OUT.mkdir(); training = read(ROOT / 'summary_train88/completion.json')
    if training['state'] != 'FIXED10_CONTENT_TRAINING_AND_FIRST_INDEPENDENT_CPU_COMPLETE_NOT_TIME_QUALITY':
        raise ValueError('Actual complete fixed10 training and first independent CPU absent')
    protocol = read(CODE / 'summary_protocol85.json')
    if (training['profile_development_GPU_seconds'] + 300 + 1800
            > protocol['profile_development_GPU_seconds_max_including_fit_and_all_failures']
            or training['all_goal_GPU_seconds'] + 300 > protocol['Goal_all_GPU_seconds_max']):
        raise ValueError('Actual profile/Goal budget cannot fund first goal and native comparison')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    check(training['final_adapter']['weights']); check(training['final_adapter']['config'])
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip() or shutil.disk_usage(ROOT).free < 10000000 or shutil.disk_usage('/dev/shm').free < 2048 * 151936 * 4:
        raise RuntimeError('Actual external GPU or specific first goal artifact capacity conflicts')
    names = ['summary_goals89.py', 'summary_goal89_gpu.py', 'summary_goal89_cpu.py',
        'summary_score86.py', 'summary_actor88.py', 'summary_protocol85.json',
        'summary_selector_interface90.json', 'summary_context90.py', 't_io.py', 't_runtime39.py']
    save(OUT / 'source_input_lock.json', dict(code={n: identity(CODE / n) for n in names},
        actual_training=identity(ROOT / 'summary_train88/completion.json'), final_adapter=training['final_adapter'],
        actual_training_CPU=training['first_independent_CPU'],
        adopted_two_goal_CPU=identity(ROOT / 'summary_baseline86/CPU_completion.json'),
        adopted_original2_BASE_goals=identity(ROOT / 'summary_baseline86/completion.json'),
        prospective_native_interface=identity(CODE / 'summary_selector_interface90.json'),
        wrapper=identity(WRAPPER), actual_GPU_apps=apps, no_new_training_or_temporal_call_yet=True))
    command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '300',
        '--planned-output-bytes', '10000000', '--capacity-reason',
        'First2 final content-adapter goals on actual adopted source inputs, all firstCPU; retain originals, no image/media/old model replay; one declared temporary score matrix',
        '--queue-seconds', '0', '--', str(PY), '-B', '-u', str(CODE / 'summary_goal89_gpu.py')]
    with (OUT / 'GPU.log').open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
        save(OUT / 'GPU_launch.json', dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / 'GPU_terminal.json', dict(exit_code=status))
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if status or resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [resource]:
        raise ValueError('First final-summary natural GPU terminal/unique ledger differs')
    result = read(OUT / 'GPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], final_adapter=training['final_adapter'],
        actual_outputs=identity(OUT / 'GPU_completion.json'), first_trained_goals=2, first_independent_CPU=2,
        GPU_seconds=resource['charged_seconds'],
        all_goal_GPU_seconds=training['all_goal_GPU_seconds'] + resource['charged_seconds'],
        profile_development_GPU_seconds=training['profile_development_GPU_seconds'] + resource['charged_seconds'],
        observed={sid: {k:v[k] for k in ['tokens','generation_seconds']} for sid,v in result['outputs'].items()},
        no_new_training_or_temporal_quality_or_package=True,
        next='First all150 native context CPU inputs90 using exact BASE86 and trained89 goals, current card and fixed cross-source shift. Then unique originalTIME comparisons; full40.48 only after first native QA.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_raw_and_successes_and_fees=True))
        raise
