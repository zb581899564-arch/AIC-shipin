"""One original-weight modality/role diagnostic after all real CPU inputs pass."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, identity, read, save

OUT = ROOT / 'description_score67'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_human_content_modal_role_probe_20261022_v67'


def execute(script, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '1500',
            '--planned-output-bytes', '10000000', '--capacity-reason',
            'Only10MB durable SSD projected raw/proofs; one full-vocabulary temporary activation in preadmitted tmpfs, independently CPU-checked before registered retirement; no training or new model',
            '--queue-seconds', '0', '--'] + command
    name = 'GPU' if GPU else 'review'
    with (OUT / (name + '.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
                PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First registered content diagnostic stage failed: ' + name)


def main():
    OUT.mkdir()
    cpu = read(ROOT / 'description_probe66/CPU_completion.json')
    if cpu['state'] != 'FIRST_ALL_PAIRED_MODALITY_ROLE_PROBE_INPUTS_PASS' or cpu['maximum_first_TF_calls'] > 192:
        raise ValueError('All actual paired CPU inputs must pass first')
    if 7998.7994901333 + 1500 > 43200:
        raise ValueError('Original cumulative Goal GPU ceiling cannot fund this diagnostic')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU compute exists; preserve all accepted inputs')
    max_activation = int(cpu['maximum_caption_tokens']) * 200000 * 4
    if shutil.disk_usage('/dev/shm').free < 2 * max_activation or shutil.disk_usage(ROOT).free < 10000000:
        raise RuntimeError('Actual projected/raw activation capacity insufficient')
    names = ['description_score67.py', 'description_score67_gpu.py', 'description_score67_cpu.py',
        'description_score67_review.py', 'description_probe66.py', 'description_tokens64.py',
        'frozen_branch46.py', 'joint_replay44.py', 'causal_policy32.py', 't_runtime39.py']
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'description_protocol67.json'),
        complete_actual_CPU=identity(ROOT / 'description_probe66/CPU_completion.json'),
        first_causal_TF_calls_max=cpu['maximum_first_TF_calls'], GPU_seconds_max=1500,
        existing_Goal_GPU_seconds=7998.7994901333, Goal_total_GPU_ceiling=43200,
        no_new_parameters_generation_training_or_quality_claim=True, fresh_confirmation_read=False,
        raw_retention='Permanent per-token target logits/log-normalizers/log-probabilities plus first independent full-vocabulary CPU proofs; full logits are temporary evaluator activations, retired only after that proof',
        temporary_activation_root='/dev/shm/aic_T_description_score67', max_single_activation_bytes=max_activation,
        actual_GPU=subprocess.check_output(['nvidia-smi'], text=True), actual_apps=apps,
        RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    save(OUT / 'source_input_lock.json', dict(registration=identity(OUT / 'registration.json'),
        all_actual_CPU_inputs=identity(ROOT / 'description_probe66/CPU_completion.json'),
        code={name: identity(CODE / name) for name in names}, wrapper=identity(WRAPPER),
        original_dependencies=read(ROOT / 'development51/source_input_lock.json')['original_dependencies']))
    execute('description_score67_gpu.py', True)
    record = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [record]:
        raise ValueError('Unique natural diagnostic GPU resource/ledger differs')
    execute('description_score67_review.py')
    save(OUT / 'completion.json', dict(state=read(OUT / 'review.json')['state'],
        review=identity(OUT / 'review.json'), actual_first_causal_TF_calls=cpu['maximum_first_TF_calls'],
        GPU_seconds=record['charged_seconds'], all_goal_GPU_seconds=7998.7994901333 + record['charged_seconds'],
        new_training=0, new_packages=0, original40_47_unchanged=True,
        no_automatic_optimization_confirmation_or_production=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
