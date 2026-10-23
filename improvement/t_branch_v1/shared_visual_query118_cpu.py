"""First actual HF CPU prototype: shared KV, exact gradients and query isolation."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import copy
import inspect
import traceback

import torch
import transformers
from transformers.models.qwen3_vl import modeling_qwen3_vl as module
from transformers.models.qwen3_vl.configuration_qwen3_vl import Qwen3VLTextConfig

from shared_visual_query118 import branch_forward, pool_native_visual, repeat_heads, shared_attention
from t_io import ROOT, identity, read, save

OUT = ROOT / 'shared_visual_query118_CPU'


def concatenated_attention(q, k, v, pk, pv, scaling):
    batch, heads, length, _ = q.shape
    groups = heads // k.shape[1]
    key = torch.cat((repeat_heads(pk, groups).expand(batch, -1, -1, -1), repeat_heads(k, groups)), dim=-2)
    value = torch.cat((repeat_heads(pv, groups).expand(batch, -1, -1, -1), repeat_heads(v, groups)), dim=-2)
    score = torch.matmul(q, key.transpose(-1, -2)) * scaling
    prefix = pk.shape[-2]
    mask = torch.cat((torch.ones((length, prefix), dtype=torch.bool),
                      torch.ones((length, length), dtype=torch.bool).tril()), dim=-1)
    score = score.masked_fill(~mask, float('-inf'))
    return torch.matmul(torch.softmax(score, dim=-1), value).transpose(1, 2).contiguous()


def kernel_contract():
    torch.manual_seed(74118)
    shapes = [(32, 4, 2, 8), (32, 2, 2, 8), (32, 2, 2, 8), (1, 2, 9, 8), (1, 2, 9, 8)]
    actual = [torch.randn(shape, dtype=torch.float64, requires_grad=True) for shape in shapes]
    expected = [v.detach().clone().requires_grad_(True) for v in actual]
    left = shared_attention(*actual, 8 ** -.5)
    right = concatenated_attention(*expected, 8 ** -.5)
    weights = torch.randn_like(left)
    grad_left = torch.autograd.grad((left * weights).mean(), actual)
    grad_right = torch.autograd.grad((right * weights).mean(), expected)
    error = float((left - right).abs().max())
    gradient = max(float((a - b).abs().max()) for a, b in zip(grad_left, grad_right))
    if error > 1e-12 or gradient > 1e-12:
        raise ValueError('FP64 shared-prefix kernel/complete QKV derivatives differ from concatenation')
    return dict(output_max_abs_error=error, all_QKV_prefix_and_query_gradient_max_abs_error=gradient,
                branches=32, grouped_query_heads=True)


def tiny_config():
    config = Qwen3VLTextConfig(vocab_size=128, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, head_dim=8,
        max_position_embeddings=128, rope_scaling=dict(rope_type='default', mrope_section=[2, 1, 1]),
        attention_dropout=0.)
    config._attn_implementation = 'eager'
    return config


def hf_contract(with_deepstack):
    torch.manual_seed(74118 + int(with_deepstack))
    model = module.Qwen3VLTextModel(tiny_config()).float().eval()
    reference = copy.deepcopy(model)
    prefix = torch.randn(1, 7, 32, requires_grad=True)
    queries = torch.randn(32, 2, 32, requires_grad=True)
    prefix_ref = prefix.detach().clone().requires_grad_(True)
    queries_ref = queries.detach().clone().requires_grad_(True)
    extras, full_extras = {}, {}
    if with_deepstack:
        mask = torch.tensor([[False, True, True, True, True, False, False]])
        features = [torch.randn(4, 32) for _ in range(2)]
        extras = dict(visual_pos_masks=mask, deepstack_visual_embeds=features)
        full_extras = dict(visual_pos_masks=torch.cat((mask.expand(32, -1), torch.zeros((32, 2), dtype=torch.bool)), 1),
            deepstack_visual_embeds=[v.repeat(32, 1) for v in features])
    initial = model(inputs_embeds=prefix, attention_mask=torch.ones((1, 7)), use_cache=True,
                    return_dict=True, **extras)
    positions = torch.arange(7, 9).view(1, 1, 2).expand(3, 32, 2)
    shared = branch_forward(model, initial.past_key_values, queries, positions, torch.ones((1, 7))).last_hidden_state
    combined = torch.cat((prefix_ref.expand(32, -1, -1), queries_ref), 1)
    plain = reference(inputs_embeds=combined, attention_mask=torch.ones((32, 9)),
        use_cache=False, return_dict=True, **full_extras).last_hidden_state[:, -2:]
    output_error = float((shared - plain).detach().abs().max())
    witness = torch.randn_like(shared)
    (shared * witness).mean().backward(); (plain * witness).mean().backward()
    errors = [float((prefix.grad - prefix_ref.grad).abs().max()),
              float((queries.grad - queries_ref.grad).abs().max())]
    for (name, left), (other, right) in zip(model.named_parameters(), reference.named_parameters()):
        if name != other or (left.grad is None) != (right.grad is None):
            raise ValueError('Shared-prefix gradient parameter/domain differs')
        if left.grad is not None:
            errors.append(float((left.grad - right.grad).abs().max()))
    if output_error > 5e-5 or max(errors) > 5e-5:
        raise ValueError('Actual HF tiny whole-model output/gradient differs from32 independent contexts')
    return model, initial.past_key_values, queries.detach(), positions, dict(
        output_max_abs_error=output_error, all_parameter_and_input_gradient_max_abs_error=max(errors),
        actual_HF_Qwen3VLTextModel=True, original_DeepStack_preserved=with_deepstack)


def isolation_contract(model, cache, queries, positions):
    with torch.no_grad():
        first = branch_forward(model, cache, queries, positions, torch.ones((1, 7))).last_hidden_state
        changed = queries.clone(); changed[0] += 3
        second = branch_forward(model, cache, changed, positions, torch.ones((1, 7))).last_hidden_state
        order = torch.arange(31, -1, -1)
        permuted = branch_forward(model, cache, queries[order], positions, torch.ones((1, 7))).last_hidden_state[order]
    leakage = float((first[1:] - second[1:]).abs().max())
    changed_branch = float((first[0] - second[0]).abs().max())
    equivariance = float((first - permuted).abs().max())
    if leakage != 0 or changed_branch == 0 or equivariance > 1e-6:
        raise ValueError('Query branches leak into each other or follow absolute branch order')
    return dict(changed_branch_max_abs_change=changed_branch, other31_branches_max_abs_change=leakage,
                branch_permutation_max_abs_error=equivariance)


def pool_contract():
    embedding = torch.arange(1 * 30 * 8, dtype=torch.float32).reshape(1, 30, 8)
    mask = torch.zeros((1, 30), dtype=torch.bool); mask[0, 2:26] = True
    actual = pool_native_visual(embedding, mask, torch.tensor([[4, 4, 6]]), 2, expected_temporal=4)
    expected = torch.stack([embedding[0, 2 + j*6:2 + (j+1)*6].double().mean(0) for j in range(4)]).float()
    if not torch.equal(actual, expected):
        raise ValueError('Measured temporal grid/merge pooling differs from independent original-token slices')
    try:
        pool_native_visual(embedding, mask, torch.tensor([[3, 4, 6]]), 2, expected_temporal=4)
    except ValueError:
        return dict(exact_toy_temporal_group_pool=True, incompatible_grid_rejected=True)
    raise ValueError('Incompatible native observation mapping was silently repaired')


def main():
    OUT.mkdir(); torch.set_num_threads(2)
    terminal = read(ROOT / 'query_binding117/completion.json')
    if terminal['state'] != 'FIRST_ALL50_QUERY_BINDING_CPU_AND_CAUSAL_DIAGNOSIS_COMPLETE':
        raise ValueError('Complete actual query-codec diagnosis required before new visual-query feasibility')
    save(OUT / 'registration.json', dict(completed_causal_diagnosis=identity(ROOT / 'query_binding117/completion.json'),
        scope='New visual-content query/read-only shared prefix CPU feasibility only, no8B or training admission',
        transformers_version=transformers.__version__, actual_model_implementation=identity(inspect.getfile(module)),
        no_source_or_confirmation_labels_read=True,
        code={n: identity(ROOT / 'code' / n) for n in ['shared_visual_query118.py', 'shared_visual_query118_cpu.py']}))
    kernel = kernel_contract(); model, cache, queries, positions, first = hf_contract(False)
    _, _, _, _, deepstack = hf_contract(True)
    isolation = isolation_contract(model, cache, queries, positions)
    pool = pool_contract()
    if torch.cuda.is_initialized():
        raise ValueError('New mathematical/actual-HF CPU prototype initialized CUDA')
    save(OUT / 'completion.json', dict(state='FIRST_SHARED_PREFIX_VISUAL_QUERY_CPU_FEASIBILITY_PASS_NOT8B',
        kernel=kernel, actual_HF_model=first, actual_DeepStack_model=deepstack,
        independent_query_isolation=isolation, native_visual_pool=pool,
        new_learned_model_parameters=0, actual8B_calls=0, actual_training_updates=0,
        old105_STOP_unchanged=True, no_source_quality_or_training_or_production_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes=True))
        raise
