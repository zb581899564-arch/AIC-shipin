"""Detailed weak-teacher temporal diagnostics for frozen P2-T baselines."""
from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def union(values: list[list[float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for a, b in sorted(values):
        if not out or a > out[-1][1]:
            out.append([a, b])
        else:
            out[-1][1] = max(out[-1][1], b)
    return out


def stats(pred: list[list[float]], truth: list[list[float]]) -> dict:
    p, g = union(pred), union(truth)
    pl = sum(b - a for a, b in p)
    gl = sum(b - a for a, b in g)
    inter = sum(max(0.0, min(pb, gb) - max(pa, ga))
                for pa, pb in p for ga, gb in g)
    precision = inter / pl if pl else (1.0 if not gl else 0.0)
    recall = inter / gl if gl else (1.0 if not pl else 0.0)
    f1 = 2 * inter / (pl + gl) if pl + gl else 1.0
    return {"pred_seconds": pl, "truth_seconds": gl, "intersection_seconds": inter,
            "precision": precision, "recall": recall, "f1": f1,
            "duration_ratio": pl / gl if gl else None, "zero_overlap": inter <= 0}


def group_bootstrap(diffs: list[float], draws: int = 10000, seed: int = 20260920) -> list[float]:
    rng = random.Random(seed)
    sims = [statistics.mean(rng.choice(diffs) for _ in diffs) for _ in range(draws)]
    sims.sort()
    return [sims[int(0.025 * draws)], sims[int(0.975 * draws)]]


def evaluate(dev_path: Path, arms: dict[str, Path], overlap_path: Path, out: Path) -> None:
    dev = read_jsonl(dev_path)
    overlap = json.loads(overlap_path.read_text(encoding="utf-8"))
    exposed = set(overlap["overlap_video_ids"])
    labels = {r["video_id"]: r for r in dev}
    per_video = []
    arm_rows = {name: {r["video_id"]: r for r in read_jsonl(path)} for name, path in arms.items()}
    if any(set(rows) != set(labels) for rows in arm_rows.values()):
        raise ValueError("arm/dev identity mismatch")
    for vid, label in labels.items():
        truth = label.get("segments_clip_local", label.get("weak_segments_clip_local"))
        if truth is None:
            raise ValueError(f"missing temporal label for {vid}")
        rec = {"video_id": vid, "youtube_id": label["youtube_id"],
               "historical_s2_exposure": vid in exposed,
               "clip_duration_sec": label["clip_end_sec"] - label["clip_start_sec"],
               "truth_segments": truth,
               "truth_segment_count": len(truth)}
        for name, rows in arm_rows.items():
            row = rows[vid]
            pred = row.get("parsed_segments") if row.get("output_valid") else []
            rec[name] = {**stats(pred or [], truth),
                         "valid": bool(row.get("output_valid")),
                         "pred_segment_count": len(pred or [])}
        per_video.append(rec)

    groups = defaultdict(list)
    for row in per_video:
        groups[row["youtube_id"]].append(row)
    per_group = []
    for gid, rows in sorted(groups.items()):
        g = {"youtube_id": gid, "videos": len(rows),
             "historical_s2_exposure": any(r["historical_s2_exposure"] for r in rows)}
        for name in arms:
            for metric in ("f1", "precision", "recall", "duration_ratio"):
                vals = [r[name][metric] for r in rows if r[name][metric] is not None]
                g[f"{name}_{metric}"] = statistics.mean(vals) if vals else None
            g[f"{name}_valid_rate"] = statistics.mean(r[name]["valid"] for r in rows)
        per_group.append(g)

    summary = {"status": "WEAK_TEACHER_DIAGNOSTIC_NOT_OFFICIAL_SCORE",
               "videos": len(per_video), "source_groups": len(per_group),
               "per_arm": {}, "paired": {}, "slices": {}, "per_video": per_video,
               "per_source_group": per_group}
    for name in arms:
        summary["per_arm"][name] = {
            "group_macro_f1": statistics.mean(g[f"{name}_f1"] for g in per_group),
            "group_macro_precision": statistics.mean(g[f"{name}_precision"] for g in per_group),
            "group_macro_recall": statistics.mean(g[f"{name}_recall"] for g in per_group),
            "valid_rate": statistics.mean(r[name]["valid"] for r in per_video),
            "zero_overlap_videos": sum(r[name]["zero_overlap"] for r in per_video),
            "pred_duration_ratio_median": statistics.median(
                r[name]["duration_ratio"] for r in per_video if r[name]["duration_ratio"] is not None),
        }

    slices = {
        "historically_exposed": [r for r in per_video if r["historical_s2_exposure"]],
        "historically_unexposed": [r for r in per_video if not r["historical_s2_exposure"]],
        "one_truth_segment": [r for r in per_video if r["truth_segment_count"] == 1],
        "multiple_truth_segments": [r for r in per_video if r["truth_segment_count"] > 1],
        "duration_le_10s": [r for r in per_video if r["clip_duration_sec"] <= 10],
        "duration_10_to_20s": [r for r in per_video if 10 < r["clip_duration_sec"] <= 20],
        "duration_gt_20s": [r for r in per_video if r["clip_duration_sec"] > 20],
    }
    for slice_name, rows in slices.items():
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["youtube_id"]].append(row)
        item = {"videos": len(rows), "source_groups": len(grouped), "arms": {}}
        for name in arms:
            group_f1 = [statistics.mean(r[name]["f1"] for r in rs)
                        for rs in grouped.values()]
            item["arms"][name] = {
                "group_macro_f1": statistics.mean(group_f1) if group_f1 else None,
                "valid_rate": statistics.mean(r[name]["valid"] for r in rows) if rows else None,
                "zero_overlap_videos": sum(r[name]["zero_overlap"] for r in rows),
            }
        summary["slices"][slice_name] = item
    names = list(arms)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            diffs = [g[f"{b}_f1"] - g[f"{a}_f1"] for g in per_group]
            summary["paired"][f"{b}_minus_{a}"] = {
                "mean": statistics.mean(diffs), "ci95": group_bootstrap(diffs),
                "source_groups": len(diffs), "seed": 20260920, "draws": 10000}
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", type=Path, required=True)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--s2", type=Path, required=True)
    ap.add_argument("--fresh", type=Path)
    ap.add_argument("--overlap", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    arms = {"BASE": a.base, "OLD_S2": a.s2}
    if a.fresh:
        arms["P2T_FRESH"] = a.fresh
    evaluate(a.dev, arms, a.overlap, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
