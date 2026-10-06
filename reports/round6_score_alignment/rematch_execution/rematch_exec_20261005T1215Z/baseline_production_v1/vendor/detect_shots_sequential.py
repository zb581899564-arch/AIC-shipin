"""Equivalent P2-J shot analysis with sequential decoding inside selected runs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

HIST_THRESHOLD = 0.35
GRAY_MAD_THRESHOLD = 0.18


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def descriptors(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    small = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [32, 16], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return hist, cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, action="append", required=True)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite shot artifacts")
    selected = sorted(read_jsonl(args.selected), key=lambda x: (str(x["video_id"]), int(x["source_frame"])))
    keys = [(x["video_id"], int(x["source_frame"])) for x in selected]
    if not selected or len(keys) != len(set(keys)):
        raise ValueError("empty or duplicate selected manifest")
    roots = [x.resolve(strict=True) for x in args.allowed_root]
    result = []
    previous = None
    cap = None
    active_path = None
    try:
        for request in selected:
            path = Path(request["source_path"]).resolve(strict=True)
            if not any(root == path or root in path.parents for root in roots):
                raise ValueError(f"source outside allowed roots: {path}")
            frame_number = int(request["source_frame"])
            contiguous = (previous is not None and previous["video_id"] == request["video_id"]
                          and previous["source_frame"] + 1 == frame_number and active_path == path)
            if not contiguous:
                if cap is not None:
                    cap.release()
                cap = cv2.VideoCapture(str(path))
                if not cap.isOpened():
                    raise RuntimeError(f"cannot open {path}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                active_path = path
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f"decode failed: {request['video_id']}:{frame_number}")
            if [frame.shape[1], frame.shape[0]] != [int(request["source_width"]), int(request["source_height"])]:
                raise RuntimeError("decoded geometry changed")
            hist, gray = descriptors(frame)
            reasons = []
            hist_distance = gray_mad = None
            if not contiguous:
                reasons.append("VIDEO_OR_SELECTION_DISCONTINUITY")
            else:
                hist_distance = float(cv2.compareHist(previous["hist"], hist,
                                                       cv2.HISTCMP_BHATTACHARYYA))
                gray_mad = float(np.mean(cv2.absdiff(previous["gray"], gray)) / 255.0)
                if hist_distance >= HIST_THRESHOLD:
                    reasons.append("HSV_HIST_CUT")
                if gray_mad >= GRAY_MAD_THRESHOLD:
                    reasons.append("GRAY_MAD_CUT")
            result.append({
                "video_id": request["video_id"], "source_frame": frame_number,
                "decoded_pixel_sha256": hashlib.sha256(memoryview(frame).cast("B")).hexdigest(),
                "is_shot_start": bool(reasons), "boundary_reasons": reasons,
                "hist_bhattacharyya": hist_distance, "gray_mad": gray_mad,
            })
            previous = {"video_id": request["video_id"], "source_frame": frame_number,
                        "hist": hist, "gray": gray}
    finally:
        if cap is not None:
            cap.release()
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for row in result:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    summary = {"status": "SHOT_ANALYSIS_COMPLETE", "frames": len(result),
               "videos": len({x["video_id"] for x in result}),
               "shot_starts": sum(x["is_shot_start"] for x in result),
               "hist_threshold": HIST_THRESHOLD, "gray_mad_threshold": GRAY_MAD_THRESHOLD,
               "selected_sha256": sha(args.selected), "output_sha256": sha(args.output)}
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
