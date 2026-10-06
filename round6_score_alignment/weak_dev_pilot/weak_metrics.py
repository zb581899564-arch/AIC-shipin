"""Spatial teacher-agreement diagnostics, never an AIC official score."""
from __future__ import annotations

import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path


def iou_xywh(a, b):
    if len(a) != 4 or len(b) != 4:
        raise ValueError("IoU requires [x,y,w,h]")
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v)
           for v in [*a, *b]):
        raise ValueError("nonfinite or nonnumeric box")
    if a[2] <= 0 or a[3] <= 0 or b[2] <= 0 or b[3] <= 0:
        raise ValueError("nonpositive box")
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    overlap = max(0, x1 - x0) * max(0, y1 - y0)
    union = a[2] * a[3] + b[2] * b[3] - overlap
    return overlap / union


def center_crop(width: int, height: int, target_ratio_wh):
    tw, th = target_ratio_wh
    if not (width > 0 and height > 0 and tw > 0 and th > 0):
        raise ValueError("invalid geometry")
    crop_w = min(width, math.floor(height * tw / th))
    crop_h = crop_w * th / tw
    x = round((width - crop_w) / 2)
    y = round((height - crop_h) / 2)
    if x + crop_w > width or y + crop_h > height:
        raise AssertionError("center crop outside source")
    return [x, y, crop_w, crop_h]


def score_records(frames, predictions=None):
    """Every frozen frame stays in the denominator; absent/invalid P1 earns 0."""
    frame_keys = [r["sample_key"] for r in frames]
    if len(frame_keys) != len(set(frame_keys)):
        raise ValueError("duplicate frozen frame")
    if predictions is not None and set(predictions) != set(frame_keys):
        raise ValueError("prediction set must equal frozen frame set")
    result = []
    for f in frames:
        w, h = f["source_width"], f["source_height"]
        weak = f["weak_roi_xywh"]
        p0 = center_crop(w, h, f["target_ratio_wh"])
        record = {"sample_key": f["sample_key"], "video_id": f["video_id"],
                  "youtube_id": f["youtube_id"], "P0_xywh": p0,
                  "WEAK_PROXY_IoU_P0": iou_xywh(p0, weak)}
        if predictions is not None:
            pred = predictions[f["sample_key"]]
            box = pred.get("box_xywh") if pred.get("output_valid") is True else None
            valid = False
            if isinstance(box, list) and len(box) == 4:
                try:
                    x, y, bw, bh = box
                    if x >= 0 and y >= 0 and x + bw <= w and y + bh <= h:
                        score = iou_xywh(box, weak)
                        valid = True
                except (TypeError, ValueError):
                    pass
            record["P1_valid"] = valid
            record["WEAK_PROXY_IoU_P1"] = score if valid else 0.0
        result.append(record)
    return result


def summarize(per_frame, bootstrap=10000, seed=20260917):
    by_video = defaultdict(list)
    for row in per_frame:
        by_video[row["video_id"]].append(row)
    videos = []
    for vid, rows in sorted(by_video.items()):
        record = {"video_id": vid, "youtube_id": rows[0]["youtube_id"], "frames": len(rows),
                  "P0_mean": statistics.mean(r["WEAK_PROXY_IoU_P0"] for r in rows)}
        if "WEAK_PROXY_IoU_P1" in rows[0]:
            record["P1_mean"] = statistics.mean(r["WEAK_PROXY_IoU_P1"] for r in rows)
            record["P1_valid"] = sum(r["P1_valid"] for r in rows)
        videos.append(record)
    by_group = defaultdict(list)
    for row in videos:
        by_group[row["youtube_id"]].append(row)
    groups = []
    for gid, rows in sorted(by_group.items()):
        rec = {"youtube_id": gid, "videos": len(rows),
               "P0_mean": statistics.mean(r["P0_mean"] for r in rows)}
        if "P1_mean" in rows[0]:
            rec["P1_mean"] = statistics.mean(r["P1_mean"] for r in rows)
            rec["P1_minus_P0"] = rec["P1_mean"] - rec["P0_mean"]
        groups.append(rec)
    out = {"status": "WEAK_PROXY_ONLY_NOT_OFFICIAL_SCORE", "frames": len(per_frame),
           "videos": len(videos), "source_groups": len(groups),
           "P0_source_macro_mean": statistics.mean(g["P0_mean"] for g in groups),
           "per_video": videos, "per_source_group": groups}
    if "P1_mean" in groups[0]:
        diffs = [g["P1_minus_P0"] for g in groups]
        rng = random.Random(seed)
        draws = sorted(statistics.mean(diffs[rng.randrange(len(diffs))]
                                        for _ in diffs) for _ in range(bootstrap))
        out.update(P1_source_macro_mean=statistics.mean(g["P1_mean"] for g in groups),
                   P1_valid_frames=sum(r["P1_valid"] for r in per_frame),
                   P1_valid_rate=sum(r["P1_valid"] for r in per_frame) / len(per_frame),
                   P1_groups_below_0_70=sum(g["P1_mean"] < 0.70 for g in groups),
                   P1_minus_P0_source_macro_mean=statistics.mean(diffs),
                   P1_minus_P0_ci95=[draws[int(.025 * bootstrap)],
                                     draws[int(.975 * bootstrap)]],
                   bootstrap_seed=seed, bootstrap_draws=bootstrap)
    return out


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    root = Path(__file__).resolve().parents[2]
    out = root / "reports" / "round6_score_alignment" / "weak_dev_pilot"
    frames = load_jsonl(out / "dev_frames.jsonl")
    p1 = out / "p1_predictions.jsonl"
    predictions = None
    if p1.exists():
        values = load_jsonl(p1)
        predictions = {row["sample_key"]: row for row in values}
        if len(predictions) != len(values):
            raise ValueError("duplicate prediction key")
    per_frame = score_records(frames, predictions)
    result = summarize(per_frame)
    name = "weak_spatial_p0_p1.json" if predictions is not None else "weak_spatial_p0.json"
    (out / name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("per_video", "per_source_group")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
