"""Reproduce additional-adapter load rounding using installed PEFT on a BF16 base."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import traceback

import torch
from peft import LoraConfig, get_peft_model

from actor_contract33 import TinyAttention
from actor_copy41 import exact_actor_copy
from actor_roles33 import adapter_equal
from t_io import ROOT, save

OUT = ROOT / 'actor_contract41'


def main():
    OUT.mkdir()
    model = get_peft_model(TinyAttention().to(torch.bfloat16), LoraConfig(r=2, lora_alpha=4,
        target_modules=['q_proj', 'v_proj'], lora_dropout=0.0, bias='none'))
    with torch.no_grad():
        for name, value in model.named_parameters():
            if 'lora_' in name:
                value.copy_(torch.arange(value.numel(), dtype=value.dtype).reshape(value.shape) / 1000.7 + 0.012345)
    path = OUT / 'synthetic_original'
    model.save_pretrained(path, safe_serialization=True)
    trainable, evidence = exact_actor_copy(model, path)
    if not adapter_equal(model) or not trainable:
        raise ValueError('Exact copied mixed-precision adapter contract failed')
    values = torch.arange(12, dtype=torch.bfloat16).reshape(3, 4) / 10
    model.eval()
    actual = model(values).detach()
    model.set_adapter('default')
    expected = model(values).detach()
    if not torch.equal(actual, expected):
        raise ValueError('Identical copied adapter changed actual mixed-precision forward')
    save(OUT / 'completion.json', dict(state='PASS_MIXED_PRECISION_ACTUAL_DEFAULT_COPY',
        actual_installed_PEFT_evidence=evidence, initial_forward_exact=True,
        actual8B_calls=0, optimizer_updates=0,
        original8B_load_failure_explanation_still_requires_live_dtype_record=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
