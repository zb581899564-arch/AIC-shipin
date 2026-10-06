#!/usr/bin/env python3
"""Probe the label time convention before building the full mapping gate.

Questions:
  * is clip.end_sec clip-local or source-absolute?
  * what is clip_fps (derivable from crop_keyframes frame/time pairs)?
  * does source_time = clip_time + clip.start_sec hold on rows with start_sec > 0?
"""
import json
from collections import Counter

LAB = "/home/inspur/aic_video_data/labels/train.jsonl"
rows = [json.loads(l) for l in open(LAB) if l.strip()]
print("rows:", len(rows))

# --- clip fps from crop_keyframes (frame, time_sec) pairs ---
fps_votes = Counter()
for r in rows:
    kfs = r.get("crop_keyframes") or []
    for kf in kfs[:4]:
        f, t = kf.get("frame"), kf.get("time_sec")
        if isinstance(f, (int, float)) and isinstance(t, (int, float)) and t > 0 and f > 0:
            fps_votes[round(f / t, 3)] += 1
print("derived clip fps votes (top 6):", fps_votes.most_common(6))

# --- start_sec vs 0 ---
n_zero = sum(1 for r in rows if r["clip"]["start_sec"] == 0)
print(f"clip.start_sec == 0: {n_zero}/{len(rows)}")
starts = sorted({r["clip"]["start_sec"] for r in rows})
print("distinct start_sec (first 12):", starts[:12])
print("max start_sec:", max(starts))

# --- convention check: is end_sec clip-local?  compare with segments ---
print("\n=== rows with start_sec > 0: compare clip.* and segments[*] ===")
shown = 0
for r in rows:
    if r["clip"]["start_sec"] <= 0:
        continue
    c = r["clip"]
    segs = r.get("segments") or []
    print(f"\nvideo_id={r['video_id']} source_vid={c['source_vid']}")
    print(f"  clip: start_sec={c['start_sec']} end_sec={c['end_sec']} "
          f"used_window={c.get('used_window')} qvh_window={c.get('qvh_window')}")
    print(f"  clip length (end-start) = {c['end_sec']-c['start_sec']:.3f}")
    for s in segs[:2]:
        print(f"  seg: start_sec={s['start_sec']:.3f} end_sec={s['end_sec']:.3f} "
              f"start_frame={s['start_frame']} end_frame={s['end_frame']} "
              f"source_start_sec={s['source_start_sec']:.3f} "
              f"source_end_sec={s['source_end_sec']:.3f}")
        print(f"       seg.start_sec - clip.start_sec = {s['start_sec']-c['start_sec']:.3f}")
        print(f"       source_start_sec - seg.start_sec = "
              f"{s['source_start_sec']-s['start_sec']:.3f}")
    kfs = r.get("crop_keyframes") or []
    if kfs:
        print(f"  kf: frame {kfs[0].get('frame')}..{kfs[-1].get('frame')}  "
              f"time {kfs[0].get('time_sec')}..{kfs[-1].get('time_sec')}")
    rois = r.get("cropRois") or []
    if rois:
        print(f"  cropRois: frames {rois[0][0]}..{rois[-1][0]}  n={len(rois)}")
    shown += 1
    if shown >= 4:
        break

# --- is clip length always <= 32?  and how do frames relate ---
lens = [r["clip"]["end_sec"] - r["clip"]["start_sec"] for r in rows]
print(f"\nclip length: min={min(lens):.3f} max={max(lens):.3f} "
      f"median={sorted(lens)[len(lens)//2]:.3f}")
# max frame seen in crop_keyframes / cropRois vs length*30
mx = []
for r in rows:
    kf = max((k.get("frame", 0) for k in (r.get("crop_keyframes") or [])), default=0)
    ro = max((x[0] for x in (r.get("cropRois") or [])), default=0)
    mx.append(max(kf, ro))
print("max frame index across labels: min=%d max=%d" % (min(mx), max(mx)))
print("implied fps if max_frame == length*fps:",
      sorted(round(m / (r["clip"]["end_sec"] - r["clip"]["start_sec"]), 2)
             for m, r in zip(mx, rows))[:5],
      "...", sorted(round(m / (r["clip"]["end_sec"] - r["clip"]["start_sec"]), 2)
                    for m, r in zip(mx, rows))[-5:])
