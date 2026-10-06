from __future__ import annotations

import math


def iou_xywh(a: list[float], b: list[float]) -> float:
    ax, ay, aw, ah = map(float, a)
    bx, by, bw, bh = map(float, b)
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def score_one_frame(predictions: list[list[float]], references: list[list[float]]) -> float:
    """Internal diagnostic only: best pair IoU; both empty=1, one empty=0."""
    if not predictions and not references:
        return 1.0
    if not predictions or not references:
        return 0.0
    return max(iou_xywh(p, r) for p in predictions for r in references)
