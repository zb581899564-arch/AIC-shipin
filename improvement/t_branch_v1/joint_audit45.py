"""First independent CPU replay of whole-source rewards, scalar losses and gradients."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
import math

import numpy as np
import torch
from safetensors.torch import load_file
from transformers import AutoTokenizer

from joint_data44 import load_sources
from t_io import ROOT, WORK, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'joint_train44'


def agreement(mask, source):
    values = []
    for review in source.reviews:
        proposed = mask & review.observed_task_domain
        reference = review.selected & review.observed_task_domain
        denominator = int(proposed.sum()) + int(reference.sum())
        values.append(2 * int((proposed & reference).sum()) / denominator if denominator else 0.)
    return math.fsum(values) / len(values)


def trajectory(ref, case, source, rt, tokenizer):
    row = read(check(ref))
    if row['CPU'] != case.CPU or row['case'] != case.name:
        raise ValueError('Accepted trajectory changed actual CPU/source identity')
    raw = read(check(row['raw']))
    tokens = raw.get('tokens', raw.get('token_ids'))
    if row['tokens'] != tokens:
        raise ValueError('Actual raw and accepted generated token suffix differ')
    text = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    segments, errors, _ = rt.parse_segments(text,
        Fraction(case.meta['window_end']) - Fraction(case.meta['window_start']), allow_empty=True)
    if errors or segments != row['segments']:
        raise ValueError('Independent original parser/token replay differs')
    if 'allowed_scores' in row:
        payload = torch.load(check(row['allowed_scores']), map_location='cpu', weights_only=True)
        if payload['allowed'] != row['allowed'] or payload['tokens'] != tokens:
            raise ValueError('Actual rollout action proof differs')
        for ids, scores, token in zip(payload['allowed'], payload['scores'], tokens):
            if token not in ids or len(ids) != len(scores) or not torch.isfinite(scores).all():
                raise ValueError('Invalid actual allowed rollout action')
    return row, source.selection(case, row)


def scalar_loss(ref, advantage, beta):
    row = read(check(ref))
    if row['advantage'] != advantage or row['kl_weight'] != beta:
        raise ValueError('Replay coefficient differs from complete-source counterfactual')
    payload = torch.load(check(row['projected']), map_location='cpu', weights_only=True)
    total_logp, divergences = 0., []
    for actor, reference, ids, token in zip(payload['actor'], payload['reference'], payload['allowed'], payload['tokens']):
        a, b = actor.numpy().astype(np.float64), reference.numpy().astype(np.float64)
        a -= a.max(); b -= b.max()
        a -= math.log(float(np.exp(a).sum())); b -= math.log(float(np.exp(b).sum()))
        total_logp += a[ids.index(token)]
        divergences.append(float((np.exp(a) * (a - b)).sum()))
    kl = math.fsum(divergences) / len(divergences)
    expected = -advantage * total_logp + beta * kl
    for actual, desired in [(row['loss'], expected), (row['sequence_logp'], total_logp), (row['mean_allowed_KL'], kl)]:
        if not math.isfinite(actual) or abs(actual - desired) > 2e-5 * (1 + abs(desired)):
            raise ValueError('Independent float64 allowed-policy scalar replay differs')
    return dict(loss=expected, sequence_logp=total_logp, mean_KL=kl)


def gradient(ref):
    path = check(ref['file'])
    total, nonzero = 0., 0
    with np.load(path, allow_pickle=False) as archive:
        if len(archive.files) != len(ref['parameter_names']) or len(archive.files) != 288:
            raise ValueError('Actual actor gradient inventory differs')
        for name in archive.files:
            value = archive[name]
            if value.dtype != np.float32 or not np.isfinite(value).all():
                raise ValueError('Persisted actor gradient nonfinite or wrong dtype')
            total += float(np.square(value.astype(np.float64)).sum())
            nonzero += int(np.count_nonzero(value) > 0)
    norm = math.sqrt(total)
    if abs(norm - ref['norm_float64']) > 1e-9 * (1 + norm):
        raise ValueError('Independent saved gradient norm differs')
    return dict(norm=norm, nonzero_tensors=nonzero)


def main():
    result = read(OUT / 'gpu_completion.json')
    protocol = read(check(result['protocol']))
    rt = runtime()
    run = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    tokenizer = AutoTokenizer.from_pretrained(read(run / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    sources = load_sources(None, None, protocol, load_values=False)
    audits, updates, signaled = [], 0, set()
    if len(result['episodes']) != protocol['method']['source_episodes']:
        raise ValueError('Final manifest lacks a complete registered source episode')
    for index, (ref, sid) in enumerate(zip(result['episodes'], protocol['method']['episode_source_order']), 1):
        episode = read(check(ref)); source = sources[sid]
        if episode['index'] != index or episode['source'] != sid:
            raise ValueError('Actual episode source order differs')
        records = read(check(episode['trajectories']))
        if set(records) != {case.name for case in source.cases}:
            raise ValueError('Whole source missing an accepted trajectory')
        sampled, greedy = {}, {}
        for case in source.cases:
            _, greedy[case.name] = trajectory(records[case.name]['greedy'], case, source, rt, tokenizer)
            _, sampled[case.name] = trajectory(records[case.name]['sampled'], case, source, rt, tokenizer)
        whole = np.logical_or.reduce(list(sampled.values()))
        reward = agreement(whole, source)
        original = read(check(episode['reward']))
        if abs(reward - original['sampled_source']['mean_f1']) > 1e-12:
            raise ValueError('Independent complete-source union reward differs')
        advantages = {}
        for name in sampled:
            other = np.zeros_like(whole)
            for key, value in sampled.items():
                other |= greedy[name] if key == name else value
            advantages[name] = reward - agreement(other, source)
            if abs(advantages[name] - original['per_window'][name]['advantage']) > 1e-12:
                raise ValueError('Independent overlap-preserving counterfactual reward differs')
        signal = any(value != 0 for value in advantages.values())
        if episode['optimizer_updates'] != int(signal):
            raise ValueError('Zero-signal source falsely counted as an optimizer update')
        losses = [scalar_loss(ref, advantages[read(check(ref))['case']], .02 / len(source.cases))
                  for ref in episode['replays']]
        gradients = [gradient(row) for row in episode['gradients']]
        if signal:
            if len(losses) != len(source.cases) or len(gradients) != len(source.cases):
                raise ValueError('Optimizer used an incomplete source replay')
            clipped = gradient(episode['clipped_gradient'])
            if not 0 < clipped['norm'] <= 1.00001 or not gradients[-1]['nonzero_tensors']:
                raise ValueError('Actual clipped gradient is missing or exceeds registered norm')
            signaled.add(sid)
        elif losses or gradients or episode['actor_before'] != episode['actor_after']:
            raise ValueError('No-signal episode changed actual actor')
        updates += int(signal)
        check(episode['recovery_checkpoint'])
        audits.append(dict(episode=index, source=sid, native_whole_source_F1=reward,
            windows=len(source.cases), real_optimizer_updates=int(signal), losses=losses,
            gradient_snapshots=len(gradients)))
        print('JOINT45_CPU_EPISODE_PASS', index, sid, flush=True)
    final = result['final_adapter']
    weights = load_file(str(check(final['weights'])), device='cpu')
    last = read(check(result['episodes'][-1]))
    checkpoint = torch.load(check(last['recovery_checkpoint']), map_location='cpu', weights_only=False)
    if set(weights) != set(checkpoint['actor']) or any(not torch.equal(weights[key], checkpoint['actor'][key]) for key in weights):
        raise ValueError('Final eligible adapter differs from final episode recovery state')
    if result['actual_optimizer_updates'] != updates or result['actual_complete_parameters'] != 8797892873:
        raise ValueError('Actual final model/update count differs')
    if updates and any(int(row['step']) != updates for row in checkpoint['optimizer']['state'].values()):
        raise ValueError('Actual AdamW state step count differs')
    save(OUT / 'independent_CPU_audit.json', dict(state='PASS_FIRST_NATIVE_REWARD_TOKEN_LOSS_GRADIENT_AND_FINAL_REPLAY',
        episodes=audits, actual_optimizer_updates=updates, signaled_sources=sorted(signaled),
        final_adapter_matches_last_episode=True, no_quality_or_official_score_claim=True))


if __name__ == '__main__':
    main()
