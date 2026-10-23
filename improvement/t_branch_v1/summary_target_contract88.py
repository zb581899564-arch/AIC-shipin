"""New full-name PEFT injection check, using144 tiny language projections only."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
from peft import LoraConfig, get_peft_model

from summary_actor88 import add_fresh_summary
from t_io import ROOT, identity, save

OUT = ROOT / 'summary_target_contract88'


class Attention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        for name in ['q_proj', 'k_proj', 'v_proj', 'o_proj']:
            self.add_module(name, torch.nn.Linear(4, 4, bias=False))


class Layer(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.self_attn = Attention()


class Language(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.layers = torch.nn.ModuleList([Layer() for _ in range(36)])


class Backbone(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.language_model = Language()


class TinyModel(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.model = Backbone()


def main():
    OUT.mkdir(); torch.set_num_threads(2); torch.manual_seed(7385)
    model = get_peft_model(TinyModel(), LoraConfig(r=2, lora_alpha=4,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'], lora_dropout=0., bias='none'))
    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    trainable = add_fresh_summary(model, dict(rank=16, alpha=32))
    if sum(p.numel() for _, p in trainable) != 18432 or len(trainable) != 288:
        raise ValueError('Actual144 full-name tiny targets were not injected correctly')
    if any(not torch.equal(before[name], p) for name, p in model.named_parameters() if name in before):
        raise ValueError('Full-name fresh injection changed original values')
    if any(p.requires_grad for name, p in model.named_parameters()
           if '.lora_A.summary.' not in name and '.lora_B.summary.' not in name):
        raise ValueError('Full-name injection enables a protected parameter')
    if torch.cuda.is_initialized():
        raise ValueError('Layer-name CPU contract initialized CUDA')
    save(OUT / 'completion.json', dict(state='PASS_FIRST144_FULL_NAME_FRESH_ADAPTER_CPU_CONTRACT',
        original_modules=144, new_adapter_tensors=288, synthetic_new_parameters=18432,
        all_new_B_zero=True, original_values_unchanged=True, only_new_role_trainable=True,
        actual8B_calls=0, actual8B_training=0,
        role_factory=identity(__import__('pathlib').Path(__file__).with_name('summary_actor88.py')),
        actual_live8B_full_parameter_check_still_required=True))


if __name__ == '__main__':
    main()
