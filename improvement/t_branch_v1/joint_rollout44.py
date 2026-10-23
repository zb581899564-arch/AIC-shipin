"""Current-policy legal trajectories; only native caches and fixed prompt reach the model."""
from fractions import Fraction
import time

import torch

from causal_policy32 import actual_allowed_states
from t_io import identity, read, check, save
from t_runtime39 import grammar


def run_case(model, processor, rt, case, target, sampling):
    target.mkdir()
    prefix = case.values['input_ids'].shape[1]
    duration = Fraction(case.meta['window_end']) - Fraction(case.meta['window_start'])
    module = grammar()
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    rule = module.make_prefix_constraint(processor.tokenizer, prefix, duration,
        candidate_token_ids=module.ascii_token_candidates(processor.tokenizer), eos_token_ids=eos, allow_empty=True)
    options = dict(do_sample=False, max_new_tokens=256, num_beams=1, repetition_penalty=1.0)
    if sampling is not None:
        options.update(sampling)
    save(target / 'request.json', dict(CPU=case.CPU, model_role='actor', options=options,
        source_start=case.meta['window_start'], source_end=case.meta['window_end'], labels_in_input=False))
    started = time.monotonic()
    model.eval()
    with torch.inference_mode():
        output = model.generate(**{k: v.cuda() if torch.is_tensor(v) else v for k, v in case.values.items()},
            prefix_allowed_tokens_fn=rule, return_dict_in_generate=True, output_scores=True, **options)
    torch.cuda.synchronize()
    tokens = output.sequences[0, prefix:].tolist()
    text = processor.tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    save(target / 'raw.json', dict(tokens=tokens, text=text, prefix=prefix, eos=eos,
                                  seconds=time.monotonic() - started))
    allowed = actual_allowed_states(case.values['input_ids'], tokens, rule)
    if len(output.scores) != len(tokens):
        raise ValueError('Actual trajectory scores and sampled actions differ')
    scores = [score[0, torch.tensor(ids, device=score.device)].float().detach().cpu()
              for score, ids in zip(output.scores, allowed)]
    if not all(torch.isfinite(score).all() for score in scores):
        raise ValueError('An actual allowed rollout action has a nonfinite score')
    projected = target / 'allowed_scores.pt'
    with projected.open('xb') as stream:
        torch.save(dict(scores=scores, allowed=allowed, tokens=tokens), stream)
    segments, errors, warnings = rt.parse_segments(text, duration, allow_empty=True)
    if segments is None or errors:
        raise ValueError('Actual sampled trajectory invalid; never convert it to empty')
    result = dict(case=case.name, CPU=case.CPU, tokens=tokens, segments=segments,
        status='MODEL_OK' if segments else 'LEGAL_EMPTY', warnings=warnings,
        raw=identity(target / 'raw.json'), allowed_scores=identity(projected), allowed=allowed,
        temperature=options.get('temperature', 1.0), source_start=case.meta['window_start'], source_end=case.meta['window_end'])
    save(target / 'acceptance.json', result)
    return result, identity(target / 'acceptance.json')


def original_greedy(case, target):
    target.mkdir()
    original = read(check(case.original))
    raw = read(check(original['raw']))
    result = dict(original, tokens=raw['token_ids'], original_control_adopted=case.original)
    save(target / 'adoption.json', dict(original=case.original, CPU=case.CPU,
        reason='Current actor exactly equals frozen original TIME; original greedy options identical',
        new_model_call=False))
    save(target / 'acceptance.json', result)
    return result, identity(target / 'acceptance.json')
