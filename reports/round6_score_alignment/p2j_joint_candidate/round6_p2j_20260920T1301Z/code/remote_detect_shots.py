"""Decode frozen non-test frames and mark conservative content boundaries."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from p2j_core import read_jsonl, sha256_file, write_jsonl

HIST_THRESHOLD = 0.35
GRAY_MAD_THRESHOLD = 0.18
VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()


def descriptors(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    small = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [32, 16], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    return hist, gray


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite shot artifacts")
    selected = read_jsonl(args.selected)
    keys = [(r["video_id"], int(r["source_frame"])) for r in selected]
    if not selected or len(keys) != len(set(keys)):
        raise ValueError("empty or duplicate selected-frame manifest")
    rows = []
    previous = None
    status_counts: dict[str, int] = {}
    for request in sorted(selected, key=lambda r: (r["video_id"], int(r["source_frame"]))):
        source = Path(request["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents:
            raise ValueError(f"source outside training media root: {source}")
        cap = cv2.VideoCapture(str(source))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(request["source_frame"]))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError(f"decode failed: {request['video_id']}:{request['source_frame']}")
        if [frame.shape[1], frame.shape[0]] != [int(request["source_width"]),
                                                int(request["source_height"])]:
            raise RuntimeError("decoded geometry changed")
        hist, gray = descriptors(frame)
        same_run = (previous is not None and previous["video_id"] == request["video_id"]
                    and previous["source_frame"] + 1 == int(request["source_frame"]))
        hist_distance = None
        gray_mad = None
        reasons = []
        if not same_run:
            reasons.append("VIDEO_OR_SELECTION_DISCONTINUITY")
        else:
            hist_distance = float(cv2.compareHist(previous["hist"], hist,
                                                   cv2.HISTCMP_BHATTACHARYYA))
            gray_mad = float(np.mean(cv2.absdiff(previous["gray"], gray)) / 255.0)
            if hist_distance >= HIST_THRESHOLD:
                reasons.append("HSV_HIST_CUT")
            if gray_mad >= GRAY_MAD_THRESHOLD:
                reasons.append("GRAY_MAD_CUT")
        is_start = bool(reasons)
        status_counts["shot_start" if is_start else "continuation"] = status_counts.get(
            "shot_start" if is_start else "continuation", 0) + 1
        rows.append({
            "video_id": request["video_id"],
            "source_frame": int(request["source_frame"]),
            "decoded_pixel_sha256": hashlib.sha256(memoryview(frame).cast("B")).hexdigest(),
            "is_shot_start": is_start,
            "boundary_reasons": reasons,
            "hist_bhattacharyya": hist_distance,
            "gray_mad": gray_mad,
        })
        previous = {"video_id": request["video_id"],
                    "source_frame": int(request["source_frame"]), "hist": hist, "gray": gray}
    write_jsonl(args.output, rows)
    report = {
        "status": "SHOT_ANALYSIS_COMPLETE",
        "selected_sha256": sha256_file(args.selected),
        "output_sha256": sha256_file(args.output),
        "frames": len(rows),
        "videos": len({r["video_id"] for r in rows}),
        "shot_starts": sum(r["is_shot_start"] for r in rows),
        "hist_threshold": HIST_THRESHOLD,
        "gray_mad_threshold": GRAY_MAD_THRESHOLD,
        "status_counts": status_counts,
    }
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
