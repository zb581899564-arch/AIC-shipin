"""Compose all 174 official test rows from frozen P2-J anchors and interpolation."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from p2j_core import (box_is_legal, canonical_ratio, group_shots, interpolate_box,
                      read_jsonl, sha256_file, write_jsonl)


def metadata_ratio(value) -> list[int]:
    values = value if isinstance(value, list) else str(value).split()
    if len(values) != 2 or any(isinstance(x, bool) for x in values):
        raise ValueError("invalid targetRatioWH metadata")
    return [int(x) for x in values]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--shots", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--anchor-output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--max-gap", type=int, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if any(x.exists() for x in (args.predictions, args.provenance, args.report)):
        raise FileExistsError("refusing to overwrite candidate artifacts")
    selected, shots = read_jsonl(args.selected), read_jsonl(args.shots)
    anchor_requests, anchor_outputs = read_jsonl(args.anchors), read_jsonl(args.anchor_output)
    metadata_rows = json.loads(args.metadata.read_text(encoding="utf-8"))["records"]
    metadata = {str(x["video_id"]): x for x in metadata_rows}
    if len(metadata) != 174:
        raise ValueError("expected 174 metadata rows")
    selected_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in selected}
    request_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in anchor_requests}
    output_by_key = {(str(x["video_id"]), int(x["source_frame"])): x for x in anchor_outputs}
    if len(selected_by_key) != len(selected) or len(request_by_key) != len(anchor_requests):
        raise ValueError("duplicate selected or anchor request")
    if set(request_by_key) != set(output_by_key):
        raise ValueError("anchor output key mismatch")
    if any(x.get("status") != "MODEL_OK" or x.get("used_fallback") for x in anchor_outputs):
        raise ValueError("invalid anchor output; fail closed")
    provenance, violations = [], []
    composed = defaultdict(list)
    grouped = group_shots(shots)
    for shot_id, shot in enumerate(grouped):
        video_id = str(shot[0]["video_id"])
        frames = [int(x["source_frame"]) for x in shot]
        anchor_boxes = {frame: output_by_key[(video_id, frame)]["box_xyw"]
                        for frame in frames if (video_id, frame) in output_by_key}
        if not anchor_boxes or min(anchor_boxes) != frames[0] or max(anchor_boxes) != frames[-1]:
            raise ValueError("shot is not endpoint-bracketed")
        if any(b - a > args.max_gap for a, b in zip(sorted(anchor_boxes), sorted(anchor_boxes)[1:])):
            raise ValueError("anchor gap exceeds frozen maximum")
        for frame in frames:
            box, source = interpolate_box(frame, anchor_boxes)
            request = selected_by_key[(video_id, frame)]
            tw, th = request["target_ratio_wh"]
            legal = box_is_legal(box, int(request["source_width"]), int(request["source_height"]),
                                 float(tw), float(th))
            if not legal:
                violations.append({"video_id": video_id, "frame": frame,
                                   "reason": "ILLEGAL_INTERPOLATED_BOX"})
            provenance.append({"video_id": video_id, "source_frame": frame,
                               "shot_id": shot_id, "box_xyw": box, "legal": legal, **source})
            composed[video_id].append({"frame": frame, "bboxes": box})
    write_jsonl(args.provenance, provenance)
    prediction_rows = []
    for vid in sorted(metadata, key=int):
        ratio = canonical_ratio(metadata_ratio(metadata[vid]["targetRatioWH"]))
        prediction_rows.append({"video_id": vid, "targetRatioWH": ratio,
                                "predictions": sorted(composed.get(vid, []), key=lambda x: x["frame"])})
    write_jsonl(args.predictions, prediction_rows)
    expected = set(selected_by_key)
    actual = {(vid, int(x["frame"])) for vid, items in composed.items() for x in items}
    report = {
        "status": "PASS_TEST_ENGINEERING" if not violations and actual == expected else "FAIL_TEST_ENGINEERING",
        "official_status": "NOT_SCORED_NOT_UPLOADED", "videos": 174,
        "videos_with_empty_predictions": sum(not x["predictions"] for x in prediction_rows),
        "selected_frames": len(expected), "composed_frames": len(actual),
        "anchor_calls": len(anchor_outputs), "shots": len(grouped),
        "call_reduction": 1 - len(anchor_outputs) / len(expected),
        "missing": len(expected - actual), "extra": len(actual - expected),
        "illegal": len(violations), "cross_shot_reuse": 0, "silent_fallbacks": 0,
        "weak_roi_inputs_used": 0, "old_test_boxes_used": 0,
        "source_counts": {
            "QWEN_ANCHOR_SAME_FRAME": sum(x["spatial_source"] == "QWEN_ANCHOR_SAME_FRAME" for x in provenance),
            "SHOT_LINEAR_INTERPOLATION": sum(x["spatial_source"] == "SHOT_LINEAR_INTERPOLATION" for x in provenance),
        },
        "selected_sha256": sha256_file(args.selected), "shots_sha256": sha256_file(args.shots),
        "anchors_sha256": sha256_file(args.anchors),
        "anchor_output_sha256": sha256_file(args.anchor_output),
        "metadata_sha256": sha256_file(args.metadata),
        "predictions_sha256": sha256_file(args.predictions),
        "provenance_sha256": sha256_file(args.provenance), "violations": violations,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"].startswith("PASS") else 6


if __name__ == "__main__":
    raise SystemExit(main())
