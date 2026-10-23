"""Four first causal TFs and one actor backward, with zero optimizer updates."""
import math
import sys

import torch

from actor_roles33 import activate_actor, adapter_equal
from policy_contract import source_policy_loss
from policy_forward34 import causal_logits, reference_forward
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'policy_probe35'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import RUN, legacy_runtime


def clone_actor(model, config):
    model.load_adapter(config['b_adapter'], adapter_name='actor', is_trainable=True)
    if not adapter_equal(model):
        raise ValueError('Actual8B actor is not an exact original TIME copy')
    trainable = activate_actor(model, 'actor')
    actor_count = sum(value.numel() for _, value in trainable)
    resident = sum(parameter.numel() for parameter in model.parameters()) + 98329
    expected = read(ROOT / 'actor_contract33/completion.json')['actual_saved_header']
    if actor_count != expected['original_TIME_adapter_parameters'] or resident != expected['actual_shared_base_two_adapters_and_head_parameters']:
        raise ValueError('Actual live8B/reference/actor/head parameter total differs from saved header')
    if resident > 9000000000:
        raise ValueError('Actual complete main/auxiliary model exceeds9B')
    return trainable, resident


def backward_only(model, descriptor, reference_logits, trainable):
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.train()
    dropout_sites = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Dropout):
            dropout_sites.append(dict(name=name, original_probability=module.p))
            module.p = 0.0
        if name.endswith('.visual'):
            module.eval()
    logits, targets = causal_logits(model, descriptor)
    loss, statistics = source_policy_loss(logits, reference_logits.cuda(), targets,
        descriptor['actual_allowed_tokens'], temperature=1.0, source_advantage=1.0, kl_weight=0.02)
    loss.backward()
    norms, nonzero = [], []
    for name, parameter in trainable:
        if parameter.grad is None or not torch.isfinite(parameter.grad).all():
            raise ValueError('Actual actor gradient missing or nonfinite')
        norm2 = float(parameter.grad.float().square().sum())
        norms.append(norm2)
        if norm2 > 0:
            nonzero.append(name)
    if not nonzero or any(p.grad is not None for name, p in model.named_parameters() if '.actor.' not in name):
        raise ValueError('Real backward has no actor signal or leaks into reference/base')
    record = dict(loss=float(loss.detach()), actor_gradient_norm=math.sqrt(math.fsum(norms)),
        trainable_tensors=len(trainable), nonzero_gradient_tensors=len(nonzero),
        nonzero_gradient_names=nonzero, sequence_logp=float(statistics['sequence_logp']),
        mean_allowed_KL=float(statistics['mean_allowed_categorical_KL']),
        synthetic_advantage_for_engineering_probe_only=1.0, actual_source_reward_not_used=True,
        dropout_sites_disabled_for_deterministic_probe=dropout_sites,
        optimizer_created=False, optimizer_updates=0)
    model.zero_grad(set_to_none=True)
    model.gradient_checkpointing_disable()
    model.disable_input_require_grads()
    model.eval()
    model.set_adapter('default')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    if not adapter_equal(model):
        raise ValueError('Backward without optimizer changed original or cloned TIME weights')
    return record


def main():
    rt = legacy_runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, _, loaded = rt.b_engine.load_model(config)
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    descriptors = [read(check(ref)) for ref in read(ROOT / 'causal_contract32/completion.json')['accepted']]
    selected = max(descriptors, key=lambda row: row['prefix_tokens'])
    target = OUT / 'causal_outputs'
    target.mkdir()
    rows, selected_reference = [], None
    for descriptor in descriptors:
        logits, receipt = reference_forward(model, descriptor, target)
        rows.append(receipt)
        if descriptor['case'] == selected['case']:
            selected_reference = logits
        print('FIRST_CAUSAL_TF34_ACCEPTED', descriptor['case'], flush=True)
    trainable, resident = clone_actor(model, config)
    gradient = backward_only(model, selected, selected_reference, trainable)
    if rt.b_engine.frozen_identity(model, config) != loaded['base'] or rt.b_engine.adapter_identity(model, config) != loaded['adapter']:
        raise ValueError('Original frozen BASE/TIME identity changed in backward-only probe')
    save(OUT / 'gpu_completion.json', dict(state='REAL8B_CAUSAL_ROLE_BACKWARD_PROBE_COMPLETE',
        first_reference_TF_calls=4, first_actor_gradient_forward=1, real_backward_calls=1,
        calibration=rows, gradient_probe=gradient, actual_complete_parameters=resident,
        torch_peak_bytes=torch.cuda.max_memory_allocated(), optimizer_updates=0,
        original_base_TIME_and_protected40_47_unchanged=True,
        no_quality_reward_or_new_generation_or_training_claim=True))


if __name__ == '__main__':
    main()
