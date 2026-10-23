"""Exact native cells from the measured paired-frame temporal grid, no labels."""
from bisect import bisect_left
from fractions import Fraction
import hashlib
import itertools

import numpy as np

from t_io import check, read


def paired_native_cells(points, start, end, ordinals, groups):
    if (len(ordinals) != 2 * groups or len(set(ordinals)) != len(ordinals)
            or any(a >= b for a, b in zip(ordinals, ordinals[1:]))):
        raise ValueError('Measured temporal grid must bind exact ordered original frame pairs')
    lo, hi = bisect_left(points, Fraction(start)), bisect_left(points, Fraction(end))
    if ordinals[0] != lo or ordinals[-1] + 1 != hi:
        raise ValueError('Complete original eligible support, not a shortened sampled subset, required')
    cuts = [lo] + [bisect_left(points, (points[ordinals[2*j-1]] + points[ordinals[2*j]]) / 2)
                    for j in range(1, groups)] + [hi]
    spans = list(zip(cuts[:-1], cuts[1:]))
    if any(not a <= ordinals[2*j] <= ordinals[2*j+1] < b for j, (a, b) in enumerate(spans)):
        raise ValueError('Native cell lost its actual visual pair or has no real support')
    return spans


def measured_cells(ref, source, timeline, expected_window):
    cpu = read(check(ref)); meta = read(check(cpu['input']))
    if (meta['source_sha256'] != source['media']['sha256']
            or meta['source_frame_ordinals'] != expected_window['source_frame_ordinals']
            or meta['sample_exact_pts'] != expected_window['sample_exact_pts']
            or meta['window_start'] != expected_window['start_exact']
            or meta['window_end'] != expected_window['end_exact']):
        raise ValueError('Actual accepted native window differs from original source plan')
    # Metadata member only. The full pixel tensor already passed its first QA;
    # no processor, RGB, image feature or old input QA is recomputed here.
    with np.load(cpu['encoded']['path'], allow_pickle=False) as archive:
        grid = archive['video_grid_thw'].copy()
    signature = cpu['detail']['tensor_signature']['video_grid_thw']
    if (grid.shape != (1, 3) or grid.dtype != np.int64
            or signature['shape'] != list(grid.shape)
            or signature['sha256'] != hashlib.sha256(grid.tobytes()).hexdigest()):
        raise ValueError('Actual stored temporal grid member differs from accepted signature')
    groups = int(grid[0, 0])
    if groups != 32:
        raise ValueError('This feasibility profile requires the measured native64/32-pair grid')
    ordinals = meta['source_frame_ordinals']
    if [str(timeline.points[i]) for i in ordinals] != meta['sample_exact_pts']:
        raise ValueError('Measured visual group ordinals do not match exact native PTS')
    spans = paired_native_cells(timeline.points, meta['window_start'], meta['window_end'], ordinals, groups)
    return meta, spans, signature


def reviewer_counts(spans, selected, domain):
    if selected.dtype != bool or domain.dtype != bool or selected.shape != domain.shape:
        raise ValueError('Exact original native selected/task-domain masks required')
    positive = np.r_[0, np.cumsum(selected & domain, dtype=np.int64)]
    observed = np.r_[0, np.cumsum(domain, dtype=np.int64)]
    return (np.array([positive[b] - positive[a] for a, b in spans], dtype=np.int64),
            np.array([observed[b] - observed[a] for a, b in spans], dtype=np.int64))


def action_coefficients(pos, observed):
    """Balanced summary-action loss, never a generic ordinary-label conversion."""
    if pos.shape != observed.shape or np.any(pos < 0) or np.any(pos > observed):
        raise ValueError('Positive/observed native counts differ')
    p, n = int(pos.sum()), int((observed - pos).sum())
    a, b = np.zeros(pos.shape, dtype=np.float64), np.zeros(pos.shape, dtype=np.float64)
    if p:
        a = pos / p * (0.5 if n else 1.)
    if n:
        b = (observed - pos) / n * (0.5 if p else 1.)
    return a, b


def attainable_unit_f1(pos, observed):
    """Reference-only upper bound, not model performance or a production cutoff."""
    total = int(pos.sum())
    if not total:
        return 0.
    order = sorted(range(len(pos)), key=lambda i: (-Fraction(int(pos[i]), int(observed[i]))
                                                  if observed[i] else Fraction(1), i))
    tp = np.cumsum(pos[order], dtype=np.int64)
    proposed = np.cumsum(observed[order], dtype=np.int64)
    return float(np.max(2. * tp / (proposed + total)))


def contracts():
    points = tuple(Fraction(i*i + i, 100) for i in range(16))
    spans = paired_native_cells(points, points[0], points[-1] + 1, [0, 2, 4, 6, 8, 10, 12, 15], 4)
    assert spans[0][0] == 0 and spans[-1][1] == 16
    assert all(a[1] == b[0] for a, b in zip(spans, spans[1:]))
    pos, obs = np.array([1, 0, 2, 0]), np.array([3, 2, 2, 1])
    actual = attainable_unit_f1(pos, obs)
    brute = max(2 * int(pos[list(bits)].sum()) / (int(obs[list(bits)].sum()) + int(pos.sum()))
                for bits in itertools.product([False, True], repeat=4))
    assert abs(actual - brute) < 1e-12
    a, b = action_coefficients(pos, obs); assert abs(a.sum() - .5) < 1e-12 and abs(b.sum() - .5) < 1e-12
    a, b = action_coefficients(pos * 0, obs * 0); assert not a.any() and not b.any()
    a, b = action_coefficients(pos, pos); assert abs(a.sum() - 1) < 1e-12 and not b.any()
    selected = np.array([True, False, True, False]); domain = np.array([True, False, False, False])
    p, n = reviewer_counts([(0, 2), (2, 4)], selected, domain)
    assert p.tolist() == [1, 0] and n.tolist() == [1, 0]
    return dict(checks=7, all_pass=True, unknown_contributes_zero_loss=True,
                exact_irregular_PTS_and_exhaustive_four_unit_upper_bound=True)
