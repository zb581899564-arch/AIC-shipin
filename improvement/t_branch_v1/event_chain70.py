"""One explicit first-input and first-event chain; no automatic source selector."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from event_memory69_common import CAPTION, INPUT
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'event_chain70'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_native_local_AV_event_memory50_20261022_v70'
NAMES = ['event_memory_protocol69.json', 'event_memory69_common.py', 'event_audio69.py',
    'event_inputs69.py', 'event_caption70_gpu.py', 'event_caption70_cpu.py', 'event_chain70.py']
ADOPTED_CODE = ['t_io.py', 'description_audio65.py', 'description_wave65.py', 'speech_scope58.py',
    'speech_decode58.py', 'speech_native58.py', 'coarse_call25.py', 'development_data46.py',
    'joint_data44.py', 'native_sets.py', 't_runtime39.py', 'prompt_contract13.py', 'frozen_branch46.py']


def run(script, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '1800',
            '--planned-output-bytes', '15000000', '--capacity-reason',
            'All original video inputs adopted; at most50 short event records/raw projections/CPU proofs on SSD, one predeclared128-token activation in tmpfs at a time',
            '--queue-seconds', '0', '--'] + command
    name = 'event_GPU' if GPU else 'input_CPU'
    with (OUT / (name + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '',
                OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First event stage failed; preserve successes: ' + name)


def main():
    OUT.mkdir()
    p = read(CODE / 'event_memory_protocol69.json')
    prior = read(ROOT / 'description_score67/completion.json')
    if prior['state'] != 'COMPLETE_HUMAN_CONTENT_MODALITY_ROLE_DIAGNOSTIC_NOT_CANDIDATE_QUALITY':
        raise ValueError('Original content observability diagnosis incomplete')
    if prior['all_goal_GPU_seconds'] + p['development_total_GPU_seconds_max'] > p['Goal_all_GPU_seconds_max']:
        raise ValueError('Remaining aggregate budget cannot fund fixed new development profile')
    for name in ['protected_best', 'protected_original']:
        ref = {k: p[name][k] for k in ['path', 'bytes', 'sha256']}; check(ref)
    if shutil.disk_usage(ROOT).free < 15000000 or shutil.disk_usage('/dev/shm').free < 50 * 30 * 16000 * 4 + 128 * 200000 * 8:
        raise RuntimeError('Specific new audio/raw/proof estimates exceed actual capacity')
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'event_memory_protocol69.json'),
        original_and_new_preparation_code={name: identity(CODE / name) for name in NAMES + ADOPTED_CODE},
        evidence=identity(ROOT / 'description_score67/completion.json'), exact_new_first_inputs=50,
        first_new_event_generations_max=50, GPU_seconds_max=1800,
        new_training=0, no_automatic_selector_confirmation_or_production=True,
        source_scope='Only two fixed development publishers, all50 windows, no human labels in inputs',
        actual_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:10],
        actual_RAM=subprocess.check_output(['free', '-b'], text=True),
        actual_GPU=subprocess.check_output(['nvidia-smi'], text=True),
        actual_disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    run('event_inputs69.py')
    cpu = read(INPUT / 'completion.json')
    if cpu['state'] != 'FIRST_ALL50_LOCAL_EVENT_AV_INPUTS_PASS':
        raise ValueError('All actual first event inputs must pass before GPU')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External compute appeared; keep all accepted inputs and do not launch GPU')
    CAPTION.mkdir()
    dependencies = read(ROOT / 'development51/source_input_lock.json')['original_dependencies']
    for ref in dependencies.values():
        check(ref)
    save(CAPTION / 'source_input_lock.json', dict(protocol=identity(CODE / 'event_memory_protocol69.json'),
        first_complete_CPU=identity(INPUT / 'completion.json'), registration=identity(OUT / 'registration.json'),
        code={name: identity(CODE / name) for name in NAMES + ADOPTED_CODE}, wrapper=identity(WRAPPER),
        original_dependencies=dependencies, actual_apps_at_admission=apps))
    run('event_caption70_gpu.py', True)
    record = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [v for v in ledger if v.get('name') == JOB] != [record]:
        raise ValueError('Unique natural event-generation resource ledger differs')
    result = read(CAPTION / 'GPU_completion.json')
    if result['actual_new_generations'] != 50 or len(list((CAPTION / 'raw').glob('*.CPU.json'))) != 50:
        raise ValueError('First complete event generation/CPU denominator differs')
    save(OUT / 'completion.json', dict(state='FIRST50_EVENT_MEMORY_GENERATIONS_AND_CPU_COMPLETE_NOT_SELECTION_QUALITY',
        inputs=identity(INPUT / 'completion.json'), events=identity(CAPTION / 'GPU_completion.json'),
        actual_first_generations=50, first_independent_CPU_proofs=50,
        GPU_seconds=record['charged_seconds'], all_goal_GPU_seconds=prior['all_goal_GPU_seconds'] + record['charged_seconds'],
        new_training=0, new_packages=0, original40_47_and40_48_unchanged=True,
        no_automatic_selector_confirmation_or_production=True,
        next='Bind all native event memory and fixed half-source text shift, measure cost, then separately admit registered common-native three-condition source selection; never infer highlight quality from event descriptions'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_and_raw=True))
        raise
