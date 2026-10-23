"""Independent scalar probability audit of first saved real-model causal projections."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import math

import numpy as np
import torch

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'policy_probe35'


def independent_logps(ref):
    row = read(check(ref))
    payload = torch.load(check(row['conditional_probabilities']), map_location='cpu', weights_only=True)
    maximum_error = 0.0
    for values, allowed, target, actual in zip(payload['allowed_logits'], payload['allowed_tokens'],
                                               payload['targets'], payload['conditional_logps']):
        scores = values.numpy().astype(np.float64)
        if len(scores) != len(set(allowed)) or target not in allowed or not np.isfinite(scores).all():
            raise ValueError('Actual saved allowed-action projection invalid')
        pivot = float(scores.max())
        denominator = pivot + math.log(math.fsum(math.exp(float(value) - pivot) for value in scores))
        expected = float(scores[allowed.index(target)]) - denominator
        error = abs(expected - float(actual))
        bound = 8 * np.finfo(np.float32).eps * (1 + abs(expected))
        if error > bound:
            raise ValueError('Independent float64 conditional-probability replay differs')
        if len(allowed) == 1 and (expected != 0 or float(actual) != 0):
            raise ValueError('Forced grammar action has nonzero policy log-probability')
        maximum_error = max(maximum_error, error)
    return dict(case=row['case'], actions=len(payload['targets']), maximum_absolute_error=maximum_error,
                argmax_matches_incremental=row['argmax_matches'], no_exact_incremental_identity_claim=True)


def main():
    gpu = read(OUT / 'gpu_completion.json')
    if gpu['state'] != 'REAL8B_CAUSAL_ROLE_BACKWARD_PROBE_COMPLETE' or gpu['optimizer_updates'] != 0:
        raise ValueError('Actual backward-only8B probe terminal differs')
    checks = [independent_logps(ref) for ref in gpu['calibration']]
    gradient = gpu['gradient_probe']
    if not math.isfinite(gradient['actor_gradient_norm']) or gradient['actor_gradient_norm'] <= 0:
        raise ValueError('No actual finite actor gradient signal')
    header = read(ROOT / 'actor_contract33/completion.json')['actual_saved_header']
    if gpu['actual_complete_parameters'] != header['actual_shared_base_two_adapters_and_head_parameters']:
        raise ValueError('Live main/auxiliary parameter total differs from exact saved shapes')
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS', causal_scalar_checks=checks,
        actual8B_gradient_nonzero_actor_only=True, model_reference_actor_weights_unchanged=True,
        training_or_quality_admitted=False, reward_was_explicit_synthetic_gradient_probe_only=True,
        GPU_terminal=identity(OUT / 'gpu_completion.json'), CUDA_initialized=torch.cuda.is_initialized()))


if __name__ == '__main__':
    main()
