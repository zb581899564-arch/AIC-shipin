#!/usr/bin/env python3
"""P1b-fix: validate annotation exports and derive P1a-compatible references.

The rules implemented here are the SAME rules as ``annotation_core.js`` (the file the
page loads).  Both sides are exercised on ``boundary_cases.json`` and compared by the
``compare`` subcommand, so the two implementations cannot drift apart silently.

Fixed in this revision (supervisor P1b review, blocker 3):
  * non-finite numbers (NaN, +/-Infinity) are rejected everywhere, not compared;
  * bools and strings are rejected as numbers;
  * frame uniqueness, interval uniqueness and interval consistency are checked;
  * an invalid export returns ``valid=false`` with problems AND ``reference=None``
    (never a consumable reference);
  * sparse keyframes always stay ``coverage="sparse"`` — never widened into a
    full-video reference and never turned into a joint score.

Commands
--------
  python validate_exports.py cases   --manifest <m> --cases <c> --out <o>
  python validate_exports.py export  --manifest <m> --export <e> [--out <o>]
  python validate_exports.py compare --python <p> --js <j> [--out <o>]

Exit codes: 0 = valid / all cases pass / identical, 2 = invalid input or divergence.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = Path(__file__).resolve().parent
DEFAULT_MANIFEST = P1B / "pilot_manifest.json"
DEFAULT_CASES = P1B / "boundary_cases.json"

CORE_VERSION = "p1b_core_v2"
EXPORT_SCHEMA = "p1b_annotation_export_v2"
DRAFT_SCHEMA = "p1b_annotation_draft_v2"
INTERVAL_SEMANTICS = "half_open_end_exclusive"
STATES = {"UNANNOTATED", "HAS_HIGHLIGHT", "NO_HIGHLIGHT", "UNCERTAIN"}
LOCATOR_METHODS = {"decoded_frame", "pts_sample", "manual_frame_input", "browser_seek", "unknown"}
EXACT_METHODS = {"decoded_frame"}
FRAME_TOLERANCE = 0.5          # half a frame of slack for a recorded estimate


class ExportError(ValueError):
    """Malformed export document."""


def is_finite_number(v) -> bool:
    return (not isinstance(v, bool)) and isinstance(v, (int, float)) and math.isfinite(v)


def is_frame(v) -> bool:
    return (not isinstance(v, bool)) and isinstance(v, int) and math.isfinite(v)


def decode_sentinel(v):
    """Decode the sentinel strings used by boundary_cases.json (NaN/Infinity/bool)."""
    if not isinstance(v, list):
        return v
    out = []
    for item in v:
        if isinstance(item, str):
            token = item.strip()
            out.append({"NaN": float("nan"), "Infinity": float("inf"),
                        "-Infinity": float("-inf"), "true": True, "false": False}
                       .get(token, None) if token in ("NaN", "Infinity", "-Infinity", "true",
                                                      "false") else float(token))
        else:
            out.append(item)
    return out


def box_height(w: float, sample: dict) -> float:
    return w * sample["target_ratio_wh"][1] / sample["target_ratio_wh"][0]


def time_from_frame(frame: int, sample: dict) -> float:
    return frame / sample["fps"]


def box_problems(box, sample: dict, where: str) -> list:
    out = []
    if not isinstance(box, list) or len(box) != 3:
        return [f"{where}: box must be a three-element [x, y, w]"]
    for name, v in zip("xyw", box):
        if isinstance(v, bool) or isinstance(v, str) or not is_finite_number(v):
            out.append(f"{where}: {name} must be a finite number (got {v!r})")
    if out:
        return out
    x, y, w = box
    if x < 0 or y < 0:
        out.append(f"{where}: x and y must be >= 0")
    if w <= 0:
        out.append(f"{where}: w must be > 0")
    h = box_height(w, sample)
    if w > sample["max_legal_crop"]["max_width"] + 1e-6:
        out.append(f"{where}: w={w} exceeds the max legal width "
                   f"{sample['max_legal_crop']['max_width']:.4f}")
    if x + w > sample["source_width"] + 1e-6 or y + h > sample["source_height"] + 1e-6:
        out.append(f"{where}: box [{x}, {y}, {w}] with derived h={h:.2f} leaves the "
                   f"{sample['source_width']}x{sample['source_height']} frame")
    return out


def locator_problems(loc, where: str, allowed_frames):
    problems, warnings = [], []
    if not isinstance(loc, dict):
        return [f"{where}: missing provenance record"], warnings
    if loc.get("method") not in LOCATOR_METHODS:
        problems.append(f"{where}: unknown locator method {loc.get('method')!r}")
    frame = loc.get("frame")
    if not is_frame(frame):
        problems.append(f"{where}: provenance must record the displayed frame it used")
    elif allowed_frames is not None and frame not in allowed_frames:
        problems.append(f"{where}: provenance frame {frame} is not one of "
                        f"{list(allowed_frames)} for this boundary")
    method = loc.get("method")
    if method == "decoded_frame":
        if not is_frame(loc.get("decoded_index")):
            problems.append(f"{where}: decoded index missing")
        if not is_finite_number(loc.get("decoded_pts_sec")):
            problems.append(f"{where}: decoded PTS missing")
        if not loc.get("image_sha256"):
            problems.append(f"{where}: decoded frame image hash missing")
        if loc.get("decoded_index") != frame:
            problems.append(f"{where}: decoded index {loc.get('decoded_index')} != "
                            f"provenanced frame {frame}")
    if method == "pts_sample" and not is_frame(loc.get("pts_sample_index")):
        problems.append(f"{where}: pts sample index missing")
    if method == "browser_seek" and loc.get("verified") is True:
        problems.append(f"{where}: a browser seek cannot be marked verified")
    err = loc.get("estimated_error_frames")
    if err is not None and not is_finite_number(err):
        problems.append(f"{where}: estimated_error_frames must be a number or null")
    if method not in EXACT_METHODS and err == 0:
        problems.append(f"{where}: only a media-verified locator "
                        f"({sorted(EXACT_METHODS)}) may claim an exact position (error 0); "
                        f"use null when the error is unknown")
    return problems, warnings


def derive_mode(state: str, ann: dict, valid: bool, sample_id: str) -> dict:
    if state == "UNANNOTATED":
        return {"mode": "NOT_EXPORTABLE", "reason": "尚未标注；未标注不等于空参考", "reference": None}
    if state == "UNCERTAIN":
        return {"mode": "NOT_EXPORTABLE", "reason": "标注者标记为不确定", "reference": None}
    if state == "NO_HIGHLIGHT":
        if not ann.get("confirm_no_highlight"):
            return {"mode": "NOT_EXPORTABLE", "reason": "无高光需标注者显式确认", "reference": None}
        if not valid:
            return {"mode": "BLOCKED_BY_VALIDATION",
                    "reason": "校验未通过（例如仍残留区间/关键帧），不允许导出空参考",
                    "reference": None}
        return {"mode": "NO_HIGHLIGHT_EMPTY_GT",
                "reason": "确认无高光：空帧集合（coverage=full, frames=[]）",
                "reference": {"coverage": "full",
                              "videos": [{"video_id": sample_id, "coverage": "full", "frames": []}]}}
    if state == "HAS_HIGHLIGHT":
        if not valid:
            return {"mode": "BLOCKED_BY_VALIDATION", "reason": "校验未通过，不允许导出参考",
                    "reference": None}
        intervals = ann.get("intervals") or []
        keyframes = ann.get("keyframes") or []
        if not intervals:
            return {"mode": "NOT_EXPORTABLE", "reason": "状态为有高光但没有时间区间",
                    "reference": None}
        if not keyframes:
            return {"mode": "TEMPORAL_ONLY",
                    "reason": "只有时间区间、没有构图关键帧：仅可做时间诊断",
                    "reference": None}
        return {"mode": "SPARSE_KEYFRAME_GT",
                "reason": "稀疏构图关键帧：coverage=sparse（只有列出的帧被标注）",
                "reference": {"coverage": "sparse",
                              "videos": [{"video_id": sample_id, "coverage": "sparse",
                                          "frames": [{"frame": kf["frame"], "box_xyw": kf["box_xyw"]}
                                                     for kf in keyframes]}]}}
    return {"mode": "NOT_EXPORTABLE", "reason": "unknown state", "reference": None}


def validate_annotation(sample: dict, ann: dict) -> dict:
    """Validate one sample's annotation (same order and wording as the JS core)."""
    problems, warnings = [], []
    state = (ann or {}).get("status")
    if state not in STATES:
        problems.append(f"unknown annotation_status {state!r}")
    intervals = (ann or {}).get("intervals")
    keyframes = (ann or {}).get("keyframes")
    n = sample["n_frames"]

    if state in ("UNANNOTATED", "UNCERTAIN"):
        if intervals is not None:
            problems.append(f"{state} must not carry intervals (unannotated is not empty)")
        if keyframes is not None:
            problems.append(f"{state} must not carry keyframes")
    if state == "NO_HIGHLIGHT":
        if not ann.get("confirm_no_highlight"):
            problems.append("NO_HIGHLIGHT requires the explicit confirmation checkbox")
        if (intervals or []) or (keyframes or []):
            problems.append("NO_HIGHLIGHT conflicts with the remaining intervals/keyframes; "
                            "clear them explicitly or switch the status back "
                            "(nothing is discarded silently)")
    if state == "HAS_HIGHLIGHT" and not intervals:
        problems.append("HAS_HIGHLIGHT requires at least one interval")

    seen_intervals = set()
    for i, iv in enumerate(intervals or []):
        where = f"interval {i}"
        if not isinstance(iv, dict):
            problems.append(f"{where}: must be an object")
            continue
        s, e = iv.get("start_frame"), iv.get("end_frame_exclusive")
        if iv.get("end_frame") is not None and e is None:
            problems.append(f"{where}: legacy closed-end field without semantics; "
                            f"refusing to convert")
            continue
        if not is_frame(s):
            problems.append(f"{where}: start_frame must be an integer")
        if not is_frame(e):
            problems.append(f"{where}: end_frame_exclusive must be an integer")
        if is_frame(s) and is_frame(e):
            if not (0 <= s < e <= n):
                problems.append(f"{where}: require 0 <= start_frame < end_frame_exclusive <= {n} "
                                f"(got [{s}, {e}))")
            key = (s, e)
            if key in seen_intervals:
                problems.append(f"{where}: duplicate interval [{s}, {e})")
            seen_intervals.add(key)
        p, w = locator_problems(iv.get("start_provenance"), f"{where} start",
                                [s] if is_frame(s) else None)
        problems += p
        warnings += w
        p, w = locator_problems(iv.get("end_provenance"), f"{where} end",
                                [e - 1] if is_frame(e) else None)
        problems += p
        warnings += w
        if is_frame(s) and is_finite_number(iv.get("start_sec")):
            err = abs(iv["start_sec"] - time_from_frame(s, sample)) * sample["fps"]
            if err > FRAME_TOLERANCE:
                problems.append(f"{where}: start_sec deviates {err:.2f} frames from the frame number")
        if is_frame(e) and is_finite_number(iv.get("end_sec")):
            err = abs(iv["end_sec"] - time_from_frame(e, sample)) * sample["fps"]
            if err > FRAME_TOLERANCE:
                problems.append(f"{where}: end_sec deviates {err:.2f} frames from the frame number")
        if is_frame(e) and e == n:
            warnings.append(f"{where}: end_frame_exclusive equals n_frames, covering the last frame")

    seen_frames = set()
    for i, kf in enumerate(keyframes or []):
        where = f"keyframe {i}"
        if not isinstance(kf, dict):
            problems.append(f"{where}: must be an object")
            continue
        frame = kf.get("frame")
        if not is_frame(frame):
            problems.append(f"{where}: frame must be an integer")
        else:
            if not (0 <= frame < n):
                problems.append(f"{where}: frame {frame} outside 0..{n - 1}")
            if frame in seen_frames:
                problems.append(f"{where}: duplicate keyframe for frame {frame}")
            seen_frames.add(frame)
        problems += box_problems(kf.get("box_xyw"), sample, where)
        p, w = locator_problems(kf.get("provenance"), where, [frame] if is_frame(frame) else None)
        problems += p
        warnings += w

    annotator = (ann or {}).get("annotator")
    if not (isinstance(annotator, str) and annotator.strip()):
        problems.append("annotator must be recorded")

    valid = not problems
    mode = derive_mode(state, ann or {}, valid, sample["sample_id"])
    return {"valid": valid, "problems": problems, "warnings": warnings,
            "mode": mode["mode"], "reason": mode["reason"],
            "reference": mode["reference"] if valid else None}


def sample_by_id(manifest: dict, sample_id: str) -> dict:
    for sample in manifest["samples"]:
        if sample["sample_id"] == sample_id:
            return sample
    raise ExportError(f"unknown sample_id {sample_id!r}")


def validate_export(export: dict, manifest: dict) -> dict:
    """Validate a v2 export document (never silently repairs anything)."""
    problems = []
    if export.get("schema") != EXPORT_SCHEMA:
        problems.append(f"unexpected schema {export.get('schema')!r} "
                        f"(v1 exports have closed interval ends and are refused, not converted)")
    if export.get("core_version") != CORE_VERSION:
        problems.append(f"core_version {export.get('core_version')!r} != {CORE_VERSION}")
    if export.get("interval_semantics") != INTERVAL_SEMANTICS:
        problems.append(f"interval_semantics {export.get('interval_semantics')!r} != "
                        f"{INTERVAL_SEMANTICS}")
    if export.get("seconds_semantics") != "nominal_frame_over_manifest_fps_not_decoded_pts":
        problems.append("seconds_semantics must identify frame/fps as nominal, not decoded PTS")
    sample = None
    try:
        sample = sample_by_id(manifest, export.get("sample_id"))
    except ExportError as exc:
        problems.append(str(exc))
    if sample is not None:
        media = export.get("media") or {}
        if media.get("sha256") != sample["sha256_local"]:
            problems.append("media sha256 does not match the manifest")
        if media.get("target_ratio_wh") != sample["target_ratio_wh"]:
            problems.append("target ratio does not match the manifest")
        annotation = {"status": export.get("annotation_status"),
                      "confirm_no_highlight": export.get("confirm_no_highlight"),
                      "intervals": export.get("intervals"),
                      "keyframes": export.get("keyframes"),
                      "annotator": (export.get("identity") or {}).get("annotator")}
        verdict = validate_annotation(sample, annotation)
        problems += verdict["problems"]
    valid = not problems
    reference = None
    mode = "INVALID_EXPORT"
    reason = "export document failed validation; no reference is produced"
    if valid and sample is not None:
        derived = derive_mode(export.get("annotation_status"),
                              {"confirm_no_highlight": export.get("confirm_no_highlight"),
                               "intervals": export.get("intervals"),
                               "keyframes": export.get("keyframes")}, True, sample["sample_id"])
        mode, reason = derived["mode"], derived["reason"]
        reference = derived["reference"]
        if reference and reference["coverage"] == "sparse":
            for video in reference["videos"]:
                if not all("frame" in f and "box_xyw" in f for f in video["frames"]):
                    problems.append("sparse reference contains an incomplete frame entry")
        if export.get("exportable_as_reference") and reference is None:
            problems.append("export claims exportable_as_reference but produced no reference")
    return {"sample_id": export.get("sample_id"), "valid": not problems, "problems": problems,
            "mode": mode, "reason": reason, "reference": None if problems else reference}


def draft_problems(draft: dict, manifest: dict) -> list:
    problems = []
    if not isinstance(draft, dict):
        return ["draft is not an object"]
    if draft.get("schema") != DRAFT_SCHEMA:
        problems.append(f"unexpected draft schema {draft.get('schema')!r}")
    if draft.get("core_version") != CORE_VERSION:
        problems.append(f"draft core_version {draft.get('core_version')!r} != {CORE_VERSION}")
    if draft.get("interval_semantics") != INTERVAL_SEMANTICS:
        problems.append("draft interval semantics cannot be converted automatically; refusing to guess")
    draft_manifest = draft.get("manifest")
    if not isinstance(draft_manifest, dict):
        problems.append("draft manifest must be an object")
        draft_manifest = {}
    digest = draft_manifest.get("sample_digest")
    expected = "|".join(f"{s['sample_id']}:{s['sha256_local']}" for s in manifest["samples"])
    if digest != expected:
        problems.append("draft was written for a different media manifest (identity mismatch)")
    if (draft_manifest.get("schema") != manifest.get("schema") or
            draft_manifest.get("run_id") != manifest.get("run_id")):
        problems.append("draft manifest schema/run_id mismatch")
    entries = draft.get("annotations")
    if not isinstance(entries, list):
        return problems + ["draft annotations must be an array"]
    known = {s["sample_id"]: s for s in manifest["samples"]}
    seen = set()
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append(f"draft annotation entry {i} must be an object")
            continue
        sid = entry.get("sample_id")
        if not isinstance(sid, str):
            problems.append(f"draft annotation entry {i} needs a string sample_id")
            continue
        if sid in seen:
            problems.append(f"duplicate sample_id {sid}")
        seen.add(sid)
        if sid not in known:
            problems.append(f"draft has unknown sample {sid}")
            continue
        if entry.get("media_sha256") != known[sid]["sha256_local"]:
            problems.append(f"draft media hash mismatch for {sid}")
        ann = entry.get("annotation")
        if ann is None:
            continue
        if not isinstance(ann, dict):
            problems.append(f"{sid}: annotation must be an object or null")
            continue
        if "status" in ann and not isinstance(ann["status"], str):
            problems.append(f"{sid}: status must be a string")
        for field in ("annotator", "reviewer", "notes"):
            if ann.get(field) is not None and not isinstance(ann[field], str):
                problems.append(f"{sid}: {field} must be a string or null")
        for field in ("intervals", "keyframes"):
            if ann.get(field) is not None and not isinstance(ann[field], list):
                problems.append(f"{sid}: {field} must be an array or null")
        for j, iv in enumerate(ann.get("intervals") if isinstance(ann.get("intervals"), list) else []):
            if not isinstance(iv, dict):
                problems.append(f"{sid} interval {j} must be an object")
                continue
            for field in ("start_provenance", "end_provenance"):
                if iv.get(field) is not None and not isinstance(iv[field], dict):
                    problems.append(f"{sid} interval {j}: {field} must be an object or null")
            if "end_frame" in iv and "end_frame_exclusive" not in iv:
                problems.append(f"{sid} interval {j}: legacy closed-end field without semantics; "
                                f"refusing to convert")
        for j, kf in enumerate(ann.get("keyframes") if isinstance(ann.get("keyframes"), list) else []):
            if not isinstance(kf, dict):
                problems.append(f"{sid} keyframe {j} must be an object")
            else:
                if not isinstance(kf.get("box_xyw"), list) or len(kf["box_xyw"]) != 3:
                    problems.append(f"{sid} keyframe {j}: box_xyw must be a three-element array")
                if kf.get("provenance") is not None and not isinstance(kf["provenance"], dict):
                    problems.append(f"{sid} keyframe {j}: provenance must be an object or null")
    return problems


def run_cases(manifest: dict, cases_path: Path) -> dict:
    doc = json.loads(cases_path.read_text(encoding="utf-8"))
    sample = sample_by_id(manifest, doc["sample_id"])
    results = []
    for case in doc["cases"]:
        ann = json.loads(json.dumps(case["annotation"]))
        for kf in ann.get("keyframes") or []:
            if "box_xyw" in kf:
                kf["box_xyw"] = decode_sentinel(kf["box_xyw"])
        verdict = validate_annotation(sample, ann)
        got = {"valid": verdict["valid"], "mode": verdict["mode"],
               "reference": verdict["reference"] is not None}
        expect = case["expect"]
        results.append({"id": case["id"], "why": case.get("why"), "expect": expect, "got": got,
                        "problems": verdict["problems"],
                        "pass": got == {"valid": expect["valid"], "mode": expect["mode"],
                                        "reference": expect["reference"]}})
    return {"schema": "p1b_boundary_results_python_v1", "core_version": CORE_VERSION,
            "cases": len(results), "passed": sum(1 for r in results if r["pass"]),
            "failed": [r["id"] for r in results if not r["pass"]], "results": results}


def compare_with_js(py: dict, js: dict) -> dict:
    py_by_id = {r["id"]: r for r in py.get("results", [])}
    js_by_id = {r["id"]: r for r in js.get("results", [])}
    divergences = []
    for case_id in sorted(set(py_by_id) | set(js_by_id)):
        a, b = py_by_id.get(case_id), js_by_id.get(case_id)
        if a is None or b is None:
            divergences.append({"id": case_id, "problem": "missing on one side",
                                "python": a is not None, "js": b is not None})
            continue
        fields = ("valid", "mode", "reference")
        va = {k: a["got"].get(k) for k in fields}
        vb = {k: b["got"].get(k) for k in fields}
        if va != vb:
            divergences.append({"id": case_id, "problem": "verdict mismatch",
                                "python": va, "js": vb,
                                "python_problems": a.get("problems"),
                                "js_problems": b.get("problems")})
        elif (a.get("problems") or []) and (b.get("problems") or []) and                 len(a["problems"]) != len(b["problems"]):
            divergences.append({"id": case_id, "problem": "same verdict but different problem count",
                                "python_problems": a["problems"], "js_problems": b["problems"]})
    return {"schema": "p1b_case_comparison_v1", "cases_python": len(py_by_id),
            "cases_js": len(js_by_id), "divergences": divergences,
            "identical": not divergences}


def write(path, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text[:2500])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_cases = sub.add_parser("cases")
    p_cases.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p_cases.add_argument("--cases", default=str(DEFAULT_CASES))
    p_cases.add_argument("--out", default=None)
    p_export = sub.add_parser("export")
    p_export.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p_export.add_argument("--export", required=True)
    p_export.add_argument("--out", default=None)
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--python", required=True)
    p_cmp.add_argument("--js", required=True)
    p_cmp.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p_cmp.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if args.command == "cases":
        result = run_cases(manifest, Path(args.cases))
        write(Path(args.out) if args.out else None, result)
        return 0 if not result["failed"] else 2
    if args.command == "export":
        export = json.loads(Path(args.export).read_text(encoding="utf-8"))
        result = validate_export(export, manifest)
        write(Path(args.out) if args.out else None, result)
        return 0 if result["valid"] else 2
    if args.command == "compare":
        py = json.loads(Path(args.python).read_text(encoding="utf-8"))
        js = json.loads(Path(args.js).read_text(encoding="utf-8"))
        result = compare_with_js(py, js)
        write(Path(args.out) if args.out else None, result)
        return 0 if result["identical"] else 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
