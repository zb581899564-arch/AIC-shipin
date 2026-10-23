"""Frozen TIME generation from accepted native64 caches; empty is a successful action."""
from fractions import Fraction
import math
import time

import numpy as np
import torch

from prompt_contract13 import prompt_binding
from t_io import check, identity, read, save


def load_case(ref, rt, tokenizer):
    cpu = read(check(ref))
    meta = read(check(cpu['input']))
    with np.load(check(cpu['encoded']), allow_pickle=False) as archive:
        values = {key: torch.from_numpy(archive[key].copy()) for key in archive.files}
    values.update(cpu['non_tensor_inputs'])
    if rt.tensor_signature(values) != cpu['detail']['tensor_signature']:
        raise ValueError('Actual original TIME inputs differ from accepted CPU tensors')
    binding = prompt_binding(tokenizer, values['input_ids'], cpu['detail'], rt.EMPTY_PROMPT, 'COARSE')
    return cpu, meta, values, binding


def generate_case(model, processor, rt, cpu_ref, output_root):
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    cpu, meta, values, binding = load_case(cpu_ref, rt, processor.tokenizer)
    prefix = int(values['input_ids'].shape[1])
    lo, hi = Fraction(meta['window_start']), Fraction(meta['window_end'])
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    candidates = ascii_token_candidates(processor.tokenizer)
    grammar = make_prefix_constraint(processor.tokenizer, prefix, hi - lo,
        candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
    folder = output_root / meta['case_id']
    folder.mkdir()
    save(folder / 'request.json', dict(CPU=cpu_ref, prefix=prefix, prompt=binding,
                                      no_labels=True, source_id=meta['source_name']))
    started = time.monotonic()
    with torch.inference_mode():
        result = model.generate(**{k: v.cuda() if torch.is_tensor(v) else v for k, v in values.items()},
            do_sample=False, max_new_tokens=256, prefix_allowed_tokens_fn=grammar,
            return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    ids = result.sequences[0, prefix:]
    raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    scores = [float(score[0, int(token)]) for score, token in zip(result.scores, ids)]
    save(folder / 'raw.json', dict(raw=raw, token_ids=ids.tolist(),
        token_scores=[value if math.isfinite(value) else str(value) for value in scores],
        generation_seconds=time.monotonic() - started, prefix=prefix, eos=eos))
    if len(scores) != len(ids) or not all(math.isfinite(value) for value in scores):
        raise ValueError('Actual selected token scores invalid; not a legal empty result')
    grammar.assert_complete(ids)
    segments, errors, warnings = rt.parse_segments(raw, hi - lo, allow_empty=True)
    if segments is None or errors:
        raise ValueError('Actual original parser failed; never converted to empty')
    save(folder / 'acceptance.json', dict(case=meta['case_id'], segments=segments, warnings=warnings,
        status='LEGAL_EMPTY' if not segments else 'MODEL_OK', raw=identity(folder / 'raw.json'),
        source_start=str(lo), source_end=str(hi), CPU=cpu_ref))
    print('FIRST_COARSE25', meta['case_id'], len(segments), time.monotonic() - started, flush=True)
    return identity(folder / 'acceptance.json')
