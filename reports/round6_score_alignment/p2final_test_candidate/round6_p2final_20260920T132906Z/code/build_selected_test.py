"""Convert frozen temporal windows to ceil/half-open test frame selections."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def metadata_ratio(value) -> list[int]:
    values = value if isinstance(value, list) else str(value).split()
    if len(values) != 2 or any(isinstance(x, bool) for x in values):
        raise ValueError("invalid targetRatioWH metadata")
    ratio = [int(x) for x in values]
    if any(x <= 0 for x in ratio):
        raise ValueError("non-positive targetRatioWH metadata")
    return ratio


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--max-invalid-rate", type=float, default=0.05)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite selection artifacts")
    temporal = rows(args.temporal)
    if len(temporal) != 174 or len({x["video_id"] for x in temporal}) != 174:
        raise ValueError("temporal output must contain 174 unique videos")
    payload = json.loads(args.metadata.read_text(encoding="utf-8"))
    metadata = {str(x["video_id"]): x for x in payload["records"]}
    if len(metadata) != 174 or payload.get("errors"):
        raise ValueError("frozen metadata is incomplete")
    windows = [w for row in temporal for w in row["windows"]]
    invalid = sum(not w.get("output_valid", False) for w in windows)
    if not windows or invalid / len(windows) > args.max_invalid_rate:
        raise RuntimeError("temporal invalid-window health gate failed")
    selected_rows = []
    per_video = []
    for record in sorted(temporal, key=lambda x: int(x["video_id"])):
        vid = str(record["video_id"])
        meta = metadata[vid]
        fps = float(record["fps"])
        n_frames = int(record["n_frames"])
        exact_fps = float(meta["fps_num"]) / float(meta["fps_den"])
        if n_frames != int(meta["n_frames"]) or abs(fps - exact_fps) > max(1e-6, exact_fps * 1e-6):
            raise RuntimeError(f"metadata mismatch for {vid}: {fps}/{n_frames} vs {exact_fps}/{meta['n_frames']}")
        ratio = metadata_ratio(meta["targetRatioWH"])
        if ratio != record["targetRatioWH"]:
            raise RuntimeError(f"ratio mismatch for {vid}")
        selected = set()
        invalid_here = 0
        for window in record["windows"]:
            if not window.get("output_valid"):
                invalid_here += 1
                continue
            start = float(window["start_sec"])
            for segment in window["parsed_segments"]:
                a, b = map(float, segment)
                first = max(0, math.ceil((start + a) * fps))
                last_exclusive = min(n_frames, math.ceil((start + b) * fps))
                if last_exclusive <= first:
                    raise RuntimeError(f"empty mapped segment for {vid}")
                selected.update(range(first, last_exclusive))
        for frame in sorted(selected):
            selected_rows.append({
                "video_id": vid, "source_frame": frame,
                "source_path": record["video_path"],
                "source_width": int(meta["width"]), "source_height": int(meta["height"]),
                "source_n_frames": n_frames, "fps": fps, "target_ratio_wh": ratio,
            })
        per_video.append({"video_id": vid, "selected_frames": len(selected),
                          "invalid_windows": invalid_here})
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for row in selected_rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "status": "SELECTION_FROZEN", "endpoint_rule": "ceil_plus_half_open",
        "videos": 174, "windows": len(windows), "invalid_windows": invalid,
        "invalid_window_rate": invalid / len(windows), "selected_frames": len(selected_rows),
        "videos_with_empty_selection": sum(x["selected_frames"] == 0 for x in per_video),
        "temporal_sha256": sha(args.temporal), "metadata_sha256": sha(args.metadata),
        "output_sha256": sha(args.output), "per_video": per_video,
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_video"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
