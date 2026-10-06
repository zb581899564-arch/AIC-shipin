"""Bound metadata I/O and new v2 manifest writer. Stdlib only, no media I/O."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

from native_clock_core import need

REMATCH_SHA = "57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32"
V3_RECEIPT_SHA = "efcb86a8435523e53c17e86eedc9506e134b9571a84acdd0ebf5e8af8d17bff5"
NONTEST_SHA = "7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a"
V3_WORKER_SHA = "0ab8632ded07c7b3c13c362845d7e46d68f67d721ccd2bd74eff58bb0bd81638"
PRODUCTION_FILES = {"native_clock_core.py", "registry_io.py", "scan_native_clock.py", "build_nontest_registry.py"}
RECORD_KEYS = {"video_id", "source_group", "source_path", "source_sha256", "width", "height", "n_frames",
               "fps_num", "fps_den", "targetRatioWH", "scope_start_sec", "scope_end_sec"}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_bound(path, expected):
    need(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "EXPECTED_METADATA_SHA256_REQUIRED")
    raw = Path(path).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, "METADATA_SHA256_MISMATCH:" + str(path))
    return json.loads(raw.decode("utf-8"))


def verify_source_lock(directory=None):
    directory = Path(directory) if directory is not None else Path(__file__).parent
    lock = json.loads((directory / "source_lock.json").read_text(encoding="utf-8"))
    need(lock.get("schema") == "aic_native_clock_source_lock_v4", "V4_SOURCE_LOCK_SCHEMA_MISMATCH")
    files = lock.get("production_files", [])
    need(len(files) == len(PRODUCTION_FILES) and {r["path"] for r in files} == PRODUCTION_FILES,
         "V4_SOURCE_LOCK_FILE_SET_MISMATCH")
    for row in files:
        need(sha(directory / row["path"]) == row["sha256"], "V4_SOURCE_LOCK_SHA_MISMATCH:" + row["path"])
    return {r["path"]: r["sha256"] for r in files}


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def validate_manifest(manifest, kind):
    expected = 426 if kind == "REMATCH426" else 8 if kind == "NONTEST_FROZEN8" else None
    need(manifest.get("schema") == "aic_rematch_A_input_v1" and manifest.get("kind") == kind
         and manifest.get("expected_count") == expected, "REGISTERED_ORIGINAL_MANIFEST_SCHEMA_COUNT_REQUIRED")
    contract = manifest.get("input_contract", {})
    need(contract.get("status") == "APPROVED_METADATA_ONLY", "ORIGINAL_METADATA_PERMISSION_REQUIRED")
    need(contract.get("contest_jsonl_values_used") in (False, "APPROVED_METADATA_ONLY"), "SEMANTIC_LABELS_FORBIDDEN")
    for field in ("data_use_evidence", "metadata_role_evidence", "target_ratio_evidence"):
        need(isinstance(contract.get(field), str) and contract[field], "MISSING_ORIGINAL_METADATA_USE_EVIDENCE")
    rows = manifest.get("records", [])
    need(len(rows) == expected and len({row["video_id"] for row in rows}) == expected, "COMPLETE_UNIQUE_MANIFEST_DENOMINATOR_REQUIRED")
    roots = [PurePosixPath(p) for p in manifest.get("allowed_source_roots", [])]
    need(roots, "ORIGINAL_ALLOWED_MEDIA_ROOTS_REQUIRED")
    seen_paths = set()
    for row in rows:
        need(set(row) == RECORD_KEYS, "ORIGINAL_MANIFEST_UNKNOWN_OR_LABEL_FIELDS")
        vid = row["video_id"]
        need(isinstance(vid, str) and re.fullmatch(r"[a-zA-Z0-9_-]+", vid), "INVALID_SOURCE_ID")
        if kind == "REMATCH426":
            need(vid.isdigit(), "REMATCH_ARCHIVE_STEM_REQUIRED")
        path = PurePosixPath(row["source_path"])
        need(path.is_absolute() and ".." not in path.parts and any(root in path.parents for root in roots)
             and str(path) not in seen_paths, "SOURCE_METADATA_PATH_SCOPE_MISMATCH")
        seen_paths.add(str(path))
        need(re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"]), "SOURCE_SHA256_REQUIRED")
        need(all(type(row[k]) is int and row[k] > 0 for k in ("width", "height", "n_frames", "fps_num", "fps_den")),
             "REGISTERED_SOURCE_GEOMETRY_FPS_REQUIRED")
        need(row["targetRatioWH"] in ([9, 16], [16, 9]), "REGISTERED_TARGET_RATIO_REQUIRED")
        start, end = row["scope_start_sec"], row["scope_end_sec"]
        need(all(type(p) in (int, float) and math.isfinite(p) for p in (start, end))
             and 0 <= start < end <= row["n_frames"] * row["fps_den"] / row["fps_num"] + 1e-6,
             "ORIGINAL_SCOPE_INVALID")


def keyed_records(receipt, rows):
    records = receipt.get("records")
    need(isinstance(records, list) and len(records) == len(rows), "RECEIPT_COMPLETE_DENOMINATOR_REQUIRED")
    keyed = {r["video_id"]: r for r in records}
    need(len(keyed) == len(rows) and set(keyed) == {r["video_id"] for r in rows}, "RECEIPT_ID_SET_MISMATCH")
    return keyed


def load_numeric(prior, numeric_root=None):
    path = Path(prior["numeric_evidence_path"])
    need(path.name == prior["video_id"] + ".numeric.json", "BOUND_NUMERIC_SOURCE_ID_PATH_MISMATCH")
    if numeric_root is not None:
        path = Path(numeric_root) / path.name
    return read_bound(path, prior["numeric_evidence_sha256"]), str(path)


def load_addendum(path, expected_sha, root=None):
    if path is None:
        need(expected_sha is None, "ADDENDUM_SHA_WITHOUT_FILE")
        return {}, None
    value = read_bound(path, expected_sha)
    need(value.get("schema") == "aic_native_endpoint_addendum_v1", "UNREGISTERED_ENDPOINT_ADDENDUM_SCHEMA")
    rows = value.get("records", [])
    need(isinstance(rows, list) and len({r["video_id"] for r in rows}) == len(rows), "ENDPOINT_DUPLICATE_SOURCE_ID")
    result = {}
    for row in rows:
        spec = row.get("ffprobe_json")
        need(isinstance(spec, dict) and isinstance(spec.get("path"), str), "BOUND_RAW_FFPROBE_JSON_REQUIRED")
        actual = Path(spec["path"])
        if root is not None:
            actual = Path(root) / actual.name
        try:
            raw = read_bound(actual, spec.get("sha256"))
            result[row["video_id"]] = (row, raw, {"path": str(actual), "sha256": spec["sha256"]})
        except Exception as exc:
            result[row["video_id"]] = (row, None, {"failure": str(exc)})
    return result, sha(path)


def failed_record(row, prior, exception):
    return {"video_id": row["video_id"], "source_sha256": row["source_sha256"], "n_frames": row["n_frames"],
        "fps_num": row["fps_num"], "fps_den": row["fps_den"], "identity_pass": False, "native_clock_usable": False,
        "cfr_eligible": False, "native_end_sec": None, "duration_seconds": None, "usable": False,
        "status": "STOP_SOURCE_CLOCK_EVIDENCE", "failures": [str(exception)],
        "terminal_evidence": {"status": "STOP_MISSING_OR_INVALID_NATIVE_ENDPOINT", "kind": "UNPROVEN"},
        "v3_pass": prior.get("pass"), "v3_failures": prior.get("failures", []), "inference_allowed": False,
        "legacy_a_admission_granted": False}


def write_bundle(manifest, manifest_sha, prior_sha, records, arrays, output, addendum_sha=None):
    output = Path(output)
    need(output.is_dir(), "NEW_OUTPUT_ROOT_MUST_BE_CLAIMED")
    array_root = output / "clock_arrays"
    array_root.mkdir(exist_ok=False)
    need(len(records) == manifest["expected_count"] and [r["video_id"] for r in records]
         == [r["video_id"] for r in manifest["records"]], "FULL_ORDERED_OUTPUT_DENOMINATOR_REQUIRED")
    for result in records:
        vid = result["video_id"]
        if arrays.get(vid) is not None:
            path = array_root / (vid + ".clock.json")
            write_new(path, arrays[vid])
            result["clock_arrays"] = {"path": str(path.resolve()), "sha256": sha(path)}
    failures = [r["video_id"] for r in records if not r["usable"]]
    registry = {"schema": "aic_source_clock_registry_v4", "kind": manifest["kind"], "expected_count": manifest["expected_count"],
        "input_manifest_sha256": manifest_sha, "v3_receipt_sha256": prior_sha, "endpoint_addendum_sha256": addendum_sha,
        "all_identity_pass": all(r["identity_pass"] for r in records), "all_sources_usable": not failures,
        "all_cfr_eligible": all(r["cfr_eligible"] for r in records), "failed_video_ids": failures, "records": records,
        "origin_contract": "SOURCE_RELATIVE_ZERO_IS_SOURCE_FRAME_0_RAW_PTS_MINUS_FIRST_FRAME_PTS",
        "inference_allowed": False, "legacy_a_admission_granted": False,
        "cfr_tolerance_changed": False, "source_bytes_modified": False, "labels_read": False,
        "models_run": False, "GPU_used": False, "media_redecoded": False,
        "v3_integer_arrays_were_not_retained": True, "v3_packet_durations_were_not_retained": True}
    registry_path = output / "clock_registry.json"
    write_new(registry_path, registry)
    manifest_path = None
    if not failures:
        clean = copy.deepcopy(manifest)
        clean.update(schema="aic_rematch_A_input_v2", input_manifest_sha256=manifest_sha,
                     clock_registry={"path": str(registry_path.resolve()), "sha256": sha(registry_path)})
        keyed = {r["video_id"]: r for r in records}
        for row in clean["records"]:
            clock = keyed[row["video_id"]]
            row.update(clock_record_id=row["video_id"], clock_branch=clock["clock_branch"])
            if clock["clock_branch"] == "NATIVE_PTS":
                need(clean["kind"] == "REMATCH426" and row["scope_start_sec"] == 0, "NATIVE_SCOPE_EXTENSION_NOT_REGISTERED")
                row["scope_end_sec"] = clock["duration_seconds"]
        clean["input_contract"].update(source_pts_status="BOUND_V4_IDENTITY_AND_CLOCK_BRANCHES",
            source_pts_evidence="new clock registry; no old A/full inference admission granted")
        manifest_path = output / "clean_manifest_v2.json"
        write_new(manifest_path, clean)
    summary = {"schema": "aic_source_native_clock_reaudit_v4", "kind": manifest["kind"],
        "status": "PASS_ALL_SOURCE_CLOCK_BRANCHES_METADATA_ONLY" if not failures else "STOP_SOURCE_CLOCK_EVIDENCE",
        "expected_count": manifest["expected_count"], "audited_sources": len(records),
        "identity_passed_sources": sum(r["identity_pass"] for r in records), "usable_sources": len(records) - len(failures),
        "cfr_eligible_sources": sum(r["cfr_eligible"] for r in records),
        "native_non_cfr_usable_sources": sum(r["native_clock_usable"] for r in records), "failed_video_ids": failures,
        "input_manifest_sha256": manifest_sha, "v3_receipt_sha256": prior_sha, "endpoint_addendum_sha256": addendum_sha,
        "clock_registry": {"path": str(registry_path.resolve()), "sha256": sha(registry_path)},
        "clean_manifest": {"path": str(manifest_path.resolve()), "sha256": sha(manifest_path)} if manifest_path else None,
        "all_sources_usable": not failures, "inference_allowed": False, "legacy_a_admission_granted": False,
        "cfr_tolerance_changed": False, "media_redecoded": False, "labels_read": False, "models_run": False, "GPU_used": False}
    write_new(output / "reaudit_receipt.json", summary)
    return summary
