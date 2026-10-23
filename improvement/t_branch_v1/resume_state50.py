"""Exact saved actor/optimizer/cumulative-gradient restoration, no old update replay."""
import random

import numpy as np
import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict

from joint_checkpoint44 import actor_digest
from t_io import check


def restore_checkpoint(model, optimizer, receipt):
    payload = torch.load(check(receipt['recovery_checkpoint']), map_location='cpu', weights_only=False)
    if payload['completed_episode'] != receipt['index']:
        raise ValueError('Recovery checkpoint episode identity differs')
    set_peft_model_state_dict(model, payload['actor'], adapter_name='actor')
    actual = get_peft_model_state_dict(model, adapter_name='actor')
    if set(actual) != set(payload['actor']) or any(not torch.equal(actual[k].detach().cpu(), payload['actor'][k]) for k in actual):
        raise ValueError('Actual actor checkpoint restoration rounded values')
    if actor_digest(model) != receipt['actor_after']:
        raise ValueError('Actual restored actor digest differs from last complete source')
    optimizer.load_state_dict(payload['optimizer'])
    rng = payload['rng']
    random.setstate(rng['python']); np.random.set_state(rng['numpy'])
    torch.set_rng_state(rng['torch']); torch.cuda.set_rng_state_all(rng['CUDA'])
    return dict(last_completed_episode=payload['completed_episode'], actor_digest=receipt['actor_after'],
        original_completed_optimizer_updates_not_repeated=True, actual_RNG_restored=True)


def restore_gradient(trainable, ref):
    if ref['parameter_names'] != [name for name, _ in trainable]:
        raise ValueError('Saved cumulative gradient parameter order differs')
    with np.load(check(ref['file']), allow_pickle=False) as archive:
        if len(archive.files) != len(trainable):
            raise ValueError('Saved cumulative gradient inventory differs')
        for index, (_, parameter) in enumerate(trainable):
            value = archive['p%03d' % index]
            if value.shape != tuple(parameter.shape) or value.dtype != np.float32 or not np.isfinite(value).all():
                raise ValueError('Saved cumulative gradient shape/dtype/finite check failed')
            parameter.grad = torch.from_numpy(value.copy()).to(parameter.device)
