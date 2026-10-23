"""Same fixed dev experiment, explicitly bound to engineering final-source50."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

import development48 as previous
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'development51'
CODE = Path(__file__).parent
TRAINING = ROOT / 'joint_continue50/completion.json'


def execute(stage, job=None, seconds=None):
    if stage == 'semantic':
        command = [str(previous.PY), '-B', '-u', str(CODE / 'development_semantic46.py')]
    else:
        command = [str(previous.PY), '-B', '-u', str(CODE / 'development_run51.py'), stage]
    if job:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute live; preserve CPU work and do not launch')
        save(OUT / (stage + '_resource_admission.json'), dict(apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'], text=True), RAM=subprocess.check_output(['free', '-b'], text=True),
            disk=subprocess.check_output(['df', '-B1', str(ROOT)], text=True),
            basis='Actual8.798B shared twoTIME/head, inference-only, prior measured27.5GB; all first actual inputs accepted, no fixed resource thresholds'))
        command = [str(previous.PY), '-B', str(previous.WRAPPER), '--name', job,
            '--max-seconds', str(seconds), '--planned-output-bytes', '100000000',
            '--capacity-reason', 'Same frozen44 development: first150greedy/shared BASE or deduplicated originalVERIFY; 50 controls adopted, remaining aggregate2400s, no training',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (stage + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if job else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (stage + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (stage + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual explicit51 development stage failed: ' + stage)
    if not job:
        return 0.
    resource = read(previous.RUN / 'controller' / (job + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == job] != [resource]:
        raise ValueError('Actual unique development natural resource/ledger differs')
    return resource['charged_seconds']


def source_lock(protocol):
    names = previous.NAMES + ['development51.py', 'development_run51.py', 'development_follow51.py']
    dependency = WORK / 'general_highlight_supervision_20261021_v1/code'
    external = [dependency / name for name in ('baseline_semantic57_prepare.py', 'baseline_bridge57_gpu.py', 'baseline_bridge57_common.py')]
    external += [WORK / 'semantic_context_production_20261016_v1/code' / name for name in
        ('production_semantic10.py', 'semantic09.py', 'semantic_oof09.py', 'monotone_head06.py')]
    external += [WORK / 'twenty_hour_five_20261014_v1/candidate_verify_v2/code' / name for name in ('cv_contract.py', 'cv_grammar.py')]
    external += [WORK / 'twenty_hour_five_20261014_v1/temporal_production_inputs_v4/code/tp_contract.py',
        previous.RUN / 'b_score_aligned_package_v4/source_color.py', previous.WRAPPER]
    return dict(protocol=protocol, code={name: identity(CODE / name) for name in names},
        original_dependencies={str(path): identity(path) for path in external},
        registration=identity(OUT / 'registration.json'), explicit_training_terminal=identity(TRAINING))


def main():
    OUT.mkdir()
    training = read(TRAINING)
    if training['state'] != 'JOINT4_TRAINING_ENGINEERING_COMPLETE':
        raise ValueError('Actual four-source-episode mechanism and CPU gates not passed')
    check(training['CPU_audit']); check(training['final_adapter']['weights'])
    protocol = identity(CODE / 'joint_policy_protocol44.json')
    if protocol['sha256'] != 'd9f01805183ab0a40028f0cc173053f6470083659cf0e17c14f848bfc7e849c7':
        raise ValueError('Original fixed scientific protocol changed')
    if training['cumulative_T1_seconds'] + 2400 > 10800:
        raise ValueError('Original cumulative T1 budget does not fund this fixed development')
    if shutil.disk_usage(ROOT).free < 3000000000:
        raise RuntimeError('Actual disk cannot hold estimated first3GB semantic inputs')
    if read(ROOT / 'development_wait48/completion.json')['state'] != 'DEPENDENCY_FAILED_NO_DEV_STARTED':
        raise ValueError('Old48 execution not proved stopped before all dev work')
    if read(ROOT / 'development_contract49/completion.json')['state'] != 'PASS_NEW_DEV_IMPORT_SHIFT_AND_NATIVE_REQUEST_INTERFACES':
        raise ValueError('New metadata/shift/VERIFY software interfaces not accepted')
    save(OUT / 'registration.json', dict(protocol=protocol, training=identity(TRAINING),
        execution_path_change_only='Explicit50 final checkpoint instead of failed47; fixed48 scientific functions/gates reused',
        arms=['original_correct', 'trained_correct', 'original_shift', 'trained_shift'],
        downstream='Same correct native content for unchanged originalTIME VERIFY and BASE semantic across all4 coarse conditions',
        old48_new_model_calls=0, first_new_greedy=150, adopted_original_greedy=50,
        unique_VERIFY_tasks_only=True, occupancy_recomputed_for_each_arm=True,
        GPU_aggregate_limit=2400, previous_T1_seconds=training['cumulative_T1_seconds'],
        no_new_training_confirmation_or_production=True, protected40_47_unchanged=True))
    lock = source_lock(protocol); save(OUT / 'source_input_lock.json', lock)
    execute('prepare')
    semantic = ROOT / 'development_semantic46/completion.json'
    if semantic.exists():
        for ref in read(semantic)['sources']:
            check(ref)
        save(OUT / 'semantic_CPU_adoption.json', dict(prior=identity(semantic), no_successful_input_repeated=True))
    else:
        execute('semantic')
    first = execute('coarse', 'T_joint4_dev_greedy_BASE_20261022_v51', 2400)
    execute('verify_prepare')
    remaining = int(2400 - first)
    if remaining <= 0:
        raise RuntimeError('Frozen aggregate development budget exhausted before VERIFY')
    save(OUT / 'verify_source_input_lock.json', dict(**lock,
        actual_coarse_and_BASE=identity(OUT / 'coarse_and_BASE_GPU_completion.json'),
        first_all_VERIFY_inputs=identity(OUT / 'verify_CPU_completion.json'),
        previous_GPU_seconds=first, remaining_GPU_seconds=remaining))
    second = execute('verify', 'T_joint4_dev_exact_VERIFY_20261022_v51', remaining)
    execute('review')
    save(OUT / 'completion.json', dict(state=read(OUT / 'review.json')['state'],
        review=identity(OUT / 'review.json'), independent_CPU=identity(OUT / 'independent_CPU_audit.json'),
        actual_GPU_seconds=first + second, T1_cumulative_GPU_seconds=training['cumulative_T1_seconds'] + first + second,
        new_packages=0, next='Only first fixed4publisher confirmation if frozen development PASS'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
