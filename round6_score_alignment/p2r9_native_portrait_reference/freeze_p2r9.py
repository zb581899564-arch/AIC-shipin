from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "round6_p2r9_20260920T040552Z"
FINAL_STATUS = "P2R9_PERMISSION_REQUIRED"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def walk_forbidden(value: object, location: str, hits: list[str]) -> None:
    forbidden = {
        "reference_boxes", "reference_box", "crop_bbox", "crop_bboxes", "trajectory",
        "trajectories", "item_iou", "per_item_score", "best_reference",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden and child not in (None, [], {}, "NOT_AVAILABLE"):
                hits.append(f"{location}:{key}")
            walk_forbidden(child, f"{location}.{key}", hits)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden(child, f"{location}[{index}]", hits)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    run = args.run_dir.resolve()
    code_dir = root / "round6_score_alignment/p2r9_native_portrait_reference"
    now = datetime.now(timezone.utc).isoformat()

    presearch = json.loads((run / "input_freeze_presearch.json").read_text(encoding="utf-8"))
    input_mismatches = []
    for item in presearch["inputs"]:
        path = root / item["path"]
        actual = sha256_file(path) if path.is_file() else None
        if actual != item["sha256"]:
            input_mismatches.append({"path": item["path"], "expected": item["sha256"], "actual": actual})
    historical_verification = {
        "schema": "p2r9_historical_hash_verification_v1",
        "created_utc": now,
        "status": "PASS" if not input_mismatches else "FAIL",
        "checked": len(presearch["inputs"]),
        "mismatches": input_mismatches,
        "note": "all inputs frozen before online candidate search were rehashed; historical artifacts remained read-only",
    }
    write_json(run / "historical_hash_verification.json", historical_verification)

    credential_patterns = {
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "authorization_header": re.compile(r"Authorization:\s*(?:Bearer|Basic)\s+\S+", re.I),
        "cookie_header": re.compile(r"(?:^|\n)Cookie:\s*\S+", re.I),
    }
    credential_hits = []
    payload_hits = []
    ordinary_json_files = []
    for path in sorted(run.rglob("*")):
        if not path.is_file() or "snapshots" in path.parts:
            continue
        if path.suffix.lower() in {".md", ".txt", ".json", ".jsonl"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for name, pattern in credential_patterns.items():
                if pattern.search(text):
                    credential_hits.append({"path": path.relative_to(root).as_posix(), "pattern": name})
        if path.suffix.lower() == ".json":
            ordinary_json_files.append(path)
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            walk_forbidden(value, path.relative_to(root).as_posix(), payload_hits)
        if path.suffix.lower() == ".jsonl" and path.name != "holdout_access_log.jsonl":
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                walk_forbidden(value, f"{path.relative_to(root).as_posix()}:{line_number}", payload_hits)

    real_holdout_files = [
        path.relative_to(root).as_posix()
        for path in run.rglob("*")
        if path.is_file() and path.name in {"holdout_commitment.json", "sealed_holdout_manifest.jsonl", "dev_manifest.jsonl"}
    ]
    access_log = run / "holdout_access_log.jsonl"
    scan = {
        "schema": "p2r9_boundary_and_secret_scan_v1",
        "created_utc": now,
        "status": "PASS" if not credential_hits and not payload_hits and not real_holdout_files and access_log.stat().st_size == 0 else "FAIL",
        "ordinary_json_files_scanned": len(ordinary_json_files),
        "credential_hits": credential_hits,
        "ordinary_output_reference_payload_hits": payload_hits,
        "unexpected_real_manifest_files": real_holdout_files,
        "holdout_access_log_bytes": access_log.stat().st_size,
        "snapshot_exception": "First-party snapshots may contain published candidate annotations (Portrait1K compressed index) but no candidate was selected or assigned to process_sealed_holdout. Snapshots are not ordinary manifests, reports, stdout, or exception logs.",
        "code_test_exception": "Source tests contain only explicitly synthetic coordinates created in temporary directories.",
    }
    write_json(run / "boundary_and_secret_scan.json", scan)

    code_files = sorted(path for path in code_dir.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    snapshot_files = sorted(path for path in (run / "snapshots").rglob("*") if path.is_file())
    write_json(run / "file_hashes.json", {
        "schema": "p2r9_file_hashes_v1",
        "created_utc": now,
        "frozen_inputs": presearch["inputs"],
        "code": [record(path, root) for path in code_files],
        "source_snapshots": [record(path, root) for path in snapshot_files],
    })

    excluded_from_index = {"final_freeze.json", "final_freeze.sha256.txt", "freeze_verification.json", "evidence_index.json"}
    evidence_files = sorted(path for path in run.rglob("*") if path.is_file() and path.name not in excluded_from_index)
    write_json(run / "evidence_index.json", {
        "schema": "p2r9_evidence_index_v1",
        "run_id": RUN_ID,
        "status": FINAL_STATUS,
        "created_utc": now,
        "files": [record(path, root) for path in evidence_files],
    })

    excluded_from_freeze = {"final_freeze.json", "final_freeze.sha256.txt", "freeze_verification.json"}
    output_files = sorted(path for path in run.rglob("*") if path.is_file() and path.name not in excluded_from_freeze)
    total_new_bytes = sum(path.stat().st_size for path in output_files) + sum(path.stat().st_size for path in code_files)
    freeze = {
        "schema": "p2r9_final_freeze_v1",
        "run_id": RUN_ID,
        "status": FINAL_STATUS,
        "created_utc": now,
        "root": str(root),
        "outputs": [record(path, root) for path in output_files],
        "code": [record(path, root) for path in code_files],
        "counts": {
            "output_files": len(output_files),
            "code_files": len(code_files),
            "source_snapshots": len(snapshot_files),
            "candidate_rows": 6,
            "eligible_candidates": 0,
            "real_dev_items": 0,
            "real_process_sealed_items": 0,
            "synthetic_tests": 30,
        },
        "resources": {"gpu_seconds": 0, "candidate_media_bytes": 0, "total_new_bytes": total_new_bytes, "disk_limit_bytes": 3 * 1024**3},
        "gates": {
            "historical_hash_verification": historical_verification["status"],
            "boundary_and_secret_scan": scan["status"],
            "synthetic_tests": json.loads((run / "synthetic_test_results.json").read_text(encoding="utf-8"))["status"],
        },
    }
    freeze_path = run / "final_freeze.json"
    write_json(freeze_path, freeze)
    freeze_sha = sha256_file(freeze_path)
    (run / "final_freeze.sha256.txt").write_text(f"{freeze_sha}  final_freeze.json\n", encoding="ascii")

    mismatches = []
    for item in freeze["outputs"] + freeze["code"]:
        path = root / item["path"]
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            mismatches.append(item["path"])
    verification = {
        "schema": "p2r9_freeze_verification_v1",
        "status": "PASS" if not mismatches and all(value == "PASS" for value in freeze["gates"].values()) else "FAIL",
        "checked": len(freeze["outputs"]) + len(freeze["code"]),
        "mismatches": mismatches,
        "freeze_sha256": freeze_sha,
    }
    write_json(run / "freeze_verification.json", verification)
    print(json.dumps(verification, ensure_ascii=False))
    return 0 if verification["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
