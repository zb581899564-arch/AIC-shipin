"""Package only complete, genuinely different, source-bound native predictions.

No training or proxy-quality prerequisite is imposed here. These are immutable
artifact, inference-completion, parameter and geometry checks only. The two
protected packages are checked before and after every production packaging.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import fcntl
from fractions import Fraction
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import uuid
import zipfile

from .contracts import (atomic_new, canonical_bytes, checked, ensure_output_isolated,
    protected_baselines as check_protected, ref, require, strict_load, strict_loads,
    stable_key, total_parameters, utc_now, validate_sources)


def read_zip_rows(path):
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None,
                "ZIP must contain exactly predictions.jsonl with valid CRC")
        raw = archive.read("predictions.jsonl")
    rows = [strict_loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return rows



def baseline_frames(protected_baselines):
    """Read exact protected ZIPs into {baseline: {video_id: {frame: bbox}}}."""
    check_protected(protected_baselines)
    result = {}
    for name, identity in protected_baselines.items():
        result[name] = {}
        for row in read_zip_rows(checked(identity)):
            require(row["video_id"] not in result[name], "Duplicate baseline source")
            mapped = {}
            for prediction in row["predictions"]:
                require(prediction["frame"] not in mapped, "Duplicate baseline frame")
                mapped[prediction["frame"]] = prediction["bboxes"]
            result[name][row["video_id"]] = mapped
    return result

def prediction_identity(rows):
    """Exclude names/accounting and normalize numerically identical int/float boxes."""
    normalized = [{"video_id": row["video_id"], "targetRatioWH": row["targetRatioWH"],
                   "predictions": [{"frame": p["frame"], "bboxes": [float(v) for v in p["bboxes"]]}
                                   for p in sorted(row["predictions"], key=lambda p: p["frame"])]}
                  for row in sorted(rows, key=lambda row: row["video_id"])]
    return hashlib.sha256(canonical_bytes(normalized)).hexdigest()


def frame_boxes(rows):
    result = {}
    for row in rows:
        for prediction in row["predictions"]:
            key = (row["video_id"], prediction["frame"])
            require(key not in result, "Duplicate source/frame prediction")
            result[key] = tuple(float(value) for value in prediction["bboxes"])
    return result


def validate_box(box, source):
    require(isinstance(box, list) and len(box) == 3 and
            all(type(value) in (float, int) and math.isfinite(value) for value in box),
            "Each bbox must be three finite real values")
    # Fractions avoid admitting an out-of-bounds box through a floating epsilon.
    x, y, width = (Fraction(str(value)) for value in box)
    rw, rh = source["targetRatioWH"]
    height = width * rh / rw
    require(x >= 0 and y >= 0 and width > 0 and
            x + width <= source["width"] and y + height <= source["height"],
            "BBox or ratio-derived height leaves the original frame")


def _evidence_document(identity, source, binding_sha, allowed_components, cache):
    key = (identity["path"], identity["sha256"])
    if key not in cache:
        value = strict_load(checked(identity))
        require(value.get("schema") == "AIC_FINAL_SPATIAL_EVIDENCE_V1" and
                value.get("video_id") == source["video_id"] and
                value.get("source_sha256") == source["media"]["sha256"] and
                value.get("binding_sha256") == binding_sha,
                "Spatial proof source/code/config binding differs")
        components = value.get("model_components")
        require(isinstance(components, list) and set(components) <= allowed_components,
                "Spatial evidence uses an uninventoried model")
        require(isinstance(value.get("algorithm"), str) and value["algorithm"],
                "Automatic spatial algorithm provenance required")
        inputs = value.get("input_refs")
        require(isinstance(inputs, list) and inputs, "Spatial proof must bind its real field/observation inputs")
        for input_ref in inputs:
            checked(input_ref)
        frames = value.get("frames")
        require(isinstance(frames, list), "Spatial proof frame records required")
        mapped = {}
        for row in frames:
            frame = row.get("frame")
            require(type(frame) is int and 0 <= frame < source["n_frames"] and frame not in mapped,
                    "Spatial proof has duplicate/non-native frames")
            validate_box(row.get("bboxes"), source)
            mapped[frame] = tuple(float(v) for v in row["bboxes"])
        cache[key] = (value, mapped)
    value, mapped = cache[key]
    require(value["video_id"] == source["video_id"], "Spatial proof reused across sources")
    return mapped


def validate_results(sources, source_results, *, baselines, binding, allowed_components):
    require(isinstance(source_results, list) and len(source_results) == len(sources),
            "Missing/extra source execution results cannot become empty predictions")
    source_map = {source["video_id"]: source for source in sources}
    result_map = {result.get("video_id"): result for result in source_results}
    require(len(result_map) == len(source_results) and set(result_map) == set(source_map),
            "Source execution identities are incomplete or duplicated")
    old = {name: frame_boxes(rows) for name, rows in baselines.items()}
    proof_cache, rows, empty, total = {}, [], [], 0
    binding_sha = stable_key(binding)
    for sid in sorted(source_map):
        source, result = source_map[sid], result_map[sid]
        require(result.get("status") in {"SUCCESS_NONEMPTY", "SUCCESS_EMPTY"},
                "Failed/incomplete source cannot be packaged: " + sid)
        predictions = result.get("predictions")
        require(isinstance(predictions, list), "Explicit successful prediction list required")
        require((result["status"] == "SUCCESS_EMPTY") == (len(predictions) == 0),
                "Successful-empty/nonempty terminal contradicts output")
        require(result.get("source_sha256") == source["media"]["sha256"],
                "Prediction source media identity differs")
        require(result.get("binding_sha256") == binding_sha,
                "Source execution result belongs to a different exact candidate binding")
        frames = [p.get("frame") for p in predictions]
        require(all(type(frame) is int and 0 <= frame < source["n_frames"] for frame in frames) and
                frames == sorted(set(frames)), "Predictions must use sorted unique native frame ordinals")
        # Empty is an explicit model/selection outcome, never the absence of
        # proof. Validate its source/config/input evidence before iterating
        # frame-level provenance, whose loop is empty for a legal empty source.
        require(isinstance(result.get("evidence"), dict),
                "Every successful source, including empty, requires its exact execution evidence")
        declared = _evidence_document(result["evidence"], source, binding_sha, allowed_components, proof_cache)
        require(set(declared) == set(frames), "Source execution evidence frame set differs from predictions")
        provenance = result.get("spatial_provenance")
        require(isinstance(provenance, list) and len(provenance) == len(predictions),
                "Every predicted frame requires real spatial provenance")
        provenance_map = {record.get("frame"): record for record in provenance}
        require(set(provenance_map) == set(frames) and len(provenance_map) == len(provenance),
                "Spatial provenance frames differ from predictions")
        for prediction in predictions:
            frame, box = prediction["frame"], prediction["bboxes"]
            validate_box(box, source)
            proof = provenance_map[frame]
            require(proof.get("source_sha256") == source["media"]["sha256"],
                    "Spatial provenance media SHA differs")
            if proof.get("kind") == "baseline_exact":
                baseline_name = proof.get("baseline")
                require(baseline_name in old and (sid, frame) in old[baseline_name] and
                        tuple(float(v) for v in box) == old[baseline_name][(sid, frame)],
                        "Inherited bbox is not the exact original protected prediction")
                require(proof.get("evidence", {}).get("sha256") == binding["protected_baselines"][baseline_name]["sha256"],
                        "Inherited bbox must refer to its protected ZIP")
                checked(proof["evidence"])
            elif proof.get("kind") in {"native_spatial_field", "grounded", "automatic_spatial"}:
                mapped = _evidence_document(proof["evidence"], source, binding_sha, allowed_components, proof_cache)
                require(frame in mapped and mapped[frame] == tuple(float(v) for v in box),
                        "Output bbox differs from its actual frame-specific spatial proof")
            else:
                raise ValueError("Unknown/approximate/default spatial provenance kind")
        row = copy.deepcopy(source.get("index_row", {}))
        row.update(video_id=sid, targetRatioWH=list(source["targetRatioWH"]), predictions=predictions)
        rows.append(row)
        total += len(predictions)
        if not predictions:
            empty.append(sid)
    require(total > 0, "ALL_EMPTY_OUTPUT: diagnose the actual pipeline before consuming a submission")
    require(total < sum(source["n_frames"] for source in sources),
            "ALL_SELECTED_OUTPUT: diagnose the actual pipeline before consuming a submission")
    return rows, {"source_count": len(rows), "selected_frames": total, "empty_source_ids": empty,
                  "native_pts_checked": True, "all_spatial_provenance_checked": True,
                  "failed_sources_converted_to_empty": 0}


@contextmanager
def _history_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_name(path.name + ".lock").open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _history(path):
    if not path.exists():
        return []
    return [strict_loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _publish_bytes(path, data):
    """Package recovery may adopt exact already-written bytes; never overwrite."""
    if path.exists():
        require(path.read_bytes() == data, "Existing package artifact has different bytes: " + str(path))
        return ref(path)
    temporary = path.with_name(path.name + ".PENDING")
    if temporary.exists():
        if temporary.read_bytes() != data:
            # The enclosing history lock excludes another package writer. A
            # torn own-output write is preserved for inspection; the complete
            # deterministic result has already been rebuilt from durable
            # source successes, so recovery performs no new model inference.
            interrupted = temporary.with_name(temporary.name + ".interrupted-" + uuid.uuid4().hex)
            os.rename(temporary, interrupted)
    if not temporary.exists():
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    os.link(temporary, path)
    temporary.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return ref(path)


def _differences(rows, baseline):
    current, prior = frame_boxes(rows), frame_boxes(baseline)
    added, removed = set(current) - set(prior), set(prior) - set(current)
    changed = {key for key in set(current) & set(prior) if current[key] != prior[key]}
    changed_sources = {sid for sid, _ in added | removed | changed}
    return {"added_frames": len(added), "removed_frames": len(removed),
            "changed_boxes": len(changed), "changed_sources": len(changed_sources)}


def _candidate_contract(candidate_id, binding, rows, baselines):
    """A declared spatial-only comparison must actually hold temporal choices fixed."""
    candidate = binding.get("candidate", {})
    if candidate_id.startswith("g_") or candidate.get("selection") == "protected40.48":
        require(candidate.get("selection") == "protected40.48",
                "G candidates must explicitly bind protected40.48 temporal selection")
        current = set(frame_boxes(rows))
        original = set(frame_boxes(baselines["40.48"]))
        require(current == original,
                "G_TEMPORAL_DRIFT: spatial candidate added/deleted protected40.48 native frames")


def build_package(*, candidate_id, sources, source_results, parameter_receipts,
                  protected_baselines, binding, output_dir, history_path, expected_count=426):
    """Build/adopt one reproducible package, never submit it to the website.

    ``expected_count != 426`` exists for synthetic contract tests only and the
    resulting receipt is explicitly non-production. The production caller must
    leave it at its default. ``binding`` includes code/config/assets identities,
    ``required_model_components`` and both ``protected_baselines``.
    """
    require(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", candidate_id or ""), "Safe explicit candidate_id required")
    require(binding.get("protected_baselines") == protected_baselines,
            "Package binding must include the exact two protected baselines")
    if expected_count == 426:
        require(binding.get("candidate_id") == candidate_id and isinstance(binding.get("candidate"), dict),
                "Production package must bind this exact registered candidate ID/configuration")
        protected_paths = check_protected(protected_baselines)
    else:
        require(binding.get("synthetic_test_only") is True, "Reduced denominator is synthetic-test-only")
        require(set(protected_baselines) == {"40.48", "40.47"}, "Both test baseline controls required")
        protected_paths = {name: checked(identity) for name, identity in protected_baselines.items()}
    validate_sources(sources, expected_count=expected_count, verify_media=True)
    budget = total_parameters(parameter_receipts)
    required = binding.get("required_model_components")
    require(isinstance(required, list) and required and set(required) <= set(budget["components"]),
            "A baseline or candidate model dependency lacks actual parameter inventory")
    baselines = {name: read_zip_rows(path) for name, path in protected_paths.items()}
    expected_ids = {source["video_id"] for source in sources}
    for name, baseline in baselines.items():
        require(len(baseline) == expected_count and {row["video_id"] for row in baseline} == expected_ids,
                "Protected baseline source set differs")
        ratios = {row["video_id"]: row["targetRatioWH"] for row in baseline}
        require(all(ratios[s["video_id"]] == s["targetRatioWH"] for s in sources),
                "Target ratios differ from protected original indices")
    rows, checks = validate_results(sources, source_results, baselines=baselines,
                                    binding=binding, allowed_components=set(budget["components"]))
    _candidate_contract(candidate_id, binding, rows, baselines)
    for row in rows:
        row["model_params_b"] = budget["total_elements"] / 1e9
    digest = prediction_identity(rows)
    require(all(digest != prediction_identity(value) for value in baselines.values()),
            "DUPLICATE_BASELINE: file names/accounting changes are not a new prediction")
    out = ensure_output_isolated(output_dir, [sources, protected_baselines, parameter_receipts, binding])
    history_path = Path(history_path).resolve()
    require(not history_path.is_relative_to(out), "Submission history must live outside individual candidate output")
    payload = b"".join(canonical_bytes(row) + b"\n" for row in rows)
    member_sha = hashlib.sha256(payload).hexdigest()
    memory = io.BytesIO()
    info = zipfile.ZipInfo("predictions.jsonl", date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr(info, payload)
    zip_data = memory.getvalue()
    with _history_lock(history_path):
        history = _history(history_path)
        for old in history:
            if old.get("prediction_sha256") == digest:
                require(old.get("candidate_id") == candidate_id and old.get("output_dir") == str(out) and
                        old.get("binding_sha256") == stable_key(binding),
                        "DUPLICATE_CANDIDATE: predictions already packaged by another registered candidate")
        out.mkdir(parents=True, exist_ok=True)
        jsonl_ref = _publish_bytes(out / "predictions.jsonl", payload)
        zip_ref = _publish_bytes(out / ("candidate_FINAL_" + candidate_id.upper() + ".zip"), zip_data)
        with zipfile.ZipFile(checked(zip_ref)) as archive:
            require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None and
                    hashlib.sha256(archive.read("predictions.jsonl")).hexdigest() == member_sha,
                    "Final ZIP CRC/member SHA differs from reviewed predictions")
        require(prediction_identity(read_zip_rows(zip_ref["path"])) == digest,
                "Final ZIP native prediction round trip differs")
        for identity in protected_baselines.values():
            checked(identity)
        receipt_path = out / "package_receipt.json"
        result = {"schema": "AIC_FINAL_PACKAGE_V1", "candidate_id": candidate_id,
                  "status": "ENGINEERING_ACCEPTED_QUALITY_UNVALIDATED" if expected_count == 426 else "SYNTHETIC_TEST_ONLY",
                  "binding": binding, "binding_sha256": stable_key(binding),
                  "zip_ref": zip_ref, "member_ref": jsonl_ref, "member_sha256": member_sha,
                  "prediction_sha256": digest, "checks": checks, "parameter_budget": budget,
                  "changes_from_baselines": {name: _differences(rows, baseline) for name, baseline in baselines.items()},
                  "protected_baselines_unchanged": True, "offline_quality_validated": False,
                  "official_score": "UNKNOWN", "website_submitted": False,
                  "output_dir": str(out), "completed_at": utc_now()}
        if receipt_path.exists():
            old = strict_load(receipt_path)
            require(old["binding_sha256"] == result["binding_sha256"] and
                    old["prediction_sha256"] == digest and old["zip_ref"] == zip_ref,
                    "Existing completion belongs to a different package")
            result = old
        else:
            atomic_new(receipt_path, result)
        if not any(old.get("prediction_sha256") == digest for old in history):
            entry = {"candidate_id": candidate_id, "prediction_sha256": digest,
                     "binding_sha256": result["binding_sha256"], "output_dir": str(out),
                     "receipt_ref": ref(receipt_path), "zip_ref": zip_ref,
                     "member_sha256": member_sha, "website_submitted": False}
            with history_path.open("ab") as stream:
                stream.write(canonical_bytes(entry) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
    return result


def verify_transfer(package_receipt, received_zip):
    """Run at the receiving end against the Linux final receipt; no repacking."""
    receipt = strict_load(checked(package_receipt)) if "path" in package_receipt else package_receipt
    received = ref(received_zip)
    require(received["bytes"] == receipt["zip_ref"]["bytes"] and
            received["sha256"] == receipt["zip_ref"]["sha256"], "Transferred ZIP is not the Linux final byte stream")
    with zipfile.ZipFile(received_zip) as archive:
        require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None and
                hashlib.sha256(archive.read("predictions.jsonl")).hexdigest() == receipt["member_sha256"],
                "Transferred member SHA/CRC differs")
    require(prediction_identity(read_zip_rows(received_zip)) == receipt["prediction_sha256"],
            "Transferred prediction identity differs")
    return {"status": "TRANSFER_IDENTICAL", "received_zip": received,
            "linux_zip": receipt["zip_ref"], "member_sha256": receipt["member_sha256"],
            "prediction_sha256": receipt["prediction_sha256"], "website_submitted": False}
