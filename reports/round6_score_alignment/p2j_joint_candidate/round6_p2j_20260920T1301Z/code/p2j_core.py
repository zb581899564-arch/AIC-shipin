"""Pure-CPU contracts for the P2-J sparse spatial pipeline."""
from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_left
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def write_jsonl(path: str | Path, rows: Iterable[Mapping]) -> None:
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite {target}")
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def selected_source_frames(clip_start_sec: float, clip_end_sec: float, fps: float,
                           segments: Sequence[Sequence[float]]) -> list[int]:
    values = (clip_start_sec, clip_end_sec, fps)
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
           for x in values):
        raise ValueError("non-finite timebase")
    if clip_start_sec < 0 or clip_end_sec <= clip_start_sec or fps <= 0:
        raise ValueError("invalid timebase")
    duration = clip_end_sec - clip_start_sec
    start_frame = math.ceil(clip_start_sec * fps)
    end_frame = math.ceil(clip_end_sec * fps)
    chosen: set[int] = set()
    for item in segments:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("segment must be [start,end)")
        a, b = item
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
               for x in (a, b)):
            raise ValueError("non-finite segment")
        if a < 0 or b <= a or b > duration + 1e-6:
            raise ValueError("segment outside clip")
        first = start_frame + math.ceil(a * fps)
        last_exclusive = min(start_frame + math.ceil(b * fps), end_frame)
        chosen.update(range(first, last_exclusive))
    return sorted(chosen)


def legal_crop_width(width: int, height: int, target_w: float, target_h: float) -> int:
    if width <= 0 or height <= 0 or target_w <= 0 or target_h <= 0:
        raise ValueError("invalid geometry")
    crop_w = width if width / height < target_w / target_h else int(
        math.floor(height * target_w / target_h + 1e-12))
    while crop_w > 1 and crop_w * target_h > height * target_w:
        crop_w -= 1
    return crop_w


def box_is_legal(box: Sequence, width: int, height: int,
                 target_w: float, target_h: float) -> bool:
    if not isinstance(box, (list, tuple)) or len(box) != 3:
        return False
    if any(isinstance(x, bool) or not isinstance(x, int) for x in box):
        return False
    x, y, crop_w = box
    crop_h = crop_w * target_h / target_w
    return (crop_w > 0 and x >= 0 and y >= 0 and x + crop_w <= width
            and math.isfinite(crop_h) and crop_h > 0
            and y + crop_h <= height + 1e-7)


def canonical_ratio(values: Sequence) -> list[int | float]:
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        raise ValueError("target ratio must contain two numbers")
    out: list[int | float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(value) or value <= 0:
            raise ValueError("invalid target ratio")
        out.append(int(value) if float(value).is_integer() else float(value))
    return out


def group_shots(analysis_rows: Sequence[Mapping]) -> list[list[dict]]:
    if not analysis_rows:
        return []
    rows = sorted((dict(x) for x in analysis_rows),
                  key=lambda x: (str(x["video_id"]), int(x["source_frame"])))
    keys = [(str(x["video_id"]), int(x["source_frame"])) for x in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate analyzed frame")
    shots: list[list[dict]] = []
    current: list[dict] = []
    previous: tuple[str, int] | None = None
    for row in rows:
        key = (str(row["video_id"]), int(row["source_frame"]))
        declared = bool(row.get("is_shot_start"))
        discontinuity = previous is None or key[0] != previous[0] or key[1] != previous[1] + 1
        if not current or declared or discontinuity:
            if current:
                shots.append(current)
            current = [row]
        else:
            current.append(row)
        previous = key
    if current:
        shots.append(current)
    return shots


def anchor_frames(frames: Sequence[int], max_gap: int) -> list[int]:
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap <= 0:
        raise ValueError("max_gap must be a positive integer")
    values = [int(x) for x in frames]
    if not values or values != sorted(set(values)):
        raise ValueError("frames must be a non-empty sorted unique sequence")
    if any(b != a + 1 for a, b in zip(values, values[1:])):
        raise ValueError("one anchor schedule cannot cross a frame discontinuity")
    anchors = list(values[::max_gap])
    if anchors[-1] != values[-1]:
        anchors.append(values[-1])
    if any(b - a > max_gap for a, b in zip(anchors, anchors[1:])):
        raise AssertionError("anchor schedule exceeded max_gap")
    return anchors


def interpolate_box(frame: int, anchors: Mapping[int, Sequence[int]]) -> tuple[list[int], dict]:
    ordered = sorted(int(x) for x in anchors)
    if frame in anchors:
        return [int(x) for x in anchors[frame]], {
            "spatial_source": "QWEN_ANCHOR_SAME_FRAME",
            "left_anchor": frame, "right_anchor": frame,
            "left_distance": 0, "right_distance": 0,
        }
    pos = bisect_left(ordered, frame)
    if pos == 0 or pos == len(ordered):
        raise ValueError("frame is not bracketed by anchors")
    left, right = ordered[pos - 1], ordered[pos]
    alpha = (frame - left) / (right - left)
    box = [int(round(float(anchors[left][i])
                     + alpha * (float(anchors[right][i]) - float(anchors[left][i]))))
           for i in range(3)]
    return box, {
        "spatial_source": "SHOT_LINEAR_INTERPOLATION",
        "left_anchor": left, "right_anchor": right,
        "left_distance": frame - left, "right_distance": right - frame,
    }


def xyw_iou(a: Sequence[int], b: Sequence[int], target_w: float = 9,
            target_h: float = 16) -> float:
    ax, ay, aw = (float(x) for x in a)
    bx, by, bw = (float(x) for x in b)
    ah, bh = aw * target_h / target_w, bw * target_h / target_w
    inter = max(0.0, min(ax + aw, bx + bw) - max(ax, bx)) * max(
        0.0, min(ay + ah, by + bh) - max(ay, by))
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0
