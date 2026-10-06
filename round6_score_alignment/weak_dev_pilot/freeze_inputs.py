"""Freeze training-only weak-label frames before any round-6 model output.

The script uses the already-audited 518-row source-disjoint split. It writes
derived manifests only; it never opens competition test media.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
ALIGN = WORKSPACE / "reports" / "round6_score_alignment" / "training_alignment_20260917"
MAPPING = WORKSPACE / "reports" / "orarl_round4" / "evidence" / "mapping_rows.jsonl"
OUT = WORKSPACE / "reports" / "round6_score_alignment" / "weak_dev_pilot"


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evenly_spaced_indices(n: int, cap: int = 4) -> list[int]:
    """Select endpoints and evenly spaced interior items, without replacement."""
    if n <= 0 or cap <= 0:
        return []
    if n <= cap:
        return list(range(n))
    return [round(i * (n - 1) / (cap - 1)) for i in range(cap)]


def eligible_keyframes(row: dict) -> list[int]:
    rois = {frame for frame, _ in row["cropRois"]}
    segments = row["segments"]
    found = {int(k["frame"]) for k in row["crop_keyframes"]
             if int(k["frame"]) in rois and
             any(s["start_frame"] <= int(k["frame"]) <= s["end_frame"] for s in segments)}
    return sorted(found)


def record_for(manifest_row: dict, row: dict, mapping: dict, frame: int) -> dict:
    if manifest_row["video_id"] != row["video_id"] or row["video_id"] != mapping["video_id"]:
        raise ValueError("video identity mismatch")
    if mapping["status"] != "usable" or not mapping.get("source_path"):
        raise ValueError("source mapping not usable")
    roi = dict(row["cropRois"])[frame]
    x, y, w, h = roi
    width, height = mapping["source_probe"]["width"], mapping["source_probe"]["height"]
    if not (0 <= x and 0 <= y and w > 0 and h > 0 and x + w <= width and y + h <= height):
        raise ValueError("ROI outside source frame")
    source_fps = float(mapping["source_probe"]["avg_fps"])
    local_fps = float(mapping["clip_fps"])
    source_time = float(row["clip"]["start_sec"]) + frame / local_fps
    source_frame = round(source_time * source_fps)
    if not 0 <= source_frame < int(mapping["source_probe"]["nb_frames"]):
        raise ValueError("mapped source frame outside video")
    return {
        "sample_key": f"{manifest_row['video_id']}#clip{frame}",
        "row_index": manifest_row["row_index"], "video_id": manifest_row["video_id"],
        "youtube_id": manifest_row["youtube_id"], "split": manifest_row["split"],
        "source_path": manifest_row["source_path"],
        "source_width": width, "source_height": height,
        "source_fps": source_fps, "clip_fps": local_fps,
        "clip_frame": frame, "source_frame": source_frame,
        "source_time_sec": source_time,
        "target_ratio_wh": row["targetRatioWH"],
        "weak_roi_xywh": roi,
        "label_status": "WEAK_TEACHER",
    }


def main():
    source_labels = ALIGN / "train.source_copy.jsonl"
    split_file = ALIGN / "weak_split_manifest.jsonl"
    summary = json.loads((ALIGN / "weak_split_summary.json").read_text(encoding="utf-8"))
    if sha256(source_labels) != summary["label_sha256"] or sha256(MAPPING) != summary["mapping_sha256"]:
        raise RuntimeError("frozen input hash mismatch")
    labels, mappings, split = read_jsonl(source_labels), read_jsonl(MAPPING), read_jsonl(split_file)
    if len(labels) != 987 or len(mappings) != 987 or len(split) != 518:
        raise RuntimeError("frozen input row count mismatch")
    all_groups = defaultdict(set)
    for item in split:
        all_groups[item["youtube_id"]].add(item["split"])
    if any(len(v) != 1 for v in all_groups.values()):
        raise RuntimeError("source group crosses splits")

    by_split = {name: [r for r in split if r["split"] == name]
                for name in ("train", "dev", "holdout")}
    if [len(by_split[n]) for n in ("train", "dev", "holdout")] != [372, 82, 64]:
        raise RuntimeError("split sizes changed")
    dev_frames = []
    temporal_dev = []
    for item in by_split["dev"]:
        idx = item["row_index"]
        row, mapping = labels[idx], mappings[idx]
        kfs = eligible_keyframes(row)
        if not kfs:
            raise RuntimeError(f"no eligible keyframe: {item['video_id']}")
        selected = [kfs[j] for j in evenly_spaced_indices(len(kfs))]
        dev_frames.extend(record_for(item, row, mapping, f) for f in selected)
        temporal_dev.append({
            "row_index": idx, "video_id": item["video_id"],
            "youtube_id": item["youtube_id"], "source_path": item["source_path"],
            "clip_start_sec": row["clip"]["start_sec"],
            "clip_end_sec": row["clip"]["end_sec"],
            "weak_segments_clip_local": [[s["start_sec"], s["end_sec"]] for s in row["segments"]],
            "label_status": "WEAK_TEACHER",
        })

    train_frames = []
    for item in by_split["train"]:
        idx = item["row_index"]
        row, mapping = labels[idx], mappings[idx]
        kfs = eligible_keyframes(row)
        if not kfs:
            raise RuntimeError(f"no eligible training keyframe: {item['video_id']}")
        train_frames.extend(record_for(item, row, mapping, kfs[j])
                            for j in evenly_spaced_indices(len(kfs)))

    # One mid-highlight frame from each of 16 distinct sources, selected by a
    # stable hash before evaluating model outputs.
    smoke = []
    seen = set()
    for item in sorted(by_split["train"], key=lambda x: hashlib.sha256(x["video_id"].encode()).hexdigest()):
        if item["youtube_id"] in seen:
            continue
        seen.add(item["youtube_id"])
        kfs = eligible_keyframes(labels[item["row_index"]])
        smoke.append(record_for(item, labels[item["row_index"]], mappings[item["row_index"]],
                                kfs[len(kfs) // 2]))
        if len(smoke) == 16:
            break
    if len(smoke) != 16 or len({r["youtube_id"] for r in smoke}) != 16:
        raise RuntimeError("cannot freeze 16 independent smoke examples")
    if len({r["sample_key"] for r in dev_frames}) != len(dev_frames):
        raise RuntimeError("duplicate dev frame")
    if len({r["youtube_id"] for r in dev_frames}) != 74:
        raise RuntimeError("dev source group count changed")
    if any("/test/" in r["source_path"] for r in dev_frames + train_frames):
        raise RuntimeError("competition test path in candidate")

    OUT.mkdir(parents=True, exist_ok=True)
    for name, records in (("dev_frames.jsonl", dev_frames), ("dev_temporal.jsonl", temporal_dev),
                          ("train_frames.jsonl", train_frames), ("smoke_frames.jsonl", smoke)):
        (OUT / name).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                                       for r in records), encoding="utf-8")
    counts = Counter(r["youtube_id"] for r in dev_frames)
    freeze = {
        "status": "FROZEN_BEFORE_MODEL_OUTPUT",
        "label_sha256": sha256(source_labels), "mapping_sha256": sha256(MAPPING),
        "weak_split_sha256": sha256(split_file),
        "sampling_rule": "eligible in-segment crop_keyframes; all if <=4 else rounded evenly spaced first/interior/last",
        "smoke_rule": "sha256(video_id) order, first 16 unique youtube_id, middle eligible keyframe",
        "dev_rows": len(temporal_dev), "dev_source_groups": len(counts),
        "dev_frames": len(dev_frames), "train_frames": len(train_frames),
        "smoke_frames": len(smoke),
        "dev_frames_per_source_min": min(counts.values()),
        "dev_frames_per_source_max": max(counts.values()),
        "dev_label_status": "WEAK_TEACHER_NOT_OFFICIAL_GROUND_TRUTH",
        "sha256": {name: sha256(OUT / name) for name in
                   ("dev_frames.jsonl", "dev_temporal.jsonl", "train_frames.jsonl", "smoke_frames.jsonl")},
    }
    (OUT / "freeze_record.json").write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(freeze, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
