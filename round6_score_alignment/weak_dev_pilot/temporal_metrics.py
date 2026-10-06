"""Weak-teacher temporal F1 on the frozen 82 training-dev clips.

This deliberately reports no official joint score. Historical S2 exposure is
reported separately and excluded from any prospective-training conclusion.
"""
from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


def union_intervals(values):
    merged = []
    for a, b in sorted(values):
        if not merged or a > merged[-1][1]:
            merged.append([a, b])
        else:
            merged[-1][1] = max(merged[-1][1], b)
    return merged


def f1(pred, label):
    a, b = union_intervals(pred), union_intervals(label)
    pl = sum(y - x for x, y in a)
    gl = sum(y - x for x, y in b)
    if pl <= 0 or gl <= 0:
        return 0.0
    intersection = sum(max(0.0, min(y1, y2) - max(x1, x2))
                       for x1, y1 in a for x2, y2 in b)
    return 2 * intersection / (pl + gl)


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(frozen, base, s2, overlap, draws=10000, seed=20260917):
    if len(frozen) != 82 or len({r["video_id"] for r in frozen}) != 82:
        raise ValueError("frozen dev rows changed")
    indexed = {}
    for arm, rows in (("BASE", base), ("S2", s2)):
        by_id = {r["video_id"]: r for r in rows}
        if len(by_id) != len(rows) or set(by_id) != {r["video_id"] for r in frozen}:
            raise ValueError(f"{arm} output universe changed")
        indexed[arm] = by_id
    exposed = set(overlap["overlap_video_ids"])
    per_video = []
    for row in frozen:
        vid = row["video_id"]
        result = {"video_id": vid, "youtube_id": row["youtube_id"],
                  "s2_historical_exposure": vid in exposed}
        for arm in ("BASE", "S2"):
            prediction = indexed[arm][vid]
            if prediction["youtube_id"] != row["youtube_id"]:
                raise ValueError("prediction identity mismatch")
            valid = prediction["output_valid"] is True
            result[arm + "_valid"] = valid
            result[arm + "_f1"] = f1(prediction["parsed_segments"],
                                     row["weak_segments_clip_local"]) if valid else 0.0
            result[arm + "_seconds"] = prediction.get("seconds")
            result[arm + "_peak_memory_mib"] = prediction.get("peak_memory_mib")
        per_video.append(result)
    by_group = defaultdict(list)
    for record in per_video:
        by_group[record["youtube_id"]].append(record)
    groups = []
    for gid, rows in sorted(by_group.items()):
        groups.append({"youtube_id": gid, "videos": len(rows),
                       "s2_historical_exposure": any(r["s2_historical_exposure"] for r in rows),
                       "BASE_mean_f1": statistics.mean(r["BASE_f1"] for r in rows),
                       "S2_mean_f1": statistics.mean(r["S2_f1"] for r in rows)})

    def summarize(rows):
        if not rows:
            return {"groups": 0}
        differences = [r["S2_mean_f1"] - r["BASE_mean_f1"] for r in rows]
        rng = random.Random(seed)
        boot = sorted(statistics.mean(differences[rng.randrange(len(rows))]
                                      for _ in rows) for _ in range(draws))
        return {"groups": len(rows), "BASE_group_macro_f1": statistics.mean(r["BASE_mean_f1"] for r in rows),
                "S2_group_macro_f1": statistics.mean(r["S2_mean_f1"] for r in rows),
                "S2_minus_BASE": statistics.mean(differences),
                "paired_ci95": [boot[int(.025 * draws)], boot[int(.975 * draws)]],
                "bootstrap_seed": seed, "bootstrap_draws": draws}

    return {"status": "WEAK_TEACHER_TEMPORAL_F1_NOT_OFFICIAL_SCORE",
            "dev_videos": len(per_video), "dev_groups": len(groups),
            "s2_exposed_videos": sum(r["s2_historical_exposure"] for r in per_video),
            "BASE_valid_rate": statistics.mean(r["BASE_valid"] for r in per_video),
            "S2_valid_rate": statistics.mean(r["S2_valid"] for r in per_video),
            "BASE_inference_seconds": sum(r["BASE_seconds"] or 0 for r in per_video),
            "S2_inference_seconds": sum(r["S2_seconds"] or 0 for r in per_video),
            "BASE_peak_memory_mib": max(r["BASE_peak_memory_mib"] or 0 for r in per_video),
            "S2_peak_memory_mib": max(r["S2_peak_memory_mib"] or 0 for r in per_video),
            "all_descriptive": summarize(groups),
            "s2_historically_exposed_descriptive": summarize([g for g in groups if g["s2_historical_exposure"]]),
            "s2_unexposed_descriptive": summarize([g for g in groups if not g["s2_historical_exposure"]]),
            "per_video": per_video, "per_source_group": groups}


def main():
    root = Path(__file__).resolve().parents[2] / "reports" / "round6_score_alignment" / "weak_dev_pilot"
    output = evaluate(read_jsonl(root / "dev_temporal.jsonl"),
                      read_jsonl(root / "temporal_BASE.jsonl"),
                      read_jsonl(root / "temporal_S2.jsonl"),
                      json.loads((root / "s2_overlap.json").read_text(encoding="utf-8")))
    (root / "weak_temporal_base_s2.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k not in ("per_video", "per_source_group")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
