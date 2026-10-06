"""Pure-temporal R7 audit, deterministic split, diagnostics, and gates."""
from __future__ import annotations

import hashlib
import math
import random
import statistics
from collections import defaultdict
from typing import Iterable


SEED = 20260921
FRAME_TOLERANCE_EPS = 1e-6


def stable_key(namespace: str, value: str, seed: int = SEED) -> str:
    return hashlib.sha256(f"{seed}:{namespace}:{value}".encode()).hexdigest()


def validate_segments(segments: list[list[float]], duration: float) -> list[str]:
    issues: list[str] = []
    if not 1 <= len(segments) <= 5:
        issues.append(f"segment_count:{len(segments)}")
    previous_end = None
    for i, pair in enumerate(segments):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            issues.append(f"segment_shape:{i}")
            continue
        a, b = pair
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   and math.isfinite(float(v)) for v in (a, b)):
            issues.append(f"segment_nonfinite:{i}")
            continue
        a, b = float(a), float(b)
        if not 0 <= a < b <= duration + 1e-9:
            issues.append(f"segment_bounds:{i}")
        if previous_end is not None and a < previous_end - 1e-9:
            issues.append(f"segment_overlap_or_unsorted:{i}")
        previous_end = b
    return issues


def audit_pts_sequence(pts: list[float], avg_fps: float) -> dict:
    """Audit decoded PTS against the index/fps convention used by Decord."""
    if avg_fps <= 0 or not math.isfinite(avg_fps):
        return {"passed": False, "reason": "invalid_avg_fps"}
    if len(pts) < 2 or any(not math.isfinite(x) for x in pts):
        return {"passed": False, "reason": "missing_or_nonfinite_pts"}
    deltas = [b - a for a, b in zip(pts, pts[1:])]
    if any(d <= 0 for d in deltas):
        return {"passed": False, "reason": "pts_not_strictly_increasing"}
    median_interval = statistics.median(deltas)
    residuals = [abs((p - pts[0]) - i / avg_fps) for i, p in enumerate(pts)]
    maximum = max(residuals)
    passed = maximum <= median_interval + FRAME_TOLERANCE_EPS
    return {
        "passed": passed,
        "reason": None if passed else "pts_residual_exceeds_one_median_frame",
        "decoded_frames": len(pts),
        "first_pts_sec": pts[0],
        "last_pts_sec": pts[-1],
        "median_frame_interval_sec": median_interval,
        "max_index_pts_residual_sec": maximum,
        "decoded_duration_sec": pts[-1] - pts[0] + median_interval,
    }


def duration_bin(value: float) -> str:
    if value <= 10:
        return "le10"
    if value <= 20:
        return "10to20"
    return "gt20"


def segment_bin(value: int) -> str:
    return str(value) if value in (1, 2) else "3plus"


def group_stratum(rows: list[dict]) -> str:
    uncertain = any(r["mapping_status"] == "time_uncertain" for r in rows)
    duration = statistics.median(r["clip_duration_sec"] for r in rows)
    segments = max(r["n_segments"] for r in rows)
    return f"{'uncertain' if uncertain else 'usable'}|{duration_bin(duration)}|{segment_bin(segments)}"


def proportional_targets(counts: dict[str, int], total: int) -> dict[str, int]:
    available = sum(counts.values())
    if total < 0 or total > available:
        raise ValueError("invalid allocation total")
    raw = {k: total * v / available for k, v in counts.items()}
    out = {k: min(counts[k], int(math.floor(raw[k]))) for k in counts}
    remaining = total - sum(out.values())
    order = sorted(counts, key=lambda k: (-(raw[k] - math.floor(raw[k])), k))
    while remaining:
        progressed = False
        for key in order:
            if out[key] < counts[key]:
                out[key] += 1
                remaining -= 1
                progressed = True
                if remaining == 0:
                    break
        if not progressed:
            raise RuntimeError("could not satisfy proportional allocation")
    return out


def select_stratified_groups(rows: list[dict], excluded_groups: set[str],
                             dev_groups: int = 96, confirm_groups: int = 96,
                             seed: int = SEED) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["youtube_id"]].append(row)
    candidates = {g: rs for g, rs in grouped.items() if g not in excluded_groups}
    if len(candidates) < dev_groups + confirm_groups:
        raise RuntimeError(
            f"insufficient model-unseen groups: {len(candidates)} < {dev_groups + confirm_groups}")
    strata: dict[str, list[str]] = defaultdict(list)
    for group, group_rows in candidates.items():
        strata[group_stratum(group_rows)].append(group)
    for key in strata:
        strata[key].sort(key=lambda g: stable_key(f"stratum:{key}", g, seed))

    dev_targets = proportional_targets({k: len(v) for k, v in strata.items()}, dev_groups)
    dev: set[str] = set()
    remaining: dict[str, list[str]] = {}
    for key, groups in strata.items():
        take = dev_targets[key]
        dev.update(groups[:take])
        remaining[key] = groups[take:]

    confirm_targets = proportional_targets(
        {k: len(v) for k, v in remaining.items()}, confirm_groups)
    confirm: set[str] = set()
    for key, groups in remaining.items():
        confirm.update(groups[:confirm_targets[key]])
    if len(dev) != dev_groups or len(confirm) != confirm_groups or dev & confirm:
        raise RuntimeError("deterministic split cardinality failure")
    train = set(grouped) - dev - confirm
    if train & dev or train & confirm:
        raise RuntimeError("source group leakage")
    return {
        "train": train,
        "dev": dev,
        "confirm": confirm,
        "model_unseen_candidates": set(candidates),
        "strata": {k: {
            "available": len(strata[k]),
            "dev": dev_targets[k],
            "confirm": confirm_targets[k],
        } for k in sorted(strata)},
    }


def union(values: Iterable[list[float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for a, b in sorted((float(a), float(b)) for a, b in values):
        if not out or a > out[-1][1]:
            out.append([a, b])
        else:
            out[-1][1] = max(out[-1][1], b)
    return out


def temporal_stats(pred: list[list[float]], truth: list[list[float]]) -> dict:
    p, g = union(pred), union(truth)
    pl = sum(b - a for a, b in p)
    gl = sum(b - a for a, b in g)
    inter = sum(max(0.0, min(pb, gb) - max(pa, ga))
                for pa, pb in p for ga, gb in g)
    precision = inter / pl if pl else (1.0 if not gl else 0.0)
    recall = inter / gl if gl else (1.0 if not pl else 0.0)
    f1 = 2 * inter / (pl + gl) if pl + gl else 1.0
    return {
        "pred_seconds": pl,
        "truth_seconds": gl,
        "intersection_seconds": inter,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "duration_ratio": pl / gl if gl else None,
        "zero_overlap": inter <= 0,
    }


def bootstrap_ci(diffs: list[float], draws: int = 10000,
                 seed: int = SEED) -> list[float]:
    if not diffs:
        raise ValueError("empty bootstrap differences")
    rng = random.Random(seed)
    sims = [statistics.mean(rng.choice(diffs) for _ in diffs) for _ in range(draws)]
    sims.sort()
    return [sims[int(0.025 * draws)], sims[int(0.975 * draws)]]


def decide_gate(data: dict, stage: str) -> dict:
    if stage not in {"dev", "confirm"}:
        raise ValueError("stage must be dev or confirm")
    arms = data["per_arm"]
    fresh, p2t2, base = arms["R7"], arms["P2T2"], arms["BASE"]
    paired = data["paired"]["R7_minus_P2T2"]
    required_gain = 0.03 if stage == "dev" else 0.02
    checks = {
        "f1_gain": paired["mean"] >= required_gain,
        "bootstrap_lower_above_zero": paired["ci95"][0] > 0,
        "recall_not_below_base_or_p2t2": fresh["group_macro_recall"] >= max(
            base["group_macro_recall"], p2t2["group_macro_recall"]),
        "precision_drop_at_most_0_03": fresh["group_macro_precision"] >= (
            p2t2["group_macro_precision"] - 0.03),
        "valid_rate_1": fresh["valid_rate"] == 1.0,
        "zero_overlap_not_increased": fresh["zero_overlap_videos"] <= p2t2["zero_overlap_videos"],
        "required_slices_not_degraded": all(
            item.get("passed", True) for item in data.get("slice_gates", {}).values()),
    }
    return {
        "stage": stage,
        "status": (f"R7_{stage.upper()}_PASS" if all(checks.values())
                   else "STOP_KEEP_P2T2"),
        "metric_status": "MODEL_UNSEEN_FIXED_WEAK_DIAGNOSTIC_NOT_OFFICIAL_SCORE",
        "required_f1_gain": required_gain,
        "checks": checks,
        "r7_minus_p2t2": paired,
        "arms": {name: arms[name] for name in ("BASE", "P2T2", "R7")},
    }
