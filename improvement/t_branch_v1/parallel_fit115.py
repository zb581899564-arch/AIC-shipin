"""Bounded fitting diagnosis after105 STOP; no retraining or automatic continuation."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'parallel_fit115'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_first_frozen_final_fit25_no_update_20261023_v115'


def admission():
    protocol = read(CODE / 'parallel_fit115.json')
    stop = read(ROOT / 'parallel_full109/completion.json')
    if (stop['state'] != 'STOP_FIXED_PARALLEL105_DEVELOPMENT'
            or stop['all_goal_GPU_seconds'] != protocol['all_goal_settled_before']
            or stop['all_goal_GPU_seconds'] + protocol['diagnostic_GPU_seconds_max_all_failures'] > 43200):
        raise ValueError('Actual completed STOP or remaining global budget differs')
    if read(ROOT / 'native_objective114/completion.json')['state'] != (
            'FIRST_FIT_ONLY_NATIVE_OBJECTIVE_AND_CHAIN_RULE_CPU_AUDIT_COMPLETE'):
        raise ValueError('First fixed CPU-only objective diagnosis absent')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Host or protected stopped CONTROL5 differs; never signal')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip() or shutil.disk_usage(ROOT).free < protocol['proposed_artifact_bytes']:
        raise RuntimeError('Specific diagnostic artifacts or actual GPU conflict; preserve external tasks')
    old_protocol = read(CODE / 'parallel_protocol105.json')
    for key in ['protected_original', 'protected_best']:
        check(old_protocol[key])
    inputs = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(inputs['loss_bindings']))
    publisher = data['schedule'][0]; sids = data['publishers'][publisher]
    if sids != ['L7ddd6bf6c93a'] or len(data['sources'][sids[0]]['cases']) != 25:
        raise ValueError('Old preregistered first publisher/full25-window source differs')
    update = read(ROOT / 'parallel_remaining108/publisher/P1/acceptance.json')
    initial, losses = {}, []
    for ref in update['all_prescribed_micro']:
        row = read(check(ref)); selection = row['actual_selection']
        output = read(check(selection))
        if output['source'] != sids[0] or output['actual_model_state'] != update['before']:
            raise ValueError('Original pre-update fitting reference is not the exact initial actor')
        initial[output['case']] = selection
        teacher = read(ROOT / 'parallel_cost107/first_TF_raw.json') if row.get('adopted_first_CPU') else row['actual_teacher']
        losses.append(teacher['weighted_preference_loss'])
    names = ['parallel_fit115.py', 'parallel_fit115_gpu.py', 'parallel_fit115_cpu.py', 'parallel_fit115.json',
        'parallel_forward107.py', 'parallel_input106.py', 'parallel_audit107.py', 'parallel_train108.py',
        'native_state100.py', 'native_prepared103.py', 'native_training_data99.py', 't_runtime39.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'parallel_fit115.json'),
        code={name: identity(CODE / name) for name in names}, actual_inputs=identity(ROOT / 'parallel_inputs106/completion.json'),
        adopted_source_lock108=identity(ROOT / 'parallel_remaining108/source_input_lock.json'),
        original_complete_training_CPU=identity(ROOT / 'parallel_remaining108/CPU_completion.json'),
        rejected_complete_development=identity(ROOT / 'parallel_full109/completion.json'),
        fixed_first_publisher=publisher, source=sids[0], actual_first_new_calls=25,
        initial_outputs=initial, initial_model_state=update['before'], initial_source_training_loss=sum(losses),
        initial_first_CPU=[identity(ROOT / 'parallel_cost107/CPU_completion.json'),
                           identity(ROOT / 'parallel_remaining108/CPU_completion.json')],
        final_adapter=read(ROOT / 'parallel_remaining108/GPU_completion.json')['final_adapter'],
        actual_GPU_apps=apps, CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args',
            '--sort=-pcpu'], text=True).splitlines()[:12], RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
        all_old_media_inputs_training_and_initial_QA_adopted=True, original4confirmation_unread=True))
    return protocol


def run(script, phase, protocol, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds',
            str(protocol['diagnostic_GPU_seconds_max_all_failures']), '--planned-output-bytes',
            str(protocol['proposed_artifact_bytes']), '--capacity-reason',
            'First final-checkpoint25 fit queries, all old pre-update25/input/CPU adopted. No training, decode, ASR, checkpoint choice, confirmation or production.',
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
        raise RuntimeError('First fitting diagnosis phase failed; preserve successes: ' + phase)


def main():
    OUT.mkdir(); protocol = admission()
    run('parallel_fit115_gpu.py', 'GPU', protocol, gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
            if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in rows if r.get('name') == JOB] != [resource]:
        raise ValueError('Actual fitting diagnostic natural terminal/unique ledger differs')
    run('parallel_fit115_cpu.py', 'first_CPU', protocol)
    result = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], CPU=identity(OUT / 'CPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=protocol['all_goal_settled_before'] + resource['charged_seconds'],
        actual_first_new_fit_queries=25, no_training_or_confirmation_or_package_admission=True,
        old105_STOP_unchanged=True, new_T_ZIPs=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes_and_fees=True))
        raise
