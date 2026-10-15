"""Deterministic five ablations; consumes independently accepted decisions.

No inference, source decoding, reference labels or production admission occurs
here. The caller must bind real input/answer/replay receipts before packaging.
"""
from bisect import bisect_left
from fractions import Fraction as F

ARMS = ("START", "END", "BOTH", "VERIFY", "VERIFY_BOTH", "SOURCE_START", "SOURCE_END", "SOURCE_BOTH")


def exact(value):
    if isinstance(value, float) or isinstance(value, bool):
        raise ValueError("Exact accepted source seconds are required")
    return F(value)


def candidate(event, endpoints, verification, arm):
    if arm not in ARMS:
        raise ValueError("Unregistered ablation")
    source_context_mode = arm.startswith("SOURCE_")
    effective_arm = arm.removeprefix("SOURCE_")
    event_id = event["event_id"]
    old = tuple(map(exact, event["original_interval_exact"]))
    lo, hi = map(exact, event["original_window_exact"])
    physical = exact(event["physical_end_exact"])
    if not 0 <= lo <= old[0] < old[1] <= hi <= physical:
        raise ValueError("Original event/window/source domain mismatch")
    side_values = {}
    changed_sides = {}
    for side, original in zip(("start", "end"), old):
        result = endpoints[event_id + "." + side]
        if (result["event_id"] != event_id or result["side"] != side or
                exact(result["original_endpoint_exact"]) != original):
            raise ValueError("Endpoint belongs to another original candidate")
        applied = result["applied_decision"]
        value = exact(result["endpoint_exact"])
        if applied == "REFINE":
            if not 0 <= value <= physical:
                raise ValueError("Accepted refinement escaped native source")
        elif applied == "KEEP" or applied.startswith("UNKNOWN"):
            if value != original:
                raise ValueError("KEEP/UNKNOWN must preserve the original cut")
        else:
            raise ValueError("Unaccepted endpoint/failure cannot become fallback")
        side_values[side] = value
        changed_sides[side] = applied == "REFINE" and value != original
    verify = verification[event_id]
    if verify["event_id"] != event_id or verify["decision"] not in ("KEEP", "UNKNOWN", "DROP"):
        raise ValueError("Missing/invalid verification is an engineering failure")
    a = side_values["start"] if effective_arm in ("START", "BOTH", "VERIFY_BOTH") else old[0]
    b = side_values["end"] if effective_arm in ("END", "BOTH", "VERIFY_BOTH") else old[1]
    conflict = a >= b
    if conflict:
        a, b = old
    drop = arm in ("VERIFY", "VERIFY_BOTH") and verify["decision"] == "DROP"
    # Length eligibility always belongs to the ORIGINAL coarse candidate.
    # Refinement must never turn another padding condition on/off.
    lead = F(3, 4)
    tail = F(1, 2) + (F(1, 4) if old[1] - old[0] >= 8 else 0)
    source_start_applied = source_context_mode and not conflict and effective_arm in ("START", "BOTH") and changed_sides["start"]
    source_end_applied = source_context_mode and not conflict and effective_arm in ("END", "BOTH") and changed_sides["end"]
    padded = (max(F(0) if source_start_applied else lo, a - lead),
              min(physical if source_end_applied else hi, b + tail))
    if not drop and padded[0] >= padded[1]:
        raise ValueError("Refined event has no support in its original window")
    return dict(event_id=event_id, source_id=event["source_id"], arm=arm,
                original_interval_exact=list(map(str, old)),
                refined_interval_exact=[str(a), str(b)],
                selected_interval_exact=None if drop else list(map(str, padded)),
                original_length_padding_eligible=old[1] - old[0] >= 8,
                pair_conflict_preserved_original=conflict,
                verification_decision=verify["decision"], event_removed=drop,
                source_context_bounds_applied={"start":source_start_applied,"end":source_end_applied},
                source_context_padding_is_not_full_local_observation_support=source_context_mode)


def combine(events, endpoints, verification, source_clocks):
    ids = [e["event_id"] for e in events]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate original events")
    expected = {event_id + "." + side for event_id in ids for side in ("start", "end")}
    if set(endpoints) != expected or set(verification) != set(ids):
        raise ValueError("Complete exact original event/answer denominator required")
    clocks = {}
    for source_id, clock in source_clocks.items():
        pts = list(map(exact, clock["normalized_exact_pts"]))
        physical = exact(clock["physical_end_exact"])
        if not pts or pts[0] != 0 or any(a >= b for a, b in zip(pts, pts[1:])) or pts[-1] >= physical:
            raise ValueError("Accepted complete native clock required")
        clocks[source_id] = pts
    outputs = {}
    for arm in ARMS:
        selected = {source_id: set() for source_id in clocks}
        decisions = []
        for event in events:
            source_id = event["source_id"]
            if (source_id not in clocks or exact(event["physical_end_exact"]) !=
                    exact(source_clocks[source_id]["physical_end_exact"])):
                raise ValueError("Event/clock source identity mismatch")
            result = candidate(event, endpoints, verification, arm)
            decisions.append(result)
            interval = result["selected_interval_exact"]
            if interval is None:
                continue
            a, b = map(exact, interval)
            pts = clocks[source_id]
            # Union of retained candidates: removing one candidate must not
            # remove a frame still supported by a different retained event.
            selected[source_id].update(range(bisect_left(pts, a), bisect_left(pts, b)))
        outputs[arm] = dict(decisions=decisions,
                            selected_ordinals={k: sorted(v) for k, v in selected.items()},
                            scientific_quality_claim=False, model_calls_in_this_module=0)
    return outputs
