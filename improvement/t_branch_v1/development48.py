"""Fixed development controls, shared BASE and exact VERIFY, aggregate GPU<=2400s."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'development48'
CODE = Path(__file__).parent
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
NAMES = ['development48.py', 'development_prepare48.py', 'development_semantic46.py', 'development_coarse48.py',
    'development_verify_prepare48.py', 'development_verify48.py', 'development_review48.py',
    'development_data46.py', 'development_call46.py', 'development_verify46.py', 'frozen_branch46.py',
    'joint_rollout44.py', 'joint_checkpoint44.py', 'joint_data44.py', 'joint_audit45.py',
    'reference_gpu19.py', 'reference_data18.py', 'coarse_call25.py', 't_runtime39.py', 'prompt_contract13.py',
    'native_sets.py', 'preference_reward.py', 't_io.py']


def execute(script, job=None, seconds=None):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if job:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute exists; preserve accepted stage instead of launch')
        save(OUT / (job + '_resource_admission.json'), dict(apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'], text=True), RAM=subprocess.check_output(['free', '-b'], text=True),
            disk=subprocess.check_output(['df', '-B1', str(ROOT)], text=True),
            basis='Two frozenTIME roles share8B, actual8.798B and prior24.95GB training peak; this stage inference only, native image chunks<=8; no new model download'))
        command = [str(PY), '-B', str(WRAPPER), '--name', job, '--max-seconds', str(seconds),
            '--planned-output-bytes', '100000000', '--capacity-reason',
            'Fixed2publisher dev; first150greedy, shared exactBASE or unique exactVERIFY; all real CPU inputs accepted, remaining aggregate2400s budget',
            '--queue-seconds', '0', '--'] + command
    name = Path(script).stem
    with (OUT / (name + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if job else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual development stage failed: ' + name)
    if not job:
        return 0.
    record = read(RUN / 'controller' / (job + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [r for r in ledger if r.get('name') == job] != [record]:
        raise ValueError('Actual unique natural development terminal differs')
    return record['charged_seconds']


def main():
    OUT.mkdir()
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Actual host differs')
    training = read(ROOT / 'joint_remaining47/completion.json')
    if training['state'] != 'JOINT4_TRAINING_ENGINEERING_COMPLETE':
        raise ValueError('Fixed train mechanism/independent CPU gates not passed')
    check(training['CPU_audit']); check(training['final_adapter']['weights'])
    protocol = identity(CODE / 'joint_policy_protocol44.json')
    if protocol['sha256'] != 'd9f01805183ab0a40028f0cc173053f6470083659cf0e17c14f848bfc7e849c7':
        raise ValueError('Original frozen scientific protocol changed')
    dependency = WORK / 'general_highlight_supervision_20261021_v1/code'
    external = [dependency / name for name in ('baseline_semantic57_prepare.py', 'baseline_bridge57_gpu.py', 'baseline_bridge57_common.py')]
    external += [WORK / 'semantic_context_production_20261016_v1/code' / name for name in
        ('production_semantic10.py', 'semantic09.py', 'semantic_oof09.py', 'monotone_head06.py')]
    external += [WORK / 'twenty_hour_five_20261014_v1/candidate_verify_v2/code' / name for name in ('cv_contract.py', 'cv_grammar.py')]
    external += [WORK / 'twenty_hour_five_20261014_v1/temporal_production_inputs_v4/code/tp_contract.py',
        RUN / 'b_score_aligned_package_v4/source_color.py', WRAPPER]
    save(OUT / 'registration.json', dict(protocol=protocol, final_frozen_training=identity(ROOT / 'joint_remaining47/completion.json'),
        arms=['original_correct', 'trained_correct', 'original_shift', 'trained_shift'],
        coarse_inputs='Original50 native64 cached; shift only measured32temporal groups by16, same prefix',
        downstream='All four arms use same original native content in unchanged originalTIME VERIFY and BASE semantic; test coarse content mechanism only',
        exact_DUPLICATE_VERIFY_tasks='Adopt identical task/input only; no repeated successful model',
        native_D8='Original endpoints .75before/.5after plus.25after when original>=8, clipped originalwindow',
        native_guard='VERIFY whole-source empty restores D8, same original40.47',
        semantic='Exact halfsecond occupied native midpoint images, original 8-frame chunks/targettext/BASE; frozenLMhead occupancy recomputed for each arm',
        new_training=0, whole_dev_sources=2, first_greedy_calls=150, original_greedy_calls_adopted=50,
        no_new_confirmation_quality_exposure=True, GPU_total_limit=2400,
        actual_T1_charged_before_dev=training['cumulative_T1_seconds'], no_threshold_prompt_dose_sweep=True))
    if training['cumulative_T1_seconds'] + 2400 > 10800:
        raise ValueError('No aggregate T1 budget for frozen development')
    if shutil.disk_usage(ROOT).free < 3000000000:
        raise RuntimeError('Actual remaining disk cannot hold estimated first semantic inputs3GB')
    lock = dict(protocol=protocol, code={name: identity(CODE / name) for name in NAMES},
        original_dependencies={str(path): identity(path) for path in external}, registration=identity(OUT / 'registration.json'))
    save(OUT / 'source_input_lock.json', lock)
    execute('development_prepare48.py')
    execute('development_semantic46.py')
    first = execute('development_coarse48.py', 'T_joint4_dev_greedy_BASE_20261022_v48', 2400)
    execute('development_verify_prepare48.py')
    remaining = int(2400 - first)
    if remaining <= 0:
        raise RuntimeError('Aggregate frozen development GPU budget exhausted before VERIFY')
    save(OUT / 'verify_source_input_lock.json', dict(**lock,
        actual_coarse_and_BASE=identity(OUT / 'coarse_and_BASE_GPU_completion.json'),
        first_all_VERIFY_inputs=identity(OUT / 'verify_CPU_completion.json'),
        previous_GPU_seconds=first, remaining_GPU_seconds=remaining))
    second = execute('development_verify48.py', 'T_joint4_dev_exact_VERIFY_20261022_v48', remaining)
    execute('development_review48.py')
    save(OUT / 'completion.json', dict(state=read(OUT / 'review.json')['state'], review=identity(OUT / 'review.json'),
        independent_CPU=identity(OUT / 'independent_CPU_audit.json'), actual_GPU_seconds=first + second,
        T1_cumulative_GPU_seconds=training['cumulative_T1_seconds'] + first + second,
        new_packages=0, next='Only frozen single four-publisher confirmation if actual development gates PASS'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_actual_successes=True, no_automatic_retry=True))
        raise
