"""Freeze anchor requests from decoded shot analysis."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from p2j_core import anchor_frames, group_shots, read_jsonl, sha256_file, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--shots", type=Path, required=True)
    parser.add_argument("--max-gap", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite anchor artifacts")
    selected = read_jsonl(args.selected)
    shots = read_jsonl(args.shots)
    selected_by_key = {(r["video_id"], int(r["source_frame"])): r for r in selected}
    if len(selected_by_key) != len(selected):
        raise ValueError("duplicate selected frames")
    shot_keys = {(r["video_id"], int(r["source_frame"])) for r in shots}
    if shot_keys != set(selected_by_key):
        raise ValueError("shot analysis does not cover the exact selected set")
    anchor_keys = set()
    grouped = group_shots(shots)
    for shot in grouped:
        video_id = shot[0]["video_id"]
        for frame in anchor_frames([int(r["source_frame"]) for r in shot], args.max_gap):
            anchor_keys.add((video_id, frame))
    shot_by_key = {(r["video_id"], int(r["source_frame"])): r for r in shots}
    rows = []
    for key in sorted(anchor_keys):
        source = dict(selected_by_key[key])
        source["kind"] = "QWEN_ANCHOR_SAME_FRAME"
        source["expected_pixel_sha256"] = shot_by_key[key]["decoded_pixel_sha256"]
        canonical = json.dumps({k: source[k] for k in sorted(source) if k != "anchor_request_sha256"},
                               ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        source["anchor_request_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        rows.append(source)
    write_jsonl(args.output, rows)
    report = {
        "status": "ANCHORS_FROZEN", "max_gap_frames": args.max_gap,
        "selected_sha256": sha256_file(args.selected), "shots_sha256": sha256_file(args.shots),
        "output_sha256": sha256_file(args.output), "selected_frames": len(selected),
        "shots": len(grouped), "anchor_calls": len(rows),
        "call_reduction": 1.0 - len(rows) / len(selected),
    }
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
