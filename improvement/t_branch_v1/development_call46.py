"""Role-aware development generation on a bound real or counterfactual input."""
from fractions import Fraction
import time

import torch

from causal_policy32 import actual_allowed_states
from t_io import identity, save
from t_runtime39 import grammar


def generate(model, processor, rt, case, folder, role, input_proof):
    folder.mkdir()
    model.set_adapter(role)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    prefix = case.values['input_ids'].shape[1]
    duration = Fraction(case.meta['window_end']) - Fraction(case.meta['window_start'])
    module = grammar()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    constraint = module.make_prefix_constraint(processor.tokenizer, prefix, duration,
        candidate_token_ids=module.ascii_token_candidates(processor.tokenizer), eos_token_ids=eos, allow_empty=True)
    save(folder / 'request.json', dict(actual_model_role=role, original_CPU=case.CPU,
        actual_input_proof=input_proof, labels_in_input=False, do_sample=False, max_new_tokens=256))
    started = time.monotonic()
    with torch.inference_mode():
        output = model.generate(**{k: v.cuda() if torch.is_tensor(v) else v for k, v in case.values.items()},
            do_sample=False, max_new_tokens=256, num_beams=1, repetition_penalty=1.0,
            prefix_allowed_tokens_fn=constraint, return_dict_in_generate=True, output_scores=True)
    torch.cuda.synchronize()
    tokens = output.sequences[0, prefix:].tolist()
    text = processor.tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    save(folder / 'raw.json', dict(tokens=tokens, text=text, prefix=prefix, eos=eos,
                                  seconds=time.monotonic() - started))
    allowed = actual_allowed_states(case.values['input_ids'], tokens, constraint)
    projected = [row[0, torch.tensor(ids, device=row.device)].detach().float().cpu()
                 for row, ids in zip(output.scores, allowed)]
    if len(projected) != len(tokens) or not all(torch.isfinite(row).all() for row in projected):
        raise ValueError('Development actual allowed generation scores invalid')
    path = folder / 'allowed.pt'
    with path.open('xb') as stream:
        torch.save(dict(scores=projected, allowed=allowed, tokens=tokens), stream)
    segments, errors, warnings = rt.parse_segments(text, duration, allow_empty=True)
    if segments is None or errors:
        raise ValueError('Development parser/model failure is not legal empty')
    result = dict(case=case.name, CPU=case.CPU, actual_input_proof=input_proof, model_role=role,
        raw=identity(folder / 'raw.json'), allowed_scores=identity(path), tokens=tokens,
        segments=segments, warnings=warnings, status='MODEL_OK' if segments else 'LEGAL_EMPTY',
        source_start=case.meta['window_start'], source_end=case.meta['window_end'])
    save(folder / 'acceptance.json', result)
    return result, identity(folder / 'acceptance.json')
