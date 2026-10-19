"""Small whole-source utility-difference critic; Qwen and TIME stay frozen.

All comparisons use the model's actual complete-source candidates. The target
is original all-rater summary utility, never a frame-level binary label. The
closed-form ridge objective has no epochs, checkpoint search or tuned cutoff.
"""
from __future__ import annotations

import math

from .contracts import require, stable_key
from .selection import CONTENT_DIM, FEATURE_DIM, finite_vector, unique_candidates

FEATURE_KINDS = ("content", "shape", "permuted")


def full_utility(selected, human):
    n = len(human["clock"]["normalized_exact_pts"])
    raters, masks = human["raters"], human["known_masks"]
    require(isinstance(raters, list) and raters and len(masks) == len(raters)
            and all(len(mask) == n and all(type(v) is bool and v for v in mask) for mask in masks),
            "Complete all-rater source membership required; UNKNOWN is not zero")
    chosen = set(selected)
    require(all(type(v) is int and 0 <= v < n for v in chosen)
            and all(all(type(v) is int and 0 <= v < n for v in truth) for truth in raters),
            "Summary/native domain mismatch")
    return sum((2 * len(chosen & truth) / (len(chosen) + len(truth))
                if chosen or truth else 1.0) for truth in raters) / len(raters)


def vector(candidate, kind):
    require(kind in FEATURE_KINDS, "Unknown feature ablation")
    values = candidate["permuted_feature"] if kind == "permuted" else candidate["feature"]
    finite_vector(values, FEATURE_DIM)
    return values[-3:] if kind == "shape" else values


def fit_pairwise(sources, supervision, *, kind="content", ridge=0.01):
    import numpy as np
    require(ridge == 0.01 and kind in FEATURE_KINDS and sources
            and set(sources) == set(supervision), "Fixed ridge and exact source split required")
    names = sorted(sources)
    require(len({sources[s]["source_sha256"] for s in names}) == len(names),
            "Source byte duplicates may not cross a fit or leave-one-source-out split")
    size = 3 if kind == "shape" else FEATURE_DIM
    candidates = {sid: unique_candidates(sources[sid]) for sid in names}
    for sid in names:
        require(supervision[sid]["source_sha256"] == sources[sid]["source_sha256"],
                "Source utility and candidate media identities differ")
    # Scaling is learned only inside THIS fit call, hence only from the24
    # included sources in a LOSO fold. The mean cancels from pair differences.
    scale_rows = np.asarray([vector(c, kind) for sid in names for c in candidates[sid]], dtype=np.float64)
    scale = scale_rows.std(axis=0)
    scale = np.where(scale > 1e-8, scale, 1.0)
    gram, rhs = np.eye(size, dtype=np.float64) * ridge, np.zeros(size, dtype=np.float64)
    pair_count, useful_sources = 0, []
    for sid in names:
        group = candidates[sid]
        targets = [full_utility(c["selected_ordinals"], supervision[sid]) for c in group]
        pairs = [(i, j) for i in range(len(group)) for j in range(i + 1, len(group))]
        if not pairs:
            continue
        useful_sources.append(sid)
        weight = 1.0 / (len(names) * len(pairs))
        for i, j in pairs:
            diff = (np.asarray(vector(group[i], kind)) - np.asarray(vector(group[j], kind))) / scale
            gram += weight * np.outer(diff, diff)
            rhs += weight * diff * (targets[i] - targets[j])
            pair_count += 1
    require(useful_sources, "No distinct complete-source actions; do not expand the pool or substitute sources")
    fitted = np.linalg.solve(gram, rhs)
    # Fold the training scale into a single inference weight vector. A shared
    # intercept is unnecessary: it cancels for all candidates of a source.
    weights = (fitted / scale).tolist()
    finite_vector(weights, size)
    residual = float(np.linalg.norm(gram @ fitted - rhs))
    require(math.isfinite(residual) and residual <= 1e-8 * (1 + float(np.linalg.norm(rhs))),
            "Actual closed-form ridge solve failed its equation residual")
    return dict(schema="AIC_SOURCE_UTILITY_CRITIC_V1", feature_kind=kind,
        weights=weights, parameters=size, fit_sources=names,
        fit_source_sha256={sid: sources[sid]["source_sha256"] for sid in names},
        fit_source_identity_sha256=stable_key([(sid, sources[sid]["source_sha256"]) for sid in names]),
        training_pairs=pair_count, informative_sources=useful_sources,
        ridge=ridge, linear_solve_residual=residual, solves=1, optimizer_updates=0,
        backbone_updates=0, training_target="FULL_SOURCE_ALL_ORIGINAL_REVIEWERS_MEAN_F1_DIFFERENCES",
        omitted_summary_is_not_exhaustive_no_highlight=True,
        scale_fit_source_ids=names, scaling_folded_into_inference_weights=True,
        checkpoint="ONE_CLOSED_FORM_FIT_NO_CHECKPOINT_SELECTION")


def score_source(head, source):
    kind = head["feature_kind"]
    require(head.get("schema") == "AIC_SOURCE_UTILITY_CRITIC_V1"
            and head.get("scaling_folded_into_inference_weights") is True
            and head.get("parameters") == (3 if kind == "shape" else FEATURE_DIM),
            "Complete fixed critic contract required")
    weights = finite_vector(head["weights"], head["parameters"])
    return [sum(a * b for a, b in zip(weights, vector(candidate, kind)))
            for candidate in source["candidates"]]


def fit_with_loso(sources, supervision):
    """Three predeclared feature ablations, each with source-exclusive fits."""
    require(len(sources) >= 3 and set(sources) == set(supervision), "At least three complete fit sources")
    final, oof, folds = {}, {kind: {} for kind in FEATURE_KINDS}, []
    for kind in FEATURE_KINDS:
        final[kind] = fit_pairwise(sources, supervision, kind=kind)
        for held in sorted(sources):
            train = {sid: value for sid, value in sources.items() if sid != held}
            human = {sid: value for sid, value in supervision.items() if sid != held}
            model = fit_pairwise(train, human, kind=kind)
            require(held not in model["fit_sources"] and sources[held]["source_sha256"]
                    not in model["fit_source_sha256"].values(), "LOSO source leakage")
            oof[kind][held] = score_source(model, sources[held])
            folds.append(dict(feature_kind=kind, held_source=held,
                fit_sources=model["fit_sources"], fit_source_sha256=model["fit_source_sha256"],
                scale_fit_source_ids=model["scale_fit_source_ids"],
                linear_solve_residual=model["linear_solve_residual"],
                weight_sha256=stable_key(model["weights"])))
    return dict(schema="AIC_CONTENT_CHOICE_CRITIC_FIT_V1", heads=final,
        out_of_fold_scores=oof, folds=folds,
        actual_linear_solves=3 * (len(sources) + 1), learned_deployed_parameters=FEATURE_DIM,
        diagnostics_are_not_deployed_models=True, final_only=True,
        validation="LEAVE_ONE_COMPLETE_SOURCE_OUT; original references historically exposed")
