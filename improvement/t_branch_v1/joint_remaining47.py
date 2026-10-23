"""One explicit remainder, preserving failed44 and passed CPU/identity artifacts."""
import json
from pathlib import Path
import traceback

import joint_controller44 as original
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'joint_remaining47'
JOB = 'T_joint_source_counterfactual_remaining_20261022_v47'


def main():
    OUT.mkdir()
    resource = read(original.RUN / 'controller' / (original.JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (original.WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'failed' or resource['exit_code'] != 1 or [r for r in ledger if r.get('name') == original.JOB] != [resource]:
        raise ValueError('Actual44 failed unique terminal/ledger differs')
    log = (original.RUN / 'controller' / (original.JOB + '.log')).read_text()
    if "has no attribute '_require_grads_hook'" not in log or 'JOINT44_TRAJECTORY' in log:
        raise ValueError('Actual failure not proved before first trajectory')
    if list((ROOT / 'joint_train44').glob('episode_*/rollout/*/raw.json')):
        raise ValueError('An original successful trajectory exists; explicit adoption needed')
    if read(ROOT / 'joint_preflight44/completion.json')['state'] != 'PASS_EXACT_FINAL_FP32_ACTOR_RELOAD':
        raise ValueError('Passed original final-roundtrip preflight missing')
    remaining = int(2400 - resource['charged_seconds'])
    if remaining <= 0:
        raise ValueError('Original frozen training budget exhausted')
    original.OUT = OUT
    original.JOB = JOB
    original.execute('joint_hook47.py')
    if read(ROOT / 'joint_hook47/completion.json')['state'] != 'PASS_REAL_TRANSFORMERS_INITIAL_AND_REPEATED_HOOK_LIFECYCLE':
        raise ValueError('Actual lifecycle regression failed')
    import subprocess
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU task active; preserve accepted recovery')
    lock = read(ROOT / 'joint_train44/source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    for name in ['joint_remaining47.py', 'joint_remaining47_gpu.py', 'joint_remaining47_audit.py', 'joint_rollout47.py', 'joint_hook47.py']:
        lock['code'][name] = identity(Path(__file__).parent / name)
    save(OUT / 'source_input_lock.json', lock)
    save(OUT / 'registration.json', dict(actual_failure=identity(ROOT / 'joint_train44/failure.json'),
        actual_failed_resource=identity(original.RUN / 'controller/T_joint_source_counterfactual_sft4_20261022_v44.resource.json'),
        original_training_limit=2400, previous_charge=resource['charged_seconds'], remaining_seconds=remaining,
        adopted_CPU_preflight=identity(ROOT / 'joint_preflight44/completion.json'),
        adopted_model_identity=identity(ROOT / 'joint_train44/model_acceptance.json'),
        original_model_trajectories=0, original_updates=0,
        model_reload_required_after_actual_process_exit=True, no_successful_generation_or_TF_or_optimizer_repeated=True,
        recovery_only='Guard first disable_input_require_grads on actual absent hook; scientific4-episode protocol unchanged'))
    original.execute('joint_remaining47_gpu.py', remaining)
    original.execute('joint_remaining47_audit.py')
    final = read(original.RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (original.WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if final['status'] != 'completed' or final['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [final]:
        raise ValueError('Unique remaining natural GPU terminal differs')
    result = read(OUT / 'gpu_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], actual_optimizer_updates=result['actual_optimizer_updates'],
        GPU_seconds=final['charged_seconds'], prior_failed44_seconds=resource['charged_seconds'],
        cumulative_T1_seconds=1302.8305039964616 + resource['charged_seconds'] + final['charged_seconds'],
        final_adapter=result['final_adapter'], CPU_audit=identity(OUT / 'independent_CPU_audit.json'),
        no_automatic_development_or_production=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
