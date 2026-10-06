#!/usr/bin/env python3
"""Frozen small-grid interval shrink on dev, then mechanical apply elsewhere."""
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
sys.path.insert(0, str(R5/'scripts'))
import temporal_common as tc


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shrink(segments, factor):
    return [[round((a+b)/2 - (b-a)*factor/2, 6),
             round((a+b)/2 + (b-a)*factor/2, 6)] for a,b in segments]


def group_ci(diff, groups, seed, nboot):
    values = [statistics.mean(diff[k] for k in ks) for ks in groups.values()]
    rng = random.Random(seed)
    n = len(values)
    boot = sorted(sum(values[rng.randrange(n)] for _ in range(n))/n
                  for _ in range(nboot))
    return [round(boot[int(nboot*0.025)], 6), round(boot[int(nboot*0.975)], 6)]


def transformed(data, factor):
    result = json.loads(json.dumps(data))
    for row in result['rows']:
        if not row['output_valid'] or not row['parsed_segments']:
            raise RuntimeError('calibration input requires every row valid')
        old = row['parsed_segments']
        new = shrink(old, factor)
        parsed, errors, warnings = tc.parse_segments(
            json.dumps({'segments': new}), row['clip_duration_sec'])
        if parsed is None or errors or warnings:
            raise RuntimeError(f'calibration created invalid segment for {row["sample_id"]}')
        row['pre_calibration_segments'] = old
        row['parsed_segments'] = new
        row['metrics'] = tc.interval_metrics(new, row['gt_segments_clip_local'],
                                             row['clip_duration_sec'])
        row['pred_duration_ratio'] = round(tc.union_length(new)/row['clip_duration_sec'], 6)
    result['calibration_factor'] = factor
    result['calibration_method'] = 'midpoint_preserving_interval_duration_scale'
    result['summary']['mean_f1'] = round(statistics.mean(r['metrics']['f1']
                                                         for r in result['rows']), 6)
    result['summary']['mean_pred_duration_ratio'] = round(statistics.mean(
        r['pred_duration_ratio'] for r in result['rows']), 6)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--report', required=True)
    p.add_argument('--mode', choices=['select','apply'], required=True)
    a = p.parse_args()
    if Path(a.out).exists() or (a.mode == 'select' and Path(a.report).exists()):
        raise RuntimeError('refusing overwrite')
    data = json.loads(Path(a.input).read_text())
    policy_path = R5/'audit/interval_calibration_protocol_v1.json'
    policy = json.loads(policy_path.read_text())
    if a.mode == 'select':
        assert data['split'] == 'dev' and len(data['rows']) == 90
        groups = defaultdict(list)
        for row in data['rows']:
            groups[row['youtube_id']].append(row['sample_id'])
        assert len(groups) == 80
        scores = {}
        for factor in policy['factors']:
            scores[factor] = {row['sample_id']: tc.interval_metrics(
                shrink(row['parsed_segments'], factor), row['gt_segments_clip_local'],
                row['clip_duration_sec'])['f1'] for row in data['rows']}
        base = scores[1.0]
        items = {}
        for factor, by_id in scores.items():
            diff = {k: by_id[k]-base[k] for k in base}
            items[str(factor)] = {
                'mean_f1': round(statistics.mean(by_id.values()), 6),
                'delta_vs_1': round(statistics.mean(diff.values()), 6),
                'group_ci95_vs_1': group_ci(diff, groups,
                    policy['bootstrap']['seed'], policy['bootstrap']['replicates'])}
        best = max(policy['factors'], key=lambda f: (items[str(f)]['mean_f1'], f))
        gain = items[str(best)]['delta_vs_1']
        lower = items[str(best)]['group_ci95_vs_1'][0]
        factor = best if best < 1 and gain >= 0.01 and lower > 0 else 1.0
        report = {'arm': data['arm'], 'split': 'dev', 'source_output': a.input,
                  'source_sha256': sha(a.input), 'protocol_sha256': sha(policy_path),
                  'factors': items, 'best_factor': best,
                  'selected_factor': factor, 'selection_passed': factor < 1}
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    else:
        assert data['split'] == 'holdout'
        report = json.loads(Path(a.report).read_text())
        assert report['protocol_sha256'] == sha(policy_path)
        assert report['arm'] == data['arm']
        factor = report['selected_factor']
    result = transformed(data, factor)
    result['calibration_report'] = a.report
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'mode': a.mode, 'factor': factor,
                      'mean_f1': result['summary']['mean_f1'], 'out': a.out}))


if __name__ == '__main__':
    main()
