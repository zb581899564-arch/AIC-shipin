#!/usr/bin/env python3
"""Frozen round-5 dev gate. Every score here uses WEAK_TEACHER labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

R5 = Path('/home/inspur/aic_video_work/temporal_round5')
sys.path.insert(0, str(R5 / 'scripts'))
import temporal_common as tc


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def as_score(pred, gt, duration):
    return tc.interval_metrics(pred, gt, duration)['f1']


def rotate(segments, duration, offset):
    result = []
    for a, b in segments:
        length = b - a
        start = (a + offset) % duration
        if start + length <= duration:
            result.append([start, start + length])
        else:
            result.extend([[start, duration], [0.0, start + length - duration]])
    return result


def ci_by_group(diff_by_row, groups, replicates, seed):
    group_values = [statistics.mean(diff_by_row[k] for k in ks) for ks in groups.values()]
    rng = random.Random(seed)
    n = len(group_values)
    samples = sorted(sum(group_values[rng.randrange(n)] for _ in range(n)) / n
                     for _ in range(replicates))
    return [round(samples[int(0.025 * replicates)], 6),
            round(samples[int(0.975 * replicates)], 6)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--outputs', nargs='+', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    policy_path = R5 / 'audit/decision_policy_v2.json'
    policy = json.loads(policy_path.read_text())
    dev_path = R5 / 'data/dev.jsonl'
    assert sha256(dev_path) == policy['frozen_data']['dev_sha256']
    dev = tc.load_split('dev', R5)
    assert len(dev) == 90
    by_id = {r['sample_id']: r for r in dev}
    assert len(by_id) == len(dev)
    keys = [r['sample_id'] for r in dev]
    groups = defaultdict(list)
    for row in dev:
        groups[row['youtube_id']].append(row['sample_id'])
    assert len(groups) == 80
    scores = {}
    valid = {}
    evidence = {}
    for path in a.outputs:
        output_path = Path(path)
        d = json.loads(output_path.read_text())
        assert d['split'] == 'dev', output_path
        arm = d['arm']
        assert arm not in scores
        indexed = {r['sample_id']: r for r in d['rows']}
        assert len(indexed) == len(d['rows']) and set(indexed) == set(keys), (arm, len(indexed))
        v = {}
        sc = {}
        for k in keys:
            r = indexed[k]
            row = by_id[k]
            assert r['youtube_id'] == row['youtube_id']
            assert abs(r['clip_duration_sec'] - row['clip_duration_sec']) < 1e-5
            gt, dur = row['segments_clip_local'], row['clip_duration_sec']
            pred = r.get('parsed_segments')
            is_valid = bool(r.get('output_valid')) and isinstance(pred, list) and len(pred) > 0
            if is_valid:
                parsed_again, errs, warns = tc.parse_segments(json.dumps({'segments': pred}), dur)
                is_valid = parsed_again is not None and not errs and not warns
            v[k] = is_valid
            sc[k] = as_score(pred, gt, dur) if is_valid else 0.0
        scores[arm] = sc
        valid[arm] = v
        evidence[arm] = {'path': str(output_path), 'sha256': sha256(output_path),
                         'adapter': d.get('adapter'), 'model': d.get('model')}

    for control, ratio in [('FULL_CLIP', 1.0), ('CENTER_70_PERCENT', 0.7),
                           ('CENTER_80_PERCENT', 0.8)]:
        scores[control] = {}
        valid[control] = {}
        for k in keys:
            row = by_id[k]
            dur = row['clip_duration_sec']
            margin = dur * (1 - ratio) / 2
            scores[control][k] = as_score([[margin, dur - margin]], row['segments_clip_local'], dur)
            valid[control][k] = True

    assert 'T1_QVH_LORA' in scores
    best_control = max(['T1_QVH_LORA', 'FULL_CLIP', 'CENTER_70_PERCENT',
                        'CENTER_80_PERCENT'], key=lambda name: statistics.mean(scores[name].values()))
    threshold = statistics.mean(scores[best_control].values()) + 0.03
    shift_score = {}
    for arm in policy['selection']['dev_candidates']:
        if arm not in scores:
            continue
        d = json.loads(Path(evidence[arm]['path']).read_text())
        indexed = {r['sample_id']: r for r in d['rows']}
        shift_score[arm] = {}
        for k in keys:
            row = by_id[k]
            pred = indexed[k].get('parsed_segments')
            dur = row['clip_duration_sec']
            if not valid[arm][k]:
                shift_score[arm][k] = 0.0
            else:
                shift_score[arm][k] = statistics.mean(
                    as_score(rotate(pred, dur, dur * phase / 33),
                             row['segments_clip_local'], dur)
                    for phase in range(1, 33))

    result = {'metric': 'WEAK_TEACHER temporal union F1; NOT AIC official score',
              'policy_sha256': sha256(policy_path), 'dev_sha256': sha256(dev_path),
              'n_rows': len(keys), 'n_youtube_groups': len(groups),
              'invalid_kept_in_denominator': True, 'shift_control':
              '32 fixed circular offsets at 1..32/33 of clip duration; same predicted lengths',
              'evidence': evidence, 'best_control': best_control,
              'required_mean_f1': round(threshold, 6), 'arms': {}}
    nboot = policy['selection']['bootstrap_replicates']
    seed = policy['selection']['bootstrap_seed']
    for arm, sc in scores.items():
        mean_f1 = statistics.mean(sc.values())
        valid_rate = statistics.mean(valid[arm].values())
        item = {'mean_f1': round(mean_f1, 6), 'valid_rate': round(valid_rate, 6),
                'n_invalid': sum(not x for x in valid[arm].values())}
        if arm in policy['selection']['dev_candidates']:
            diff = {k: sc[k] - scores[best_control][k] for k in keys}
            ci = ci_by_group(diff, groups, nboot, seed)
            item['delta_vs_best_control'] = round(mean_f1 - statistics.mean(scores[best_control].values()), 6)
            item['delta_vs_best_control_group_ci95'] = ci
            sdiff = {k: sc[k] - shift_score[arm][k] for k in keys}
            sci = ci_by_group(sdiff, groups, nboot, seed + 1)
            item['delta_vs_circular_shift'] = round(statistics.mean(sdiff.values()), 6)
            item['delta_vs_circular_shift_group_ci95'] = sci
            item['gate_pass'] = (valid_rate == 1.0 and mean_f1 >= threshold
                                 and ci[0] >= 0 and sci[0] > 0)
        result['arms'][arm] = item
    out = Path(a.out)
    if out.exists():
        raise RuntimeError(f'refusing overwrite: {out}')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result['arms'], indent=2))
    print('best_control', best_control, 'required_mean_f1', threshold)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
