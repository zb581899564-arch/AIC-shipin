"""Restore a durable gradient prefix and finish the same source update once."""
import random

import numpy as np
import torch

from joint_checkpoint44 import actor_digest, gradient_snapshot, recovery_checkpoint
from joint_replay44 import backward_window
from joint_reward43 import source_counterfactuals
from resume_rollout50 import rollout
from resume_state50 import restore_gradient
from t_io import check, identity, read, save


def gradient_prefix(source, old_episode):
    replays, gradients, missing = [], [], False
    for case in source.cases:
        path = old_episode / (case.name + '_gradient_acceptance.json')
        if not path.exists():
            missing = True
            continue
        if missing:
            raise ValueError('Old accepted cumulative gradient prefix has a hole')
        ref = read(path)
        check(ref['file'])
        backward = old_episode / (case.name + '_replay/backward.json')
        row = read(backward)
        if row['case'] != case.name or row['CPU'] != case.CPU:
            raise ValueError('Old accepted backward input identity differs')
        replays.append(identity(backward)); gradients.append(ref)
    return replays, gradients


def episode(model, processor, rt, source, index, method, optimizer, trainable, cache, old_episode, folder):
    folder.mkdir()
    if (old_episode / 'clipped_gradient.npz').exists():
        raise ValueError('Old source may already have executed optimizer; require checkpoint adoption, never guess/repeat it')
    before = actor_digest(model)
    greedy, sampled, receipts = rollout(model, processor, rt, source, old_episode, folder / 'rollout', method['sampling'])
    if actor_digest(model) != before:
        raise ValueError('Actor changed during remaining complete-source rollout')
    reward = source_counterfactuals(sampled, greedy, source.allowed, source.reviews, len(source.reviews))
    save(folder / 'reward.json', reward); save(folder / 'trajectories.json', receipts)
    prior_reward = old_episode / 'reward.json'
    if prior_reward.exists() and read(prior_reward) != reward:
        raise ValueError('Same completed source actions yield different reward on recovery')
    signal = any(row['advantage'] != 0 for row in reward['per_window'].values())
    optimizer.zero_grad(set_to_none=True)
    replays, gradients = gradient_prefix(source, old_episode)
    adopted = len(gradients)
    if gradients:
        restore_gradient(trainable, gradients[-1])
    if signal:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        for case in source.cases[adopted:]:
            result = read(check(receipts[case.name]['sampled']))
            replays.append(backward_window(model, case, result, reward['per_window'][case.name]['advantage'],
                .02 / len(source.cases), cache, folder / (case.name + '_replay')))
            gradients.append(gradient_snapshot(folder / (case.name + '_cumulative_grad.npz'), trainable))
            save(folder / (case.name + '_gradient_acceptance.json'), gradients[-1])
            print('REMAIN50_FIRST_BACKWARD', index, case.name, flush=True)
        if actor_digest(model) != before:
            raise ValueError('Remaining actor changed before entire source accumulated')
        norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in trainable], method['global_gradient_clip'], error_if_nonfinite=True))
        clipped = gradient_snapshot(folder / 'clipped_gradient.npz', trainable)
        if not np.isfinite(norm) or norm == 0:
            raise ValueError('Actual source signal has no finite gradient')
        optimizer.step()
    else:
        if gradients:
            raise ValueError('Old accepted gradients contradict no-signal source')
        norm, clipped = 0., None
    after = actor_digest(model)
    if signal and before == after:
        raise ValueError('Remaining actual optimizer produced no actor change')
    rng = dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state(), CUDA=torch.cuda.get_rng_state_all())
    checkpoint = recovery_checkpoint(folder / 'recovery_only.pt', model, optimizer, index, rng)
    save(folder / 'completion.json', dict(index=index, source=source.sid, actor_before=before, actor_after=after,
        trajectories=identity(folder / 'trajectories.json'), reward=identity(folder / 'reward.json'),
        state='SOURCE_UPDATE' if signal else 'NO_SOURCE_SIGNAL', optimizer_updates=int(signal),
        replays=replays, gradients=gradients, norm_before_clip=norm, clipped_gradient=clipped,
        recovery_checkpoint=checkpoint, intermediate_checkpoint_selection=False,
        adopted_completed_backward_windows=adopted, old_completed_optimizer_repeated=False))
    return identity(folder / 'completion.json')
