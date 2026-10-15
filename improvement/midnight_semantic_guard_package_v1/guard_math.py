"""SEMANTIC_GUARD native-frame event selection, without files or inference.

Raw semantic proposals are protection evidence only.  They never add frames.
All interval operations are half-open on the previously accepted native clock.
"""
from bisect import bisect_left

from package_math import (SKIP_DROP, SKIP_NO64, bound_event, exact, interval,
                          require, validate_parsed)

ARM = 'SEMANTIC_GUARD'
SEMANTIC_FIELDS = ('action', 'reaction', 'information')


def event_native_keys(source, selected_interval_exact, points):
    if selected_interval_exact is None:
        return set()
    start, end = interval(selected_interval_exact)
    return {(source, ordinal) for ordinal in range(bisect_left(points, start), bisect_left(points, end))}


def semantic_native_keys(entry, points):
    """Map the three actual []/[a,b] fields; b=64 uses the explicit old end."""
    source, ordinals, samples = entry['source_id'], entry['source_ordinals'], entry['exact_pts']
    require(isinstance(ordinals, list) and len(ordinals) == len(samples) == 64 and
            all(type(ordinal) is int and 0 <= ordinal < len(points) for ordinal in ordinals) and
            all(a < b for a, b in zip(ordinals, ordinals[1:])), 'Actual distinct 64 native observations required')
    require(list(map(exact, samples)) == [points[ordinal] for ordinal in ordinals],
            'Exact sample PTS differ from the previously accepted native clock')
    lo, hi = interval(entry['window_exact'])
    native_end, end_ordinal = exact(entry['window_native_end_exact']), entry['window_native_end_ordinal']
    require(all(lo <= points[ordinal] < hi for ordinal in ordinals) and
            type(end_ordinal) is int and ordinals[-1] < end_ordinal <= len(points) and
            lo < native_end <= hi and bisect_left(points, native_end) == end_ordinal,
            'Actual sample-64 exclusive native endpoint evidence differs')
    selected, witnesses = set(), []
    for field in SEMANTIC_FIELDS:
        answer = entry['parsed'][field]
        require(isinstance(answer, list) and (not answer or (len(answer) == 2 and
                all(type(value) is int for value in answer) and 0 <= answer[0] < answer[1] <= 64)),
                'Semantic field must be its original [] or one [a,b]')
        if not answer:
            continue
        a, b = answer
        first, last = ordinals[a], ordinals[b] if b < 64 else end_ordinal
        require(first < last, 'Semantic interval contains no actual native frame')
        selected.update((source, ordinal) for ordinal in range(first, last))
        witnesses.append(dict(field=field, sample_interval=list(answer), native_interval=[first, last]))
    return selected, witnesses


def case_guard(entry, points, expected_events, physical_end_exact):
    candidates = entry['candidate_events']
    require(isinstance(candidates, list) and candidates, 'Real guard case needs its original surviving candidates')
    validate_parsed(entry['parsed'], len(candidates))
    require(exact(entry['window_exact'][1]) <= exact(physical_end_exact), 'Original view exceeds accepted physical native source')
    semantic, witnesses = semantic_native_keys(entry, points)
    ids = []
    for candidate in candidates:
        event_id, original = bound_event(candidate, entry['source_id'], expected_events)
        require(original['decision'] in ('KEEP', 'UNKNOWN') and not original.get('old_structural_no64', False),
                'Old DROP/NO64 is not a new real comparative model case')
        if original.get('original_case_id') is not None:
            require(original['original_case_id'] == entry['case_id'], 'Original event belongs to another case')
        ids.append(event_id)
    require(len(ids) == len(set(ids)), 'Duplicate event in one original case')
    weakest = entry['parsed']['redundant']
    require(len(weakest) == (1 if len(candidates) >= 2 else 0), 'Use only the actual single weakest ID; no invented ranking')
    proof = dict(case_id=entry['case_id'], source_id=entry['source_id'], candidate_count=len(candidates),
                 semantic_native_intervals=witnesses, actual_model_parsed_unchanged=True,
                 deterministic_deletion_policy=ARM)
    if not weakest:
        return dict(event_ids=ids, weak_event_id=None, protected=False,
                    proof=dict(proof, decision='NO_COMPARATIVE_CANDIDATE', intersecting_native_frames=0))
    event_id = ids[weakest[0]]
    weak = event_native_keys(entry['source_id'], expected_events[event_id]['selected_interval_exact'], points)
    overlap = weak & semantic
    return dict(event_ids=ids, weak_event_id=event_id, protected=bool(overlap),
                proof=dict(proof, weak_event_id=event_id, actual_redundant_index=weakest[0],
                    weak_selected_native_frames=len(weak), intersecting_native_frames=len(overlap),
                    first_intersecting_native_ordinal=min((ordinal for _, ordinal in overlap), default=None),
                    decision='PROTECT_FULL_EVENT' if overlap else 'DELETE_WORST_EVENT'))


def select_guard(entries, baseline_keys, source_clocks, expected_events, structural_skips=()):
    """Select all retained original events; duplicates across cases are errors.

    Mechanism counts compare raw native event unions before the independent
    empty-source submission guard.  Existing KEEP/UNKNOWN geometry is fixed.
    """
    points = {}
    for source, clock in source_clocks.items():
        values = list(map(exact, clock['normalized_exact_pts']))
        require(values and values[0] == 0 and all(a < b for a, b in zip(values, values[1:])) and
                values[-1] < exact(clock['physical_end_exact']), 'Accepted complete production native clock required')
        points[source] = values

    def union(removed):
        result = set()
        for event_id, event in expected_events.items():
            require(event['source_id'] in points, 'Original event source missing from native clock')
            if event_id not in removed:
                result.update(event_native_keys(event['source_id'], event['selected_interval_exact'], points[event['source_id']]))
        return result

    require(union(set()) == baseline_keys, 'Original VERIFY event union must exactly reproduce protected baseline')
    seen_cases, seen_events, all_weak, removed, protected, proofs = set(), set(), set(), set(), set(), []
    for entry in entries:
        case, source = entry['case_id'], entry['source_id']
        require(isinstance(case, str) and case and case not in seen_cases and source in points,
                'Duplicate/missing original case or source')
        seen_cases.add(case)
        result = case_guard(entry, points[source], expected_events, source_clocks[source]['physical_end_exact'])
        require(not (seen_events & set(result['event_ids'])), 'Unexpected cross-case event repetition is an engineering failure')
        seen_events.update(result['event_ids'])
        event_id = result['weak_event_id']
        if event_id is not None:
            all_weak.add(event_id)
            (protected if result['protected'] else removed).add(event_id)
        proofs.append(result['proof'])
    skip_keys, skip_audit = set(), []
    for skip in structural_skips:
        case, source, reason = skip['case_id'], skip['source_id'], skip['reason']
        require(source in points and reason in (SKIP_DROP, SKIP_NO64) and (case, reason) not in skip_keys and
                'parsed' not in skip and 'decision_ref' not in skip, 'Invalid or fabricated original structural skip')
        skip_keys.add((case, reason))
        require(reason != SKIP_NO64 or case not in seen_cases, 'Original NO64 cannot become a new real call')
        candidates = skip['candidate_events']
        require(isinstance(candidates, list) and candidates, 'Structural skip must enumerate its original event')
        ids = []
        for candidate in candidates:
            event_id, original = bound_event(candidate, source, expected_events)
            require(event_id not in seen_events and original.get('original_case_id') == case,
                    'Structural skip conflicts with original unique event/case coverage')
            if reason == SKIP_DROP:
                require(original['decision'] == 'DROP' and original['selected_interval_exact'] is None,
                        'Old DROP structural skip cannot contribute frames')
            else:
                require(original['decision'] == 'UNKNOWN' and original['selected_interval_exact'] is not None and
                        original.get('old_structural_no64') is True, 'Only original predeclared NO64 UNKNOWN is retained')
            seen_events.add(event_id); ids.append(event_id)
        skip_audit.append(dict(case_id=case, source_id=source, reason=reason, event_ids=ids,
                               old_decision_ref=skip['old_decision_ref'], new_model_calls=0))
    require(seen_events == set(expected_events), 'Full unique original event coverage required')
    raw_selected, unprotected = union(removed), union(all_weak)
    require(unprotected <= raw_selected <= baseline_keys and removed <= all_weak and not (removed & protected),
            'Guard must only protect full original events, without new frames')
    restoration, deletion = raw_selected - unprotected, baseline_keys - raw_selected
    mechanism = dict(sources_with_real_restoration_vs_WORST_ALL=len({source for source, _ in restoration}),
        sources_with_real_deletion_vs_original_VERIFY=len({source for source, _ in deletion}),
        restored_native_frames_vs_unprotected_WORST_ALL=len(restoration), removed_native_frames=len(deletion),
        comparison_scope='RAW_NATIVE_RETAINED_EVENT_UNIONS_BEFORE_EMPTY_SOURCE_FORMAT_GUARD')
    selected, guarded = set(raw_selected), []
    present = {source for source, _ in selected}
    for source in points:
        if source not in present:
            original = {key for key in baseline_keys if key[0] == source}
            require(original, 'Original protected source must be nonempty')
            selected.update(original); guarded.append(source)
    return dict(selected_keys=selected, empty_source_format_guard=guarded,
        removed_event_ids=sorted(removed), protected_event_ids=sorted(protected), decision_proofs=proofs,
        structural_skips=skip_audit, mechanism=mechanism, added_frames=0,
        removed_frames=len(baseline_keys-selected), actual_model_parsed_unchanged=True,
        deterministic_deletion_policy=ARM, semantic_proposals_added_as_predictions=False)
