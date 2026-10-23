"""Bounded same-science remaining recovery after measured input-materialization cost STOP."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'native_next_two104'
CODE = Path(__file__).parent
TEMP = Path('/dev/shm/aic_T_native_next_two104')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_native_action_exact_remaining_input_reuse_two_20261023_v104'


def run(script, phase, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '600',
            '--planned-output-bytes', '20000000', '--capacity-reason',
            'Only fixed remaining micros2/3; exact first101 gradient/Adam/RNG adopted. One validated input shared across same greedy+teacher, bounded CPU prefetch, original caps and full scientific scope unchanged; no optimizer step or old successful calls repeated',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '', OMP_NUM_THREADS='2',
                     MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = process.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Prepared remaining-two phase failed; retain successful steps: ' + phase)


def admit():
    prior = read(ROOT / 'native_first_micro101/completion.json')
    if (prior['state'] != 'FIRST_NATIVE_MICRO_CPU_PASS_REMAINING_COST_STOP'
            or prior['native_combined_remaining_seconds'] <= 600
            or read(ROOT / 'native_prepared_contract103/completion.json')['state']
                != 'PASS_THREE_PREPARED_INPUT_LIFECYCLE_CPU_CONTRACTS'):
        raise ValueError('Actual sequential cost STOP/first micro or input-reuse CPU gate differs')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Actual host or CONTROL5 guard differs; do not signal')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if (apps.strip() or shutil.disk_usage(ROOT).free < 20000000
            or shutil.disk_usage(TEMP.parent).free < 130000000 or TEMP.exists()):
        raise RuntimeError('Specific two-micro artifacts conflict with current capacity or external GPU')
    protocol = read(CODE / 'native_action_protocol98.json')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    save(OUT / 'registration.json', dict(original_protocol=identity(CODE / 'native_action_protocol98.json'),
        explicit_engineering=identity(CODE / 'native_input_reuse_registration103.json'),
        original_sequential_cost_STOP=identity(ROOT / 'native_first_micro101/completion.json'),
        no_old_successful_generation_teacher_gradient_or_CPU_repeated=True,
        fixed_next_micro_numbers=[2, 3], actual_optimizer_updates=0, GPU_limit_seconds=600,
        root_artifact_upper_bytes=20000000, tmpfs_artifact_upper_bytes=130000000,
        actual_GPU_apps=apps, CPU=subprocess.check_output(
            ['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
        official_rules=identity(ROOT / 'official_rules23_before_native101/completion.json')))
    names = ['native_next_two104.py', 'native_next_two104_gpu.py', 'native_next_two104_cpu.py',
        'native_generate104.py', 'native_teacher104.py', 'native_prepared103.py',
        'native_recovery102.py', 'native_actor98.py', 'native_codec98.py', 'native_state100.py',
        'native_audit100.py', 'native_render100.py', 'native_input99.py', 'native_training_data99.py',
        'actor_roles33.py', 'joint_rollout47.py', 'joint_checkpoint44.py', 'summary_recovery88.py',
        'joint_data44.py', 'native_sets.py', 't_io.py', 't_runtime39.py', 'native_action_protocol98.json',
        'native_input_reuse_registration103.json']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        first_micro=identity(ROOT / 'native_first_micro101/GPU_completion.json'),
        first_micro_CPU=identity(ROOT / 'native_first_micro101/CPU_completion.json'),
        loss_bindings=identity(ROOT / 'native_action_loss99/completion.json'),
        actual_inputs=identity(ROOT / 'native_action_inputs99/completion.json'),
        protocol=identity(CODE / 'native_action_protocol98.json'), wrapper=identity(WRAPPER),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies']))
    return prior


def main():
    OUT.mkdir()
    prior = admit()
    run('native_next_two104_gpu.py', 'GPU', gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0
            or [row for row in ledger if row.get('name') == JOB] != [resource]):
        raise ValueError('Actual bounded remaining-two natural terminal/unique ledger differs')
    run('native_next_two104_cpu.py', 'first_CPU')
    result = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'],
        first_CPU=identity(OUT / 'CPU_completion.json'), actual_outputs=identity(OUT / 'GPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=prior['all_goal_GPU_seconds']
            + resource['charged_seconds'], native_profile_GPU_seconds=prior['native_profile_GPU_seconds']
            + resource['charged_seconds'], remaining_original5600_seconds=result['original5600_remaining_seconds'],
        actual_new_greedy=2, actual_new_teacher_backwards=2, actual_optimizer_updates=0,
        total_successful_training_micro=3,
        remaining214_and150dev_cost_admitted=result['remaining214_and150dev_cost_admitted'],
        no_quality_or_confirmation_or_production_admission=True,
        next='Only if costPASS, explicit restore micro3 exact gradient+RNG/initial actor+Adam; process fixed remaining214 and150dev. No repeated micros1..3, no shortened scope or cap extension. CostSTOP means stop this fixed native profile.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_all_successful_calls_raw_gradient_RNG_and_fees=True,
                no_automatic_repeat_or_recovery=True))
        raise
