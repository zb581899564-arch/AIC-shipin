"""Freeze source-disjoint temporal training inputs for P2-T.

This derives manifests from the already frozen 372/82/64 weak split.  It does
not read the holdout rows' label payloads beyond the public split manifest and
never touches competition-test media.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALIGN = ROOT / "reports" / "round6_score_alignment" / "training_alignment_20260917"
OLD = ROOT / "reports" / "round6_score_alignment" / "weak_dev_pilot"
RUN_ID = "round6_p2t_20260920T1429Z"
OUT = ROOT / "reports" / "round6_score_alignment" / "p2t_temporal_improvement" / RUN_ID


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                            for r in rows), encoding="utf-8")


def temporal_record(item: dict, label: dict) -> tuple[dict | None, list[str]]:
    if item["video_id"] != label["video_id"]:
        raise ValueError(f"identity mismatch at row {item['row_index']}")
    raw_segs = [[float(s["start_sec"]), float(s["end_sec"])]
                for s in label.get("segments", [])]
    duration = float(label["clip"]["end_sec"] - label["clip"]["start_sec"])
    reasons: list[str] = []
    if not raw_segs or len(raw_segs) > 5:
        reasons.append(f"invalid_segment_count:{len(raw_segs)}")
    if any(not (0 <= a < b) for a, b in raw_segs):
        reasons.append("nonpositive_or_negative_segment")
    frame_interval = 1.0 / float(item["clip_fps"])
    if any(b - duration > frame_interval + 1e-9 for _, b in raw_segs):
        reasons.append("segment_end_exceeds_one_frame_tolerance")
    if reasons:
        return None, reasons
    clamp_notes = [{"original_end": b, "clamped_end": duration,
                    "overrun_seconds": b - duration}
                   for _, b in raw_segs if b > duration]
    segs = [[a, min(b, duration)] for a, b in raw_segs]
    return {
        "sample_id": f"{item['youtube_id']}__r{item['row_index']}",
        "row_index": item["row_index"],
        "video_id": item["video_id"],
        "youtube_id": item["youtube_id"],
        "source_path": item["source_path"],
        "clip_start_sec": float(label["clip"]["start_sec"]),
        "clip_end_sec": float(label["clip"]["end_sec"]),
        "clip_duration_sec": duration,
        "segments_clip_local": segs,
        "n_segments": len(segs),
        "label_status": "WEAK_TEACHER",
        "split": item["split"],
        "segment_clamp_notes": clamp_notes,
    }, []


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    split_path = ALIGN / "weak_split_manifest.jsonl"
    labels_path = ALIGN / "train.source_copy.jsonl"
    split = read_jsonl(split_path)
    labels = read_jsonl(labels_path)
    if len(split) != 518 or len(labels) != 987:
        raise RuntimeError("frozen row counts changed")
    by_split = {name: [r for r in split if r["split"] == name]
                for name in ("train", "dev", "holdout")}
    if {k: len(v) for k, v in by_split.items()} != {"train": 372, "dev": 82, "holdout": 64}:
        raise RuntimeError("frozen split sizes changed")
    groups = {k: {r["youtube_id"] for r in v} for k, v in by_split.items()}
    if groups["train"] & groups["dev"] or groups["train"] & groups["holdout"] or groups["dev"] & groups["holdout"]:
        raise RuntimeError("source group leakage")

    derived, exclusions = {"train": [], "dev": []}, []
    for split_name in ("train", "dev"):
        for item in by_split[split_name]:
            rec, reasons = temporal_record(item, labels[item["row_index"]])
            if rec is None:
                exclusions.append({"split": split_name, "video_id": item["video_id"],
                                   "row_index": item["row_index"], "reasons": reasons})
            else:
                derived[split_name].append(rec)
    train, dev = derived["train"], derived["dev"]
    if len(dev) != 82 or len(train) != 370:
        raise RuntimeError(f"unexpected valid temporal rows: train={len(train)} dev={len(dev)}")
    old_dev = read_jsonl(OLD / "dev_temporal.jsonl")
    old_by_id = {r["video_id"]: r for r in old_dev}
    for r in dev:
        old = old_by_id.get(r["video_id"])
        if old is None or old["weak_segments_clip_local"] != r["segments_clip_local"]:
            raise RuntimeError(f"dev reproduction mismatch: {r['video_id']}")

    # Stable 16-source engineering smoke set.  It is repeated only by the
    # trainer; the frozen manifest itself contains each record exactly once.
    ordered = sorted(train, key=lambda r: hashlib.sha256(r["video_id"].encode()).hexdigest())
    smoke, seen = [], set()
    for row in ordered:
        if row["youtube_id"] in seen:
            continue
        seen.add(row["youtube_id"])
        smoke.append(row)
        if len(smoke) == 16:
            break
    if len(smoke) != 16:
        raise RuntimeError("could not freeze 16 independent smoke sources")

    write_jsonl(OUT / "train_temporal.jsonl", train)
    write_jsonl(OUT / "dev_temporal.jsonl", dev)
    write_jsonl(OUT / "smoke_temporal.jsonl", smoke)
    (OUT / "temporal_exclusions.json").write_text(
        json.dumps({"count": len(exclusions), "records": exclusions},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inputs = {
        "run_id": RUN_ID,
        "status": "FROZEN_BEFORE_NEW_MODEL_OUTPUT",
        "label_status": "WEAK_TEACHER_NOT_OFFICIAL_GROUND_TRUTH",
        "split_rows": {k: len(v) for k, v in by_split.items()},
        "split_groups": {k: len(v) for k, v in groups.items()},
        "valid_temporal_rows": {"train": len(train), "dev": len(dev)},
        "temporal_exclusions": exclusions,
        "train_dev_group_overlap": len(groups["train"] & groups["dev"]),
        "holdout_policy": "64-row holdout remains closed; not used for selection or evaluation",
        "competition_test_policy": "not read, inferred, packaged, or uploaded in P2-T",
        "source_hashes": {
            "weak_split_manifest": sha256(split_path),
            "label_source_copy": sha256(labels_path),
            "old_dev_temporal": sha256(OLD / "dev_temporal.jsonl"),
            "old_base_predictions": sha256(OLD / "temporal_BASE.jsonl"),
            "old_s2_predictions": sha256(OLD / "temporal_S2.jsonl"),
        },
        "derived_hashes": {name: sha256(OUT / name) for name in
                           ("train_temporal.jsonl", "dev_temporal.jsonl",
                            "smoke_temporal.jsonl", "temporal_exclusions.json")},
        "smoke_rule": "sha256(video_id) order; first row from each of 16 unique train youtube_id",
    }
    (OUT / "input_freeze.json").write_text(
        json.dumps(inputs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
