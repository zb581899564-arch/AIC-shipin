#!/usr/bin/env python3
"""Replay the supervisor's P1a reproductions against whatever the code currently does.

This script *records* behaviour; it does not assert.  Running it before and after
the fix produces the before/after evidence pair required by the fix handoff.

Cases (from reports/round6_score_alignment/SUPERVISOR_P1A_REVIEW.md):
  C1  single video, legal empty prediction, full reference record without "frames"
  C2  duplicate video_id where the second record re-declares empty frames
  C3  sparse reference: which per-video fields are exposed
  C4  traceable composition: is there a top-level status / deliverability flag
  C5  declared distance limit: does it accept NaN / Infinity / bool / float
  C6  provenance naming for the within-shot copy

Usage:
    python round6_score_alignment/p1a/repro_supervisor_cases.py --out <path.json>
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import scoring  # noqa: E402
from aic6.compose import (  # noqa: E402
    CompositionError, CompositionMode, ShotMap, WindowRequest, compose,
)
from aic6.segments import SegmentConstraint  # noqa: E402

INDEX = {
    "0": {"video_id": "0", "targetRatioWH": [16.0, 9.0], "width": 720, "height": 1280,
          "n_frames": 630, "video_path": "synthetic"},
}
BOX = [0, 0, 720]


def _write(tmp: Path, name: str, payload) -> Path:
    path = tmp / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def case_1_and_2(tmp: Path) -> dict:
    """Missing frames field / duplicate video_id must not yield OK 100."""
    out = {}
    preds = tmp / "p.jsonl"
    preds.write_text(json.dumps({"video_id": "0", "targetRatioWH": [16, 9],
                                 "predictions": []}) + "\n", encoding="utf-8")
    prediction_set = scoring.load_predictions(preds, INDEX)

    c1 = _write(tmp, "c1.json", {
        "schema": "aic_round6_reference_v1", "coverage": "full",
        "label_status": "SYNTHETIC", "annotation_source": "synthetic",
        "videos": [{"video_id": "0"}]})
    try:
        reference = scoring.load_reference(c1, INDEX)
        out["C1_missing_frames_field"] = scoring.score_joint(
            predictions=prediction_set, reference=reference, index=INDEX)
    except scoring.ReferenceError as exc:
        out["C1_missing_frames_field"] = {"raised": "ReferenceError", "message": str(exc)}

    c2 = _write(tmp, "c2.json", {
        "schema": "aic_round6_reference_v1", "coverage": "full",
        "label_status": "SYNTHETIC", "annotation_source": "synthetic",
        "videos": [{"video_id": "0", "frames": [{"frame": 0, "box_xyw": BOX}]},
                   {"video_id": "0", "frames": []}]})
    try:
        reference = scoring.load_reference(c2, INDEX)
        out["C2_duplicate_video_id"] = scoring.score_joint(
            predictions=prediction_set, reference=reference, index=INDEX)
    except scoring.ReferenceError as exc:
        out["C2_duplicate_video_id"] = {"raised": "ReferenceError", "message": str(exc)}
    return out


def case_3(tmp: Path) -> dict:
    preds = tmp / "p3.jsonl"
    preds.write_text(json.dumps({"video_id": "0", "targetRatioWH": [16, 9],
                                 "predictions": [{"frame": 5, "bboxes": BOX},
                                                 {"frame": 6, "bboxes": BOX}]}) + "\n",
                     encoding="utf-8")
    ref = _write(tmp, "c3.json", {
        "schema": "aic_round6_reference_v1", "coverage": "sparse",
        "label_status": "WEAK_HUMAN_SPARSE", "annotation_source": "sparse keyframes",
        "videos": [{"video_id": "0", "coverage": "sparse",
                    "frames": [{"frame": 5, "box_xyw": BOX}]}]})
    prediction_set = scoring.load_predictions(preds, INDEX)
    reference = scoring.load_reference(ref, INDEX)
    result = scoring.score_joint(predictions=prediction_set, reference=reference, index=INDEX)
    banned = {"precision", "recall", "f1", "time_precision", "time_recall", "time_f1",
              "unmatched_predictions", "missed_ground_truth", "both_empty", "one_side_empty",
              "n_pred", "n_gt"}
    leaked = sorted({k for row in result.get("per_video", []) for k in row} & banned)
    return {"status": result.get("status"), "score": result.get("score"),
            "per_video_fields": sorted(result.get("per_video", [{}])[0]) if result.get("per_video") else [],
            "full_video_fields_leaked": leaked,
            "sparse_block": result.get("sparse")}


def case_4(tmp: Path) -> dict:
    shots = ShotMap(shots_by_video={"0": ((0, 10), (10, 20), (20, 630))})
    gap_key = "max_shot_nearest_gap_frames" if _supports_new_name() else "max_interpolation_gap_frames"
    kwargs = dict(spatial_source={"0": {0: BOX, 1: BOX, 2: BOX, 3: BOX}},
                  fps_by_video={"0": 30.0}, n_frames_by_video={"0": 630},
                  constraint=SegmentConstraint(0, 5), mode=CompositionMode.TRACEABLE,
                  shot_map=shots, **{gap_key: 10})
    good_then_bad = compose(requests=[
        WindowRequest(video_id="0", index=0, start_sec=0.0, end_sec=11.0,
                      raw_output='{"segments":[[0.0,0.2]]}'),
        WindowRequest(video_id="0", index=1, start_sec=11.0, end_sec=22.0,
                      raw_output="not json at all")], **kwargs)
    empty_only = compose(requests=[
        WindowRequest(video_id="0", index=0, start_sec=0.0, end_sec=11.0,
                      raw_output='{"segments":[]}')], **kwargs)
    missing_spatial = compose(requests=[
        WindowRequest(video_id="0", index=0, start_sec=10.0, end_sec=21.0,
                      raw_output='{"segments":[[5.0,5.2]]}')],
        spatial_source={"0": {0: BOX, 1: BOX, 2: BOX, 3: BOX}},
        fps_by_video={"0": 30.0}, n_frames_by_video={"0": 630},
        constraint=SegmentConstraint(0, 5), mode=CompositionMode.TRACEABLE, shot_map=None)
    return {
        "one_good_one_bad": {"status": good_then_bad.get("status"),
                             "deliverable": good_then_bad.get("deliverable"),
                             "top_level_keys": sorted(good_then_bad),
                             "invalid_windows": good_then_bad["totals"]["invalid_windows"]},
        "empty_only": {"status": empty_only.get("status"),
                       "deliverable": empty_only.get("deliverable")},
        "missing_spatial": {"status": missing_spatial.get("status"),
                            "deliverable": missing_spatial.get("deliverable"),
                            "needs_spatial_inference": missing_spatial["totals"]["needs_spatial_inference"]},
    }


def case_5(tmp: Path) -> dict:
    """Which values does the declared distance limit accept?"""
    shots = ShotMap(shots_by_video={"0": ((0, 10), (10, 20), (20, 630))})
    key = "max_shot_nearest_gap_frames" if _supports_new_name() else "max_interpolation_gap_frames"
    results = {}
    for label, value in (("NaN", float("nan")), ("Infinity", float("inf")),
                         ("negative", -1), ("zero", 0), ("bool_true", True),
                         ("float", 1.5), ("string", "30")):
        try:
            report = compose(
                requests=[WindowRequest(video_id="0", index=0, start_sec=0.0, end_sec=11.0,
                                        raw_output='{"segments":[[0.0,0.2]]}')],
                spatial_source={"0": {0: BOX}}, fps_by_video={"0": 30.0},
                n_frames_by_video={"0": 630}, constraint=SegmentConstraint(0, 5),
                mode=CompositionMode.TRACEABLE, shot_map=shots, **{key: value})
            results[label] = {"accepted": True,
                              "needs_spatial_inference": report["totals"]["needs_spatial_inference"]}
        except CompositionError as exc:
            results[label] = {"accepted": False, "error": f"CompositionError: {str(exc)[:100]}"}
        except Exception as exc:  # noqa: BLE001 - the point is to record what happens
            results[label] = {"accepted": False, "error": f"{type(exc).__name__}: {str(exc)[:100]}"}
    return results


def _supports_new_name() -> bool:
    import inspect
    return "max_shot_nearest_gap_frames" in inspect.signature(compose).parameters


def case_6(tmp: Path) -> dict:
    shots = ShotMap(shots_by_video={"0": ((0, 10), (10, 20), (20, 630))})
    kwargs = dict(spatial_source={"0": {0: BOX, 1: BOX, 2: BOX, 3: BOX}},
                  fps_by_video={"0": 30.0}, n_frames_by_video={"0": 630},
                  constraint=SegmentConstraint(0, 5), mode=CompositionMode.TRACEABLE,
                  shot_map=shots)
    request = [WindowRequest(video_id="0", index=0, start_sec=0.0, end_sec=11.0,
                             raw_output='{"segments":[[0.0,0.2],[0.2,0.4]]}')]
    key = "max_shot_nearest_gap_frames" if _supports_new_name() else "max_interpolation_gap_frames"
    report = compose(requests=request, **{**kwargs, key: 10})
    blob = json.dumps(report, ensure_ascii=False)
    return {
        "provenance_values": sorted({f["provenance"] for f in report["videos"][0]["frames"]}),
        "totals_keys": sorted(report["totals"]),
        "mentions_old_name": "SOURCE_SHOT_INTERPOLATION" in blob,
        "mentions_interpolation_word": "interpolat" in blob.lower(),
        "uses_new_name": "SOURCE_SHOT_NEAREST" in blob,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="aic6_repro_") as tmpdir:
        tmp = Path(tmpdir)
        payload = {
            "note": "records actual behaviour of the current code; run before and after the fix",
            "cases": {},
        }
        payload["cases"].update(case_1_and_2(tmp))
        payload["cases"]["C3_sparse_fields"] = case_3(tmp)
        payload["cases"]["C4_composition_status"] = case_4(tmp)
        payload["cases"]["C5_distance_limit_type_validation"] = case_5(tmp)
        payload["cases"]["C6_provenance_naming"] = case_6(tmp)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
                   encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
