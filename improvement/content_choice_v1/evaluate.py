"""Independent complete-source/rater evaluation, candidate regret and gates.

None of these temporal summary metrics is the official space-time score. The
old DPO STOP is an immutable separate experiment, never reclassified here.
"""
from __future__ import annotations

import math
import random

from improvement.native_preference_v1.run import mean_metrics
from .contracts import require
from .critic import full_utility
from .selection import choose, fixed_scores, unique_candidates


def bootstrap_mean_interval(values, *, draws=4096):
    require(values and all(math.isfinite(float(v)) for v in values), "Finite source differences required")
    rng = random.Random(20261019)
    samples = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(draws))
    return dict(low=samples[int(.025 * draws)], high=samples[min(draws - 1, int(.975 * draws))],
        draws=draws, unit="complete_source", seed=20261019,
        confidence=.95, admission_test=False,
        caveat="Historically exposed small source sample; LOSO folds share training data")


def pair_accuracy(source, scores, human):
    candidates = unique_candidates(source)
    values, ignored = [], 0
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            delta = full_utility(a["selected_ordinals"], human) - full_utility(b["selected_ordinals"], human)
            if delta == 0:
                ignored += 1
                continue
            gap = scores[a["slot"]] - scores[b["slot"]]
            values.append(0.5 if gap == 0 else float(gap * delta > 0))
    return dict(accuracy=sum(values) / len(values) if values else None,
                non_tied_pairs=len(values), utility_ties_ignored=ignored)


def compare_selections(supervision, greedy, policies, *, rankings=None):
    """Every role covers every source; a legal empty set is still a record."""
    names = sorted(supervision)
    require(names and set(greedy) == set(names) and policies
            and all(set(rows) == set(names) for rows in policies.values()),
            "Missing source is not an empty prediction")
    all_roles = dict(greedy=greedy, protected_proxy={sid: supervision[sid]["baseline"] for sid in names},
                     **policies)
    per_source, macro = [], {}
    for sid in names:
        human = supervision[sid]
        for role in all_roles.values():
            full_utility(role[sid], human)  # Includes full-domain and known-mask validation.
        row = dict(source_id=sid, source_sha256=human["source_sha256"],
            original_reviewer_count=len(human["raters"]),
            nonempty_original_reviewers=sum(bool(rater) for rater in human["raters"]),
            metrics={name: mean_metrics(set(role[sid]), human["raters"]) for name, role in all_roles.items()},
            frames={name: len(set(role[sid])) for name, role in all_roles.items()},
            differences={})
        for name, role in policies.items():
            original, current = set(greedy[sid]), set(role[sid])
            added, removed = current - original, original - current
            row["differences"][name] = dict(added=len(added), removed=len(removed),
                changed=len(current ^ original), f1_delta_vs_greedy=
                    row["metrics"][name]["f1"] - row["metrics"]["greedy"]["f1"],
                f1_delta_vs_protected=row["metrics"][name]["f1"] - row["metrics"]["protected_proxy"]["f1"],
                false_empty=not current and bool(original) and any(human["raters"]),
                added_summary_membership=(sum(len(added & truth) / len(added) for truth in human["raters"])
                                           / len(human["raters"]) if added else None),
                removed_summary_membership=(sum(len(removed & truth) / len(removed) for truth in human["raters"])
                                             / len(human["raters"]) if removed else None))
        per_source.append(row)
    for role in all_roles:
        macro[role] = {metric: sum(row["metrics"][role][metric] for row in per_source) / len(names)
                       for metric in ("f1", "precision", "recall")}
    effects = {}
    for role in policies:
        values = [row["differences"][role] for row in per_source]
        deltas = [row["f1_delta_vs_greedy"] for row in values]
        effects[role] = dict(added=sum(row["added"] for row in values),
            removed=sum(row["removed"] for row in values), changed=sum(row["changed"] for row in values),
            source_wins=sum(delta > 0 for delta in deltas), source_losses=sum(delta < 0 for delta in deltas),
            source_ties=sum(delta == 0 for delta in deltas),
            false_empty_sources=[row["source_id"] for row in per_source if row["differences"][role]["false_empty"]],
            source_delta_interval=bootstrap_mean_interval(deltas))
    return dict(macro=macro, per_source=per_source, effects=effects,
        rankings=rankings or {}, historical_exposure=True, official_score="NOT_MEASURED",
        all_raters_empty_source_ids=[row["source_id"] for row in per_source
                                    if row["nonempty_original_reviewers"] == 0],
        spatial_joint_utility="UNKNOWN_NO_BOUND_VIDEO_SPATIAL_REFERENCE",
        target="Complete source, mean over ALL original reviewers, then source macro",
        omission_is_not_no_highlight_truth=True)


def evaluate_pool(sources, supervision, score_maps):
    require(set(sources) == set(supervision) and score_maps
            and all(set(rows) == set(sources) for rows in score_maps.values()),
            "Exact complete source/score/reference denominator required")
    require(len({s["source_sha256"] for s in sources.values()}) == len(sources),
            "Duplicated media cannot count as independent evaluation sources")
    for sid, source in sources.items():
        require(source["source_sha256"] == supervision[sid]["source_sha256"]
                and source["native_count"] == len(supervision[sid]["clock"]["normalized_exact_pts"]),
                "Candidate and reference source SHA/native clock domain differ")
    greedy = {sid: set(source["candidates"][0]["selected_ordinals"]) for sid, source in sources.items()}
    selections, decisions, rankings = {}, {}, {}
    for name, scores_by_source in score_maps.items():
        decisions[name] = {sid: choose(source, scores_by_source[sid]) for sid, source in sources.items()}
        selections[name] = {sid: set(row["selected_ordinals"]) for sid, row in decisions[name].items()}
        rows = {sid: pair_accuracy(source, scores_by_source[sid], supervision[sid]) for sid, source in sources.items()}
        defined = [row["accuracy"] for row in rows.values() if row["accuracy"] is not None]
        rankings[name] = dict(source_macro=sum(defined) / len(defined) if defined else None,
            source_coverage=len(defined), total_sources=len(rows), per_source=rows)
    result = compare_selections(supervision, greedy, selections, rankings=rankings)
    bounds, regrets = [], {name: [] for name in score_maps}
    for sid, source in sources.items():
        candidates = unique_candidates(source)
        utilities = {c["slot"]: full_utility(c["selected_ordinals"], supervision[sid]) for c in candidates}
        all_utility = [full_utility(c["selected_ordinals"], supervision[sid]) for c in source["candidates"]]
        oracle = max(utilities.values())
        bounds.append(dict(source_id=sid, unique_native_candidates=len(candidates),
            candidate_frames=[len(c["selected_ordinals"]) for c in source["candidates"]],
            utility=all_utility, oracle=oracle, oracle_gain_vs_greedy=oracle - all_utility[0],
            union_coverage_frames=len(set().union(*(set(c["selected_ordinals"]) for c in candidates)))))
        for name in score_maps:
            regrets[name].append(oracle - all_utility[decisions[name][sid]["slot"]])
    result.update(candidate_pool=bounds,
        oracle_macro=sum(row["oracle"] for row in bounds) / len(bounds),
        mean_regret={name: sum(values) / len(values) for name, values in regrets.items()},
        oracle_is_reference_assisted_bound_not_a_predictor=True,
        decisions={name: {sid: {k: v for k, v in row.items() if k != "selected_ordinals"}
                          for sid, row in rows.items()} for name, rows in decisions.items()})
    return result, selections


def _improves(report, role, other):
    return report["macro"][role]["f1"] > report["macro"][other]["f1"]


def _rank_improves(report, role, other):
    a, b = report["rankings"][role], report["rankings"][other]
    return (a["source_coverage"] == b["source_coverage"] == a["total_sources"]
            and a["source_macro"] is not None and b["source_macro"] is not None
            and a["source_macro"] > b["source_macro"])


def admission_reasons(candidate, cross, *, oof=None, observation_evidence=None):
    require(candidate in ("observation", "contrast", "critic"), "Unknown mechanism gate")
    stops = []
    role = candidate
    if not cross["effects"][role]["changed"]:
        stops.append("NO_CHANGE_IN_ACTUAL_COMPLETE_SOURCE_SELECTION")
    if not _improves(cross, role, "greedy"):
        stops.append("CROSS_SOURCE_F1_DID_NOT_BEAT_ORIGINAL_TIME")
    if not _improves(cross, role, "protected_proxy"):
        stops.append("CROSS_SOURCE_F1_DID_NOT_BEAT_PROTECTED_EXTERNAL_PROXY")
    if cross["effects"][role]["false_empty_sources"]:
        stops.append("NEW_FALSE_EMPTY_COMPLETE_SOURCE")
    if candidate == "observation":
        require(observation_evidence is not None, "Observation identity diagnostics required")
        if observation_evidence.get("changed_input_windows", 0) == 0:
            stops.append("NO_NEW_ACTUAL_VISUAL_OBSERVATION")
    elif candidate == "contrast":
        if not _improves(cross, role, "raw"):
            stops.append("CONDITIONAL_SCORE_DID_NOT_BEAT_SAME_POOL_RAW_MEAN_LOGP")
        if not _rank_improves(cross, role, "raw"):
            stops.append("CONDITIONAL_SCORE_DID_NOT_IMPROVE_FULL_SOURCE_UTILITY_ORDERING")
    else:
        require(oof is not None, "Source-exclusive LOSO evidence required for trained critic")
        if not _improves(oof, role, "greedy"):
            stops.append("LOSO_F1_DID_NOT_BEAT_ORIGINAL_TIME")
        for comparator in ("shape", "permuted"):
            if not _improves(cross, role, comparator):
                stops.append("CROSS_F1_DID_NOT_BEAT_" + comparator.upper() + "_CONTROL")
            if not _rank_improves(cross, role, comparator):
                stops.append("CROSS_UTILITY_ORDERING_DID_NOT_BEAT_" + comparator.upper() + "_CONTROL")
        if not _rank_improves(oof, role, "shape"):
            stops.append("LOSO_UTILITY_ORDERING_DID_NOT_BEAT_SHAPE_ONLY_CONTROL")
    return stops
