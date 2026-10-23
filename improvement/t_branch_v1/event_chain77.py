"""First remaining actual-best route, charged inside fixed downstream budget."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from event_route77_common import OUT, GENERAL, source_inputs, old_model_registration
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_first_exact40_48_route_missing_news277_20261022_v77'
FILES = ['event_route77_common.py', 'event_route77_gpu.py', 'event_route77_cpu.py', 'event_chain77.py']


def run(script, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '150',
            '--planned-output-bytes', '10000000', '--capacity-reason',
            'One first277-cell backbone only; Nobel294 features adopted, first two fixed head projections and any original expert branch; existing333MB tmpfs RGB adopted; no8B/model download',
            '--queue-seconds', '0', '--'] + command
    phase = 'GPU' if GPU else 'CPU'
    with (OUT / (phase + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '', OMP_NUM_THREADS='2',
                     MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First actual-best source route failed: ' + phase)


def main():
    OUT.mkdir()
    previous = read(ROOT / 'event_selection72/completion.json')
    if previous['state'] != 'PASS_FIRST_ALL150_NATIVE_MEMORY_OUTPUTS_NOT_FULL40_48_QUALITY':
        raise ValueError('All150 first native selector outputs must pass before downstream admission')
    if previous['all_goal_GPU_seconds'] + 1800 > 43200:
        raise ValueError('Actual remaining Goal budget cannot fund fixed downstream')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip() or shutil.disk_usage(ROOT).free < 10000000:
        raise RuntimeError('External compute conflict or insufficient specific output capacity')
    old = old_model_registration()
    check(old['expert_checkpoint']); check(old['class_names'])
    for source in source_inputs().values():
        check(source['input'])
        if source['existing_feature'] is not None:
            check(source['existing_feature'])
    protocol = read(CODE / 'event_memory_protocol69.json')
    for key in ['protected_best', 'protected_original']:
        check({k: protocol[key][k] for k in ['path', 'bytes', 'sha256']})
    dependencies = read(GENERAL / 'routing_production62/source_input_lock.json')['dependencies']
    for ref in dependencies.values():
        check(ref)
    save(OUT / 'registration.json', dict(fixed_protocol=identity(CODE / 'event_memory_protocol69.json'),
        previous_complete=identity(ROOT / 'event_selection72/completion.json'),
        first_all_route_CPU=identity(ROOT / 'event_route_inputs75/completion.json'),
        old_expert=old['expert_checkpoint'], old_class_names=old['class_names'],
        new_backbone_cells=277, old294_backbone_cells_adopted=True,
        first_GPU_seconds_max=150, remaining_profile_downstream_seconds=1800,
        actual_apps=apps, actual_resources=subprocess.check_output(['nvidia-smi'], text=True),
        actual_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:9],
        actual_RAM=subprocess.check_output(['free', '-b'], text=True),
        actual_disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    save(OUT / 'source_input_lock.json', dict(registration=identity(OUT / 'registration.json'),
        old_successful_models_not_repeated=True,
        code={n: identity(CODE / n) for n in FILES + ['t_io.py']}, dependencies=dependencies,
        all_actual_source_inputs=source_inputs(), wrapper=identity(WRAPPER)))
    run('event_route77_gpu.py', True)
    record = read(RUN / 'controller' / (JOB + '.resource.json'))
    rows = [json.loads(l) for l in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if l.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [v for v in rows if v.get('name') == JOB] != [record]:
        raise ValueError('Unique natural exact-best route resource/ledger differs')
    run('event_route77_cpu.py')
    save(OUT / 'completion.json', dict(state='PASS_FIRST_CURRENT40_48_ROUTE_BOTH_EXTERNAL_SOURCES',
        source_routes=identity(OUT / 'CPU_completion.json'), GPU_seconds=record['charged_seconds'],
        all_goal_GPU_seconds=previous['all_goal_GPU_seconds'] + record['charged_seconds'],
        remaining_fixed_downstream_GPU_seconds=1800 - record['charged_seconds'],
        new8B_calls=0, new_training=0, no_new_candidate_or_confirmation_admission=True,
        next='First missing VERIFY only, first new output QA and original semantic occupancy followed by these exact fixed keep masks; evaluate full source40.48 comparison.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
