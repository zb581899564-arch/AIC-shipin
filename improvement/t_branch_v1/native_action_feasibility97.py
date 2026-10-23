"""Fit-only native-unit supervision feasibility, no new policy/model admission."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
from pathlib import Path
import traceback

import numpy as np

from native_sets import NativeTimeline
from native_units97 import action_coefficients, attainable_unit_f1, contracts, measured_cells, reviewer_counts
from summary_reference97 import reference
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'native_action_feasibility97'


def source_feasibility(row, accepted):
    source = row['source']; sid = source['sid']
    timeline = NativeTimeline.from_clock(read(check(source['clock'])))
    refs = {read(check(read(check(ref))['input']))['case_id']: ref for ref in accepted}
    spans, cells, cases = [], [], []
    for window in row['windows']:
        name = sid + '_W' + str(window['index']).zfill(3)
        meta, bounds, grid = measured_cells(refs[name], source, timeline, window)
        offset = len(spans); spans.extend(bounds)
        cells.extend(dict(case=name, unit=j, native_start=a, native_stop=b)
                     for j, (a, b) in enumerate(bounds))
        cases.append(dict(case=name, CPU=refs[name], grid=grid,
                          cells=[offset, len(spans)], original_window=window))
    if (len(cases) != len(accepted) or spans[0][0] != 0 or spans[-1][1] != len(timeline.points)
            or any(a[1] != b[0] for a, b in zip(spans, spans[1:]))):
        raise ValueError('Original complete-source native cells overlap, omit frames or miss a case')
    names, targets, domain, ref, first = reference(source, timeline, OUT)
    if targets.dtype != bool or domain.dtype != bool:
        raise ValueError('Original selected/task-domain dtype differs; do not cast labels')
    positive = np.zeros(len(spans)); negative = positive.copy(); oracle = []; zero_windows = 0
    per_review = []
    for name, selected in zip(names, targets):
        pos, observed = reviewer_counts(spans, selected, domain)
        a, b = action_coefficients(pos, observed)
        if not pos.sum() or abs(a.sum() + b.sum() - 1) > 1e-12:
            raise ValueError('Complete original human summary lacks observed support')
        positive += a / len(names); negative += b / len(names)
        attainable = attainable_unit_f1(pos, observed); oracle.append(attainable)
        all_overlap_count = int(observed[pos > 0].sum()); p = int(pos.sum())
        blank = sum(not pos[part['cells'][0]:part['cells'][1]].any() for part in cases)
        zero_windows += blank
        per_review.append(dict(reviewer=name, original_positive_native_frames=p,
            no_positive_review_windows=blank, cell_oracle_f1=attainable,
            positive_overlap_cells_f1=2 * p / (all_overlap_count + p)))
    path = OUT / (sid + '_native_cells.npz')
    with path.open('xb') as stream:
        np.savez_compressed(stream, native_start=[a for a, _ in spans], native_stop=[b for _, b in spans],
            summary_action_positive_coefficient=positive, summary_action_negative_coefficient=negative)
    if abs(positive.sum() + negative.sum() - 1) > 1e-12:
        raise ValueError('All-reviewer/source action-loss normalization differs')
    return dict(source=source, cases=cases, original_reference=ref, reference_first_created=first,
        native_cells=identity(path), reviewers=len(names), windows=len(cases), cells=len(spans),
        mean_cell_oracle_f1=math.fsum(oracle) / len(oracle), per_review=per_review,
        no_positive_review_window_fraction=zero_windows / (len(names) * len(cases)),
        balanced_positive_mass=float(positive.sum()), balanced_negative_mass=float(negative.sum()))


def main():
    OUT.mkdir()
    terminal = read(ROOT / 'summary_diagnosis96/completion.json')
    if terminal['state'] != 'FIRST_STOP85_STAGEWISE_CPU_DIAGNOSIS_COMPLETE':
        raise ValueError('Complete rejected-profile stagewise evidence required first')
    inventory = read(ROOT / 'summary_content81/completion.json')
    if len(inventory['planned']) != 9 or any(r['source']['role'] != 'fit' for r in inventory['planned']):
        raise ValueError('Original nine fit sources only; no development or confirmation oracle tuning')
    save(OUT / 'registration.json', dict(stagewise_diagnosis=identity(ROOT / 'summary_diagnosis96/completion.json'),
        fit_inventory=identity(ROOT / 'summary_content81/completion.json'),
        scope='Exact32 measured temporal-pair native prediction cells, not new feature extraction or a model result',
        oracle='Reference-only representational bound, no production threshold or candidate qualification',
        target='Human-summary action preference, omitted content remains semantically UNKNOWN',
        no_training_admission=True, no_new_model_calls=True, no_original_confirmation_read=True,
        code={n: identity(ROOT / 'code' / n) for n in ['native_action_feasibility97.py',
              'native_units97.py', 'summary_reference97.py']}, CPU_contracts=contracts()))
    accepted = read(ROOT / 'summary_inputs84/completion.json')['accepted']
    rows = [source_feasibility(row, accepted[row['source']['sid']]) for row in inventory['planned']]
    if sum(r['windows'] for r in rows) != 217 or sum(r['reviewers'] for r in rows) != 86:
        raise ValueError('Complete original217 windows/all86 reviews not represented')
    save(OUT / 'completion.json', dict(state='FIRST_FIT9_NATIVE_UNIT_SUMMARY_ACTION_FEASIBILITY_COMPLETE_NOT_TRAINING',
        sources=rows, all_native_windows=217, actual_native_cells=sum(r['cells'] for r in rows),
        all_original_reviewers=86, first_native_references=sum(r['reference_first_created'] for r in rows),
        adopted_original_references=sum(not r['reference_first_created'] for r in rows),
        mean_source_cell_oracle_f1=math.fsum(r['mean_cell_oracle_f1'] for r in rows) / 9,
        no_oracle_as_model_or_official_score=True, no_unknown_as_ordinary=True,
        no_new_model_training_or_package_admission=True, no_development_or_confirmation_labels_read=True,
        next='Only use actual granularity, blank-target prevalence and cost to decide whether to register a distinct native-action learning profile. Do not revive85, tune a threshold or claim quality.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
