"""Fresh content adapter lifecycle; original BASE/TIME stay physically protected."""
import hashlib

import torch
from peft import LoraConfig, get_peft_model_state_dict, set_peft_model_state_dict
from peft.tuners.tuners_utils import BaseTunerLayer
from safetensors.torch import load_file

from actor_roles33 import activate_actor
from t_io import identity


def state_CPU(model):
    return {name: value.detach().contiguous().cpu()
            for name, value in get_peft_model_state_dict(model, adapter_name='summary').items()}


def digest(model):
    value = hashlib.sha256()
    for name, tensor in sorted(state_CPU(model).items()):
        value.update(name.encode()); value.update(str(tensor.dtype).encode())
        value.update(str(tuple(tensor.shape)).encode()); value.update(tensor.view(torch.uint8).numpy().tobytes())
    return value.hexdigest()


def add_fresh_summary(model, method):
    names = [name for name, module in model.base_model.model.named_modules()
             if isinstance(module, BaseTunerLayer)]
    suffixes = ('q_proj', 'k_proj', 'v_proj', 'o_proj')
    if (len(names) != 144 or any('.language_model.layers.' not in name
            or not name.endswith(suffixes) or '.visual.' in name for name in names)):
        raise ValueError('Actual original144 language-only qkvo targets differ')
    original = model.peft_config['default']
    config = LoraConfig(r=method['rank'], lora_alpha=method['alpha'], lora_dropout=0.,
        target_modules=names, bias='none', task_type=original.task_type, init_lora_weights=True)
    model.add_adapter('summary', config)
    trainable = activate_actor(model, 'summary')
    if any(bool(module.disable_adapters) or module.active_adapters != ['summary']
           for module in model.modules() if isinstance(module, BaseTunerLayer)):
        raise ValueError('Actual fresh content role was not enabled exclusively')
    for _, parameter in trainable:
        parameter.data = parameter.data.float()
    modules = dict(model.base_model.model.named_modules())
    expected = method['rank'] * sum(modules[name].in_features + modules[name].out_features for name in names)
    if (len(trainable) != 288 or sum(p.numel() for _, p in trainable) != expected
            or any(torch.count_nonzero(p).item() for name, p in trainable if '.lora_B.' in name)):
        raise ValueError('Actual fresh summary rank/inventory/zero-B initialization differs')
    return trainable


def final_save_reload(model, folder):
    expected = {name: value.clone() for name, value in state_CPU(model).items()}
    model.save_pretrained(str(folder), selected_adapters=['summary'], safe_serialization=True,
                          save_embedding_layers=False)
    path = folder / 'summary'; saved = load_file(str(path / 'adapter_model.safetensors'), device='cpu')
    if set(saved) != set(expected) or any(not torch.equal(saved[k], expected[k]) for k in saved):
        raise ValueError('Saved final FP32 summary adapter differs from actual trained values')
    model.set_adapter('default'); model.delete_adapter('summary')
    model.load_adapter(str(path), adapter_name='summary', is_trainable=False)
    # Same installed-PEFT additional-load rounding corrected by the verified85
    # explicit FP32 state assignment, never by accepting approximate weights.
    set_peft_model_state_dict(model, saved, adapter_name='summary')
    actual = state_CPU(model)
    if set(saved) != set(actual) or any(not torch.equal(saved[k], actual[k]) for k in saved):
        raise ValueError('Final actual8B summary save/reload was not lossless')
    return dict(adapter_directory=str(path), weights=identity(path / 'adapter_model.safetensors'),
                config=identity(path / 'adapter_config.json'), exact_FP32_save_reload=True)
