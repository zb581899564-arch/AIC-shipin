#!/usr/bin/env python3
"""Round-6 P0: how defensible is the "nearest old spatial box" copy?

For every gap between two consecutive old (43.48) prediction intervals, compare the
box on each side of the gap.  A large box difference across a gap means the gap
spans a content/scene change, so copying either side's box into the gap is
arbitrary.  Runs purely on existing JSONL; no video decoding, no model.

Output: reports/round6_score_alignment/phase0/evidence/box_gap_continuity.json
"""
from __future__ import annotations

import bisect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAND = ROOT / "submissions/round5_s2_temporal_20260917/predictions.jsonl"
BASE = ROOT / "submissions/qwen3vl_lora_reader_20260912/predictions.jsonl"
RAW = ROOT / "reports/temporal_round5/evidence/temporal_raw_v1.jsonl"
OUT = ROOT / "reports/round6_score_alignment/phase0/evidence/box_gap_continuity.json"


def read_jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def box_iou(b1, b2, ratio):
    """[x,y,w] source-pixel boxes; height derived as h = w * th / tw."""
    tw, th = ratio
    h1, h2 = b1[2] * th / tw, b2[2] * th / tw
    r1 = (b1[0], b1[1], b1[0] + b1[2], b1[1] + h1)
    r2 = (b2[0], b2[1], b2[0] + b2[2], b2[1] + h2)
    ix = max(0.0, min(r1[2], r2[2]) - max(r1[0], r2[0]))
    iy = max(0.0, min(r1[3], r2[3]) - max(r1[1], r2[1]))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    a1 = (r1[2] - r1[0]) * (r1[3] - r1[1])
    a2 = (r2[2] - r2[0]) * (r2[3] - r2[1])
    return inter / (a1 + a2 - inter)


def intervals(frames):
    out = []
    for f in frames:
        if out and f == out[-1][1] + 1:
            out[-1][1] = f
        else:
            out.append([f, f])
    return out


def main():
    cand = {str(r["video_id"]): r for r in read_jsonl(CAND)}
    base = {str(r["video_id"]): r for r in read_jsonl(BASE)}
    raw = {str(r["video_id"]): r for r in read_jsonl(RAW)}

    n_reuse = 0
    buckets = {"identical": 0, "iou_ge_0.8": 0, "iou_0.5_0.8": 0, "iou_0.2_0.5": 0,
               "iou_lt_0.2": 0, "one_sided_open_gap": 0}
    per_video = {}
    for vid, c in cand.items():
        ratio = [float(x) for x in raw[vid]["targetRatioWH"]]
        n_frames = int(raw[vid]["n_frames"])
        if ratio[0] not in (9, 16) or n_frames <= 0:
            continue
        b = {int(p["frame"]): p["bboxes"] for p in base[vid]["predictions"]}
        bf = sorted(b)
        bset = set(bf)
        ints = intervals(bf)
        gaps = []
        for (a1, z1), (a2, z2) in zip(ints, ints[1:]):
            gaps.append((z1, a2, b[z1], b[a2]))          # (last frame before, first after)
        if ints:                                          # open ends
            gaps.append((None, ints[0][0], None, b[ints[0][0]]))
            gaps.append((ints[-1][1], None, b[ints[-1][1]], None))
        for p in c["predictions"]:
            f = int(p["frame"])
            if f in bset:
                continue
            n_reuse += 1
            hit = None
            for g in gaps:
                lo = g[0] if g[0] is not None else -1
                hi = g[1] if g[1] is not None else n_frames
                if lo < f < hi:
                    hit = g
                    break
            if hit is None:
                buckets["one_sided_open_gap"] += 1
                continue
            if hit[2] is None or hit[3] is None:
                buckets["one_sided_open_gap"] += 1
                per_video.setdefault(vid, {"n": 0, "worst": 1.0})
                per_video[vid]["n"] += 1
                continue
            iou = box_iou(hit[2], hit[3], ratio)
            if hit[2] == hit[3]:
                buckets["identical"] += 1
            if iou >= 0.8:
                buckets["iou_ge_0.8"] += 1
            elif iou >= 0.5:
                buckets["iou_0.5_0.8"] += 1
            elif iou >= 0.2:
                buckets["iou_0.2_0.5"] += 1
            else:
                buckets["iou_lt_0.2"] += 1
            e = per_video.setdefault(vid, {"n": 0, "worst": 1.0})
            e["n"] += 1
            e["worst"] = min(e["worst"], iou)

    res = {
        "method": ("for each reused frame, find the gap between two consecutive old prediction "
                   "intervals and compute the IoU between the boxes on the two sides of the gap "
                   "(boxes are [x,y,w] with derived height h = w*th/tw)"),
        "reused_frames": n_reuse,
        "side_box_iou_identical": buckets["identical"],
        "side_box_iou_ge_0.8": buckets["iou_ge_0.8"],
        "side_box_iou_0.5_0.8": buckets["iou_0.5_0.8"],
        "side_box_iou_0.2_0.5": buckets["iou_0.2_0.5"],
        "side_box_iou_lt_0.2": buckets["iou_lt_0.2"],
        "gap_open_at_video_edge": buckets["one_sided_open_gap"],
        "videos_with_reuse": len(per_video),
        "worst_videos": [{"video_id": v, "reused": e["n"], "worst_side_box_iou": round(e["worst"], 4)}
                         for v, e in sorted(per_video.items(), key=lambda kv: kv[1]["worst"])[:10]],
        "interpretation_limit": ("box discontinuity across a gap is only a proxy: it cannot prove a "
                                 "shot cut without decoding video, which P0 must not do"),
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
