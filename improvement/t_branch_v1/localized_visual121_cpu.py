"""First targeted local-visibility math/HF/actual25-prefix mask CPU checks."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import copy
import traceback

import numpy as np
import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as module

from localized_visual121 import localized_attention, localized_kernel, native_visibility
from shared_visual_query118 import branch_forward, repeat_heads
from shared_visual_query118_cpu import tiny_config
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'localized_visual121_CPU'


def reference(q, k, v, pk, pv, scaling, visibility):
    batch, heads, length, _ = q.shape
    groups = heads // k.shape[1]
    key = torch.cat((repeat_heads(pk, groups).expand(batch, -1, -1, -1), repeat_heads(k, groups)), -2)
    value = torch.cat((repeat_heads(pv, groups).expand(batch, -1, -1, -1), repeat_heads(v, groups)), -2)
    mask = torch.cat((visibility[:, None, :].expand(batch, length, -1),
        torch.ones((length, length), dtype=torch.bool).tril()[None].expand(batch, -1, -1)), -1)
    score = torch.matmul(q, key.transpose(-1, -2)) * scaling
    probability = torch.softmax(score.masked_fill(~mask[:, None], float('-inf')), -1)
    return torch.matmul(probability, value).transpose(1, 2).contiguous()


def kernel_check():
    torch.manual_seed(74121)
    shapes = [(32, 4, 2, 8), (32, 2, 2, 8), (32, 2, 2, 8), (1, 2, 69, 8), (1, 2, 69, 8)]
    actual = [torch.randn(shape, dtype=torch.float64, requires_grad=True) for shape in shapes]
    other = [v.detach().clone().requires_grad_(True) for v in actual]
    video = torch.zeros((1, 69), dtype=torch.bool); video[0, 2:66] = True
    visibility = native_visibility(video)
    left = localized_attention(*actual, 8 ** -.5, visibility)
    right = reference(*other, 8 ** -.5, visibility)
    weights = torch.randn_like(left)
    ga = torch.autograd.grad((left * weights).mean(), actual)
    gb = torch.autograd.grad((right * weights).mean(), other)
    difference = float((left - right).abs().max())
    gradient = max(float((a - b).abs().max()) for a, b in zip(ga, gb))
    order = torch.arange(31, -1, -1)
    moved = localized_attention(*(v[order] if i < 3 else v for i, v in enumerate(actual)),
                                8 ** -.5, visibility[order])[order]
    equivariance = float((moved - left).detach().abs().max())
    if difference > 1e-12 or gradient > 1e-12 or equivariance > 1e-12:
        raise ValueError('Native visibility kernel/value/gradient/permutation differs from independent reference')
    return dict(output_max_abs_error=difference, all_QKV_gradient_max_abs_error=gradient,
                branch_permutation_max_abs_error=equivariance, all32_native_groups_checked=True)


def hf_check():
    torch.manual_seed(74121)
    model = module.Qwen3VLTextModel(tiny_config()).float().eval(); other = copy.deepcopy(model)
    prefix = torch.randn(1, 7, 32, requires_grad=True); queries = torch.randn(32, 2, 32, requires_grad=True)
    p = prefix.detach().clone().requires_grad_(True); q = queries.detach().clone().requires_grad_(True)
    visibility = torch.ones((32, 7), dtype=torch.bool)
    visibility[:, 1:5] = False; visibility[torch.arange(32), 1 + torch.arange(32) % 4] = True
    cached = model(inputs_embeds=prefix, attention_mask=torch.ones((1, 7)), use_cache=True, return_dict=True)
    positions = torch.arange(7, 9).view(1, 1, 2).expand(3, 32, 2)
    with localized_kernel(visibility):
        result = branch_forward(model, cached.past_key_values, queries, positions, torch.ones((1, 7))).last_hidden_state
    mask = torch.ones((32, 1, 9, 9), dtype=torch.bool).tril()
    mask[:, 0, -2:, :7] = visibility[:, None, :]
    additive = torch.zeros(mask.shape).masked_fill(~mask, torch.finfo(torch.float32).min)
    plain = other(inputs_embeds=torch.cat((p.expand(32, -1, -1), q), 1), attention_mask=additive,
                  use_cache=False, return_dict=True).last_hidden_state[:, -2:]
    witness = torch.randn_like(result)
    (result * witness).mean().backward(); (plain * witness).mean().backward()
    error = float((result - plain).detach().abs().max())
    gradients = [float((prefix.grad - p.grad).abs().max()), float((queries.grad - q.grad).abs().max())]
    for (_, a), (_, b) in zip(model.named_parameters(), other.named_parameters()):
        if (a.grad is None) != (b.grad is None):
            raise ValueError('ActualHF localized attention changed gradient parameter domain')
        if a.grad is not None:
            gradients.append(float((a.grad - b.grad).abs().max()))
    if error > 5e-5 or max(gradients) > 5e-5:
        raise ValueError('Actual installedHF localized prefix/query output or complete gradient differs')
    return dict(actual_HF_output_max_abs_error=error, all_parameter_input_gradient_max_abs_error=max(gradients))


def actual_masks():
    inputs = read(ROOT / 'visual_query_inputs119/completion.json'); masks = {}
    for name, ref in inputs['inputs'].items():
        row = read(check(ref))
        with np.load(check(row['text']), allow_pickle=False) as data:
            video = torch.from_numpy(data['input_ids'] == row['video_token_id'])
        mask = native_visibility(video)
        positions = video[0].nonzero().flatten(); spatial = len(positions)//32
        matrix = mask[:, positions].reshape(32, 32, spatial).sum(-1)
        if not torch.equal(matrix, torch.eye(32, dtype=torch.long) * spatial) or not mask[:, ~video[0]].all():
            raise ValueError('Actual prefix mask does not retain exactly own visual pair and all nonvisual context')
        path = OUT / (name + '_visibility.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, visibility=mask.numpy())
        with np.load(path, allow_pickle=False) as data:
            if not np.array_equal(data['visibility'], mask.numpy()):
                raise ValueError('Actual native visibility mask serialization differs')
        masks[name] = dict(mask=identity(path), original_input=ref, shape=list(mask.shape),
            own_group_visual_tokens=spatial, shared_nonvisual_tokens=int((~video).sum()))
    return masks


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    old = read(ROOT / 'visual_query_fit120/completion.json')
    if old['state'] != 'FIRST_COMPLETE25_SHARED_VISUAL_FIT_DIAGNOSIS_AND_ALL_CPU_PASS':
        raise ValueError('Complete unmasked control/source diagnosis required')
    save(OUT / 'registration.json', dict(actual_unmasked_control=identity(ROOT / 'visual_query_fit120/completion.json'),
        scope='Fixed per-query own native visual temporal group plus all nonvisual context; no model or label use',
        no_new8B_training_or_quality_admission=True,
        code={n: identity(ROOT / 'code' / n) for n in ['localized_visual121.py', 'localized_visual121_cpu.py']}))
    kernel = kernel_check(); hf = hf_check(); masks = actual_masks()
    if len(masks) != 25 or torch.cuda.is_initialized():
        raise ValueError('All25 real prefix mask scope or CPU-only role differs')
    save(OUT / 'completion.json', dict(state='FIRST_LOCAL_NATIVE_VISIBILITY_CPU_MODEL_GRADIENT_AND25_MASKS_PASS',
        kernel=kernel, actual_HF=hf, masks=masks, source_labels_read=False,
        only_attention_visibility_changes_no_prompt_pool_or_weight_change=True,
        actual8B_calls=0, new_training_updates=0, no_scientific_quality_or_production_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
