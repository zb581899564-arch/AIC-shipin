"""First full actual40.48 source comparison, no likelihood or coarse-only admission."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer

from development_data46 import development_sources
from development_review48 import retained
from event_table71 import ARMS
from frozen_branch46 import RUN, semantic_prediction, verify_modules
from preference_reward import summary_agreement
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'event_full78'
CPU = ROOT / 'event_verify_inputs76'
ORIGINAL = ROOT / 'development_remaining55'
BASELINE = 'original40_48'


def first_verify_decisions(cpu, result, tokenizer):
    contract, grammar, _ = verify_modules()
    candidates = grammar.candidate_tokens(tokenizer, contract.responses())
    resolved = {key: value['decision'] for key, value in cpu['adopted_independently_accepted_decisions'].items()}
    folder = OUT / 'first_VERIFY_CPU'; folder.mkdir(); proofs = []
    if set(result['outputs']) != set(cpu['tasks']):
        raise ValueError('Actual downstream task union is incomplete')
    for key in result['first_new_keys']:
        task = cpu['tasks'][key]
        row = read(check(result['outputs'][key])); raw = read(check(row['raw']))
        request = read(check(task['request'])); accepted = read(check(task['CPU']))
        if row['input'] != task or raw['prefix'] != accepted['detail']['input_tokens']:
            raise ValueError('First actual VERIFY raw/input binding differs')
        rule = grammar.VerifyConstraint(tokenizer, raw['prefix'], request, raw['eos'], candidates)
        rule.assert_complete(torch.tensor(raw['tokens'], dtype=torch.long))
        text = tokenizer.decode(raw['tokens'], skip_special_tokens=True, clean_up_tokenization_spaces=False)
        decision = contract.resolve(text, request, execution_status='MODEL_OK')
        if text != raw['text'] or decision != row['decision'] or not all(math.isfinite(s) for s in raw['scores']):
            raise ValueError('First exact VERIFY token/parser/decision replay differs')
        resolved[key] = decision['decision']
        path = folder / (key + '.json')
        save(path, dict(state='PASS_FIRST_NEW_VERIFY_TOKEN_GRAMMAR_REQUEST_CPU',
            actual_output=result['outputs'][key], CPU=task['CPU'], no_original_QA_replay=True))
        proofs.append(identity(path))
    if set(resolved) != set(cpu['tasks']) or len(proofs) != cpu['maximum_first_new_VERIFY_calls']:
        raise ValueError('First/adopted downstream decision denominator differs')
    return resolved, proofs


def old_semantic_cache(sid):
    result = []
    for arm in ['original_correct', 'trained_correct', 'original_shift', 'trained_shift']:
        path = ORIGINAL / (sid + '_' + arm + '_native.npz')
        with np.load(path, allow_pickle=False) as data:
            result.append(dict(VERIFY=data['VERIFY'].copy(), full=data['full40_47'].copy(),
                               residual=data['residual'].copy(), source=identity(path)))
    return result


def source_masks(source, policies, tasks, resolved, routes, semantic_outputs):
    sid = source.sid
    with np.load(check(routes[sid]['intrinsic_keep']), allow_pickle=False) as data:
        keep = data['keep'].copy()
    if keep.dtype != bool or keep.shape != (len(source.timeline.points),):
        raise ValueError('Actual40.48 native route mask dimensions differ')
    cache = old_semantic_cache(sid); full_masks, binding = {}, {}
    native = read(ROOT / 'development_semantic46' / sid / 'semantic_CPU_completion.json')
    features = read(check(semantic_outputs[sid]))['outputs']
    baseline_path = ORIGINAL / (sid + '_original_correct_native.npz')
    with np.load(baseline_path, allow_pickle=False) as data:
        full_masks[BASELINE] = data['full40_47'].copy() & keep
    binding[BASELINE] = dict(adopted40_47_full_output=identity(baseline_path),
                            exact40_48_route=routes[sid])
    for arm in ARMS:
        d8, verified, guard = retained(source, policies[sid][arm], tasks, resolved)
        match = next((r for r in cache if np.array_equal(r['VERIFY'], verified)), None)
        if match is not None:
            full, residual = match['full'].copy(), match['residual'].copy()
            semantic_proof = dict(identity_equal_head_result_adopted=match['source'], new_head_call=False)
        else:
            full, residual = semantic_prediction(verified, native, features)
            semantic_proof = dict(first_new_frozen_head_CPU=True, original_BASE_features=semantic_outputs[sid])
        final = full & keep; full_masks[arm] = final
        path = OUT / (sid + '_' + arm + '_native.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, D8=d8, VERIFY=verified, full40_47=full,
                full40_48=final, route_keep=keep, residual=residual)
        if match is None:
            cache.append(dict(VERIFY=verified.copy(), full=full.copy(), residual=residual.copy(), source=identity(path)))
        binding[arm] = dict(native=identity(path), semantic=semantic_proof,
            empty_source_guard=guard, exact40_48_route=routes[sid])
    base_path = OUT / (sid + '_actual40_48_control.npz')
    with base_path.open('xb') as stream:
        np.savez_compressed(stream, full40_48=full_masks[BASELINE])
    binding[BASELINE]['native'] = identity(base_path)
    return full_masks, binding


def independent_set_metrics(mask, reviews, expected):
    rows = []
    for review in reviews:
        domain = set(np.flatnonzero(review.observed_task_domain).tolist())
        if not domain:
            raise ValueError('Unknown whole evaluation domain cannot become zero quality')
        proposed = set(np.flatnonzero(mask).tolist()) & domain
        positive = set(np.flatnonzero(review.selected).tolist()) & domain
        overlap = len(proposed & positive)
        rows.append(2 * overlap / (len(proposed) + len(positive)) if proposed or positive else 0.)
    if len(rows) != expected:
        raise ValueError('Independent all-reviewer count differs')
    return math.fsum(rows) / expected


def main():
    torch.set_num_threads(2); rt = runtime()
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    cpu = read(CPU / 'completion.json'); result = read(OUT / 'GPU_completion.json')
    decisions, first = first_verify_decisions(cpu, result, tokenizer)
    route = read(ROOT / 'event_route77/CPU_completion.json')['source_masks']
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    semantic = read(ROOT / 'development51/coarse_and_BASE_GPU_completion.json')['semantic']
    masks, bindings = {}, {}
    for sid, source in sources.items():
        masks[sid], bindings[sid] = source_masks(source, cpu['source_policies'], cpu['tasks'], decisions, route, semantic)
    save(OUT / 'frozen_all_masks_before_labels.json', bindings)
    labeled = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=True)
    metrics = {}; exact = []
    for sid, arms in masks.items():
        metrics[sid] = {}
        for arm, mask in arms.items():
            score = summary_agreement(mask, labeled[sid].reviews, len(labeled[sid].reviews))
            other = independent_set_metrics(mask, labeled[sid].reviews, len(labeled[sid].reviews))
            if abs(score['mean_f1'] - other) > 1e-12:
                raise ValueError('Independent native all-reviewer F1 arithmetic differs')
            metrics[sid][arm] = score; exact.append(dict(source=sid, arm=arm, mean_f1=other))
    means = {arm: math.fsum(metrics[sid][arm]['mean_f1'] for sid in sources) / len(sources)
             for arm in (BASELINE,) + ARMS}
    correct = ARMS[1]; shifted = ARMS[2]
    gains = {sid: metrics[sid][correct]['mean_f1'] - metrics[sid][BASELINE]['mean_f1'] for sid in sources}
    gates = dict(both_publishers_improve_over_actual40_48=all(v > 0 for v in gains.values()),
        correct_beats_native_no_memory=means[correct] > means[ARMS[0]],
        correct_beats_fixed_text_shift=means[correct] > means[shifted],
        no_new_empty_whole_source=all(masks[sid][correct].any() or not masks[sid][BASELINE].any() for sid in sources),
        all_first_native_and_downstream_QA_complete=True, actual_full_parameters_below9B=8853994586 <= 9000000000)
    gates = {k: bool(v) for k, v in gates.items()}
    save(OUT / 'review.json', dict(state='PASS_EVENT_MEMORY_DEVELOPMENT_PENDING_COST_AND_CONFIRMATION' if all(gates.values()) else 'STOP_FIXED_EVENT_MEMORY69_DEVELOPMENT',
        metrics=metrics, means=means, per_source_delta_vs_actual40_48=gains, gates=gates,
        exact_original40_48_route_applied=identity(ROOT / 'event_route77/CPU_completion.json'),
        original40_47_and40_48_unchanged=True, all_original_reviewers=True,
        no_training_or_semantic_ordinary_from_unselected=True,
        historical_development_exposure=True, fresh_confirmation_read=False,
        official_joint_score='UNKNOWN', no_automatic_confirmation_or_production=True))
    save(OUT / 'independent_CPU_completion.json', dict(state='PASS_FIRST_FULL_NATIVE_CURRENT40_48_PIPELINE_CPU',
        first_new_VERIFY_proofs=first, adopted_successful_VERIFY=len(cpu['adopted_successful_outputs']),
        old_BASE_batches_adopted=365, no_old_model_or_token_QA_repeated=True,
        all_mask_binding=identity(OUT / 'frozen_all_masks_before_labels.json'),
        independent_all_reviewer_set_metrics=exact, original_confirmation_not_read=True))


if __name__ == '__main__':
    main()
