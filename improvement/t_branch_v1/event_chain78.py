"""First missing VERIFY and full source review under the fixed downstream budget."""
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'event_full78'
CPU = ROOT / 'event_verify_inputs76'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_event_memory_first_missing_VERIFY_20261022_v78'
FILES = ['event_chain78.py', 'event_verify78_gpu.py', 'event_full79.py']


def measured_cost(calls):
    prior = read(ROOT / 'development_remaining55/verify_GPU_completion.json')['outputs']
    seconds = [read(check(read(check(ref))['raw']))['seconds'] for ref in prior.values()]
    old = read(RUN / 'controller/T_joint4_dev_only_VERIFY_remaining_20261022_v55.resource.json')
    return dict(first_missing_calls=calls, old_calls=len(seconds), prior_GPU_seconds=old['charged_seconds'],
        max_observed_task_seconds=max(seconds),
        prior_non_generation_seconds=max(0., old['charged_seconds'] - math.fsum(seconds)),
        conservative_estimate=calls * max(seconds) + max(0., old['charged_seconds'] - math.fsum(seconds)))


def run(script, GPU_seconds=None):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU_seconds is not None:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', str(GPU_seconds),
            '--planned-output-bytes', '20000000', '--capacity-reason',
            'Only first missing exact candidate VERIFY; old successful outputs and365 BASE batches adopted. New small raw/proofs, no image, model download or primary preparation',
            '--queue-seconds', '0', '--'] + command
    phase = 'GPU' if GPU_seconds is not None else 'CPU'
    with (OUT / (phase + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU_seconds is not None else '',
                OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First full event downstream stage failed: ' + phase)


def main():
    OUT.mkdir()
    route = read(ROOT / 'event_route77/completion.json')
    if route['state'] != 'PASS_FIRST_CURRENT40_48_ROUTE_BOTH_EXTERNAL_SOURCES':
        raise ValueError('Actual current-best external route must pass first')
    cpu = read(CPU / 'completion.json')
    if cpu['state'] != 'FIRST_ALL_REQUIRED_EVENT_VERIFY_INPUTS_PASS':
        raise ValueError('All actual new candidate VERIFY inputs must pass first')
    remaining = math.floor(route['remaining_fixed_downstream_GPU_seconds'])
    estimate = measured_cost(cpu['maximum_first_new_VERIFY_calls'])
    if estimate['conservative_estimate'] > remaining:
        save(OUT / 'cost_admission_failed_before_GPU.json', dict(estimate=estimate, remaining=remaining,
            no_new_GPU_or_old_success_repeated=True))
        raise RuntimeError('Measured complete required VERIFY work does not fit remaining fixed budget')
    if route['all_goal_GPU_seconds'] + remaining > 43200 or shutil.disk_usage(ROOT).free < 20000000:
        raise RuntimeError('Aggregate remaining budget or proposed output capacity insufficient')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU compute exists; preserve CPU inputs and do not launch')
    protocol = read(CODE / 'event_memory_protocol69.json')
    for key in ['protected_best', 'protected_original']:
        check({k: protocol[key][k] for k in ['path', 'bytes', 'sha256']})
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'event_memory_protocol69.json'),
        actual_route=identity(ROOT / 'event_route77/completion.json'), actual_remaining_seconds=remaining,
        measured_cost_estimate=estimate, no_new_BASE_or_event_calls=True,
        original_all_first_QA_adopted=True, actual_apps=apps,
        actual_resources=subprocess.check_output(['nvidia-smi'], text=True),
        actual_RAM=subprocess.check_output(['free', '-b'], text=True),
        actual_disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    save(OUT / 'source_input_lock.json', dict(registration=identity(OUT / 'registration.json'),
        actual_verify_CPU=identity(CPU / 'completion.json'), wrapper=identity(WRAPPER),
        code={n: identity(CODE / n) for n in FILES + ['t_io.py', 't_runtime39.py', 'reference_gpu19.py',
            'reference_data18.py', 'frozen_branch46.py', 'development_review48.py', 'preference_reward.py',
            'development_data46.py', 'joint_data44.py', 'native_sets.py', 'event_table71.py', 'prompt_contract13.py']},
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies']))
    charged = 0.
    if cpu['maximum_first_new_VERIFY_calls']:
        run('event_verify78_gpu.py', remaining)
        record = read(RUN / 'controller' / (JOB + '.resource.json'))
        rows = [json.loads(l) for l in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if l.strip()]
        if record['status'] != 'completed' or record['exit_code'] != 0 or [r for r in rows if r.get('name') == JOB] != [record]:
            raise ValueError('Unique natural remaining VERIFY ledger differs')
        charged = record['charged_seconds']
    else:
        save(OUT / 'GPU_completion.json', dict(state='ALL_VERIFY_TASKS_ALREADY_ACCEPTED_NO_NEW_GPU',
            outputs=cpu['adopted_successful_outputs'], first_new_keys=[], first_new_calls=0))
    run('event_full79.py')
    review = read(OUT / 'review.json')
    save(OUT / 'completion.json', dict(state=review['state'], review=identity(OUT / 'review.json'),
        first_full_CPU=identity(OUT / 'independent_CPU_completion.json'),
        first_new_VERIFY_calls=cpu['maximum_first_new_VERIFY_calls'], GPU_seconds=charged,
        all_goal_GPU_seconds=route['all_goal_GPU_seconds'] + charged,
        all_new_profile_GPU_seconds=route['all_goal_GPU_seconds'] + charged - 8937.787863712758,
        exact_current40_48_comparison=True, no_automatic_confirmation_or_production=True,
        new_training=0, new_packages=0, original40_47_and40_48_unchanged=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
