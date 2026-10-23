"""Initialize a second adapter from the actual inference adapter, without load rounding."""
import torch
from peft import get_peft_model_state_dict, set_peft_model_state_dict

from actor_roles33 import activate_actor, adapter_equal


def exact_actor_copy(model, adapter_path, actor='actor'):
    reference = get_peft_model_state_dict(model, adapter_name='default')
    before = {name: value.detach().clone() for name, value in reference.items()}
    model.load_adapter(str(adapter_path), adapter_name=actor, is_trainable=True)
    first = get_peft_model_state_dict(model, adapter_name=actor)
    if set(first) != set(before):
        raise ValueError('Additional adapter has a different tensor inventory')
    differences = [float((first[key].float() - before[key].float()).abs().max()) for key in before]
    dtypes = sorted({(str(before[key].dtype), str(first[key].dtype)) for key in before})
    # PEFT additional loading can copy saved FP32 values through a BF16 layer
    # before autocasting it back to FP32. Load the actual default values only
    # after the destination dtype has been established, then require exactness.
    set_peft_model_state_dict(model, before, adapter_name=actor)
    if not adapter_equal(model, right=actor):
        raise ValueError('Lossless actual reference-to-actor copy still differs')
    after = get_peft_model_state_dict(model, adapter_name='default')
    if any(not torch.equal(before[key], after[key]) for key in before):
        raise ValueError('Actual reference changed while initializing actor')
    trainable = activate_actor(model, actor)
    return trainable, dict(before_exact_copy_max_abs_error=max(differences), dtype_pairs=dtypes,
                           exact_actual_default_copy=True, reference_untouched=True,
                           adapter_tensors=len(before))
