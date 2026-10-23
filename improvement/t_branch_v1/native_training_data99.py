"""Separate loss bindings: whole-source review coefficients never enter inputs."""
from fractions import Fraction
import hashlib

import numpy as np

from t_io import ROOT, check, identity, read


def bind_training(inputs):
    reference = read(ROOT / 'native_action_feasibility97/completion.json')
    rows = {row['source']['sid']: row for row in reference['sources']}
    if set(rows) != set(inputs['fit']) or len(rows) != 9:
        raise ValueError('Whole original nine-fit loss/input set differs')
    publishers, sources = {}, {}
    for sid, row in rows.items():
        source = row['source']
        if source['role'] != 'fit' or source != inputs['original_fit_sources'][sid]:
            raise ValueError('Fit loss source/role differs from label-free input source')
        with np.load(check(row['native_cells']), allow_pickle=False) as data:
            begin, end = data['native_start'].copy(), data['native_stop'].copy()
            a = data['summary_action_positive_coefficient'].copy()
            b = data['summary_action_negative_coefficient'].copy()
        if (a.shape != begin.shape or b.shape != begin.shape or a.dtype != np.float64
                or b.dtype != np.float64 or not np.isfinite(a).all() or not np.isfinite(b).all()
                or (a < 0).any() or (b < 0).any() or abs(float(a.sum() + b.sum()) - 1) > 1e-12):
            raise ValueError('Source-global all-reviewer loss coefficient denominator invalid')
        cases = []
        for case in row['cases']:
            name = case['case']; low, high = case['cells']
            actual = inputs['fit'][sid][name]; proof = read(check(actual))
            bounds = np.stack([begin[low:high], end[low:high]], axis=1).tolist()
            if high - low != 32 or proof['source_native_cells'] != bounds or proof['original_CPU'] != case['CPU']:
                raise ValueError('Actual input cell geometry differs from its independent native label partition')
            cases.append(dict(case=name, actual_input_CPU=actual, original_CPU=case['CPU'],
                source_loss_coefficients=row['native_cells'], cell_slice=[low, high],
                source_summary_reference=row['original_reference'], native_cells=bounds,
                positive_mass=float(a[low:high].sum()), negative_mass=float(b[low:high].sum()),
                loss_scope='SOURCE_GLOBAL_ALL_REVIEWER_SUMMARY_ACTION_NOT_GENERIC_ORDINARY'))
        if (set(inputs['fit'][sid]) != {case['case'] for case in cases}
                or sum(c['cell_slice'][1] - c['cell_slice'][0] for c in cases) != len(a)):
            raise ValueError('All original native fit windows/cells not retained exactly once')
        sources[sid] = dict(source=source, cases=cases, reviewer_count=row['reviewers'],
            original_native_reference=row['original_reference'],
            whole_positive_mass=float(a.sum()), whole_negative_mass=float(b.sum()),
            no_window_loss_renormalization=True)
        publishers.setdefault(source['publisher'], []).append(sid)
    for sids in publishers.values():
        sids.sort()
        for sid in sids:
            sources[sid]['publisher_source_weight'] = str(Fraction(1, len(sids)))
    schedule = sorted(publishers, key=lambda p: hashlib.sha256(p.encode()).hexdigest())
    if len(schedule) != 5 or sum(len(v['cases']) for v in sources.values()) != 217:
        raise ValueError('Fixed complete217 windows/five publisher updates not bound')
    return dict(sources=sources, publishers=publishers, schedule=schedule,
                original_feasibility=identity(ROOT / 'native_action_feasibility97/completion.json'))


def coefficients(case, source_weight):
    with np.load(check(case['source_loss_coefficients']), allow_pickle=False) as data:
        first, last = case['cell_slice']
        a = data['summary_action_positive_coefficient'][first:last].copy()
        b = data['summary_action_negative_coefficient'][first:last].copy()
    if a.shape != (32,) or b.shape != (32,) or not 0 < Fraction(source_weight) <= 1:
        raise ValueError('Actual teacher uses a different native cell or publisher denominator')
    if (not np.isclose(a.sum(), case['positive_mass'], atol=1e-12, rtol=0)
            or not np.isclose(b.sum(), case['negative_mass'], atol=1e-12, rtol=0)):
        raise ValueError('Actual source-global coefficients changed before first teacher call')
    return a, b, float(Fraction(source_weight))
