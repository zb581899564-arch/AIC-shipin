"""Unique originalTIME model job after all150 actual new context inputs pass."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'summary_selection91'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_original_TIME_source_goal_three_conditions150_20261022_v91'


def run(script, phase, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '1800',
            '--planned-output-bytes', '40000000', '--capacity-reason',
            'First150 unique originalTIME/current-card source-goal contexts; all real inputs CPU passed; only native projected outputs/proofs, no video/processor/training or old model replay',
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
        raise RuntimeError('Actual content-goal native phase failed; preserve all successes: ' + phase)


def main():
    OUT.mkdir(); goals = read(ROOT / 'summary_goals89/completion.json')
    cpu = read(ROOT / 'summary_context90/completion.json')
    protocol = read(CODE / 'summary_protocol85.json')
    if (cpu['state'] != 'FIRST_ALL150_SOURCE_SUMMARY_NATIVE_CONTEXT_INPUTS_PASS'
            or cpu['unique_first_model_calls'] != 150):
        raise ValueError('Actual complete150 distinct native inputs absent; never repeat duplicate successful tasks')
    if (goals['profile_development_GPU_seconds'] + 1800 + 1800
            > protocol['profile_development_GPU_seconds_max_including_fit_and_all_failures']
            or goals['all_goal_GPU_seconds'] + 1800 > protocol['Goal_all_GPU_seconds_max']):
        raise ValueError('Actual remaining fixed budget cannot fund native selection and full downstream')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip() or shutil.disk_usage(ROOT).free < 40000000:
        raise RuntimeError('Actual external GPU or proposed native output capacity conflicts')
    names = ['summary_selection91.py', 'summary_select91_gpu.py', 'summary_select91_cpu.py',
        'summary_context90.py', 'summary_selector_interface90.json', 'summary_protocol85.json',
        'event_select72_gpu.py', 'event_select72_cpu.py', 'event_select72_common.py',
        'event_native71.py', 'event_table71.py', 'causal_policy32.py', 't_io.py', 't_runtime39.py']
    save(OUT / 'source_input_lock.json', dict(code={n: identity(CODE / n) for n in names},
        complete_actual_native_context_CPU=identity(ROOT / 'summary_context90/completion.json'),
        trained_goals=identity(ROOT / 'summary_goals89/completion.json'),
        final_summary_adapter=goals['final_adapter'], prospective_method_parameters=8869330010,
        native_grammar=cpu['old_native_grammar_CPU_adopted']['code'],
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        wrapper=identity(WRAPPER), actual_GPU_apps_at_admission=apps,
        no_fresh_confirmation_or_training_or_label_read=True))
    run('summary_select91_gpu.py', 'GPU', GPU=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [resource]:
        raise ValueError('Actual native150 natural GPU terminal/unique ledger differs')
    run('summary_select91_cpu.py', 'first_output_CPU')
    result = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], actual_new_TIME_calls=150,
        first_independent_output_CPU=identity(OUT / 'CPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=goals['all_goal_GPU_seconds'] + resource['charged_seconds'],
        profile_development_GPU_seconds=goals['profile_development_GPU_seconds'] + resource['charged_seconds'],
        no_time_quality_confirmation_or_package_admission=True,
        next='Only first missingVERIFY and full frozen semantic/current40.48/all-reviewer final masks can decide this fixed content-supervision profile. No coarse-only quality gate, no further training.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_raw_and_fees=True))
        raise
