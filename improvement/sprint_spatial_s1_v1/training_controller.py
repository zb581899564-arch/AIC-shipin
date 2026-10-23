"""Adopt completed first preparation, then one frozen three-arm S1 experiment."""
from datetime import datetime, timezone
import os
import traceback
from common import ROOT, checked, read, ref, write, run_stage, baseline_identity


def main():
    write(ROOT / 'training_claim.json', dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat()))
    preparation = read(ROOT / 'preparation_completion.json')
    if preparation['status'] != 'S1_CPU_AND762_FROZEN_CENTERS_READY_FOR_CONDITIONED_TRAINING_INPUTS':
        raise ValueError('Only naturally completed CPU/center chain can be adopted')
    baseline = baseline_identity()
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(read(ROOT / 'prepare_launch.json')['UTC'])).total_seconds()
    if elapsed + 3600 + 900 > read(ROOT / 'protocol.json')['research_wall_seconds']:
        raise ValueError('Remaining declared wall budget cannot fit first training and confirm')
    contract = read(ROOT / 'training_cpu_contract_acceptance.json')
    if contract['status'] != 'PASS' or contract['tests'] != 3:
        raise ValueError('Current real Torch/PEFT CPU contracts have not passed')
    for asset in read(ROOT / 'training_code_acceptance02.json')['files'].values():
        checked(asset)
    run_stage('conditioned', 'condition_inputs.py')
    profile = read(ROOT / 'center_throughput8.json')
    recipe = dict(updates=50, grad_accum=8, seed=20261021, lr=1e-4, rank=8, alpha=16, dropout=.05,
         original_BASE_fresh_initialization=True, no_old_adapter_used=True, first8_cost_profile=profile,
         all_gpu_seconds_limit=7200, proposed_training_and_dev_wrapper_seconds=3600,
         actual_first_center_seconds=preparation['charged_seconds'], final_checkpoint_only=True,
         no_learning_rate_grid_or_checkpoint_selection=True)
    if preparation['charged_seconds'] >= 3000:
        raise ValueError('Center actual cost leaves insufficient fixed3arm budget; stop before training')
    write(ROOT / 'training_recipe.json', recipe)
    write(ROOT / 'training_source_lock.json', dict(recipe=ref(ROOT / 'training_recipe.json'),
        inputs=ref(ROOT / 'conditioned_input_acceptance.json'), preaccepted=ref(ROOT / 'pixel_acceptance.json'),
        cpu_contracts=ref(ROOT / 'training_cpu_contract_acceptance.json'),
        code={p.name: ref(p) for p in sorted((ROOT / 'code').glob('*.py'))}, baseline=baseline,
        centers=ref(ROOT / 'center_completion.json'), upstream=ref(ROOT / 'upstream_acceptance.json')))
    train_record = run_stage('three_arms', 'train_arms.py', gpu_seconds=3600)
    run_stage('dev_audit_review', 'audit_review.py', ['--role', 'dev'])
    confirm_record = None
    if (ROOT / 'selected.json').exists():
        remaining = 7200 - preparation['charged_seconds'] - train_record['charged_seconds']
        if remaining < 900:
            raise ValueError('Not enough declared budget for first confirm; preserve selected and all dev outputs')
        confirm_record = run_stage('first_confirm', 'confirm.py', gpu_seconds=min(900, int(remaining)))
        run_stage('confirm_audit_review', 'audit_review.py', ['--role', 'confirm'])
        passed = read(ROOT / 'confirm_review.json')['arms'][0]['summary']['passed']
        status = 'S1_STATIC_CONFIRM_RISK_GATES_PASSED_SEPARATE_S2_REVIEW_REQUIRED' if passed else 'STOP_S1_FIXED_CONFIRM_RISKS'
    else:
        status = read(ROOT / 'development_stop.json')['status']
    if baseline_identity() != baseline:
        raise ValueError('Protected baseline modified')
    for entry in read(ROOT / 'training_source_lock.json')['code'].values():
        checked(entry)
    result = dict(status=status, dev=ref(ROOT / 'dev_review.json'), new_updates=150,
        new_dev_generations=240, new_confirm_generations=80 if confirm_record else 0,
        centers=762, center_GPU_seconds=preparation['charged_seconds'],
        training_and_dev_GPU_seconds=train_record['charged_seconds'],
        confirm_GPU_seconds=confirm_record['charged_seconds'] if confirm_record else 0,
        all_GPU_seconds=preparation['charged_seconds'] + train_record['charged_seconds'] + (confirm_record['charged_seconds'] if confirm_record else 0),
        arms=[dict(arm=r['arm'], summary=r['summary']) for r in read(ROOT / 'dev_review.json')['arms']],
        old_width200_STOP_unchanged=True, baseline_unchanged=True, new_ZIP=0,
        automatic_S2_or_production=False, official_joint_score='UNKNOWN', completed_UTC=datetime.now(timezone.utc).isoformat())
    if confirm_record:
        result['confirm'] = read(ROOT / 'confirm_review.json')['arms'][0]['summary']
        result['selected_arm'] = read(ROOT / 'selected.json')['arm']
    write(ROOT / 'completion.json', result)
    write(ROOT / 'short_result.json', result)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'training_failure.json', dict(status='ACTUAL_FAILURE_ALL_SUCCESS_PRESERVED', traceback=traceback.format_exc()))
        raise
