"""Round-6 P1a runner.

Executes, in order:

1. provenance verification of the vendored evaluator sources and of every
   protected historical input (hash pinned);
2. the hand-computed test suite (``tests/``) with a per-test outcome log;
3. the CPU historical replay: legacy rule reproduction of the 174-row round-5
   package, three-state parse consistency over the 203 recorded windows, the new
   time-convention frame-set difference, and the spatial-gap audit;
4. a second protected-input snapshot that must equal the first;
5. ``protocol.json``, ``test_results.json`` and ``replay_comparison.json``.

Usage (from the repository root):
    python round6_score_alignment/p1a/run_p1a.py
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
import unittest
from io import StringIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_OUT_DIR = ROOT / "reports/round6_score_alignment/phase1a_fix"
FIRST_P1A_DIR = ROOT / "reports/round6_score_alignment/phase1a"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import provenance, replay, scoring  # noqa: E402
from aic6.compose import ShotMap, load_spatial_source, load_windows  # noqa: E402
from aic6.segments import SegmentConstraint, check_label_cardinality, parse_response  # noqa: E402
from aic6.timebase import TimeConvention  # noqa: E402

RUN_ID = "round6_p1a_fix_20260917T0510Z"
WINDOW_CONSTRAINT = SegmentConstraint(0, 5)
# Illustrative *declared* limit for the single-whole-video-shot audit: 30 frames (about 1 s at
# 30 fps).  It is a round, pre-declared number, NOT fitted from any test statistic, and it is
# reported as an experiment, not as a recommended threshold.
DECLARED_ILLUSTRATIVE_GAP = 30


class OutcomeRecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes.append({"test": str(test), "status": "pass"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes.append({"test": str(test), "status": "fail",
                              "detail": self._exc_info_to_string(err, test).splitlines()[-1]})

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes.append({"test": str(test), "status": "error",
                              "detail": self._exc_info_to_string(err, test).splitlines()[-1]})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes.append({"test": str(test), "status": "skip", "detail": reason})


def run_tests() -> dict:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(HERE / "tests"), top_level_dir=str(HERE),
                            pattern="test_*.py")
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=OutcomeRecordingResult)
    started = time.time()
    result = runner.run(suite)
    elapsed = round(time.time() - started, 3)
    counts = {"tests_run": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "skipped": len(result.skipped),
              "passed": sum(1 for o in result.outcomes if o["status"] == "pass")}
    return {"counts": counts, "elapsed_seconds": elapsed,
            "stdout_tail": stream.getvalue()[-4000:], "outcomes": result.outcomes,
            "ok": counts["failures"] == 0 and counts["errors"] == 0}


def replay_pipeline() -> dict:
    protected = provenance.PROTECTED_INPUTS
    temporal_raw = protected["round5_temporal_raw"][0]
    spatial_base = protected["spatial_base_lora_reader"][0]
    packaged_path = protected["round5_predictions"][0]

    requests, fps_by_video, n_frames_by_video = load_windows(temporal_raw)
    spatial_source = load_spatial_source(spatial_base)
    packaged = replay.load_packaged_predictions(packaged_path)

    recorded_parse = {}
    for line in temporal_raw.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        vid = str(record["video_id"])
        for window in record["windows"]:
            recorded_parse[f"{vid}#{int(window['index'])}"] = {
                "output_valid": bool(window.get("output_valid")),
                "parsed_segments": window.get("parsed_segments"),
                "parse_errors": window.get("parse_errors"),
            }

    legacy = replay.replay_legacy_composition(
        requests=requests, spatial_source=spatial_source, fps_by_video=fps_by_video,
        n_frames_by_video=n_frames_by_video, constraint=WINDOW_CONSTRAINT, packaged=packaged)
    consistency = replay.parse_consistency(requests=requests, recorded=recorded_parse,
                                           constraint=WINDOW_CONSTRAINT)
    convention = replay.convention_diff(requests=requests, fps_by_video=fps_by_video,
                                        n_frames_by_video=n_frames_by_video,
                                        constraint=WINDOW_CONSTRAINT)
    convention_vs_ceil = replay.convention_diff(
        requests=requests, fps_by_video=fps_by_video, n_frames_by_video=n_frames_by_video,
        constraint=WINDOW_CONSTRAINT,
        legacy_convention=TimeConvention.LEGACY_CEIL_HALFOPEN.value)
    gap_no_shots = replay.spatial_gap_audit(
        requests=requests, spatial_source=spatial_source, fps_by_video=fps_by_video,
        n_frames_by_video=n_frames_by_video, constraint=WINDOW_CONSTRAINT, shot_map=None)
    # a single declared whole-video shot is the only shot structure the recorded data supports
    # without a shot-detection model, so the second audit declares one shot per video.
    shots_per_video = ShotMap(shots_by_video={
        vid: ((0, int(n_frames_by_video[vid])),) for vid in sorted(n_frames_by_video)})
    gap_one_shot = replay.spatial_gap_audit(
        requests=requests, spatial_source=spatial_source, fps_by_video=fps_by_video,
        n_frames_by_video=n_frames_by_video, constraint=WINDOW_CONSTRAINT,
        shot_map=shots_per_video, max_shot_nearest_gap_frames=DECLARED_ILLUSTRATIVE_GAP)

    return {
        "inputs": {
            "temporal_raw": str(temporal_raw.relative_to(ROOT)).replace("\\", "/"),
            "spatial_source": str(spatial_base.relative_to(ROOT)).replace("\\", "/"),
            "packaged_predictions": str(packaged_path.relative_to(ROOT)).replace("\\", "/"),
            "windows": len(requests),
            "videos": len(fps_by_video),
        },
        "legacy_replay": legacy,
        "parse_consistency": consistency,
        "convention_diff": convention,
        "convention_diff_vs_legacy_ceil_halfopen": convention_vs_ceil,
        "spatial_gap_audit_no_shot_map": gap_no_shots,
        "spatial_gap_audit_single_declared_shot_per_video": gap_one_shot,
        "no_ground_truth_used": True,
        "no_quality_score_computed": True,
        "notes": [
            "the recorded 174-row package is a prediction, never a reference",
            "the spatial source is a box source, never ground truth",
            "legacy modes exist only to reproduce history and are not delivery paths",
        ],
    }


def label_cardinality_snapshot() -> dict:
    """Cardinality check of the historical weak-label rows (read-only)."""
    dataset = ROOT / "reports/temporal_round5/evidence/split_manifest.json"
    return {
        "checked": False,
        "reason": ("the 818-row split files live only on the remote workspace and P1a must not "
                   "connect remotely; the 7-segment row is recorded in phase0 evidence "
                   "(split_manifest.json max n_segments = 7 in train)"),
        "phase0_evidence": str(dataset.relative_to(ROOT)).replace("\\", "/"),
        "phase0_evidence_exists": dataset.is_file(),
    }


def code_manifest() -> dict:
    """SHA-256 of every file written by P1a (self-describing artifact)."""
    files = {}
    for path in sorted(list((HERE / "aic6").rglob("*.py")) + list((HERE / "tests").rglob("*.py"))
                       + [HERE / "run_p1a.py"]):
        if "__pycache__" in path.parts:
            continue
        files[str(path.relative_to(ROOT)).replace("\\", "/")] = provenance.sha256_file(path)
    return files


def collect_fix_evidence(*, reports_dir: Path, protocol: dict) -> dict:
    """Before/after evidence required by the P1a fix handoff."""
    prefix_code_path = reports_dir / "prefix_code_hashes.json"
    prefix_code = json.loads(prefix_code_path.read_text(encoding="utf-8")) \
        if prefix_code_path.is_file() else {}
    current_code = protocol["code_manifest"]
    source_diff = []
    for name in sorted(set(prefix_code) | set(current_code)):
        before, after = prefix_code.get(name), current_code.get(name)
        if before == after:
            continue
        source_diff.append({
            "file": name, "before_sha256": before, "after_sha256": after,
            "change": "added" if before is None else "removed" if after is None else "modified",
        })

    prefix_repro = reports_dir / "prefix_reproduction.json"
    postfix_repro = reports_dir / "postfix_reproduction.json"
    run = subprocess.run([sys.executable, "-B", str(HERE / "repro_supervisor_cases.py"),
                          "--out", str(postfix_repro)], capture_output=True, text=True)
    before = json.loads(prefix_repro.read_text(encoding="utf-8"))["cases"] if prefix_repro.is_file() else {}
    after = json.loads(postfix_repro.read_text(encoding="utf-8"))["cases"] if postfix_repro.is_file() else {}

    def verdict(case: dict) -> dict:
        """Reduce a reproduction case to the property the supervisor asked for."""
        if "raised" in case:
            return {"compliant": True, "outcome": case["raised"]}
        if "full_video_fields_leaked" in case:
            return {"compliant": not case["full_video_fields_leaked"],
                    "leaked_fields": case["full_video_fields_leaked"]}
        if "one_good_one_bad" in case:
            return {"compliant": (case["one_good_one_bad"].get("status") == "FAILED_INVALID_WINDOWS"
                                  and case["empty_only"].get("status") == "OK_DELIVERABLE"
                                  and case["missing_spatial"].get("status")
                                  == "NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE"),
                    "one_good_one_bad": case["one_good_one_bad"].get("status"),
                    "empty_only": case["empty_only"].get("status"),
                    "missing_spatial": case["missing_spatial"].get("status")}
        if "NaN" in case:
            return {"compliant": all(not v.get("accepted") for v in case.values()),
                    "accepted_values": [k for k, v in case.items() if v.get("accepted")]}
        if "provenance_values" in case:
            return {"compliant": bool(case.get("uses_new_name") and not case.get("mentions_old_name")
                                      and not case.get("mentions_interpolation_word")),
                    "provenance_values": case.get("provenance_values"),
                    "totals_keys": case.get("totals_keys")}
        if "status" in case and "score" in case:
            return {"compliant": case.get("score") is None and case.get("status") != "OK",
                    "status": case.get("status"), "score": case.get("score")}
        return {"compliant": False, "outcome": "unrecognised case"}

    comparisons = [{"case": key, "before": verdict(before.get(key, {})),
                    "after": verdict(after.get(key, {}))}
                   for key in sorted(set(before) | set(after))]

    first_report = {}
    for name in ("REPORT.md", "protocol.json", "test_results.json", "replay_comparison.json",
                 "DATA_PILOT_BRIEF.md"):
        path = FIRST_P1A_DIR / name
        info = {"sha256": provenance.sha256_file(path), "bytes": path.stat().st_size} \
            if path.is_file() else {"missing": True}
        first_report[name] = info
    baseline_path = reports_dir / "phase1a_first_report_hashes.json"
    if baseline_path.is_file():
        recorded = json.loads(baseline_path.read_text(encoding="utf-8"))
        for name, info in first_report.items():
            key = str((FIRST_P1A_DIR / name).relative_to(ROOT)).replace("\\", "/")
            original = recorded.get(key)
            info["matches_first_report"] = bool(original and original["sha256"] == info.get("sha256"))

    return {
        "source_diff": source_diff,
        "reproductions": {
            "before_file": str(prefix_repro.relative_to(ROOT)).replace("\\", "/"),
            "after_file": str(postfix_repro.relative_to(ROOT)).replace("\\", "/"),
            "after_command_returncode": run.returncode,
            "comparisons": comparisons,
            "all_cases_compliant_after_fix": all(row["after"].get("compliant") for row in comparisons),
            "cases_non_compliant_before": [row["case"] for row in comparisons
                                           if row["before"].get("compliant") is not True],
        },
        "first_report": first_report,
        "protocol_section": {
            "round": "p1a_fix",
            "supervisor_review": "reports/round6_score_alignment/SUPERVISOR_P1A_REVIEW.md",
            "fixes": [
                "load_reference rejects missing/null/wrong-typed videos or frames, duplicate "
                "video_id and missing provenance metadata; only an explicit frames: [] is empty",
                "sparse references produce sparse-only diagnostics (no per-video F1/precision/"
                "recall/time-F1, no false positives from unannotated frames, no whole-video "
                "empty judgement); zero annotated frames reports NO_EVIDENCE",
                "SOURCE_SHOT_NEAREST replaces SOURCE_SHOT_INTERPOLATION; the declared gap limit "
                "must be a non-bool positive integer",
                "composition reports status/deliverable/exit_code; INVALID windows fail the run, "
                "legal empty stays a success, missing spatial boxes are undeliverable",
                "aic6.cli is the public failure boundary and exits non-zero on failure",
                "duplicate-counting wording and the symmetric-difference wording corrected",
            ],
            "outputs_dir": str(reports_dir.relative_to(ROOT)).replace("\\", "/"),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR),
                        help="where protocol/test/replay JSON is written (default: "
                             "reports/round6_score_alignment/phase1a_fix; the first P1a report "
                             "directory is never written to)")
    args = parser.parse_args(argv)
    reports_dir = Path(args.out_dir).resolve()
    if reports_dir == FIRST_P1A_DIR:
        raise SystemExit("refusing to write into the first P1a report directory; "
                         "pass --out-dir reports/round6_score_alignment/phase1a_fix")
    started = time.time()
    reports_dir.mkdir(parents=True, exist_ok=True)

    source_check = provenance.verify_evaluator_sources()
    protected_before = provenance.snapshot_protected()

    tests = run_tests()
    replay_result = replay_pipeline()

    protected_after = provenance.snapshot_protected()
    protection_problems = provenance.assert_protected_unchanged(protected_before, protected_after)

    legacy = replay_result["legacy_replay"]
    convention = replay_result["convention_diff"]
    gaps = replay_result["spatial_gap_audit_no_shot_map"]["traceable_mode"]

    protocol = {
        "run_id": RUN_ID,
        "spec_version": provenance.SPEC_VERSION,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "official_status": "INTERNAL_SPEC_REIMPLEMENTATION",
        "not_the_official_evaluator": True,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "sources": provenance.input_manifest(),
        "evaluator_source_verification": {k: v for k, v in source_check.items() if k != "mismatches"},
        "rules": [
            {"rule": "seconds->frame, new internal policy",
             "definition": "frame f selected iff a <= f/fps < b; legal frames 0..N-1",
             "mode": TimeConvention.TIMESTAMP_HALFOPEN.value,
             "source": "P1a internal policy; the published AIC page does not settle endpoint semantics "
                       "for the hidden labels"},
            {"rule": "local window time origin",
             "definition": "local time 0 is the real first sampled frame ceil(window_start*fps)/fps",
             "source": "P1a fix for the round-5 mismatch between the model timeline and the composer"},
            {"rule": "legacy ceil half-open",
             "definition": "ceil(a*fps-eps)..ceil(b*fps-eps)-1", "mode": "legacy_ceil_halfopen",
             "source": "historical 43.48 chain (inference_v2/temporal.seconds_to_frame_segments)"},
            {"rule": "legacy round inclusive",
             "definition": "round(a*fps)..round(b*fps) inclusive", "mode": "legacy_round_inclusive",
             "source": "historical round-5 composer (compose_temporal_candidate_v1)"},
            {"rule": "VFR", "definition": "explicit decoded PTS only; no PTS means no VFR claim",
             "source": "P1a internal policy"},
            {"rule": "three states", "definition": "VALID_NONEMPTY / VALID_EMPTY / INVALID(reasons)",
             "source": "P1a internal policy; replaces the historical invalid==empty conflation"},
            {"rule": "segment cardinality",
             "definition": f"one configurable constraint shared by prompt/training/inference; "
                           f"window replay constraint = {WINDOW_CONSTRAINT.min_segments}..{WINDOW_CONSTRAINT.max_segments}",
             "source": "P1a internal policy; the historical prompt allowed 1..5 and the parsing "
                       "allowed a different maximum"},
            {"rule": "centre-80% fallback",
             "definition": "exists only in legacy_replay mode; the new mode keeps invalid invalid",
             "source": "P1a internal policy"},
            {"rule": "spatial provenance",
             "definition": "SOURCE_SAME_FRAME / SOURCE_SHOT_NEAREST / NEEDS_SPATIAL_INFERENCE",
             "source": "P1a internal policy; any distance limit must be declared by the caller"},
            {"rule": "legacy nearest box",
             "definition": "nearest source frame anywhere in the video", "mode": "legacy_replay",
             "source": "historical round-5 composer"},
            {"rule": "joint score", "definition": "2*sum(matched_frame_IoU)/(N_pred+N_gt); "
                                                  "both empty 1; one side empty 0; mean over index videos x100",
             "source": "published AIC formula (seen 2026-09-17); internal re-implementation"},
            {"rule": "strict validation", "definition": "validation failure => score null, issues listed, "
                                                        "nothing cleaned",
             "source": "P1a internal policy"},
            {"rule": "missing reference", "definition": "no reference or incomplete reference => "
                                                        "NOT_COMPUTABLE; sparse reference => SPARSE_DIAGNOSTIC",
             "source": "P1a internal policy; supervisor P0 erratum 1"},
        ],
        "modes": {
            "scoring": ["OK", "SPARSE_DIAGNOSTIC", "NOT_COMPUTABLE", "INVALID_INPUT"],
            "composition": ["traceable", "legacy_replay"],
            "time": [m.value for m in TimeConvention],
        },
        "code_manifest": code_manifest(),
        "protected_inputs_before": protected_before,
        "protected_inputs_after": protected_after,
        "protected_inputs_unchanged": not protection_problems,
        "deviations_from_vendored_evaluator": list(scoring.DEVIATIONS_FROM_VENDORED),
    }

    test_results = {
        "run_id": RUN_ID,
        "created_utc": protocol["created_utc"],
        "commands": [
            "python round6_score_alignment/p1a/run_p1a.py",
            "python -m unittest discover -s round6_score_alignment/p1a/tests -t round6_score_alignment/p1a",
        ],
        "test_suite": tests,
        "replay_integration_checks": {
            "legacy_rule_reproduces_recorded_package": {
                "videos_identical_including_boxes": legacy["videos_identical_including_boxes"],
                "videos_total": legacy["videos_total"],
                "frame_count_mismatches": legacy["frame_count_mismatches"],
                "box_mismatch_count": legacy["box_mismatch_count"],
                "packaged_frame_count": legacy["packaged_frame_count"],
                "pass": (legacy["videos_identical_including_boxes"] == legacy["videos_total"]
                         and legacy["frame_count_mismatches"] == 0
                         and legacy["box_mismatch_count"] == 0),
            },
            "recorded_window_text_parse_consistency": {
                "windows": replay_result["parse_consistency"]["windows"],
                "matched": replay_result["parse_consistency"]["windows_matching_recorded_parse"],
                "pass": (replay_result["parse_consistency"]["windows_matching_recorded_parse"]
                         == replay_result["parse_consistency"]["windows"]),
            },
            "new_policy_reports_frame_set_difference": {
                "frames_new_policy": convention["frames_new_policy"],
                "frames_legacy_policy": convention["frames_legacy_policy"],
                "frames_added_total": convention["frames_added_total"],
                "frames_removed_total": convention["frames_removed_total"],
                "non_zero_origin_offsets": convention["origin_offset_sec"]["n_nonzero"],
                "pass": convention["videos_compared"] == len(convention["per_video"]),
            },
            "new_spatial_mode_reports_gaps_instead_of_copying": {
                "needs_spatial_inference": gaps["needs_spatial_inference"],
                "legacy_nearest_copies": replay_result["spatial_gap_audit_no_shot_map"]
                ["legacy_mode_for_contrast"]["legacy_nearest_copies"],
                "pass": gaps["needs_spatial_inference"] > 0,
            },
            "protected_inputs_unchanged": {
                "problems": protection_problems,
                "pass": not protection_problems,
            },
        },
        "label_cardinality_snapshot": label_cardinality_snapshot(),
        "wall_seconds": round(time.time() - started, 2),
    }

    provenance.write_json(reports_dir / "protocol.json", protocol)
    provenance.write_json(reports_dir / "test_results.json", test_results)
    provenance.write_json(reports_dir / "replay_comparison.json", replay_result)

    # ---- fix-round evidence: reproductions before/after, source diff, first-report guard ----
    fix_evidence = collect_fix_evidence(reports_dir=reports_dir, protocol=protocol)
    protocol["fix_round"] = fix_evidence["protocol_section"]
    test_results["supervisor_reproductions"] = fix_evidence["reproductions"]
    test_results["source_diff"] = fix_evidence["source_diff"]
    test_results["first_p1a_report"] = fix_evidence["first_report"]
    provenance.write_json(reports_dir / "protocol.json", protocol)
    provenance.write_json(reports_dir / "test_results.json", test_results)

    summary = {
        "tests": tests["counts"],
        "tests_ok": tests["ok"],
        "legacy_replay_videos_identical": legacy["videos_identical_including_boxes"],
        "box_mismatches": legacy["box_mismatch_count"],
        "parse_consistency": f"{replay_result['parse_consistency']['windows_matching_recorded_parse']}"
                             f"/{replay_result['parse_consistency']['windows']}",
        "new_vs_legacy_frames": f"{convention['frames_new_policy']} vs {convention['frames_legacy_policy']}",
        "needs_spatial_inference": gaps["needs_spatial_inference"],
        "legacy_nearest_copies": replay_result["spatial_gap_audit_no_shot_map"]
        ["legacy_mode_for_contrast"]["legacy_nearest_copies"],
        "protected_inputs_unchanged": not protection_problems,
        "wall_seconds": test_results["wall_seconds"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if tests["ok"] and not protection_problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
