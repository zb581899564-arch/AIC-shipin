"""Evaluate one predeclared author model and same-pixel temporal control."""
import numpy as np
from common import ROOT, PREVIOUS, checked, grouped_ap, read, ref, write


def primary_scores(source):
    acceptance = read(ROOT / 'outputs' / source['sid'] / 'acceptance.json')
    scores = {}
    for mode in ['real', 'reverse']:
        outputs = sorted((r for r in acceptance['outputs'] if r['mode'] == mode),
                         key=lambda r: r['start'])
        position = 0
        parts = []
        for row in outputs:
            assert row['start'] == position
            parts.append(np.load(checked(row['output']), allow_pickle=False)['scores'])
            position += row['cells']
        assert position == source['native_cells']
        scores[mode] = np.concatenate(parts)
    return scores


def main():
    inputs = read(ROOT / 'input_acceptance.json')
    old = read(checked(inputs['previous_quality']))
    rows = []
    for index, source in enumerate(inputs['sources']):
        scores = primary_scores(source)
        target = np.load(checked(source['target']), allow_pickle=False)
        ids = source['query_ids']
        other = inputs['sources'][(index + 1) % 8]['query_ids']
        events = []
        for j, query in enumerate(ids):
            streams = dict(correct=scores['real'][:, query],
                  reverse=scores['reverse'][:, query],
                  within_query_swap=scores['real'][:, ids[(j + 1) % len(ids)]],
                  cross_video_query_swap=scores['real'][:, other[j % len(other)]],
                  temporal_shift=np.roll(scores['real'][:, query], len(target['counts']) // 2))
            ap = {key: grouped_ap(values, target['positive'][j], target['counts'])
                  for key, values in streams.items()}
            assert all(v is not None for v in ap.values())
            ap['constant'] = float(target['positive'][j].sum() / target['counts'].sum())
            events.append(dict(query_id=query, AP=ap))
        means = {k: float(np.mean([e['AP'][k] for e in events])) for k in events[0]['AP']}
        original = next(s for s in old['sources'] if s['sid'] == source['sid'])
        rows.append(dict(sid=source['sid'], AP=means, events=events,
                         versus_static_clip=means['correct'] - original['AP']['correct']))
    macro = {k: float(np.mean([s['AP'][k] for s in rows])) for k in rows[0]['AP']}
    gate = read(ROOT / 'protocol.json')['gate']
    tests = dict(
        within=macro['correct'] - macro['within_query_swap'] >= gate['within_gain'],
        cross=macro['correct'] - macro['cross_video_query_swap'] >= gate['cross_gain'],
        shifted=macro['correct'] - macro['temporal_shift'] >= gate['shift_gain'],
        constant=macro['correct'] - macro['constant'] >= gate['constant_gain'],
        sources=sum(s['AP']['correct'] > s['AP']['within_query_swap'] for s in rows) >= gate['sources'],
        versus_static=macro['correct'] - old['source_macro_AP']['correct'] >= gate['static_gain'],
        order_evidence=macro['correct'] - macro['reverse'] >= gate['reverse_gain'],
    )
    write(ROOT / 'review.json', dict(status='ELIGIBLE_FOR_SEPARATE_AUTOMATIC_QUERY_PILOT'
          if all(tests.values()) else 'STOP_FROZEN_VIDEO_SEMANTIC_GROUNDING',
          tests=tests, source_macro_AP=macro, sources=rows,
          static_clip_macro=old['source_macro_AP']['correct'],
          historical_exposure=True, human_event_query_positive_control_only=True,
          action_order_causal_claim=False, short_highlight_or_official_score_claim=False,
          production_allowed=False, automatic_query_test_run=False))


if __name__ == '__main__':
    main()
