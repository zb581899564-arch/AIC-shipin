"""One fixed CPU conditional-utility readout, with prespecified small controls.

Accepted group features and a previously fitted train-only RMS/PCA are inputs;
this module neither fits PCA nor reads files, labels, models or source locks.
Targets supplied to fit_heads are absolute z=N/(2*c)*mean_rater_delta_F1.
Source centering is used only for the ORIGINAL group representation. Final
candidate designs and targets retain their absolute source state and zero point.
"""
from __future__ import annotations

from numbers import Integral

import numpy as np


FEATURE_DIM = 8192
PCA_DIM = 16
DESIGN_DIM = 19
TRAIN_SOURCES = 20
RIDGE_LAMBDA = .01
RMS_FLOOR = 1e-4
METADATA_COLUMNS = (17, 18)
STATE_KEYS = {
    'visual_mean', 'visual_scale', 'visual_beta', 'visual_intercept',
    'metadata_mean', 'metadata_scale', 'metadata_beta', 'metadata_intercept',
    'constant_z',
}


def _require(value, message):
    if not value:
        raise ValueError(message)


def _integer(value, name):
    _require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)),
             name+' must be an integer')
    return int(value)


def _design(value):
    _require(isinstance(value, np.ndarray) and value.dtype == np.float64
             and value.ndim == 2 and value.shape[1] == DESIGN_DIM and np.isfinite(value).all(),
             'Finite float64[K,19] candidate design required, including K=0')
    return value


def _clips(clips, native_frames):
    size = _integer(native_frames, 'Native length')
    _require(size > 0, 'Native length must be positive')
    result = []
    for clip in clips:
        _require(isinstance(clip, dict), 'Original candidate clip dictionary required')
        _require('native_start' in clip and 'native_end_exclusive' in clip,
                 'Original half-open native candidate range required')
        lo = _integer(clip['native_start'], 'Candidate start')
        hi = _integer(clip['native_end_exclusive'], 'Candidate end')
        _require(0 <= lo < hi <= size, 'Nonempty candidate range inside original native length required')
        if 'native_frames' in clip:
            _require(_integer(clip['native_frames'], 'Candidate length') == hi-lo,
                     'Candidate native length does not match original bounds')
        result.append((dict(clip), lo, hi))
    ordered = sorted(result, key=lambda item: item[1])
    _require(all(first[2] <= second[1] for first, second in zip(ordered, ordered[1:])),
             'Fixed tiling candidates must be unique and nonoverlapping')
    return result


def build_design(features_float32_Gx8192, native_groups_int_N, baseline_bool_N, clips_list, transform):
    """Build 19 features without labels or a new PCA fit.

    Group ownership must cover every original native frame. Candidate clips come
    from the independently accepted complete-four-group inventory; this API does
    not receive occupied-cell ownership and cannot re-prove that inventory.
    It does verify group boundaries, exactly four groups and tiling alignment.
    Baseline pooling counts selected native frames even for a partially selected
    group. For an empty baseline the source-relative B pool is the zero vector;
    baseline coverage explicitly equals zero. No anchor requirement is imposed.
    """
    features = features_float32_Gx8192
    _require(isinstance(features, np.ndarray) and features.dtype == np.float32
             and features.ndim == 2 and features.shape[0] > 0 and features.shape[1] == FEATURE_DIM
             and np.isfinite(features).all(), 'Finite accepted float32[G,8192] group features required')
    groups = np.asarray(native_groups_int_N)
    _require(groups.ndim == 1 and len(groups) > 0 and groups.dtype.kind in 'iu'
             and (groups >= 0).all() and (groups < len(features)).all()
             and (np.diff(groups.astype(np.int64)) >= 0).all()
             and np.array_equal(np.unique(groups), np.arange(len(features))),
             'Complete ordered native-to-group ownership required')
    groups = groups.astype(np.int64)
    baseline = np.asarray(baseline_bool_N)
    _require(baseline.dtype == np.bool_ and baseline.shape == groups.shape,
             'Exact bool[N] original baseline required; unknowns cannot become zero')
    _require(isinstance(transform, dict) and set(transform) == {'RMS', 'PCA16'},
             'Only accepted train-only RMS and the fixed first16 PCA columns required')
    rms, projection = transform['RMS'], transform['PCA16']
    _require(isinstance(rms, np.ndarray) and rms.dtype == np.float64 and rms.shape == (FEATURE_DIM,)
             and np.isfinite(rms).all() and (rms >= RMS_FLOOR).all(), 'Accepted float64[8192] train RMS required')
    _require(isinstance(projection, np.ndarray) and projection.dtype == np.float32
             and projection.shape == (FEATURE_DIM, PCA_DIM) and np.isfinite(projection).all(),
             'Accepted float32[8192,16] PCA prefix required')
    clips = _clips(clips_list, len(groups))
    counts = np.bincount(groups, minlength=len(features)).astype(np.float64)
    boundaries = np.r_[0, np.cumsum(counts.astype(np.int64))]
    source_mean = np.sum(features.astype(np.float64)*(counts/counts.sum())[:, None], axis=0)
    scaled = ((features.astype(np.float64)-source_mean)/rms).astype(np.float32)
    _require(np.isfinite(scaled).all(), 'Source-centered group scaling overflow')
    projected = (scaled @ projection).astype(np.float64)
    _require(np.isfinite(projected).all(), 'Finite fixed-PCA group projection required')
    selected_counts = np.bincount(groups[baseline], minlength=len(features)).astype(np.float64)
    baseline_count = int(baseline.sum())
    baseline_pool = (np.sum(projected*selected_counts[:, None], axis=0)/baseline_count
                     if baseline_count else np.zeros(PCA_DIM, dtype=np.float64))
    rows = []
    for clip, lo, hi in clips:
        first, last = int(groups[lo]), int(groups[hi-1])+1
        _require(first % 4 == 0 and last-first == 4
                 and int(boundaries[first]) == lo and int(boundaries[last]) == hi,
                 'Original fixed tiling of four complete group ranges required')
        if 'start_group' in clip:
            _require(_integer(clip['start_group'], 'Start group') == first, 'Candidate start group mismatch')
        if 'end_group_exclusive' in clip:
            _require(_integer(clip['end_group_exclusive'], 'End group') == last, 'Candidate end group mismatch')
        _require(not bool(baseline[lo:hi].any()), 'Candidate must not intersect any original baseline native frame')
        candidate_counts = np.bincount(groups[lo:hi], minlength=len(features)).astype(np.float64)
        candidate_pool = np.sum(projected*candidate_counts[:, None], axis=0)/(hi-lo)
        contrast = candidate_pool-baseline_pool
        row = np.r_[contrast, np.mean(contrast**2), baseline_count/len(groups), (hi-lo)/len(groups)]
        _require(row.shape == (DESIGN_DIM,) and np.isfinite(row).all(), 'Finite conditional19 feature row required')
        rows.append(row)
    return np.asarray(rows, dtype=np.float64).reshape(len(rows), DESIGN_DIM)


def fit_heads(designs_by_source, targets_z_by_source, train_ids):
    """Fit VISUAL19 and METADATA2 once, plus a source-equal constant control.

    Every train source has weight 1/20 and every candidate in that source has
    weight 1/(20*K). There is no sign balancing, target source centering or
    target-magnitude weighting. Global weighted X/y centering implements a free,
    unpenalized intercept; train-only per-column RMS scales ridge coordinates.
    Only the explicitly named twenty training source entries are inspected.
    """
    ids = list(train_ids)
    _require(len(ids) == TRAIN_SOURCES and len(set(ids)) == TRAIN_SOURCES,
             'Exactly20 unique declared training sources required')
    designs, targets, weights, source_rows = [], [], [], []
    offset = 0
    for sid in ids:
        _require(sid in designs_by_source and sid in targets_z_by_source, 'Missing declared training source')
        design = _design(designs_by_source[sid])
        target = np.asarray(targets_z_by_source[sid])
        _require(len(design) > 0 and target.dtype.kind in 'fiu' and target.shape == (len(design),)
                 and np.isfinite(target).all(), 'Nonempty finite absolute z per train candidate required')
        designs.append(design); targets.append(target.astype(np.float64))
        weights.append(np.full(len(design), 1/(TRAIN_SOURCES*len(design)), dtype=np.float64))
        source_rows.append(dict(id=sid, start=offset, end=offset+len(design), candidates=len(design),
                                source_weight=1/TRAIN_SOURCES, candidate_weight=1/(TRAIN_SOURCES*len(design))))
        offset += len(design)
    design, target, weight = np.concatenate(designs), np.concatenate(targets), np.concatenate(weights)
    _require(abs(float(weight.sum())-1.) < 1e-12, 'Source-equal candidate weights must total1')
    target_mean = float(weight @ target)
    centered_target = target-target_mean
    state = {'constant_z': np.array(target_mean, dtype=np.float64)}
    metrics = {}
    for name, columns in (('visual', tuple(range(DESIGN_DIM))), ('metadata', METADATA_COLUMNS)):
        x = design[:, columns]
        mean = np.sum(weight[:, None]*x, axis=0)
        centered = x-mean
        scale = np.maximum(np.sqrt(np.sum(weight[:, None]*centered**2, axis=0)), RMS_FLOOR)
        normalized = centered/scale
        gram = normalized.T @ (weight[:, None]*normalized) + RIDGE_LAMBDA*np.eye(len(columns))
        beta = np.linalg.solve(gram, normalized.T @ (weight*centered_target))
        _require(np.isfinite(mean).all() and np.isfinite(scale).all() and np.isfinite(beta).all(),
                 'Finite fixed ridge state required')
        state.update({name+'_mean': mean, name+'_scale': scale, name+'_beta': beta,
                      name+'_intercept': np.array(target_mean, dtype=np.float64)})
        prediction = normalized @ beta+target_mean
        metrics[name.upper()] = dict(weighted_MSE=float(np.sum(weight*(prediction-target)**2)),
            coefficients=len(columns), intercept=float(target_mean),
            source_MSE={row['id']: float(np.mean((prediction[row['start']:row['end']]-target[row['start']:row['end']])**2))
                        for row in source_rows})
    metrics['CONSTANT'] = dict(weighted_MSE=float(np.sum(weight*centered_target**2)), coefficients=0,
                               value=target_mean)
    report = dict(train_ids=ids, sources=TRAIN_SOURCES, candidates=len(design), source_rows=source_rows,
        weights_sum=float(weight.sum()), metrics=metrics, lambda_value=RIDGE_LAMBDA, RMS_floor=RMS_FLOOR,
        unpenalized_global_intercept=True, source_centered_targets=False, positive_negative_balancing=False,
        new_PCA_fits=0, new_optimizer_updates=0, closed_form_solves=2,
        design_columns=['candidate_minus_baseline_PC'+str(i) for i in range(PCA_DIM)]+
                       ['mean_squared_PC_distance', 'baseline_native_fraction', 'candidate_native_fraction'],
        metadata_columns=list(METADATA_COLUMNS), target='Absolute z=N/(2c)*mean_rater_delta_F1',
        empty_baseline_pool='Zero source-relative PC16; coverage0', uncertainty_calibrated=False)
    return state, report


def predict(state, design):
    """Use saved flat NumPy state on a label-free candidate design."""
    x = _design(design)
    _require(isinstance(state, dict) and set(state) == STATE_KEYS, 'Complete conditional19/control state required')
    for name, value in state.items():
        _require(isinstance(value, np.ndarray) and value.dtype == np.float64 and np.isfinite(value).all(),
                 'Every saved state entry must be a finite float64 NumPy array: '+name)
    _require(state['constant_z'].shape == (), 'Scalar constant control required')
    result = {}
    for name, columns in (('visual', tuple(range(DESIGN_DIM))), ('metadata', METADATA_COLUMNS)):
        mean, scale, beta, intercept = [state[name+'_'+suffix] for suffix in ('mean', 'scale', 'beta', 'intercept')]
        _require(mean.shape == scale.shape == beta.shape == (len(columns),) and intercept.shape == ()
                 and (scale >= RMS_FLOOR).all() and np.array_equal(intercept, state['constant_z']),
                 'Saved mean/scale/coefficient/intercept mismatch')
        values = ((x[:, columns]-mean)/scale) @ beta+intercept
        _require(values.shape == (len(x),) and np.isfinite(values).all(), 'Finite absolute z predictions required')
        result[name.upper()] = values
    result['CONSTANT'] = np.full(len(x), float(state['constant_z']), dtype=np.float64)
    return result


def select_addition(clips, pred_z, N):
    """Choose at most one positive predicted DELTA, preserving the zero action.

    The input clips must be the same accepted disjoint candidates used to build
    design; build_design checks their baseline exclusion. This function sees no
    baseline mask and never creates/deletes original frames. z is converted to
    delta=(2*c/N)*z before ranking. Exact ties use earliest native start.
    """
    candidates = _clips(clips, N)
    scores = np.asarray(pred_z)
    _require(scores.shape == (len(candidates),) and scores.dtype.kind in 'fiu' and np.isfinite(scores).all(),
             'One finite z prediction per original candidate required')
    rows = []
    for index, ((clip, lo, hi), z) in enumerate(zip(candidates, scores)):
        delta = (2*(hi-lo)/int(N))*float(z)
        _require(np.isfinite(delta), 'Predicted delta conversion overflow')
        rows.append(dict(clip, candidate_index=index, predicted_z=float(z), predicted_delta=delta))
    best = max(rows, key=lambda row: (row['predicted_delta'], -row['native_start'])) if rows else None
    selected = best if best is not None and best['predicted_delta'] > 0 else None
    return dict(status='SELECT_ONE' if selected else 'ABSTAIN', selected=selected,
        predicted_delta=selected['predicted_delta'] if selected else 0.,
        best_candidate_predicted_delta=best['predicted_delta'] if best else None,
        candidate_results=rows, added_native_frames=(selected['native_end_exclusive']-selected['native_start']) if selected else 0,
        baseline_frames_removed=0,
        abstain_reason=None if selected else 'NO_CANDIDATES' if not rows else 'NO_STRICTLY_POSITIVE_PREDICTED_DELTA',
        probability_or_confidence=False, rank_by='Predicted delta=(2*c/N)*z; ties earlier native start')
