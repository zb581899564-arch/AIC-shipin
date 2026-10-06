#!/usr/bin/env python3
"""Diagnose why rows land in time_uncertain: inspect crop_keyframes patterns."""
import json
from collections import Counter

LAB = "/home/inspur/aic_video_data/labels/train.jsonl"
rows = [json.loads(l) for l in open(LAB) if l.strip()]

n_empty = sum(1 for r in rows if not (r.get("crop_keyframes") or []))
print("rows with EMPTY crop_keyframes:", n_empty)

# ratio distribution per row
patterns = Counter()
examples = {}
for r in rows:
    kfs = r.get("crop_keyframes") or []
    if not kfs:
        continue
    pairs = [(k.get("frame"), k.get("time_sec")) for k in kfs
             if isinstance(k.get("frame"), (int, float))
             and isinstance(k.get("time_sec"), (int, float))]
    pos = [(f, t) for f, t in pairs if f > 0 and t > 0]
    if not pos:
        patterns["all_zero_frame_or_time"] += 1
        continue
    ratios = sorted({round(f / t, 4) for f, t in pos})
    key = len(ratios)
    patterns[f"n_distinct_ratio_{min(key,5) if key<5 else 'ge5'}"] += 1
    if key >= 2:
        examples.setdefault(key, (r["video_id"], pos[:8], ratios[:8]))

print("\nper-row distinct frame/time ratio count:")
for k, v in sorted(patterns.items()):
    print(f"  {k:32s} {v}")

print("\nexamples with >=2 distinct ratios:")
for k in sorted(examples)[:4]:
    vid, pos, ratios = examples[k]
    print(f"  video_id={vid} n_distinct={k}")
    print(f"    (frame, time_sec) first8 = {pos}")
    print(f"    distinct ratios first8   = {ratios}")

# how do time_sec values look?
print("\n=== time_sec rounding check (first 5 rows) ===")
for r in rows[:5]:
    kfs = r.get("crop_keyframes") or []
    print(f"  {r['video_id']}: " +
          ", ".join(f"({k.get('frame')},{k.get('time_sec')})" for k in kfs[:5]))

# does a robust median-fps fit work?
ok = 0
for r in rows:
    kfs = r.get("crop_keyframes") or []
    pos = [(k["frame"], k["time_sec"]) for k in kfs
           if isinstance(k.get("frame"), (int, float))
           and isinstance(k.get("time_sec"), (int, float))
           and k["frame"] > 0 and k["time_sec"] > 0]
    if not pos:
        continue
    ratios = sorted(f / t for f, t in pos)
    med = ratios[len(ratios) // 2]
    if all(abs(f - round(t * med)) <= 1 for f, t in pos):
        ok += 1
print(f"\nrows where median-fps fits every keyframe within 1 frame: {ok}")
