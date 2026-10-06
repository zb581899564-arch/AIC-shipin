#!/usr/bin/env python3
"""One-shot round-5 holdout gate; never used for candidate or threshold selection."""
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ci(values, nboot=10000, seed=20260916):
    rng = random.Random(seed)
    n = len(values)
    boot = sorted(sum(values[rng.randrange(n)] for _ in range(n))/n
                  for _ in range(nboot))
    return [round(boot[int(0.025*nboot)], 6),
            round(boot[int(0.975*nboot)], 6)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--arm', required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--t1', required=True)
    p.add_argument('--dev-gate', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    out = Path(a.out)
    if out.exists():
        raise RuntimeError(f'refusing overwrite: {out}')
    policy = json.loads((R5/'audit/decision_policy_v2.json').read_text())
    assert sha(R5/'data/holdout.jsonl') == policy['frozen_data']['holdout_sha256']
    dev_gate = json.loads(Path(a.dev_gate).read_text())
    assert dev_gate['arms'][a.arm]['gate_pass']
    rows = tc.load_split('holdout', R5)
    assert len(rows) == 88
    by_id = {r['sample_id']: r for r in rows}
    assert len(by_id) == len(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row['youtube_id']].append(row['sample_id'])
    assert len(groups) == 80
    scores = {}
    valid = {}
    evidence = {}
    for arm, path in [(a.arm, a.candidate), ('T1_QVH_LORA', a.t1)]:
        d = json.loads(Path(path).read_text())
        assert d['arm'] == arm and d['split'] == 'holdout'
        index = {r['sample_id']: r for r in d['rows']}
        assert len(index) == len(d['rows']) and set(index) == set(by_id)
        evidence[arm] = {'path': path, 'sha256': sha(path),
                         'adapter': d.get('adapter')}
        scores[arm], valid[arm] = {}, {}
        for k, row in by_id.items():
            r = index[k]
            assert r['youtube_id'] == row['youtube_id']
            pred = r.get('parsed_segments')
            is_valid = bool(r.get('output_valid')) and bool(pred)
            if is_valid:
                segs, errs, warns = tc.parse_segments(
                    json.dumps({'segments': pred}), row['clip_duration_sec'])
                is_valid = segs is not None and not errs and not warns
            valid[arm][k] = is_valid
            scores[arm][k] = tc.interval_metrics(
                pred if is_valid else [], row['segments_clip_local'],
                row['clip_duration_sec'])['f1']
    mean_cand = statistics.mean(scores[a.arm].values())
    mean_t1 = statistics.mean(scores['T1_QVH_LORA'].values())
    group_diff = [statistics.mean(scores[a.arm][k] - scores['T1_QVH_LORA'][k]
                                  for k in ids) for ids in groups.values()]
    paired_ci = ci(group_diff)
    durations = sorted(row['clip_duration_sec'] for row in rows)
    edges = [durations[round((len(rows)-1)*q)] for q in [0.25, 0.5, 0.75]]
    quartiles = {}
    for q in range(4):
        keys = [k for k, row in by_id.items()
                if (q == 0 or row['clip_duration_sec'] > edges[q-1]) and
                (q == 3 or row['clip_duration_sec'] <= edges[q])]
        quartiles[f'Q{q+1}'] = {'n': len(keys),
                               'candidate_mean': round(statistics.mean(scores[a.arm][k] for k in keys), 6),
                               't1_mean': round(statistics.mean(scores['T1_QVH_LORA'][k] for k in keys), 6),
                               'delta': round(statistics.mean(scores[a.arm][k] - scores['T1_QVH_LORA'][k]
                                                              for k in keys), 6)}
    gate = (all(valid[a.arm].values()) and mean_cand - mean_t1 >= 0.02
            and paired_ci[0] >= 0
            and all(x['delta'] >= -0.02 for x in quartiles.values()))
    result = {'metric': 'WEAK_TEACHER temporal union F1; NOT AIC official score',
              'holdout_attempt': 1, 'arm': a.arm, 'candidate_selected_before_holdout': True,
              'holdout_sha256': sha(R5/'data/holdout.jsonl'),
              'policy_sha256': sha(R5/'audit/decision_policy_v2.json'),
              'dev_gate_sha256': sha(a.dev_gate), 'evidence': evidence,
              'n_rows': len(rows), 'n_youtube_groups': len(groups),
              'candidate_mean_f1': round(mean_cand, 6), 't1_mean_f1': round(mean_t1, 6),
              'delta': round(mean_cand-mean_t1, 6), 'paired_group_ci95': paired_ci,
              'candidate_valid_rate': round(statistics.mean(valid[a.arm].values()), 6),
              'candidate_invalid_n': sum(not x for x in valid[a.arm].values()),
              'duration_quartile_edges': edges, 'quartiles': quartiles,
              'gate_pass_except_replay': gate,
              'replay_three_dev_three_holdout': 'PENDING_SEPARATE_CHECK'}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
