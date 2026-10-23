"""First real Torch/PEFT/loss/actual-token codec CPU gate, never an8B forward."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path
import traceback

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from native_actor98 import attach_native_actor
from native_codec98 import NativeChoices, causal_history, preference_loss, vocabulary
from summary_target_contract88 import TinyModel
from t_io import ROOT, identity, read, save

OUT = ROOT / 'native_action_contract98'


def loss_contract():
    torch.manual_seed(7398)
    logits = torch.randn(32, 2, requires_grad=True)
    a = torch.arange(32, dtype=torch.float64) / 1000
    b = torch.flip(a, dims=[0]); a[5] = 0; b[5] = 0
    loss, _ = preference_loss(logits, a, b, .5); loss.backward()
    z = logits.detach().numpy().astype(np.float64)
    normal = z.max(axis=1, keepdims=True)
    logp = z - normal - np.log(np.exp(z - normal).sum(axis=1, keepdims=True))
    expected = -.5 * np.sum(a.numpy() * logp[:, 0] + b.numpy() * logp[:, 1])
    grad = .5 * ((a.numpy() + b.numpy())[:, None] * np.exp(logp) - np.stack([a.numpy(), b.numpy()], axis=1))
    if not math.isclose(float(loss), float(expected), rel_tol=1e-6, abs_tol=1e-7):
        raise ValueError('Independent native preference CPU reduction differs')
    if not np.allclose(logits.grad.numpy(), grad, atol=1e-7, rtol=1e-6) or logits.grad[5].any():
        raise ValueError('Native coefficient gradients or UNKNOWN-zero mask differ')
    return dict(checks=3, independent_FP64_loss_and_gradient=True, unknown_zero_gradient=True)


def clone_contract():
    model = get_peft_model(TinyModel(), LoraConfig(r=16, lora_alpha=32,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'], lora_dropout=0., bias='none'))
    with torch.no_grad():
        for name, p in model.named_parameters():
            if '.lora_B.default.' in name:
                p.fill_(.02)
    before = {n: p.detach().clone() for n, p in model.named_parameters()}
    trainable = attach_native_actor(model)
    if len(trainable) != 288 or sum(p.numel() for _, p in trainable) != 18432:
        raise ValueError('Actual144 tiny language projections or clone parameter shape differ')
    sample = torch.randn(2, 4); projection = model.base_model.model.model.language_model.layers[0].self_attn.q_proj
    model.set_adapter('default'); model.eval(); control = projection(sample).detach()
    from actor_roles33 import activate_actor
    activate_actor(model, 'actor'); model.eval(); copied = projection(sample)
    if not torch.equal(control, copied.detach()):
        raise ValueError('Copied native role changed actual tiny forward before training')
    loss = copied.square().mean() + 1e-4 * sum(p.square().sum() for _, p in trainable)
    loss.backward()
    if any(p.grad is not None for n, p in model.named_parameters() if n in before):
        raise ValueError('New role gradient reached a protected original parameter')
    torch.optim.AdamW([p for _, p in trainable], lr=5e-5, weight_decay=0.).step()
    if any(not torch.equal(before[n], p) for n, p in model.named_parameters() if n in before):
        raise ValueError('Actual new native-role step changed protected original values')
    return dict(checks=4, actual_tiny_tensors=288, synthetic_parameters=18432,
                original_TIME_copy_exact=True, original_forward_equal=True, original_values_unchanged=True)


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    feasibility = read(ROOT / 'native_action_feasibility97/completion.json')
    if feasibility['all_native_windows'] != 217 or feasibility['all_original_reviewers'] != 86:
        raise ValueError('Complete original native-unit reference evidence absent')
    protocol = read(Path(__file__).with_name('native_action_protocol98.json'))
    if sum(protocol['components'].values()) != 8869330010:
        raise ValueError('Prospective full-method component budget differs')
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    eos = [tokenizer.eos_token_id]; code = vocabulary(tokenizer, eos)
    prefix = torch.tensor([[1, 2, 3]], dtype=torch.long)
    tokens = [token for anchor in code['anchors'] for token in [anchor, code['No']]] + [code['EOS']]
    grammar = NativeChoices(3, code)
    if grammar.parse(tokens).any():
        raise ValueError('Successful allNo must remain a legal empty')
    for invalid in [tokens[:-1], tokens + [code['EOS']], [code['Yes']] + tokens[1:]]:
        try:
            grammar.parse(invalid)
        except ValueError:
            continue
        raise ValueError('An actual native action failure became successful/empty')
    teacher = causal_history(prefix, tokens, code)
    if (teacher['input_ids'][0, 3:].tolist() != tokens[:-1]
            or teacher['logits_to_keep'] != list(range(3, 67, 2))):
        raise ValueError('Actual on-policy anchored choice causal positions differ')
    loss = loss_contract(); role = clone_contract()
    if torch.cuda.is_initialized():
        raise ValueError('New native-action contract initialized CUDA')
    save(OUT / 'completion.json', dict(state='FIRST_NATIVE_ACTION_CODEC_LOSS_ROLE_CPU_PASS',
        protocol=identity(Path(__file__).with_name('native_action_protocol98.json')),
        measured_native_feasibility=identity(ROOT / 'native_action_feasibility97/completion.json'),
        actual_token_codec=code, actual_tokenizer_only_no8B=True,
        finite_codec_checks=5, loss=loss, role=role, no_actual8B_forward_or_training=True,
        code={n: identity(Path(__file__).with_name(n)) for n in ['native_action_contract98.py',
              'native_actor98.py', 'native_codec98.py']},
        next='First all417 label-free native-action text/transform inputs and source/publisher/source-global coefficient binding, then actual live model/first-micro cost admission. No automatic training from CPU pass.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
