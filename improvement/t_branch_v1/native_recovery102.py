"""Exact first-micro adoption and publisher-boundary actor/Adam recovery."""
import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict

from joint_checkpoint44 import recovery_checkpoint
from native_state100 import fingerprint
from summary_recovery88 import first_optimizer_witness, gradient_state, rng
from t_io import check, identity, read, save


def restore_first(model, optimizer, trainable, raw, base):
    checkpoint = torch.load(check(raw['initial_actor_optimizer']), map_location='cpu', weights_only=True)
    packet = torch.load(check(raw['exact_successful_gradient']['file']), map_location='cpu', weights_only=True)
    if checkpoint['completed_episode'] != 0 or packet['cursor'] != raw['cursor']:
        raise ValueError('First micro recovery actor/update cursor differs')
    set_peft_model_state_dict(model, checkpoint['actor'], adapter_name='actor')
    state = get_peft_model_state_dict(model, adapter_name='actor')
    if set(state) != set(checkpoint['actor']) or any(not torch.equal(
            state[k].detach().cpu(), checkpoint['actor'][k]) for k in state):
        raise ValueError('First exact actor weights did not round-trip')
    optimizer.load_state_dict(checkpoint['optimizer'])
    if optimizer.state:
        raise ValueError('Initial Adam state contains an unregistered completed update')
    if set(packet['gradients']) != {name for name, _ in trainable}:
        raise ValueError('Exact accumulated first gradient parameter inventory differs')
    for name, parameter in trainable:
        value = packet['gradients'][name]
        parameter.grad = value.to(device=parameter.device).clone()
        if not torch.equal(parameter.grad.detach().cpu(), value):
            raise ValueError('Exact first-micro gradient restore differs')
    torch.set_rng_state(packet['random_state']['torch_CPU'])
    torch.cuda.set_rng_state_all(packet['random_state']['torch_CUDA'])
    if fingerprint(model, 'actor', base) != raw['actual_actor_state']:
        raise ValueError('First accepted greedy/teacher model state differs on exact restore')
    return raw['initial_actor_optimizer']


def publisher_update(model, optimizer, trainable, temporary, folder, episode,
                     cursor, before_state, base, rows):
    folder.mkdir()
    before = {name: p.detach().float().cpu().clone() for name, p in trainable} if episode == 1 else None
    norm = torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1., error_if_nonfinite=True)
    if not torch.isfinite(norm) or norm <= 0:
        raise ValueError('Actual full publisher gradient has no finite nonzero direction')
    clipped = gradient_state(temporary / ('publisher%d_clipped.pt' % episode), trainable, cursor, None)
    optimizer.step()
    witness = None
    if episode == 1:
        witness = first_optimizer_witness(folder / 'first_AdamW_witness.pt', before, clipped, trainable)
    after = fingerprint(model, 'actor', base)
    if after == before_state:
        raise ValueError('Actual complete publisher update changed no actor weights')
    checkpoint = recovery_checkpoint(temporary / ('publisher%d_actor_Adam.pt' % episode),
                                    model, optimizer, episode, dict(cursor=cursor, **rng()))
    save(folder / 'acceptance.json', dict(episode=episode, publisher=cursor['publisher'],
        actual_optimizer_updates=1, cursor=cursor, all_prescribed_micro=rows,
        before=before_state, after=after, unclipped_gradient_norm=float(norm),
        clipped_gradient=clipped, first_optimizer_witness=witness, checkpoint=checkpoint))
    optimizer.zero_grad(set_to_none=True)
    return identity(folder / 'acceptance.json'), checkpoint
