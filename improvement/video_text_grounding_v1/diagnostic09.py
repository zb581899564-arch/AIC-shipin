"""Posthoc order sensitivity and cached-view geometry, never a new selection gate."""
import numpy as np
from common import ROOT, checked, read, ref, write


def score_streams(source):
    accepted = read(ROOT / 'outputs' / source['sid'] / 'acceptance.json')
    result = {}
    for mode in ['real', 'reverse']:
        rows = sorted([r for r in accepted['outputs'] if r['mode'] == mode], key=lambda r: r['start'])
        result[mode] = np.concatenate([np.load(checked(r['output']), allow_pickle=False)['scores'] for r in rows])
    return result


def source_diagnostic(source):
    scores = score_streams(source)
    indices = np.triu_indices(source['native_cells'], 1)
    rows = []
    for query in source['query_ids']:
        real, reverse = (scores[name][:, query].astype(np.float64) for name in ['real', 'reverse'])
        original_order = np.sign((real[:, None] - real[None, :])[indices])
        reverse_order = np.sign((reverse[:, None] - reverse[None, :])[indices])
        rows.append(dict(query=query, unordered_cell_pairs=len(original_order),
              pair_order_agreement=float(np.mean(original_order == reverse_order)),
              mean_absolute_cosine_change=float(np.abs(real - reverse).mean())))
    clock = read(checked(source['clock']))
    width, height = clock['width'], clock['height']
    scale = 256 / min(width, height)
    resized = [round(width * scale), round(height * scale)]
    return dict(sid=source['sid'], query_diagnostics=rows,
          pair_order_agreement=float(np.mean([r['pair_order_agreement'] for r in rows])),
          frame_dimensions=[width, height], resized_dimensions=resized,
          retained_resized_view_area=224 ** 2 / (resized[0] * resized[1]))


def main():
    assert read(ROOT / 'completion.json')['status'] == 'STOP_FROZEN_VIDEO_SEMANTIC_GROUNDING'
    rows = [source_diagnostic(source) for source in read(ROOT / 'input_acceptance.json')['sources']]
    out = dict(status='POSTHOC_DIAGNOSTIC_ONLY_STOP_UNCHANGED', sources=rows,
          macro_pair_order_agreement=float(np.mean([r['pair_order_agreement'] for r in rows])),
          macro_retained_resized_view_area=float(np.mean([r['retained_resized_view_area'] for r in rows])),
          all_ties_included_not_favorably_removed=True, original_gate_unchanged=True,
          model_calls=0, training_updates=0, new_decode=0, new_labels=0,
          attention_or_cropping_causality_proven=False, full_view_quality_proven=False,
          interpretation='Order agreement describes these saved scores only. Both encoders used the same center view; geometry cannot explain their difference or prove omitted important content.')
    write(ROOT / 'posthoc_diagnostic09.json', out)
    print({k: v for k, v in out.items() if k != 'sources'})


if __name__ == '__main__':
    main()
