"""Pure native-frame applications for the five new automatic decision arms.

This module reads no files, labels, media, model or quality metric.  Half-open
sample intervals are projected through the accepted full native clock.
"""
from bisect import bisect_left
from fractions import Fraction

ARMS = ("ORDINARY", "REDUNDANT", "ACTION", "REACTION", "INFORMATION")
QUALITY_ARMS = frozenset(ARMS[:2])
RISK_ARMS = frozenset(ARMS[2:])
PARSED_KEYS = {name.lower() for name in ARMS}
SKIP_DROP = "OLD_VERIFY_DROP_NO_BASELINE_CONTRIBUTION"
SKIP_NO64 = "ADOPTED_ORIGINAL_NO64_UNKNOWN_PRESERVE_BASELINE"
DELETION_POLICIES = frozenset(("WORST_ALL", "WORST_FRACTION_1_3", "WORST_PAIR_ONLY"))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def exact(value):
    require(not isinstance(value, (float, bool)), "Exact rational seconds required")
    return Fraction(value)


def interval(value):
    require(isinstance(value, list) and len(value) == 2, "Exact interval must have two endpoints")
    a, b = map(exact, value)
    require(a < b, "Exact interval must be nonempty")
    return a, b


def validate_parsed(parsed, candidate_count):
    require(isinstance(parsed, dict) and set(parsed) == PARSED_KEYS, "Five-way answer schema differs")
    for name in ("ordinary", "redundant"):
        values = parsed[name]
        require(isinstance(values, list) and all(type(v) is int and 0 <= v < candidate_count for v in values),
                "Candidate index outside this exact window")
        require(len(values) == len(set(values)), "Duplicate candidate index")
    for name in ("action", "reaction", "information"):
        values = parsed[name]
        require(isinstance(values, list) and (not values or
                (len(values) == 2 and all(type(v) is int for v in values) and 0 <= values[0] < values[1] <= 64)),
                "Recall answer must be [] or one [a,b], 0<=a<b<=64")


def validate_deletion_policy_map(value):
    if value is None:
        return
    require(isinstance(value, dict) and set(value) == QUALITY_ARMS and
            all(isinstance(policy, str) and policy in DELETION_POLICIES for policy in value.values()),
            "Deletion policy map must bind exactly ORDINARY/REDUNDANT to the three registered strategies")


def deterministic_policy_for(arm, deletion_policy_map):
    require(arm in QUALITY_ARMS, "Recall risk arms have no deletion policy")
    return deletion_policy_map[arm] if deletion_policy_map is not None else "DIRECT_PARSED_" + arm


def deletion_indices(arm, parsed, candidate_count, deletion_policy_map):
    if deletion_policy_map is None:
        return parsed[arm.lower()]
    policy = deletion_policy_map[arm]
    actual_worst = parsed["redundant"]
    require(len(actual_worst) <= 1, "Worst-candidate strategy requires at most one actual model worst index")
    apply = (candidate_count >= 2 if policy == "WORST_ALL" else
             candidate_count >= 3 if policy == "WORST_FRACTION_1_3" else candidate_count == 2)
    return actual_worst if apply else []


def union_events(events, points, removed=frozenset()):
    selected = set()
    for event_id, event in events.items():
        if event_id in removed or event["selected_interval_exact"] is None:
            continue
        a, b = interval(event["selected_interval_exact"])
        source = event["source_id"]
        selected.update((source, ordinal) for ordinal in range(bisect_left(points[source], a), bisect_left(points[source], b)))
    return selected


def bound_event(event, source, expected_events):
    event_id = event["event_id"]
    require(event_id in expected_events, "Unknown original candidate")
    original = expected_events[event_id]
    require(original["source_id"] == source and
            interval(event["original_interval_exact"]) == interval(original["original_interval_exact"]) and
            event["decision"] == original["decision"], "Candidate identity or old VERIFY decision changed")
    value, expected = event["selected_interval_exact"], original["selected_interval_exact"]
    require((value is None and expected is None) or
            (value is not None and expected is not None and interval(value) == interval(expected)),
            "Already padded protected event selection changed")
    return event_id, original


def combine(entries, baseline_keys, source_clocks, expected_events, structural_skips=(), deletion_policy_map=None):
    """Apply event removals or category recall, each independently of the rest.

    ``expected_events`` must be the frozen original VERIFY candidate decisions,
    including its already padded selected intervals and old DROP candidates.
    Reconstructing its event union must reproduce the protected ZIP exactly.
    Repeated observation of one event uses an explicit OR of removal decisions;
    no frame is removed while a different retained event still supports it.
    """
    validate_deletion_policy_map(deletion_policy_map)
    points = {}
    for source, clock in source_clocks.items():
        pts = list(map(exact, clock["normalized_exact_pts"]))
        require(pts and pts[0] == 0 and all(a < b for a, b in zip(pts, pts[1:])) and
                pts[-1] < exact(clock["physical_end_exact"]), "Malformed complete native clock")
        points[source] = pts
    require(baseline_keys and all(source in points and type(frame) is int and 0 <= frame < len(points[source])
                                 for source, frame in baseline_keys), "Protected baseline keys differ from native domain")
    require(union_events(expected_events, points) == baseline_keys,
            "Original VERIFY padded event union does not exactly reproduce protected 40.46 ZIP")
    removed = {name: set() for name in QUALITY_ARMS}
    additions = {name: set() for name in RISK_ARMS}
    witnesses = {name: [] for name in RISK_ARMS}
    seen_cases, seen_events = set(), set()
    for entry in entries:
        case_id, source = entry["case_id"], entry["source_id"]
        require(isinstance(case_id, str) and case_id and case_id not in seen_cases, "Duplicate/missing production case")
        seen_cases.add(case_id)
        require(source in points, "Unregistered production source")
        pts = points[source]
        ordinals, sample_pts = entry["source_ordinals"], entry["exact_pts"]
        require(isinstance(ordinals, list) and len(ordinals) == 64 and len(sample_pts) == 64 and
                all(type(v) is int and 0 <= v < len(pts) for v in ordinals) and
                all(a < b for a, b in zip(ordinals, ordinals[1:])), "Actual 64 distinct native-frame sample ordinals invalid")
        require(list(map(exact, sample_pts)) == [pts[v] for v in ordinals], "Sample PTS do not match accepted original native clock")
        lo, hi = interval(entry["window_exact"])
        native_end = exact(entry["window_native_end_exact"])
        end_ordinal = entry["window_native_end_ordinal"]
        require(0 <= lo < hi <= exact(source_clocks[source]["physical_end_exact"]) and
                all(lo <= pts[v] < hi for v in ordinals), "Actual sample escaped its exact window")
        require(type(end_ordinal) is int and ordinals[-1] < end_ordinal <= len(pts) and
                lo < native_end <= hi and bisect_left(pts, native_end) == end_ordinal,
                "Sample endpoint 64 lacks its actual exclusive native window witness")
        candidates = entry["candidate_events"]
        require(isinstance(candidates, list) and candidates, "A real new model case must have surviving original candidates")
        local_ids = [event["event_id"] for event in candidates]
        require(len(local_ids) == len(set(local_ids)), "Duplicate candidate inside a window")
        for event in candidates:
            event_id, original = bound_event(event, source, expected_events)
            require(original["decision"] in ("KEEP", "UNKNOWN") and not original.get("old_structural_no64", False),
                    "Old DROP/structural NO64 cannot masquerade as a new model candidate")
            seen_events.add(event_id)
        parsed = entry["parsed"]
        validate_parsed(parsed, len(candidates))
        for arm in QUALITY_ARMS:
            removed[arm].update(local_ids[index] for index in deletion_indices(arm, parsed, len(candidates), deletion_policy_map))
        for arm in RISK_ARMS:
            answer = parsed[arm.lower()]
            if not answer:
                continue
            a, b = answer
            first = ordinals[a]
            last = ordinals[b] if b < 64 else end_ordinal
            require(first < last, "Recall interval contains no actual native frame")
            additions[arm].update((source, ordinal) for ordinal in range(first, last))
            witnesses[arm].append(dict(case_id=case_id, source_id=source, sample_interval=answer,
                                       native_interval=[first, last], exact_interval=[str(pts[first]),
                                       str(pts[ordinals[b]]) if b < 64 else str(native_end)]))
    skip_keys, skip_events, skip_audit = set(), set(), []
    require(isinstance(structural_skips, (list, tuple)), "Structural skips must be an explicit list")
    for skip in structural_skips:
        case_id, source, reason = skip["case_id"], skip["source_id"], skip["reason"]
        require(isinstance(case_id, str) and case_id and source in points and reason in (SKIP_DROP, SKIP_NO64),
                "Unapproved structural skip")
        require((case_id, reason) not in skip_keys and "parsed" not in skip and "decision_ref" not in skip,
                "Structural skip duplicates or fabricates a new model answer")
        skip_keys.add((case_id, reason))
        require(reason != SKIP_NO64 or case_id not in seen_cases, "Original NO64 skip cannot also be a new model call")
        candidates = skip["candidate_events"]
        require(isinstance(candidates, list) and candidates, "Structural skip must identify its actual original candidates")
        event_ids = []
        for event in candidates:
            event_id, original = bound_event(event, source, expected_events)
            require(event_id not in seen_events and event_id not in skip_events, "An original event is both modeled and structurally skipped")
            require(original.get("original_case_id") == case_id, "Structural skip belongs to another original case")
            if reason == SKIP_DROP:
                require(original["decision"] == "DROP" and original["selected_interval_exact"] is None,
                        "DROP skip must have no protected baseline contribution")
            else:
                require(original["decision"] == "UNKNOWN" and original["selected_interval_exact"] is not None and
                        original.get("old_structural_no64") is True,
                        "NO64 skip must be the predeclared old structural UNKNOWN, preserving its original contribution")
            skip_events.add(event_id); event_ids.append(event_id)
        skip_audit.append(dict(case_id=case_id, source_id=source, reason=reason, event_ids=event_ids,
                               old_decision_ref=skip["old_decision_ref"], new_model_calls=0, fabricated_parsed=False))
    seen_events.update(skip_events)
    require(seen_events == set(expected_events), "Production candidate coverage is incomplete")
    baseline_by_source = {source: {key for key in baseline_keys if key[0] == source} for source in points}
    outputs = {}
    for arm in ARMS:
        selected = (union_events(expected_events, points, removed[arm]) if arm in QUALITY_ARMS
                    else baseline_keys | additions[arm])
        guarded = []
        selected_sources = {source for source, _ in selected}
        for source in points:
            if source not in selected_sources:
                require(baseline_by_source[source], "Protected ZIP already has an empty source")
                selected.update(baseline_by_source[source])
                guarded.append(source)
        outputs[arm] = dict(selected_keys=selected, empty_source_format_guard=guarded,
                            structural_skips=skip_audit,
                            removed_event_ids=sorted(removed[arm]) if arm in QUALITY_ARMS else [],
                            added_interval_witnesses=witnesses[arm] if arm in RISK_ARMS else [],
                            added_frames=len(selected - baseline_keys), removed_frames=len(baseline_keys - selected))
        if arm in QUALITY_ARMS:
            outputs[arm].update(actual_model_parsed_unchanged=True,
                                deterministic_deletion_policy=deterministic_policy_for(arm, deletion_policy_map))
    return outputs
