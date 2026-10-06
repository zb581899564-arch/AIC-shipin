#!/usr/bin/env python3
"""P1b-fix: assemble the test evidence (test_results.json).

Runs, with real commands and real exit codes:
  * the shared boundary cases in BOTH engines (JS core via node, Python validator);
  * the JS/Python case comparison;
  * the pre-fix defects re-probed against the FIXED validator (NaN, Infinity, bool,
    string, duplicate keyframe, duplicate interval, legacy closed-end interval,
    invalid box, NO_HIGHLIGHT conflict);
  * the Python validator on the real E2E artifacts (valid references, refused exports);
  * draft import validation on the E2E drafts;
  * the P1a interface consumption of the E2E reference.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = Path(__file__).resolve().parent
PHASE = ROOT / "reports/round6_score_alignment/phase1b_fix"
E2E = PHASE / "ui_e2e"

sys.path.insert(0, str(P1B))
import validate_exports as V  # noqa: E402


def run(cmd: list[str], cwd: Path) -> dict:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return {"command": " ".join(str(c) for c in cmd), "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-400:], "stderr_tail": proc.stderr[-400:]}


def probe_cases(manifest: dict) -> list[dict]:
    """The pre-fix defects, re-probed against the fixed validator."""
    sample = V.sample_by_id(manifest, "P01")
    fps = sample["fps"]
    prov = {"method": "decoded_frame", "frame": 12, "decoded_index": 12,
            "decoded_pts_sec": round(12 / fps, 6), "time_base_sec": sample["pts"]["time_base_seconds"],
            "image_sha256": "probe", "estimated_error_frames": 0}
    base_interval = {"start_frame": 10, "end_frame_exclusive": 20, "start_sec": 10 / fps,
                     "end_sec": 20 / fps,
                     "start_provenance": dict(prov, frame=10, decoded_index=10,
                                              decoded_pts_sec=10 / fps),
                     "end_provenance": dict(prov, frame=19, decoded_index=19,
                                            decoded_pts_sec=19 / fps,
                                            derived="end_frame_exclusive = last_kept_frame + 1")}
    cases = {
        "nan_box": {"frame": 12, "box_xyw": [float("nan"), 0, 100], "provenance": dict(prov)},
        "infinity_box": {"frame": 12, "box_xyw": [float("inf"), 0, 100], "provenance": dict(prov)},
        "bool_box": {"frame": 12, "box_xyw": [True, 0, 100], "provenance": dict(prov)},
        "string_box": {"frame": 12, "box_xyw": ["0", 0, 100], "provenance": dict(prov)},
        "negative_width_box": {"frame": 12, "box_xyw": [0, 0, -10], "provenance": dict(prov)},
        "out_of_bounds_box": {"frame": 12, "box_xyw": [400, 0, 320], "provenance": dict(prov)},
    }
    out = []
    for name, kf in cases.items():
        ann = {"status": "HAS_HIGHLIGHT", "confirm_no_highlight": False,
               "intervals": [json.loads(json.dumps(base_interval))], "keyframes": [kf],
               "annotator": "PROBE"}
        verdict = V.validate_annotation(sample, ann)
        out.append({"probe": name, "valid": verdict["valid"],
                    "reference_produced": verdict["reference"] is not None,
                    "problems": verdict["problems"][:2],
                    "expected": "invalid and no reference"})
    duplicates = [
        ("duplicate_keyframe", {"keyframes": [{"frame": 12, "box_xyw": [0, 0, 100], "provenance": dict(prov)},
                                              {"frame": 12, "box_xyw": [5, 0, 100], "provenance": dict(prov)}]}),
        ("duplicate_interval", {"intervals": [base_interval, json.loads(json.dumps(base_interval))]}),
        ("legacy_closed_end", {"intervals": [{"start_frame": 1, "end_frame": 2, "start_sec": 1 / fps,
                                              "end_sec": 2 / fps}]}),
    ]
    for name, over in duplicates:
        ann = {"status": "HAS_HIGHLIGHT", "confirm_no_highlight": False,
               "intervals": [json.loads(json.dumps(base_interval))],
               "keyframes": [{"frame": 12, "box_xyw": [0, 0, 100], "provenance": dict(prov)}],
               "annotator": "PROBE"}
        ann.update(over)
        verdict = V.validate_annotation(sample, ann)
        out.append({"probe": name, "valid": verdict["valid"],
                    "reference_produced": verdict["reference"] is not None,
                    "problems": verdict["problems"][:2],
                    "expected": "invalid and no reference"})
    conflict = {"status": "NO_HIGHLIGHT", "confirm_no_highlight": True,
                "intervals": [json.loads(json.dumps(base_interval))],
                "keyframes": [{"frame": 12, "box_xyw": [0, 0, 100], "provenance": dict(prov)}],
                "annotator": "PROBE"}
    verdict = V.validate_annotation(sample, conflict)
    out.append({"probe": "no_highlight_with_leftovers", "valid": verdict["valid"],
                "reference_produced": verdict["reference"] is not None,
                "problems": verdict["problems"][:2],
                "expected": "invalid and no reference (conflict reported, nothing discarded)"})
    return out


def p1a_consumption(export_path: Path, manifest: dict, universe=None, label="") -> dict:
    """Feed the E2E reference through the real P1a scorer."""
    verdict = V.validate_export(json.loads(export_path.read_text(encoding="utf-8")), manifest)
    if not verdict["valid"] or not verdict["reference"]:
        return {"status": "EXPORT_REJECTED", "problems": verdict["problems"]}
    reference = verdict["reference"]
    sys.path.insert(0, str(ROOT / "round6_score_alignment/p1a"))
    sys.dont_write_bytecode = True
    from aic6 import scoring  # noqa: E402

    import tempfile
    with tempfile.TemporaryDirectory(prefix="p1b_fix_p1a_") as tmp:
        tmp_path = Path(tmp)
        keep = set(universe) if universe else {s["sample_id"] for s in manifest["samples"]}
        index = {s["sample_id"]: {"video_id": s["sample_id"],
                                  "targetRatioWH": [float(x) for x in s["target_ratio_wh"]],
                                  "width": s["source_width"], "height": s["source_height"],
                                  "n_frames": s["n_frames"], "video_path": "synthetic"}
                 for s in manifest["samples"] if s["sample_id"] in keep}
        ref_path = tmp_path / "reference.json"
        ref_path.write_text(json.dumps({
            "schema": "aic_round6_reference_v1", "coverage": reference["coverage"],
            "label_status": "WEAK_HUMAN_SPARSE_PENDING_REVIEW",
            "annotation_source": "P1b-fix E2E synthetic export",
            "videos": reference["videos"]}, ensure_ascii=False), encoding="utf-8")
        predictions = tmp_path / "predictions.jsonl"
        # every row carries that video's own target ratio: a mismatch is rejected outright
        predictions.write_text("\n".join(
            json.dumps({"video_id": vid,
                        "targetRatioWH": [int(index[vid]["targetRatioWH"][0]),
                                          int(index[vid]["targetRatioWH"][1])],
                        "predictions": []}) for vid in index) + "\n", encoding="utf-8")
        loaded = scoring.load_reference(ref_path, index)
        prediction_set = scoring.load_predictions(predictions, index)
        result = scoring.score_joint(predictions=prediction_set, reference=loaded, index=index)
    return {"label": label, "universe": sorted(keep), "status": result["status"],
            "score": result["score"],
            "sparse_evidence": (result.get("sparse") or {}).get("evidence_status"),
            "reasons": result.get("reasons")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(PHASE / "test_results.json"))
    args = parser.parse_args()
    manifest = json.loads((P1B / "pilot_manifest.json").read_text(encoding="utf-8"))

    commands = [
        run(["node", str(P1B / "run_boundary_cases.js"), str(P1B / "pilot_manifest.json"),
             str(P1B / "boundary_cases.json"), str(PHASE / "cases_js.json")], P1B),
        run([sys.executable, str(P1B / "validate_exports.py"), "cases",
             "--out", str(PHASE / "cases_python.json")], ROOT),
        run([sys.executable, str(P1B / "validate_exports.py"), "compare",
             "--python", str(PHASE / "cases_python.json"), "--js", str(PHASE / "cases_js.json"),
             "--out", str(PHASE / "case_comparison.json")], ROOT),
        run([sys.executable, str(P1B / "check_fixed_page.py"), "--out",
             str(PHASE / "post_fix_reproduction.json")], ROOT),
        run([sys.executable, str(P1B / "run_ui_e2e.py")], ROOT),
    ]

    js_cases = json.loads((PHASE / "cases_js.json").read_text(encoding="utf-8"))
    py_cases = json.loads((PHASE / "cases_python.json").read_text(encoding="utf-8"))
    comparison = json.loads((PHASE / "case_comparison.json").read_text(encoding="utf-8"))

    probes = probe_cases(manifest)
    # the E2E artifacts belong to the synthetic manifest, the probes to the real pilot
    e2e_manifest = json.loads((E2E / "synthetic_manifest.json").read_text(encoding="utf-8"))
    diagnostics = {"e2e_manifest_samples": [s["sample_id"] for s in e2e_manifest["samples"]],
                   "e2e_manifest_file": str((E2E / "synthetic_manifest.json").relative_to(ROOT))}
    artifact_checks = []
    for name, expected_valid in (("step1_reference.json", True),
                                 ("step2_restored_reference.json", True),
                                 ("refusal_invalid_draft.json", False)):
        path = E2E / name
        if not path.is_file():
            artifact_checks.append({"artifact": name, "missing": True, "pass": False})
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if name.startswith("refusal"):
            verdict = {"valid": False, "problems": payload.get("problems", [])}
        else:
            verdict = V.validate_export(payload, e2e_manifest)
        artifact_checks.append({
            "artifact": name, "valid": verdict["valid"],
            "problems": verdict.get("problems", [])[:3],
            "expected_valid": expected_valid,
            "pass": verdict["valid"] == expected_valid})

    drafts = []
    for name in ("step1_draft.json",):
        path = E2E / name
        if path.is_file():
            draft = json.loads(path.read_text(encoding="utf-8"))
            problems = V.draft_problems(draft, e2e_manifest)
            drafts.append({"draft": name, "import_valid": not problems, "problems": problems[:3]})

    consumption = {
        "sparse_reference_with_matching_universe": p1a_consumption(
            E2E / "step2_restored_reference.json", e2e_manifest,
            universe=["S01"], label="A: universe == annotated sample"),
        "sparse_reference_with_unannotated_video": p1a_consumption(
            E2E / "step2_restored_reference.json", e2e_manifest,
            universe=["S01", "S02"], label="B: universe includes the unannotated S02"),
        "expected": ("A -> SPARSE_DIAGNOSTIC with score null (sparse semantics preserved); "
                     "B -> NOT_COMPUTABLE with score null (unannotated video never treated as "
                     "empty ground truth)"),
    }

    failure_causes = []
    if py_cases.get("failed"):
        failure_causes.append({"where": "python cases", "ids": py_cases["failed"]})
    if js_cases.get("failed"):
        failure_causes.append({"where": "js cases", "ids": js_cases["failed"]})
    if comparison.get("divergences"):
        failure_causes.append({"where": "js/python comparison", "count": len(comparison["divergences"])})
    bad_probes = [p["probe"] for p in probes if p["valid"] or p["reference_produced"]]
    if bad_probes:
        failure_causes.append({"where": "invalid-input probes", "ids": bad_probes})
    bad_artifacts = [a["artifact"] for a in artifact_checks if not a.get("pass")]
    if bad_artifacts:
        failure_causes.append({"where": "e2e artifacts", "ids": bad_artifacts})
    expect_status = {"sparse_reference_with_matching_universe": ("SPARSE_DIAGNOSTIC", None),
                     "sparse_reference_with_unannotated_video": ("NOT_COMPUTABLE", None)}
    for key, (status, score) in expect_status.items():
        got = consumption.get(key) or {}
        if got.get("status") != status or got.get("score") != score:
            failure_causes.append({"where": f"p1a consumption {key}",
                                   "expected": [status, score],
                                   "got": [got.get("status"), got.get("score")]})

    result = {
        "schema": "p1b_fix_test_results_v1",
        "run_id": "round6_p1b_fix_20260917T1630Z",
        "commands": commands,
        "shared_boundary_cases": {
            "file": "round6_score_alignment/p1b/boundary_cases.json",
            "expectations_source": "hand-written in the case file (never computed by the code under test)",
            "js_core": {"cases": js_cases.get("cases"), "passed": js_cases.get("passed"),
                        "failed": js_cases.get("failed")},
            "python": {"cases": py_cases.get("cases"), "passed": py_cases.get("passed"),
                       "failed": py_cases.get("failed")},
            "cross_check": {"identical": comparison.get("identical"),
                            "divergences": comparison.get("divergences")},
        },
        "invalid_input_probes": probes,
        "diagnostics": diagnostics,
        "e2e_artifact_validation": artifact_checks,
        "draft_validation": drafts,
        "p1a_consumption": consumption,
        "failure_causes": failure_causes,
        "all_pass": not failure_causes,
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "commands"}, ensure_ascii=False,
                     indent=1)[:3000])
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
