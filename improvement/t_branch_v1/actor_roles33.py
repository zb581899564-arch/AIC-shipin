"""Explicit actor/reference roles: one shared frozen base and two small adapters."""
from contextlib import contextmanager


def adapter_parameter(name, actor):
    return ('.lora_A.' + actor + '.' in name or '.lora_B.' + actor + '.' in name)


def activate_actor(model, actor):
    model.set_adapter(actor)
    trainable = []
    for name, parameter in model.named_parameters():
        active = adapter_parameter(name, actor)
        parameter.requires_grad_(active)
        if active:
            if '.visual.' in name:
                raise ValueError('TIME actor must not train the visual backbone')
            trainable.append((name, parameter))
    if not trainable or model.active_adapter != actor:
        raise ValueError('Actor role activation has no actual trainable TIME adapter')
    return trainable


@contextmanager
def frozen_reference(model, actor, reference='default'):
    """Restore actor flags even if reference forward fails; no BASE disable_adapter()."""
    if model.active_adapter != actor:
        raise ValueError('Reference context must start from the explicit actor role')
    training = model.training
    try:
        model.set_adapter(reference)
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        model.eval()
        yield
    finally:
        activate_actor(model, actor)
        model.train(training)


def adapter_equal(model, left='default', right='actor'):
    import torch
    from peft import get_peft_model_state_dict
    a = get_peft_model_state_dict(model, adapter_name=left)
    b = get_peft_model_state_dict(model, adapter_name=right)
    return set(a) == set(b) and all(torch.equal(a[key], b[key]) for key in a)
