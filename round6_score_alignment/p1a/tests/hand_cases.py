"""Shared hand-computed fixtures for the P1a test suite.

Every expected value in the tests is derived by hand in the comments and written
as a literal.  Nothing here imports the implementation to *produce* an expected
value; the implementation is only compared against the literals.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

BOX_FULL = [0, 0, 720]          # [x, y, w]; h = 720 * 9 / 16 = 405.0, inside 720x1280
BOX_SHIFTED_LOW = [0, 0, 100]   # h = 100 * 9 / 16 = 56.25
BOX_SHIFTED_HIGH = [0, 28.125, 100]   # same height, shifted by half of h
BOX_NO_OVERLAP = [0, 500, 720]  # pred y 0..405 vs this y 500..905 -> IoU 0


def two_video_index() -> dict:
    """Media index for hand cases (not ground truth)."""
    return {
        "0": {"video_id": "0", "targetRatioWH": [16.0, 9.0], "width": 720, "height": 1280,
              "n_frames": 630, "video_path": "synthetic"},
        "1": {"video_id": "1", "targetRatioWH": [16.0, 9.0], "width": 720, "height": 1280,
              "n_frames": 630, "video_path": "synthetic"},
    }


def write_predictions(path: Path, rows: Mapping[str, Iterable[dict]]) -> Path:
    """Write a submission-shaped JSONL; ``box=None`` emits a bare frame record."""
    with Path(path).open("w", encoding="utf-8") as fh:
        for video_id, predictions in rows.items():
            if predictions is None:                 # omit the line entirely
                continue
            record = {"video_id": video_id, "targetRatioWH": [16, 9], "predictions": []}
            for item in predictions:
                if item is None:
                    continue
                frame = item["frame"]
                if item.get("raw") is not None:
                    record["predictions"].append(item["raw"])
                else:
                    record["predictions"].append({"frame": frame, "bboxes": item["box"]})
            fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return Path(path)


def write_raw_predictions(path: Path, lines: Sequence[str]) -> Path:
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return Path(path)


def write_reference(path: Path, *, coverage: str, videos: Mapping[str, Mapping[int, Sequence[int]]],
                    label_status: str = "SYNTHETIC_HAND_CASE") -> Path:
    payload = {
        "schema": "aic_round6_reference_v1",
        "coverage": coverage,
        "label_status": label_status,
        "annotation_source": "hand-written synthetic case (not a real video annotation)",
        "videos": [
            {"video_id": vid,
             "coverage": coverage,
             "frames": [{"frame": int(frame), "box_xyw": list(box)}
                        for frame, box in sorted(frames.items())]}
            for vid, frames in sorted(videos.items())
        ],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return Path(path)
