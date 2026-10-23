"""Causal surrogate replay; immutable frozen-reference cache, actor-only gradients."""
import hashlib
import json

import torch

from actor_roles33 import activate_actor
from causal_policy32 import causal_suffix
from policy_contract import source_policy_loss
from t_io import ROOT, check, identity, read, save


def forward(model, case, tokens):
    suffix = causal_suffix(case.values['input_ids'], tokens)
    values = dict(case.values, input_ids=suffix['input_ids'], attention_mask=suffix['attention_mask'])
    result = model(**{key: value.cuda() if torch.is_tensor(value) else value
                      for key, value in values.items()}, logits_to_keep=len(tokens), use_cache=False)
    logits = result.logits[0]
    if logits.shape[0] != len(tokens):
        raise ValueError('Actual causal suffix/action length differs')
    return logits


def project(logits, allowed):
    result = [row[torch.tensor(ids, device=row.device)].detach().float().cpu()
              for row, ids in zip(logits, allowed)]
    if not all(torch.isfinite(row).all() for row in result):
        raise ValueError('Actual allowed causal logits are nonfinite')
    return result


def actor_training_mode(model):
    activate_actor(model, 'actor')
    model.train()
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Dropout):
            module.p = 0.0
        if name.endswith('.visual'):
            module.eval()


class ReferenceCache:
    def __init__(self, folder):
        self.folder, self.entries, self.prior = folder, {}, {}
        folder.mkdir()
        for ref in read(ROOT / 'policy_adopt40/completion.json')['accepted']:
            row = read(check(ref))
            desc = row['native_contract']
            payload = torch.load(check(row['conditional_probabilities']), map_location='cpu', weights_only=True)
            key = self.key(desc['original_CPU'], payload['targets'], payload['allowed_tokens'])
            self.prior[key] = (payload['allowed_logits'], ref)

    @staticmethod
    def key(cpu, tokens, allowed):
        return hashlib.sha256(json.dumps([cpu['sha256'], tokens, allowed], separators=(',', ':')).encode()).hexdigest()

    def get(self, model, case, result):
        key = self.key(case.CPU, result['tokens'], result['allowed'])
        if key in self.entries:
            values, ref = self.entries[key]
            return values, dict(cache=ref, repeated_frozen_forward=False)
        if key in self.prior:
            values, ref = self.prior[key]
            self.entries[key] = (values, ref)
            return values, dict(adopted_successful_TF=ref, repeated_frozen_forward=False)
        model.set_adapter('default')
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        model.eval()
        with torch.no_grad():
            values = project(forward(model, case, result['tokens']), result['allowed'])
        path = self.folder / (key + '.pt')
        with path.open('xb') as stream:
            torch.save(dict(allowed_logits=values, allowed_tokens=result['allowed'],
                            targets=result['tokens'], CPU=case.CPU), stream)
        self.entries[key] = (values, identity(path))
        return values, dict(first_reference_TF=identity(path), repeated_frozen_forward=False)


def backward_window(model, case, result, advantage, beta, cache, folder):
    folder.mkdir()
    reference, adoption = cache.get(model, case, result)
    actor_training_mode(model)
    logits = forward(model, case, result['tokens'])
    dense_reference = torch.zeros_like(logits, dtype=torch.float32)
    for index, (allowed, values) in enumerate(zip(result['allowed'], reference)):
        dense_reference[index, torch.tensor(allowed, device=logits.device)] = values.to(logits.device)
    loss, statistics = source_policy_loss(logits, dense_reference.detach(), result['tokens'],
        result['allowed'], 1.0, advantage, beta)
    payload = folder / 'projected.pt'
    with payload.open('xb') as stream:
        torch.save(dict(actor=project(logits, result['allowed']), reference=reference,
            allowed=result['allowed'], tokens=result['tokens']), stream)
    record = dict(case=case.name, CPU=case.CPU, advantage=advantage, kl_weight=beta,
        loss=float(loss.detach()), sequence_logp=float(statistics['sequence_logp']),
        mean_allowed_KL=float(statistics['mean_allowed_categorical_KL']),
        projected=identity(payload), frozen_reference=adoption,
        physical_incremental_probability_identity_claim=False)
    loss.backward()
    if any(p.grad is not None for name, p in model.named_parameters() if '.actor.' not in name):
        raise ValueError('Source surrogate leaked gradient into BASE/reference')
    save(folder / 'backward.json', record)
    return identity(folder / 'backward.json')
