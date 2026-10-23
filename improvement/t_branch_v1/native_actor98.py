"""Exact originalTIME initialization for one separate native-action actor role."""
from copy import deepcopy

import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict
from peft.tuners.tuners_utils import BaseTunerLayer

from actor_roles33 import activate_actor


def attach_native_actor(model):
    if set(model.peft_config) != {'default'}:
        raise ValueError('Only the protected originalTIME may initialize this new actor; no failed roles')
    names = [name for name, module in model.base_model.model.named_modules()
             if isinstance(module, BaseTunerLayer)]
    if (len(names) != 144 or any('.language_model.layers.' not in name
            or not name.endswith(('q_proj', 'k_proj', 'v_proj', 'o_proj')) for name in names)):
        raise ValueError('Actual original144 language-only projections differ')
    original = {name: value.detach().float().cpu().clone() for name, value in
                get_peft_model_state_dict(model, adapter_name='default').items()}
    method = deepcopy(model.peft_config['default'])
    if method.r != 16 or method.lora_alpha != 32:
        raise ValueError('Original TIME rank/alpha differ from this fixed clone profile')
    method.target_modules = set(names); method.lora_dropout = 0.; method.inference_mode = False
    model.add_adapter('actor', method)
    trainable = activate_actor(model, 'actor')
    for _, parameter in trainable:
        parameter.data = parameter.data.float()
    set_peft_model_state_dict(model, original, adapter_name='actor')
    actual = get_peft_model_state_dict(model, adapter_name='actor')
    if set(actual) != set(original) or any(not torch.equal(actual[k].detach().cpu(), original[k]) for k in original):
        raise ValueError('Native action actor was not an exact FP32 clone of originalTIME')
    activate_actor(model, 'actor')
    if len(trainable) != 288 or any(m.disable_adapters or m.active_adapters != ['actor']
                                   for m in model.modules() if isinstance(m, BaseTunerLayer)):
        raise ValueError('Actual native actor tensor inventory/exclusive role differs')
    return trainable
