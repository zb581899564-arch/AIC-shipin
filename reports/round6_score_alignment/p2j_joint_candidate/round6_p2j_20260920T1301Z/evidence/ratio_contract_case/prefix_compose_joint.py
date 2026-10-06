"""Compose all P2-T2-selected frames from frozen same-shot Qwen anchors."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from p2j_core import (box_is_legal, group_shots, interpolate_box, read_jsonl,
                      sha256_file, write_jsonl)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--shots", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--anchor-output", type=Path, required=True)
    parser.add_argument("--max-gap", type=int, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if any(p.exists() for p in (args.predictions, args.provenance, args.report)):
        raise FileExistsError("refusing to overwrite joint composition")
    selected, shots = read_jsonl(args.selected), read_jsonl(args.shots)
    anchor_requests, anchor_outputs = read_jsonl(args.anchors), read_jsonl(args.anchor_output)
    selected_by_key = {(r["video_id"], int(r["source_frame"])): r for r in selected}
    request_by_key = {(r["video_id"], int(r["source_frame"])): r for r in anchor_requests}
    output_by_key = {(r["video_id"], int(r["source_frame"])): r for r in anchor_outputs}
    if len(selected_by_key) != len(selected) or len(request_by_key) != len(anchor_requests):
        raise ValueError("duplicate selected or anchor request")
    if set(request_by_key) != set(output_by_key):
        raise ValueError("anchor output key mismatch")
    if any(r.get("status") != "MODEL_OK" or r.get("used_fallback")
           for r in anchor_outputs):
        raise ValueError("invalid anchor output; fail closed")
    provenance = []
    composed = defaultdict(list)
    violations = []
    grouped = group_shots(shots)
    for shot_id, shot in enumerate(grouped):
        video_id = shot[0]["video_id"]
        frames = [int(r["source_frame"]) for r in shot]
        anchor_boxes = {frame: output_by_key[(video_id, frame)]["box_xyw"]
                        for frame in frames if (video_id, frame) in output_by_key}
        if not anchor_boxes or min(anchor_boxes) != frames[0] or max(anchor_boxes) != frames[-1]:
            raise ValueError("shot is not endpoint-bracketed by anchors")
        if any(b - a > args.max_gap for a, b in zip(sorted(anchor_boxes), sorted(anchor_boxes)[1:])):
            raise ValueError("anchor gap exceeds frozen maximum")
        for frame in frames:
            box, source = interpolate_box(frame, anchor_boxes)
            request = selected_by_key[(video_id, frame)]
            tw, th = request["target_ratio_wh"]
            legal = box_is_legal(box, int(request["source_width"]), int(request["source_height"]),
                                 float(tw), float(th))
            if not legal:
                violations.append({"video_id": video_id, "source_frame": frame,
                                   "reason": "ILLEGAL_INTERPOLATED_BOX"})
            row = {"video_id": video_id, "source_frame": frame, "shot_id": shot_id,
                   "box_xyw": box, "legal": legal, **source}
            provenance.append(row)
            composed[video_id].append({"frame": frame, "bboxes": box,
                                       "source": source["spatial_source"]})
    write_jsonl(args.provenance, provenance)
    prediction_rows = [{"video_id": video_id, "targetRatioWH": [9, 16],
                        "predictions": sorted(items, key=lambda x: x["frame"])}
                       for video_id, items in sorted(composed.items())]
    write_jsonl(args.predictions, prediction_rows)
    expected = set(selected_by_key)
    actual = {(v, int(x["frame"])) for v, items in composed.items() for x in items}
    report = {
        "status": "PASS_JOINT_ENGINEERING" if not violations and actual == expected else "FAIL_JOINT_ENGINEERING",
        "official_status": "NOT_OFFICIAL_SCORE", "selected_sha256": sha256_file(args.selected),
        "shots_sha256": sha256_file(args.shots), "anchors_sha256": sha256_file(args.anchors),
        "anchor_output_sha256": sha256_file(args.anchor_output),
        "predictions_sha256": sha256_file(args.predictions),
        "provenance_sha256": sha256_file(args.provenance),
        "videos": len(composed), "selected_frames": len(expected), "composed_frames": len(actual),
        "anchor_calls": len(anchor_outputs), "call_reduction": 1 - len(anchor_outputs) / len(expected),
        "shots": len(grouped), "missing": len(expected - actual), "extra": len(actual - expected),
        "illegal": len(violations), "cross_shot_reuse": 0, "silent_fallbacks": 0,
        "weak_roi_inputs_used": 0, "old_test_boxes_used": 0,
        "source_counts": {name: sum(r["spatial_source"] == name for r in provenance)
                          for name in ("QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION")},
        "violations": violations,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"].startswith("PASS") else 6


if __name__ == "__main__":
    raise SystemExit(main())
