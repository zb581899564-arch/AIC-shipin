"""Freeze a source-disjoint weak-supervision candidate set (no model training)."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
LABELS = HERE / "train.source_copy.jsonl"
MAPPING = HERE.parent.parent / "orarl_round4" / "evidence" / "mapping_rows.jsonl"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def split_for(youtube_id: str) -> str:
    bucket = int(hashlib.sha256(youtube_id.encode()).hexdigest()[:8], 16) % 100
    return "train" if bucket < 70 else "dev" if bucket < 85 else "holdout"


def main():
    labels, mappings = load_jsonl(LABELS), load_jsonl(MAPPING)
    assert len(labels) == len(mappings) == 987
    records = []
    reject = Counter()
    groups = defaultdict(set)
    for i, (r, m) in enumerate(zip(labels, mappings)):
        if m["status"] != "usable":
            reject["mapping_" + m["status"]] += 1
            continue
        if not r["cropRois"]:
            reject["empty_spatial_labels"] += 1
            continue
        if len(r["segments"]) > 5:
            reject["over_five_temporal_segments"] += 1
            continue
        if not m.get("youtube_id") or not m.get("source_path"):
            reject["missing_source_identity"] += 1
            continue
        source_fps = float(m["source_probe"]["avg_fps"])
        clip_fps = float(m["clip_fps"])
        source_frames = [round((float(r["clip"]["start_sec"]) + f / clip_fps) * source_fps)
                         for f, _ in r["cropRois"]]
        if len(source_frames) != len(set(source_frames)):
            reject["noninjective_source_frame_mapping"] += 1
            continue
        if min(source_frames) < 0 or max(source_frames) >= int(m["source_probe"]["nb_frames"]):
            reject["source_frame_out_of_bounds"] += 1
            continue
        split = split_for(m["youtube_id"])
        groups[m["youtube_id"]].add(split)
        records.append({
            "row_index": i, "video_id": r["video_id"], "source_vid": m["source_vid"],
            "youtube_id": m["youtube_id"], "source_path": m["source_path"],
            "split": split, "original_dataset_split": r["dataset_split"],
            "clip_start_sec": r["clip"]["start_sec"], "clip_end_sec": r["clip"]["end_sec"],
            "clip_fps": clip_fps, "source_fps": source_fps,
            "source_width": m["source_probe"]["width"], "source_height": m["source_probe"]["height"],
            "n_segments": len(r["segments"]), "n_roi_frames": len(r["cropRois"]),
            "target_ratio_wh": r["targetRatioWH"],
            "label_type": "WEAK_TEACHER_ALIGNED_CANDIDATE",
            "provenance_seed_model": (r.get("provenance") or {}).get("seed_model"),
        })
    if any(len(v) != 1 for v in groups.values()):
        raise AssertionError("source-group leakage")
    split_rows = Counter(x["split"] for x in records)
    split_groups = Counter(next(iter(v)) for v in groups.values())
    if split_rows["train"] < 200 or split_rows["dev"] < 50 or split_rows["holdout"] < 50:
        raise AssertionError(f"too few rows in one or more splits: {split_rows}")
    (HERE / "weak_split_manifest.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    summary = {
        "status": "FROZEN_WEAK_CANDIDATE_NOT_TRAINED",
        "label_sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest(),
        "mapping_sha256": hashlib.sha256(MAPPING.read_bytes()).hexdigest(),
        "split_rule": "sha256(youtube_id) first 32 bits modulo 100: <70 train, 70-84 dev, 85-99 holdout",
        "inclusion": "usable exact-stem source mapping, nonempty ROI, <=5 segments, in-bounds injective source-frame map",
        "source_frame_rule": "round((clip.start_sec + clip_local_frame/clip_fps) * source_fps); provisional, not exact short-video reproduction",
        "split_rows": dict(split_rows), "split_source_groups": dict(split_groups),
        "rejection_counts": dict(reject),
        "records": len(records), "source_groups": len(groups),
        "label_semantics": "Seed-model weak temporal/spatial labels, all target ratio 9:16; no official or human ground truth claim",
        "holdout_limit": "New split is group-disjoint within this candidate, but prior project experiments used overlapping source labels; not a previously untouched blind benchmark",
    }
    (HERE / "weak_split_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
