"""Exact per-success gradient and publisher-state recovery, no checkpoint selection."""
import math

import torch

from joint_checkpoint44 import cpu_tree
from summary_actor88 import state_CPU
from t_io import identity


def rng():
    return dict(torch_CPU=torch.get_rng_state(), torch_CUDA=torch.cuda.get_rng_state_all())


def gradient_state(path, trainable, cursor, publisher_checkpoint):
    gradients = {}; squares = []; nonzero = 0
    for name, p in trainable:
        if p.grad is None:
            raise ValueError('A declared content-adapter parameter has no gradient')
        value = p.grad.detach().float().contiguous().cpu()
        if not torch.isfinite(value).all():
            raise ValueError('Actual accumulated content gradient is nonfinite')
        squares.append(float(value.double().square().sum()))
        nonzero += int(torch.count_nonzero(value)); gradients[name] = value
    with path.open('xb') as stream:
        torch.save(dict(gradients=gradients, cursor=cursor,
            publisher_checkpoint=publisher_checkpoint, random_state=rng(),
            exact_accumulated_gradient=True, not_checkpoint_selection=True), stream)
    return dict(file=identity(path), norm_float64=math.sqrt(math.fsum(squares)),
                nonzero_elements=nonzero, tensors=len(gradients), cursor=cursor)


def publisher_checkpoint(path, model, optimizer, completed_updates, cursor):
    with path.open('xb') as stream:
        torch.save(dict(summary=state_CPU(model), optimizer=cpu_tree(optimizer.state_dict()),
            completed_optimizer_updates=completed_updates, cursor=cursor, random_state=rng(),
            exact_recovery_only_not_checkpoint_selection=True), stream)
    return identity(path)


def first_optimizer_witness(path, before, clipped, trainable):
    with path.open('xb') as stream:
        torch.save(dict(before=before,
            clipped_gradient={name: p.grad.detach().float().cpu() for name, p in trainable},
            after={name: p.detach().cpu() for name, p in trainable},
            actual_clipped_gradient=clipped, step=1, optimizer='AdamW',
            learning_rate=5e-5, betas=[.9, .999], epsilon=1e-8, weight_decay=0.), stream)
    return identity(path)
