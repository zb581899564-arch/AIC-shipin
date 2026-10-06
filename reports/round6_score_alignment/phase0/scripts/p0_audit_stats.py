#!/usr/bin/env python3
"""Round-6 P0 read-only CPU audit statistics.

Inputs (all read-only, no video decoding, no model, no GPU):
  reports/temporal_round5/evidence/temporal_raw_v1.jsonl   round-5 S2 temporal inference record
  submissions/round5_s2_temporal_20260917/predictions.jsonl round-5 packaged candidate
  submissions/qwen3vl_lora_reader_20260912/predictions.jsonl the 43.48 spatial base

Output: reports/round6_score_alignment/phase0/evidence/p0_cpu_stats.json

Three questions answered numerically:
  A. Does the composer's seconds->frame rule (round + inclusive end) reproduce the
     packaged candidate?  (replication check of compose_temporal_candidate_v1.py)
  B. How many frames does that convention add/remove relative to the convention used
     by the previously scored 43.48 pipeline (ceil + half-open [start,end))?
  C. How far can a reused ("nearest old spatial box") frame be from the frame whose
     box it copies, and do those copies span gaps between old prediction intervals?
"""
from __future__ import annotations

import bisect
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "reports/temporal_round5/evidence/temporal_raw_v1.jsonl"
CAND = ROOT / "submissions/round5_s2_temporal_20260917/predictions.jsonl"
BASE = ROOT / "submissions/qwen3vl_lora_reader_20260912/predictions.jsonl"
OUT = ROOT / "reports/round6_score_alignment/phase0/evidence/p0_cpu_stats.json"


def read_jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def pct(vals, p):
    if not vals:
        return None
    v = sorted(vals)
    return v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))]


def new_frames(start, a0, b0, fps, n_frames):
    """compose_temporal_candidate_v1.py:110-115 (round, inclusive end)."""
    fa = max(0, min(n_frames - 1, round((start + a0) * fps)))
    fb = max(0, min(n_frames - 1, round((start + b0) * fps)))
    if fb <= fa:
        fb = min(n_frames - 1, fa + 1)
    return set(range(fa, fb + 1))


def old_frames(start, a0, b0, fps, n_frames, duration):
    """inference_v2/temporal.py: clip to duration, ceil, half-open [f0,f1)."""
    a = max(0.0, min(start + a0, duration))
    b = max(0.0, min(start + b0, duration))
    if b <= a:
        return set()
    eps = 1e-9
    f0 = max(0, min(int(math.ceil(a * fps - eps)), n_frames))
    f1 = max(0, min(int(math.ceil(b * fps - eps)), n_frames))
    return set(range(f0, f1)) if f1 > f0 else set()


def intervals_of(sorted_frames):
    out = []
    for f in sorted_frames:
        if out and f == out[-1][1] + 1:
            out[-1][1] = f
        else:
            out.append([f, f])
    return out


def main():
    raw = {str(r["video_id"]): r for r in read_jsonl(RAW)}
    cand = {str(r["video_id"]): r for r in read_jsonl(CAND)}
    base = {str(r["video_id"]): r for r in read_jsonl(BASE)}

    res = {
        "inputs": {
            "temporal_raw": str(RAW.relative_to(ROOT)),
            "candidate": str(CAND.relative_to(ROOT)),
            "spatial_base": str(BASE.relative_to(ROOT)),
        },
        "counts": {
            "videos_temporal_raw": len(raw),
            "videos_candidate": len(cand),
            "videos_spatial_base": len(base),
            "windows": sum(len(r["windows"]) for r in raw.values()),
        },
        "replication": {},
        "convention": {},
        "box_reuse": {},
        "invalid_windows": {},
    }

    # ---------- window / validity accounting ----------
    w_total = w_valid = w_fallback = 0
    parse_error_kinds = {}
    empty_segments = 0
    for r in raw.values():
        for w in r["windows"]:
            w_total += 1
            if w.get("output_valid") and w.get("parsed_segments"):
                w_valid += 1
            else:
                w_fallback += 1
            for e in (w.get("parse_errors") or []):
                key = e.split(":")[0][:60]
                parse_error_kinds[key] = parse_error_kinds.get(key, 0) + 1
            if w.get("parsed_segments") == []:
                empty_segments += 1
    res["invalid_windows"] = {
        "windows_total": w_total,
        "windows_with_usable_segments": w_valid,
        "windows_needing_composer_fallback": w_fallback,
        "windows_with_explicit_empty_segment_list": empty_segments,
        "parse_error_kinds": parse_error_kinds,
        "note": ("composer line 99-102: output_valid False OR empty parsed_segments "
                 "=> centred 80% of window; illegal-empty and parse-failure are the same branch"),
    }

    # ---------- A. replication of the packaged candidate ----------
    rep_mismatch = []
    new_total = old_total = 0
    both_empty = 0
    only_new = only_old = 0
    diff_hist = {}
    for vid, t in raw.items():
        n_frames, fps, dur = int(t["n_frames"]), float(t["fps"]), float(t["duration_sec"])
        sel_new, sel_old = set(), set()
        for w in t["windows"]:
            start = float(w["start_sec"])
            segs = w.get("parsed_segments") if w.get("output_valid") else None
            if not segs:
                segs = [[float(w["duration_sec"]) * 0.1, float(w["duration_sec"]) * 0.9]]
            for a0, b0 in segs:
                sel_new |= new_frames(start, a0, b0, fps, n_frames)
                sel_old |= old_frames(start, a0, b0, fps, n_frames, dur)
        got = {int(p["frame"]) for p in cand[vid]["predictions"]}
        if got != sel_new:
            rep_mismatch.append({"video_id": vid, "expected_new": len(sel_new), "got": len(got),
                                 "symdiff": len(got ^ sel_new)})
        new_total += len(sel_new)
        old_total += len(sel_old)
        if not sel_new and not sel_old:
            both_empty += 1
        elif sel_new and not sel_old:
            only_new += 1
        elif sel_old and not sel_new:
            only_old += 1
        d = len(sel_new) - len(sel_old)
        diff_hist[str(d)] = diff_hist.get(str(d), 0) + 1

    res["replication"] = {
        "videos_reproduced_exactly": len(raw) - len(rep_mismatch),
        "videos_with_mismatch": len(rep_mismatch),
        "mismatch_examples": rep_mismatch[:5],
        "packaged_total_frames": sum(len(c["predictions"]) for c in cand.values()),
        "recomputed_new_convention_frames": new_total,
    }
    res["convention"] = {
        "frames_new_round_inclusive": new_total,
        "frames_old_ceil_halfopen": old_total,
        "delta_frames": new_total - old_total,
        "delta_ratio": round((new_total - old_total) / old_total, 6) if old_total else None,
        "videos_both_empty": both_empty,
        "videos_only_new_nonempty": only_new,
        "videos_only_old_nonempty": only_old,
        "per_video_frame_delta_histogram": dict(sorted(diff_hist.items(), key=lambda kv: int(kv[0]))),
        "note": ("old convention = improvement/inference_worker/inference_v2/temporal.py "
                 "seconds_to_frame_segments (ceil, half-open) — the convention validated by "
                 "accept_candidate.py:68 range(start,end) for the 43.48 package"),
    }

    # ---------- C. nearest-box reuse geometry ----------
    n_reuse = 0
    gaps = []
    reuse_box_mismatch = 0
    reuse_outside_base_union = 0
    per_video_gap_max = {}
    reuse_anchor_is_in_gap_side = 0
    for vid, c in cand.items():
        b = base[vid]
        base_boxes = {}
        for p in b["predictions"]:
            base_boxes[int(p["frame"])] = p["bboxes"]
        bf = sorted(base_boxes)
        bset = set(bf)
        # union of base intervals (tolerance 0: exact contiguity)
        bint = intervals_of(bf)
        covered = set()
        for a, z in bint:
            covered.update(range(a, z + 1))
        vid_gaps = []
        for p in c["predictions"]:
            f = int(p["frame"])
            if f in bset:
                continue
            n_reuse += 1
            i = bisect.bisect_left(bf, f)
            options = bf[max(0, i - 1):min(len(bf), i + 1)]
            near = min(options, key=lambda x: (abs(x - f), x))
            gap = abs(near - f)
            gaps.append(gap)
            vid_gaps.append(gap)
            if base_boxes[near] != p["bboxes"]:
                reuse_box_mismatch += 1
            if f not in covered:
                reuse_outside_base_union += 1
            # is the anchor on the other side of a base interval boundary?
            for a, z in bint:
                if a <= near <= z and not (a <= f <= z):
                    reuse_anchor_is_in_gap_side += 1
                    break
        if vid_gaps:
            per_video_gap_max[vid] = max(vid_gaps)

    worst = sorted(per_video_gap_max.items(), key=lambda kv: -kv[1])[:10]
    res["box_reuse"] = {
        "reused_frames": n_reuse,
        "reuse_ratio_of_predictions": round(n_reuse / max(1, sum(len(c["predictions"]) for c in cand.values())), 6),
        "gap_frames_p50": pct(gaps, 0.50),
        "gap_frames_p90": pct(gaps, 0.90),
        "gap_frames_p99": pct(gaps, 0.99),
        "gap_frames_max": max(gaps) if gaps else None,
        "gap_histogram": {str(k): sum(1 for g in gaps if (g == k if k in (0, 1) else g <= k and g > prev))
                          for prev, k in [(0, 1), (1, 5), (5, 15), (15, 30), (30, 60), (60, 300)]},
        "gap_le_1": sum(1 for g in gaps if g <= 1),
        "gap_le_5": sum(1 for g in gaps if g <= 5),
        "gap_le_15": sum(1 for g in gaps if g <= 15),
        "gap_le_30": sum(1 for g in gaps if g <= 30),
        "gap_gt_30": sum(1 for g in gaps if g > 30),
        "boundary_crossing_copies": reuse_anchor_is_in_gap_side,
        "reused_frame_outside_all_base_intervals": reuse_outside_base_union,
        "box_identity_mismatch_vs_nearest": reuse_box_mismatch,
        "videos_with_reuse": len(per_video_gap_max),
        "worst_videos_by_max_gap": [{"video_id": v, "max_gap_frames": g} for v, g in worst],
        "note": ("gap = |predicted frame - nearest base-prediction frame|; the composer has no "
                 "shot-boundary or distance guard (compose_temporal_candidate_v1.py:121-127). "
                 "No video decoding is possible in P0, so shot cuts cannot be counted here."),
    }

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("inputs",)}, ensure_ascii=False, indent=2)[:6000])
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
