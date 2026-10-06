#!/usr/bin/env python3
"""One-off: make the P1a consumption check use each sample's own target ratio.

The synthetic E2E manifest has an S01 (16:9) and an S02 (9:16); writing every
prediction row as [16,9] made the P1a validator reject the file (TARGET_RATIO_MISMATCH)
and the consumption check reported INVALID_INPUT instead of the sparse diagnostic.
"""
from __future__ import annotations

from pathlib import Path

p = Path(__file__).resolve().parent / "run_fix_validation.py"
text = p.read_text(encoding="utf-8")

old = '''        predictions = tmp_path / "predictions.jsonl"
        predictions.write_text("\\n".join(
            json.dumps({"video_id": vid, "targetRatioWH": [16, 9], "predictions": []})
            for vid in index) + "\\n", encoding="utf-8")'''
new = '''        predictions = tmp_path / "predictions.jsonl"
        # every row carries that video's own target ratio: a mismatch is rejected outright
        predictions.write_text("\\n".join(
            json.dumps({"video_id": vid,
                        "targetRatioWH": [int(index[vid]["targetRatioWH"][0]),
                                          int(index[vid]["targetRatioWH"][1])],
                        "predictions": []}) for vid in index) + "\\n", encoding="utf-8")'''
assert old in text, "prediction block not found"
p.write_text(text.replace(old, new), encoding="utf-8")
print("p1a consumption predictions now use each sample's target ratio")
