"""CPU-only remote source-frame, PTS and media identity gate for P2-D."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from p2d_core import load_jsonl, sha256_file

VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()
FFPROBE = Path("/home/inspur/anaconda3/envs/Andy/bin/ffprobe")


def frame_sha(frame) -> str:
    return hashlib.sha256(memoryview(frame).cast("B")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("requests")
    parser.add_argument("freeze")
    parser.add_argument("output")
    args = parser.parse_args()
    requests_path, freeze_path, output = map(Path, (args.requests, args.freeze, args.output))
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if sha256_file(requests_path) != freeze["request_manifest"]["sha256"]:
        raise RuntimeError("request manifest hash differs from freeze")
    requests = load_jsonl(requests_path)
    selected_path = freeze_path.parent / freeze["selected_frames_manifest"]["path"]
    if sha256_file(selected_path) != freeze["selected_frames_manifest"]["sha256"]:
        raise RuntimeError("selected-frames manifest hash differs from freeze")
    selected_meta = {(row["video_id"], int(row["source_frame"])): row
                     for row in load_jsonl(selected_path)}
    by_video = {}
    for row in requests:
        by_video.setdefault(row["video_id"], []).append(row)

    import cv2
    results = []
    overall = True
    for video_id, rows in sorted(by_video.items()):
        source = Path(rows[0]["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents:
            raise RuntimeError(f"non-training source path: {source}")
        selected = sorted(int(row["source_frame"]) for row in rows)
        probes = sorted({selected[0], selected[len(selected) // 2], selected[-1]})
        cap = cv2.VideoCapture(str(source))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sequential = {}
        target_set = set(probes)
        index = 0
        while index <= probes[-1]:
            ok, frame = cap.read()
            if not ok:
                break
            if index in target_set:
                sequential[index] = frame.copy()
            index += 1
        cap.release()
        random_frames = {}
        for probe in probes:
            seek = cv2.VideoCapture(str(source))
            seek.set(cv2.CAP_PROP_POS_FRAMES, probe)
            ok, frame = seek.read()
            seek.release()
            if ok:
                random_frames[probe] = frame

        if not FFPROBE.is_file():
            raise RuntimeError(f"pinned ffprobe not found: {FFPROBE}")
        ffprobe = subprocess.run([
            str(FFPROBE), "-v", "error", "-select_streams", "v:0",
            "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0",
            str(source)], check=True, text=True, capture_output=True)
        pts = [float(line.strip().split(",")[0]) for line in ffprobe.stdout.splitlines()
               if line.strip() and line.strip().split(",")[0] not in {"N/A", ""}]
        first_pts = pts[0] if pts else None
        checks = []
        for probe in probes:
            seq = sequential.get(probe)
            rnd = random_frames.get(probe)
            pts_value = pts[probe] if probe < len(pts) else None
            source_fps = float(selected_meta[(video_id, probe)]["source_fps"])
            expected = probe / source_fps
            normalized_pts = pts_value - first_pts if pts_value is not None and first_pts is not None else None
            mad = None
            if seq is not None and rnd is not None:
                mad = float(cv2.absdiff(seq, rnd).mean())
            checks.append({
                "source_frame": probe,
                "sequential_decoded": seq is not None,
                "random_seek_decoded": rnd is not None,
                "sequential_pixel_sha256": frame_sha(seq) if seq is not None else None,
                "random_seek_pixel_sha256": frame_sha(rnd) if rnd is not None else None,
                "mean_abs_pixel_difference": mad,
                "best_effort_timestamp_time": pts_value,
                "normalized_pts_sec": normalized_pts,
                "expected_cfr_sec": expected,
                "pts_abs_error_sec": abs(normalized_pts - expected) if normalized_pts is not None else None,
            })
        expected_fps = float(selected_meta[(video_id, selected[0])]["source_fps"])
        tolerance = 1.0 / expected_fps + 1e-6
        video_ok = (
            width == int(rows[0]["source_width"])
            and height == int(rows[0]["source_height"])
            and abs(fps - expected_fps) <= 1e-3
            and n_frames > selected[-1]
            and len(pts) > selected[-1]
            and all(item["sequential_decoded"] and item["random_seek_decoded"]
                    and item["mean_abs_pixel_difference"] == 0.0
                    and item["pts_abs_error_sec"] is not None
                    and item["pts_abs_error_sec"] <= tolerance for item in checks)
        )
        overall = overall and video_ok
        results.append({
            "video_id": video_id,
            "source_path": str(source),
            "source_sha256": sha256_file(source),
            "metadata": {"fps": fps, "expected_fps": expected_fps,
                         "n_frames": n_frames, "width": width, "height": height,
                         "pts_count": len(pts), "first_pts_sec": first_pts,
                         "pts_monotonic": all(b >= a for a, b in zip(pts, pts[1:]))},
            "selected_frame_count": len(selected),
            "selected_first_last": [selected[0], selected[-1]],
            "probe_checks": checks,
            "one_frame_tolerance_sec": tolerance,
            "gate_pass": video_ok,
        })
    report = {
        "schema": "aic6_p2d_identity_gate_v1",
        "status": "PASS_SOURCE_IDENTITY" if overall else "FAIL_SOURCE_IDENTITY",
        "gate_pass": overall,
        "requests_sha256": sha256_file(requests_path),
        "selected_frames_sha256": sha256_file(selected_path),
        "freeze_sha256": sha256_file(freeze_path),
        "videos": results,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "videos": len(results),
                      "output_sha256": sha256_file(output)}, indent=2))
    return 0 if overall else 3


if __name__ == "__main__":
    raise SystemExit(main())
