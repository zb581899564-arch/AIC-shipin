"""Fixed native temporal visibility; no learned head, score cutoff or token ID."""
from contextlib import contextmanager

import torch

import shared_visual_query118 as shared


def native_visibility(video_mask, temporal=32):
    if video_mask.ndim != 2 or video_mask.shape[0] != 1 or video_mask.dtype != torch.bool:
        raise ValueError('One exact original video placeholder mask required')
    positions = video_mask[0].nonzero().flatten()
    if not len(positions) or len(positions) % temporal:
        raise ValueError('Actual video tokens cannot be divided into complete native temporal groups')
    groups = positions.reshape(temporal, -1)
    result = (~video_mask).expand(temporal, -1).clone()
    result[torch.arange(temporal, device=result.device)[:, None], groups] = True
    return result


def localized_attention(query, key, value, prefix_key, prefix_value, scaling, visibility):
    batch, heads, length, width = query.shape
    if (visibility.dtype != torch.bool or visibility.shape != (batch, prefix_key.shape[-2])
            or prefix_key.shape[0] != 1 or prefix_key.shape != prefix_value.shape
            or key.shape != value.shape or key.shape[0] != batch or heads % key.shape[1]
            or key.shape[-2:] != (length, width) or prefix_key.shape[1] != key.shape[1]
            or not visibility.any(dim=1).all()):
        raise ValueError('Exact per-branch native visibility and complete shared prefix required')
    groups = heads // key.shape[1]
    dtype = torch.float64 if query.dtype == torch.float64 else torch.float32
    q = query.to(dtype)
    k, v = shared.repeat_heads(key, groups).to(dtype), shared.repeat_heads(value, groups).to(dtype)
    pk = shared.repeat_heads(prefix_key, groups)[0].to(dtype)
    pv = shared.repeat_heads(prefix_value, groups)[0].to(dtype)
    head_query = q.permute(1, 0, 2, 3).reshape(heads, batch * length, width)
    prefix_scores = torch.bmm(head_query, pk.transpose(1, 2)) * scaling
    prefix_scores = prefix_scores.reshape(heads, batch, length, -1).permute(1, 0, 2, 3)
    prefix_scores = prefix_scores.masked_fill(~visibility[:, None, None, :], float('-inf'))
    local_scores = torch.matmul(q, k.transpose(-1, -2)) * scaling
    causal = torch.ones((length, length), dtype=torch.bool, device=q.device).tril()
    local_scores = local_scores.masked_fill(~causal, float('-inf'))
    probability = torch.softmax(torch.cat((prefix_scores, local_scores), dim=-1), dim=-1)
    prefix_length = prefix_key.shape[-2]
    head_probability = probability[..., :prefix_length].permute(1, 0, 2, 3).reshape(
        heads, batch * length, prefix_length)
    prefix_output = torch.bmm(head_probability, pv).reshape(heads, batch, length, width).permute(1, 0, 2, 3)
    local_output = torch.matmul(probability[..., prefix_length:], v)
    return (prefix_output + local_output).to(query.dtype).transpose(1, 2).contiguous()


@contextmanager
def localized_kernel(visibility):
    original = shared.shared_attention
    def operation(query, key, value, prefix_key, prefix_value, scaling):
        return localized_attention(query, key, value, prefix_key, prefix_value, scaling, visibility)
    shared.shared_attention = operation
    try:
        yield
    finally:
        shared.shared_attention = original
        if shared.shared_attention is not original:
            raise ValueError('Own-process localized kernel wrapper was not restored')
