"""Pure 16:9 deployment geometry and paired S1 risk arithmetic.

Centers are frozen BASE predictions in normalized source coordinates. Reference
rectangles stay in original pixel coordinates; choosing a width never edits them.
"""

import math
from numbers import Integral, Real

import numpy as np


def _integer(value, name, minimum=0, maximum=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    value = int(value)
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside its legal range")
    return value


def _vector(value, name, size=None):
    try:
        raw = np.asarray(value, dtype=object)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a numeric vector") from exc
    if raw.ndim != 1 or raw.size == 0 or (size is not None and raw.size != size):
        raise ValueError(f"{name} has an invalid dimension or length")
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, Real) for v in raw):
        raise ValueError(f"{name} must contain real numbers")
    try:
        result = raw.astype(np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must contain finite real numbers") from exc
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain finite real numbers")
    return result


def _frame(W, H):
    return _integer(W, "W", 1), _integer(H, "H", 1)


def _center(center):
    result = _vector(center, "center", 2)
    if np.any((result < 0) | (result > 1)):
        raise ValueError("center must be normalized to [0, 1]")
    return result


def _reference(reference_xywh, W=None, H=None):
    result = _vector(reference_xywh, "reference_xywh", 4)
    x, y, width, height = result
    if min(x, y) < 0 or min(width, height) <= 0:
        raise ValueError("reference_xywh must have nonnegative origin and positive size")
    if W is not None and (x + width > W + 1e-9 or y + height > H + 1e-9):
        raise ValueError("reference_xywh lies outside the source frame")
    return result


def _place(W, H, center, relative):
    max_width = min(W, H * 16 // 9)
    width = max(1, max_width * relative // 1000)
    height = width * 9 / 16
    x = round(min(max(center[0] * W - width / 2, 0), W - width))
    y_limit = math.floor(H - height + 1e-9)
    y = round(min(max(center[1] * H - height / 2, 0), y_limit))
    return [int(x), int(y), width]


def box_for_width(W, H, center, relative):
    """Return integer [x, y, width] using the unchanged deployment placement."""
    W, H = _frame(W, H)
    center = _center(center)
    relative = _integer(relative, "relative", 1, 1000)
    return _place(W, H, center, relative)


def rect(box):
    """Expand a legal integer crop triplet to [x, y, width, float_height]."""
    try:
        raw = np.asarray(box, dtype=object)
    except (TypeError, ValueError) as exc:
        raise ValueError("box must be an integer triplet") from exc
    if raw.ndim != 1 or raw.size != 3:
        raise ValueError("box must be an integer triplet")
    x = _integer(raw[0], "box x", 0)
    y = _integer(raw[1], "box y", 0)
    width = _integer(raw[2], "box width", 1)
    return [x, y, width, width * 9 / 16]


def _iou_xywh(candidate, reference):
    x, y, width, height = candidate
    rx, ry, rw, rh = reference
    intersection = max(0.0, min(x + width, rx + rw) - max(x, rx)) * max(
        0.0, min(y + height, ry + rh) - max(y, ry)
    )
    union = width * height + rw * rh - intersection
    if not math.isfinite(union) or union <= 0:
        raise ValueError("rectangle areas must be positive and finite")
    return float(intersection / union)


def iou(box, reference_xywh):
    """Calculate crop IoU against an unmodified pixel-space reference."""
    return _iou_xywh(rect(box), _reference(reference_xywh))


def conditioned_target(W, H, center, reference_xywh):
    """Enumerate 1..1000 at the deployed center and return (relative, box, IoU).

    Exactly equal IoUs prefer larger pixel width, then larger relative width.
    The target optimizes only this finite width family at the supplied center.
    """
    W, H = _frame(W, H)
    center = _center(center)
    reference = _reference(reference_xywh, W, H)
    best_relative, best_box, best_iou = 0, None, -1.0
    for relative in range(1, 1001):
        box = _place(W, H, center, relative)
        score = _iou_xywh([*box, box[2] * 9 / 16], reference)
        improves = score > best_iou
        tied_wider = score == best_iou and (box[2], relative) > (
            best_box[2], best_relative
        )
        if improves or tied_wider:
            best_relative, best_box, best_iou = relative, box, score
    return best_relative, best_box, best_iou


def human_width_target(W, H, normalized_xyxy):
    """Normalize the human reference width by maximum legal 16:9 integer width."""
    W, H = _frame(W, H)
    x1, y1, x2, y2 = _vector(normalized_xyxy, "normalized_xyxy", 4)
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        raise ValueError("normalized_xyxy must be ordered and lie in [0, 1]")
    max_width = min(W, H * 16 // 9)
    return min(1000, max(1, round((x2 - x1) * W / max_width * 1000)))


def _paired_metrics(baseline, candidate):
    # Convert before subtracting: unsigned inputs must not wrap around.
    delta = candidate.astype(np.float64) - baseline.astype(np.float64)
    count = max(1, math.ceil(delta.size * 0.1))
    metrics = {
        "mean_delta": float(np.mean(delta)),
        "median_delta": float(np.median(delta)),
        "worst_decile_mean_delta": float(np.mean(np.sort(delta)[:count])),
        "loss_over_025_fraction": float(np.mean(delta < -0.25)),
        "mean_base": float(np.mean(baseline)),
        "mean_candidate": float(np.mean(candidate)),
        "positive_fraction": float(np.mean(delta > 0)),
    }
    gates = {
        "mean_positive": metrics["mean_delta"] > 0,
        "median_nonnegative": metrics["median_delta"] >= 0,
        "worst_decile_at_least_minus_010": metrics["worst_decile_mean_delta"] >= -0.10,
        "severe_loss_at_most_005": metrics["loss_over_025_fraction"] <= 0.05,
    }
    return {"n": int(delta.size), **metrics, "gates": gates, "passed": all(gates.values())}


def _bin_labels(human_bin, count):
    try:
        labels = np.asarray(human_bin, dtype=object)
    except (TypeError, ValueError) as exc:
        raise ValueError("human_bin must be a vector of labels") from exc
    if labels.ndim != 1 or labels.size != count:
        raise ValueError("human_bin must align with the IoU vectors")
    is_text = all(isinstance(v, str) and bool(v.strip()) for v in labels)
    is_integer = all(
        isinstance(v, Integral) and not isinstance(v, (bool, np.bool_)) for v in labels
    )
    if not (is_text or is_integer):
        raise ValueError("human_bin must contain homogeneous integer or nonempty string labels")
    return labels


def risk_summary(baseline_iou, candidate_iou, relative_pred, human_bin=None):
    """Report paired risks, fixed acceptance gates, and optional human-bin detail.

    IoUs are finite one-dimensional [0, 1] values. Predictions are integer grammar
    values 1..1000. Optional labels may be homogeneous integers or strings; this
    function does not infer bin boundaries or weight the overall metrics by bin.
    """
    baseline = _vector(baseline_iou, "baseline_iou")
    candidate = _vector(candidate_iou, "candidate_iou", baseline.size)
    prediction = _vector(relative_pred, "relative_pred", baseline.size)
    if np.any((baseline < 0) | (baseline > 1) | (candidate < 0) | (candidate > 1)):
        raise ValueError("IoUs must lie in [0, 1]")
    if np.any((prediction < 1) | (prediction > 1000) | (prediction != np.floor(prediction))):
        raise ValueError("relative_pred must contain integer values in 1..1000")
    result = _paired_metrics(baseline, candidate)
    result["relative_pred_mean"] = float(np.mean(prediction))
    result["relative_pred_min"] = int(np.min(prediction))
    result["relative_pred_max"] = int(np.max(prediction))
    if human_bin is not None:
        labels = _bin_labels(human_bin, baseline.size)
        result["by_human_bin"] = {
            str(label): _paired_metrics(baseline[labels == label], candidate[labels == label])
            for label in sorted(set(labels.tolist()))
        }
    return result
