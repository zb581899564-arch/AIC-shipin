"""Actual32 native choices from one shared multimodal forward; no generated history."""
import time

import torch

from native_render100 import render
from parallel_query105 import select
from t_io import check, identity, read, save


def forward(model, gpu, proof, code):
    row = read(check(proof))
    positions = row['query_positions']
    if len(positions) != 32 or positions != list(range(row['prefix_tokens_before_queries'] + 1,
                                                     row['input_tokens'], 2)):
        raise ValueError('Actual parallel query positions differ from complete independent suffix')
    result = model(**gpu, logits_to_keep=positions, use_cache=False, return_dict=True)
    logits = result.logits[0].float()
    if logits.ndim != 2 or logits.shape[0] != 32 or not torch.isfinite(logits).all():
        raise ValueError('Actual parallel native forward is incomplete or nonfinite')
    return logits, logits[:, [code['Yes'], code['No']]]


def accepted(source, case, proof, code, state, role, binary, signature, seconds, folder):
    row = read(check(proof))
    selected = select(binary, code)
    raw = folder / 'raw.json'
    save(raw, dict(actual_input=proof, actual_GPU_signature=signature,
        actual_model_state=state, model_role=role, query_code=code,
        query_positions=row['query_positions'], binary_logits=binary.detach().float().cpu().tolist(),
        selected_token_ids=[code['Yes'] if v else code['No'] for v in selected],
        actual_forward_seconds=seconds, actual_forward_calls=1,
        no_autoregressive_generation_or_previous_answers=True, no_human_reference_in_input=True))
    path = folder / 'acceptance.json'
    save(path, dict(case=case.name, source=source.sid, CPU=proof, original_CPU=case.CPU,
        raw=identity(raw), physical_alias=None, physical_input_key=row['physical_input_key'],
        actual_model_state=state, model_role=role,
        **render(source, case, row['source_native_cells'], selected)))
    return identity(path)


def infer(model, source, case, proof, code, state, role, gpu, signature, folder):
    folder.mkdir()
    model.eval()
    started = time.monotonic()
    with torch.inference_mode():
        full, binary = forward(model, gpu, proof, code)
    elapsed = time.monotonic() - started
    result = accepted(source, case, proof, code, state, role, binary, signature, elapsed, folder)
    del full, binary
    return result, elapsed
