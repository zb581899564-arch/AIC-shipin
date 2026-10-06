"""Prepare exact sequentially decoded frames only for random-seek identity failures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--previous-output", type=Path, required=True)
    parser.add_argument("--frame-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, required=True)
    args = parser.parse_args()
    if args.frame_dir.exists() or args.manifest.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite retry preparation")
    selected = sorted(read_jsonl(args.selected), key=lambda x: (str(x["video_id"]), int(x["source_frame"])))
    requests = read_jsonl(args.requests)
    prior = read_jsonl(args.previous_output)
    request_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in requests}
    prior_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in prior}
    if set(request_by_key) != set(prior_by_key):
        raise ValueError("prior output does not cover exact request set")
    failed = {key for key, row in prior_by_key.items() if row.get("status") != "MODEL_OK"}
    if not failed or any(prior_by_key[key].get("parse_error") !=
                         "RuntimeError: decoded frame identity changed" for key in failed):
        raise ValueError("retry set contains an unregistered failure type")
    selected_keys = {(str(x["video_id"]), int(x["source_frame"])) for x in selected}
    if not failed <= selected_keys:
        raise ValueError("failed anchor outside selected frame set")
    root = args.allowed_root.resolve(strict=True)
    args.frame_dir.mkdir(parents=True, exist_ok=False)
    rows, mismatches = [], []
    cap = None
    active_path = None
    previous = None
    try:
        for item in selected:
            path = Path(item["source_path"]).resolve(strict=True)
            if root not in path.parents:
                raise ValueError(f"source outside allowed root: {path}")
            key = (str(item["video_id"]), int(item["source_frame"]))
            contiguous = (previous is not None and previous[0] == key[0]
                          and previous[1] + 1 == key[1] and active_path == path)
            if not contiguous:
                if cap is not None:
                    cap.release()
                cap = cv2.VideoCapture(str(path))
                if not cap.isOpened():
                    raise RuntimeError(f"cannot open {path}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, key[1])
                active_path = path
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f"decode failed: {key}")
            if key in failed:
                pixel_hash = hashlib.sha256(memoryview(frame).cast("B")).hexdigest()
                expected = request_by_key[key]["expected_pixel_sha256"]
                if pixel_hash != expected:
                    mismatches.append({"video_id": key[0], "source_frame": key[1],
                                       "expected": expected, "actual": pixel_hash})
                frame_path = args.frame_dir / f"{key[0]}_{key[1]}.npy"
                np.save(frame_path, frame, allow_pickle=False)
                rows.append({"video_id": key[0], "source_frame": key[1],
                             "frame_npy": str(frame_path), "frame_npy_sha256": sha(frame_path),
                             "decoded_pixel_sha256": pixel_hash,
                             "anchor_request_sha256": request_by_key[key]["anchor_request_sha256"],
                             "target_ratio_wh": request_by_key[key]["target_ratio_wh"],
                             "source_width": int(item["source_width"]),
                             "source_height": int(item["source_height"])})
            previous = key
    finally:
        if cap is not None:
            cap.release()
    with args.manifest.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report = {"status": "PASS_IDENTITY_RETRY_PREPARATION" if not mismatches and len(rows) == len(failed)
              else "FAIL_IDENTITY_RETRY_PREPARATION", "failed_anchors": len(failed),
              "prepared_frames": len(rows), "identity_matches": len(rows) - len(mismatches),
              "identity_mismatches": len(mismatches), "mismatches": mismatches,
              "selected_sha256": sha(args.selected), "requests_sha256": sha(args.requests),
              "previous_output_sha256": sha(args.previous_output),
              "manifest_sha256": sha(args.manifest),
              "frame_bytes": sum(Path(x["frame_npy"]).stat().st_size for x in rows)}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"].startswith("PASS") else 5


if __name__ == "__main__":
    raise SystemExit(main())
