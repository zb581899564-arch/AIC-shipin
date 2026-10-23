"""Recovery artifacts and exact final non-default adapter serialization/reload."""
import hashlib

import numpy as np
import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict
from safetensors.torch import load_file

from t_io import identity, save


def actor_digest(model):
    state = get_peft_model_state_dict(model, adapter_name='actor')
    digest = hashlib.sha256()
    for name, value in sorted(state.items()):
        value = value.detach().contiguous().cpu()
        digest.update(name.encode()); digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode()); digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def gradient_snapshot(path, trainable):
    arrays, norms = {}, []
    for index, (name, value) in enumerate(trainable):
        if value.grad is None or not torch.isfinite(value.grad).all():
            raise ValueError('Actor gradient missing or nonfinite before durable accumulation')
        array = value.grad.detach().float().cpu().numpy()
        arrays['p%03d' % index] = array
        norms.append(float(np.square(array.astype(np.float64)).sum()))
    with path.open('xb') as stream:
        np.savez_compressed(stream, **arrays)
    return dict(file=identity(path), parameter_names=[name for name, _ in trainable],
                norm_float64=float(np.sqrt(sum(norms))), cumulative=True)


def cpu_tree(value):
    if torch.is_tensor(value):
        return value.detach().cpu()
    if isinstance(value, dict):
        return {key: cpu_tree(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(cpu_tree(item) for item in value)
    return value


def recovery_checkpoint(path, model, optimizer, episode, rng):
    payload = dict(actor=cpu_tree(get_peft_model_state_dict(model, adapter_name='actor')),
                   optimizer=cpu_tree(optimizer.state_dict()), completed_episode=episode, rng=rng,
                   recovery_only_not_checkpoint_selection=True)
    with path.open('xb') as stream:
        torch.save(payload, stream)
    return identity(path)


def final_save_reload(model, folder):
    expected = cpu_tree(get_peft_model_state_dict(model, adapter_name='actor'))
    model.save_pretrained(str(folder), selected_adapters=['actor'], safe_serialization=True,
                          save_embedding_layers=False)
    adapter = folder / 'actor'
    saved = load_file(str(adapter / 'adapter_model.safetensors'), device='cpu')
    if set(saved) != set(expected) or any(not torch.equal(saved[key], expected[key]) for key in saved):
        raise ValueError('Final saved FP32 actor differs from actual trained values')
    model.delete_adapter('actor')
    model.load_adapter(str(adapter), adapter_name='actor', is_trainable=False)
    set_peft_model_state_dict(model, saved, adapter_name='actor')
    actual = get_peft_model_state_dict(model, adapter_name='actor')
    if set(actual) != set(saved) or any(not torch.equal(actual[key].detach().cpu(), saved[key]) for key in saved):
        raise ValueError('Lossless final actor reload differs')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return dict(adapter_directory=str(adapter), weights=identity(adapter / 'adapter_model.safetensors'),
                config=identity(adapter / 'adapter_config.json'), exact_fp32_roundtrip=True)
