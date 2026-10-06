#!/usr/bin/env python3
"""Re-audit all bound 426 v3 numeric records; never decode or infer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
from native_clock_core import audit_record, need
from registry_io import (REMATCH_SHA, V3_RECEIPT_SHA, V3_WORKER_SHA, failed_record, keyed_records,
    load_addendum, load_numeric, read_bound, sha, validate_manifest, verify_source_lock, write_bundle, write_new)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--v3-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--numeric-root", type=Path, help="optional byte-identical metadata mirror, never media")
    parser.add_argument("--endpoint-addendum", type=Path)
    parser.add_argument("--expected-addendum-sha256")
    parser.add_argument("--addendum-json-root", type=Path, help="optional raw-JSON metadata mirror")
    args = parser.parse_args()
    started = time.monotonic()
    output = None
    try:
        verify_source_lock()
        manifest = read_bound(args.manifest, REMATCH_SHA)
        validate_manifest(manifest, "REMATCH426")
        receipt = read_bound(args.v3_receipt, V3_RECEIPT_SHA)
        need(receipt.get("schema") == "aic_source_origin_identity_v3" and receipt.get("registered_sources") == 426
             and receipt.get("audited_sources") == 426 and receipt.get("input_manifest_sha256") == REMATCH_SHA,
             "BOUND_COMPLETE_V3_RECEIPT_REQUIRED")
        need(receipt.get("labels_read") is False and receipt.get("models_run") is False
             and receipt.get("GPU_used") is False and receipt.get("source_bytes_modified") is False,
             "V3_RECEIPT_SCOPE_MISMATCH")
        workers = {p["path"]: p["sha256"] for p in receipt["source_code"]}
        need(workers.get("numeric_source_worker.py") == V3_WORKER_SHA, "FROZEN_V3_INTEGER_FLOAT64_PARSER_HASH_REQUIRED")
        prior = keyed_records(receipt, manifest["records"])
        endpoint, endpoint_sha = load_addendum(args.endpoint_addendum, args.expected_addendum_sha256, args.addendum_json_root)
        need(set(endpoint) <= set(prior), "ADDENDUM_UNREGISTERED_SOURCE_ID")
        args.output_root.mkdir(parents=True, exist_ok=False)
        output = args.output_root
        records, arrays = [], {}
        source_hashes = {p.name: sha(p) for p in Path(__file__).parent.glob("*.py")}
        for row in manifest["records"]:
            vid = row["video_id"]
            old = prior[vid]
            try:
                numeric, numeric_path = load_numeric(old, args.numeric_root)
                addendum_record, ffprobe, addendum_spec = endpoint.get(vid, (None, None, None))
                result, clock = audit_record(row, numeric, old, addendum_record, ffprobe)
                result["numeric_evidence"] = {"path": numeric_path, "sha256": old["numeric_evidence_sha256"]}
                if addendum_spec:
                    result["endpoint_addendum_evidence"] = addendum_spec
                arrays[vid] = clock
            except Exception as exc:
                result = failed_record(row, old, exc)
            records.append(result)
        need(source_hashes == {p.name: sha(p) for p in Path(__file__).parent.glob("*.py")}, "V4_REAUDIT_SOURCE_CHANGED")
        summary = write_bundle(manifest, REMATCH_SHA, V3_RECEIPT_SHA, records, arrays, output, endpoint_sha)
        write_new(output / "execution_evidence.json", {"source_hashes": source_hashes,
            "wall_seconds": time.monotonic() - started, "frameworks_imported": False, "media_read": False,
            "original_manifest_rewritten": False, "numeric_files_rewritten": False})
        print(json.dumps(summary, allow_nan=False), flush=True)
        return 0 if summary["all_sources_usable"] else 1
    except Exception as exc:
        failure = {"status": "STOP_V4_REAUDIT_ADMISSION_OR_IO", "failure": str(exc),
            "expected_count": 426, "inference_allowed": False, "media_redecoded": False,
            "original_manifest_rewritten": False, "wall_seconds": time.monotonic() - started}
        if output is not None:
            write_new(output / "failed_scan_receipt.json", failure)
        print(json.dumps(failure), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
