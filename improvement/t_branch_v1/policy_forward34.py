"""First original-token causal forward probes, adopting all successful visual tensors."""
import math

import numpy as np
import torch

from policy_contract import sampled_logps
from t_io import check, identity, read, save


def forward_inputs(descriptor):
    cpu = read(check(descriptor['original_CPU']))
    with np.load(check(cpu['encoded']), allow_pickle=False) as archive:
        values = {key: torch.from_numpy(archive[key].copy()) for key in archive.files
                  if key not in ['input_ids', 'attention_mask']}
    with np.load(check(descriptor['causal_text']), allow_pickle=False) as archive:
        values.update({key: torch.from_numpy(archive[key].copy()) for key in ['input_ids', 'attention_mask']})
        targets = archive['targets'][0].tolist()
    if len(targets) != descriptor['logits_to_keep'] or len(targets) != len(descriptor['actual_allowed_tokens']):
        raise ValueError('Actual target and allowed grammar suffix counts differ')
    values.update(cpu['non_tensor_inputs'])
    return values, targets


def causal_logits(model, descriptor):
    values, targets = forward_inputs(descriptor)
    output = model(**{key: value.cuda() if torch.is_tensor(value) else value for key, value in values.items()},
                   logits_to_keep=descriptor['logits_to_keep'], use_cache=False)
    logits = output.logits[0]
    if logits.shape[0] != len(targets) or not torch.isfinite(logits).all():
        raise ValueError('Actual model causal suffix is nonfinite or has the wrong length')
    return logits, targets


def reference_forward(model, descriptor, output):
    with torch.no_grad():
        logits, targets = causal_logits(model, descriptor)
    raw = read(check(descriptor['original_raw']))
    selected = logits.float()[torch.arange(len(targets), device=logits.device), targets]
    observed = torch.tensor(raw['token_scores'], device=logits.device, dtype=torch.float32)
    # This only bounds low-precision TF versus cached incremental-kernel drift.
    # It is deliberately not described as exact rollout-probability identity.
    precision = torch.finfo(model.get_base_model().dtype).eps
    bound = 4 * precision * (1 + observed.abs())
    errors = (selected - observed).abs()
    allowed = descriptor['actual_allowed_tokens']
    logps = sampled_logps(logits, targets, allowed, 1.0)
    permitted = [row[torch.tensor(ids, device=row.device)].float().cpu()
                 for row, ids in zip(logits, allowed)]
    matches = sum(int(ids[int(torch.argmax(row))]) == target
                  for row, ids, target in zip(permitted, allowed, targets))
    payload = output / (descriptor['case'] + '.pt')
    with payload.open('xb') as stream:
        torch.save(dict(allowed_logits=permitted, allowed_tokens=allowed,
                        targets=targets, conditional_logps=logps.detach().float().cpu()), stream)
    record = dict(case=descriptor['case'], native_contract=descriptor,
        selected_raw_logits=selected.cpu().tolist(), cached_generation_logits=observed.cpu().tolist(),
        absolute_logit_errors=errors.cpu().tolist(), numerical_bounds=bound.cpu().tolist(),
        argmax_matches=matches, actions=len(targets), forced_states=descriptor['forced_states'],
        exact_incremental_probability_identity_claim=False,
        conditional_probabilities=identity(payload), temperature=1.0)
    save(output / (descriptor['case'] + '.json'), record)
    if not bool(torch.all(errors <= bound)) or not math.isfinite(float(logps.sum())):
        raise ValueError('Actual causal/incremental logits exceed predeclared numerical drift bound')
    return logits.detach().float().cpu(), identity(output / (descriptor['case'] + '.json'))
