"""One fixed source-relative CPU time ranker and an uncalibrated addition rule.

Human soft votes describe original summary selection, not ordinary events.
No query API accepts labels. Native ownership, rather than assumed seconds,
defines the four-group candidate intervals.
"""
from __future__ import annotations

import numpy as np
import torch


TRAIN_SOURCES = 20
PCA_DIM = 32
SEED = 20261018
PCA_POWER_ITERATIONS = 2
RIDGE_LAMBDA = .01
RMS_FLOOR = 1e-4
WINDOW_GROUPS = 4


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _features(value):
    _require(isinstance(value, np.ndarray) and value.dtype == np.float32
             and value.ndim == 2 and min(value.shape) > 0
             and np.isfinite(value).all(), 'Finite nonempty float32[G,D] features required')
    return value


def _counts(value, size):
    n = np.asarray(value)
    _require(n.ndim == 1 and n.shape == (size,) and n.dtype.kind in 'iu'
             and (n > 0).all() and (n <= np.iinfo(np.int64).max).all(),
             'Positive integer native counts for every observed group required')
    w = n.astype(np.float64)
    total = float(w.sum())
    _require(np.isfinite(total) and total > 0, 'Finite positive native denominator required')
    return n.astype(np.int64), w / total


def source_center(values, native_counts):
    """Return float64 centered values, native-weighted mean and normalized weights."""
    x = np.asarray(values)
    _require(x.ndim in (1, 2) and len(x) > 0 and x.dtype.kind in 'fiu'
             and np.isfinite(x).all(), 'Finite source vector/matrix required')
    _, w = _counts(native_counts, len(x))
    x = x.astype(np.float64)
    mean = np.sum(x * (w if x.ndim == 1 else w[:, None]), axis=0)
    return x - mean, mean, w


def _query_design(features, native_counts, rms, projection):
    x = _features(features)
    centered, _, _ = source_center(x, native_counts)
    scaled = (centered / rms).astype(np.float32)
    _require(np.isfinite(scaled).all(), 'Source-relative feature scaling overflow')
    # Fit and query use this same per-source float32 GEMM before float64 ridge.
    return (scaled @ projection).astype(np.float64)


def fit(sources, train_ids, *, synthetic=False):
    """Fit exactly one train-only PCA32 and one source-equal ridge solve.

    sources[sid] contains features[G,D], native_counts[G], softvote[G].
    Only declared train IDs are inspected; synthetic=True is for pure tests.
    State contains just three NumPy arrays, directly serializable with np.savez.
    """
    ids = list(train_ids)
    _require(bool(ids) and len(ids) == len(set(ids))
             and (synthetic or len(ids) == TRAIN_SOURCES), 'Exactly20 unique training sources required')
    torch.set_num_threads(2)
    centered_sources = []
    centered_targets = []
    weights = []
    native_counts = []
    original_features = []
    source_rows = []
    dimension = None
    offset = 0
    for sid in ids:
        _require(sid in sources, 'Missing declared training source: ' + str(sid))
        row = sources[sid]
        x = _features(row['features'])
        n, _ = _counts(row['native_counts'], len(x))
        y = np.asarray(row['softvote'], dtype=np.float64)
        _require(y.shape == (len(x),) and np.isfinite(y).all()
                 and ((y >= 0) & (y <= 1)).all(), 'Aligned original human soft votes in[0,1] required')
        if dimension is None:
            dimension = x.shape[1]
        _require(x.shape[1] == dimension, 'All training sources must share one feature dimension')
        xc, _, w = source_center(x, n)
        yc, _, _ = source_center(y, n)
        centered_sources.append(xc)
        centered_targets.append(yc)
        weights.append(w / len(ids))
        native_counts.append(n)
        original_features.append(x)
        source_rows.append(dict(source_id=sid, start=offset, end=offset + len(x),
                                groups=len(x), native_frames=sum(map(int, n)), loss_weight=1 / len(ids)))
        offset += len(x)
    w = np.concatenate(weights)
    y = np.concatenate(centered_targets)
    _require(abs(float(w.sum()) - 1.) < 1e-12
             and min(offset, dimension) >= PCA_DIM, 'Complete source-equal weights and PCA32 domain required')
    # No global feature mean: every source has already been native-centered.
    rms_square = sum(np.sum(ws[:, None] * xc**2, axis=0)
                     for ws, xc in zip(weights, centered_sources))
    rms = np.maximum(np.sqrt(rms_square), RMS_FLOOR)
    _require(rms.shape == (dimension,) and np.isfinite(rms).all(), 'Finite train-only per-dimension RMS required')
    scaled = np.concatenate([(xc / rms).astype(np.float32) for xc in centered_sources])
    weighted = scaled * np.sqrt(w).astype(np.float32)[:, None]
    _require(np.isfinite(weighted).all(), 'Finite weighted train-only PCA input required')
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(SEED)
        _, singular, components = torch.pca_lowrank(
            torch.from_numpy(weighted), q=PCA_DIM, center=False, niter=PCA_POWER_ITERATIONS)
    projection = components.numpy().astype(np.float32)
    _require(projection.shape == (dimension, PCA_DIM) and np.isfinite(projection).all()
             and np.allclose(projection.T @ projection, np.eye(PCA_DIM), atol=2e-5),
             'Actual orthonormal CPU PCA32 required')
    design = np.concatenate([_query_design(x, n, rms, projection)
                             for x, n in zip(original_features, native_counts)])
    gram = design.T @ (w[:, None] * design) + RIDGE_LAMBDA * np.eye(PCA_DIM)
    beta = np.linalg.solve(gram, design.T @ (w * y))
    _require(beta.shape == (PCA_DIM,) and np.isfinite(beta).all(), 'Finite32 ridge coefficients required')
    state = dict(RMS=rms, PCA=projection, beta=beta)
    # Preserve query's per-source matrix shape for the final dot product too.
    prediction = np.concatenate([design[row['start']:row['end']] @ beta for row in source_rows])
    for x, n, row in zip(original_features, native_counts, source_rows):
        _require(np.array_equal(prediction[row['start']:row['end']], predict(state, x, n)),
                 'Training and label-free query transforms differ')
    mse = float(np.sum(w * (prediction - y)**2))
    report = dict(train_ids=ids, sources=len(ids), rows=source_rows, feature_dimension=dimension,
                  supervised_coefficients=PCA_DIM, intercept=False, lambda_value=RIDGE_LAMBDA,
                  weights_sum=float(w.sum()), source_equal_native_centered_MSE=mse,
                  penalized_objective=mse + RIDGE_LAMBDA * float(beta @ beta),
                  train_only_RMS=True, global_mean_used=False, RMS_floor=RMS_FLOOR,
                  PCA_dimensions=PCA_DIM, PCA_seed=SEED, PCA_power_iterations=PCA_POWER_ITERATIONS,
                  PCA_singular_values=singular.numpy().astype(float).tolist(),
                  pairwise_equivalence='Centered MSE = half ordered native-weighted all-pair difference MSE per source',
                  new_optimizer_updates=0, closed_form_solves=1, new_PCA_fits=1,
                  query_labels_required=False, uncertainty_calibrated=False)
    return state, report


def predict(state, features, native_counts):
    """Score all groups using this source's unlabeled native-weighted feature mean."""
    x = _features(features)
    _require(set(state) == {'RMS', 'PCA', 'beta'}, 'Complete fixed relative ranker state required')
    rms, projection, beta = state['RMS'], state['PCA'], state['beta']
    _require(all(isinstance(a, np.ndarray) and a.dtype.kind == 'f' and np.isfinite(a).all()
                 for a in (rms, projection, beta))
             and rms.shape == (x.shape[1],) and (rms >= RMS_FLOOR).all()
             and projection.shape == (x.shape[1], PCA_DIM) and projection.dtype == np.float32
             and beta.shape == (PCA_DIM,), 'Saved PCA/RMS/beta shape, type or finite-value mismatch')
    result = _query_design(x, native_counts, rms, projection) @ beta
    _require(result.shape == (len(x),) and np.isfinite(result).all(), 'Finite source-relative group scores required')
    return result


def _indices(value, name):
    a = np.asarray(value)
    _require(a.ndim == 1 and len(a) > 0 and a.dtype.kind in 'iu'
             and (a <= np.iinfo(np.int64).max).all() and (a >= 0).all(),
             'Nonempty ordered integer native ownership required: ' + name)
    a = a.astype(np.int64)
    _require((np.diff(a) >= 0).all(), 'Native ownership must follow native-frame order: ' + name)
    return a


def select_window(scores, native_groups, old_native_groups, baseline):
    """Choose at most one full four-group addition, or abstain; not confidence.

    Both ownership arrays contain one entry per ORIGINAL native frame. Complete
    groups require both old observation cells, including rejecting an odd tail.
    The returned evidence is JSON serializable and includes every sliding window.
    """
    score = np.asarray(scores)
    _require(score.ndim == 1 and len(score) > 0 and score.dtype.kind in 'fiu'
             and np.isfinite(score).all(), 'Finite scalar score for each observed time group required')
    score = score.astype(np.float64)
    groups = _indices(native_groups, 'native_groups')
    cells = _indices(old_native_groups, 'old_native_groups')
    base = np.asarray(baseline)
    _require(base.dtype == np.bool_ and base.shape == groups.shape == cells.shape,
             'Exact bool baseline and aligned original native ownership required')
    _require(np.array_equal(np.unique(cells), np.arange(int(cells[-1]) + 1))
             and np.array_equal(groups, cells // 2)
             and np.array_equal(np.unique(groups), np.arange(len(score))),
             'Original contiguous observation-cell domain and exact paired-group mapping required')
    counts = np.bincount(groups, minlength=len(score))
    boundaries = np.r_[0, np.cumsum(counts)]
    present_cells = set(map(int, np.unique(cells)))
    complete = np.array([2*g in present_cells and 2*g+1 in present_cells
                         for g in range(len(score))], dtype=bool)
    windows, anchors, candidates = [], [], []
    for first in range(max(0, len(score) - WINDOW_GROUPS + 1)):
        last = first + WINDOW_GROUPS
        lo, hi = int(boundaries[first]), int(boundaries[last])
        native_count = hi - lo
        overlap = int(base[lo:hi].sum())
        full = bool(complete[first:last].all())
        kind = ('INCOMPLETE_GROUP' if not full else 'BASELINE_ANCHOR' if overlap == native_count
                else 'DISJOINT_CANDIDATE' if overlap == 0 else 'INTERSECTS_BASELINE')
        row = dict(start_group=first, end_group_exclusive=last, native_start=lo,
                   native_end_exclusive=hi, native_frames=native_count, baseline_native_frames=overlap,
                   complete_groups=full, kind=kind,
                   score=float(np.average(score[first:last], weights=counts[first:last])))
        windows.append(row)
        if kind == 'BASELINE_ANCHOR':
            anchors.append(row)
        elif kind == 'DISJOINT_CANDIDATE':
            candidates.append(row)
    best = max(candidates, key=lambda r: (r['score'], -r['start_group'])) if candidates else None
    anchor_max = max((r['score'] for r in anchors), default=None)
    selected = None
    if not anchors:
        reason = 'NO_COMPLETE_BASELINE_ANCHOR'
    elif best is None:
        reason = 'NO_DISJOINT_COMPLETE_CANDIDATE'
    elif best['score'] <= anchor_max:
        reason = 'BEST_NOT_STRICTLY_ABOVE_ALL_BASELINE_ANCHORS'
    else:
        reason = None
        selected = dict(best)
    added = selected['native_frames'] if selected is not None else 0
    baseline_count = int(base.sum())
    return dict(status='SELECT_ONE_COMPLETE_FOUR_GROUP_WINDOW' if selected else 'ABSTAIN',
                abstain_reason=reason, selected=selected, windows=windows, anchors=anchors, candidates=candidates,
                temporal_groups=len(score), old_observation_cells=len(present_cells),
                complete_group_count=int(complete.sum()), incomplete_group_ids=np.flatnonzero(~complete).tolist(),
                possible_windows=len(windows), baseline_anchor_count=len(anchors), candidate_count=len(candidates),
                incomplete_window_count=sum(r['kind'] == 'INCOMPLETE_GROUP' for r in windows),
                intersecting_window_count=sum(r['kind'] == 'INTERSECTS_BASELINE' for r in windows),
                baseline_max_score=anchor_max, best_candidate_score=best['score'] if best else None,
                baseline_native_frames=baseline_count, added_native_frames=added,
                proposal_native_frames=baseline_count + added, baseline_frames_removed=0,
                maximum_added_windows=1, scores_are_confidence=False,
                window_score='Native-frame-weighted mean; max-over-pool rule has no confidence calibration')


def apply_selection(baseline, decision):
    """Materialize the chosen native interval while retaining every baseline frame."""
    base = np.asarray(baseline)
    _require(base.ndim == 1 and base.dtype == np.bool_, 'Original bool native baseline required')
    result = base.copy()
    selected = decision['selected']
    if selected is not None:
        lo, hi = selected['native_start'], selected['native_end_exclusive']
        _require(type(lo) is int and type(hi) is int and 0 <= lo < hi <= len(base)
                 and not base[lo:hi].any() and hi-lo == selected['native_frames'],
                 'Chosen addition must be a genuinely disjoint native interval')
        result[lo:hi] = True
    _require(not np.any(base & ~result) and int(result.sum()-base.sum()) == decision['added_native_frames'],
             'Original baseline deletion or addition count mismatch')
    return result
