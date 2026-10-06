"""Weak temporal and endpoint diagnostics for the already-frozen P2-D slice."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from p2d_core import load_jsonl, sha256_file

ROOT = Path(__file__).resolve().parents[2]
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"
PINNED = {
    "dev_temporal.jsonl": "242a3a0475f6c5b66cd2a25deef88f3b477f3f6ea5f4d22984c1a12830d3bd3c",
    "temporal_S2.jsonl": "ca51e6d49e2394dcef28dc1b651e9803646ae8921a97e6f669632cc082e73903",
}


def duration(intervals):
    return sum(max(0.0, b - a) for a, b in intervals)


def intersection_duration(left, right):
    return sum(max(0.0, min(b1, b2) - max(a1, a2))
               for a1, b1 in left for a2, b2 in right)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    out = Path(args.evidence_dir).resolve()
    target = out / "temporal_slice_weak_diagnostic.json"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite {target}")
    for name, expected in PINNED.items():
        if sha256_file(WEAK / name) != expected:
            raise RuntimeError(f"protected input changed: {name}")
    freeze = json.loads((out / "freeze_manifest.json").read_text(encoding="utf-8"))
    chosen = {row["video_id"]: row for row in freeze["selected_videos"]}
    weak = {row["video_id"]: row for row in load_jsonl(WEAK / "dev_temporal.jsonl")}
    s2 = {row["video_id"]: row for row in load_jsonl(WEAK / "temporal_S2.jsonl")}
    rows = []
    for video_id in sorted(chosen):
        gt = [[float(a), float(b)] for a, b in weak[video_id]["weak_segments_clip_local"]]
        pred = [[float(a), float(b)] for a, b in s2[video_id]["parsed_segments"]]
        overlap = intersection_duration(pred, gt)
        pred_d, gt_d = duration(pred), duration(gt)
        precision = overlap / pred_d if pred_d else (1.0 if not gt_d else 0.0)
        recall = overlap / gt_d if gt_d else (1.0 if not pred_d else 0.0)
        f1 = 2 * overlap / (pred_d + gt_d) if pred_d + gt_d else 1.0
        endpoint = None
        if len(pred) == len(gt):
            errors = [abs(value - reference)
                      for pair, truth in zip(pred, gt)
                      for value, reference in zip(pair, truth)]
            endpoint = {
                "status": "ORDERED_PAIRING_SAME_SEGMENT_COUNT",
                "endpoint_count": len(errors),
                "mean_abs_error_sec": statistics.fmean(errors) if errors else 0.0,
                "max_abs_error_sec": max(errors, default=0.0),
            }
        else:
            endpoint = {"status": "NOT_COMPARABLE_SEGMENT_COUNT",
                        "predicted_segments": len(pred), "weak_segments": len(gt)}
        rows.append({
            "video_id": video_id,
            "youtube_id": chosen[video_id]["youtube_id"],
            "historical_s2_source_exposure": chosen[video_id]["historical_s2_source_exposure"],
            "predicted_segments": pred,
            "weak_segments": gt,
            "predicted_duration_sec": pred_d,
            "weak_duration_sec": gt_d,
            "intersection_sec": overlap,
            "weak_precision": precision,
            "weak_recall": recall,
            "weak_f1": f1,
            "endpoint_diagnostic": endpoint,
        })
    comparable = [row["endpoint_diagnostic"] for row in rows
                  if row["endpoint_diagnostic"]["status"] == "ORDERED_PAIRING_SAME_SEGMENT_COUNT"]
    report = {
        "schema": "aic6_p2d_temporal_slice_weak_diagnostic_v1",
        "status": "WEAK_DIAGNOSTIC_ONLY",
        "official_status": "NOT_OFFICIAL_SCORE",
        "videos": len(rows),
        "source_groups": len({row["youtube_id"] for row in rows}),
        "video_macro_weak_f1": statistics.fmean(row["weak_f1"] for row in rows),
        "zero_overlap_videos": sum(row["intersection_sec"] == 0 for row in rows),
        "same_segment_count_videos": len(comparable),
        "same_count_endpoint_mean_abs_error_sec": (
            statistics.fmean(row["mean_abs_error_sec"] for row in comparable)
            if comparable else None),
        "same_count_endpoint_max_abs_error_sec": max(
            (row["max_abs_error_sec"] for row in comparable), default=None),
        "interpretation": "Weak teacher intervals only; endpoint pairing is reported only when segment counts match and is not official truth.",
        "per_video": rows,
        "protected_input_hashes": PINNED,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "videos", "video_macro_weak_f1", "zero_overlap_videos",
        "same_segment_count_videos", "same_count_endpoint_mean_abs_error_sec",
        "same_count_endpoint_max_abs_error_sec")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
