"""Independent local visual queries over one read-only full-context KV prefix."""
from contextlib import contextmanager
from types import MethodType

import torch


def repeat_heads(value, groups):
    batch, heads, length, width = value.shape
    if groups == 1:
        return value
    return value[:, :, None].expand(batch, heads, groups, length, width).reshape(
        batch, heads * groups, length, width)


def shared_attention(query, key, value, prefix_key, prefix_value, scaling):
    """Exact attention without copying the full prefix for every query branch."""
    batch, heads, length, width = query.shape
    if (prefix_key.shape[0] != 1 or prefix_value.shape != prefix_key.shape
            or key.shape != value.shape or key.shape[0] != batch
            or key.shape[-2:] != (length, width) or heads % key.shape[1]
            or prefix_key.shape[1] != key.shape[1] or prefix_key.shape[-1] != width):
        raise ValueError('One shared prefix and complete independent query groups required')
    groups = heads // key.shape[1]
    dtype = torch.float64 if query.dtype == torch.float64 else torch.float32
    q = query.to(dtype)
    k, v = repeat_heads(key, groups).to(dtype), repeat_heads(value, groups).to(dtype)
    pk = repeat_heads(prefix_key, groups)[0].to(dtype)
    pv = repeat_heads(prefix_value, groups)[0].to(dtype)
    # Head-major BMM avoids materializing batch32 copies of every prefix K/V.
    head_query = q.permute(1, 0, 2, 3).reshape(heads, batch * length, width)
    prefix_scores = torch.bmm(head_query, pk.transpose(1, 2)) * scaling
    prefix_scores = prefix_scores.reshape(heads, batch, length, -1).permute(1, 0, 2, 3)
    local_scores = torch.matmul(q, k.transpose(-1, -2)) * scaling
    causal = torch.ones((length, length), dtype=torch.bool, device=query.device).tril()
    local_scores = local_scores.masked_fill(~causal, float('-inf'))
    scores = torch.cat((prefix_scores, local_scores), dim=-1)
    probability = torch.softmax(scores, dim=-1)
    prefix_length = prefix_key.shape[-2]
    head_probability = probability[..., :prefix_length].permute(1, 0, 2, 3).reshape(
        heads, batch * length, prefix_length)
    prefix_output = torch.bmm(head_probability, pv).reshape(heads, batch, length, width).permute(1, 0, 2, 3)
    local_output = torch.matmul(probability[..., prefix_length:], v)
    return (prefix_output + local_output).to(query.dtype).transpose(1, 2).contiguous()


def cache_signature(cache):
    def version(tensor):
        try:
            return tensor._version
        except RuntimeError:
            return None  # Inference tensors have no version counter.
    return tuple((tuple(v.shape), tuple(v.stride()), str(v.dtype), str(v.device), v.data_ptr(), version(v))
                 for layer in cache.layers for v in (layer.keys, layer.values))


@contextmanager
def independent_attention(text_model, prefix_cache):
    """Only this instance's branch attention changes, and is always restored."""
    from transformers.models.qwen3_vl.modeling_qwen3_vl import apply_rotary_pos_emb
    if text_model.is_gradient_checkpointing:
        raise ValueError('This prototype requires an ordinary differentiable read-only prefix graph')
    signature = cache_signature(prefix_cache)
    original = [(layer.self_attn, layer.self_attn.forward) for layer in text_model.layers]
    if len(prefix_cache.layers) != len(original):
        raise ValueError('Complete original layer prefix cache required')

    def branch_forward(module, hidden_states, position_embeddings, attention_mask,
                       past_key_values=None, cache_position=None, **kwargs):
        if past_key_values is not prefix_cache or module.attention_dropout != 0:
            raise ValueError('Unexpected cache or stochastic attention in independent branches')
        shape = hidden_states.shape[:-1]
        heads = (*shape, -1, module.head_dim)
        query = module.q_norm(module.q_proj(hidden_states).view(heads)).transpose(1, 2)
        key = module.k_norm(module.k_proj(hidden_states).view(heads)).transpose(1, 2)
        value = module.v_proj(hidden_states).view(heads).transpose(1, 2)
        query, key = apply_rotary_pos_emb(query, key, *position_embeddings)
        layer = prefix_cache.layers[module.layer_idx]
        output = shared_attention(query, key, value, layer.keys, layer.values, module.scaling)
        return module.o_proj(output.reshape(*shape, -1).contiguous()), None

    try:
        for module, _ in original:
            module.forward = MethodType(branch_forward, module)
        yield
    finally:
        for module, forward in original:
            module.forward = forward
        if cache_signature(prefix_cache) != signature:
            raise ValueError('Independent query branches mutated the accepted prefix cache')


def branch_forward(text_model, prefix_cache, queries, position_ids, prefix_mask):
    batch, length, _ = queries.shape
    prefix_length = prefix_cache.get_seq_length()
    if (length != 2 or prefix_mask.shape != (1, prefix_length) or not prefix_mask.bool().all()
            or position_ids.shape != (3, batch, length)
            or not torch.equal(position_ids, position_ids[:, :1].expand_as(position_ids))):
        raise ValueError('Exactly two local tokens and identical positions per independent branch required')
    mask = torch.ones((batch, prefix_length + length), dtype=prefix_mask.dtype, device=queries.device)
    cache_position = torch.arange(prefix_length, prefix_length + length, device=queries.device)
    with independent_attention(text_model, prefix_cache):
        return text_model(inputs_embeds=queries, attention_mask=mask, position_ids=position_ids,
            past_key_values=prefix_cache, cache_position=cache_position, use_cache=True, return_dict=True)


def pool_native_visual(embeddings, visual_mask, grid, spatial_merge_size, expected_temporal=32):
    if embeddings.ndim != 3 or embeddings.shape[0] != 1 or visual_mask.shape != embeddings.shape[:2]:
        raise ValueError('One complete real multimodal prefix and exact video mask required')
    if grid.shape != (1, 3) or spatial_merge_size <= 0:
        raise ValueError('Only one actual video and measured positive spatial merge supported')
    temporal, height, width = map(int, grid[0].tolist())
    if temporal != expected_temporal or height % spatial_merge_size or width % spatial_merge_size:
        raise ValueError('Measured temporal-pair grid/merge does not match the registered source cells')
    spatial = (height // spatial_merge_size) * (width // spatial_merge_size)
    if int(visual_mask.sum()) != temporal * spatial:
        raise ValueError('Actual embedded video tokens cannot be assigned exactly to measured temporal groups')
    feature = embeddings[visual_mask].reshape(temporal, spatial, embeddings.shape[-1])
    return feature.float().mean(dim=1)
