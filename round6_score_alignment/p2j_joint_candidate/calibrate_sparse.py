"""Measure fixed sparse interpolation against frozen per-frame P2-D Qwen output."""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from p2j_core import (anchor_frames, box_is_legal, group_shots, interpolate_box,
                      read_jsonl, sha256_file, xyw_iou)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--full-qwen", type=Path, required=True)
    parser.add_argument("--shots", type=Path, required=True)
    parser.add_argument("--max-gap", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite calibration")
    selected = read_jsonl(args.selected)
    outputs = read_jsonl(args.full_qwen)
    shots = read_jsonl(args.shots)
    meta = {(r["video_id"], int(r["source_frame"])): r for r in selected}
    boxes = {(r["video_id"], int(r["source_frame"])): r["box_xyw"] for r in outputs}
    if len(meta) != len(selected) or set(meta) != set(boxes):
        raise ValueError("frozen Qwen output does not exactly cover selected frames")
    groups = group_shots(shots)
    per_frame = []
    anchor_count = 0
    for shot_id, shot in enumerate(groups):
        video_id = shot[0]["video_id"]
        frames = [int(r["source_frame"]) for r in shot]
        anchor_ids = anchor_frames(frames, args.max_gap)
        anchor_count += len(anchor_ids)
        anchor_boxes = {f: boxes[(video_id, f)] for f in anchor_ids}
        for frame in frames:
            box, provenance = interpolate_box(frame, anchor_boxes)
            request = meta[(video_id, frame)]
            tw, th = request["target_ratio_wh"]
            legal = box_is_legal(box, int(request["source_width"]), int(request["source_height"]),
                                 float(tw), float(th))
            per_frame.append({
                "video_id": video_id, "source_frame": frame, "shot_id": shot_id,
                "iou_to_full_qwen": xyw_iou(box, boxes[(video_id, frame)], tw, th),
                "box_legal": legal, **provenance,
            })
    by_video = defaultdict(list)
    for row in per_frame:
        by_video[row["video_id"]].append(row["iou_to_full_qwen"])
    group_values = [statistics.mean(v) for v in by_video.values()]
    report = {
        "status": "PASS_SPARSE_FIDELITY_GATE" if (
            all(r["box_legal"] for r in per_frame)
            and 1 - anchor_count / len(per_frame) >= 0.80
            and statistics.mean(group_values) >= 0.90) else "FAIL_SPARSE_FIDELITY_GATE",
        "metric_status": "ENGINEERING_FIDELITY_TO_FULL_QWEN_NOT_GROUND_TRUTH",
        "max_gap_frames": args.max_gap,
        "selected_sha256": sha256_file(args.selected),
        "full_qwen_sha256": sha256_file(args.full_qwen),
        "shots_sha256": sha256_file(args.shots),
        "frames": len(per_frame), "videos": len(by_video), "shots": len(groups),
        "anchor_calls": anchor_count, "call_reduction": 1 - anchor_count / len(per_frame),
        "frame_mean_iou": statistics.mean(r["iou_to_full_qwen"] for r in per_frame),
        "frame_median_iou": statistics.median(r["iou_to_full_qwen"] for r in per_frame),
        "group_macro_iou": statistics.mean(group_values), "minimum_group_iou": min(group_values),
        "frames_below_0_5": sum(r["iou_to_full_qwen"] < 0.5 for r in per_frame),
        "legal_rate": statistics.mean(r["box_legal"] for r in per_frame),
        "per_video": {k: {"frames": len(v), "mean_iou": statistics.mean(v),
                           "minimum_iou": min(v)} for k, v in sorted(by_video.items())},
        "per_frame": per_frame,
        "gates": {"call_reduction_at_least_0_80": 1 - anchor_count / len(per_frame) >= 0.80,
                  "group_macro_iou_at_least_0_90": statistics.mean(group_values) >= 0.90,
                  "all_interpolated_boxes_legal": all(r["box_legal"] for r in per_frame)},
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "frames", "shots", "anchor_calls",
                                              "call_reduction", "frame_mean_iou",
                                              "group_macro_iou", "minimum_group_iou")}, indent=2))
    return 0 if report["status"].startswith("PASS") else 4


if __name__ == "__main__":
    raise SystemExit(main())
