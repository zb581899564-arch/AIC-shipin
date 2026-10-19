"""Pure exact-clock observation diagnostics; no decoding, fitting or selection.

Thirty-two time targets depend only on a registered native clip and its clock.
Original all-rater summary labels are inspected afterwards for observation
error. A hit on a summary-positive run does not establish visible-event or
model quality, and nearest-observation reconstruction creates no new GT.
"""
from __future__ import annotations

from bisect import bisect_left
from fractions import Fraction
from numbers import Integral

import numpy as np


SAMPLES = 32
OLD_SAMPLES = 8
APPLICABLE = 'APPLICABLE_32_DISTINCT_NATIVE_FRAMES'
INAPPLICABLE = 'INAPPLICABLE'


def _require(value, message):
    if not value:
        raise ValueError(message)


def _integer(value):
    _require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)),
             'Original native ordinals must be integers')
    return int(value)


def _exact(value):
    _require(isinstance(value, (str, Integral, Fraction)) and not isinstance(value, (bool, np.bool_)),
             'Exact native PTS required; float/bool time is not accepted')
    return Fraction(int(value)) if isinstance(value, Integral) else Fraction(value)


def _points(exact_pts):
    values = list(map(_exact, exact_pts))
    _require(values and all(a < b for a, b in zip(values, values[1:])),
             'Complete strictly increasing original native PTS required')
    return values


def _nearest(points, target, lo, hi):
    right = bisect_left(points, target, lo, hi)
    candidates = ([right-1] if right > lo else [])+([right] if right < hi else [])
    _require(candidates, 'No actual native observation in the registered clip')
    return min(candidates, key=lambda ordinal: (abs(points[ordinal]-target), ordinal))


def sample_uniform_native(exact_pts, native_start, native_end_exclusive, *, source_end_exact, samples=32):
    """Nearest native frame to start+i*duration/32, i=0..31, ties earlier.

    Bounds are original half-open native ordinals. The temporal end is PTS[hi]
    or the independently established physical source end, never inferred FPS.
    Independent nearest choices must already yield32 distinct frames; this
    function never shifts targets, removes duplicates, pads or repairs a plan.
    Inapplicability has sample_ordinals=None rather than a successful empty set.
    """
    _require(type(samples) is int and samples == SAMPLES, 'Only the fixed32-target observation hypothesis is registered')
    points = _points(exact_pts)
    lo, hi = _integer(native_start), _integer(native_end_exclusive)
    physical_end = _exact(source_end_exact)
    _require(physical_end > points[-1] and 0 <= lo < hi <= len(points),
             'Original native bounds and physical end must be valid without endpoint repair')
    start = points[lo]; end = points[hi] if hi < len(points) else physical_end
    duration = end-start
    targets = [start+i*duration/SAMPLES for i in range(SAMPLES)]
    result = dict(status=INAPPLICABLE, applicable=False, reason=None,
        sampling_method='FIXED32_UNIFORM_TIME_NEAREST_NATIVE_NOT_ACTUAL_AUDIT_ARM',
        requested_samples=SAMPLES, source_native_frames=len(points), native_range_half_open=[lo, hi],
        eligible_native_frames=hi-lo, clip_start_exact=str(start), clip_end_exact=str(end),
        clip_duration_exact=str(duration), clip_native_exact_pts=list(map(str, points[lo:hi])),
        target_exact_pts=list(map(str, targets)), sample_ordinals=None, sample_exact_pts=None,
        attempted_nearest_ordinals=None, distinct_nearest_native_frames=None,
        selection_uses_labels=False, padding_or_duplicate_repair=False, model_quality_established=False)
    if hi-lo < SAMPLES:
        result['reason'] = 'FEWER_THAN32_NATIVE_FRAMES_IN_REGISTERED_CLIP'
        return result
    nearest = [_nearest(points, target, lo, hi) for target in targets]
    result['attempted_nearest_ordinals'] = nearest
    result['distinct_nearest_native_frames'] = len(set(nearest))
    if len(set(nearest)) != SAMPLES:
        result['reason'] = 'FIXED_UNIFORM_TARGETS_DO_NOT_YIELD32_DISTINCT_NATIVE_FRAMES'
        return result
    _require(all(a < b for a, b in zip(nearest, nearest[1:])) and all(lo <= i < hi for i in nearest),
             'Nearest observations must preserve original order and exact registered domain')
    result.update(status=APPLICABLE, applicable=True, reason=None, sample_ordinals=nearest,
                  sample_exact_pts=[str(points[i]) for i in nearest])
    return result


def _ordinals(values, lo, hi, expected=None):
    values = list(map(_integer, values))
    _require(values and (expected is None or len(values) == expected)
             and all(a < b for a, b in zip(values, values[1:])) and lo <= values[0] <= values[-1] < hi,
             'Actual unique ordered observations must stay inside the original registered clip')
    return values


def augment_native_samples(exact_pts, native_start, native_end_exclusive, old_sample_ordinals,
                           *, source_end_exact, samples=32):
    """Retain actual old8, then24 label-free exact-PTS farthest-point steps.

    Every step maximizes the minimum PTS distance from the observations already
    selected. Equal distances choose the earlier native ordinal. No old sample
    is shifted or replaced, so this observation hypothesis changes density
    while retaining the old phase. This is the intended actual metadata arm.
    """
    _require(type(samples) is int and samples == SAMPLES, 'Only the fixed nested8plus24 observation hypothesis is registered')
    points = _points(exact_pts)
    lo, hi = _integer(native_start), _integer(native_end_exclusive)
    physical_end = _exact(source_end_exact)
    _require(physical_end > points[-1] and 0 <= lo < hi <= len(points),
             'Original native bounds and physical end must be valid without endpoint repair')
    old = _ordinals(old_sample_ordinals, lo, hi, OLD_SAMPLES)
    start = points[lo]; end = points[hi] if hi < len(points) else physical_end
    result = dict(status=INAPPLICABLE, applicable=False, reason=None,
        sampling_method='OLD8_PLUS24_EXACT_PTS_FARTHEST_POINT', requested_samples=SAMPLES,
        source_native_frames=len(points), native_range_half_open=[lo, hi], eligible_native_frames=hi-lo,
        clip_start_exact=str(start), clip_end_exact=str(end), clip_duration_exact=str(end-start),
        clip_native_exact_pts=list(map(str, points[lo:hi])), target_exact_pts=None,
        original_sample_ordinals=old, retained_original_observations=OLD_SAMPLES,
        sample_ordinals=None, sample_exact_pts=None, added_sample_ordinals=None,
        augmentation_step_ordinals=[], augmentation_step_min_distance_exact=[],
        selection_uses_labels=False, padding_or_duplicate_repair=False, model_quality_established=False)
    if hi-lo < SAMPLES:
        result['reason'] = 'FEWER_THAN32_NATIVE_FRAMES_IN_REGISTERED_CLIP'
        return result
    remaining = set(range(lo, hi))-set(old)
    distances = {i: min(abs(points[i]-points[j]) for j in old) for i in remaining}
    added = []
    for _ in range(SAMPLES-OLD_SAMPLES):
        winner = max(remaining, key=lambda i: (distances[i], -i))
        _require(distances[winner] > 0, 'New observation must be a distinct actual native PTS')
        result['augmentation_step_ordinals'].append(winner)
        result['augmentation_step_min_distance_exact'].append(str(distances[winner]))
        added.append(winner); remaining.remove(winner)
        for i in remaining:
            distances[i] = min(distances[i], abs(points[i]-points[winner]))
    selected = sorted(old+added)
    _require(len(selected) == len(set(selected)) == SAMPLES and set(old) <= set(selected),
             'All original8 must survive in exactly32 distinct sorted native observations')
    result.update(status=APPLICABLE, applicable=True, reason=None, sample_ordinals=selected,
        sample_exact_pts=[str(points[i]) for i in selected], added_sample_ordinals=sorted(added))
    return result


def _components(labels, lo):
    result = []
    for rater in range(labels.shape[1]):
        edges = np.diff(np.r_[False, labels[:, rater], False].astype(np.int8))
        result.append([(int(a)+lo, int(b)+lo) for a, b in
                       zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))])
    return result


def _view(labels, ordinals, lo, hi, points, full_density, components):
    observed = labels[ordinals]
    density = observed.mean(axis=0, dtype=np.float64)
    difference = density-full_density
    per_rater = []
    for rater, spans in enumerate(components):
        hits = [any(start <= ordinal < end for ordinal in ordinals) for start, end in spans]
        mass = sum(end-start for start, end in spans)
        observed_mass = sum(end-start for (start, end), hit in zip(spans, hits) if hit)
        per_rater.append(dict(rater_index=rater,
            positive_reference_components=len(spans), observed_positive_components=sum(hits),
            missed_positive_components=len(spans)-sum(hits),
            component_observation_fraction=sum(hits)/len(spans) if spans else None,
            positive_reference_component_native_frames=mass,
            hit_component_native_frames=observed_mass, missed_component_native_frames=mass-observed_mass,
            hit_component_native_mass_fraction=observed_mass/mass if mass else None,
            reference_components_native_half_open=[list(span) for span in spans], component_hits=hits))
    # Each original native PTS receives its nearest observed reference value.
    # These temporary values measure reconstruction error, and are not returned
    # as dense labels, training targets or semantic event classifications.
    sample_pts = [points[i-lo] for i in ordinals]
    assignments = [_nearest(sample_pts, point, 0, len(sample_pts)) for point in points]
    weights = np.bincount(assignments, minlength=len(ordinals)).astype(np.int64)
    reconstructed_density = np.sum(observed.astype(np.float64)*weights[:, None], axis=0)/(hi-lo)
    mismatches = np.not_equal(observed[np.asarray(assignments)], labels[lo:hi]).mean(axis=0, dtype=np.float64)
    fractions = [r['component_observation_fraction'] for r in per_rater if r['positive_reference_components']]
    mass_fractions = [r['hit_component_native_mass_fraction'] for r in per_rater if r['positive_reference_components']]
    return dict(sample_ordinals=list(ordinals), samples=len(ordinals), raters=labels.shape[1],
        density_per_rater=density.tolist(), mean_rater_density=float(density.mean()),
        signed_density_error_per_rater=difference.tolist(), absolute_density_error_per_rater=np.abs(difference).tolist(),
        mean_absolute_density_error=float(np.abs(difference).mean()),
        positive_component_observability=dict(per_rater=per_rater,
            positive_reference_components=sum(r['positive_reference_components'] for r in per_rater),
            observed_positive_components=sum(r['observed_positive_components'] for r in per_rater),
            missed_positive_components=sum(r['missed_positive_components'] for r in per_rater),
            positive_reference_component_native_frames=sum(r['positive_reference_component_native_frames'] for r in per_rater),
            hit_component_native_frames=sum(r['hit_component_native_frames'] for r in per_rater),
            missed_component_native_frames=sum(r['missed_component_native_frames'] for r in per_rater),
            raters_with_positive_components=len(fractions),
            macro_component_observation_fraction=float(np.mean(fractions)) if fractions else None,
            macro_hit_component_native_mass_fraction=float(np.mean(mass_fractions)) if mass_fractions else None,
            mass_meaning='Native size of reference components hit at least once, not total frames actually observed',
            scope='Contiguous summary-selected native runs clipped to this registered clip; not semantic events'),
        nearest_observation_native_reconstruction=dict(
            observation_native_frame_weights=weights.tolist(), native_frames=hi-lo,
            density_per_rater=reconstructed_density.tolist(),
            signed_density_error_per_rater=(reconstructed_density-full_density).tolist(),
            mean_absolute_density_error=float(np.abs(reconstructed_density-full_density).mean()),
            native_reference_disagreement_fraction_per_rater=mismatches.tolist(),
            mean_native_reference_disagreement_fraction=float(mismatches.mean()),
            tie_rule='Earlier actual sample PTS', weighting='One vote per original native frame',
            diagnostic_only=True, new_dense_GT_created=False, usable_as_training_labels=False))


def compare_observations(labels_bool_NxR, old_sample_ordinals, sampling):
    """Compare actual old8, fixed new32 and complete native all-rater labels.

    Sampling and registered clip bounds are immutable inputs. All raters remain
    in density/error averages, including all-zero references. Positive-component
    coverage is None when there are no positive components, not a perfect score.
    An inapplicable32 plan stays explicit; it never becomes a successful empty
    observation. No labels or densities can change a clip or a sampling target.
    """
    labels = np.asarray(labels_bool_NxR)
    _require(labels.dtype == np.bool_ and labels.ndim == 2 and min(labels.shape) > 0,
             'Complete original bool[N,R] labels required; no unknown-to-zero conversion')
    lo, hi = map(_integer, sampling['native_range_half_open'])
    _require(0 <= lo < hi <= len(labels) and sampling['source_native_frames'] == len(labels)
             and sampling['requested_samples'] == SAMPLES and sampling['selection_uses_labels'] is False,
             'Original complete native length and independently label-free32 plan required')
    points = _points(sampling['clip_native_exact_pts'])
    _require(len(points) == hi-lo and points[0] == _exact(sampling['clip_start_exact'])
             and points[-1] < _exact(sampling['clip_end_exact']), 'Unchanged exact local native clock required')
    old = _ordinals(old_sample_ordinals, lo, hi, OLD_SAMPLES)
    nested = sampling['sampling_method'] == 'OLD8_PLUS24_EXACT_PTS_FARTHEST_POINT'
    if nested:
        _require(sampling['original_sample_ordinals'] == old, 'Nested observation must retain these exact actual old8')
    new = None
    if sampling['status'] == APPLICABLE:
        _require(sampling['applicable'] is True and sampling['reason'] is None, 'Explicit applicable32 state required')
        new = _ordinals(sampling['sample_ordinals'], lo, hi, SAMPLES)
        _require(sampling['sample_exact_pts'] == [str(points[i-lo]) for i in new], 'Actual32 native PTS binding differs')
        if nested:
            _require(set(old) <= set(new) and sampling['added_sample_ordinals'] == sorted(set(new)-set(old))
                     and len(sampling['augmentation_step_ordinals']) == SAMPLES-OLD_SAMPLES
                     and set(sampling['augmentation_step_ordinals']) == set(new)-set(old),
                     'Nested32 must preserve all old8 and identify exactly24 added native observations')
    else:
        _require(sampling['status'] == INAPPLICABLE and sampling['applicable'] is False
                 and sampling['sample_ordinals'] is None and sampling['sample_exact_pts'] is None
                 and isinstance(sampling['reason'], str) and bool(sampling['reason']),
                 'Invalid plans must remain explicit inapplicability, never an empty success')
    full = labels[lo:hi].mean(axis=0, dtype=np.float64)
    components = _components(labels[lo:hi], lo)
    views = dict(OLD8=_view(labels, old, lo, hi, points, full, components),
                 NEW32=_view(labels, new, lo, hi, points, full, components) if new is not None else None,
                 FULL_NATIVE=_view(labels, list(range(lo, hi)), lo, hi, points, full, components))
    return dict(status='COMPLETE_REFERENCE_OBSERVATION_DIAGNOSTIC_NOT_MODEL_QUALITY',
        sampling_method=sampling['sampling_method'], nested_original8_preserved=(True if nested and new is not None else None),
        native_range_half_open=[lo, hi], native_frames=hi-lo, original_raters=labels.shape[1],
        full_native_density_per_rater=full.tolist(), full_native_mean_rater_density=float(full.mean()),
        new32_applicable=new is not None, new32_inapplicable_reason=sampling['reason'], views=views,
        all_original_raters_used=True, registered_clips_changed=False, sampling_uses_labels=False,
        original_GT_changed=False, summary_unselected_is_ordinary=False,
        model_quality_established=False, new_dense_GT_created=False, training_labels_created=False)
