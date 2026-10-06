from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable


class ReferenceValidationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReferenceValidationError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ReferenceValidationError(f"{name} must be finite")
    return value


def validate_item(item: dict, media_root: Path) -> None:
    required = {
        "dataset", "item_id", "source_group", "split", "target_ratio_wh",
        "media_rel_path", "media_sha256", "source_width", "source_height",
        "reference_boxes", "annotation_semantics", "coverage", "evidence_tier",
    }
    missing = sorted(required - item.keys())
    if missing:
        raise ReferenceValidationError(f"missing fields: {missing}")
    if item["split"] not in {"dev", "sealed_holdout"}:
        raise ReferenceValidationError("invalid split")
    if item["coverage"] not in {"single_image", "sparse"}:
        raise ReferenceValidationError("invalid coverage")
    ratio = item["target_ratio_wh"]
    if not isinstance(ratio, list) or len(ratio) != 2:
        raise ReferenceValidationError("target_ratio_wh must be [w,h]")
    rw, rh = (_number(ratio[0], "ratio_w"), _number(ratio[1], "ratio_h"))
    if rw <= 0 or rh <= 0:
        raise ReferenceValidationError("target ratio must be positive")
    width = int(_number(item["source_width"], "source_width"))
    height = int(_number(item["source_height"], "source_height"))
    if width <= 0 or height <= 0:
        raise ReferenceValidationError("invalid media dimensions")
    boxes = item["reference_boxes"]
    if not isinstance(boxes, list) or not boxes:
        raise ReferenceValidationError("reference_boxes must be nonempty")
    for i, box in enumerate(boxes):
        if not isinstance(box, list) or len(box) != 4:
            raise ReferenceValidationError(f"box {i} must be [x,y,w,h]")
        x, y, w, h = (_number(v, f"box[{i}]") for v in box)
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width + 1e-6 or y + h > height + 1e-6:
            raise ReferenceValidationError(f"box {i} out of bounds")
        expected = rw / rh
        actual = w / h
        pixel_tolerance = 2.0 / max(h, 1.0)
        if abs(actual - expected) > pixel_tolerance:
            raise ReferenceValidationError(f"box {i} wrong ratio: {actual} vs {expected}")
    media = media_root / item["media_rel_path"]
    if not media.is_file():
        raise ReferenceValidationError(f"missing media: {media}")
    if sha256_file(media).lower() != str(item["media_sha256"]).lower():
        raise ReferenceValidationError("media sha256 mismatch")


def validate_manifest(rows: Iterable[dict], media_root: Path) -> dict:
    rows = list(rows)
    seen = set()
    groups_by_split: dict[str, set[str]] = {"dev": set(), "sealed_holdout": set()}
    issues: list[dict] = []
    for idx, item in enumerate(rows):
        frame_identity = item.get("frame_index", item.get("item_id"))
        key = (item.get("source_group"), frame_identity, tuple(item.get("target_ratio_wh", [])))
        if key in seen:
            issues.append({"row": idx, "error": "duplicate item/ratio"})
            continue
        seen.add(key)
        try:
            validate_item(item, media_root)
            groups_by_split[item["split"]].add(item["source_group"])
        except (ReferenceValidationError, OSError) as exc:
            issues.append({"row": idx, "error": str(exc)})
    overlap = sorted(groups_by_split["dev"] & groups_by_split["sealed_holdout"])
    if overlap:
        issues.append({"row": None, "error": f"source leakage across splits: {overlap}"})
    return {
        "status": "OK" if not issues else "INVALID_INPUT",
        "rows": len(rows),
        "issues": issues,
        "dev_groups": len(groups_by_split["dev"]),
        "sealed_holdout_groups": len(groups_by_split["sealed_holdout"]),
    }


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ReferenceValidationError(f"invalid JSON line {line_no}: {exc}") from exc
            if not isinstance(value, dict):
                raise ReferenceValidationError(f"line {line_no} is not an object")
            rows.append(value)
    return rows
