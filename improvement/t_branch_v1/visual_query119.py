"""First2 actual local visual-query engineering only; no automatic fitting/production."""
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

OUT = ROOT / 'visual_query_engine119'
CODE = Path(__file__).parent
TEMP = Path('/dev/shm/aic_T_visual_query119_first')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_local_visual_shared_prefix_first2_20261023_v119'


def admission():
    protocol = read(CODE / 'visual_query_protocol119.json')
    previous = read(ROOT / 'query_binding117/completion.json')
    if (previous['state'] != 'FIRST_ALL50_QUERY_BINDING_CPU_AND_CAUSAL_DIAGNOSIS_COMPLETE'
            or previous['all_goal_GPU_seconds'] != protocol['Goal_GPU_seconds_before']
            or previous['all_goal_GPU_seconds'] + protocol['profile_GPU_seconds_max_all_failures'] > 43200):
        raise ValueError('Complete causal evidence or original Goal budget differs')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Host/CONTROL5 identity differs; never signal')
    if (TEMP.exists() or shutil.disk_usage(ROOT).free < protocol['root_artifact_upper_bytes']
            or shutil.disk_usage(TEMP.parent).free < protocol['temporary_full_activation_upper_bytes']):
        raise RuntimeError('Specific first real visual-query proof capacity or unique temporary root differs')
    for key in ['protected_original', 'protected_best']:
        check(read(CODE / 'parallel_protocol105.json')[key])
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'visual_query_protocol119.json'),
        actual_CPU118=identity(ROOT / 'shared_visual_query118_CPU/completion.json'),
        causal117=identity(ROOT / 'query_binding117/completion.json'),
        first_actual_multimodal_prefills=2, first_actual32_branch_decoder_batches=2,
        source_labels_or_training_or_confirmation_read=False,
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'],
                                    text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), str(TEMP.parent)], text=True)))
    return protocol


def freeze_inputs():
    inputs = read(ROOT / 'visual_query_inputs119/completion.json')
    if inputs['state'] != 'FIRST_ALL25_LOCAL_VISUAL_SHARED_PREFIX_CPU_INPUTS_PASS':
        raise ValueError('All25 first shared-context CPU signatures/native mapping required')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU task conflicts with current unique shared wrapper')
    names = ['visual_query119.py', 'visual_query119_gpu.py', 'visual_query119_cpu.py',
        'visual_query_prefix119.py', 'visual_query_inputs119.py', 'visual_query_runtime119.py',
        'visual_query_protocol119.json', 'shared_visual_query118.py', 'shared_visual_query118_cpu.py',
        'native_render100.py', 'parallel_query105.py', 'native_prepared103.py',
        'parallel_train108.py', 't_runtime39.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'visual_query_protocol119.json'),
        code={name: identity(CODE / name) for name in names},
        actual_inputs=identity(ROOT / 'visual_query_inputs119/completion.json'),
        previous_original_model=identity(ROOT / 'parallel_remaining108/GPU_completion.json'),
        first_CPU118=identity(ROOT / 'shared_visual_query118_CPU/completion.json'),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        actual_GPU_apps=apps, all_old_pixels_processor_ASR_original_CPU_adopted=True))


def run(script, phase, protocol, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds',
            str(protocol['first_engineering_GPU_seconds_max_all_failures']), '--planned-output-bytes',
            str(protocol['root_artifact_upper_bytes']), '--capacity-reason',
            'First2 original8B local-visual shared-prefix engineering; all25newtextCPU first, old native pixels/ASR adopted. First actual visual/attention/LM activations only new tmpfs upper536870912B, checked separately; no training or production.',
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
        raise RuntimeError('First real visual-query engineering failed; preserve all successes: ' + phase)


def main():
    OUT.mkdir(); protocol = admission()
    run('visual_query_inputs119.py', 'first_inputs_CPU', protocol)
    freeze_inputs()
    run('visual_query119_gpu.py', 'GPU', protocol, gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
            if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in rows if r.get('name') == JOB] != [resource]:
        raise ValueError('Actual real visual-query natural terminal/unique ledger differs')
    run('visual_query119_cpu.py', 'first_real_CPU', protocol)
    gpu = read(OUT / 'GPU_completion.json')
    views = [row['complete_view_seconds'] for row in gpu['outputs'].values()]
    overhead = max(60., resource['charged_seconds'] - sum(views))
    estimate = 23 * max(views) + overhead
    remaining = math.floor(protocol['profile_GPU_seconds_max_all_failures'] - resource['charged_seconds'])
    save(OUT / 'completion.json', dict(state='FIRST2_REAL_VISUAL_QUERY_ENGINEERING_CPU_PASS_NOT_QUALITY',
        first_CPU=identity(OUT / 'CPU_completion.json'), actual_GPU=identity(OUT / 'GPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=protocol['Goal_GPU_seconds_before'] + resource['charged_seconds'],
        profile_GPU_seconds=resource['charged_seconds'], actual_physical_model_forwards=4,
        actual_native_decisions=64, actual_model_parameters=8853994586,
        projected_complete_remaining23_seconds=estimate, remaining_original_profile_seconds=remaining,
        complete_remaining_fit_cost_admitted=estimate <= remaining,
        no_automatic_fitting_or_training_or_confirmation_or_production=True, new_T_ZIPs=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_successful_inputs_outputs_raw_and_fees=True, no_failure_as_empty_or_automatic_retry=True))
        raise
