"""Fixed sparse point comparison, without changing the preselected points."""
import math
import numpy as np
from common import ROOT, checked, normalize, read, save_array, write


def point_ap(scores, labels):
    total = sum(labels)
    if total == 0 or total == len(labels):
        return None
    order = np.argsort(-np.asarray(scores), kind='stable')
    tp = seen = result = 0.0
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and scores[order[j]] == scores[order[i]]:
            j += 1
        added = sum(labels[int(k)] for k in order[i:j])
        tp += added
        seen += j - i
        result += (added / total) * (tp / seen)
        i = j
    return float(result)


def review():
    inputs = read(ROOT / 'input_acceptance.json')
    inference = read(ROOT / 'inference_completion.json')
    reference = read(checked(inputs['point_reference']))
    images = normalize(np.concatenate([np.load(checked(f), allow_pickle=False) for f in inference['files']]))
    text = normalize(np.load(checked(inputs['text']), allow_pickle=False))
    scores = images @ text.T
    assert scores.shape == (112, 26) and np.isfinite(scores).all()
    save_array(ROOT / 'outputs/scores.npy', scores)
    rows = []
    for source in reference['sources']:
        points = [r for r in inputs['rows'] if r['sid'] == source['sid']]
        assert [r['ordinal'] for r in points] == source['ordinals']
        events = []
        ids = [q['query_id'] for q in source['queries']]
        for index, query in enumerate(source['queries']):
            aps = {}
            for arm in ('center', 'full'):
                selected = scores[[p[f'{arm}_index'] for p in points], query['query_id']]
                aps[arm] = point_ap(selected, query['positive'])
                wrong = scores[[p[f'{arm}_index'] for p in points], ids[(index + 1) % len(ids)]]
                aps[f'{arm}_next_query'] = point_ap(wrong, query['positive'])
            assert query['scorable'] == (aps['center'] is not None)
            events.append(dict(query_id=query['query_id'], scorable=query['scorable'], AP=aps))
        usable = [e for e in events if e['scorable']]
        means = {k: float(np.mean([e['AP'][k] for e in usable])) for k in usable[0]['AP']} if usable else None
        rows.append(dict(sid=source['sid'], events=events, scorable_queries=len(usable), AP=means,
                         full_minus_center=means['full'] - means['center'] if means else None))
    supported = [r for r in rows if r['AP'] is not None]
    macro = {k: float(np.mean([r['AP'][k] for r in supported])) for k in supported[0]['AP']}
    gain = macro['full'] - macro['center']
    gate = read(ROOT / 'protocol.json')['gate']
    tests = dict(support=reference['support']['supported'], macro_gain=gain >= gate['macro_gain'],
                 sources=sum(r['full_minus_center'] > 0 for r in supported) >= math.ceil(gate['source_fraction'] * len(supported)),
                 no_large_loss=min(r['full_minus_center'] for r in supported) >= -gate['max_source_loss'])
    write(ROOT / 'review.json', dict(status='SUPPORT_SEPARATE_AUTOMATIC_QUERY_DESIGN' if all(tests.values()) else 'STOP_FIXED_FULL_VIEW_PROFILE',
          tests=tests, macro_AP=macro, full_minus_center=gain, sources=rows,
          improved_sources=sum(r['full_minus_center'] > 0 for r in supported), support=reference['support'],
          metric='AP at eight hash-fixed native points per supported source; human broad event queries',
          scale_and_fill_are_part_of_the_input_change=True, sparse_not_dense=True, historical_exposure=True,
          generic_highlight_or_official_joint_quality_proven=False, production_allowed=False))


if __name__ == '__main__':
    review()
