#!/usr/bin/env python3
"""Negative tests: prove invalid model output is NOT counted as success.

Runs the exact parsers used by run_inference.py against malformed / degenerate
payloads. CPU only. Every case must come back valid=False with a non-empty
error list, and must never be silently repaired into a usable box or span.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SRC = Path("/home/inspur/aic_video_work/orarl_round1/scripts/run_inference.py")
spec = importlib.util.spec_from_file_location("ri", SRC)
ri = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ri)

CTX_IMG = {"image_w": 534, "image_h": 300}
CTX_VID = {"clip_duration_sec": 32.2}

CASES = [
    # (task, name, raw_output, ctx)
    ("spatial_grounding", "empty string", "", CTX_IMG),
    ("spatial_grounding", "no answer tag", "the man is on the right", CTX_IMG),
    ("spatial_grounding", "empty answer tag", "<answer></answer>", CTX_IMG),
    ("spatial_grounding", "not JSON", "<answer>bbox: 1,2,3,4</answer>", CTX_IMG),
    ("spatial_grounding", "JSON object not list", '<answer>{"bbox_2d":[1,2,3,4]}</answer>', CTX_IMG),
    ("spatial_grounding", "empty list", "<answer>[]</answer>", CTX_IMG),
    ("spatial_grounding", "bbox has 3 numbers", '<answer>[{"bbox_2d":[1,2,3]}]</answer>', CTX_IMG),
    ("spatial_grounding", "out of norm1000 range", '<answer>[{"bbox_2d":[1,2,1500,4]}]</answer>', CTX_IMG),
    ("spatial_grounding", "inverted box", '<answer>[{"bbox_2d":[400,300,100,50]}]</answer>', CTX_IMG),
    ("spatial_grounding", "nested thinking text only",
     "The object is a shirt. <｜end▁of▁thinking｜>", CTX_IMG),

    ("temporal_grounding", "empty", "", CTX_VID),
    ("temporal_grounding", "no answer tag", "0 to 21", CTX_VID),
    ("temporal_grounding", "one number only", "<answer>12</answer>", CTX_VID),
    ("temporal_grounding", "start >= end", "<answer> 25 to 4 </answer>", CTX_VID),
    ("temporal_grounding", "beyond clip duration", "<answer> 5 to 99 </answer>", CTX_VID),
    ("temporal_grounding", "negative start", "<answer> -3 to 9 </answer>", CTX_VID),

    ("tracking", "empty", "", CTX_VID),
    ("tracking", "no answer tag", '{"boxes": {"1": [1,2,3,4]}}', CTX_VID),
    ("tracking", "not JSON", "<answer>boxes 1..32</answer>", CTX_VID),
    ("tracking", "list not object", "<answer>[1,2,3]</answer>", CTX_VID),
    ("tracking", "missing boxes key", '<answer>{"times": {}}</answer>', CTX_VID),
    ("tracking", "empty boxes dict", '<answer>{"boxes": {}}</answer>', CTX_VID),
    ("tracking", "bbox out of range", '<answer>{"boxes": {"1": [0,0,5000,5000]}}</answer>', CTX_VID),
    ("tracking", "second key > 32", '<answer>{"boxes": {"99": [1,2,3,4]}}</answer>', CTX_VID),
    ("tracking", "non-integer second key", '<answer>{"boxes": {"abc": [1,2,3,4]}}</answer>', CTX_VID),
    ("tracking", "inverted box", '<answer>{"boxes": {"1": [500,400,100,50]}}</answer>', CTX_VID),
]

# a case that MUST pass, to show the parsers are not rejecting everything
POSITIVE = [
    ("spatial_grounding", "valid box", '<answer>[{"bbox_2d": [393, 11, 998, 997]}]</answer>', CTX_IMG),
    ("temporal_grounding", "valid span", "<answer> 0 to 21 </answer>", CTX_VID),
    ("tracking", "valid 32 seconds",
     '<answer>{"boxes": {' + ", ".join(f'"{i}": [{100+i},200,300,400]' for i in range(1, 33)) + '}}</answer>',
     CTX_VID),
]

fails = []
print("=== NEGATIVE CASES (all must be INVALID) ===")
for task, name, raw, ctx in CASES:
    parsed, errors, warnings = ri.PARSERS[task](raw, ctx)
    ok = (parsed is None) or bool(errors)
    if not ok:
        fails.append((task, name))
    print(f"  [{'PASS' if ok else 'FAIL'}] {task:20s} {name:32s} "
          f"parsed={'None' if parsed is None else 'value'} errors={len(errors)}"
          + (f"  e0={errors[0][:60]}" if errors else ""))

print("\n=== POSITIVE CASES (must be VALID) ===")
for task, name, raw, ctx in POSITIVE:
    parsed, errors, warnings = ri.PARSERS[task](raw, ctx)
    ok = (parsed is not None) and not errors
    if not ok:
        fails.append((task, name))
    print(f"  [{'PASS' if ok else 'FAIL'}] {task:20s} {name:32s} errors={errors}")

print("\n=== TRACKING PARTIAL COVERAGE -> warning, still valid (declared, not hidden) ===")
parsed, errors, warnings = ri.PARSERS["tracking"](
    '<answer>{"boxes": {"1": [393,11,998,997], "5": [400,0,998,997]}}</answer>', CTX_VID)
print(f"  parsed seconds={parsed['seconds_present_n'] if parsed else None} "
      f"errors={errors} warnings={warnings}")
print(f"  -> missing seconds are reported as a warning, NOT as silent success: "
      f"{'OK' if warnings and not errors else 'UNEXPECTED'}")

print(f"\nRESULT: {'ALL PASS' if not fails else 'FAILURES: ' + str(fails)}")
sys.exit(0 if not fails else 1)
