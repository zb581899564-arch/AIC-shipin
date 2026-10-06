from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    labels_path = args.root / "reports/round6_score_alignment/training_alignment_20260917/train.source_copy.jsonl"
    mapping_path = args.root / "reports/orarl_round4/evidence/mapping_rows.jsonl"
    weak_path = args.root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl"
    structural_path = args.root / "reports/round6_score_alignment/training_alignment_20260917/structural_audit.json"
    pilot_path = args.root / "round6_score_alignment/p1b/pilot_manifest.json"
    mappings = [json.loads(x) for x in mapping_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    weak = [json.loads(x) for x in weak_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    structural = json.loads(structural_path.read_text(encoding="utf-8"))
    holdout_indices = {int(r["row_index"]) for r in weak if r.get("split") == "holdout"}
    label_lines = [x for x in labels_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    usable_roi = []
    interp_total = interp_1px = keyframe_hits = unbracketed = repeated_adjacent = 0
    source_groups = set()
    per_row = []
    for idx, (label_line, mapping) in enumerate(zip(label_lines, mappings)):
        if idx in holdout_indices:
            continue
        label = json.loads(label_line)
        rois = label.get("cropRois") or []
        if mapping.get("status") != "usable" or not rois:
            continue
        usable_roi.append(idx)
        source_groups.add(mapping.get("youtube_id"))
        keyframes = sorted(label.get("crop_keyframes") or [], key=lambda x: int(x["frame"]))
        kframes = [int(k["frame"]) for k in keyframes]
        kpos = [float(k["free_axis_position_px"]) for k in keyframes]
        kset = set(kframes)
        row_interp = row_total = row_repeats = 0
        prev_box = None
        for frame, box in rois:
            frame = int(frame); x, y, w, h = map(float, box)
            if prev_box == tuple(box):
                repeated_adjacent += 1; row_repeats += 1
            prev_box = tuple(box)
            if frame in kset:
                keyframe_hits += 1
            j = bisect.bisect_right(kframes, frame)
            if j == 0 or j == len(kframes):
                unbracketed += 1
                continue
            f0, f1 = kframes[j - 1], kframes[j]
            p0, p1 = kpos[j - 1], kpos[j]
            expected = p0 + (p1 - p0) * (frame - f0) / (f1 - f0)
            # The label field is the crop's top-left coordinate on the free axis,
            # not the crop centre. Keep the comparison in that native convention.
            observed = x if label.get("clip", {}).get("free_axis") == "x" else y
            interp_total += 1; row_total += 1
            if abs(observed - expected) <= 1.01:
                interp_1px += 1; row_interp += 1
        per_row.append({"row_index": idx, "roi_count": len(rois), "keyframe_count": len(keyframes), "bracketed_roi_count": row_total, "linear_interp_within_1px": row_interp, "adjacent_exact_repeats": row_repeats})
    ratios = collections.Counter(tuple(x.get("target_ratio_wh", [])) for x in weak)
    pilot_rows = pilot.get("samples", [])
    inventory = {
        "schema": "p2r_existing_evidence_inventory_v1",
        "input_hashes": {str(p.relative_to(args.root)): sha256(p) for p in [labels_path, mapping_path, weak_path, structural_path, pilot_path]},
        "official_training": {
            "published_aggregate_rows": structural["counts"]["rows"],
            "published_aggregate_usable_rows_with_roi": structural["counts"]["status_usable_with_rois"],
            "published_aggregate_crop_keyframe_entries_all": structural["counts"]["crop_keyframe_entries"],
            "published_aggregate_crop_roi_entries_all": structural["counts"]["roi_entries"],
            "published_aggregate_usable_keyframe_entries": structural["counts"]["usable_crop_keyframe_entries"],
            "recomputed_scope": "all non-holdout rows only; weak holdout row payloads excluded before JSON parsing",
            "excluded_holdout_row_indices_count": len(holdout_indices),
            "recomputed_non_holdout_usable_rows_with_roi": len(usable_roi),
            "recomputed_non_holdout_usable_roi_source_groups": len(source_groups),
            "recomputed_non_holdout_roi_entries": sum(x["roi_count"] for x in per_row),
            "recomputed_non_holdout_keyframe_entries": sum(x["keyframe_count"] for x in per_row),
            "usable_rows_with_roi": len(usable_roi),
            "usable_roi_entries": sum(x["roi_count"] for x in per_row),
            "usable_keyframe_entries": sum(x["keyframe_count"] for x in per_row),
            "roi_frames_equal_keyframe_index": keyframe_hits,
            "bracketed_roi_frames": interp_total,
            "bracketed_roi_frames_linear_within_1px": interp_1px,
            "linear_consistency_rate": interp_1px / interp_total if interp_total else None,
            "unbracketed_roi_frames": unbracketed,
            "adjacent_exact_box_repeats": repeated_adjacent,
            "provenance_seed_models": ["api_doubao_doubao-seed-2-1-pro-260628"],
            "spatial_fps_values": [1.0],
            "annotator_identity": "MODEL_TEACHER",
            "human_reviewer": "UNKNOWN",
            "evidence_tier": "TIER_W_WEAK_TEACHER",
            "inference": "The per-frame ROI sequence is highly consistent with interpolation of 1 Hz model keyframes; consistency is structural evidence, not proof of the unpublished generator implementation.",
        },
        "frozen_weak_split": {"rows": len(weak), "ratios": {str(k): v for k, v in ratios.items()}, "holdout_rows_excluded_from_final_recomputation": len(holdout_indices), "boundary_note": "An initial superseded audit parsed these labels structurally; see boundary_incident.json."},
        "p1b": {
            "rows": len(pilot_rows),
            "ratios": dict(collections.Counter("%s:%s" % tuple(r["target_ratio_wh"]) for r in pilot_rows)),
            "annotation_statuses": dict(collections.Counter(r.get("annotation_status") for r in pilot_rows)),
            "annotator": "NONE", "reviewer": "NONE", "evidence_tier": "NOT_ELIGIBLE_REFERENCE_UNANNOTATED",
        },
        "per_row_interpolation_summary": per_row,
    }
    args.out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
