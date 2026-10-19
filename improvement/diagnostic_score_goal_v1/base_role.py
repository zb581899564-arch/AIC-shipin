"""Explicit restoration of PEFT trainability flags after frozen BASE use.

The caller persists each generation INSIDE this scope, before PEFT's exit
can restore enabled adapters and mutate their requires_grad flags.
"""
from contextlib import contextmanager


@contextmanager
def frozen_original_base(model,expected_layers=144):
    parameters=list(model.parameters());flags=[bool(p.requires_grad) for p in parameters]
    layers=[m for m in model.modules() if hasattr(m,'disable_adapters') and hasattr(m,'lora_A')]
    if len(layers)!=expected_layers or any(flags) or any(bool(m.disable_adapters) for m in layers):
        raise ValueError('Exact enabled/frozen original TIME state required before BASE scope')
    try:
        with model.disable_adapter():
            if not all(bool(m.disable_adapters) for m in layers):
                raise ValueError('Actual BASE role did not disable all TIME layers')
            yield
    finally:
        for p,flag in zip(parameters,flags):p.requires_grad_(flag)
        if any(bool(m.disable_adapters) for m in layers) or [bool(p.requires_grad) for p in parameters]!=flags:
            raise ValueError('Original enabled/frozen TIME state not restored after BASE scope')
