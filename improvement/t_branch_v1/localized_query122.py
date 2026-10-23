"""Single bounded actual8B local-attention pilot, then all first independent QA."""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from official_freshness122 import review
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'localized_query122'
CODE = Path(__file__).parent
TEMP = Path('/dev/shm/aic_T_localized_query122')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_fixed_local_native_visibility25_original8B_20261023_v122'


def capacity(inputs):
    first = inputs['first_engineering_cases']
    retired = read(ROOT / 'visual_query_engine119/first_activation_retirement.json')['only_new_full_activations_retired']
    sizes = {name: sum(ref['bytes'] for ref in retired if Path(ref['path']).name.startswith(name + '_'))
             for name in first}
    rows = [read(check(inputs['inputs'][name])) for name in first]
    prior = read(ROOT / 'visual_query_engine119/GPU_completion.json')
    permanent = max(read(check(prior['outputs'][name]['witnesses']))['permanent']['bytes'] for name in first)
    temporary = 0
    for ref in inputs['inputs'].values():
        row = read(check(ref))
        if row['video_grid_thw'] != rows[0]['video_grid_thw']:
            raise ValueError('New pilot visual geometry differs from real measured profile')
        temporary += math.ceil(max(sizes.values()) * max(1., row['input_tokens'] /
            min(item['input_tokens'] for item in rows))) + 1048576
    root = 25 * (permanent + 65536) + 2097152
    if (len(inputs['inputs']) != 25 or not all(sizes.values()) or TEMP.exists()
            or root > shutil.disk_usage(ROOT).free or temporary > shutil.disk_usage(TEMP.parent).free):
        raise RuntimeError('Actual measured new25 proof costs conflict with current shared capacity')
    return dict(root_artifact_upper_bytes=root, temporary_activation_upper_bytes=temporary,
        actual_root_free=shutil.disk_usage(ROOT).free, actual_tmpfs_free=shutil.disk_usage(TEMP.parent).free,
        first119_measured_temporary_bytes=sizes, all25_windows_accounted=True)


def admission():
    protocol = read(CODE / 'localized_query_protocol122.json')
    old = read(ROOT / 'visual_query_fit120/completion.json')
    accepted = read(ROOT / 'localized_visual121_CPU/completion.json')
    if (old['state'] != 'FIRST_COMPLETE25_SHARED_VISUAL_FIT_DIAGNOSIS_AND_ALL_CPU_PASS'
            or accepted['state'] != 'FIRST_LOCAL_NATIVE_VISIBILITY_CPU_MODEL_GRADIENT_AND25_MASKS_PASS'
            or old['all_goal_GPU_seconds'] != protocol['Goal_GPU_seconds_before']
            or protocol['Goal_GPU_seconds_before'] + protocol['new_GPU_seconds_max_all_failures'] > 43200):
        raise ValueError('Prior natural results/current mask CPU/Goal budget identity differs')
    if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['deadline']):
        raise RuntimeError('Original competition cutoff reached; no new pilot admission')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Host or permanently stopped CONTROL5 differs; never signal it')
    for key in ['protected_original', 'protected_best']:
        check(read(CODE / 'parallel_protocol105.json')[key])
    inputs = read(ROOT / 'visual_query_inputs119/completion.json')
    if set(inputs['inputs']) != set(accepted['masks']):
        raise ValueError('Frozen all25 mask/input scope differs')
    for name, ref in inputs['inputs'].items():
        if accepted['masks'][name]['original_input'] != ref:
            raise ValueError('Frozen mask prefix provenance differs')
        check(accepted['masks'][name]['mask'])
    actual_capacity = capacity(inputs)
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('Current GPU job conflicts with this measured21GB single-GPU pilot')
    rules = review()
    names = ['localized_query122.py', 'localized_query122_gpu.py', 'localized_query122_cpu.py',
        'localized_query_review122.py', 'localized_query_metrics122.py', 'localized_query_protocol122.json',
        'official_freshness122.py', 'localized_visual121.py', 'localized_visual121_cpu.py',
        'visual_query_prefix119.py', 'visual_query_runtime119.py', 'visual_query119_cpu.py',
        'visual_query_metrics120.py', 'shared_visual_query118.py', 'shared_visual_query118_cpu.py',
        'parallel_discrimination116.py', 'parallel_train108.py', 'native_prepared103.py',
        'native_render100.py', 't_runtime39.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'localized_query_protocol122.json'),
        code={name: identity(CODE / name) for name in names},
        actual_inputs=identity(ROOT / 'visual_query_inputs119/completion.json'),
        accepted_masks=identity(ROOT / 'localized_visual121_CPU/completion.json'),
        unmasked_control=identity(ROOT / 'visual_query_fit120/completion.json'),
        current_official_rules=rules, capacity=actual_capacity, actual_GPU_apps=apps,
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,stat,pcpu,pmem,args', '--sort=-pcpu'],
                                    text=True).splitlines()[:12], RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), str(TEMP.parent)], text=True)))
    return protocol, actual_capacity


def run(script, phase, protocol, actual_capacity, gpu=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if gpu:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds',
            str(protocol['new_GPU_seconds_max_all_failures']), '--planned-output-bytes',
            str(actual_capacity['root_artifact_upper_bytes']), '--capacity-reason',
            'First fixed masked-attention25 pilot; old25 control/input/121masks adopted. New real native decisions and full activation proofs measured from119; no training/confirmation/production.',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if gpu else '', OMP_NUM_THREADS='2',
                     MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First fixed local-query phase failed; preserve accepted outputs: ' + phase)


def main():
    OUT.mkdir(); protocol, actual_capacity = admission()
    run('localized_query122_gpu.py', 'GPU', protocol, actual_capacity, gpu=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [resource]:
        raise ValueError('Natural new masked8B terminal and unique ledger disagree')
    run('localized_query122_cpu.py', 'first_complete_CPU', protocol, actual_capacity)
    cpu = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=cpu['state'], first_CPU=identity(OUT / 'CPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=protocol['Goal_GPU_seconds_before'] + resource['charged_seconds'],
        actual_new_logical_windows=25, actual_new_physical_model_forwards=50, actual_new_native_decisions=800,
        local_information_gate_pass=cpu['local_information_gate_pass'],
        no_automatic_training_confirmation_or_production=True, new_T_ZIPs=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            resource = RUN / 'controller' / (JOB + '.resource.json')
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                resource=read(resource) if resource.exists() else None,
                preserve_all_successes_and_fees=True, no_automatic_retry=True))
        raise
