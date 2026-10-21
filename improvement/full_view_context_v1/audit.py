"""Independent first CPU dot products, native labels and tied-point AP."""
from fractions import Fraction
import numpy as np
import torch
from common import ROOT, CLIP, checked, read, ref, write


def independent_ap(scores, labels):
    labels = np.asarray(labels, dtype=np.float64)
    if labels.sum() in (0, len(labels)):
        return None
    order = np.argsort(-scores, kind='stable')
    cumulative = np.cumsum(labels[order])
    ends = np.r_[np.flatnonzero(np.diff(scores[order])), len(scores) - 1]
    recall = cumulative[ends] / labels.sum()
    precision = cumulative[ends] / (ends + 1)
    return float(np.sum(np.diff(np.r_[0, recall]) * precision))


def main():
    inputs = read(ROOT / 'input_acceptance.json')
    primary = read(ROOT / 'inference_completion.json')
    review = read(ROOT / 'review.json')
    reference = read(checked(inputs['point_reference']))
    old_inputs = read(CLIP / 'input_acceptance.json')
    annotation = {r['video_id']: r for r in read(checked(old_inputs['author_annotation']))}
    raw = np.concatenate([np.load(checked(f), allow_pickle=False) for f in primary['files']])
    image = torch.tensor(raw, dtype=torch.float64)
    text = torch.tensor(np.load(checked(inputs['text']), allow_pickle=False), dtype=torch.float64)
    assert image.shape == (112, 512) and text.shape == (26, 512)
    image = torch.nn.functional.normalize(image, dim=-1)
    text = torch.nn.functional.normalize(text, dim=-1)
    measured_scores = (image @ text.T).numpy()
    stored = np.load(ROOT / 'outputs/scores.npy', allow_pickle=False)
    max_error = float(np.max(np.abs(measured_scores - stored)))
    assert max_error < 1e-12
    comparisons = label_points = nulls = 0
    for source, result in zip(reference['sources'], review['sources']):
        assert source['sid'] == result['sid']
        pts = read(checked(source['clock']))['original_exact_pts']
        points = [r for r in inputs['rows'] if r['sid'] == source['sid']]
        query_ids = [q['query_id'] for q in source['queries']]
        for index, (query, event) in enumerate(zip(source['queries'], result['events'])):
            assert query['query_id'] == event['query_id']
            bounds = annotation[source['name']]['timestamps'][query['event']]
            left, right = [Fraction(str(v)) for v in bounds]
            labels = [int(left <= Fraction(pts[p['ordinal']]) < right) for p in points]
            assert labels == query['positive']
            label_points += len(labels)
            for arm in ('center', 'full'):
                indices = [p[f'{arm}_index'] for p in points]
                for suffix, qid in [('', query['query_id']), ('_next_query', query_ids[(index + 1) % len(query_ids)])]:
                    ap = independent_ap(stored[indices, qid], labels)
                    expected = event['AP'][arm + suffix]
                    if ap is None:
                        assert expected is None
                        nulls += 1
                    else:
                        assert abs(ap - expected) < 1e-12
                        comparisons += 1
    write(ROOT / 'independent_cpu_audit.json', dict(status='PASS_FIRST_TORCH_DOTS_NATIVE_LABELS_POINT_AP',
          point_label_checks=label_points, AP_comparisons=comparisons, unscorable_checks=nulls,
          cosine_values_checked=int(stored.size), maximum_dot_error=max_error,
          review=ref(ROOT / 'review.json'), original_model_calls=0, new_fit=0))


if __name__ == '__main__':
    main()
