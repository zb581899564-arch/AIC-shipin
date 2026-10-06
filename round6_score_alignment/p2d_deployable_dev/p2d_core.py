"""Pure-CPU helpers for the P2-D deployable development slice.

This module deliberately has no model dependency.  It implements the frozen
crop geometry, strict per-frame accounting and weak-reference IoU used by the
P2-D validation scripts.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path | str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def write_jsonl(path: Path | str, rows: Iterable[Mapping]) -> None:
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite {target}")
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def legal_crop_width(width: int, height: int, target_w: float, target_h: float) -> int:
    """Mirror the frozen baseline's maximum legal submitted integer width."""
    if width <= 0 or height <= 0 or target_w <= 0 or target_h <= 0:
        raise ValueError("invalid source or target geometry")
    if width / float(height) >= target_w / target_h:
        crop_w = min(width, max(1, int(math.floor(height * target_w / target_h + 1e-12))))
    else:
        crop_w = width
    while crop_w > 1 and crop_w * target_h > height * target_w:
        crop_w -= 1
    return crop_w


def center_max_crop(width: int, height: int, target_w: float, target_h: float) -> list[int]:
    crop_w = legal_crop_width(width, height, target_w, target_h)
    crop_h = crop_w * target_h / target_w
    max_x = max(0, width - crop_w)
    max_y = max(0, int(math.floor(height - crop_h + 1e-9)))
    x = min(max_x, max(0, int(round(width * 0.5 - crop_w * 0.5))))
    y = min(max_y, max(0, int(round(height * 0.5 - crop_h * 0.5))))
    return [x, y, crop_w]


def box_is_legal(box: Sequence, width: int, height: int,
                 target_w: float, target_h: float) -> bool:
    if not isinstance(box, (list, tuple)) or len(box) != 3:
        return False
    if any(isinstance(value, bool) or not isinstance(value, int) for value in box):
        return False
    x, y, crop_w = box
    if crop_w <= 0 or x < 0 or y < 0 or x + crop_w > width:
        return False
    crop_h = crop_w * target_h / target_w
    return math.isfinite(crop_h) and crop_h > 0 and y + crop_h <= height + 1e-7


def validate_outputs(requests: Sequence[Mapping], outputs: Sequence[Mapping]) -> dict:
    """Validate model results without treating failures as legal empty output."""
    request_keys = [(str(row["video_id"]), int(row["source_frame"])) for row in requests]
    output_keys = [(str(row.get("video_id")), int(row.get("source_frame", -1))) for row in outputs]
    request_set, output_set = set(request_keys), set(output_keys)
    duplicate_requests = len(request_keys) - len(request_set)
    duplicate_outputs = len(output_keys) - len(output_set)
    missing = sorted(request_set - output_set)
    extra = sorted(output_set - request_set)
    request_by_key = {(str(r["video_id"]), int(r["source_frame"])): r for r in requests}
    failures: list[dict] = []
    legal = 0
    for row in outputs:
        key = (str(row.get("video_id")), int(row.get("source_frame", -1)))
        req = request_by_key.get(key)
        reasons = []
        if req is None:
            reasons.append("EXTRA_KEY")
        else:
            status = row.get("status")
            if status != "MODEL_OK":
                reasons.append(f"STATUS_{status or 'MISSING'}")
            if row.get("used_fallback"):
                reasons.append("SILENT_FALLBACK_FORBIDDEN")
            source = str(row.get("spatial_source", ""))
            if source != "REAL_QWEN_SAME_FRAME":
                reasons.append("NON_DEPLOYABLE_SPATIAL_SOURCE")
            tw, th = req["target_ratio_wh"]
            if not box_is_legal(row.get("box_xyw"), int(req["source_width"]),
                                int(req["source_height"]), float(tw), float(th)):
                reasons.append("ILLEGAL_OR_MISSING_BOX")
        if reasons:
            failures.append({"video_id": key[0], "source_frame": key[1], "reasons": reasons})
        else:
            legal += 1
    selection_complete = (not duplicate_requests and not duplicate_outputs and not missing
                          and not extra and legal == len(request_keys) and not failures)
    return {
        "requested": len(request_keys),
        "outputs": len(output_keys),
        "legal_deployable": legal,
        "duplicate_requests": duplicate_requests,
        "duplicate_outputs": duplicate_outputs,
        "missing_count": len(missing),
        "extra_count": len(extra),
        "missing_first_20": missing[:20],
        "extra_first_20": extra[:20],
        "failure_count": len(failures),
        "failures": failures,
        "format_valid": not duplicate_outputs and not extra and not any(
            "ILLEGAL_OR_MISSING_BOX" in item["reasons"] for item in failures),
        "selection_complete": selection_complete,
        "deployable": selection_complete,
    }


def xywh_iou(pred_xyw: Sequence[int] | None, weak_xywh: Sequence[int]) -> float:
    """IoU between implicit-height submitted box and an explicit weak ROI."""
    if pred_xyw is None:
        return 0.0
    px, py, pw = (float(v) for v in pred_xyw)
    ph = pw * 16.0 / 9.0
    wx, wy, ww, wh = (float(v) for v in weak_xywh)
    ix1, iy1 = max(px, wx), max(py, wy)
    ix2, iy2 = min(px + pw, wx + ww), min(py + ph, wy + wh)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = pw * ph + ww * wh - inter
    return inter / union if union > 0 else 0.0

