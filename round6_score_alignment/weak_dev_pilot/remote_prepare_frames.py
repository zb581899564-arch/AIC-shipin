"""Training-host PTS gate, then exact-order frame extraction for weak dev data.

Usage: python remote_prepare_frames.py dev_frames.jsonl OUTPUT_DIRECTORY
The script rejects any path outside the training-video tree. It must finish
with PTS_GATE_PASS before a GPU job is allowed to consume its images.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import cv2


VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def timestamps(path: Path) -> list[float | None]:
    run = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "frame=best_effort_timestamp_time",
                          "-of", "csv=p=0", str(path)], capture_output=True,
                         text=True, check=True, timeout=180)
    result = []
    for line in run.stdout.splitlines():
        token = line.strip().split(",")[0]
        if token:
            result.append(None if token == "N/A" else float(token))
    return result


def main(manifest_path: str, output_dir: str):
    manifest = Path(manifest_path)
    rows = load_jsonl(manifest)
    if not rows or len({r["sample_key"] for r in rows}) != len(rows):
        raise ValueError("empty or duplicate frozen manifest")
    groups = defaultdict(list)
    for row in rows:
        source = Path(row["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents or source.suffix.lower() != ".mp4":
            raise ValueError(f"source outside training videos: {source}")
        groups[source].append(row)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    for path, items in sorted(groups.items()):
        pts = timestamps(path)
        for item in items:
            n = int(item["source_frame"])
            delta = (abs(pts[n] - float(item["source_time_sec"]))
                     if 0 <= n < len(pts) and pts[n] is not None else None)
            limit = 1 / float(item["source_fps"])
            checks.append({"sample_key": item["sample_key"], "source_frame": n,
                           "source_pts_sec": pts[n] if delta is not None else None,
                           "source_time_sec": item["source_time_sec"],
                           "abs_difference_sec": delta, "limit_sec": limit,
                           "pass": delta is not None and delta <= limit + 1e-9})
    gate = {"status": "PTS_GATE_PASS" if all(x["pass"] for x in checks) else "PTS_GATE_FAIL",
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "frames": len(rows), "source_files": len(groups),
            "max_abs_difference_sec": max((x["abs_difference_sec"] or 0) for x in checks),
            "failures": [x for x in checks if not x["pass"]],
            "checks": checks}
    (out / "pts_gate.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if gate["status"] != "PTS_GATE_PASS":
        print(f"PTS_GATE_FAIL: {len(gate['failures'])}/{len(checks)}", flush=True)
        return 2

    images = out / "images"
    images.mkdir(exist_ok=True)
    extraction = []
    for path, items in sorted(groups.items()):
        wanted = defaultdict(list)
        for item in items:
            wanted[int(item["source_frame"])].append(item)
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise RuntimeError(f"cannot open source {path}")
        found = 0
        for frame_number in range(max(wanted) + 1):
            ok, frame = cap.read()
            if not ok:
                break
            if frame_number not in wanted:
                continue
            for item in wanted[frame_number]:
                if frame.shape[1] != item["source_width"] or frame.shape[0] != item["source_height"]:
                    raise RuntimeError(f"dimension mismatch for {item['sample_key']}")
                name = hashlib.sha256(item["sample_key"].encode()).hexdigest()[:24] + ".png"
                dest = images / name
                if not cv2.imwrite(str(dest), frame):
                    raise RuntimeError(f"cannot save {dest}")
                extraction.append({"sample_key": item["sample_key"],
                                   "source_frame": frame_number, "image_path": str(dest),
                                   "image_sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
                found += 1
        cap.release()
        if found != len(items):
            raise RuntimeError(f"decoded {found}/{len(items)} wanted frames for {path}")
    if len(extraction) != len(rows):
        raise RuntimeError("incomplete extraction")
    (out / "extracted_frames.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in extraction), encoding="utf-8")
    print(f"PTS_GATE_PASS extracted={len(extraction)} sources={len(groups)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
