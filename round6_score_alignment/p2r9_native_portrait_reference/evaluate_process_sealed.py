from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from sealed_evaluator import SealedEvaluationError, evaluate, sha256_file


def safe_hash(path: Path) -> str | None:
    try:
        return sha256_file(path)
    except OSError:
        return None


def append_access_log(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--sealed-reference", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--protected-registry", type=Path, required=True)
    parser.add_argument("--access-log", type=Path, required=True)
    args = parser.parse_args(argv)
    wrapper = Path(__file__).resolve()
    engine = wrapper.with_name("sealed_evaluator.py")
    error_code = None
    try:
        result = evaluate(
            args.commitment.resolve(), args.sealed_reference.resolve(), args.predictions.resolve(),
            args.protected_registry.resolve(), wrapper, engine,
        )
        exit_code = 0
    except SealedEvaluationError as exc:
        error_code = exc.code
        result = {
            "schema": "p2r9_process_sealed_aggregate_v1",
            "status": "REFUSED",
            "protocol": "PROCESS_SEALED",
            "cryptographic_blind": False,
            "aggregate_generated": False,
            "error_code": error_code,
        }
        exit_code = 2
    except Exception:
        error_code = "INTERNAL_ERROR_REDACTED"
        result = {
            "schema": "p2r9_process_sealed_aggregate_v1",
            "status": "REFUSED",
            "protocol": "PROCESS_SEALED",
            "cryptographic_blind": False,
            "aggregate_generated": False,
            "error_code": error_code,
        }
        exit_code = 3

    log_row = {
        "schema": "p2r9_holdout_access_log_v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "actor": os.environ.get("P2R9_EVALUATOR_ACTOR", "UNSPECIFIED_LOCAL_ACTOR"),
        "code_sha256": safe_hash(wrapper),
        "engine_sha256": safe_hash(engine),
        "prediction_sha256": safe_hash(args.predictions),
        "commitment_sha256": safe_hash(args.commitment),
        "result_status": result["status"],
        "aggregate_generated": result.get("status") == "PASS_AGGREGATE",
        "error_code": error_code,
    }
    try:
        append_access_log(args.access_log.resolve(), log_row)
    except Exception:
        result = {
            "schema": "p2r9_process_sealed_aggregate_v1",
            "status": "REFUSED",
            "protocol": "PROCESS_SEALED",
            "cryptographic_blind": False,
            "aggregate_generated": False,
            "error_code": "ACCESS_LOG_APPEND_FAILED",
        }
        exit_code = 4
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
