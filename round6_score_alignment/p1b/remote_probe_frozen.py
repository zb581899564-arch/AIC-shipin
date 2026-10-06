#!/usr/bin/env python3
"""P1b step 4 (part 1): read-only metadata + SHA-256 for the 8 frozen pilot files.

Prints JSON to stdout; writes nothing.  ffprobe is the project's existing binary.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

VIDEOS = Path("/home/inspur/aic_video_data/videos")
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"

FROZEN = [
    ("P01", "0ReDuH0_rpI_210.0_360.0.mp4", [16, 9]),
    ("P02", "FQEW3xLOa9M_210.0_360.0.mp4", [16, 9]),
    ("P03", "GYH6HdJ6nao_210.0_360.0.mp4", [16, 9]),
    ("P04", "QPcwfuStFnU_210.0_360.0.mp4", [16, 9]),
    ("P05", "Snpclpo7Ono_210.0_360.0.mp4", [9, 16]),
    ("P06", "Xm1ouND-aiQ_210.0_360.0.mp4", [9, 16]),
    ("P07", "dEuxoRj0G5Y_210.0_360.0.mp4", [9, 16]),
    ("P08", "vvT-gqzwUxA_60.0_210.0.mp4", [9, 16]),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def probe(path: Path) -> dict:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames,codec_name",
         "-show_entries", "format=duration,start_time,format_name,bit_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        return {"error": out.stderr.strip()[:200]}
    payload = json.loads(out.stdout)
    stream = (payload.get("streams") or [{}])[0]
    fmt = payload.get("format") or {}
    num, _, den = (stream.get("avg_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den) if float(den or 0) else None
    return {
        "width": int(stream["width"]), "height": int(stream["height"]),
        "codec": stream.get("codec_name"),
        "r_frame_rate_raw": stream.get("r_frame_rate"),
        "avg_frame_rate_raw": stream.get("avg_frame_rate"),
        "avg_fps": fps,
        "nb_frames": int(stream["nb_frames"]) if stream.get("nb_frames") else None,
        "duration_sec": float(fmt["duration"]) if fmt.get("duration") else None,
        "format_start_time": float(fmt["start_time"]) if fmt.get("start_time") is not None else None,
        "format_name": fmt.get("format_name"),
        "bit_rate": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
    }


def main() -> int:
    index = {p.name: p for p in VIDEOS.rglob("*.mp4")}
    result = {"ffprobe": FFPROBE, "corpus_files_indexed": len(index), "items": []}
    for sample_id, name, ratio in FROZEN:
        path = index.get(name)
        item = {"sample_id": sample_id, "file_name": name,
                "remote_path": str(path) if path else None,
                "target_ratio_wh": ratio, "exists": path is not None}
        if item["exists"]:
            item["bytes"] = path.stat().st_size
            item["sha256"] = sha256(path)
            item["probe"] = probe(path)
            probe_ok = "error" not in item["probe"]
            duration = item["probe"].get("duration_sec") if probe_ok else None
            item["checks"] = {
                "readable": probe_ok,
                "duration_in_5_180": bool(duration and 5.0 <= duration <= 180.0),
                "has_frames": bool(item["probe"].get("nb_frames") or 0) and
                              bool(item["probe"].get("avg_fps")),
            }
        result["items"].append(item)
    result["all_checks_pass"] = all(
        i.get("checks", {}).get("readable") and i.get("checks", {}).get("duration_in_5_180")
        and i.get("checks", {}).get("has_frames") for i in result["items"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
