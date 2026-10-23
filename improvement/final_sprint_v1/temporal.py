"""Action-phase event assembly and preregistered whole-source selection.

There is no fitted head, threshold search, source-specific switch, or access
to a reference label here.  R_EVENT and R_APEX reuse exactly the same genuine
phase observations; they are a structural ablation, not independent evidence.
"""
from __future__ import annotations

from fractions import Fraction
import math

from .observation import exact_clock, plan_clips
from .qwen_runtime import PHASES, TRANSITIONS


def _require(value, message):
    if not value:
        raise ValueError(message)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _event(rows, clip_id, ordinal):
    peaks = [row for row in rows if row["phase"] == "apex"]
    if not peaks:
        return None
    duration = sum((Fraction(row["cell"]["end_exact"]) - Fraction(row["cell"]["start_exact"])
                    for row in rows), Fraction(0))
    weighted = sum(float(Fraction(row["cell"]["end_exact"]) - Fraction(row["cell"]["start_exact"]))
                   * row["selected_minus_ordinary"] for row in rows)
    return dict(event_id=f"{clip_id}:event_{ordinal:03d}", clip_id=clip_id,
                cells=[row["cell"] for row in rows], phases=[row["phase"] for row in rows],
                apex_cells=[row["cell"] for row in peaks],
                evidence_mean_margin=weighted / float(duration),
                first=rows[0]["cell"]["first"], stop=rows[-1]["cell"]["stop"],
                start_exact=rows[0]["cell"]["start_exact"], end_exact=rows[-1]["cell"]["end_exact"],
                has_setup=any(row["phase"] == "setup" for row in rows),
                has_resolution=any(row["phase"] == "resolution" for row in rows),
                completeness="OBSERVED_PHASE_ARC_NOT_A_GUARANTEE_OF_COMPLETE_REAL_WORLD_EVENT")


def assemble_events(source, clip_results, *, clip_seconds=8, samples_per_clip=32):
    """Require complete physical clip coverage and legal action-phase paths."""
    plans = plan_clips(source, clip_seconds=clip_seconds, samples_per_clip=samples_per_clip)
    _require(len(clip_results) == len(plans), "Every physical source clip must complete successfully")
    events, rejected = [], []
    for plan, result in zip(plans, clip_results):
        _require(result["clip"] == plan and result["status"] in ("MODEL_OK", "LEGAL_EMPTY"),
                 "Missing, failed, reordered or foreign local clip")
        _require(result["no_global_source_prefix"] is True and result["training_updates"] == 0,
                 "Physical local-input inference contract changed")
        _require(result["input_proof"]["physical_source_sha256"] == source["media"]["sha256"],
                 "Actual local input belongs to another physical source")
        rows = result["phases"]
        _require(len(rows) == len(plan["cells"]), "One actual phase per native temporal group required")
        previous, current, arc = "ordinary", [], 0
        for group, (row, cell) in enumerate(zip(rows, plan["cells"])):
            _require(row["group"] == group and row["cell"] == cell and row["phase"] in PHASES,
                     "Native action-phase output is not aligned to actual cells")
            _require(row["phase"] in TRANSITIONS[previous], "Invalid/cyclic event phase transition")
            _require(_finite(row["selected_minus_ordinary"]), "Nonfinite semantic phase margin")
            alternatives = row["alternatives"]
            _require([value["phase"] for value in alternatives] == list(PHASES),
                     "Full semantic alternatives were not recorded")
            _require(all(_finite(value["mean_log_probability"]) and _finite(value["log_probability_sum"])
                         and value["token_ids"] and len(value["token_ids"]) == len(value["token_log_probabilities"])
                         for value in alternatives), "Incomplete semantic full-vocabulary likelihood evidence")
            for value in alternatives:
                token_sum = sum(value["token_log_probabilities"])
                _require(all(_finite(item) for item in value["token_log_probabilities"])
                         and abs(token_sum - value["log_probability_sum"]) <= 1e-10
                         and abs(token_sum / len(value["token_ids"]) - value["mean_log_probability"]) <= 1e-10,
                         "Stored complete semantic likelihood is internally inconsistent")
            allowed = TRANSITIONS[previous]
            chosen = max((i for i, phase in enumerate(PHASES) if phase in allowed),
                         key=lambda i: (alternatives[i]["mean_log_probability"], -i))
            _require(PHASES[chosen] == row["phase"] and abs(row["selected_minus_ordinary"] - (
                alternatives[chosen]["mean_log_probability"] - alternatives[0]["mean_log_probability"])) <= 1e-10,
                "Stored semantic decision or ordinary margin differs from actual likelihoods")
            if row["phase"] == "ordinary":
                if current:
                    value = _event(current, plan["clip_id"], arc)
                    (events if value else rejected).append(value if value else dict(
                        clip_id=plan["clip_id"], reason="SETUP_WITHOUT_OBSERVED_APEX",
                        first=current[0]["cell"]["first"], stop=current[-1]["cell"]["stop"]))
                    arc += 1
                    current = []
            else:
                current.append(row)
            previous = row["phase"]
        if current:
            value = _event(current, plan["clip_id"], arc)
            (events if value else rejected).append(value if value else dict(
                clip_id=plan["clip_id"], reason="SETUP_WITHOUT_OBSERVED_APEX",
                first=current[0]["cell"]["first"], stop=current[-1]["cell"]["stop"]))
    return events, rejected


def select_event_budget(events, source_duration, *, fraction=Fraction(1, 4), segment_penalty=0.15,
                        cost_resolution_ms=1, max_frontier=50000):
    """Exact0/1 DP on conservative millisecond costs, not a threshold scan.

    Rounding each event cost up and the budget down guarantees the actual
    duration cap.  Pareto pruning is exact for these registered costs.  An
    excessive frontier raises a computational failure; it never changes the
    cap, drops arbitrary states or silently uses an approximate selection.
    """
    duration = Fraction(str(source_duration))
    fraction = Fraction(fraction)
    _require(duration > 0 and 0 < fraction <= 1 and _finite(segment_penalty)
             and segment_penalty >= 0 and type(cost_resolution_ms) is int and cost_resolution_ms > 0,
             "Invalid registered source budget")
    quantum = Fraction(cost_resolution_ms, 1000)
    budget = math.floor(duration * fraction / quantum)
    frontier = [(0, 0.0, ())]
    costs, utilities = [], []
    for index, event in enumerate(events):
        event_duration = Fraction(event["end_exact"]) - Fraction(event["start_exact"])
        _require(event_duration > 0 and _finite(event["evidence_mean_margin"]), "Invalid event arc")
        cost = math.ceil(event_duration / quantum)
        utility = event["evidence_mean_margin"] - segment_penalty
        costs.append(cost)
        utilities.append(utility)
        extended = frontier + [(spent + cost, score + utility, selected + (index,))
                               for spent, score, selected in frontier if spent + cost <= budget]
        # For equal objective/cost prefer the fewer, then lexically earlier arcs.
        extended.sort(key=lambda row: (row[0], -row[1], len(row[2]), row[2]))
        new, best = [], -math.inf
        for state in extended:
            if state[1] > best:
                new.append(state)
                best = state[1]
        _require(len(new) <= max_frontier, "Exact event-budget DP frontier exceeds fixed computational bound")
        frontier = new
    chosen = min(frontier, key=lambda row: (-row[1], row[0], len(row[2]), row[2]))
    indices = list(chosen[2])
    actual = sum((Fraction(events[index]["end_exact"]) - Fraction(events[index]["start_exact"])
                  for index in indices), Fraction(0))
    _require(actual <= duration * fraction, "Actual selected event duration exceeds preregistered cap")
    return indices, dict(budget_fraction=str(fraction), duration_budget_exact=str(duration * fraction),
                         actual_event_duration_exact=str(actual), cost_resolution_ms=cost_resolution_ms,
                         segment_penalty=segment_penalty, objective=chosen[1],
                         selected_event_ids=[events[index]["event_id"] for index in indices],
                         event_costs=costs, event_utilities=utilities,
                         fixed_risk_prior_not_validated_optimum=True, minimum_selection_enforced=False)


def select_source(source, clip_results, *, policy="event", clip_seconds=8, samples_per_clip=32,
                  fraction=Fraction(1, 4), segment_penalty=0.15):
    """Return exact native frame ordinals and policy provenance for rendering.

    Both policies select the same event identities using the full arc cost.
    `apex` then retains only the selected events' apex cells.  Thus the ablation
    changes event completion, not the count/threshold or event ranking.
    """
    _require(policy in ("event", "apex"), "Only the two preregistered structural policies are supported")
    points, end = exact_clock(source)
    events, rejected = assemble_events(source, clip_results, clip_seconds=clip_seconds,
                                       samples_per_clip=samples_per_clip)
    selected, budget = select_event_budget(events, end, fraction=fraction,
                                           segment_penalty=segment_penalty)
    cells = [cell for index in selected
             for cell in (events[index]["cells"] if policy == "event" else events[index]["apex_cells"])]
    frames = sorted({frame for cell in cells for frame in range(cell["first"], cell["stop"])})
    _require(all(0 <= value < len(points) for value in frames), "Selected native ordinal outside source")
    return dict(video_id=source["video_id"], status="MODEL_OK" if frames else "LEGAL_EMPTY",
                frames=frames, policy=policy, events=events, rejected_partial_arcs=rejected,
                selected_event_ids=budget["selected_event_ids"], budget=budget,
                actual_source_frames=len(points), no_forced_nonempty=True,
                difference="NEW_PHYSICAL_LOCAL_ACTION_PHASES_AND_EVENT_ARC_SELECTION",
                offline_quality_validated=False, shares_phase_evidence_with_other_policy=True)
