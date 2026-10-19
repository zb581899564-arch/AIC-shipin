"""Whole-source candidate composition and identity-checked decision features.

Four candidate slots are composed BEFORE any reference utility is read.  A
source decision chooses one complete slot. It cannot silently choose the best
slot independently in each window or add together window F1 improvements.
"""
from __future__ import annotations

from fractions import Fraction
import math

from .contracts import require, stable_key

FEATURE_DIM = 131
CONTENT_DIM = 128
SHAPE_NAMES = ("native_selection_fraction", "runs_per_max_source_runs", "suffix_budget_fraction")


def runs(selected):
    ordered = sorted(selected)
    return sum(index == 0 or value != ordered[index - 1] + 1
               for index, value in enumerate(ordered))


def finite_vector(value, dimension):
    require(isinstance(value, list) and len(value) == dimension
            and all(type(v) in (int, float) and math.isfinite(v) for v in value),
            "Finite feature vector of exact dimension required")
    return value


def validate_source_candidates(source):
    require(source.get("status") == "ACCEPTED" and source.get("source_id")
            and type(source.get("native_count")) is int and source["native_count"] > 0,
            "Complete accepted source candidate record required")
    candidates = source["candidates"]
    require(isinstance(candidates, list) and [x["slot"] for x in candidates] == list(range(4)),
            "Exactly greedy/sample1/sample2/explicit-empty complete source slots required")
    for candidate in candidates:
        selected = candidate["selected_ordinals"]
        require(isinstance(selected, list) and selected == sorted(set(selected))
                and all(type(i) is int and 0 <= i < source["native_count"] for i in selected),
                "Candidate selections must be unique actual native ordinals")
        finite_vector(candidate["feature"], FEATURE_DIM)
        if candidate.get("permuted_feature") is not None:
            finite_vector(candidate["permuted_feature"], FEATURE_DIM)
        require(type(candidate["suffix_tokens"]) is int and candidate["suffix_tokens"] > 0,
                "Actual complete suffix token denominator required")
        for key in ("mean_logprob", "logprob_sum"):
            require(type(candidate[key]) in (int, float) and math.isfinite(candidate[key]),
                    "Finite actual candidate score required")
        require(candidate.get("contrast") is None or
                (type(candidate["contrast"]) in (int, float) and math.isfinite(candidate["contrast"])),
                "Finite conditional score or explicitly absent diagnostic required")
    require(candidates[3]["selected_ordinals"] == [], "Slot3 must be the explicit full-source empty action")
    return source


def aggregate_source(source_id, source_sha256, clock, requests, windows):
    """Source-native union plus duration-weighted candidate-conditioned features."""
    require(requests and set(requests) == set(windows), "All source windows, including empty ones, required")
    points = list(map(Fraction, clock["normalized_exact_pts"]))
    n = len(points)
    end = Fraction(clock["physical_end_exact"])
    require(points and points[0] == 0 and points == sorted(set(points)) and points[-1] < end,
            "Complete increasing normalized native clock required")
    order = sorted(requests, key=lambda uid: Fraction(requests[uid]["plan"]["window_start_exact"]))
    previous = Fraction(0)
    weights, limits = {}, {}
    for uid in order:
        request, row = requests[uid], windows[uid]
        left, right = (Fraction(request["plan"][key]) for key in
                       ("window_start_exact", "window_end_exact"))
        require(left == previous < right <= end and request["sid"] == source_id
                and request["source_sha256"] == source_sha256 and row.get("status") == "ACCEPTED"
                and row["uid"] == uid and row["source_id"] == source_id
                and [c["slot"] for c in row["slots"]] == list(range(4)),
                "Missing/failed/foreign/noncontiguous window cannot become empty")
        previous = right
        weights[uid] = float((right - left) / end)
        limits[uid] = (left, right)
    require(previous == end, "Candidate source must cover the measured physical endpoint")
    result = []
    for slot in range(4):
        selected, tokens, logprob, shifted_logprob = set(), 0, 0.0, 0.0
        vector, shifted_vector, has_shift = [0.0] * CONTENT_DIM, [0.0] * CONTENT_DIM, True
        for uid in order:
            case = windows[uid]["slots"][slot]
            require(case["status"] == "ACCEPTED", "A failed candidate is not a legal empty action")
            chosen = case["selected_ordinals"]
            require(chosen == sorted(set(chosen)) and all(type(i) is int and 0 <= i < n for i in chosen),
                    "Window native selection is invalid")
            require(all(limits[uid][0] <= points[i] < limits[uid][1] for i in chosen),
                    "Window selection includes a native PTS outside its own interval")
            selected.update(chosen)
            real, shift = case["real"], case.get("permuted")
            finite_vector(real["feature"], CONTENT_DIM)
            require(type(real["suffix_tokens"]) is int and real["suffix_tokens"] == len(case["ids"]),
                    "Feature score does not cover this exact complete answer/EOS")
            tokens += real["suffix_tokens"]
            logprob += real["logprob"]
            for i, value in enumerate(real["feature"]):
                vector[i] += weights[uid] * value
            if shift is None:
                has_shift = False
            else:
                finite_vector(shift["feature"], CONTENT_DIM)
                require(shift["suffix_tokens"] == real["suffix_tokens"], "Counterfactual answer tokens changed")
                shifted_logprob += shift["logprob"]
                for i, value in enumerate(shift["feature"]):
                    shifted_vector[i] += weights[uid] * value
        shape = [len(selected) / n, runs(selected) / (6 * len(order)), tokens / (512 * len(order))]
        result.append(dict(slot=slot, selected_ordinals=sorted(selected),
            native_selection_sha256=stable_key(source_sha256, sorted(selected)),
            feature=vector + shape, permuted_feature=shifted_vector + shape if has_shift else None,
            suffix_tokens=tokens, logprob_sum=logprob, mean_logprob=logprob / tokens,
            permuted_logprob_sum=shifted_logprob if has_shift else None,
            contrast=(logprob - shifted_logprob) / tokens if has_shift else None,
            legal_empty=not selected))
    document = dict(status="ACCEPTED", source_id=source_id, source_sha256=source_sha256,
        native_count=n, window_ids=order, window_weights=weights, candidates=result,
        rule="ONE_SAME_SLOT_COMPLETE_SOURCE; no window utility or reference labels used",
        labels_read=False, learned_projection=False)
    return validate_source_candidates(document)


def unique_candidates(source):
    """Deduplicate native actions for fitting/diagnostics, preserving the first slot."""
    validate_source_candidates(source)
    seen, result = set(), []
    for candidate in source["candidates"]:
        key = tuple(candidate["selected_ordinals"])
        if key not in seen:
            seen.add(key)
            result.append(candidate)
    return result


def choose(source, scores):
    validate_source_candidates(source)
    finite_vector(list(scores), 4)
    # Exact ties select the earlier slot; slot0 is the retained greedy control.
    index = max(range(4), key=lambda i: (scores[i], -i))
    return dict(slot=index, score=float(scores[index]),
                selected_ordinals=source["candidates"][index]["selected_ordinals"])


def fixed_scores(source, kind):
    require(kind in ("greedy", "raw", "contrast"), "Unknown untrained comparator")
    if kind == "greedy":
        return [1.0, 0.0, 0.0, 0.0]
    key = "mean_logprob" if kind == "raw" else "contrast"
    result = [candidate[key] for candidate in source["candidates"]]
    return finite_vector(result, 4)
