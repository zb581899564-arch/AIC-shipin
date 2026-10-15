"""Evaluate strict adapter outputs against the fixed, source-held-out references."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

from sft_contract import decode_output


def rank_correlation(a, b):
    def ranks(values):
        values = np.asarray(values)
        order = np.argsort(values, kind='stable')
        out = np.empty(len(values), dtype=float)
        first = 0
        while first < len(order):
            end = first + 1
            while end < len(order) and values[order[end]] == values[order[first]]:
                end += 1
            out[order[first:end]] = (first + end - 1) / 2
            first = end
        return out
    if len(set(a)) < 2 or len(set(b)) < 2:
        return None
    return float(np.corrcoef(ranks(a), ranks(b))[0, 1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--targets', required=True)
    p.add_argument('--predictions', required=True, help='JSONL: {id, answer: raw JSON string}')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    targets = [json.loads(s) for s in Path(args.targets).read_text(encoding='utf-8').splitlines()]
    predictions = [json.loads(s) for s in Path(args.predictions).read_text(encoding='utf-8').splitlines()]
    lookup = {p['id']: p for p in predictions}
    assert len(lookup) == len(predictions) and set(lookup) == {t['id'] for t in targets}
    errors, ious, source_pairs, invalid = [], [], defaultdict(lambda: [[], []]), []
    for t in targets:
        pred = lookup[t['id']]['answer']
        try:
            if t['task'].endswith('_x20'):
                actual = decode_output(pred, t['task'], image_count=len(t['images']))['scores_x20']
                expected = json.loads(t['messages'][1]['content'])['scores_x20']
                errors.extend((np.asarray(actual) - np.asarray(expected)) / 20)
                source_pairs[t['source_group']][0].extend(actual)
                source_pairs[t['source_group']][1].extend(expected)
            else:
                prompt = t['messages'][0]['content']
                iw, ih = map(int, re.search(r'Source image is (\d+)x(\d+)', prompt).groups())
                ratio = tuple(map(int, re.search(r'to (\d+):(\d+)', prompt).groups()))
                actual = decode_output(pred, t['task'], source_size=(iw, ih), ratio=ratio)['box_xywh']
                expected = decode_output(t['messages'][1]['content'], t['task'], source_size=(iw, ih), ratio=ratio)['box_xywh']
                x, y, w, h = actual; a, b, c, d = expected
                intersection = max(0, min(x+w, a+c)-max(x, a))*max(0, min(y+h, b+d)-max(y, b))
                ious.append(intersection/(w*h+c*d-intersection))
        except (ValueError, TypeError, KeyError) as exc:
            invalid.append({'id': t['id'], 'error': str(exc)})
    correlations = {}
    for source, (pred, gold) in source_pairs.items():
        correlations[source] = rank_correlation(pred, gold)
    report = {'rows': len(targets), 'invalid_outputs': invalid, 'invalid_rate': len(invalid)/len(targets),
              'temporal_mae': float(np.mean(np.abs(errors))) if errors else None,
              'temporal_rmse': float(np.sqrt(np.mean(np.square(errors)))) if errors else None,
              'temporal_spearman_per_source': correlations,
              'mean_crop_iou_against_model_labels': float(np.mean(ious)) if ious else None,
              'scope': 'TVSum human importance or weak crop-label agreement, not official AIC score',
              'metrics_calculated_on_valid_outputs_only': True,
              'invalid_targets_not_silently_repaired_or_converted_to_empty': True}
    out = Path(args.output)
    assert not out.exists()
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
