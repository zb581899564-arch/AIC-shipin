"""Milestone-4 runner: freeze the P2 candidate implementation.

Collects SHA-256 of every code file, of every input consumed, and of every
evidence artifact produced by the P2 milestones; verifies the full local test
suite and both CPU runners one last time; then writes a single freeze record.
The freeze covers only what exists locally; it grants no authority to run
test-set inference.
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
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import provenance                                    # noqa: E402

RUN_ID_DEFAULT = "round6_p2_freeze_20260918T0000Z"
P2_REPORTS = ROOT / "reports/round6_score_alignment/p2_joint_coverage"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run_tests() -> dict:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(HERE / "tests"), top_level_dir=str(HERE),
                            pattern="test_*.py")
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=0)
    started = time.time()
    result = runner.run(suite)
    return {"tests_run": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors),
            "ok": not result.failures and not result.errors,
            "elapsed_seconds": round(time.time() - started, 3)}


def run_runner(script: str, run_id: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-B", str(HERE / script), "--run-id", run_id,
         "--out-dir", str(P2_REPORTS / f"{run_id}_check")],
        capture_output=True, text=True, timeout=300)
    return {"script": script, "exit_code": proc.returncode,
            "stderr_tail": proc.stderr[-500:] if proc.returncode else ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(P2_REPORTS))
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    started = time.monotonic()

    code_files = {}
    for path in sorted(list((HERE / "aic6").rglob("*.py"))
                       + list((HERE / "tests").rglob("*.py"))
                       + [HERE / p for p in (
                           "run_m1_coverage_audit.py", "run_m2a_sim_cpu.py",
                           "run_m2b_boundary.py", "run_m3_paired.py", "run_freeze.py",
                           "remote_infer_gaps.py")]):
        if "__pycache__" in path.parts and False:
            continue
        if path.is_file():
            code_files[str(path.relative_to(HERE)).replace("\\", "/")] = sha256_file(path)

    inputs = {}
    for key, (path, _expected) in provenance.PROTECTED_INPUTS.items():
        p = Path(path)
        inputs[key] = {"path": str(p.relative_to(ROOT)).replace("\\", "/")
                       if p.is_relative_to(ROOT) else str(p),
                       "sha256": sha256_file(p) if p.is_file() else None}
    for extra in ("p2_infer_requests.jsonl", "gap_predictions.jsonl",
                  "gap_predictions.run.json", "p2_infer_requests_v2_source_grid.jsonl",
                  "p2_infer_requests_v2_subset.jsonl", "gap_predictions_v2_subset.jsonl",
                  "gap_predictions_v2_subset.run.json", "control_quality_v2.json",
                  "gpu_ledger_addendum_20260918.jsonl",
                  "SUPERVISOR_REVIEW_20260918.md"):
        p = P2_REPORTS / extra
        inputs[extra] = {"path": f"reports/round6_score_alignment/p2_joint_coverage/{extra}",
                         "sha256": sha256_file(p) if p.is_file() else None}

    tests = run_tests()
    checks = {}
    if tests["ok"]:
        checks["unit_tests"] = tests
        checks["runner_m2a"] = run_runner("run_m2a_sim_cpu.py", f"{args.run_id}_m2a")
        checks["runner_m2b"] = run_runner("run_m2b_boundary.py", f"{args.run_id}_m2b")
        checks["runner_m3"] = run_runner("run_m3_paired.py", f"{args.run_id}_m3")
    all_ok = (tests["ok"]
              and all(v.get("exit_code") == 0 for k, v in checks.items() if k.startswith("runner")))

    evidence = {}
    for path in sorted(P2_REPORTS.glob("*.json")):
        if path.name.startswith(args.run_id):
            continue
        evidence[path.name] = sha256_file(path)

    record = {
        "schema": "aic6_p2_freeze_record_v1",
        "run_id": args.run_id,
        "status": "READY_FOR_SUPERVISOR_REVIEW" if all_ok else "FREEZE_CHECKS_FAILED",
        "official_status": "NOT_OFFICIAL_SCORE",
        "module": "round6_score_alignment/p2_joint_coverage",
        "reports_dir": "reports/round6_score_alignment/p2_joint_coverage",
        "code_files": code_files,
        "inputs": inputs,
        "verification": checks,
        "evidence_artifacts": evidence,
        "python": platform.python_version(),
        "frozen_at_seconds": round(time.monotonic() - started, 3),
    }
    provenance.write_json(out_dir / f"{args.run_id}.json", record)
    print(f"status: {record['status']}")
    print(f"code files: {len(code_files)}; inputs pinned: {len(inputs)}; "
          f"evidence artifacts: {len(evidence)}")
    for k, v in checks.items():
        if k.startswith("runner"):
            print(k, "exit", v["exit_code"])
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
