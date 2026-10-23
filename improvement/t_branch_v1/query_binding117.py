"""Fixed50-query causal diagnosis after full CPU gates, not candidate production."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'query_binding117'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_frozen_query_order_and_anchor_causal50_20261023_v117'


def initial_admission():
    protocol = read(CODE / 'query_binding_protocol117.json')
    previous = read(ROOT / 'parallel_fit115/completion.json')
    diagnosis = read(ROOT / 'parallel_discrimination116/completion.json')
    if (previous['state'] != 'FIRST_FINAL_FIT25_ALL_NATIVE_CPU_AND_METRICS_PASS'
            or diagnosis['state'] != 'FIRST_FIXED_FIT_NATIVE_DISCRIMINATION_DIAGNOSIS_COMPLETE'
            or previous['all_goal_GPU_seconds'] != protocol['Goal_GPU_seconds_before']
            or previous['all_goal_GPU_seconds'] + protocol['diagnostic_GPU_seconds_max_all_failures'] > 43200):
        raise ValueError('Exact prior terminal/causal scope/remaining Goal budget differs')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Actual host/CONTROL5 differs; never signal it')
    if shutil.disk_usage(ROOT).free < protocol['specific_artifact_upper_bytes']:
        raise RuntimeError('Specific complete new text/raw/proof artifacts do not fit current capacity')
    for key in ['protected_original', 'protected_best']:
        check(read(CODE / 'parallel_protocol105.json')[key])
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'query_binding_protocol117.json'),
        completed_fit=identity(ROOT / 'parallel_fit115/completion.json'),
        prior_discrimination=identity(ROOT / 'parallel_discrimination116/completion.json'),
        new_model_calls_max=50, no_labels_training_or_candidate_selection=True,
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'],
                                    text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    return protocol


def freeze_inputs(protocol):
    inputs = read(ROOT / 'query_binding_inputs117/completion.json')
    if inputs['state'] != 'FIRST_ALL50_QUERY_BINDING_TRANSFORM_CPU_INPUTS_PASS':
        raise ValueError('All actual50 bijective text/permutation CPU checks required')
    estimate = 50 * protocol['measured_consumer_upper_seconds'] + protocol['conservative_fixed_overhead_seconds']
    if estimate > protocol['diagnostic_GPU_seconds_max_all_failures']:
        raise ValueError('Actual measured complete50-query cost does not fit fixed diagnostic cap')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU activity conflicts with shared unique wrapper; preserve prepared CPU')
    names = ['query_binding117.py', 'query_binding117_gpu.py', 'query_binding117_cpu.py',
        'query_binding117_common.py', 'query_binding_inputs117.py', 'query_binding_protocol117.json',
        'parallel_fit115_gpu.py', 'parallel_forward107.py', 'parallel_audit107.py',
        'parallel_train108.py', 'native_prepared103.py', 'native_state100.py', 't_runtime39.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'query_binding_protocol117.json'),
        code={name: identity(CODE / name) for name in names},
        actual_inputs=identity(ROOT / 'query_binding_inputs117/completion.json'),
        adopted_lock115=identity(ROOT / 'parallel_fit115/source_input_lock.json'),
        complete_original25_model=identity(ROOT / 'parallel_fit115/GPU_completion.json'),
        first_original25_CPU=identity(ROOT / 'parallel_fit115/CPU_completion.json'),
        actual_GPU_apps=apps, measured_complete50_cost=estimate,
        no_input_decode_processor_ASR_or_old_model_repeated=True, no_confirmation_read=True))


def run(script, phase, protocol, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds',
            str(protocol['diagnostic_GPU_seconds_max_all_failures']), '--planned-output-bytes',
            str(protocol['specific_artifact_upper_bytes']), '--capacity-reason',
            'First50 fixed query-order/consistent-anchor causal outputs. Original25/finalactor/pixels/ASR/QA adopted, no training or candidate selection.',
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
        raise RuntimeError('First causal query stage failed; preserve all successes: ' + phase)


def main():
    OUT.mkdir(); protocol = initial_admission()
    run('query_binding_inputs117.py', 'first_inputs_CPU', protocol)
    freeze_inputs(protocol)
    run('query_binding117_gpu.py', 'GPU', protocol, gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if (resource['status'] != 'completed' or resource['exit_code'] != 0
            or [row for row in ledger if row.get('name') == JOB] != [resource]):
        raise ValueError('Actual causal-query natural terminal/unique ledger differs')
    run('query_binding117_cpu.py', 'first_outputs_CPU', protocol)
    cpu = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=cpu['state'], first_CPU=identity(OUT / 'CPU_completion.json'),
        analyses=cpu['analyses'], actual_first_new_calls=50, actual_training_updates=0,
        GPU_seconds=resource['charged_seconds'],
        all_goal_GPU_seconds=protocol['Goal_GPU_seconds_before'] + resource['charged_seconds'],
        old105_STOP_unchanged=True, new_T_ZIPs=0, no_automatic_candidate_or_followup_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_all_successful_inputs_outputs_and_fees=True))
        raise
