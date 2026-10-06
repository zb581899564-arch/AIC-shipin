"""Three-arm source-group temporal diagnostics for frozen R7 manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from r7_core import SEED, bootstrap_ci, temporal_stats


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def group_summary(per_video: list[dict], arm: str) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in per_video:
        grouped[row["youtube_id"]].append(row)
    out = []
    for group, rows in sorted(grouped.items()):
        out.append({
            "youtube_id": group,
            "videos": len(rows),
            "f1": statistics.mean(r[arm]["f1"] for r in rows),
            "precision": statistics.mean(r[arm]["precision"] for r in rows),
            "recall": statistics.mean(r[arm]["recall"] for r in rows),
            "valid_rate": statistics.mean(r[arm]["valid"] for r in rows),
            "zero_overlap_rate": statistics.mean(r[arm]["zero_overlap"] for r in rows),
        })
    return out


def arm_summary(per_video: list[dict], arm: str) -> dict:
    groups = group_summary(per_video, arm)
    return {
        "videos": len(per_video),
        "source_groups": len(groups),
        "group_macro_f1": statistics.mean(g["f1"] for g in groups),
        "group_macro_precision": statistics.mean(g["precision"] for g in groups),
        "group_macro_recall": statistics.mean(g["recall"] for g in groups),
        "valid_rate": statistics.mean(r[arm]["valid"] for r in per_video),
        "zero_overlap_videos": sum(r[arm]["zero_overlap"] for r in per_video),
        "pred_duration_ratio_median": statistics.median(
            r[arm]["duration_ratio"] for r in per_video
            if r[arm]["duration_ratio"] is not None),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--p2t2", type=Path, required=True)
    ap.add_argument("--r7", type=Path, required=True)
    ap.add_argument("--stage", choices=("dev", "confirm"), required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise RuntimeError("refusing to overwrite diagnostics")
    labels = read_jsonl(args.manifest)
    label_by_id = {r["video_id"]: r for r in labels}
    if len(label_by_id) != len(labels):
        raise ValueError("duplicate manifest video_id")
    arm_paths = {"BASE": args.base, "P2T2": args.p2t2, "R7": args.r7}
    arms = {}
    for name, path in arm_paths.items():
        records = read_jsonl(path)
        by_id = {r["video_id"]: r for r in records}
        if len(by_id) != len(records) or set(by_id) != set(label_by_id):
            raise ValueError(f"{name} identity mismatch")
        if any(r.get("arm") != name for r in records):
            raise ValueError(f"{name} arm marker mismatch")
        arms[name] = by_id

    per_video = []
    for video_id, label in label_by_id.items():
        rec = {
            "video_id": video_id,
            "youtube_id": label["youtube_id"],
            "mapping_status": label["mapping_status"],
            "clip_duration_sec": label["clip_duration_sec"],
            "truth_segment_count": label["n_segments"],
            "truth_segments": label["segments_clip_local"],
        }
        for name, records in arms.items():
            output = records[video_id]
            valid = bool(output.get("output_valid"))
            pred = output.get("parsed_segments") if valid else []
            rec[name] = {**temporal_stats(pred or [], label["segments_clip_local"]),
                         "valid": valid,
                         "parse_errors": output.get("parse_errors") or []}
        per_video.append(rec)

    per_arm = {name: arm_summary(per_video, name) for name in arms}
    groups_by_arm = {name: {g["youtube_id"]: g for g in group_summary(per_video, name)}
                     for name in arms}
    group_ids = sorted(groups_by_arm["R7"])
    differences = [groups_by_arm["R7"][g]["f1"] - groups_by_arm["P2T2"][g]["f1"]
                   for g in group_ids]
    paired = {"R7_minus_P2T2": {
        "mean": statistics.mean(differences),
        "ci95": bootstrap_ci(differences, 10000, SEED),
        "source_groups": len(differences), "draws": 10000, "seed": SEED}}

    slice_filters = {
        "multiple_segments": lambda r: r["truth_segment_count"] > 1,
        "duration_gt20": lambda r: r["clip_duration_sec"] > 20,
        "mapping_usable": lambda r: r["mapping_status"] == "usable",
        "mapping_time_uncertain": lambda r: r["mapping_status"] == "time_uncertain",
    }
    slices, slice_gates = {}, {}
    for name, predicate in slice_filters.items():
        selected = [r for r in per_video if predicate(r)]
        groups = len({r["youtube_id"] for r in selected})
        summaries = ({arm: arm_summary(selected, arm) for arm in arms}
                     if selected else {arm: None for arm in arms})
        slices[name] = {"videos": len(selected), "source_groups": groups,
                        "per_arm": summaries}
        required = name in {"multiple_segments", "duration_gt20"} and groups >= 10
        delta = (None if not selected else
                 summaries["R7"]["group_macro_f1"] -
                 summaries["P2T2"]["group_macro_f1"])
        slice_gates[name] = {
            "required": required,
            "delta_r7_minus_p2t2": delta,
            "passed": (True if not required else delta >= -0.03),
        }

    output = {
        "status": "MODEL_UNSEEN_FIXED_WEAK_DIAGNOSTIC_NOT_OFFICIAL_SCORE",
        "stage": args.stage,
        "manifest_sha256": sha256(args.manifest),
        "prediction_hashes": {name: sha256(path) for name, path in arm_paths.items()},
        "videos": len(per_video),
        "source_groups": len(group_ids),
        "per_arm": per_arm,
        "paired": paired,
        "slices": slices,
        "slice_gates": slice_gates,
        "per_video": per_video,
        "per_source_group": {
            name: [groups_by_arm[name][g] for g in group_ids] for name in arms},
    }
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({k: output[k] for k in
                      ("status", "stage", "videos", "source_groups", "per_arm", "paired",
                       "slice_gates")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
