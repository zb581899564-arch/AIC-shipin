"""Same finite native-codec greedy call from one already transferred input."""
import time

import torch

from native_codec98 import NativeChoices
from native_prepared103 import unchanged
from native_render100 import render
from t_io import check, identity, read, save


def generate(model, tokenizer, source, case, proof, code, state, gpu, signature, snapshot, folder):
    row = read(check(proof))
    folder.mkdir()
    rule = NativeChoices(row['input_tokens'], code)
    model.eval()
    started = time.monotonic()
    with torch.inference_mode():
        result = model.generate(**gpu, do_sample=False, num_beams=1, max_new_tokens=65,
            repetition_penalty=1., use_cache=True, prefix_allowed_tokens_fn=rule,
            return_dict_in_generate=True, output_scores=True)
    tokens = result.sequences[0, row['input_tokens']:].tolist()
    selected = rule.parse(tokens)
    allowed, scores = [], []
    for index, score in enumerate(result.scores):
        domain = rule.allowed(tokens[:index])
        allowed.append(domain)
        projected = score[0, torch.tensor(domain, device=score.device)].detach().float().cpu()
        if not torch.isfinite(projected).all():
            raise ValueError('Actual shared-input native action logit is nonfinite')
        scores.append(projected.tolist())
    seconds = time.monotonic() - started
    unchanged(gpu, snapshot)
    path = folder / 'raw.json'
    save(path, dict(tokens=tokens, text=tokenizer.decode(tokens, skip_special_tokens=True,
        clean_up_tokenization_spaces=False), prefix=row['input_tokens'], codec=code,
        actual_input=proof, actual_GPU_signature=signature, actual_model_state=state,
        model_role='actor', allowed=allowed, allowed_logits=scores, seconds=seconds,
        shared_input_immutable_storage_verified=True, no_human_reference_in_input=True))
    accepted = dict(case=case.name, source=source.sid, CPU=proof, original_CPU=case.CPU,
        raw=identity(path), physical_alias=None, physical_input_key=row['physical_input_key'],
        actual_model_state=state, model_role='actor',
        **render(source, case, row['source_native_cells'], selected))
    save(folder / 'acceptance.json', accepted)
    return identity(folder / 'acceptance.json'), seconds
