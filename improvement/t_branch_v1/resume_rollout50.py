"""Only unfinished source actions; adopt saved outputs and reconstruct sampling RNG."""
from fractions import Fraction

import torch

from actor_roles33 import activate_actor
from causal_policy32 import actual_allowed_states
from joint_rollout44 import run_case
from joint_rollout47 import evaluation_mode
from resume_rng50 import advance
from t_io import check, identity, read, save
from t_runtime39 import grammar


def prior_result(folder, case, rt, tokenizer, eos):
    path = folder / 'acceptance.json'
    if path.exists():
        accepted = read(path)
        raw = read(check(accepted['raw']))
        if raw['tokens'] != accepted['tokens'] or raw['prefix'] != case.values['input_ids'].shape[1]:
            raise ValueError('Accepted actual trajectory tokens/prefix differ')
        return accepted, identity(path)
    raw_path = folder / 'raw.json'
    if not raw_path.exists():
        return None, None
    raw = read(raw_path)
    request = read(folder / 'request.json')
    if request['CPU'] != case.CPU or raw['prefix'] != case.values['input_ids'].shape[1]:
        raise ValueError('Interrupted completed raw has a different actual input binding')
    tokens = raw['tokens']
    duration = Fraction(case.meta['window_end']) - Fraction(case.meta['window_start'])
    module = grammar()
    rule = module.make_prefix_constraint(tokenizer, case.values['input_ids'].shape[1], duration,
        candidate_token_ids=module.ascii_token_candidates(tokenizer), eos_token_ids=eos, allow_empty=True)
    allowed = actual_allowed_states(case.values['input_ids'], tokens, rule)
    text = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    segments, errors, warnings = rt.parse_segments(text, duration, allow_empty=True)
    if errors or segments is None or text != raw['text']:
        raise ValueError('Complete interrupted raw is not a valid original trajectory')
    row = dict(case=case.name, CPU=case.CPU, tokens=tokens, segments=segments, warnings=warnings,
        status='MODEL_OK' if segments else 'LEGAL_EMPTY', raw=identity(raw_path), allowed=allowed,
        source_start=case.meta['window_start'], source_end=case.meta['window_end'],
        acceptance_interrupted_after_complete_raw=True)
    payload_path = folder / 'allowed_scores.pt'
    if payload_path.exists():
        try:
            payload = torch.load(payload_path, map_location='cpu', weights_only=True)
        except (RuntimeError, EOFError):
            payload = None
        if payload is not None:
            if payload['tokens'] != tokens or payload['allowed'] != allowed:
                raise ValueError('Interrupted saved rollout score identity differs')
            row['allowed_scores'] = identity(payload_path)
    if 'allowed_scores' not in row:
        row['actual_rollout_scores_unavailable_due_timeout'] = True
    return row, identity(raw_path)


def rollout(model, processor, rt, source, old_episode, folder, sampling):
    folder.mkdir()
    evaluation_mode(model); activate_actor(model, 'actor')
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    vocabulary = model.get_base_model().lm_head.weight.shape[0]
    sampled, greedy, receipts = {}, {}, {}
    for case in source.cases:
        receipts[case.name] = {}
        for kind, sampling_options in [('greedy', None), ('sample', sampling)]:
            old_folder = old_episode / 'rollout' / (case.name + '_' + kind)
            result, adopted = prior_result(old_folder, case, rt, processor.tokenizer, eos)
            destination = folder / (case.name + '_' + kind)
            if result is None:
                result, ref = run_case(model, processor, rt, case, destination, sampling_options)
            else:
                destination.mkdir()
                if result['CPU'] != case.CPU or result['case'] != case.name:
                    raise ValueError('Old completed action has different actual source input')
                replay = advance(result, vocabulary) if kind == 'sample' else None
                result = dict(result, adopted_actual_output=adopted, RNG_reconstruction=replay)
                save(destination / 'acceptance.json', result)
                ref = identity(destination / 'acceptance.json')
            if kind == 'sample':
                sampled[case.name] = source.selection(case, result)
            else:
                greedy[case.name] = source.selection(case, result)
            receipts[case.name]['sampled' if kind == 'sample' else 'greedy'] = ref
            rng = destination / 'post_action_rng.pt'
            with rng.open('xb') as stream:
                torch.save(dict(CUDA=torch.cuda.get_rng_state_all(), CPU=torch.get_rng_state()), stream)
        print('REMAIN50_ACTION', source.sid, case.name, flush=True)
    return greedy, sampled, receipts
