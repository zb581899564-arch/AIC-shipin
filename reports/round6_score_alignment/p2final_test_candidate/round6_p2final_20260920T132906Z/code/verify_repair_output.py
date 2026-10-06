"""Independently verify the targeted decoder-repair output before composition."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row: dict) -> tuple[str, int]:
    return str(row["video_id"]), int(row["source_frame"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--repaired", type=Path, required=True)
    parser.add_argument("--repair-manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("refusing to overwrite verification report")

    requests = read_jsonl(args.requests)
    previous = read_jsonl(args.previous)
    repaired = read_jsonl(args.repaired)
    manifest = read_jsonl(args.repair_manifest)
    request_map = {key(row): row for row in requests}
    previous_map = {key(row): row for row in previous}
    repaired_map = {key(row): row for row in repaired}
    manifest_map = {key(row): row for row in manifest}
    issues: list[dict] = []

    if len(request_map) != len(requests):
        issues.append({"code": "DUPLICATE_REQUEST_KEY"})
    if len(previous_map) != len(previous):
        issues.append({"code": "DUPLICATE_PREVIOUS_KEY"})
    if len(repaired_map) != len(repaired):
        issues.append({"code": "DUPLICATE_REPAIRED_KEY"})
    if set(request_map) != set(repaired_map):
        issues.append({"code": "REQUEST_KEY_SET_MISMATCH"})

    previous_valid = {k for k, row in previous_map.items()
                      if row.get("status") == "MODEL_OK" and row.get("used_fallback") is False}
    repaired_keys = set(request_map) - previous_valid
    preservation_mismatches = [k for k in sorted(previous_valid) if previous_map[k] != repaired_map.get(k)]
    if preservation_mismatches:
        issues.append({"code": "PRESERVED_ROW_CHANGED", "count": len(preservation_mismatches),
                       "examples": preservation_mismatches[:5]})

    if set(manifest_map) != repaired_keys:
        issues.append({"code": "REPAIR_MANIFEST_KEY_SET_MISMATCH",
                       "manifest": len(manifest_map), "expected": len(repaired_keys)})

    for k, row in repaired_map.items():
        request = request_map.get(k)
        if request is None:
            continue
        if row.get("anchor_request_sha256") != request.get("anchor_request_sha256"):
            issues.append({"code": "REQUEST_HASH_MISMATCH", "key": k})
        if k in repaired_keys:
            source = manifest_map.get(k)
            if (source is None or
                    (source.get("anchor_request_sha256") is not None and
                     source.get("anchor_request_sha256") != request.get("anchor_request_sha256")) or
                    source.get("decoded_pixel_sha256") != request.get("expected_pixel_sha256")):
                issues.append({"code": "REPAIR_IDENTITY_EVIDENCE_MISMATCH", "key": k})
        elif row.get("decoded_pixel_sha256") != request.get("expected_pixel_sha256"):
            issues.append({"code": "PRESERVED_PIXEL_HASH_MISMATCH", "key": k})
        if row.get("status") != "MODEL_OK" or row.get("used_fallback") is not False:
            issues.append({"code": "INVALID_OUTPUT_STATUS", "key": k,
                           "status": row.get("status"), "used_fallback": row.get("used_fallback")})
        box = row.get("box_xyw")
        if (not isinstance(box, list) or len(box) != 3 or
                any(isinstance(x, bool) or not isinstance(x, int) for x in box)):
            issues.append({"code": "INVALID_BOX_TYPE", "key": k})

    report = {
        "status": "PASS_REPAIR_OUTPUT" if not issues else "FAIL_REPAIR_OUTPUT",
        "requests": len(requests),
        "previous_valid_rows": len(previous_valid),
        "targeted_repair_rows": len(repaired_keys),
        "repaired_output_rows": len(repaired),
        "preservation_mismatches": len(preservation_mismatches),
        "invalid_rows": sum(row.get("status") != "MODEL_OK" or row.get("used_fallback") is not False
                            for row in repaired),
        "requests_sha256": sha256(args.requests),
        "previous_sha256": sha256(args.previous),
        "repaired_sha256": sha256(args.repaired),
        "repair_manifest_sha256": sha256(args.repair_manifest),
        "issues": issues,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not issues else 5


if __name__ == "__main__":
    raise SystemExit(main())
