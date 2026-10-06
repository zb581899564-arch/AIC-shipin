#!/usr/bin/env python3
"""Audit all 426 registered sources; preserve every failure, never infer."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
from a_contract import sha, validate_manifest, write_json
from time_origin_core import ORIGIN_CONTRACT, PASS_STATUS, audit_origin, finite

HERE = Path(__file__).resolve().parent
REGISTERED_MANIFEST_SHA = "57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32"
PRODUCTION_FILES = {"time_origin_core.py", "numeric_source_worker.py", "scan_source_origin.py"}


def verify_dependencies():
    lock = json.loads((HERE/"dependency_lock.json").read_text(encoding="utf-8"))
    if {r["path"] for r in lock["files"]} != {"a_contract.py", "vendor/p2j_core.py"}:
        raise ValueError("UNCHANGED_CPU_CONTRACT_DEPENDENCY_SET_MISMATCH")
    for r in lock["files"]:
        if sha(HERE/r["path"]) != r["sha256"]:
            raise ValueError("UNCHANGED_CPU_CONTRACT_DEPENDENCY_HASH_MISMATCH")
    source_lock = json.loads((HERE/"source_lock.json").read_text(encoding="utf-8"))
    if {r["path"] for r in source_lock["production_files"]} != PRODUCTION_FILES:
        raise ValueError("SOURCE_ORIGIN_PRODUCTION_SET_MISMATCH")
    for r in source_lock["production_files"]:
        if sha(HERE/r["path"]) != r["sha256"]:
            raise ValueError("SOURCE_ORIGIN_PRODUCTION_HASH_MISMATCH")
    return source_lock["production_files"]


def audit_numeric(row, numeric):
    audit = audit_origin(numeric["raw_pts_sec"], row["fps_num"], row["fps_den"], row["n_frames"],
                         numeric["stream_start_time"], numeric["stream_time_base"],
                         numeric["decord_timestamps"], numeric["decord_fps"], numeric["decord_frames"],
                         numeric["decord_numeric_epsilon"])
    extra = []
    if [numeric["width"], numeric["height"]] != [row["width"], row["height"]]:
        extra.append("REGISTERED_SOURCE_GEOMETRY_MISMATCH")
    if numeric["ffprobe_fps_num"]*row["fps_den"] != row["fps_num"]*numeric["ffprobe_fps_den"]:
        extra.append("REGISTERED_FFPROBE_AVERAGE_TIMEBASE_MISMATCH")
    if (numeric["raw_integer_pts_count"] != row["n_frames"] or
            numeric["raw_textual_pts_count"] != row["n_frames"]):
        extra.append("ALL_INTEGER_AND_TEXTUAL_RAW_PTS_REQUIRED")
    pair_error = numeric["max_integer_text_pts_error_sec"]
    if not finite(pair_error) or pair_error > 1e-6+1e-12:
        extra.append("INTEGER_TIMEBASE_AND_TEXTUAL_PTS_DISAGREE_OR_MISSING")
    start_tick, start = numeric["stream_start_pts_sec"], numeric["stream_start_time"]
    if not finite(start_tick) or not finite(start) or abs(start_tick-start) > 1e-6+1e-12:
        extra.append("STREAM_INTEGER_AND_TEXTUAL_START_ORIGIN_UNCONFIRMED")
    elif audit["raw_first_pts_sec"] is not None and abs(start_tick-audit["raw_first_pts_sec"]) > max(float(Fraction(numeric["stream_time_base"])), 1e-6):
        extra.append("STREAM_INTEGER_START_AND_FIRST_RAW_PTS_DISAGREE")
    audit["failures"].extend(extra)
    audit["pass"] = not audit["failures"]
    audit["stream_start_pts"] = numeric["stream_start_pts"]
    audit["stream_start_pts_sec"] = start_tick
    return audit


def run_numeric_worker(source, ffprobe, numeric_path, log_path, timeout, threads):
    command = [sys.executable, "-B", str(HERE/"numeric_source_worker.py"), "--source", str(source),
               "--ffprobe", str(ffprobe), "--output", str(numeric_path), "--decord-num-threads", str(threads)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with log_path.open("x", encoding="utf-8") as log:
        # A native crash or hang must fail this source and continue the audit.
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, env=env)


def scan_records(manifest, root, ffprobe, timeout, threads):
    numeric_root, record_root = root/"numeric", root/"records"
    numeric_root.mkdir()
    record_root.mkdir()
    allowed_roots = [Path(p).resolve() for p in manifest["allowed_source_roots"]]
    results, origins = [], []
    total = len(manifest["records"])
    for index, row in enumerate(manifest["records"], 1):
        vid = row["video_id"]
        result = {"video_id": vid, "source_sha256": row["source_sha256"], "pass": False, "failures": []}
        numeric_path, log_path = numeric_root/(vid+".numeric.json"), numeric_root/(vid+".worker.log")
        try:
            source = Path(row["source_path"]).resolve(strict=True)
            if not any(p in source.parents for p in allowed_roots) or sha(source) != row["source_sha256"]:
                raise ValueError("SOURCE_PATH_OR_BYTE_IDENTITY_MISMATCH")
            size_before = source.stat().st_size
            run_numeric_worker(source, ffprobe, numeric_path, log_path, timeout, threads)
            if source.stat().st_size != size_before or sha(source) != row["source_sha256"]:
                raise ValueError("SOURCE_BYTES_CHANGED_DURING_NUMERIC_SCAN")
            numeric = json.loads(numeric_path.read_text(encoding="utf-8"))
            audit = audit_numeric(row, numeric)
            result.update(audit, numeric_evidence_path=str(numeric_path), numeric_evidence_sha256=sha(numeric_path),
                          worker_log_path=str(log_path), decord_version=numeric["decord_version"],
                          decord_timestamp_dtype=numeric["decord_timestamp_dtype"],
                          source_bytes=size_before, source_hash_verified_before_and_after=True)
        except Exception as exc:
            # Retain the complete denominator; never convert failure to valid.
            code = str(exc) if re.fullmatch(r"[A-Z][A-Z0-9_]+", str(exc)) else type(exc).__name__
            result["failures"] = [code]
            result["failure_exception_type"] = type(exc).__name__
            result["failure_detail"] = str(exc)
            result["worker_log_path"] = str(log_path) if log_path.exists() else None
            if numeric_path.exists():
                result["numeric_evidence_path"] = str(numeric_path)
                result["numeric_evidence_sha256"] = sha(numeric_path)
        write_json(record_root/(vid+".identity.json"), result)
        results.append(result)
        origins.append({"video_id": vid, "source_sha256": row["source_sha256"],
                        "fps_num": row["fps_num"], "fps_den": row["fps_den"], "n_frames": row["n_frames"],
                        "raw_first_pts_sec": result.get("raw_first_pts_sec"),
                        "decord_clock_mode": result.get("decord_clock_mode", "UNCONFIRMED"),
                        "pass": result["pass"], "failures": result["failures"],
                        "numeric_evidence_sha256": result.get("numeric_evidence_sha256")})
        print(f"Source origin identity {index}/{total} pass={result['pass']}", flush=True)
    return results, origins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--expected-manifest-sha256", required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--ffprobe", type=Path, default=Path("/home/inspur/anaconda3/envs/Andy/bin/ffprobe"))
    ap.add_argument("--source-timeout-seconds", type=int, default=900)
    ap.add_argument("--decord-num-threads", type=int, default=0)
    args = ap.parse_args()
    if args.expected_manifest_sha256 != REGISTERED_MANIFEST_SHA or sha(args.manifest) != REGISTERED_MANIFEST_SHA:
        raise ValueError("REGISTERED_COMPLETE_M0_MANIFEST_HASH_REQUIRED")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    if manifest["kind"] != "REMATCH426" or len(manifest["records"]) != 426:
        raise ValueError("REGISTERED_426_SOURCE_SET_REQUIRED")
    production_hashes = verify_dependencies()
    root = args.output_root.resolve()
    if args.output_root.exists():
        raise FileExistsError("use a new evidence root; preserve old failure audit")
    if sys.platform.startswith("linux") and Path("/home/inspur/aic_video_work") not in root.parents:
        raise ValueError("source identity evidence must stay under aic_video_work")
    if args.source_timeout_seconds <= 0 or args.decord_num_threads < 0:
        raise ValueError("invalid registered CPU execution limits")
    if not args.ffprobe.is_file():
        raise ValueError("FFPROBE_EXECUTABLE_UNCONFIRMED")
    ffprobe_path = args.ffprobe.resolve(strict=True)
    version = subprocess.run([str(ffprobe_path), "-version"], check=True, capture_output=True, text=True, timeout=30).stdout
    root.mkdir(parents=True)
    results, origins = scan_records(manifest, root, ffprobe_path, args.source_timeout_seconds, args.decord_num_threads)
    failed = [r["video_id"] for r in results if not r["pass"]]
    passed = not failed and len(results) == 426
    registry = {"schema": "aic_source_time_origin_registry_v3", "origin_contract": ORIGIN_CONTRACT,
                "input_manifest_sha256": REGISTERED_MANIFEST_SHA, "records": origins,
                "all_sources_pass": passed, "failed_video_ids": failed}
    write_json(root/"origin_registry.json", registry)
    receipt = {"schema": "aic_source_origin_identity_v3", "status": PASS_STATUS if passed else "BLOCK_SOURCE_ORIGIN_IDENTITY",
               "origin_contract": ORIGIN_CONTRACT,
               "contract_authority": "LOCAL_SOURCE_FRAME_IDENTITY_NOT_OFFICIAL_TIMESTAMP_ORIGIN_REQUIREMENT",
               "input_manifest_sha256": REGISTERED_MANIFEST_SHA, "registered_sources": 426,
               "audited_sources": len(results), "passed_sources": len(results)-len(failed),
               "failed_video_ids": failed, "records": results, "origin_registry_sha256": sha(root/"origin_registry.json"),
               "one_frame_cfr_tolerance_changed": False, "zero_raw_pts_required": False,
               "source_bytes_modified": False, "images_exported_or_displayed": False,
               "pixels_may_be_decoded_internally": True, "automatic_all_frame_ffprobe_decord_metadata_scan": True,
               "labels_read": False, "models_run": False, "GPU_used": False, "inference_allowed": False,
               "source_timeout_seconds": args.source_timeout_seconds, "decord_num_threads": args.decord_num_threads,
               "source_code": production_hashes, "source_lock_sha256": sha(HERE/"source_lock.json"),
               "dependency_lock_sha256": sha(HERE/"dependency_lock.json"), "python_version": sys.version,
               "python_executable": sys.executable, "ffprobe_path": str(ffprobe_path),
               "ffprobe_sha256": sha(ffprobe_path), "ffprobe_version": version}
    write_json(root/"pts_origin_receipt.json", receipt)
    if passed:
        new_manifest = copy.deepcopy(manifest)
        new_manifest["input_contract"].update(
            source_pts_status=PASS_STATUS, source_pts_schema="aic_source_origin_identity_v3",
            source_time_origin_contract=ORIGIN_CONTRACT,
            source_pts_evidence=str(root/"pts_origin_receipt.json")+" SHA256 "+sha(root/"pts_origin_receipt.json"),
            source_origin_registry=str(root/"origin_registry.json"),
            source_origin_registry_sha256=sha(root/"origin_registry.json"))
        validate_manifest(new_manifest)
        write_json(root/"clean_manifest_426_pts_origin_v3.json", new_manifest)
        print("Origin-manifest SHA256", sha(root/"clean_manifest_426_pts_origin_v3.json"), flush=True)
    print(json.dumps({"status": receipt["status"], "audited_sources": len(results), "failed_video_ids": failed,
                      "receipt_sha256": sha(root/"pts_origin_receipt.json")}, ensure_ascii=False), flush=True)
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
