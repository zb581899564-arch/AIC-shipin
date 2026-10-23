"""Bound first50 same-codec originalTIME controls, adopted by later training trial."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'native_action_control100'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_native_action_original_TIME_codec_control50_20261023_v100'
FILES = ['native_action_control100.py', 'native_control100_gpu.py', 'native_control100_cpu.py',
         'native_greedy100.py', 'native_audit100.py', 'native_render100.py', 'native_state100.py']


def run(script, phase, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '900',
            '--planned-output-bytes', '6000000', '--capacity-reason',
            'First50 initial originalTIME native-codec controls; all417actual CPU inputs and217source loss bindings accepted; raw finite token projections/proofs only, no media/processor/ASR/training or old calls repeated',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '', OMP_NUM_THREADS='2',
                     MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual native-codec control phase failed; preserve successes: ' + phase)


def main():
    OUT.mkdir(); protocol = read(CODE / 'native_action_protocol98.json')
    if protocol['Goal_GPU_seconds_already_settled'] + protocol['profile_GPU_seconds_max_all_failures'] > 43200:
        raise ValueError('Whole remaining fixed profile does not fit original Goal GPU budget')
    inputs = read(ROOT / 'native_action_inputs99/completion.json')
    losses = read(ROOT / 'native_action_loss99/completion.json')
    if (inputs['state'] != 'FIRST_ALL417_LOGICAL_NATIVE_ACTION_INPUTS_CPU_PASS'
            or losses['state'] != 'FIRST217_NATIVE_ACTION_LOSS_INPUT_BINDINGS_PASS'):
        raise ValueError('Actual all417 inputs/217loss source bindings not complete')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Actual host or protected CONTROL5 changed; do not signal it')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip() or shutil.disk_usage(ROOT).free < 6000000:
        raise RuntimeError('Live external GPU or specific new control/proof capacity conflict')
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'native_action_protocol98.json'),
        same_codec_initial_controls=50, updates=0, no_quality_labels_read=True,
        native_profile_max_seconds=7200, native_combined_phase_max_seconds=5600,
        this_initial_control_max_seconds=900, fee_must_be_deducted_before_training=True,
        actual_GPU_apps=apps, CPU=subprocess.check_output(
            ['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    names = FILES + ['native_input99.py', 'native_codec98.py', 'native_actor98.py',
        'native_training_data99.py', 'development_data46.py', 'joint_data44.py',
        'native_sets.py', 'coarse_call25.py', 't_io.py', 't_runtime39.py',
        'native_action_protocol98.json', 'prompt_contract13.py']
    save(OUT / 'source_input_lock.json', dict(code={n: identity(CODE / n) for n in names},
        actual_inputs=identity(ROOT / 'native_action_inputs99/completion.json'),
        actual_source_loss_bindings=identity(ROOT / 'native_action_loss99/completion.json'),
        actual_new_CPU_contract=identity(ROOT / 'native_action_contract98/completion.json'),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        wrapper=identity(WRAPPER), original_hook_lifecycle_CPU=identity(ROOT / 'joint_hook47/completion.json')))
    run('native_control100_gpu.py', 'GPU', GPU=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0
            or [row for row in ledger if row.get('name') == JOB] != [resource]):
        raise ValueError('Actual native initial50 natural terminal/unique ledger differs')
    run('native_control100_cpu.py', 'first_output_CPU')
    result = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'],
        actual_control_CPU=identity(OUT / 'CPU_completion.json'),
        actual_outputs=identity(OUT / 'GPU_completion.json'), GPU_seconds=resource['charged_seconds'],
        all_goal_GPU_seconds=15335.679833392613 + resource['charged_seconds'],
        native_profile_GPU_seconds=resource['charged_seconds'],
        remaining_native_training_and150dev_GPU_seconds=5600 - resource['charged_seconds'],
        no_actual8B_training_or_quality_or_package=True,
        next='Adopt all50controls and first CPU exactly once. Fixed5publisher/217native on-policy action training and150final dev only after actual parameter/first-micro cost admission under remaining5600; do not change profile or repeat controls.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_raw_and_fees=True))
        raise
