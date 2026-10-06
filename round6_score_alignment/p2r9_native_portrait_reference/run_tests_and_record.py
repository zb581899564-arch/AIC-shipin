from __future__ import annotations

import argparse
import io
import json
import os
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--tests-dir", type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    os.environ["P2R9_RUN_DIR"] = str(run)
    suite = unittest.defaultTestLoader.discover(str(args.tests_dir.resolve()), pattern="test_*.py")
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.perf_counter() - started
    console = stream.getvalue()
    (run / "synthetic_test_console.txt").write_text(console, encoding="utf-8")
    summary = {
        "schema": "p2r9_synthetic_test_results_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "elapsed_seconds": elapsed,
        "scope": "synthetic protocol and protected-boundary tests only; no real candidate labels or holdout were bound",
        "stdout_reference_payload_exposure": 0 if result.wasSuccessful() else "NOT_COMPUTABLE",
    }
    (run / "synthetic_test_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
