"""Fixed CPU full-output representation readout; no artifacts or model IO.

fit([{source_id,role:'train',pairs:[{pair:[a,b],x4096,geometry_delta11,
digit_delta3,target[,iou_A,iou_B]}, ...exactly2]}]) -> (numeric_state, report).
Exactly602 unique sources; target is original IoU(B)-IoU(A). A single globally
bound4096-token selection is supplied by the caller, never per-source tokens.
predict(state,X4096[K,4096],G11[K,11]) -> FULL43/GEOM11 arrays.

No centering or smoothing. RMS and uncentered thin SVD are train-only. The
digit/common-mode projection is diagnostic only and never transforms features.
Caller enforces the registered900s CPU budget/deadline and artifact identities.
"""
from __future__ import annotations

import math
from numbers import Integral, Real

import numpy as np

SOURCES = 602
PAIRS_PER_SOURCE = 2
INPUT_DIM = 4096
PCS = 32
GEOMETRY_DIM = 11
RIDGE = .01
MIN_RATIO = 1e-6
ARMS = ('FULL43', 'GEOM11')
STATE_KEYS = {'version', 'ridge', 'RMS4096', 'PCA32', 'singular_values', 'RMS43', 'FULL43_beta', 'GEOM11_beta'}


class ReadoutStop(ValueError):
    """Valid, pre-registered structural STOP rather than an engineering failure."""
    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = dict(diagnostics)


def _require(value, message):
    if not value:
        raise ValueError(message)


def _number(value):
    _require(isinstance(value, Real) and not isinstance(value, (bool, np.bool_)) and math.isfinite(value),
             'Known finite numeric value required')
    return float(value)


def _index(value):
    _require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)) and value >= 0,
             'Known nonnegative integer required')
    return int(value)


def _array(value, shape):
    _require(isinstance(value, (list, tuple, np.ndarray)), 'Explicit numeric array required')
    if not isinstance(value, np.ndarray):
        raw = np.asarray(value, dtype=object)
        _require(not any(isinstance(v, (bool, np.bool_)) for v in raw.flat), 'Boolean is not a known numeric feature')
    result = np.asarray(value)
    _require(result.shape == shape and result.dtype.kind in 'fiu', 'Wrong numeric array shape/dtype')
    result = np.asarray(result, dtype=np.float64)
    _require(bool(np.isfinite(result).all()), 'Nonfinite feature/state array')
    return result


def _matrix(value, columns):
    _require(isinstance(value, (list, tuple, np.ndarray)), 'Explicit numeric design required')
    result = np.asarray(value)
    _require(result.ndim == 2 and result.shape[1] == columns, 'Wrong design column count')
    return _array(result, result.shape)


def _source_rows(rows):
    _require(isinstance(rows, (list, tuple)) and len(rows) == SOURCES, 'Exactly602 train sources required')
    identities, x, geometry, digits, target = [], [], [], [], []
    for source in rows:
        sid = source['source_id']
        _require(isinstance(sid, str) and sid and sid not in identities and source.get('role', 'train') == 'train',
                 'Unique602 explicit train identities; no evaluation sources')
        identities.append(sid)
        pairs = source['pairs']
        _require(isinstance(pairs, (list, tuple)) and len(pairs) == PAIRS_PER_SOURCE, 'Exactly2 unordered pairs/source')
        seen = set()
        for pair in pairs:
            indices = pair['pair']
            _require(isinstance(indices, (list, tuple)) and len(indices) == 2, 'Canonical unordered candidate indices required')
            a, b = map(_index, indices)
            _require(a < b and (a, b) not in seen, 'Canonical distinct a<b pairs; reversed rows are not extra samples')
            seen.add((a, b)); y = _number(pair['target'])
            _require(-1 <= y <= 1, 'Original IoU(B)-IoU(A) target outside[-1,1]')
            _require(('iou_A' in pair) == ('iou_B' in pair), 'Both original IoUs or neither required')
            if 'iou_A' in pair:
                ia, ib = _number(pair['iou_A']), _number(pair['iou_B'])
                _require(0 <= ia <= 1 and 0 <= ib <= 1 and y == ib-ia, 'Target sign/value differs from original IoU(B)-IoU(A)')
            x.append(_array(pair['x4096'], (INPUT_DIM,)))
            geometry.append(_array(pair['geometry_delta11'], (GEOMETRY_DIM,)))
            digits.append(_array(pair['digit_delta3'], (3,)))
            target.append(y)
    weights = np.full(SOURCES*PAIRS_PER_SOURCE, 1./(SOURCES*PAIRS_PER_SOURCE), dtype=np.float64)
    return np.stack(x), np.stack(geometry), np.stack(digits), np.asarray(target, np.float64), weights, identities


def _outside_nuisance_diagnostic(x, digits):
    """Rank-aware QR span of digit differences plus within-row raw mean.

    Stable independent-column selection removes numerically dependent/zero
    nuisance columns before QR. Its tolerance is machine precision, not tuned.
    This projection is NEVER supplied to RMS, PCA, regression or prediction.
    """
    x = _matrix(x, x.shape[1]); digits = _array(digits, (len(x), 3))
    nuisance = np.column_stack((digits, x.mean(axis=1)))
    scale = float(np.max(np.linalg.norm(nuisance, axis=0)))
    tolerance = np.finfo(np.float64).eps*max(nuisance.shape)*scale
    basis, selected = [], []
    for index in range(4):
        residual = nuisance[:, index].copy()
        for _ in range(2):
            for column in basis:
                residual -= column*(column@residual)
        length = float(np.linalg.norm(residual))
        _require(math.isfinite(length), 'Nonfinite nuisance QR norm')
        if length > tolerance:
            basis.append(residual/length); selected.append(index)
    if selected:
        q, _ = np.linalg.qr(nuisance[:, selected], mode='reduced')
        residual = x-q@(q.T@x)
    else:
        residual = x
    with np.errstate(over='ignore', invalid='ignore'):
        total = float(np.sum(x*x)); remaining = float(np.sum(residual*residual))
    _require(math.isfinite(total) and math.isfinite(remaining), 'Nonfinite raw-feature diagnostic energy')
    ratio = remaining/total if total > 0 else 0.
    diagnostics = dict(raw_frobenius_energy=total, residual_frobenius_energy=remaining,
        residual_energy_ratio=ratio, minimum_residual_energy_ratio=MIN_RATIO,
        nuisance_columns=4, nuisance_QR_rank=len(selected), independent_nuisance_columns=selected,
        nuisance_numerical_rank_tolerance=tolerance, projection_applied_to_features=False,
        claims_new_visual_information=False, SVD_computed=False)
    if ratio <= MIN_RATIO:
        raise ReadoutStop('STOP_FULL_OUTPUT_NO_ENERGY_OUTSIDE_DIGIT_COMMONMODE', diagnostics)
    return diagnostics


def _pca32(normalized, diagnostics):
    """Uncentered thin SVD; fixed32, deterministic per-row sign convention."""
    normalized = _matrix(normalized, normalized.shape[1])
    _require(min(normalized.shape) >= PCS, 'Design must support32 components')
    _, singular, vt = np.linalg.svd(normalized, full_matrices=False)
    _require(singular.shape == (min(normalized.shape),) and vt.shape == (min(normalized.shape), normalized.shape[1])
        and bool(np.isfinite(singular).all()) and bool(np.isfinite(vt).all()) and bool((singular >= 0).all()),
        'Invalid finite thin SVD output')
    largest = float(singular[0]); smallest = float(singular[PCS-1])
    rank_tolerance = np.finfo(np.float64).eps*max(normalized.shape)*largest
    rank = int(np.count_nonzero(singular > rank_tolerance))
    ratio = smallest/largest if largest > 0 else 0.
    diagnostics = dict(diagnostics, SVD_computed=True, numerical_rank=rank,
        rank_tolerance=rank_tolerance, required_components=PCS, s1=largest, s32=smallest,
        s32_over_s1=ratio, minimum_s32_over_s1=MIN_RATIO)
    if rank < PCS or ratio <= MIN_RATIO:
        raise ReadoutStop('STOP_FULL_OUTPUT_INSUFFICIENT_FIXED32_RANK', diagnostics)
    components = np.asarray(vt[:PCS], dtype=np.float64).copy()
    for row in components:
        anchor = int(np.argmax(np.abs(row)))
        if row[anchor] < 0:
            row *= -1.
    components[components == 0.] = 0.
    return components, singular.copy(), diagnostics


def _rms(x, weights):
    with np.errstate(over='ignore', invalid='ignore'):
        result = np.sqrt(weights@(x*x))
    _require(bool(np.isfinite(result).all()), 'Nonfinite train-only RMS')
    result[result == 0.] = 1.
    return result


def fit(source_rows):
    x, geometry, digits, y, weights, identities = _source_rows(source_rows)
    diagnostics = _outside_nuisance_diagnostic(x, digits)
    rms4096 = _rms(x, weights)
    pca, singular, diagnostics = _pca32(x/rms4096, diagnostics)
    scores = (x/rms4096)@pca.T
    joined = np.column_stack((scores, geometry))
    rms43 = _rms(joined, weights); design = joined/rms43
    state = dict(version=np.array(1, np.int64), ridge=np.array(RIDGE, np.float64), RMS4096=rms4096,
        PCA32=pca, singular_values=singular, RMS43=rms43)
    metrics = {}
    for arm, a in (('FULL43', design), ('GEOM11', design[:, PCS:])):
        beta = np.linalg.solve(a.T@(weights[:, None]*a)+RIDGE*np.eye(a.shape[1]), a.T@(weights*y))
        _require(bool(np.isfinite(beta).all()), 'Nonfinite fixed full-output solve')
        state[arm+'_beta'] = beta
        metrics[arm] = dict(parameters=len(beta), train_source_equal_MSE=float(weights@((a@beta-y)**2)),
            primary=arm == 'FULL43', package_eligible_arm=arm == 'FULL43')
    report = dict(primary='FULL43', arms=metrics, sources=SOURCES, unordered_pairs=len(x), source_ids=identities,
        source_equal_pair_mean=True, weight_sum=float(weights.sum()), ridge=RIDGE, solves=2, intercept=False,
        global_centering=False, source_centered_X=False, source_centered_targets=False,
        smoothing=False, PCA_centering=False, RMS_train_only=True, zero_RMS_replaced_by=1.,
        input_dimension=INPUT_DIM, fixed_components=PCS, primary_dimension=43,
        PCA_sign_convention='FIRST_MAX_ABS_ENTRY_POSITIVE', diagnostics=diagnostics,
        prediction_arrays=['RMS4096', 'PCA32', 'RMS43', 'FULL43_beta', 'GEOM11_beta'],
        diagnostic_only_arrays=['singular_values'], primary_prediction_parameters=INPUT_DIM+PCS*INPUT_DIM+43+43,
        train_metrics_are_not_quality=True, claims_new_visual_information=False,
        controls_may_not_replace_primary=True, requires_caller_cpu_budget_seconds=900)
    return state, report


def _state(state):
    _require(isinstance(state, dict) and set(state) == STATE_KEYS, 'Exact numeric full-output state required')
    version, ridge = np.asarray(state['version']), np.asarray(state['ridge'])
    _require(version.shape == () and version.dtype == np.int64 and int(version) == 1
        and ridge.shape == () and ridge.dtype == np.float64 and float(ridge) == RIDGE, 'Fixed state version/ridge differs')
    rms4096 = _array(state['RMS4096'], (INPUT_DIM,)); pca = _array(state['PCA32'], (PCS, INPUT_DIM))
    singular = _array(state['singular_values'], (SOURCES*PAIRS_PER_SOURCE,))
    rms43 = _array(state['RMS43'], (PCS+GEOMETRY_DIM,))
    _require(bool((rms4096 > 0).all()) and bool((rms43 > 0).all())
        and bool((singular >= 0).all()) and bool((singular[:-1] >= singular[1:]).all()), 'Invalid RMS/spectrum state')
    betas = dict(FULL43=_array(state['FULL43_beta'], (PCS+GEOMETRY_DIM,)),
                 GEOM11=_array(state['GEOM11_beta'], (GEOMETRY_DIM,)))
    return rms4096, pca, rms43, betas


def predict(state, X4096, G11):
    rms4096, pca, rms43, betas = _state(state)
    x = _matrix(X4096, INPUT_DIM); geometry = _array(G11, (len(x), GEOMETRY_DIM))
    joined = np.column_stack(((x/rms4096)@pca.T, geometry))/rms43
    result = dict(FULL43=joined@betas['FULL43'], GEOM11=joined[:, PCS:]@betas['GEOM11'])
    for values in result.values():
        _require(bool(np.isfinite(values).all()), 'Nonfinite predicted IoU gain')
        values[values == 0.] = 0.
    return result


def choose_pool(predicted_gains, baseline_index=0):
    _require(isinstance(predicted_gains, (list, tuple, np.ndarray)) and len(predicted_gains) > 0, 'Complete nonempty gains required')
    gains = _array(predicted_gains, (len(predicted_gains),)); baseline = _index(baseline_index)
    _require(baseline < len(gains) and gains[baseline] == 0., 'Exact baseline self gain zero required')
    index = max(range(len(gains)), key=lambda i:(float(gains[i]), i == baseline, -i))
    _require(index == baseline or gains[index] > 0., 'Change only on strictly positive expected gain')
    return dict(selected_index=index, baseline_index=baseline, changed=index != baseline,
        predicted_gain=float(gains[index]), candidates=len(gains), max_one=True, predicted_gain_is_confidence=False)


def quality_checks(summary, phase, self_gain_zero_count, invalid_count, new_geometry_mean, original_geometry_mean,
                   action_differs_old47_margin):
    _require(phase in ('screen20', 'confirm19'), 'Only fixed screen20/confirm19 quality scopes')
    _require(type(action_differs_old47_margin) is bool, 'Explicit actual action-difference evidence required')
    expected, minimum_gain, minimum_improved = (20, .01, 5) if phase == 'screen20' else (19, .005, 3)
    count, improved, changed = map(_index, (summary['sources'], summary['improved'], summary['changed']))
    zeros, invalid = _index(self_gain_zero_count), _index(invalid_count)
    gain, loss, selected = map(_number, (summary['mean_gain'], summary['worst_loss'], summary['mean_selected_iou']))
    new_geometry, original_geometry = _number(new_geometry_mean), _number(original_geometry_mean)
    _require(0 <= improved <= changed <= count and 0 <= zeros <= count and -1 <= gain <= 1 and 0 <= loss <= 1
        and all(0 <= v <= 1 for v in (selected, new_geometry, original_geometry)), 'Invalid source/quality summary')
    checks = dict(source_count=count == expected, mean_gain=gain >= minimum_gain, improved_sources=improved >= minimum_improved,
        worst_loss=loss <= .10, actual_changed=changed > 0, invalid_zero=invalid == 0,
        all_self_gain_exact_zero=zeros == expected, beats_new_GEOM11=selected > new_geometry,
        beats_original33_geometry=selected > original_geometry, action_differs_old47_margin=action_differs_old47_margin)
    return dict(primary='FULL43', phase=phase, checks=checks, admitted=all(checks.values()),
        thresholds=dict(sources=expected, minimum_mean_gain=minimum_gain, minimum_improved=minimum_improved, maximum_worst_loss=.10),
        controls_may_not_replace_primary=True, scope='FIXED_FULL_OUTPUT_READOUT_RESEARCH_NOT_OFFICIAL_OR_NEW_VISUAL_INFORMATION')
