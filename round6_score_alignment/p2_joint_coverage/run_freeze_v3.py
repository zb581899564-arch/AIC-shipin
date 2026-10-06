"""Freeze the corrected P2 development evidence without running a GPU job.

All Python sources and existing evidence files are hashed.  The v2 source-grid
subset and composition are replayed in a new, retained check directory.  A
successful freeze is explicitly partial: the 7,591 unprocessed selected frames
and the 186 label-sourced boxes make this NOT_DELIVERABLE_BUDGET.
"""
from __future__ import annotations

import argparse
import hashlib
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
P2 = ROOT / "reports/round6_score_alignment/p2_joint_coverage"
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import provenance  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run_tests() -> dict:
    suite = unittest.TestLoader().discover(
        start_dir=str(HERE / "tests"), top_level_dir=str(HERE),
        pattern="test_*.py")
    output = StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=0).run(suite)
    return {"tests_run": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "ok": result.wasSuccessful(),
            "output_tail": output.getvalue()[-1000:]}


def run_script(script: str, *args: str) -> dict:
    result = subprocess.run(
        [sys.executable, "-B", str(HERE / script), *args],
        capture_output=True, text=True, timeout=300)
    return {"script": script, "exit_code": result.returncode,
            "stdout_tail": result.stdout[-1200:],
            "stderr_tail": result.stderr[-1200:]}


def manifest(files: list[Path], base: Path) -> dict[str, str]:
    return {path.relative_to(base).as_posix(): sha256_file(path)
            for path in sorted(files)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="round6_p2_freeze_v3_20260918T0000Z")
    args = parser.parse_args()
    P2.mkdir(parents=True, exist_ok=True)
    output = P2 / f"{args.run_id}.json"
    checks = P2 / f"{args.run_id}_checks"
    if output.exists() or checks.exists():
        raise RuntimeError("refusing to overwrite a prior freeze or check directory")
    started = time.monotonic()

    code_files = manifest(list(HERE.rglob("*.py")), HERE)
    evidence_files = [path for path in P2.iterdir() if path.is_file()]
    evidence_before = manifest(evidence_files, P2)
    protected_before = provenance.snapshot_protected()
    pin_problems = [key for key, item in protected_before.items()
                    if not item.get("matches")]

    # Keep check outputs as small immutable evidence rather than deleting them.
    # They are outside the top-level evidence manifest to avoid self-reference.
    checks.mkdir()
    verification = {"unit_tests": run_tests()}
    if verification["unit_tests"]["ok"] and not pin_problems:
        verification["subset_replay"] = run_script("run_subset_replay.py")
        verification["m1_coverage"] = run_script(
            "run_m1_coverage_audit.py", "--run-id", f"{args.run_id}_m1",
            "--out-dir", str(checks))
        verification["m2b_boundary"] = run_script(
            "run_m2b_boundary.py", "--run-id", f"{args.run_id}_m2b",
            "--out-dir", str(checks))
        verification["m2f_source_grid"] = run_script(
            "run_m2f_real_compose_v2.py", "--run-id", f"{args.run_id}_m2f",
            "--out-dir", str(checks))

    replay = checks / f"{args.run_id}_m2f.real_composed_predictions.jsonl"
    historical = P2 / "round6_p2_m2f_20260918T0200Z.real_composed_predictions.jsonl"
    replay_report = checks / f"{args.run_id}_m2f.json"
    m1_report = checks / f"{args.run_id}_m1.json"
    m2b_report = checks / f"{args.run_id}_m2b.json"
    result = json.loads(replay_report.read_text(encoding="utf-8")) \
        if replay_report.is_file() else None
    m1 = json.loads(m1_report.read_text(encoding="utf-8")) \
        if m1_report.is_file() else None
    m2b = json.loads(m2b_report.read_text(encoding="utf-8")) \
        if m2b_report.is_file() else None
    exact = (replay.is_file() and historical.is_file()
             and replay.read_bytes() == historical.read_bytes())
    verification["v2_composition_replay"] = {
        "byte_exact": exact,
        "replayed_sha256": sha256_file(replay) if replay.is_file() else None,
        "historical_sha256": sha256_file(historical) if historical.is_file() else None,
        "replay_report_sha256": sha256_file(replay_report)
        if replay_report.is_file() else None,
        "format_valid": result.get("format_valid") if result else None,
        "selection_complete": result.get("selection_complete") if result else None,
        "deployable": result.get("deployable") if result else None,
        "delivery_status": result.get("delivery_status") if result else None,
        "selected_source_frames": result.get("selection_totals", {}).get(
            "selected_source_frames") if result else None,
        "composed_boxes": result.get("composition", {}).get("n_boxes")
        if result else None,
        "source_counts": result.get("composition", {}).get("source_counts")
        if result else None,
    }
    verification["historical_m3_excluded"] = (
        "run_m3_paired.py uses v1's incorrect clip-grid inference output; "
        "it is intentionally not a v3 verification gate")
    verification["m1_counts"] = m1.get("totals") if m1 else None
    verification["m2b_counts"] = m2b.get("counts") if m2b else None
    check_artifacts = manifest(
        [path for path in checks.iterdir() if path.is_file()], checks)

    evidence_after = manifest(evidence_files, P2)
    protected_after = provenance.snapshot_protected()
    protected_problems = provenance.assert_protected_unchanged(
        protected_before, protected_after)
    run_checks_ok = all(item["exit_code"] == 0 for key, item in
                        verification.items() if isinstance(item, dict)
                        and "exit_code" in item)
    v = verification["v2_composition_replay"]
    all_ok = (not pin_problems and not protected_problems
              and evidence_before == evidence_after
              and verification["unit_tests"]["ok"] and run_checks_ok
              and v["byte_exact"] and v["format_valid"] is True
              and v["selection_complete"] is False
              and v["deployable"] is False
              and v["delivery_status"] == "NOT_DELIVERABLE_BUDGET"
              and v["selected_source_frames"] == 13777
              and v["composed_boxes"] == 6186
              and v["source_counts"] == {
                  "REAL_INFERENCE": 6000, "WEAK_ROI_SAME_FRAME": 186,
                  "NOT_INFERRED_BUDGET": 7591, "INVALID_INFERENCE": 0}
              and verification["m1_counts"] is not None
              and verification["m1_counts"]["n_selected"] == 40384
              and verification["m1_counts"]["NEEDS_INFERENCE"] == 3200
              and verification["m2b_counts"] == {
                  "total": 16, "pass": 16, "fail": 0})

    freeze = {
        "schema": "aic6_p2_partial_dev_freeze_v3",
        "run_id": args.run_id,
        "status": "PARTIAL_DEV_EVIDENCE_FROZEN" if all_ok else "FREEZE_CHECKS_FAILED",
        "delivery_status": "NOT_DELIVERABLE_BUDGET",
        "official_status": "NOT_OFFICIAL_SCORE",
        "code_files": code_files,
        "protected_inputs": protected_after,
        "evidence_artifacts": evidence_before,
        "checks_dir": checks.relative_to(ROOT).as_posix(),
        "check_artifacts": check_artifacts,
        "verification": verification,
        "pinned_input_problems": pin_problems,
        "protected_input_problems": protected_problems,
        "historical_evidence_unchanged": evidence_before == evidence_after,
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    provenance.write_json(output, freeze)
    print(json.dumps({"status": freeze["status"],
                      "delivery_status": freeze["delivery_status"],
                      "code_files": len(code_files),
                      "evidence_files": len(evidence_before),
                      "verification": verification["v2_composition_replay"]},
                     ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
