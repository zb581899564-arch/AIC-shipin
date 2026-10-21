"""External-only action/coverage ceilings, computed from accepted cached answers.

No model, media, training or official-data interface. Reference-assisted optima
are diagnostic bounds, never a selector that may be used on competition data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time
import traceback

import numpy as np


def utility(selected, labels):
    labels = np.asarray(labels)
    if labels.dtype != np.bool_ or labels.ndim != 2 or not labels.shape[1]:
        raise ValueError("Exact native-by-original-reviewer Boolean membership required")
    chosen = sorted(set(selected))
    if any(type(i) is not int or not 0 <= i < len(labels) for i in chosen):
        raise ValueError("Native ordinal outside original label domain")
    total = labels.sum(axis=0, dtype=np.int64)
    tp = labels[chosen].sum(axis=0, dtype=np.int64)
    denominator = len(chosen) + total
    return float(np.divide(2.0 * tp, denominator, out=np.ones_like(tp, dtype=float),
                           where=denominator != 0).mean())


def shared_subset_oracle(labels, allowed):
    """Exact max_P mean_r 2|P intersect G_r|/(|P|+|G_r|), P subset allowed.

    For a fixed cardinality k, a frame's additive weight is
    mean_r 1[frame in G_r]/(k+|G_r|). Choose the k highest weights.
    Equal reviewer-membership patterns are grouped; all k are examined.
    Reviewers are NEVER optimized independently or cherry-picked.
    """
    labels = np.asarray(labels)
    utility([], labels)  # Same full-domain and empty-reviewer convention.
    allowed = sorted(set(allowed))
    if any(type(i) is not int or not 0 <= i < len(labels) for i in allowed):
        raise ValueError("Allowed domain outside original native clock")
    if labels.shape[1] > 63:
        raise ValueError("This bounded implementation supports at most63 reviewers")
    base = utility([], labels)
    if not allowed:
        return dict(f1=base, selected_count=0, allowed_count=0, pattern_count=0)
    selected_labels = labels[allowed]
    powers = np.left_shift(np.uint64(1), np.arange(labels.shape[1], dtype=np.uint64))
    signatures = (selected_labels.astype(np.uint64) * powers).sum(axis=1, dtype=np.uint64)
    unique, indices, counts = np.unique(signatures, return_index=True, return_counts=True)
    patterns = selected_labels[indices].astype(np.float64)
    truth_sizes = labels.sum(axis=0, dtype=np.int64)
    best_value, best_k, best_order = base, 0, None
    for start in range(1, len(allowed) + 1, 256):
        k = np.arange(start, min(start + 256, len(allowed) + 1), dtype=np.int64)
        weights = (1.0 / (k[:, None] + truth_sizes[None, :])) @ patterns.T / labels.shape[1]
        order = np.argsort(-weights, axis=1, kind="stable")
        ordered_counts = counts[order]
        before = np.cumsum(ordered_counts, axis=1) - ordered_counts
        used = np.minimum(np.maximum(k[:, None] - before, 0), ordered_counts)
        values = 2.0 * (used * np.take_along_axis(weights, order, axis=1)).sum(axis=1)
        j = int(np.argmax(values))
        if float(values[j]) > best_value:
            best_value, best_k, best_order = float(values[j]), int(k[j]), order[j].tolist()
    if best_k:
        # A real common subset certifies the algebra; labels never leave Linux.
        chosen, remaining = [], best_k
        for group in best_order:
            members = [allowed[i] for i in np.flatnonzero(signatures == unique[group])]
            take = min(remaining, len(members))
            chosen.extend(members[:take])
            remaining -= take
            if not remaining:
                break
        if remaining or not math.isclose(utility(chosen, labels), best_value, abs_tol=1e-12):
            raise AssertionError("Oracle cardinality/reference certificate mismatch")
    return dict(f1=best_value, selected_count=best_k, allowed_count=len(allowed),
                pattern_count=len(unique), exact=True,
                common_subset_for_all_original_reviewers=True)


def window_action_oracle(windows, labels, limit=2_000_000):
    """Exact complete-source optimum over disjoint window action combinations."""
    utility([], labels)
    groups, seen = [], set()
    for candidates in windows:
        unique = sorted({tuple(sorted(set(c))) for c in candidates})
        if not unique:
            raise ValueError("Missing candidate window cannot be an empty action")
        domain = set().union(*(set(c) for c in unique))
        if seen & domain:
            raise ValueError("Window actions overlap; additive combination would double-count")
        seen.update(domain)
        for c in unique:
            utility(c, labels)
        groups.append(unique)
    if not groups:
        raise ValueError("Complete nonempty window catalog required")
    count = math.prod(len(g) for g in groups)
    if count > limit:
        raise ValueError(f"Exact enumeration {count} exceeds registered bound{limit}; do not approximate")
    sizes, tp = np.zeros(1, dtype=np.int64), np.zeros((1, labels.shape[1]), dtype=np.int64)
    for group in groups:
        sizes = (sizes[:, None] + np.asarray([len(c) for c in group])[None, :]).reshape(-1)
        new_tp = np.asarray([labels[list(c)].sum(axis=0, dtype=np.int64) for c in group])
        tp = (tp[:, None, :] + new_tp[None, :, :]).reshape(-1, labels.shape[1])
    denom = sizes[:, None] + labels.sum(axis=0, dtype=np.int64)[None, :]
    values = np.divide(2.0 * tp, denom, out=np.ones_like(tp, dtype=float), where=denom != 0).mean(axis=1)
    flat = int(np.argmax(values))
    choice = np.unravel_index(flat, tuple(len(g) for g in groups))
    chosen = set().union(*(set(g[i]) for g, i in zip(groups, choice)))
    value = float(values[flat])
    if not math.isclose(value, utility(chosen, labels), abs_tol=1e-12):
        raise AssertionError("Complete-source combination certificate mismatch")
    return dict(f1=value, selected_count=len(chosen), combinations=count,
                unique_actions_by_window=[len(g) for g in groups], exact=True)


def checked_json(ref, workspace):
    path = Path(ref["path"]).resolve(strict=True)
    if not path.is_relative_to(workspace):
        raise ValueError("Bound file escapes Linux project workspace")
    blob = path.read_bytes()
    if len(blob) != ref["bytes"] or hashlib.sha256(blob).hexdigest() != ref["sha256"]:
        raise ValueError("Bound input byte identity changed: " + str(path))
    return json.loads(blob)


def reference(path):
    blob = Path(path).read_bytes()
    return dict(path=str(Path(path).resolve()), bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())


def save_new(path, data):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)


def run(root):
    started = time.monotonic()
    root = Path(root).resolve(strict=True)
    workspace = root.parent.resolve(strict=True)
    reg = json.loads((root / "registration01.json").read_text())
    protocol = checked_json(reg["protocol_ref"], workspace)
    if protocol["new_model_calls"] != 0 or protocol["first_stage"] != "CACHED_EXTERNAL_CANDIDATE_ACTION_AND_COVERAGE_DECOMPOSITION":
        raise ValueError("Explicit external-only diagnostic registration required")
    checked_json(reg["prior_collection_ref"], workspace)
    prior = checked_json(reg["prior_review_ref"], workspace)
    collection = checked_json(prior["collect_check_ref"], workspace)
    if collection["scope"] != "check" or collection["source_count"] != 8 or collection["window_count"] != 43:
        raise ValueError("Exact8 external sources/43 accepted windows required")
    if collection["labels_read"] is not False:
        raise ValueError("Candidate collection must precede reference access")
    # Read only CPU metadata and original human membership; no tensor import.
    code_root = Path(reg["prior_code_root"]).resolve(strict=True)
    if not code_root.is_relative_to(workspace):
        raise ValueError("Prior code root outside workspace")
    sys.path.insert(0, str(code_root))
    from improvement.native_preference_v1.inputs import NativeInputStore
    manifest = checked_json(collection["asset_manifest_ref"], workspace)
    store = NativeInputStore(manifest, "check")
    rows = {}
    for uid, ref in collection["window_refs"].items():
        row = checked_json(ref, workspace)
        if row["status"] != "ACCEPTED" or row["uid"] != uid or row["labels_read"] is not False:
            raise ValueError("Missing/failed candidate is not a successful empty")
        if row["source_sha256"] != store.requests[uid]["source_sha256"]:
            raise ValueError("Cached candidate source differs from accepted external input")
        if row["input_signature"] != store.requests[uid]["input_signature"]:
            raise ValueError("Cached candidate and original accepted input signature differ")
        rows[uid] = row
    if set(rows) != set(store.case_ids) or set(collection["sources"]) != set(store.source_ids):
        raise ValueError("Full external source/window denominator mismatch")
    results = []
    for sid in sorted(store.source_ids):
        if time.monotonic() - started > protocol["cpu_seconds_budget"]:
            raise TimeoutError("Registered CPU budget expired")
        human = store.source_supervision(sid)
        n, r = len(human["clock"]["normalized_exact_pts"]), len(human["raters"])
        if not all(all(mask) and len(mask) == n for mask in human["known_masks"]):
            raise ValueError("Unknown supervision must not be treated as unselected")
        labels = np.zeros((n, r), dtype=np.bool_)
        for col, truth in enumerate(human["raters"]):
            labels[sorted(truth), col] = True
        windows = []
        for uid in collection["sources"][sid]["window_ids"]:
            row, req = rows[uid], store.requests[uid]
            if row["source_id"] != sid or [s["slot"] for s in row["slots"]] != list(range(4)):
                raise ValueError("Source/slot catalog mismatch")
            lo, hi = [Fraction(req["plan"][k]) for k in ("window_start_exact", "window_end_exact")]
            points = human["clock"]["normalized_exact_pts"]
            actions = []
            for slot in row["slots"]:
                chosen = slot["selected_ordinals"]
                if slot["status"] != "ACCEPTED" or chosen != sorted(set(chosen)):
                    raise ValueError("Invalid original action")
                if any(not 0 <= i < n or not lo <= Fraction(points[i]) < hi for i in chosen):
                    raise ValueError("Window action outside exact native PTS domain")
                actions.append(set(chosen))
            if actions[3]:
                raise ValueError("Explicit-empty slot changed")
            windows.append(actions)
        for slot in range(4):
            combined = set().union(*(actions[slot] for actions in windows))
            if combined != set(collection["sources"][sid]["candidates"][slot]["selected_ordinals"]):
                raise ValueError("Window/source action composition mismatch")
        union = set().union(*(set(c["selected_ordinals"]) for c in collection["sources"][sid]["candidates"]))
        prior_pool = next(v for v in prior["cross_source_evaluation"]["candidate_pool"] if v["source_id"] == sid)
        window_best = window_action_oracle(windows, labels, protocol["exact_window_enumeration_limit"])
        union_best = shared_subset_oracle(labels, union)
        native_best = shared_subset_oracle(labels, list(range(n)))
        old_best = float(prior_pool["oracle"])
        if not (old_best <= window_best["f1"] + 1e-12 <= union_best["f1"] + 2e-12
                <= native_best["f1"] + 3e-12):
            raise AssertionError("Nested action-space oracle inequalities failed")
        original = next(v for v in prior["cross_source_evaluation"]["per_source"] if v["source_id"] == sid)
        recalls = [len(set(truth) & union) / len(truth) if truth else None for truth in human["raters"]]
        result = dict(source_id=sid, source_sha256=human["source_sha256"],
            native_frames=n, original_reviewers=r, windows=len(windows), candidate_union_frames=len(union),
            actual_TIME_f1_adopted=original["metrics"]["greedy"]["f1"],
            actual_contrast_f1_adopted=original["metrics"]["contrast"]["f1"],
            protected_proxy_f1_adopted=original["metrics"]["protected_proxy"]["f1"],
            whole_source_four_slot_oracle_adopted=old_best,
            exact_window_action_oracle=window_best, exact_union_subset_oracle=union_best,
            exact_full_native_subset_oracle=native_best,
            mean_reviewer_summary_coverage_by_candidate_union=sum(v for v in recalls if v is not None)
                / sum(v is not None for v in recalls),
            gaps=dict(whole_slot_ranking=old_best-original["metrics"]["greedy"]["f1"],
                same_slot_coupling=window_best["f1"]-old_best,
                within_window_action_granularity=union_best["f1"]-window_best["f1"],
                missing_union_content=native_best["f1"]-union_best["f1"]))
        save_new(root / (sid + "_diagnostic01.json"), result)
        results.append(result)
    scalar = ["actual_TIME_f1_adopted", "actual_contrast_f1_adopted", "protected_proxy_f1_adopted",
              "whole_source_four_slot_oracle_adopted", "mean_reviewer_summary_coverage_by_candidate_union"]
    macro = {k: sum(v[k] for v in results)/len(results) for k in scalar}
    for key in ["exact_window_action_oracle", "exact_union_subset_oracle", "exact_full_native_subset_oracle"]:
        macro[key] = sum(v[key]["f1"] for v in results)/len(results)
    gaps = {k: sum(v["gaps"][k] for v in results)/len(results) for k in results[0]["gaps"]}
    result = dict(status="COMPLETE_NEW_EXTERNAL_ONLY_DIAGNOSTIC", source_count=8, window_count=43,
        macro=macro, gaps=gaps, source_refs=[reference(root/(v["source_id"]+"_diagnostic01.json")) for v in results],
        seconds=time.monotonic()-started, new_model_calls=0, new_training=0,
        old_evaluation_chain_reruns=0, original_metrics="ADOPTED_EXISTING_REVIEW_NOT_NEW_RESULTS",
        official_data_read=False, oracle_deployable=False, spatial_joint_utility="UNKNOWN",
        historical_exposure=True, omission_is_exhaustive_no_highlight=False,
        next_admission="MAIN_AGENT_REVIEW_REQUIRED_NO_AUTOMATIC_MODEL_OR_PRODUCTION")
    save_new(root / "completion01.json", result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    try:
        run(args.run_root)
    except BaseException:
        fail = dict(status="FAILED_NEW_DIAGNOSTIC_PRESERVE_OLD_SUCCESS", traceback=traceback.format_exc(),
                    utc=datetime.now(timezone.utc).isoformat())
        save_new(Path(args.run_root)/"failure01.json", fail)
        raise
