"""First fixed on-policy micro, exact recovery and complete-scope cost admission."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'native_first_micro101'
TEMP = Path('/dev/shm/aic_T_native_action100_first')
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_native_action_first_onpolicy_gradient_micro_20261023_v101'


def child(script, phase, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '600',
            '--planned-output-bytes', '16000000', '--capacity-reason',
            'One first fixed217 on-policy native-action micro; first greedy/teacher/gradient recovery retained in tmpfs, no update or repeated inputs/control; actual cost before remaining216 plus150dev admission',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '',
                     OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = process.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First native cost micro failed; preserve exact accepted work: ' + phase)


def admission():
    protocol = read(CODE / 'native_action_protocol98.json')
    control = read(ROOT / 'native_action_control100/completion.json')
    if (control['state'] != 'FIRST50_ORIGINAL_TIME_NATIVE_CODEC_CPU_PASS_NOT_QUALITY'
            or read(ROOT / 'native_action_inputs99/completion.json')['state']
                != 'FIRST_ALL417_LOGICAL_NATIVE_ACTION_INPUTS_CPU_PASS'
            or read(ROOT / 'native_action_loss99/completion.json')['state']
                != 'FIRST217_NATIVE_ACTION_LOSS_INPUT_BINDINGS_PASS'):
        raise ValueError('First current native controls/all inputs/loss bindings incomplete')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Actual host/CONTROL5 guard differs; do not signal it')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if (apps.strip() or shutil.disk_usage(ROOT).free < 16000000
            or shutil.disk_usage(TEMP.parent).free < 150000000 or TEMP.exists()):
        raise RuntimeError('Specific first-micro artifacts conflict with current capacity or external job')
    rules = ROOT / 'official_rules23_before_native101/completion.json'
    if read(rules)['state'] != 'CURRENT23_OFFICIAL_HTML_AND_NOTICE_LINKS_REVIEWED':
        raise ValueError('Current official scope not reviewed before first native micro')
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'native_action_protocol98.json'),
        first_prescribed_micro_only=True, actual_optimizer_updates=0, preserve_successful_micro_for_remaining=True,
        first_greedy_calls=1, first_teacher_backwards=1, GPU_limit_seconds=600,
        specific_root_artifact_upper_bytes=16000000, specific_tmpfs_upper_bytes=150000000,
        current_rules=identity(rules), current_GPU_apps=apps,
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'],
                                    text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    names = ['native_first_micro101.py', 'native_first_micro101_gpu.py', 'native_first_micro101_cpu.py',
        'native_teacher101_cpu.py', 'native_greedy100.py', 'native_audit100.py', 'native_render100.py',
        'native_state100.py', 'native_input99.py', 'native_codec98.py', 'native_actor98.py',
        'native_training_data99.py', 'actor_roles33.py', 'joint_rollout47.py', 'joint_checkpoint44.py',
        'summary_recovery88.py', 'joint_data44.py', 'native_sets.py', 't_io.py', 't_runtime39.py',
        'frozen_branch46.py', 'native_action_protocol98.json']
    wrapper = identity(WRAPPER)
    if wrapper['sha256'] != '9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
        raise ValueError('Existing unique shared GPU wrapper differs')
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        loss_bindings=identity(ROOT / 'native_action_loss99/completion.json'),
        actual_inputs=identity(ROOT / 'native_action_inputs99/completion.json'),
        protocol=identity(CODE / 'native_action_protocol98.json'), wrapper=wrapper,
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        actual_initial50=identity(ROOT / 'native_action_control100/completion.json'),
        actual_codec_role_CPU=identity(ROOT / 'native_action_contract98/completion.json')))
    return control


def completion(control):
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0
            or [row for row in ledger if row.get('name') == JOB] != [resource]):
        raise ValueError('Actual first micro natural terminal/unique charge differs')
    child('native_first_micro101_cpu.py', 'first_gradient_CPU')
    result = read(OUT / 'CPU_completion.json')
    spent = control['native_profile_GPU_seconds'] + resource['charged_seconds']
    remaining = 5600 - spent
    projected = result['cost_projection']['conservative_remaining_GPU_seconds']
    fits = projected <= remaining
    save(OUT / 'completion.json', dict(state='FIRST_NATIVE_MICRO_CPU_PASS_REMAINING_COST_' + ('PASS' if fits else 'STOP'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=control['all_goal_GPU_seconds']
            + resource['charged_seconds'], native_profile_GPU_seconds=spent,
        actual_first_greedy_calls=1, actual_first_teacher_backwards=1, actual_optimizer_updates=0,
        first_CPU=identity(OUT / 'CPU_completion.json'), actual_outputs=identity(OUT / 'GPU_completion.json'),
        native_combined_remaining_seconds=remaining, conservative_remaining_seconds=projected,
        remaining216_and150dev_cost_admitted=fits, profile_remaining_seconds=7200 - spent,
        complete_original_scope_not_reduced=True, quality_confirmation_production_admitted=False,
        next='Explicit exact remaining recovery only if cost PASS; restore accepted first micro and never repeat it. No automatic full train, confirmation, production or packaging.'))


def main():
    OUT.mkdir()
    control = admission()
    child('native_first_micro101_gpu.py', 'GPU', gpu=True)
    completion(control)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_all_successful_greedy_teacher_gradient_RNG_and_fees=True,
                no_automatic_repeat_or_recovery=True))
        raise
