"""Differentiable token policy on exactly the grammar-allowed action set."""
import math

import torch


def distributions(logits, allowed_tokens, temperature):
    if logits.ndim != 2 or len(allowed_tokens) != logits.shape[0]:
        raise ValueError('Token states and causal logit positions differ')
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError('An explicit positive sampling temperature is required')
    result = []
    for row, allowed in zip(logits, allowed_tokens):
        ids = torch.as_tensor(allowed, dtype=torch.long, device=row.device)
        if ids.ndim != 1 or ids.numel() == 0 or ids.unique().numel() != ids.numel():
            raise ValueError('Invalid/duplicate allowed token set')
        if int(ids.min()) < 0 or int(ids.max()) >= row.numel():
            raise ValueError('Allowed token outside actual vocabulary')
        values = row.index_select(0, ids)
        if not torch.isfinite(values).all():
            raise ValueError('Nonfinite logits in an allowed policy action')
        # Preserve float64 in numerical checks; accumulate low-precision model logits in float32.
        values = values if values.dtype == torch.float64 else values.float()
        result.append(torch.log_softmax(values / temperature, dim=0))
    return result


def sampled_logps(logits, tokens, allowed_tokens, temperature):
    if len(tokens) != logits.shape[0]:
        raise ValueError('Sample length and causal forward positions differ')
    values = distributions(logits, allowed_tokens, temperature)
    selected = []
    for token, allowed, log_probs in zip(tokens, allowed_tokens, values):
        positions = [i for i, candidate in enumerate(allowed) if int(candidate) == int(token)]
        if len(positions) != 1:
            raise ValueError('Actual sampled token was forbidden by its grammar state')
        selected.append(log_probs[positions[0]])
    return torch.stack(selected)


def source_policy_loss(actor_logits, reference_logits, tokens, allowed_tokens,
                       temperature, source_advantage, kl_weight):
    if reference_logits.requires_grad or reference_logits.shape != actor_logits.shape:
        raise ValueError('Reference must be detached and shape-identical')
    if not math.isfinite(source_advantage) or not math.isfinite(kl_weight) or kl_weight < 0:
        raise ValueError('Invalid source reward or reference penalty')
    actor = distributions(actor_logits, allowed_tokens, temperature)
    reference = distributions(reference_logits, allowed_tokens, temperature)
    token_kl = torch.stack([(a.exp() * (a - b)).sum() for a, b in zip(actor, reference)])
    policy_logps = sampled_logps(actor_logits, tokens, allowed_tokens, temperature)
    loss = -float(source_advantage) * policy_logps.sum() + kl_weight * token_kl.mean()
    if not torch.isfinite(loss):
        raise ValueError('Nonfinite policy objective; never convert it to a skipped/empty success')
    return loss, dict(sequence_logp=policy_logps.detach().sum(),
                      mean_allowed_categorical_KL=token_kl.detach().mean())
