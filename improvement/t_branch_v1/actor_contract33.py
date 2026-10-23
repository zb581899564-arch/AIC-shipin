"""Installed-PEFT CPU role/gradient checks and exact original TIME parameter header."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import math
from pathlib import Path
import traceback

import torch
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
from safetensors import safe_open

from actor_roles33 import activate_actor, adapter_equal, frozen_reference
from t_io import ROOT, WORK, identity, read, save

OUT = ROOT / 'actor_contract33'


class TinyAttention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.q_proj = torch.nn.Linear(4, 4, bias=False)
        self.v_proj = torch.nn.Linear(4, 4, bias=False)

    def forward(self, values):
        return self.q_proj(values) + self.v_proj(values)


def actual_peft_checks():
    torch.manual_seed(7333)
    model = get_peft_model(TinyAttention(), LoraConfig(r=2, lora_alpha=4,
        target_modules=['q_proj', 'v_proj'], lora_dropout=0.0, bias='none'))
    original = OUT / 'synthetic_reference'
    model.save_pretrained(original, safe_serialization=True)
    model.load_adapter(str(original), adapter_name='actor', is_trainable=True)
    if not adapter_equal(model):
        raise ValueError('Actual installed PEFT actor initialization differs from reference')
    trainable = activate_actor(model, 'actor')
    before = {name: value.detach().clone() for name, value in model.named_parameters()}
    values = torch.randn(3, 4)
    with frozen_reference(model, 'actor'):
        with torch.no_grad():
            expected = model(values).detach()
        if model.active_adapter != 'default' or any(p.requires_grad for p in model.parameters()):
            raise ValueError('Actual reference role is not fully frozen')
    actual = model(values)
    if not torch.equal(actual.detach(), expected):
        raise ValueError('Identical actual actor/reference adapters change forward output')
    actual.square().sum().backward()
    if not any(parameter.grad is not None and torch.count_nonzero(parameter.grad) for _, parameter in trainable):
        raise ValueError('Actual installed PEFT actor gradient is empty')
    if any(parameter.grad is not None for name, parameter in model.named_parameters()
           if '.actor.' not in name):
        raise ValueError('Reference or base received an actor gradient')
    try:
        with frozen_reference(model, 'actor'):
            raise RuntimeError('deliberate role-restore test')
    except RuntimeError as error:
        if str(error) != 'deliberate role-restore test':
            raise
    if model.active_adapter != 'actor' or not all(parameter.requires_grad for _, parameter in trainable):
        raise ValueError('Reference exception did not restore actor role')
    if any(not torch.equal(before[name], parameter) for name, parameter in model.named_parameters()):
        raise ValueError('Backward-only role contract changed a parameter')
    model.zero_grad(set_to_none=True)
    return dict(actor_equal_reference_at_initialization=True, identical_forward=True,
                actor_nonzero_gradient_only=True, exception_restores_actor=True,
                optimizer_updates=0, synthetic_parameters=sum(p.numel() for p in model.parameters()))


def original_header():
    run = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    config = read(run / 'b_score_aligned_package_v4/config.json')
    adapter = Path(config['b_adapter']) / 'adapter_model.safetensors'
    with safe_open(str(adapter), framework='pt', device='cpu') as stream:
        count = sum(math.prod(stream.get_slice(key).get_shape()) for key in stream.keys())
        tensors = len(stream.keys())
    actual = 8782459120 + count + 98329
    if tensors != 288 or actual > 9000000000:
        raise ValueError('Original saved TIME header/actor+reference+semantic budget differs')
    return dict(original_TIME_adapter_parameters=count, saved_tensors=tensors,
                original_BASE_TIME=8782459120, frozen_semantic_head=98329,
                actual_shared_base_two_adapters_and_head_parameters=actual,
                original_saved_adapter=identity(adapter),
                full_live8B_parameter_measurement_still_required=True)


def main():
    OUT.mkdir()
    result = actual_peft_checks()
    header = original_header()
    save(OUT / 'completion.json', dict(state='PASS_INSTALLED_PEFT_CPU_ROLE_CONTRACT_AND_TIME_HEADER',
        role_checks=result, actual_saved_header=header, actual8B_model_calls=0,
        CUDA_initialized=torch.cuda.is_initialized(), no_training_or_quality_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
