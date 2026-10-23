"""Exact remaining216 training/five updates and150dev under original3600 limit."""
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'parallel_remaining108'
CODE = Path(__file__).parent
TEMP = Path('/dev/shm/aic_T_parallel_remaining108')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_parallel_queries_exact_remaining216_five_updates150dev_20261023_v108'


def run(script, phase, seconds=None):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if seconds is not None:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', str(seconds),
            '--planned-output-bytes', '260000000', '--capacity-reason',
            'Exact first107gradient/Adam/RNG adoption, first remaining216 independent-query backward windows, fixed5publisher updates/finalFP32adapter then150finaldev; actual firstcostPASS, no old model/input calls repeated or scope/cap changes. Full gradient recovery in tmpfs, firstAdam witness/finaladapter on root.',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if seconds is not None else '',
                     OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = process.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Exact remaining query phase failed; retain all successful windows/updates: ' + phase)


def admission():
    prior = read(ROOT / 'parallel_cost107/completion.json')
    protocol = read(CODE / 'parallel_protocol105.json')
    if (prior['state'] != 'FIRST_PARALLEL50_CONTROL_GRADIENT_CPU_PASS_COST_PASS'
            or not prior['remaining216_and150dev_cost_admitted']):
        raise ValueError('Actual complete-scope first control/micro cost not admitted')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Actual host/CONTROL5 guard differs; do not signal')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    first = read(check(prior['actual_outputs']))['first_micro']
    gradient_bytes = first['exact_successful_gradient']['file']['bytes']
    #216 new cumulative states,5 clipped states,5 actor+two-moment Adam states,small overhead.
    temporary_bytes = (216 + 5 + 5 * 3) * gradient_bytes + 32000000
    if (apps.strip() or shutil.disk_usage(ROOT).free < 260000000
            or shutil.disk_usage(TEMP.parent).free < temporary_bytes or TEMP.exists()):
        raise RuntimeError('Specific remaining gradient/final artifacts conflict with live capacity/external job')
    seconds = math.floor(prior['remaining_native3600_seconds'])
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'parallel_protocol105.json'),
        actual_first_cost=identity(ROOT / 'parallel_cost107/completion.json'),
        original_initial50_and_first_micro_adopted=True, actual_new_target_forwards=216,
        actual_new_development_forwards=150, fixed_optimizer_updates=5,
        exact_GPU_seconds_limit=seconds, original_native_total_limit=3600, original_profile_limit=5400,
        specific_root_upper_bytes=260000000, specific_tmpfs_upper_bytes=temporary_bytes,
        actual_GPU_apps=apps, CPU=subprocess.check_output(
            ['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    names = ['parallel_remaining108.py', 'parallel_remaining108_gpu.py', 'parallel_remaining108_cpu.py',
        'parallel_step108.py', 'parallel_train108.py', 'parallel_dev108.py', 'parallel_training_audit108.py',
        'parallel_input106.py', 'parallel_query105.py', 'parallel_forward107.py', 'parallel_training107.py',
        'parallel_audit107.py', 'parallel_protocol105.json', 'native_prepared103.py', 'native_recovery102.py',
        'native_actor98.py', 'native_codec98.py', 'native_state100.py', 'native_render100.py',
        'native_training_data99.py', 'actor_roles33.py', 'joint_checkpoint44.py', 'joint_rollout47.py',
        'summary_recovery88.py', 'summary_train88_cpu.py', 'native_sets.py', 'joint_data44.py',
        'development_data46.py', 't_io.py', 't_runtime39.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        protocol=identity(CODE / 'parallel_protocol105.json'),
        actual_inputs=identity(ROOT / 'parallel_inputs106/completion.json'),
        first_actual_micro=prior['actual_outputs'], first_actual_CPU=prior['first_CPU'],
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        wrapper=identity(WRAPPER), first_live_role_footprint=8869330010))
    return prior, seconds


def main():
    OUT.mkdir()
    prior, seconds = admission()
    run('parallel_remaining108_gpu.py', 'GPU', seconds)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0
            or [row for row in ledger if row.get('name') == JOB] != [resource]):
        raise ValueError('Actual remaining query natural terminal/unique ledger differs')
    run('parallel_remaining108_cpu.py', 'first_CPU')
    result = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], first_CPU=identity(OUT / 'CPU_completion.json'),
        actual_outputs=identity(OUT / 'GPU_completion.json'), GPU_seconds=resource['charged_seconds'],
        all_goal_GPU_seconds=prior['all_goal_GPU_seconds'] + resource['charged_seconds'],
        profile_GPU_seconds=prior['profile_GPU_seconds'] + resource['charged_seconds'],
        actual_new_target_forwards=216, actual_optimizer_updates=5, actual_new_development_forwards=150,
        complete_native_training_windows=217, actual_complete_parameters=8869330010,
        old_initial50_and_firstmicro_CPU_adopted=True,
        no_quality_confirmation_or_production_admission=True,
        next='First all-source downstream D8/VERIFY/current40.48 comparison and actual remaining-profile cost; adopt all successful semantic/route/identical VERIFY. No new confirmation or426 until complete quality gates.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_all_successful_raw_gradient_updates_checkpoints_and_fees=True,
                no_automatic_repeat_or_success_to_empty=True))
        raise
