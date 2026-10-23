"""One complete matched/misaligned/no-memory native selector after event gates."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from event_select72_common import CPU, OUT
from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_native_event_memory_three_conditions150_20261022_v72'
NAMES = ['event_native71.py', 'event_table71.py', 'event_prepare71.py', 'event_select72_common.py',
         'event_select72_gpu.py', 'event_select72_cpu.py', 'event_chain72.py']


def run(script, phase):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if phase == 'GPU':
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '2700',
            '--planned-output-bytes', '30000000', '--capacity-reason',
            'Adopt original50 native visual inputs and50 verified event records; only100 new small text prefixes and150 projected raw outputs/CPU proofs; no new RGB or model',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if phase == 'GPU' else '',
                OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First event selector stage failed; preserve all successes: ' + phase)


def main():
    OUT.mkdir()
    protocol = read(CODE / 'event_memory_protocol69.json')
    event = read(ROOT / 'event_adoption73/completion.json')
    if event['state'] != 'ADOPTED_ALL50_EVENT_OUTPUTS_AFTER_FLAG_ONLY_FINAL_CHECK_FAILURE':
        raise ValueError('First complete neutral event memory/CPU gate absent')
    if event['GPU_seconds'] + 2700 + 1800 > protocol['development_total_GPU_seconds_max']:
        raise ValueError('Fixed total development cost cannot fund complete control matrix')
    if event['all_goal_GPU_seconds'] + 2700 > protocol['Goal_all_GPU_seconds_max']:
        raise ValueError('Original all-Goal GPU ceiling reached')
    for key in ['protected_best', 'protected_original']:
        check({k: protocol[key][k] for k in ['path', 'bytes', 'sha256']})
    if shutil.disk_usage(ROOT).free < 30000000:
        raise RuntimeError('Actual proposed150 outputs and CPU proofs exceed current disk')
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'event_memory_protocol69.json'),
        completed_event_gate=identity(ROOT / 'event_adoption73/completion.json'),
        exact_three_conditions=protocol['prospective_selector_matrix'], first_new_generations_max=150,
        GPU_seconds_max=2700, all_remaining_profile_cost_fits=True,
        no_labels_in_inference_or_confirmation_read=True, new_training=0,
        actual_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:10],
        actual_RAM=subprocess.check_output(['free', '-b'], text=True),
        actual_GPU=subprocess.check_output(['nvidia-smi'], text=True),
        actual_disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    run('event_prepare71.py', 'input_CPU')
    cpu = read(CPU / 'completion.json')
    if cpu['state'] != 'FIRST_ALL150_NATIVE_MEMORY_SELECTOR_INPUTS_PASS':
        raise ValueError('First complete source-memory and native action CPU contract failed')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External compute appeared; keep all accepted inputs and wait for explicit remaining recovery')
    code = {name: identity(CODE / name) for name in NAMES}
    for name in ['event_memory69_common.py', 't_io.py', 't_runtime39.py', 'coarse_call25.py',
                 'development_data46.py', 'causal_policy32.py', 'frozen_branch46.py', 'event_adoption73.py']:
        code[name] = identity(CODE / name)
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'event_memory_protocol69.json'),
        complete_actual_CPU=identity(CPU / 'completion.json'), code=code,
        native_grammar=cpu['native_grammar_contract']['code'], wrapper=identity(WRAPPER),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        no_old_model_replayed=True, actual_apps_at_admission=apps))
    run('event_select72_gpu.py', 'GPU')
    record = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [record]:
        raise ValueError('Unique native selector natural GPU terminal/ledger differs')
    run('event_select72_cpu.py', 'output_CPU')
    review = read(OUT / 'CPU_completion.json')
    save(OUT / 'completion.json', dict(state=review['state'], actual_new_generations=150,
        first_native_output_QA=identity(OUT / 'CPU_completion.json'),
        GPU_seconds=record['charged_seconds'], all_goal_GPU_seconds=event['all_goal_GPU_seconds'] + record['charged_seconds'],
        total_profile_GPU_seconds=event['GPU_seconds'] + record['charged_seconds'],
        no_new_training_or_package=True, protected40_47_and40_48_unchanged=True,
        no_automatic_confirmation_or_production=True,
        next='Continue first exact downstream VERIFY/current40.48 route review within remaining registered1800GPU seconds; coarse diagnostics alone do not qualify candidate'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_and_raw=True))
        raise
