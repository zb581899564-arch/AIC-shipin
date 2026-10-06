"""Query-conditioned temporal diagnostics with paired source-group bootstrap."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
from collections import defaultdict


def intervals(values, duration=None):
    result = []
    for pair in values:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError('interval must be [start,end]')
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in pair):
            raise ValueError('nonfinite/non-numeric interval')
        a, b = map(float, pair)
        if a < 0 or b <= a or (duration is not None and b > duration + 1e-5):
            raise ValueError(f'invalid interval {pair}, duration={duration}')
        result.append([a, b])
    merged = []
    for a, b in sorted(result):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return merged


def overlap(a, b):
    i = j = 0
    total = 0.0
    while i < len(a) and j < len(b):
        total += max(0.0, min(a[i][1], b[j][1]) - max(a[i][0], b[j][0]))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return total


def score_pair(pred, truth):
    p = sum(b-a for a, b in pred)
    g = sum(b-a for a, b in truth)
    hit = overlap(pred, truth)
    f1 = 2*hit/(p+g) if p+g else 1.0
    precision = hit/p if p else float(not g)
    recall = hit/g if g else float(not p)
    window_iou = []
    for a, b in truth:
        best = 0.0
        for c, d in pred:
            intersection = max(0., min(b, d)-max(a, c))
            best = max(best, intersection/((b-a)+(d-c)-intersection))
        window_iou.append(best)
    return dict(f1=f1, precision=precision, recall=recall,
                mean_gt_best_window_iou=sum(window_iou)/len(window_iou) if window_iou else float(not p))


def truth_intervals(row):
    if 'relevant_windows' in row:
        return row['relevant_windows']
    if 'segments_sec' in row:
        return row['segments_sec']
    answer = row['answer']
    if isinstance(answer, str):
        answer = json.loads(answer)
    return answer['segments']


def evaluate_rows(predictions, references):
    refs = {str(x['video_id']): x for x in references}
    preds = {str(x['video_id']): x for x in predictions}
    if len(refs) != len(references) or len(preds) != len(predictions):
        raise ValueError('duplicate video_id')
    if refs.keys() != preds.keys():
        raise ValueError(f'coverage mismatch: missing={len(refs.keys()-preds.keys())}, extra={len(preds.keys()-refs.keys())}')
    rows = []
    for key, ref in refs.items():
        pred = preds[key]
        if pred.get('status', 'ok') not in ('ok', 'success', 'valid_empty'):
            raise ValueError(f'non-success prediction {key}: {pred.get("status")}')
        duration = float(ref.get('duration_sec', ref.get('duration')))
        p = intervals(pred['segments_sec'], duration)
        g = intervals(truth_intervals(ref), duration)
        metrics = score_pair(p, g)
        if 'saliency_segments' in ref:
            metrics['saliency_f1'] = score_pair(p, intervals(ref['saliency_segments'], duration))['f1']
        rows.append(dict(video_id=key, source_group=ref['source_group'], empty=not p, **metrics))
    names = ['f1','precision','recall','mean_gt_best_window_iou']
    if all('saliency_f1' in x for x in rows):
        names += ['saliency_f1']
    return dict(kind='internal_query_conditioned_diagnostic', official_aic_score=None,
                count=len(rows), empty_count=sum(x['empty'] for x in rows),
                metrics={k:sum(x[k] for x in rows)/len(rows)*100 for k in names}, rows=rows)


def compare(candidate, baseline, draws=10000, seed=42):
    a={x['video_id']:x for x in candidate['rows']}; b={x['video_id']:x for x in baseline['rows']}
    if a.keys() != b.keys():
        raise ValueError('comparison coverage mismatch')
    grouped=defaultdict(list)
    for key,x in a.items():
        if x['source_group'] != b[key]['source_group']:
            raise ValueError('source group drift')
        grouped[x['source_group']].append((x['f1']-b[key]['f1'])*100)
    groups=[grouped[k] for k in sorted(grouped)]
    rng=random.Random(seed); samples=[]
    for _ in range(draws):
        selected=[groups[rng.randrange(len(groups))] for _ in groups]
        samples.append(sum(sum(g) for g in selected)/sum(len(g) for g in selected))
    samples.sort()
    low, high=samples[int(.025*draws)],samples[min(draws-1,int(.975*draws))]
    delta=candidate['metrics']['f1']-baseline['metrics']['f1']
    return dict(delta_f1_pp=delta, source_groups=len(groups), bootstrap_draws=draws,
                seed=seed, ci95_pp=[low,high], eligible_dev=delta>=1 and low>0)


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--predictions',required=True); ap.add_argument('--reference',required=True)
    ap.add_argument('--baseline-report'); ap.add_argument('--out',required=True); args=ap.parse_args()
    report=evaluate_rows(read_jsonl(args.predictions),read_jsonl(args.reference))
    if args.baseline_report:
        report['comparison']=compare(report,json.loads(Path(args.baseline_report).read_text()))
    report['reference_sha256']=hashlib.sha256(Path(args.reference).read_bytes()).hexdigest()
    report['predictions_sha256']=hashlib.sha256(Path(args.predictions).read_bytes()).hexdigest()
    Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__=='__main__':
    main()
