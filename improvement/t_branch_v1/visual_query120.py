"""Finish the original25 fitting diagnostic, adopting first2 and original1800 cap."""
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

OUT = ROOT / 'visual_query_fit120'
CODE = Path(__file__).parent
TEMP = Path('/dev/shm/aic_T_visual_query120_remaining')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_shared_visual_query_only_remaining23_fit_20261023_v120'


def capacity(inputs, prior):
    first = inputs['first_engineering_cases']
    retired = read(ROOT / 'visual_query_engine119/first_activation_retirement.json')['only_new_full_activations_retired']
    sizes = {name: sum(v['bytes'] for v in retired if Path(v['path']).name.startswith(name + '_')) for name in first}
    lengths = [read(check(inputs['inputs'][name]))['input_tokens'] for name in first]
    grid = read(check(inputs['inputs'][first[0]]))['video_grid_thw']
    permanent = max(read(check(prior['outputs'][name]['witnesses']))['permanent']['bytes'] for name in first)
    temporary, count = 0, 0
    for name, ref in inputs['inputs'].items():
        if name in first:
            continue
        row = read(check(ref))
        if row['video_grid_thw'] != grid:
            raise ValueError('Remaining input has a different visual geometry; no guessed capacity fallback')
        temporary += math.ceil(max(sizes.values()) * max(1., row['input_tokens'] / min(lengths))) + 1048576
        count += 1
    root = count * (permanent + 32768) + 2097152
    if count != 23 or TEMP.exists() or root > shutil.disk_usage(ROOT).free or temporary > shutil.disk_usage(TEMP.parent).free:
        raise RuntimeError('Specific complete remaining23 permanent/temporary proofs conflict with actual capacity')
    return dict(remaining_windows=count, root_artifact_upper_bytes=root, temporary_activation_upper_bytes=temporary,
        original_first119_capacity_allowances_unchanged=True, geometry_matches_actual_first119=True,
        per_first_measured_temporary=sizes, per_first_prefix_lengths=lengths)


def admission():
    protocol = read(CODE / 'visual_query_fit120.json')
    old = read(ROOT / 'visual_query_engine119/completion.json')
    if (old['state'] != 'FIRST2_REAL_VISUAL_QUERY_ENGINEERING_CPU_PASS_NOT_QUALITY'
            or not old['complete_remaining_fit_cost_admitted']
            or old['all_goal_GPU_seconds'] != protocol['Goal_GPU_seconds_before']
            or old['remaining_original_profile_seconds'] != protocol['remaining_GPU_seconds_max_all_failures']
            or protocol['Goal_GPU_seconds_before'] + protocol['remaining_GPU_seconds_max_all_failures'] > 43200):
        raise ValueError('Exact first119 completion/CPU/cost or unchanged remaining1800/Goal budget differs')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Host or CONTROL5 differs; never signal it')
    for key in ['protected_original', 'protected_best']:
        check(read(CODE / 'parallel_protocol105.json')[key])
    inputs = read(ROOT / 'visual_query_inputs119/completion.json')
    prior = read(ROOT / 'visual_query_engine119/GPU_completion.json')
    actual_capacity = capacity(inputs, prior)
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU work conflicts with existing unique shared wrapper')
    names = ['visual_query120.py', 'visual_query120_gpu.py', 'visual_query120_cpu.py',
        'visual_query_review120.py', 'visual_query_metrics120.py', 'visual_query_fit120.json',
        'visual_query_prefix119.py', 'visual_query_runtime119.py', 'visual_query119_cpu.py',
        'visual_query_protocol119.json', 'shared_visual_query118.py', 'shared_visual_query118_cpu.py',
        'parallel_discrimination116.py', 'parallel_train108.py', 't_runtime39.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'visual_query_fit120.json'),
        original119_protocol=identity(CODE / 'visual_query_protocol119.json'),
        code={name: identity(CODE / name) for name in names},
        actual_inputs=identity(ROOT / 'visual_query_inputs119/completion.json'),
        actual_first2_model=identity(ROOT / 'visual_query_engine119/GPU_completion.json'),
        actual_first2_CPU=identity(ROOT / 'visual_query_engine119/CPU_completion.json'),
        capacity=actual_capacity, actual_GPU_apps=apps,
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'],
                                    text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        actual_disk=subprocess.check_output(['df', '-B1', str(ROOT), str(TEMP.parent)], text=True)))
    return protocol, actual_capacity


def run(script, phase, protocol, actual_capacity, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds',
            str(protocol['remaining_GPU_seconds_max_all_failures']), '--planned-output-bytes',
            str(actual_capacity['root_artifact_upper_bytes']), '--capacity-reason',
            'Exact remaining23 original shared-visual fit contexts, first2/input/CPU adopted. Original1800 remaining1670 unchanged; root/tmpfs full actual-witness costs measured from119 and checked. No training or production.',
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
        raise RuntimeError('First remaining visual-query phase failed; preserve success: ' + phase)


def main():
    OUT.mkdir(); protocol, actual_capacity = admission()
    run('visual_query120_gpu.py', 'GPU', protocol, actual_capacity, gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [resource]:
        raise ValueError('Actual remaining23 natural terminal/unique ledger differs')
    run('visual_query120_cpu.py', 'first_complete_CPU', protocol, actual_capacity)
    cpu = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=cpu['state'], first_CPU=identity(OUT / 'CPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=protocol['Goal_GPU_seconds_before'] + resource['charged_seconds'],
        profile119_GPU_seconds=protocol['prior_profile_GPU_seconds'] + resource['charged_seconds'],
        actual_first_new_physical_model_forwards=46, all_native_windows=25,
        prospective_training_information_signal=cpu['prospective_training_information_signal'],
        no_automatic_training_confirmation_or_production=True, new_T_ZIPs=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_successful_inputs_outputs_and_fees=True, no_automatic_retry=True))
        raise
