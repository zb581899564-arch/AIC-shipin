"""Adopt first scalar replay40, inspect first real remaining actor-gradient terminal."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import math

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'policy_remaining42'


def main():
    gpu = read(OUT / 'gpu_completion.json')
    adopted = read(ROOT / 'policy_adopt40/completion.json')
    if adopted['state'] != 'FOUR_SUCCESSFUL_CAUSAL_TF_ADOPTED_CPU_SCALAR_PASS':
        raise ValueError('Original successful TF scalar replay absent')
    if gpu['calibration'] != adopted['accepted'] or gpu['adopted_reference_TF_calls'] != 4:
        raise ValueError('Remaining backward used different reference projections')
    for ref in gpu['calibration']:
        check(ref)
    gradient = gpu['gradient_probe']
    if (gpu['optimizer_updates'] != 0 or gradient['optimizer_created'] or
            not math.isfinite(gradient['actor_gradient_norm']) or gradient['actor_gradient_norm'] <= 0):
        raise ValueError('Expected real actor-only backward without optimizer differs')
    expected = read(ROOT / 'actor_contract33/completion.json')['actual_saved_header']
    if gpu['actual_complete_parameters'] != expected['actual_shared_base_two_adapters_and_head_parameters']:
        raise ValueError('Actual complete parameter total differs')
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS',
        adopted_scalar_replay=identity(ROOT / 'policy_adopt40/completion.json'),
        first_actor_gradient_and_frozen_weight_checks=identity(OUT / 'gpu_completion.json'),
        exact_copy=identity(OUT / 'actual_actor_copy.json'),
        actual8B_actor_gradient_nonzero=True, optimizer_updates=0,
        synthetic_advantage_not_real_training_reward=True, quality_or_training_admitted=False))


if __name__ == '__main__':
    main()
