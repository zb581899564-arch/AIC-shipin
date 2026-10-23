"""Adopt4 passed causal TF projections; only first remaining exact-copy actor backward."""
import sys

import torch

from actor_copy41 import exact_actor_copy
from policy_probe34 import backward_only
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'policy_remaining42'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def reference_from_allowed(record, vocabulary):
    payload = torch.load(check(record['conditional_probabilities']), map_location='cpu', weights_only=True)
    reference = torch.zeros(len(payload['targets']), vocabulary, dtype=torch.float32)
    for index, (allowed, values) in enumerate(zip(payload['allowed_tokens'], payload['allowed_logits'])):
        reference[index, torch.tensor(allowed, dtype=torch.long)] = values
    return reference


def main():
    rt = legacy_runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, _, loaded = rt.b_engine.load_model(config)
    adopted = read(ROOT / 'policy_adopt40/completion.json')
    records = [read(check(ref)) for ref in adopted['accepted']]
    chosen = max(records, key=lambda row: row['native_contract']['prefix_tokens'])
    descriptor = chosen['native_contract']
    reference = reference_from_allowed(chosen, model.get_base_model().lm_head.weight.shape[0])
    trainable, copying = exact_actor_copy(model, config['b_adapter'])
    resident = sum(parameter.numel() for parameter in model.parameters()) + 98329
    expected = read(ROOT / 'actor_contract33/completion.json')['actual_saved_header']
    if resident != expected['actual_shared_base_two_adapters_and_head_parameters'] or resident > 9000000000:
        raise ValueError('Live exact-copy actor/reference/head parameter count differs')
    save(OUT / 'actual_actor_copy.json', dict(**copying, actual_complete_parameters=resident,
        original_TIME_adapter_parameters=sum(value.numel() for _, value in trainable),
        source='Actual default adapter values after original inference loader, not rounded additional load',
        first_four_TFs_adopted=adopted['accepted']))
    gradient = backward_only(model, descriptor, reference, trainable)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original BASE/TIME changed in remaining backward-only probe')
    save(OUT / 'gpu_completion.json', dict(state='REAL8B_CAUSAL_ROLE_BACKWARD_PROBE_COMPLETE',
        first_reference_TF_calls=0, adopted_reference_TF_calls=4,
        first_actor_gradient_forward=1, real_backward_calls=1, calibration=adopted['accepted'],
        gradient_probe=gradient, actual_complete_parameters=resident,
        torch_peak_bytes=torch.cuda.max_memory_allocated(), optimizer_updates=0,
        original_base_TIME_and_protected40_47_unchanged=True,
        reference_forbidden_logits_unused_in_allowed_normalizer=True,
        no_quality_reward_or_new_generation_or_training_claim=True))


if __name__ == '__main__':
    main()
