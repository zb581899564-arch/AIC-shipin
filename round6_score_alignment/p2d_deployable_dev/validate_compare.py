"""Strict validation, paired center arm, and sparse weak diagnostics for P2-D."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from p2d_core import (center_max_crop, load_jsonl, sha256_file, validate_outputs,
                      write_jsonl, xywh_iou)


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    out = Path(args.evidence_dir).resolve()
    requests = load_jsonl(out / "inference_requests.jsonl")
    selected = load_jsonl(out / "selected_frames.jsonl")
    outputs = load_jsonl(out / "raw_inference.jsonl")
    run = json.loads((out / "raw_inference.run.json").read_text(encoding="utf-8"))
    validation = validate_outputs(requests, outputs)
    output_by_key = {(row["video_id"], int(row["source_frame"])): row for row in outputs}

    center_started = time.monotonic()
    center_rows = []
    qwen_rows = []
    frame_status = []
    weak_matches = []
    center_by_video, qwen_by_video = {}, {}
    for request in requests:
        key = (request["video_id"], int(request["source_frame"]))
        tw, th = request["target_ratio_wh"]
        center = center_max_crop(int(request["source_width"]), int(request["source_height"]),
                                 float(tw), float(th))
        center_by_video.setdefault(request["video_id"], []).append({
            "frame": int(request["source_frame"]), "bboxes": center,
            "source": "CENTER_MAX_LEGAL"})
        qwen = output_by_key.get(key)
        if qwen and qwen.get("status") == "MODEL_OK":
            qwen_by_video.setdefault(request["video_id"], []).append({
                "frame": int(request["source_frame"]), "bboxes": qwen["box_xyw"],
                "source": "REAL_QWEN_SAME_FRAME"})
        frame_status.append({
            "video_id": key[0], "source_frame": key[1],
            "qwen_status": qwen.get("status") if qwen else "MISSING_OUTPUT",
            "qwen_box_xyw": qwen.get("box_xyw") if qwen else None,
            "center_box_xyw": center,
            "qwen_seconds": qwen.get("seconds") if qwen else None,
            "qwen_spatial_source": qwen.get("spatial_source") if qwen else None,
            "qwen_used_fallback": qwen.get("used_fallback") if qwen else None,
        })
    center_seconds = time.monotonic() - center_started
    for row in selected:
        if row.get("weak_roi_xywh") is None:
            continue
        key = (row["video_id"], int(row["source_frame"]))
        qwen = output_by_key.get(key)
        center = center_max_crop(int(row["source_width"]), int(row["source_height"]), 9, 16)
        weak_matches.append({
            "video_id": row["video_id"], "youtube_id": row["youtube_id"],
            "source_frame": int(row["source_frame"]),
            "weak_roi_xywh": row["weak_roi_xywh"],
            "weak_status": "WEAK_TEACHER_NOT_GROUND_TRUTH",
            "qwen_status": qwen.get("status") if qwen else "MISSING_OUTPUT",
            "qwen_box_xyw": qwen.get("box_xyw") if qwen else None,
            "center_box_xyw": center,
            "qwen_weak_iou": xywh_iou(qwen.get("box_xyw") if qwen else None,
                                      row["weak_roi_xywh"]),
            "center_weak_iou": xywh_iou(center, row["weak_roi_xywh"]),
        })

    video_order = []
    for row in requests:
        if row["video_id"] not in video_order:
            video_order.append(row["video_id"])
    for video_id in video_order:
        center_rows.append({"video_id": video_id, "targetRatioWH": [9, 16],
                            "predictions": center_by_video.get(video_id, [])})
        qwen_rows.append({"video_id": video_id, "targetRatioWH": [9, 16],
                          "predictions": qwen_by_video.get(video_id, [])})
    write_jsonl(out / "frame_status.jsonl", frame_status)
    write_jsonl(out / "center_composed_dev.jsonl", center_rows)
    write_jsonl(out / "qwen_composed_dev.jsonl", qwen_rows)
    write_jsonl(out / "weak_matches.jsonl", weak_matches)

    per_video = []
    for video_id in video_order:
        requested = [row for row in requests if row["video_id"] == video_id]
        qrows = [row for row in outputs if row["video_id"] == video_id]
        matches = [row for row in weak_matches if row["video_id"] == video_id]
        per_video.append({
            "video_id": video_id,
            "selected_frames": len(requested),
            "qwen_legal_frames": sum(row.get("status") == "MODEL_OK" for row in qrows),
            "qwen_failures": sum(row.get("status") != "MODEL_OK" for row in qrows),
            "qwen_seconds_sum": sum(float(row.get("seconds", 0)) for row in qrows),
            "qwen_peak_memory_mib": max((float(row.get("peak_memory_mib", 0)) for row in qrows), default=0),
            "center_legal_frames": len(requested),
            "weak_match_frames": len(matches),
            "qwen_weak_iou_mean": mean([row["qwen_weak_iou"] for row in matches]),
            "center_weak_iou_mean": mean([row["center_weak_iou"] for row in matches]),
        })
    by_group = {}
    for row in weak_matches:
        by_group.setdefault(row["youtube_id"], []).append(row)
    group_qwen = [mean([row["qwen_weak_iou"] for row in rows]) for rows in by_group.values()]
    group_center = [mean([row["center_weak_iou"] for row in rows]) for rows in by_group.values()]
    report = {
        "schema": "aic6_p2d_validation_and_comparison_v1",
        "engineering_status": ("ENGINEERING_COMPLETE_DEV_SLICE"
                               if validation["deployable"] else "ENGINEERING_INCOMPLETE_DEV_SLICE"),
        "quality_status": "WEAK_DIAGNOSTIC_ONLY" if weak_matches else "QUALITY_NOT_COMPUTABLE",
        "official_status": "NOT_OFFICIAL_SCORE",
        "format_valid": validation["format_valid"],
        "selection_complete": validation["selection_complete"],
        "deployable": validation["deployable"],
        "validation": validation,
        "qwen_cost": {
            "model_wall_seconds_including_load": run["total_wall_seconds"],
            "model_load_seconds": run["model_load_seconds"],
            "per_frame_seconds_sum": sum(float(row.get("seconds", 0)) for row in outputs),
            "peak_memory_mib_model_reported": run["peak_memory_mib"],
            "rows": run["rows"],
        },
        "center_cost": {"model_inference": False, "cpu_generation_seconds": center_seconds,
                        "rows": len(requests)},
        "coverage": {"requested_frames": len(requests),
                     "qwen_legal_frames": validation["legal_deployable"],
                     "center_legal_frames": len(requests)},
        "weak_diagnostic": {
            "label_status": "WEAK_TEACHER_NOT_GROUND_TRUTH",
            "matched_frames": len(weak_matches),
            "matched_videos": len({row["video_id"] for row in weak_matches}),
            "matched_source_groups": len(by_group),
            "qwen_frame_mean_iou": mean([row["qwen_weak_iou"] for row in weak_matches]),
            "center_frame_mean_iou": mean([row["center_weak_iou"] for row in weak_matches]),
            "qwen_source_group_mean_iou": mean(group_qwen),
            "center_source_group_mean_iou": mean(group_center),
            "invalid_qwen_outputs_counted_as_zero": True,
            "no_bootstrap_due_to_sparse_slice": True,
        },
        "per_video": per_video,
        "artifacts": {},
    }
    for name in ("frame_status.jsonl", "center_composed_dev.jsonl",
                 "qwen_composed_dev.jsonl", "weak_matches.jsonl"):
        report["artifacts"][name] = sha256_file(out / name)
    report_path = out / "validation_comparison.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"engineering_status": report["engineering_status"],
                      "quality_status": report["quality_status"],
                      "requested": len(requests), "weak_matches": len(weak_matches),
                      "report_sha256": sha256_file(report_path)}, ensure_ascii=False, indent=2))
    return 0 if validation["deployable"] else 4


if __name__ == "__main__":
    raise SystemExit(main())

