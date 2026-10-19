"""Pure source-bound clip preferences, fixed pair sampling and addition policy.

Class order is always A, B, TIE. Summary omission is never named ordinary.
Two presentation orders of a pair are correlated views, not independent data.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from numbers import Integral

import numpy as np


CLASSES = ('A', 'B', 'TIE')
WINDOW_GROUPS = 4
STRATA_QUOTAS = dict(decisive=6, tie=6, disagreement=4)


def _require(value, message):
    if not value:
        raise ValueError(message)


def _indices(value):
    a = np.asarray(value)
    _require(a.ndim == 1 and len(a) and a.dtype.kind in 'iu'
             and (a >= 0).all() and (a <= np.iinfo(np.int64).max).all(),
             'Nonempty nonnegative integer native ownership required')
    a = a.astype(np.int64)
    _require((np.diff(a) >= 0).all(), 'Native ownership must follow original frame order')
    return a


def _ownership(native_groups, old_native_groups):
    groups, cells = _indices(native_groups), _indices(old_native_groups)
    _require(groups.shape == cells.shape and np.array_equal(groups, cells//2)
             and np.array_equal(np.unique(cells), np.arange(int(cells[-1])+1)),
             'Exact original contiguous observation cells and paired native ownership required')
    counts = np.bincount(groups)
    bounds = np.r_[0, np.cumsum(counts)]
    present = set(map(int, np.unique(cells)))
    complete = [2*g in present and 2*g+1 in present for g in range(len(counts))]
    return groups, cells, counts, bounds, complete


def _window(first, bounds):
    last = first+WINDOW_GROUPS
    lo, hi = int(bounds[first]), int(bounds[last])
    return dict(start_group=first, end_group_exclusive=last,
                cell_start=2*first, cell_end_exclusive=2*last,
                native_start=lo, native_end_exclusive=hi, native_frames=hi-lo)


def full_clips(native_groups, old_native_groups):
    """Fixed nonoverlapping starts0,4,8...; an odd observed tail is incomplete."""
    _, _, counts, bounds, complete = _ownership(native_groups, old_native_groups)
    return [_window(g, bounds) for g in range(0, len(counts)-WINDOW_GROUPS+1, WINDOW_GROUPS)
            if all(complete[g:g+WINDOW_GROUPS])]


def _clip_bounds(clip, native_length):
    lo, hi = clip['native_start'], clip['native_end_exclusive']
    _require(all(isinstance(v, Integral) and not isinstance(v, (bool, np.bool_)) for v in (lo, hi))
             and 0 <= lo < hi <= native_length, 'Positive half-open clip native range required')
    lo, hi = int(lo), int(hi)
    _require('native_frames' not in clip or clip['native_frames'] == hi-lo,
             'Clip native count disagrees with original range')
    return lo, hi


def _labels(value):
    y = np.asarray(value)
    _require(y.dtype == np.bool_ and y.ndim == 2 and min(y.shape) > 0,
             'Complete original bool[N,R] labels required; unknowns cannot become zero')
    return y


def preference_votes(labels_bool_NxR, clipA, clipB):
    """Compare each original rater's native selection fractions EXACTLY."""
    y = _labels(labels_bool_NxR)
    a0, a1 = _clip_bounds(clipA, len(y)); b0, b1 = _clip_bounds(clipB, len(y))
    _require(a1 <= b0 or b1 <= a0, 'Training preference clips must not overlap')
    na, nb = a1-a0, b1-b0
    ca = list(map(int, y[a0:a1].sum(axis=0)))
    cb = list(map(int, y[b0:b1].sum(axis=0)))
    choices = [0 if a*nb > b*na else 1 if a*nb < b*na else 2 for a, b in zip(ca, cb)]
    counts = [choices.count(k) for k in range(3)]
    return dict(distribution=[n/y.shape[1] for n in counts], counts=dict(zip(CLASSES, counts)),
                raters=y.shape[1], selected_native_counts_A=ca, selected_native_counts_B=cb,
                native_frames_A=na, native_frames_B=nb,
                per_rater_preferences=[CLASSES[k] for k in choices],
                zero_is_ordinary=False)


def _distribution(value):
    p = np.asarray(value)
    _require(p.shape == (3,) and p.dtype.kind in 'fiu' and np.isfinite(p).all()
             and ((p >= 0) & (p <= 1)).all() and abs(float(p.sum())-1.) <= 1e-6,
             'Complete finite normalized A/B/TIE distribution required')
    return p.astype(np.float64)


def swapped_distribution(distribution):
    return _distribution(distribution)[[1, 0, 2]].tolist()


def make_train_pairs(sourceSHA, clips, labels, limit=16):
    """SHA-stable 6/6/4 preference strata, then SHA backfill; at most16 pairs.

    Smaller explicit limits truncate the quota passes in declared stratum order;
    the registered production recipe uses16. Returned orders share one pair ID.
    """
    _require(isinstance(sourceSHA, str) and len(sourceSHA) == 64
             and all(c in '0123456789abcdef' for c in sourceSHA), 'Original lowercase source SHA256 required')
    _require(type(limit) is int and 1 <= limit <= 16, 'At most16 distinct unordered pairs required')
    y = _labels(labels)
    ordered = sorted((dict(c) for c in clips), key=lambda c: _clip_bounds(c, len(y)))
    for previous, current in zip(ordered, ordered[1:]):
        _require(_clip_bounds(previous, len(y))[1] <= _clip_bounds(current, len(y))[0],
                 'Duplicate or overlapping clip pool is not independent full tiling')
    pool = []
    for a, b in itertools.combinations(ordered, 2):
        vote = preference_votes(y, a, b); p = vote['distribution']
        stratum = 'decisive' if max(p[:2]) > .5 else 'tie' if p[2] > .5 else 'disagreement'
        key = json.dumps([sourceSHA, _clip_bounds(a, len(y)), _clip_bounds(b, len(y))], separators=(',', ':'))
        pair_id = hashlib.sha256(('PAIR_PREFERENCE_V1:'+key).encode('ascii')).hexdigest()
        pool.append(dict(pair_id=pair_id, source_sha256=sourceSHA, clip_A=a, clip_B=b,
                         stratum=stratum, votes=vote,
                         orders=[dict(order='AB', clip_A=a, clip_B=b, target=p),
                                 dict(order='BA', clip_A=b, clip_B=a, target=swapped_distribution(p))]))
    pool.sort(key=lambda r: r['pair_id'])
    selected, seen = [], set()
    for stratum, quota in STRATA_QUOTAS.items():
        for row in [r for r in pool if r['stratum'] == stratum][:min(quota, limit-len(selected))]:
            selected.append(row); seen.add(row['pair_id'])
    for row in pool:
        if len(selected) == limit:
            break
        if row['pair_id'] not in seen:
            selected.append(row); seen.add(row['pair_id'])
    selected.sort(key=lambda r: r['pair_id'])
    _require(len(selected) == min(limit, len(pool)) == len(seen), 'Unique complete pair selection required')
    return dict(source_sha256=sourceSHA, limit=limit, quotas=dict(STRATA_QUOTAS),
                available_pairs=len(pool), selected_pairs=len(selected), ordered_examples=2*len(selected),
                available_strata={s: sum(r['stratum'] == s for r in pool) for s in STRATA_QUOTAS},
                selected_strata={s: sum(r['stratum'] == s for r in selected) for s in STRATA_QUOTAS},
                pairs=selected, two_orders_are_independent=False)


def _baseline(value, groups):
    b = np.asarray(value)
    _require(b.dtype == np.bool_ and b.shape == groups.shape, 'Exact original bool native baseline required')
    return b


def choose_anchor(native_groups, old_native_groups, baseline):
    """Closest full sliding window to the longest native baseline run's center."""
    groups, _, counts, bounds, complete = _ownership(native_groups, old_native_groups)
    base = _baseline(baseline, groups)
    edge = np.diff(np.r_[False, base, False].astype(np.int8))
    runs = [dict(native_start=int(lo), native_end_exclusive=int(hi), native_frames=int(hi-lo))
            for lo, hi in zip(np.flatnonzero(edge == 1), np.flatnonzero(edge == -1))]
    longest = min(runs, key=lambda r: (-r['native_frames'], r['native_start'])) if runs else None
    windows = []
    for g in range(len(counts)-WINDOW_GROUPS+1):
        if all(complete[g:g+WINDOW_GROUPS]):
            row = _window(g, bounds)
            if base[row['native_start']:row['native_end_exclusive']].all():
                windows.append(row)
    eligible = [r for r in windows if longest is not None
                and longest['native_start'] <= r['native_start']
                and r['native_end_exclusive'] <= longest['native_end_exclusive']]
    anchor = min(eligible, key=lambda r: (abs(r['native_start']+r['native_end_exclusive']
                    -longest['native_start']-longest['native_end_exclusive']), r['native_start'])) if eligible else None
    return dict(anchor=dict(anchor) if anchor else None, longest_baseline_run=longest,
                baseline_runs=runs, baseline_windows=windows, eligible_anchor_windows=eligible,
                abstain_reason=None if anchor else 'NO_COMPLETE_BASELINE_ANCHOR')


def prepare_policy(native_groups, old_native_groups, baseline):
    """GT-free frozen anchor and candidate inventory, before any model calls."""
    groups, _, _, _, _ = _ownership(native_groups, old_native_groups)
    base = _baseline(baseline, groups)
    result = choose_anchor(native_groups, old_native_groups, base)
    clips = full_clips(native_groups, old_native_groups)
    candidates, rejected = [], []
    for row in clips:
        overlap = int(base[row['native_start']:row['native_end_exclusive']].sum())
        if overlap:
            rejected.append(dict(row, baseline_native_frames=overlap))
        else:
            candidates.append(row)
    return dict(**result, candidates=candidates, overlap_rejected_clips=rejected,
                tiling_clip_count=len(clips), candidate_count=len(candidates),
                baseline_native_frames=int(base.sum()), native_frames=len(base))


def select_addition(native_groups, old_native_groups, baseline, candidate_probabilities):
    """Each score row has start_group/candidate_first/anchor_first distributions.

    candidate_first classA is candidate; anchor_first classB is candidate. All
    eligible candidates must have both observations, or the operation fails.
    """
    inventory = prepare_policy(native_groups, old_native_groups, baseline)
    rows = list(candidate_probabilities)
    if inventory['anchor'] is None:
        _require(not rows, 'No model predictions should be made without the fixed baseline anchor')
    score_rows = {}
    for row in rows:
        g = row['start_group']
        _require(type(g) is int and g not in score_rows, 'Unique candidate group score rows required')
        score_rows[g] = row
    candidates = inventory['candidates']
    if inventory['anchor'] is not None:
        _require(set(score_rows) == {r['start_group'] for r in candidates}, 'Missing or extraneous candidate pair prediction')
    results = []
    for clip in candidates if inventory['anchor'] is not None else []:
        row = score_rows[clip['start_group']]
        first = _distribution(row['candidate_first'])
        reverse = np.asarray(swapped_distribution(row['anchor_first']))
        results.append(dict(clip, candidate_first_mapped=first.tolist(), anchor_first_mapped=reverse.tolist(),
                            minimum_candidate_probability=float(min(first[0], reverse[0])),
                            wins_both_orders=bool(first[0] > .5 and reverse[0] > .5)))
    winners = [r for r in results if r['wins_both_orders']]
    selected = max(winners, key=lambda r: (r['minimum_candidate_probability'], -r['start_group'])) if winners else None
    reason = (inventory['abstain_reason'] if inventory['anchor'] is None else
              'NO_DISJOINT_COMPLETE_CANDIDATE' if not candidates else
              'NO_CANDIDATE_WINS_BOTH_ORDERS' if selected is None else None)
    added = selected['native_frames'] if selected else 0
    return dict(inventory, status='SELECT_ONE' if selected else 'ABSTAIN', selected=selected,
                abstain_reason=reason, candidate_results=results, added_native_frames=added,
                proposal_native_frames=inventory['baseline_native_frames']+added, baseline_frames_removed=0,
                probability_rule='Both mapped candidate probabilities strictly>0.5; choose largest minimum, ties earlier',
                uncertainty_calibrated=False, two_orders_are_independent=False)


def apply_selection(baseline, decision):
    base = np.asarray(baseline)
    _require(base.ndim == 1 and base.dtype == np.bool_, 'Original bool native baseline required')
    result = base.copy(); chosen = decision['selected']
    if chosen is not None:
        lo, hi = _clip_bounds(chosen, len(base))
        _require(not base[lo:hi].any(), 'An addition must not intersect the original baseline')
        result[lo:hi] = True
    _require(not np.any(base & ~result) and int(result.sum()-base.sum()) == decision['added_native_frames'],
             'Original baseline deletion or addition count mismatch')
    return result


def brier(predicted, target):
    """Sum squared error over all3 classes, without dividing by3."""
    return float(np.sum((_distribution(predicted)-_distribution(target))**2))


def source_metrics(records_by_source):
    """Average pairs within source, then sources equally.

    Record keys: target, first_order, reverse_order; optional same_clip=True.
    Reverse A/B probabilities are mapped back before comparison. Both-order
    Brier is averaged AFTER scoring, so inconsistent orders cannot cancel out.
    """
    per_source = {}
    for sid, records in records_by_source.items():
        values = []
        for row in records:
            target = _distribution(row['target']); first = _distribution(row['first_order'])
            reverse = np.asarray(swapped_distribution(row['reverse_order']))
            same = row.get('same_clip', False)
            _require(type(same) is bool, 'same_clip must be an explicit bool')
            if same:
                _require(np.array_equal(target, [0., 0., 1.]), 'Identical clip controls must have a true TIE target')
            values.append(dict(distribution_brier=(brier(first, target)+brier(reverse, target))/2,
                               swap_total_variation=float(np.abs(first-reverse).sum()/2),
                               target=target, prediction=(first+reverse)/2, same=same,
                               tie_probability=(float(first[2])+float(reverse[2]))/2,
                               tie_strict_argmax_both=bool(first[2] > max(first[:2]) and reverse[2] > max(reverse[:2]))))
        controls = [v for v in values if v['same']]
        per_source[sid] = dict(pairs=len(values), distribution_brier=float(np.mean([v['distribution_brier'] for v in values])) if values else None,
             swap_total_variation=float(np.mean([v['swap_total_variation'] for v in values])) if values else None,
             mean_target=np.mean([v['target'] for v in values], axis=0).tolist() if values else None,
             mean_prediction=np.mean([v['prediction'] for v in values], axis=0).tolist() if values else None,
             same_clip_controls=len(controls), same_clip_tie_probability=float(np.mean([v['tie_probability'] for v in controls])) if controls else None,
             same_clip_tie_strict_argmax_both_fraction=float(np.mean([v['tie_strict_argmax_both'] for v in controls])) if controls else None)
    scored = [r for r in per_source.values() if r['pairs']]
    controlled = [r for r in per_source.values() if r['same_clip_controls']]
    macro = {key: float(np.mean([r[key] for r in scored])) if scored else None
             for key in ('distribution_brier', 'swap_total_variation')}
    for key in ('same_clip_tie_probability', 'same_clip_tie_strict_argmax_both_fraction'):
        macro[key] = float(np.mean([r[key] for r in controlled])) if controlled else None
    return dict(per_source=per_source, macro=macro, sources_total=len(per_source), sources_scored=len(scored),
                sources_without_pairs=len(per_source)-len(scored), sources_with_same_clip_controls=len(controlled),
                averaging='Pair mean within source, then equal-source macro over applicable sources',
                brier_definition='Sum3 squared probability-minus-target errors, averaged across both mapped orders')
