"""Targeted installed-PEFT check: preserve tiny FP32 updates on final reload."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict

from actor_contract33 import TinyAttention
from actor_copy41 import exact_actor_copy
from joint_checkpoint44 import final_save_reload
from t_io import ROOT, save


def main():
    out = ROOT / 'joint_preflight44'
    out.mkdir()
    torch.manual_seed(7344)
    model = get_peft_model(TinyAttention().to(torch.bfloat16), LoraConfig(r=2,
        lora_alpha=4, target_modules=['q_proj', 'v_proj'], bias='none', lora_dropout=0))
    with torch.no_grad():
        for name, value in model.named_parameters():
            if 'lora_' in name:
                value.fill_(0.01234567)
    original = out / 'reference'
    model.save_pretrained(original, safe_serialization=True)
    before = {k: v.detach().clone() for k, v in get_peft_model_state_dict(model).items()}
    trainable, _ = exact_actor_copy(model, original)
    with torch.no_grad():
        for _, value in trainable:
            value.add_(1e-6)
    proof = final_save_reload(model, out / 'final')
    after = get_peft_model_state_dict(model, adapter_name='default')
    if any(not torch.equal(before[key], after[key]) for key in before):
        raise ValueError('Final reload changed original reference')
    actor = get_peft_model_state_dict(model, adapter_name='actor')
    if any(torch.equal(before[key], actor[key]) for key in before):
        raise ValueError('Tiny actual FP32 update lost on final reload')
    save(out / 'completion.json', dict(state='PASS_EXACT_FINAL_FP32_ACTOR_RELOAD',
        reference_unchanged=True, all_tiny_updates_retained=True, roundtrip=proof,
        actual8B_calls=0, optimizer_updates=0, CUDA_initialized=torch.cuda.is_initialized()))


if __name__ == '__main__':
    main()
