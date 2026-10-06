#!/usr/bin/env python3
"""One-off: rename the keyframe field `box` -> `box_xyw` to match the P1a reference schema.

The P1a `aic6.scoring.load_reference` reads three-element [x, y, w] triplets from
`box_xyw`, so the P1b tool must emit that same key.  This script performs the rename
across the tool, its tests and the shared case file, verifying every replacement.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = ROOT / "round6_score_alignment/p1b"


def patch(rel: str, pairs: list[tuple[str, str]]) -> None:
    path = P1B / rel
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert old in text, f"{rel}: pattern not found: {old[:70]!r}"
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"{rel}: {len(pairs)} replacement(s) applied")


JS_TICK = "`"
patch("annotation_core.js", [
    ("      problems.push(...boxProblems(kf.box, sample, where));",
     "      problems.push(...boxProblems(kf.box_xyw, sample, where));"),
    ("frames: keyframes.map(kf => ({ frame: kf.frame, box: kf.box }))",
     "frames: keyframes.map(kf => ({ frame: kf.frame, box_xyw: kf.box_xyw }))"),
    ("        box: kf.box,\n        box_height_derived: boxHeight(kf.box[2], sample),",
     "        box_xyw: kf.box_xyw,\n        box_height_derived: boxHeight(kf.box_xyw[2], sample),"),
    (" *   keyframes are sparse composition boxes [x, y, w] at one exact frame; the height\n"
     " *       is derived as h = w * target_h / target_w and must stay inside the frame.",
     " *   keyframes are sparse composition boxes stored under `box_xyw` = [x, y, w] (the same\n"
     " *       key the P1a reference schema uses) at one exact frame; the height is derived as\n"
     " *       h = w * target_h / target_w and must stay inside the frame."),
])

patch("annotate_template.html", [
    ("    a.keyframes.push({ frame: frameValue(), box: box, provenance: currentProvenance() });",
     "    a.keyframes.push({ frame: frameValue(), box_xyw: box, provenance: currentProvenance() });"),
    ("${kf.box[0]}</td><td>${kf.box[1]}</td><td>${kf.box[2]}</td>" +
     JS_TICK + " +\n      " + JS_TICK + "<td>${CORE.boxHeight(kf.box[2], s).toFixed(2)}</td>",
     "${kf.box_xyw[0]}</td><td>${kf.box_xyw[1]}</td><td>${kf.box_xyw[2]}</td>" +
     JS_TICK + " +\n      " + JS_TICK + "<td>${CORE.boxHeight(kf.box_xyw[2], s).toFixed(2)}</td>"),
])

patch("validate_exports.py", [
    ('        problems += box_problems(kf.get("box"), sample, where)',
     '        problems += box_problems(kf.get("box_xyw"), sample, where)'),
    ('"frames": [{"frame": kf["frame"], "box": kf["box"]}',
     '"frames": [{"frame": kf["frame"], "box_xyw": kf["box_xyw"]}'),
    ('if not all("frame" in f and "box" in f for f in video["frames"]):',
     'if not all("frame" in f and "box_xyw" in f for f in video["frames"]):'),
    ('            if "box" in kf:\n                kf["box"] = decode_sentinel(kf["box"])',
     '            if "box_xyw" in kf:\n                kf["box_xyw"] = decode_sentinel(kf["box_xyw"])'),
])

patch("run_boundary_cases.js", [
    ("{ box: decodeBox(kf.box) }", "{ box_xyw: decodeBox(kf.box_xyw) }"),
])

patch("run_ui_e2e.py", [
    ("corrupt.annotations[0].annotation.keyframes[0].box = [0, 0, -10];",
     "corrupt.annotations[0].annotation.keyframes[0].box_xyw = [0, 0, -10];"),
    ("out.checks.after_reimport_box = (afterReimport.keyframes || [{}])[0].box;",
     "out.checks.after_reimport_box = (afterReimport.keyframes || [{}])[0].box_xyw;"),
])

patch("run_fix_validation.py", [
    ('"box": [', '"box_xyw": ['),
    ('(afterReimport.keyframes || [{}])[0].box', '(afterReimport.keyframes || [{}])[0].box_xyw'),
])

cases = P1B / "boundary_cases.json"
doc = json.loads(cases.read_text(encoding="utf-8"))
renamed = 0
for case in doc["cases"]:
    for kf in case["annotation"].get("keyframes") or []:
        if "box" in kf:
            kf["box_xyw"] = kf.pop("box")
            renamed += 1
cases.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"boundary_cases.json: renamed {renamed} keyframe boxes")

# final sweep: no plain "box" key should remain in the tool
leftovers = []
for path in list(P1B.glob("*.py")) + list(P1B.glob("*.js")) + [P1B / "annotate_template.html"]:
    text = path.read_text(encoding="utf-8")
    if '"box"' in text or "kf.box" in text:
        leftovers.append(path.name)
print("leftovers:", leftovers or "none")
