"""Fixed pure continuous-IoU gain critic; no artifacts, model or data IO.

pair_features(f_raw3, r_raw3, geometry_A13, geometry_B13) -> float64[14].
Geometry vectors are supplied by the caller's bound original geometry helper.
fit([{source_id, pairs:[{pair:[a,b], x14, target}, ...exactly2]}]) -> state,report.
Each unordered pair must use canonical a<b, target=original IoU(B)-IoU(A).
Optional iou_A/iou_B fields, if supplied, are independently checked against target.
predict(state, X[K,14]) -> {JOINT14,GEOM11,MARGIN1}: float64[K].
choose_pool(gains, baseline_index=0) -> decision. The baseline gain must be zero.

Only JOINT14 is primary. These learned gains are not confidence probabilities.
"""
from __future__ import annotations

import math
from numbers import Integral, Real
import numpy as np

ARMS = ('JOINT14', 'GEOM11', 'MARGIN1')
RIDGE = .01
GEOMETRY_INDICES = tuple(range(1, 12))
STATE_KEYS = {'version', 'ridge', 'RMS', 'JOINT14_beta', 'GEOM11_beta', 'MARGIN1_beta'}


def _require(value, message):
    if not value:
        raise ValueError(message)


def _number(value):
    _require(isinstance(value, Real) and not isinstance(value, (bool, np.bool_))
             and math.isfinite(value), 'Known finite numeric value required')
    return float(value)


def _index(value):
    _require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)) and value >= 0,
             'Known nonnegative integer required')
    return int(value)


def _vector(value, size):
    _require(isinstance(value, (list, tuple, np.ndarray)), 'Explicit numeric vector required')
    raw = np.asarray(value, dtype=object)
    _require(raw.shape == (size,), 'Wrong feature/logit vector shape')
    return np.array([_number(v) for v in raw], dtype=np.float64)


def _matrix(value):
    _require(isinstance(value, (list, tuple, np.ndarray)), 'Explicit numeric design required')
    raw = np.asarray(value, dtype=object)
    _require(raw.ndim == 2 and raw.shape[1] == 14, 'Actual Kx14 design required')
    return np.array([_number(v) for v in raw.flat], dtype=np.float64).reshape(raw.shape)


def _softmax3(raw):
    values = _vector(raw, 3)
    with np.errstate(over='ignore', invalid='ignore'):
        exponential = np.exp(values-values.max())
    p = exponential/exponential.sum()
    _require(bool(np.isfinite(p).all()), 'Finite three-class softmax required')
    return values, p


def pair_features(forward_raw3, reverse_raw3, geometry_A13, geometry_B13):
    """A/B forward and B/A reverse, preserving exact swap-odd features."""
    f, pf = _softmax3(forward_raw3); r, pr = _softmax3(reverse_raw3)
    a, b = _vector(geometry_A13, 13), _vector(geometry_B13, 13)
    _require(a[0] == b[0] == 1. and a[12] == b[12], 'Original13 geometry with one source aspect required')
    if np.array_equal(a, b):
        _require(np.array_equal(f, r), 'Self pair must adopt the exact same successful raw, never a different forward')
    with np.errstate(over='ignore', invalid='ignore'):
        s = ((f[1]-f[0])+(r[0]-r[1]))/2.
        t = (pf[2]+pr[2])/2.
        # Written symmetrically so swapping f/r only exchanges the first two terms.
        u = .5*(abs(pf[0]-pr[1])+abs(pf[1]-pr[0])+abs(pf[2]-pr[2]))
        result = np.concatenate(([s, s*t, s*u], (b-a)[list(GEOMETRY_INDICES)]))
    _require(result.shape == (14,) and bool(np.isfinite(result).all()), 'Finite14 swap-odd features required')
    result[result == 0.] = 0.  # Canonical positive zero for self/control artifacts.
    if np.array_equal(a, b):
        _require(bool((result == 0.).all()), 'Every self-pair gain feature must be exactly zero')
    return result


def _columns(arm):
    return slice(None) if arm == 'JOINT14' else slice(3, 14) if arm == 'GEOM11' else slice(0, 1)


def _training_rows(source_rows):
    _require(isinstance(source_rows, (list, tuple)) and len(source_rows) > 0, 'Nonempty fixed train sources required')
    design, target, identities = [], [], []
    for source in source_rows:
        sid = source['source_id']
        _require(isinstance(sid, str) and sid and sid not in identities, 'Unique explicit train source identities required')
        _require(source.get('role', 'train') == 'train', 'Evaluation/unknown sources cannot enter a critic fit')
        identities.append(sid)
        pairs = source['pairs']
        _require(isinstance(pairs, (list, tuple)) and len(pairs) == 2, 'Exactly two unordered pairs per train source')
        seen = set()
        for pair in pairs:
            indices = pair['pair']
            _require(isinstance(indices, (list, tuple)) and len(indices) == 2, 'Canonical unordered candidate pair required')
            a, b = map(_index, indices)
            _require(a < b and (a, b) not in seen, 'Unordered pairs must be distinct canonical a<b; mirrors are not samples')
            seen.add((a, b))
            y = _number(pair['target'])
            _require(-1. <= y <= 1., 'True original-IoU difference must lie in[-1,1]')
            _require(('iou_A' in pair) == ('iou_B' in pair), 'Both original IoUs or neither must be supplied')
            if 'iou_A' in pair:
                ia, ib = _number(pair['iou_A']), _number(pair['iou_B'])
                _require(0 <= ia <= 1 and 0 <= ib <= 1 and y == ib-ia, 'Target differs from original IoU(B)-IoU(A)')
            x = _vector(pair['x14'], 14)
            _require(bool((x != 0.).any()) or y == 0., 'Zero difference observation cannot have a nonzero target')
            design.append(x); target.append(y)
    # Exactly two pairs per source: source-equal pair-mean weights sum to one.
    weights = np.full(len(design), 1./(2*len(identities)), dtype=np.float64)
    return np.stack(design), np.asarray(target, np.float64), weights, identities


def fit(source_rows):
    """Exactly three .01-ridge solves; no intercept or X/y centering."""
    x, y, weights, identities = _training_rows(source_rows)
    with np.errstate(over='ignore', invalid='ignore'):
        rms = np.sqrt(weights@(x*x))
    _require(bool(np.isfinite(rms).all()), 'Nonfinite train-only RMS')
    rms[rms == 0.] = 1.
    z = x/rms
    state = dict(version=np.array(1, np.int64), ridge=np.array(RIDGE, np.float64), RMS=rms)
    metrics = {}
    for arm in ARMS:
        a = z[:, _columns(arm)]
        beta = np.linalg.solve(a.T@(weights[:, None]*a)+RIDGE*np.eye(a.shape[1]), a.T@(weights*y))
        _require(bool(np.isfinite(beta).all()), 'Nonfinite fixed critic solve')
        state[arm+'_beta'] = beta
        metrics[arm] = dict(parameters=len(beta), train_source_equal_MSE=float(weights@((a@beta-y)**2)),
                            primary=arm == 'JOINT14', package_eligible_arm=arm == 'JOINT14')
    return state, dict(primary='JOINT14', arms=metrics, sources=len(identities), unordered_pairs=len(x),
        source_ids=identities, source_equal_pair_mean=True, weight_sum=float(weights.sum()), ridge=RIDGE,
        intercept=False, source_centered_X=False, source_centered_targets=False, global_centering=False,
        RMS_train_only=True, zero_RMS_replaced_by=1., solves=3, train_metrics_are_not_quality=True,
        MARGIN1_positive_beta_same_sign_as_raw_margin=bool(state['MARGIN1_beta'][0] > 0.),
        MARGIN1_package_eligible=False, controls_may_not_replace_primary=True)


def _state(state):
    _require(isinstance(state, dict) and set(state) == STATE_KEYS, 'Exact flat immutable critic state required')
    _require(np.asarray(state['version']).shape == () and np.asarray(state['version']).dtype == np.int64
             and int(state['version']) == 1
             and np.asarray(state['ridge']).shape == () and float(state['ridge']) == RIDGE, 'Fixed critic version/ridge differs')
    rms = _vector(state['RMS'], 14)
    _require(bool((rms > 0.).all()), 'Positive train-only RMS required')
    betas = {arm: _vector(state[arm+'_beta'], {'JOINT14': 14, 'GEOM11': 11, 'MARGIN1': 1}[arm]) for arm in ARMS}
    return rms, betas


def predict(state, design):
    rms, betas = _state(state); x = _matrix(design); z = x/rms
    result = {arm: z[:, _columns(arm)]@betas[arm] for arm in ARMS}
    for arm, values in result.items():
        _require(bool(np.isfinite(values).all()), 'Nonfinite expected-IoU-gain prediction')
        values[values == 0.] = 0.
    return result


def choose_pool(predicted_gains, baseline_index=0):
    _require(isinstance(predicted_gains, (list, tuple, np.ndarray)) and len(predicted_gains) > 0,
             'Nonempty complete native candidate gains required')
    gains = _vector(predicted_gains, len(predicted_gains)); baseline = _index(baseline_index)
    _require(baseline < len(gains) and gains[baseline] == 0., 'Actual baseline self gain must be exactly zero')
    index = max(range(len(gains)), key=lambda i: (float(gains[i]), i == baseline, -i))
    _require(index == baseline or gains[index] > 0., 'Only a strictly positive expected gain can change BASE')
    return dict(selected_index=index, baseline_index=baseline, changed=index != baseline,
                predicted_gain=float(gains[index]), candidates=len(gains), max_one=True,
                predicted_gain_is_calibrated_confidence=False)


def quality_checks(summary, phase, self_gain_zero_count, invalid_count, new_geometry_mean, original_geometry_mean):
    """Fixed JOINT14 research gate; external artifact binding belongs to caller."""
    _require(phase in ('screen20', 'confirm19'), 'Only fixed screen20/confirm19 scopes')
    expected, minimum_gain, minimum_improved = (20, .01, 5) if phase == 'screen20' else (19, .005, 3)
    count = _index(summary['sources']); improved = _index(summary['improved']); changed = _index(summary['changed'])
    zeros = _index(self_gain_zero_count); invalid = _index(invalid_count)
    gain = _number(summary['mean_gain']); loss = _number(summary['worst_loss']); selected = _number(summary['mean_selected_iou'])
    new_geometry, original_geometry = _number(new_geometry_mean), _number(original_geometry_mean)
    _require(0 <= improved <= changed <= count and 0 <= zeros <= count and -1 <= gain <= 1 and 0 <= loss <= 1
             and all(0 <= value <= 1 for value in (selected, new_geometry, original_geometry)), 'Invalid source/IoU summary')
    checks = dict(source_count=count == expected, mean_gain=gain >= minimum_gain,
        improved_sources=improved >= minimum_improved, worst_loss=loss <= .10,
        actual_changed=changed > 0, invalid_zero=invalid == 0, all_self_gain_exact_zero=zeros == expected,
        beats_new_GEOM11=selected > new_geometry, beats_original33_geometry=selected > original_geometry)
    return dict(primary='JOINT14', phase=phase, checks=checks, admitted=all(checks.values()),
        thresholds=dict(sources=expected, minimum_mean_gain=minimum_gain, minimum_improved=minimum_improved, maximum_worst_loss=.10),
        controls_may_not_replace_primary=True, scope='FIXED_CONTINUOUS_UTILITY_RESEARCH_NOT_OFFICIAL_SCORE')
