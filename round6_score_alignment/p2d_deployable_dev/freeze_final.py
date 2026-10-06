"""Freeze every P2-D code and evidence artifact by SHA-256."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
from pathlib import Path

from p2d_core import sha256_file

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--output", default="final_freeze.json")
    args = parser.parse_args()
    evidence = Path(args.evidence_dir).resolve()
    target = evidence / args.output
    if target.exists():
        raise FileExistsError(f"refusing to overwrite {target}")
    code_files = sorted(path for path in HERE.rglob("*.py") if "__pycache__" not in path.parts)
    evidence_files = sorted(path for path in evidence.iterdir()
                            if path.is_file() and not path.name.startswith("final_freeze"))
    validation = json.loads((evidence / "validation_comparison.json").read_text(encoding="utf-8"))
    strict = json.loads((evidence / "strict_format_validation.json").read_text(encoding="utf-8"))
    resource = json.loads((evidence / "gpu_resource_postflight.json").read_text(encoding="utf-8"))
    run = json.loads((evidence / "raw_inference.run.json").read_text(encoding="utf-8"))
    report = {
        "schema": "aic6_p2d_final_freeze_v1",
        "run_id": "round6_p2d_20260919T130011Z",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "engineering_status": validation["engineering_status"],
        "quality_status": validation["quality_status"],
        "official_status": "NOT_OFFICIAL_SCORE",
        "stage_status": "STOP_WAIT_SUPERVISOR_ACCEPTANCE",
        "gates": {
            "format_valid": validation["format_valid"],
            "selection_complete": validation["selection_complete"],
            "deployable": validation["deployable"],
            "strict_serialized_format": strict["status"],
            "budget": resource["budget_status"],
            "weak_roi_inputs_used": run["weak_roi_inputs_used"],
            "old_test_boxes_used": run["old_test_boxes_used"],
            "silent_fallbacks": run["silent_fallbacks"],
        },
        "code_files": {relative(path): sha256_file(path) for path in code_files},
        "evidence_files": {relative(path): sha256_file(path) for path in evidence_files},
        "remote_model_hashes": run["model_hashes"],
        "remote_baseline_sha256": run["baseline_sha256"],
        "remote_local_sync_hashes": resource["remote_local_hash_matches"],
        "python": platform.python_version(),
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["stage_status"],
                      "code_files": len(report["code_files"]),
                      "evidence_files": len(report["evidence_files"]),
                      "final_freeze_sha256": sha256_file(target)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
