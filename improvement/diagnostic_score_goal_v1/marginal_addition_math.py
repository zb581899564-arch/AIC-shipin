"""Pure all-rater marginal F1 diagnostics for disjoint native-frame additions.

This is a reference-assisted diagnostic, not a selector or a model target
registration. Boolean human summary membership is required; omitted frames are
not named ordinary. Each original rater has equal weight. F1(empty, empty)=1;
all other F1 values are 2*intersection/(prediction_size+reference_size).
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np


GAIN_CLASSES = ('POSITIVE', 'NEGATIVE', 'ZERO')
PREFERENCE_CLASSES = ('CANDIDATE', 'ANCHOR', 'TIE')


def _require(value, message):
    if not value:
        raise ValueError(message)


def _labels(value):
    labels = np.asarray(value)
    _require(labels.dtype == np.bool_ and labels.ndim == 2 and min(labels.shape) > 0,
             'Complete original bool[N,R] labels required; unknowns cannot become zero')
    return labels


def _mask(value, size, name, *, nonempty=False):
    mask = np.asarray(value)
    _require(mask.dtype == np.bool_ and mask.shape == (size,),
             name+' must be an exact bool[N] native-frame mask')
    _require(not nonempty or bool(mask.any()), name+' must contain at least one native frame')
    return mask


def _sign(value):
    return 'POSITIVE' if value > 0 else 'NEGATIVE' if value < 0 else 'ZERO'


def _fraction_fields(value):
    return dict(numerator=value.numerator, denominator=value.denominator)


def gain_distribution(deltas):
    """Describe signed per-rater gains without majority/magnitude conflation.

    Vote fractions count raters. Magnitude probabilities divide each sign's
    absolute gain sum by the total absolute gain; ZERO has unit mass only when
    every gain is exactly zero. These are descriptive quantities, not confidence
    or a registered training objective. Fractions preserve exact cancellation.
    """
    values = list(deltas)
    _require(values, 'At least one original rater gain required')
    exact = []
    for value in values:
        _require(isinstance(value, (Fraction, int, float, np.integer, np.floating))
                 and not isinstance(value, (bool, np.bool_)), 'Finite numeric rater gain required')
        if isinstance(value, Fraction):
            item = value
        elif isinstance(value, (int, np.integer)):
            item = Fraction(int(value))
        else:
            _require(bool(np.isfinite(value)), 'Finite numeric rater gain required')
            item = Fraction(float(value))
        _require(-1 <= item <= 1, 'A paired F1 gain must lie in [-1,1]')
        exact.append(item)
    counts = {name: sum(_sign(v) == name for v in exact) for name in GAIN_CLASSES}
    positive = sum((v for v in exact if v > 0), Fraction(0))
    negative = -sum((v for v in exact if v < 0), Fraction(0))
    absolute = positive+negative
    mean = sum(exact, Fraction(0))/len(exact)
    mass = ([float(positive/absolute), float(negative/absolute), 0.]
            if absolute else [0., 0., 1.])
    return dict(class_order=list(GAIN_CLASSES), raters=len(exact), counts=counts,
                vote_fractions=[counts[name]/len(exact) for name in GAIN_CLASSES],
                positive_gain_sum=float(positive), negative_gain_magnitude_sum=float(negative),
                total_absolute_gain=float(absolute), magnitude_probabilities=mass,
                mean_delta=float(mean), mean_delta_exact=_fraction_fields(mean),
                mean_gain_sign=_sign(mean), is_confidence=False)


def f1_delta(labels_bool_NxR, baseline_bool_N, candidate_bool_N):
    """Return original-rater and macro F1 before/after a complete addition.

    Candidate is nonempty and strictly disjoint from baseline; baseline may be
    empty. For b+r>0, gain sign equals sign(s*(b+r)-t*c), where b=|B|,
    r=|reference|, t=|B intersect reference|, c=|C|, s=|C intersect reference|.
    Thus positive gain requires s/c > F1(B)/2, not a preference over an anchor.
    When b=r=0, before F1 is 1 and after F1 is 0: the nonempty addition has -1
    gain, and the regular integer numerator is intentionally None.
    """
    labels = _labels(labels_bool_NxR)
    baseline = _mask(baseline_bool_N, len(labels), 'Baseline')
    candidate = _mask(candidate_bool_N, len(labels), 'Candidate', nonempty=True)
    _require(not bool((baseline & candidate).any()), 'Candidate must not overlap any baseline native frame')
    b, c = int(baseline.sum()), int(candidate.sum())
    rows, exact_gains, exact_before, exact_after = [], [], [], []
    for index in range(labels.shape[1]):
        truth = labels[:, index]
        r = int(truth.sum()); t = int((baseline & truth).sum()); s = int((candidate & truth).sum())
        before_denominator, after_denominator = b+r, b+c+r
        before = Fraction(2*t, before_denominator) if before_denominator else Fraction(1)
        after = Fraction(2*(t+s), after_denominator)
        delta = after-before
        numerator = s*before_denominator-t*c if before_denominator else None
        positive_condition = Fraction(s, c) > before/2
        _require(positive_condition == (delta > 0), 'Exact positive marginal-F1 density identity failed')
        if numerator is not None:
            _require(_sign(numerator) == _sign(delta), 'Exact regular marginal-F1 sign identity failed')
        rows.append(dict(rater_index=index, truth_native_frames=r,
            baseline_truth_native_frames=t, candidate_truth_native_frames=s,
            before_denominator=before_denominator, after_denominator=after_denominator,
            baseline_f1=float(before), augmented_f1=float(after), f1_delta=float(delta),
            f1_delta_exact=_fraction_fields(delta), gain_sign=_sign(delta),
            regular_integer_gain_numerator=numerator,
            candidate_truth_density=float(Fraction(s, c)), positive_gain_density_threshold=float(before/2),
            candidate_density_exceeds_gain_threshold=positive_condition,
            empty_prediction_and_truth_before=(before_denominator == 0)))
        exact_gains.append(delta); exact_before.append(before); exact_after.append(after)
    macro_before = sum(exact_before, Fraction(0))/len(rows)
    macro_after = sum(exact_after, Fraction(0))/len(rows)
    distribution = gain_distribution(exact_gains)
    return dict(native_frames=len(labels), raters=len(rows), baseline_native_frames=b,
                candidate_native_frames=c, augmented_native_frames=b+c,
                baseline_macro_f1=float(macro_before), augmented_macro_f1=float(macro_after),
                macro_delta=distribution['mean_delta'], macro_delta_exact=distribution['mean_delta_exact'],
                per_rater=rows, gain_distribution=distribution,
                empty_empty_f1=1., baseline_frames_removed=0, zero_is_ordinary=False,
                reference_assisted_diagnostic=True)


def preference_comparison(labels_bool_NxR, baseline_bool_N, candidate_bool_N, anchor_bool_N):
    """Compare old candidate/anchor summary-density preference with true gain.

    Anchor must be a nonempty subset of the fixed baseline. Preferences use the
    original exact integer cross product and all original raters. A strict
    candidate rater majority is descriptive only: this function does not apply
    thresholds to model predictions or select any source/window.
    """
    result = f1_delta(labels_bool_NxR, baseline_bool_N, candidate_bool_N)
    labels = _labels(labels_bool_NxR)
    baseline = _mask(baseline_bool_N, len(labels), 'Baseline')
    candidate = _mask(candidate_bool_N, len(labels), 'Candidate', nonempty=True)
    anchor = _mask(anchor_bool_N, len(labels), 'Anchor', nonempty=True)
    _require(not bool((anchor & ~baseline).any()), 'Anchor must be wholly contained in the fixed baseline')
    c, a = result['candidate_native_frames'], int(anchor.sum())
    contingency = {gain: {pref: 0 for pref in PREFERENCE_CLASSES} for gain in GAIN_CLASSES}
    comparisons = []
    for row in result['per_rater']:
        index = row['rater_index']; s = row['candidate_truth_native_frames']
        anchor_truth = int((anchor & labels[:, index]).sum())
        cross = s*a-anchor_truth*c
        pref = 'CANDIDATE' if cross > 0 else 'ANCHOR' if cross < 0 else 'TIE'
        contingency[row['gain_sign']][pref] += 1
        comparisons.append(dict(rater_index=index, preference=pref, gain_sign=row['gain_sign'],
            anchor_truth_native_frames=anchor_truth, candidate_truth_native_frames=s,
            exact_preference_cross_product=cross,
            zero_zero_tie=(s == 0 and anchor_truth == 0),
            positive_equal_density_tie=(cross == 0 and s > 0),
            positive_gain_without_candidate_preference=(row['gain_sign'] == 'POSITIVE' and pref != 'CANDIDATE'),
            candidate_preference_without_positive_gain=(pref == 'CANDIDATE' and row['gain_sign'] != 'POSITIVE')))
    counts = {pref: sum(r['preference'] == pref for r in comparisons) for pref in PREFERENCE_CLASSES}
    majority = counts['CANDIDATE']*2 > len(comparisons)
    macro_positive = result['gain_distribution']['mean_gain_sign'] == 'POSITIVE'
    return dict(marginal=result, anchor_native_frames=a, preference_class_order=list(PREFERENCE_CLASSES),
        preference_counts=counts, preference_distribution=[counts[p]/len(comparisons) for p in PREFERENCE_CLASSES],
        candidate_has_strict_rater_majority=majority, contingency=contingency, per_rater=comparisons,
        zero_zero_tie_raters=sum(r['zero_zero_tie'] for r in comparisons),
        positive_equal_density_tie_raters=sum(r['positive_equal_density_tie'] for r in comparisons),
        positive_gain_without_candidate_preference_raters=sum(r['positive_gain_without_candidate_preference'] for r in comparisons),
        candidate_preference_without_positive_gain_raters=sum(r['candidate_preference_without_positive_gain'] for r in comparisons),
        macro_positive_without_preference_majority=macro_positive and not majority,
        preference_majority_without_macro_positive=majority and not macro_positive,
        rater_disagreement_is_TIE=False, model_probability_read=False, zero_is_ordinary=False,
        reference_assisted_diagnostic=True)
