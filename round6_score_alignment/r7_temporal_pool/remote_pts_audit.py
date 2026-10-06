#!/usr/bin/env python3
"""CPU-only full-source PTS audit for R7 temporal candidates."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import time
from collections import defaultdict
from pathlib import Path

from r7_core import audit_pts_sequence


VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def locate_ffprobe() -> str:
    candidates = [
        "/home/inspur/anaconda3/envs/Andy/bin/ffprobe",
        "/usr/local/bin/ffprobe",
        "/usr/bin/ffprobe",
        shutil.which("ffprobe"),
    ]
    for item in candidates:
        if item and Path(item).is_file():
            return item
    raise RuntimeError("ffprobe not found")


def scan_source(ffprobe: str, path_text: str, avg_fps: float, timeout: int) -> dict:
    started = time.monotonic()
    try:
        path = Path(path_text).resolve(strict=True)
        if VIDEO_ROOT not in path.parents:
            raise ValueError("source outside training video root")
        process = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_frames",
             "-show_entries", "frame=best_effort_timestamp_time", "-of", "csv=p=0",
             str(path)], capture_output=True, text=True, timeout=timeout, check=True)
        pts: list[float] = []
        for line in process.stdout.splitlines():
            token = line.strip().split(",")[0]
            if token and token != "N/A":
                pts.append(float(token))
        result = audit_pts_sequence(pts, float(avg_fps))
        result.update(source_path=str(path), source_stem=path.stem,
                      wall_seconds=round(time.monotonic() - started, 3))
        return result
    except Exception as exc:
        return {"passed": False, "reason": f"{type(exc).__name__}:{exc}",
                "source_path": path_text,
                "wall_seconds": round(time.monotonic() - started, 3)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=240)
    args = ap.parse_args()
    if not 1 <= args.workers <= 4:
        raise ValueError("workers must be in [1,4]")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows_out = args.out_dir / "pts_audit.jsonl"
    report_out = args.out_dir / "pts_audit_report.json"
    if rows_out.exists() or report_out.exists():
        raise RuntimeError("refusing to overwrite PTS audit outputs")

    candidates = read_jsonl(args.manifest)
    if not candidates or len({r["row_index"] for r in candidates}) != len(candidates):
        raise ValueError("empty or duplicate candidate manifest")
    by_source: dict[str, list[dict]] = defaultdict(list)
    for row in candidates:
        by_source[row["source_path"]].append(row)
    ffprobe = locate_ffprobe()
    source_results: dict[str, dict] = {}
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(scan_source, ffprobe, path, group[0]["source_avg_fps"],
                        args.timeout): path
            for path, group in by_source.items()
        }
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            path = futures[future]
            source_results[path] = future.result()
            completed += 1
            if completed % 25 == 0 or completed == len(futures):
                print(json.dumps({"completed_sources": completed,
                                  "total_sources": len(futures)}), flush=True)

    audited = []
    for row in candidates:
        source = source_results[row["source_path"]]
        reasons: list[str] = []
        if not source.get("passed"):
            reasons.append(f"source_pts:{source.get('reason')}")
        if source.get("source_stem") and source["source_stem"] != row["source_vid"]:
            reasons.append("source_stem_mismatch")
        interval = source.get("median_frame_interval_sec")
        decoded_duration = source.get("decoded_duration_sec")
        if decoded_duration is None or interval is None:
            reasons.append("decoded_duration_unavailable")
        else:
            if row["clip_start_sec"] < -1e-9:
                reasons.append("clip_start_negative")
            if row["clip_end_sec"] > decoded_duration + interval + 1e-9:
                reasons.append("clip_end_exceeds_decoded_source")
        passed = not reasons
        out = dict(row)
        out.update({
            "pts_audit_status": "PASS" if passed else "FAIL",
            "pts_audit_reasons": reasons,
            "pts_max_residual_sec": source.get("max_index_pts_residual_sec"),
            "pts_frame_interval_sec": interval,
            "decoded_source_frames": source.get("decoded_frames"),
            "decoded_source_duration_sec": decoded_duration,
            "temporal_mapping_status": (
                "TEMPORAL_SECONDS_USABLE" if passed else "TEMPORAL_REJECTED"),
            "spatial_mapping_status": row["mapping_status"],
        })
        audited.append(out)

    with rows_out.open("x", encoding="utf-8") as stream:
        for row in audited:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    passed_rows = [r for r in audited if r["pts_audit_status"] == "PASS"]
    report = {
        "status": "PTS_AUDIT_COMPLETED",
        "manifest_sha256": sha256(args.manifest),
        "candidate_rows": len(candidates),
        "candidate_groups": len({r["youtube_id"] for r in candidates}),
        "unique_source_files": len(by_source),
        "passed_source_files": sum(r.get("passed", False) for r in source_results.values()),
        "failed_source_files": sum(not r.get("passed", False) for r in source_results.values()),
        "passed_rows": len(passed_rows),
        "failed_rows": len(audited) - len(passed_rows),
        "passed_groups": len({r["youtube_id"] for r in passed_rows}),
        "passed_time_uncertain_rows": sum(
            r["mapping_status"] == "time_uncertain" for r in passed_rows),
        "ffprobe": ffprobe,
        "workers": args.workers,
        "wall_seconds": round(time.monotonic() - started, 3),
        "output_sha256": sha256(rows_out),
        "source_failures": [r for r in source_results.values() if not r.get("passed")],
    }
    report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
