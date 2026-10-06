#!/usr/bin/env python3
"""Bound historical non-test eight CFR registry. No new frame/media reading."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from native_clock_core import audit_record, need
from registry_io import (NONTEST_SHA, V3_WORKER_SHA, failed_record, keyed_records, load_numeric, read_bound,
                         validate_manifest, verify_source_lock, write_bundle, write_new)

COLLECTOR_SHA = "612da27ff7a1c360557d80ce5f0aa3ae9c00d1346fb88c04d3ca02964da3f2cc"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--collector-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--numeric-root", type=Path)
    args = parser.parse_args()
    output = None
    try:
        verify_source_lock()
        manifest = read_bound(args.manifest, NONTEST_SHA)
        validate_manifest(manifest, "NONTEST_FROZEN8")
        collector = read_bound(args.collector_receipt, COLLECTOR_SHA)
        need(collector.get("schema") == "aic_nontest_numeric_clock_v1" and collector.get("source_count") == 8
             and collector.get("input_manifest_sha256") == NONTEST_SHA
             and collector.get("numeric_worker_sha256") == V3_WORKER_SHA,
             "BOUND_FROZEN_WORKER_NONTEST_EIGHT_COLLECTOR_REQUIRED")
        need(collector.get("labels_read") is False and collector.get("models_run") is False
             and collector.get("GPU_used") is False and collector.get("source_bytes_modified") is False
             and collector.get("images_exported_or_displayed") is False, "NONTEST_COLLECTOR_SCOPE_MISMATCH")
        prior = keyed_records(collector, manifest["records"])
        args.output_root.mkdir(parents=True, exist_ok=False)
        output = args.output_root
        records, arrays = [], {}
        for row in manifest["records"]:
            vid, evidence = row["video_id"], prior[row["video_id"]]
            old = dict(evidence.get("v3_audit") or {})
            old.update(video_id=vid, source_sha256=evidence.get("source_sha256"),
                source_hash_verified_before_and_after=evidence.get("source_hash_verified_before_and_after"),
                media_rewritten=False, numeric_evidence_path=evidence.get("numeric_evidence_path"),
                numeric_evidence_sha256=evidence.get("numeric_evidence_sha256"))
            try:
                numeric, path = load_numeric(old, args.numeric_root)
                result, clock = audit_record(row, numeric, old)
                need(result["cfr_eligible"] and result["usable"], "NONTEST_CFR_ONLY_SCOPE_REQUIRED")
                result["numeric_evidence"] = {"path": path, "sha256": old["numeric_evidence_sha256"]}
                arrays[vid] = clock
            except Exception as exc:
                result = failed_record(row, old, exc)
            records.append(result)
        summary = write_bundle(manifest, NONTEST_SHA, COLLECTOR_SHA, records, arrays, output)
        print(json.dumps(summary), flush=True)
        return 0 if summary["all_sources_usable"] else 1
    except Exception as exc:
        failure = {"status": "STOP_NONTEST_REGISTRY_ADMISSION_OR_IO", "expected_count": 8,
            "failure": str(exc), "inference_allowed": False, "media_redecoded": False}
        if output is not None:
            write_new(output / "failed_scan_receipt.json", failure)
        print(json.dumps(failure), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
