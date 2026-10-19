"""Fixed pure v33 crop selection/control/metrics; no artifacts or model IO.

Human-IoU targets are single-editor-derived. Oracle is diagnostic only;
admission checks describe historical static research, never official quality.
"""
from __future__ import annotations

import math
from numbers import Integral, Real

import numpy as np

RIDGE = 0.01
FEATURES = 13


def _require(value, message):
    if not value:
        raise ValueError(message)


def _index(value):
    _require(isinstance(value, Integral) and not isinstance(value, bool) and value >= 0,
             'Known nonnegative integer index/count required')
    return int(value)


def _finite(value):
    _require(isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value),
             'Known finite numeric value required')
    return float(value)


def _iou(value):
    value = _finite(value)
    _require(0 <= value <= 1, 'Known original candidate IoU in[0,1] required')
    return value


def _probabilities(values):
    _require(isinstance(values, (list, tuple, np.ndarray)) and len(values) == 3,
             'Three actual probabilities in class0/1/2 order required')
    result = np.array([_finite(v) for v in values], dtype=np.float64)
    _require(bool(((result >= 0) & (result <= 1)).all())
        and math.isclose(float(result.sum()), 1., rel_tol=0., abs_tol=1e-6),
        'Probabilities must be finite, nonnegative and sum to1; never renormalize')
    return result


def _pool(pool):
    _require(isinstance(pool, (list, tuple)) and len(pool) > 0, 'Nonempty fixed native crop pool required')
    checked = []
    for box in pool:
        _require(isinstance(box, (list, tuple)) and len(box) == 3
            and all(isinstance(v, Integral) and not isinstance(v, bool) for v in box),
            'Native integer[x,y,w] pool required')
        x, y, w = map(int, box)
        _require(x >= 0 and y >= 0 and w > 0, 'Positive legal native candidate required')
        checked.append((x, y, w))
    _require(len(set(checked)) == len(checked), 'Fixed pool must already be deduplicated')
    return checked


def strict_tie(probabilities):
    """samecrop control passes only when class2 is the unique maximum."""
    probs = _probabilities(probabilities)
    return bool(probs[2] > probs[0] and probs[2] > probs[1])


def select_pool(pool, baseline_index, pairs):
    """Forward is BASE=A/candidate=B; reverse is candidate=A/BASE=B.

    Both winning probabilities must exceed .5. Maximize their minimum,
    then prefer the earlier candidate index. Missing pairs are errors.
    """
    boxes = _pool(pool)
    baseline = _index(baseline_index)
    _require(baseline < len(boxes), 'Baseline index outside fixed pool')
    _require(isinstance(pairs, (list, tuple)), 'Complete alternative comparison list required')
    seen, winners = set(), []
    for pair in pairs:
        _require(isinstance(pair, dict) and set(pair) == {'candidate_index', 'forward_probs', 'reverse_probs'},
                 'Explicit probability-only pair schema required')
        index = _index(pair['candidate_index'])
        _require(index < len(boxes) and index != baseline and index not in seen,
                 'Unknown, duplicate or baseline candidate comparison')
        seen.add(index)
        forward, reverse = _probabilities(pair['forward_probs']), _probabilities(pair['reverse_probs'])
        if forward[1] > .5 and reverse[0] > .5:
            winners.append((min(float(forward[1]), float(reverse[0])), index))
    _require(seen == set(range(len(boxes)))-{baseline}, 'Missing fixed candidate pair; no silent abstention')
    return max(winners, key=lambda item: (item[0], -item[1]))[1] if winners else baseline


def geometry_features(box, width, height):
    """Fixed unnormalized13-vector; all coordinates use original dimensions."""
    width, height = _index(width), _index(height)
    _require(min(width, height) > 0, 'Positive original dimensions required')
    x, y, w = _pool([box])[0]
    _require(x+w <= width and 16*y+9*w <= 16*height, 'Candidate outside original native geometry')
    x, y, w, h = x/width, y/height, w/width, 9*w/(16*height)
    return np.array([1., x, y, w, h, x*x, y*y, w*w, h*h, x*y, x*w, y*h,
                     math.log(width/height)], dtype=np.float64)


def fit_geometry(train_sources):
    """Source-equal candidate MSE + .01 ridge, intercept unpenalized.

    Caller binds the actual602 fit scope and persists the returned float64
    coefficients. No normalization, hyperparameter selection or file reads.
    """
    _require(isinstance(train_sources, (list, tuple)) and len(train_sources) > 0,
             'Nonempty fixed training sources required')
    count = len(train_sources)
    matrix, target = np.zeros((FEATURES, FEATURES), dtype=np.float64), np.zeros(FEATURES, dtype=np.float64)
    seen = set()
    for source in train_sources:
        identity = source['source_id']
        _require(isinstance(identity, str) and identity and identity not in seen, 'Unique source identities required')
        seen.add(identity)
        pool = _pool(source['pool'])
        values = source['candidate_ious']
        _require(isinstance(values, (list, tuple, np.ndarray)) and len(values) == len(pool),
                 'Every fixed candidate needs its actual known IoU')
        x = np.stack([geometry_features(box, source['width'], source['height']) for box in pool])
        y = np.array([_iou(value) for value in values], dtype=np.float64)
        weight = 1./(count*len(pool))
        matrix += weight*(x.T@x)
        target += weight*(x.T@y)
    penalty = np.eye(FEATURES, dtype=np.float64)*RIDGE
    penalty[0, 0] = 0.
    beta = np.linalg.solve(matrix+penalty, target)
    _require(beta.shape == (FEATURES,) and bool(np.isfinite(beta).all()), 'Nonfinite geometry fit')
    return beta


def geometry_select(pool, width, height, beta, baseline_index=0):
    boxes = _pool(pool)
    baseline = _index(baseline_index)
    _require(baseline < len(boxes), 'Baseline index outside fixed pool')
    _require(isinstance(beta, (list, tuple, np.ndarray)) and len(beta) == FEATURES, 'Exactly13 coefficients required')
    coefficients = np.array([_finite(v) for v in beta], dtype=np.float64)
    scores = np.stack([geometry_features(box, width, height) for box in boxes])@coefficients
    _require(bool(np.isfinite(scores).all()), 'Nonfinite geometry prediction')
    return max(range(len(boxes)), key=lambda i: (float(scores[i]), i == baseline, -i))


def summarize(sources):
    """Macro over unique sources; worst_loss=max(0,BASE-selected)."""
    _require(isinstance(sources, (list, tuple)) and len(sources) > 0, 'Nonempty source metrics required')
    seen, rows = set(), []
    for source in sources:
        identity = source['source_id']
        _require(isinstance(identity, str) and identity and identity not in seen, 'Unique evaluated source identities required')
        seen.add(identity)
        baseline, selected, geometry, oracle = [_iou(source[key]) for key in
            ('baseline_iou', 'selected_iou', 'geometry_iou', 'oracle_iou')]
        _require(oracle+1e-12 >= max(baseline, selected, geometry), 'Reference-assisted oracle inconsistent with same pool')
        selected_index, baseline_index = _index(source['selected_index']), _index(source['baseline_index'])
        gain = selected-baseline
        rows.append(dict(source_id=identity, baseline_iou=baseline, selected_iou=selected,
            geometry_iou=geometry, oracle_iou=oracle, selected_index=selected_index, baseline_index=baseline_index,
            gain=gain, gain_vs_geometry=selected-geometry, changed=selected_index != baseline_index,
            improved=gain > 0., degraded=gain < 0.))
    means = {name: float(np.mean([row[name] for row in rows])) for name in
             ('baseline_iou', 'selected_iou', 'geometry_iou', 'oracle_iou')}
    return dict(sources=len(rows), mean_baseline_iou=means['baseline_iou'], mean_selected_iou=means['selected_iou'],
        mean_geometry_iou=means['geometry_iou'], mean_oracle_iou=means['oracle_iou'],
        mean_gain=means['selected_iou']-means['baseline_iou'],
        mean_gain_vs_geometry=means['selected_iou']-means['geometry_iou'],
        improved=sum(row['improved'] for row in rows), degraded=sum(row['degraded'] for row in rows),
        unchanged_iou=sum(row['gain'] == 0. for row in rows), changed=sum(row['changed'] for row in rows),
        worst_loss=max(0., max(-row['gain'] for row in rows)), per_source=rows,
        oracle_is_reference_assisted_diagnostic=True, historical_sources_not_blind=True,
        scope='STATIC_SINGLE_EDITOR_REFERENCE_RESEARCH_NOT_OFFICIAL_SCORE')


def quality_checks(summary, phase, self_tie_pass_count, invalid_count):
    _require(phase in ('screen20', 'confirm19'), 'Only frozen screen20/confirm19 phases allowed')
    expected, minimum_gain, minimum_improved = (20, .01, 5) if phase == 'screen20' else (19, .005, 3)
    count = _index(summary['sources'])
    samecrop, invalid = _index(self_tie_pass_count), _index(invalid_count)
    improved, changed = _index(summary['improved']), _index(summary['changed'])
    gain = _finite(summary['mean_gain'])
    vs_geometry = _finite(summary['mean_gain_vs_geometry'])
    loss = _finite(summary['worst_loss'])
    _require(0 <= improved <= count and 0 <= changed <= count and loss >= 0,
             'Invalid source metric counts/loss')
    checks = dict(source_count=count == expected, mean_gain=gain >= minimum_gain,
        beats_geometry=vs_geometry > 0., improved_sources=improved >= minimum_improved,
        worst_loss=loss <= .10, all_samecrop_strict_tie=samecrop == expected,
        invalid_zero=invalid == 0, actual_changed=changed > 0)
    return dict(phase=phase, checks=checks, admitted=all(checks.values()),
        thresholds=dict(sources=expected, minimum_mean_gain=minimum_gain,
            minimum_improved=minimum_improved, maximum_worst_loss=.10),
        scope='HISTORICAL_STATIC_RESEARCH_GATE_NOT_OFFICIAL_OR_BLIND_QUALITY')
