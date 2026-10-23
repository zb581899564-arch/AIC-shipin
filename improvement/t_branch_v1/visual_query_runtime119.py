"""Actual visual features become private queries; no token identifiers or new head."""
from contextlib import contextmanager
from pathlib import Path
import time

import torch

import shared_visual_query118 as shared
from native_render100 import render
from parallel_query105 import select
from t_io import identity, read, save


def tensors(path, packet):
    value = {key: item.detach().cpu() if torch.is_tensor(item) else item for key, item in packet.items()}
    with path.open('xb') as stream:
        torch.save(value, stream)
    return identity(path)


@contextmanager
def attention_witness(path):
    """Record two actual branches of the first layer, without another forward."""
    original = shared.shared_attention; result = {}; calls = 0
    def traced(query, key, value, prefix_key, prefix_value, scaling):
        nonlocal calls
        output = original(query, key, value, prefix_key, prefix_value, scaling)
        if calls == 0:
            result['file'] = tensors(path, dict(query=query[[0, 31]], key=key[[0, 31]],
                value=value[[0, 31]], prefix_key=prefix_key, prefix_value=prefix_value,
                scaling=scaling, actual_attention_output=output[[0, 31]], native_query_indices=[0, 31]))
        calls += 1
        return output
    shared.shared_attention = traced
    try:
        yield result
    finally:
        shared.shared_attention = original
        if shared.shared_attention is not original:
            raise ValueError('Own-process witness kernel wrapper was not restored')


def prefix(model, core, values, proof):
    packet = {}; row = read(proof['path'])
    def capture(module, args, kwargs):
        embeddings = kwargs['inputs_embeds']; mask = kwargs['visual_pos_masks']
        expected = values['input_ids'] == row['video_token_id']
        if mask is None or not torch.equal(mask, expected):
            raise ValueError('Actual decoder visual mask does not match accepted video placeholders')
        pooled = shared.pool_native_visual(embeddings, mask, values['video_grid_thw'], row['spatial_merge_size'])
        packet.update(pooled=pooled, video_features=embeddings[mask],
                      positions=kwargs['position_ids'], visual_token_positions=mask.nonzero())
    hook = core.model.language_model.register_forward_pre_hook(capture, with_kwargs=True)
    started = time.monotonic()
    try:
        output = model(**values, use_cache=True, logits_to_keep=1, return_dict=True)
    finally:
        hook.remove()
    torch.cuda.synchronize()
    if output.past_key_values is None or output.rope_deltas is None or output.rope_deltas.shape != (1, 1):
        raise ValueError('Actual model did not return one complete native prefix cache and RoPE delta')
    length = values['input_ids'].shape[1]
    if any(layer.keys.shape[0] != 1 or layer.keys.shape[-2] != length for layer in output.past_key_values.layers):
        raise ValueError('Actual shared layer cache is missing/truncated or has another prefix batch')
    packet.update(cache=output.past_key_values, rope_deltas=output.rope_deltas,
                  prefix_tokens=length, prefill_seconds=time.monotonic() - started)
    return packet


def choose(model, core, packet, values, proof, code, source, case, signature, folder, temporary):
    folder.mkdir(); row = read(proof['path'])
    question = core.get_input_embeddings()(torch.tensor([code['Question']], device=packet['pooled'].device))
    queries = torch.stack((packet['pooled'].to(question.dtype), question.expand(32, -1)), dim=1)
    start_position = packet['prefix_tokens'] + int(packet['rope_deltas'][0, 0])
    positions = torch.arange(start_position, start_position + 2, device=queries.device).view(1, 1, 2).expand(3, 32, 2)
    started = time.monotonic()
    with attention_witness(temporary / (case.name + '_attention.pt')) as attention:
        result = shared.branch_forward(core.model.language_model, packet['cache'], queries,
                                       positions, values['attention_mask'])
    hidden = result.last_hidden_state[:, -1, :]
    logits = core.lm_head(hidden)
    torch.cuda.synchronize(); seconds = time.monotonic() - started
    if logits.ndim != 2 or logits.shape[0] != 32 or not torch.isfinite(logits).all():
        raise ValueError('Actual complete original-LM readout is incomplete/nonfinite')
    binary = logits[:, [code['Yes'], code['No']]].float()
    selected = select(binary, code)
    raw = folder / 'raw.json'
    save(raw, dict(actual_input=proof, actual_GPU_signature=signature, model_role='original_default_TIME',
        binary_logits=binary.cpu().tolist(), selected_token_ids=[code['Yes'] if v else code['No'] for v in selected],
        query_positions_identical_per_branch=True, actual_prefix_forwards=1,
        actual32_branch_decoder_forwards=1, local_shift16_rows_alias=list(range(16, 32)) + list(range(16)),
        branch_seconds=seconds, prefill_seconds=packet['prefill_seconds'], no_arbitrary_cell_tokens=True))
    accepted = folder / 'acceptance.json'
    save(accepted, dict(case=case.name, source=source.sid, CPU=proof, raw=identity(raw),
        **render(source, case, row['source_native_cells'], selected)))
    permanent = tensors(folder / 'projected_witness.pt', dict(pooled_FP32=packet['pooled'],
        original_Question_embedding=question, actual_query_embeddings=queries, actual_query_positions=positions,
        actual_final_hidden=hidden, actual_original_LM_rows=core.lm_head.weight[[code['Yes'], code['No']]],
        binary_logits=binary, grid=values['video_grid_thw'], rope_deltas=packet['rope_deltas']))
    visual = tensors(temporary / (case.name + '_visual.pt'), dict(video_features=packet['video_features'],
        actual_prefix_position_ids=packet['positions'], visual_token_positions=packet['visual_token_positions']))
    full = tensors(temporary / (case.name + '_full_vocabulary.pt'), dict(logits=logits))
    save(folder / 'witnesses.json', dict(permanent=permanent, temporary_visual=visual,
        temporary_attention=attention['file'], temporary_full_vocab=full, actual_output=identity(accepted),
        prefix_tokens=packet['prefix_tokens'], measured_model_hidden=hidden.shape[-1],
        no_new_classifier_weights=True, actual_shared_prefix_readonly=True))
    return dict(output=identity(accepted), witnesses=identity(folder / 'witnesses.json'),
                measured_prefill_seconds=packet['prefill_seconds'], measured_branch_seconds=seconds)
