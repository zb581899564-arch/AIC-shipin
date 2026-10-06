#!/usr/bin/env python3
"""P1b: validate annotation exports and derive P1a-compatible references.

The rules implemented here mirror the JavaScript in ``annotate.html`` exactly
(same mode names, same conditions) so the page and this validator cannot drift
silently.  Nothing here invents annotations: an export is either consistent with
what a human recorded, or it is rejected.

Validated per export:
  * schema / sample identity / media hash must match the pilot manifest;
  * ``annotation_status`` must be one of the four states;
  * UNANNOTATED and UNCERTAIN must carry ``intervals = null`` and
    ``keyframes = null`` (未标注 != 空) and never yield a reference;
  * NO_HIGHLIGHT requires the explicit confirmation flag before it may export an
    empty ground-truth frame set;
  * HAS_HIGHLIGHT requires at least one interval; boxes must be inside the frame
    and satisfy ``h = w * th / tw``;
  * frame numbers must be integers inside ``0 .. n_frames-1``;
  * ``start_sec`` / ``end_sec`` must stay within one frame of ``frame / fps``;
  * an annotator is mandatory for a usable export; ``reviewer`` stays null unless
    a human is recorded.

Outputs: reports/round6_score_alignment/phase1b/tool_validation.json
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = ROOT / "round6_score_alignment/p1b"
PHASE1B = ROOT / "reports/round6_score_alignment/phase1b"
MANIFEST = P1B / "pilot_manifest.json"
OUT = PHASE1B / "tool_validation.json"

STATES = {"UNANNOTATED", "HAS_HIGHLIGHT", "NO_HIGHLIGHT", "UNCERTAIN"}
FRAME_TOLERANCE = 1.0 / 2.0          # half a frame of slack for a recorded estimate
SAMPLE_KEY = "P01"


class ExportError(ValueError):
    pass


def derive(export: dict) -> dict:
    """Mirror of buildExport() in annotate.html."""
    status = export.get("annotation_status")
    if status == "UNANNOTATED":
        return {"mode": "NOT_EXPORTABLE",
                "reason": "尚未标注；未标注不等于空参考", "reference": None}
    if status == "UNCERTAIN":
        return {"mode": "NOT_EXPORTABLE", "reason": "标注者标记为不确定", "reference": None}
    if status == "NO_HIGHLIGHT":
        if not export.get("confirm_no_highlight"):
            return {"mode": "NOT_EXPORTABLE",
                    "reason": "无高光需标注者显式确认", "reference": None}
        return {"mode": "NO_HIGHLIGHT_EMPTY_GT",
                "reason": "标注者确认整段无高光：空帧集合（coverage=full, frames=[]）",
                "reference": {"coverage": "full",
                              "videos": [{"video_id": export["sample_id"], "coverage": "full",
                                          "frames": []}]}}
    if status == "HAS_HIGHLIGHT":
        intervals = export.get("intervals")
        keyframes = export.get("keyframes")
        if not intervals:
            return {"mode": "NOT_EXPORTABLE", "reason": "状态为有高光但没有时间区间",
                    "reference": None}
        if not keyframes:
            return {"mode": "TEMPORAL_ONLY",
                    "reason": "只有时间区间、没有构图关键帧：仅可做时间诊断", "reference": None}
        return {"mode": "SPARSE_KEYFRAME_GT",
                "reason": "稀疏构图关键帧：coverage=sparse",
                "reference": {"coverage": "sparse",
                              "videos": [{"video_id": export["sample_id"], "coverage": "sparse",
                                          "frames": [{"frame": kf["frame"], "box_xyw": kf["box"]}
                                                     for kf in keyframes]}]}}
    raise ExportError(f"unknown annotation_status {status!r}")


def validate_export(export: dict, manifest: dict) -> dict:
    problems: list[str] = []
    sample = next((s for s in manifest["samples"] if s["sample_id"] == export.get("sample_id")),
                  None)
    if sample is None:
        raise ExportError(f"unknown sample_id {export.get('sample_id')!r}")
    if export.get("schema") != "p1b_annotation_export_v1":
        problems.append(f"unexpected schema {export.get('schema')!r}")
    if export.get("annotation_status") not in STATES:
        problems.append(f"invalid annotation_status {export.get('annotation_status')!r}")

    media = export.get("media") or {}
    if media.get("sha256") != sample["sha256_local"]:
        problems.append("media sha256 does not match the pilot manifest")
    if media.get("target_ratio_wh") != sample["target_ratio_wh"]:
        problems.append("target ratio does not match the pilot manifest")
    fps = sample["fps"]
    n_frames = sample["n_frames"]
    tw, th = sample["target_ratio_wh"]
    max_w = sample["max_legal_crop"]["max_width"]

    status = export.get("annotation_status")
    intervals = export.get("intervals")
    keyframes = export.get("keyframes")

    if status in ("UNANNOTATED", "UNCERTAIN"):
        if intervals is not None or keyframes is not None:
            problems.append("unannotated/uncertain export must keep intervals and keyframes null")
    if status == "NO_HIGHLIGHT" and not export.get("confirm_no_highlight"):
        problems.append("NO_HIGHLIGHT without the explicit confirmation flag")
    if status == "NO_HIGHLIGHT" and (intervals or keyframes):
        problems.append("NO_HIGHLIGHT must not carry intervals or keyframes")

    max_time_error_frames = 0.0
    for i, item in enumerate(intervals or []):
        for key in ("start_frame", "end_frame"):
            value = item.get(key)
            if isinstance(value, bool) or not isinstance(value, int):
                problems.append(f"interval {i}: {key} must be a non-bool integer")
            elif not 0 <= value < n_frames:
                problems.append(f"interval {i}: {key}={value} outside 0..{n_frames - 1}")
        if isinstance(item.get("start_frame"), int) and isinstance(item.get("end_frame"), int):
            if item["end_frame"] <= item["start_frame"]:
                problems.append(f"interval {i}: end must be greater than start")
        for fkey, skey in (("start_frame", "start_sec"), ("end_frame", "end_sec")):
            frame, sec = item.get(fkey), item.get(skey)
            if isinstance(frame, int) and isinstance(sec, (int, float)):
                expected = frame / fps
                err_frames = abs(sec - expected) * fps
                max_time_error_frames = max(max_time_error_frames, err_frames)
                if err_frames > FRAME_TOLERANCE:
                    problems.append(f"interval {i}: {skey}={sec} deviates "
                                    f"{err_frames:.2f} frames from {expected:.6f}")

    for i, kf in enumerate(keyframes or []):
        frame, box = kf.get("frame"), kf.get("box")
        if isinstance(frame, bool) or not isinstance(frame, int):
            problems.append(f"keyframe {i}: frame must be a non-bool integer")
        elif not 0 <= frame < n_frames:
            problems.append(f"keyframe {i}: frame={frame} outside 0..{n_frames - 1}")
        if not (isinstance(box, list) and len(box) == 3):
            problems.append(f"keyframe {i}: box must be a three-element [x, y, w]")
            continue
        x, y, w = box
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (x, y, w)):
            problems.append(f"keyframe {i}: box values must be numeric")
            continue
        if x < 0 or y < 0 or w <= 0:
            problems.append(f"keyframe {i}: box requires x>=0, y>=0, w>0")
        if w > max_w + 1e-6:
            problems.append(f"keyframe {i}: w={w} exceeds the max legal width {max_w:.4f}")
        h = w * th / tw
        if x + w > sample["source_width"] + 1e-6 or y + h > sample["source_height"] + 1e-6:
            problems.append(f"keyframe {i}: box [{x},{y},{w}] with derived h={h:.2f} "
                            f"leaves {sample['source_width']}x{sample['source_height']}")

    identity = export.get("identity") or {}
    annotator = identity.get("annotator")
    if export.get("exportable_as_reference") and not annotator:
        problems.append("an exportable annotation must record an annotator")
    if identity.get("reviewer") and not isinstance(identity["reviewer"], str):
        problems.append("reviewer must be a string or null")
    if export.get("label_status") != "WEAK_HUMAN_SPARSE_PENDING_REVIEW":
        problems.append("label_status must stay WEAK_HUMAN_SPARSE_PENDING_REVIEW until reviewed")

    derived = derive(export)
    return {
        "sample_id": export.get("sample_id"),
        "valid": not problems,
        "problems": problems,
        "derived_mode": derived["mode"],
        "derived_reason": derived["reason"],
        "max_time_mapping_error_frames": round(max_time_error_frames, 4),
        "reference": derived["reference"],
    }


# --------------------------------------------------------------------------- #
# synthetic fixtures
# --------------------------------------------------------------------------- #
def fixture(manifest: dict, sample_id: str, **overrides) -> dict:
    sample = next(s for s in manifest["samples"] if s["sample_id"] == sample_id)
    fps = sample["fps"]
    base = {
        "schema": "p1b_annotation_export_v1", "sample_id": sample_id,
        "source_group": sample["source_group"], "split": "pilot_dev",
        "media": {"file_name": sample["file_name"], "sha256": sample["sha256_local"],
                  "fps": fps, "n_frames": sample["n_frames"],
                  "source_width": sample["source_width"], "source_height": sample["source_height"],
                  "target_ratio_wh": sample["target_ratio_wh"]},
        "annotation_status": "UNANNOTATED", "confirm_no_highlight": False,
        "intervals": None, "keyframes": None,
        "frame_provenance": {"frame_source": "pts_sample", "estimated_error_frames": 0},
        "identity": {"annotator": "SYNTHETIC_TEST_ANNOTATOR", "reviewer": None},
        "notes": "synthetic fixture for tool validation; not a real annotation",
        "exportable_as_reference": False,
        "label_status": "WEAK_HUMAN_SPARSE_PENDING_REVIEW",
    }
    base.update(overrides)
    return base


def p1a_integration_reference(reference: dict, universe: tuple[str, ...] = ("P01",)) -> dict:
    """Feed a derived reference through the real P1a loader/scorer.

    ``universe`` is the scored video set and is deliberately INDEPENDENT of the
    reference: building the index from the reference alone would shrink the scored
    set to whatever the annotation happened to cover and would hide a missing-GT
    situation behind a spuriously complete comparison.
    """
    sys.path.insert(0, str(ROOT / "round6_score_alignment/p1a"))
    sys.dont_write_bytecode = True
    from aic6 import scoring

    with tempfile.TemporaryDirectory(prefix="p1b_p1a_") as tmp:
        tmp_path = Path(tmp)
        index = {vid: {"video_id": vid, "targetRatioWH": [16.0, 9.0], "width": 534, "height": 300,
                       "n_frames": 1000, "video_path": "synthetic"} for vid in universe}
        ref_path = tmp_path / "reference.json"
        ref_path.write_text(json.dumps({
            "schema": "aic_round6_reference_v1",
            "coverage": reference["coverage"],
            "label_status": "WEAK_HUMAN_SPARSE_PENDING_REVIEW",
            "annotation_source": "P1b annotation export (synthetic fixture)",
            "videos": reference["videos"]}, ensure_ascii=False), encoding="utf-8")
        loaded = scoring.load_reference(ref_path, index)
        predictions_rows = []
        for vid in index:
            predictions_rows.append({"video_id": vid, "targetRatioWH": [16, 9], "predictions": []})
        pred_path = tmp_path / "predictions.jsonl"
        pred_path.write_text("\n".join(json.dumps(r) for r in predictions_rows) + "\n",
                             encoding="utf-8")
        prediction_set = scoring.load_predictions(pred_path, index)
        result = scoring.score_joint(predictions=prediction_set, reference=loaded, index=index)
    return {"status": result["status"], "score": result["score"],
            "score_present": result["score"] is not None}


def static_html_checks() -> dict:
    html = (P1B / "annotate.html").read_text(encoding="utf-8")
    # Network *APIs* are forbidden; URL strings inside the embedded provenance JSON are
    # recorded references, not requests.  Remote sub-resources are forbidden too.
    api_tokens = ["fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon",
                  "import(", "serviceWorker"]
    remote_resource_tokens = ['<script src=', '<link ', '<img src="http', '<video src="http',
                              'srcset=', '<iframe']
    found_apis = [t for t in api_tokens if t in html]
    found_remote = [t for t in remote_resource_tokens if t in html]
    url_strings = html.count("https://") + html.count("http://")
    return {
        "bytes": len(html.encode("utf-8")),
        "contains_manifest": "const MANIFEST = {" in html,
        "samples_embedded": html.count('"sample_id"'),
        "no_network_apis": not found_apis,
        "no_remote_subresources": not found_remote,
        "forbidden_tokens_found": found_apis + found_remote,
        "url_strings_in_embedded_data_only": url_strings,
        "url_strings_note": ("URLs appear only as recorded provenance text inside the embedded "
                             "manifest JSON; the page issues no request"),
        "media_srcs_are_relative": 'media_rel_path' in html and 'v.src = s.media_rel_path' in html,
        "has_status_selector": 'value="UNANNOTATED"' in html and 'value="NO_HIGHLIGHT"' in html,
        "has_confirm_checkbox": 'id="confirmNoHighlight"' in html,
        "has_pts_samples": "verified_sample_frames" in html,
        "has_ratio_constraint": "max_legal_crop" in html,
        "exports_only_annotated": "annotation_status !== \"UNANNOTATED\"" in html,
        "reviewer_not_autofilled": 'reviewer: null' in html,
    }


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sample_id = SAMPLE_KEY
    s = next(x for x in manifest["samples"] if x["sample_id"] == sample_id)
    good_box = [0, 0, 320]
    cases = {
        "T1_unannotated_is_not_empty": fixture(manifest, sample_id),
        "T2_no_highlight_without_confirmation": fixture(
            manifest, sample_id, annotation_status="NO_HIGHLIGHT", confirm_no_highlight=False),
        "T3_no_highlight_confirmed_exports_empty_gt": fixture(
            manifest, sample_id, annotation_status="NO_HIGHLIGHT", confirm_no_highlight=True,
            exportable_as_reference=True),
        "T4_sparse_keyframes_export_sparse": fixture(
            manifest, sample_id, annotation_status="HAS_HIGHLIGHT",
            intervals=[{"start_frame": 10, "end_frame": 20, "start_sec": 10 / s["fps"],
                        "end_sec": 20 / s["fps"]}],
            keyframes=[{"frame": 12, "box": good_box}], exportable_as_reference=True),
        "T5_intervals_without_keyframes_is_temporal_only": fixture(
            manifest, sample_id, annotation_status="HAS_HIGHLIGHT",
            intervals=[{"start_frame": 10, "end_frame": 20, "start_sec": 10 / s["fps"],
                        "end_sec": 20 / s["fps"]}]),
        "T6_box_out_of_bounds_is_rejected": fixture(
            manifest, sample_id, annotation_status="HAS_HIGHLIGHT",
            intervals=[{"start_frame": 1, "end_frame": 2, "start_sec": 1 / s["fps"],
                        "end_sec": 2 / s["fps"]}],
            keyframes=[{"frame": 1, "box": [1000, 0, 320]}], exportable_as_reference=True),
        "T7_width_above_max_legal_is_rejected": fixture(
            manifest, sample_id, annotation_status="HAS_HIGHLIGHT",
            intervals=[{"start_frame": 1, "end_frame": 2, "start_sec": 1 / s["fps"],
                        "end_sec": 2 / s["fps"]}],
            keyframes=[{"frame": 1, "box": [0, 0, 534]}], exportable_as_reference=True),
        "T8_estimated_time_mismatch_is_flagged": fixture(
            manifest, sample_id, annotation_status="HAS_HIGHLIGHT",
            intervals=[{"start_frame": 10, "end_frame": 20, "start_sec": 0.0,
                        "end_sec": 1.0}],
            keyframes=[{"frame": 12, "box": good_box}], exportable_as_reference=True),
        "T9_missing_annotator_is_rejected": fixture(
            manifest, sample_id, annotation_status="HAS_HIGHLIGHT",
            intervals=[{"start_frame": 1, "end_frame": 2, "start_sec": 1 / s["fps"],
                        "end_sec": 2 / s["fps"]}],
            keyframes=[{"frame": 1, "box": good_box}], identity={"annotator": None, "reviewer": None},
            exportable_as_reference=True),
        "T10_uncertain_is_not_exported": fixture(
            manifest, sample_id, annotation_status="UNCERTAIN"),
    }
    results = {name: validate_export(export, manifest) for name, export in cases.items()}

    expectations = {
        "T1_unannotated_is_not_empty": ("NOT_EXPORTABLE", True),
        "T2_no_highlight_without_confirmation": ("NOT_EXPORTABLE", False),
        "T3_no_highlight_confirmed_exports_empty_gt": ("NO_HIGHLIGHT_EMPTY_GT", True),
        "T4_sparse_keyframes_export_sparse": ("SPARSE_KEYFRAME_GT", True),
        "T5_intervals_without_keyframes_is_temporal_only": ("TEMPORAL_ONLY", True),
        "T6_box_out_of_bounds_is_rejected": ("SPARSE_KEYFRAME_GT", False),
        "T7_width_above_max_legal_is_rejected": ("SPARSE_KEYFRAME_GT", False),
        "T8_estimated_time_mismatch_is_flagged": ("SPARSE_KEYFRAME_GT", False),
        "T9_missing_annotator_is_rejected": ("SPARSE_KEYFRAME_GT", False),
        "T10_uncertain_is_not_exported": ("NOT_EXPORTABLE", True),
    }
    checks = []
    for name, (mode, valid) in expectations.items():
        got = results[name]
        checks.append({"case": name, "expected_mode": mode, "got_mode": got["derived_mode"],
                       "expected_valid": valid, "got_valid": got["valid"],
                       "pass": got["derived_mode"] == mode and got["valid"] == valid,
                       "problems": got["problems"][:3]})
    for name in ("T2_no_highlight_without_confirmation", "T6_box_out_of_bounds_is_rejected",
                 "T7_width_above_max_legal_is_rejected", "T9_missing_annotator_is_rejected"):
        assert results[name]["problems"], f"{name} must report a problem"
    for name in ("T1_unannotated_is_not_empty", "T10_uncertain_is_not_exported"):
        assert results[name]["reference"] is None, f"{name} must not produce a reference"

    integration = {
        "confirmed_no_highlight_through_p1a": p1a_integration_reference(
            results["T3_no_highlight_confirmed_exports_empty_gt"]["reference"]),
        "sparse_keyframes_through_p1a": p1a_integration_reference(
            results["T4_sparse_keyframes_export_sparse"]["reference"]),
    }
    integration["confirmed_no_highlight_through_p1a"]["expected"] = "OK with score 100 (both empty)"
    integration["sparse_keyframes_through_p1a"]["expected"] = "SPARSE_DIAGNOSTIC with score null"

    # An unannotated sample must never be turned into an empty ground truth.  The sharpest
    # end-to-end check: a FULL-coverage reference that mentions only the annotated sample must
    # be refused by the scorer instead of scoring the other sample as "empty ground truth".
    incomplete_full = {"coverage": "full",
                       "videos": [{"video_id": sample_id, "coverage": "full", "frames": []}]}
    integration["incomplete_full_reference_is_refused"] = {
        "note": "derived from a bundle where P02 is still UNANNOTATED; a full reference that "
                "omits P02 must not be scored (missing coverage), never treated as empty GT",
        "universe": ["P01", "P02"],
        "p1a_result": p1a_integration_reference(incomplete_full, universe=("P01", "P02"))}
    # And the sparse path for the same situation must stay score-less and diagnostic-only.
    two_video_sparse = {"coverage": "sparse",
                        "videos": [{"video_id": sample_id, "coverage": "sparse",
                                    "frames": [{"frame": 12, "box_xyw": good_box}]},
                                   {"video_id": "P02", "coverage": "sparse", "frames": []}]}
    integration["unannotated_video_in_sparse_bundle_yields_no_score"] = {
        "note": "P02 carries no annotated frames; the sparse branch must not invent a score",
        "universe": ["P01", "P02"],
        "p1a_result": p1a_integration_reference(two_video_sparse, universe=("P01", "P02"))}

    result = {
        "schema": "p1b_tool_validation_v1",
        "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "rules_mirror": "derive()/validate_export() mirror buildExport() in annotate.html",
        "cases": checks,
        "all_cases_pass": all(c["pass"] for c in checks),
        "case_details": results,
        "p1a_integration": integration,
        "static_html_checks": static_html_checks(),
        "synthetic_media": json.loads(
            (P1B / "synthetic/synthetic_manifest.json").read_text(encoding="utf-8")),
        "ui_rendering_evidence": "see REPORT.md (browser/UI rendering status)",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_cases_pass": result["all_cases_pass"],
                      "cases": [{c["case"]: c["pass"]} for c in checks],
                      "p1a_integration": integration,
                      "static_html_checks": result["static_html_checks"]},
                     ensure_ascii=False, indent=1))
    return 0 if result["all_cases_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
