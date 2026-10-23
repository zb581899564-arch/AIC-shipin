"""Strict identities and native contracts for the separately authorized final sprint.

This module does not import a model, read labels, or revive an archived protocol.
A successful engineering check is never a quality claim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re

BASE_COMMIT = "e8224c4339007790a1be383be19fdb200cc817bc"
MAX_PARAMETERS = 9_000_000_000
PROTECTED = {
    "40.48": {"bytes": 384482, "sha256": "85778a086f3fb0152947ece40b8dc258c7fef717b40519fe3e23fd4f7b0fabbe"},
    "40.47": {"bytes": 384630, "sha256": "b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3"},
}
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_VERIFIED = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def strict_loads(text):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result

    def number(value):
        result = float(value)
        require(math.isfinite(result), "Nonfinite JSON number")
        return result

    def reject(value):
        raise ValueError("Nonfinite JSON: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_float=number, parse_constant=reject)


def strict_load(path):
    return strict_loads(Path(path).read_text(encoding="utf-8"))


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def stable_key(*values):
    return hashlib.sha256(canonical_bytes(values)).hexdigest()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file(), "A regular file is required: " + str(path))
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def checked(identity, root=None):
    """Hash each immutable file once per unchanged inode/stat identity in this process."""
    require(isinstance(identity, dict) and {"path", "sha256", "bytes"} <= identity.keys(),
            "Explicit absolute path, byte count and SHA256 required")
    require(isinstance(identity["path"], str) and Path(identity["path"]).is_absolute(),
            "Asset path must be absolute")
    require(isinstance(identity["sha256"], str) and _SHA.fullmatch(identity["sha256"]),
            "Full lowercase SHA256 required")
    require(type(identity["bytes"]) is int and identity["bytes"] >= 0, "Invalid asset byte count")
    path = Path(identity["path"]).resolve(strict=True)
    require(path.is_file(), "Referenced file is unavailable: " + str(path))
    if root is not None:
        require(path.is_relative_to(Path(root).resolve(strict=True)), "Asset escaped permitted root")
    stat = path.stat()
    require(stat.st_size == identity["bytes"], "Asset byte count changed: " + str(path))
    key = (str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    actual = _VERIFIED.get(key)
    if actual is None:
        actual = sha256(path)
        _VERIFIED[key] = actual
    require(actual == identity["sha256"], "Asset SHA256 changed: " + str(path))
    return path


def save_new(path, value):
    path = Path(path)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


def atomic_new(path, value):
    """Publish complete JSON with no replacement of an existing final artifact."""
    import uuid
    path = Path(path)
    temporary = path.with_name(path.name + ".partial-" + uuid.uuid4().hex)
    try:
        save_new(temporary, value)
        os.link(temporary, path)  # Atomic publish; raises if final already exists.
        temporary.unlink()
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()
    return ref(path)


def iter_refs(value):
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"} <= value.keys():
            yield value
        else:
            for item in value.values():
                yield from iter_refs(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_refs(item)


def protected_baselines(identities):
    require(set(identities) == set(PROTECTED), "Both protected baseline identities are required")
    result = {}
    for name, expected in PROTECTED.items():
        identity = identities[name]
        require(all(identity.get(key) == value for key, value in expected.items()),
                "Wrong protected " + name + " baseline identity")
        result[name] = checked(identity)
    return result


def ensure_output_isolated(output_dir, identities):
    output = Path(output_dir).resolve()
    require(output.is_absolute(), "Absolute output directory required")
    for identity in iter_refs(identities):
        source = Path(identity["path"]).resolve()
        require(source != output and not source.is_relative_to(output),
                "Output directory contains a protected/input asset")
        require(not output.is_relative_to(source), "Output is inside a file asset")
    return output


def native_clock(clock, expected_sha):
    require(isinstance(clock, dict) and clock.get("source_sha256") == expected_sha,
            "Native clock/media SHA mismatch")
    values = clock.get("normalized_exact_pts")
    require(isinstance(values, list) and values, "Complete exact native PTS list required")
    require(all(isinstance(v, (str, int)) and not isinstance(v, bool) for v in values),
            "PTS must use exact rationals, never rounded float seconds")
    pts = [Fraction(value) for value in values]
    end_value = clock.get("physical_end_exact")
    require(isinstance(end_value, (str, int)) and not isinstance(end_value, bool),
            "Physical endpoint must use an exact rational")
    end = Fraction(end_value)
    require(pts[0] == 0 and all(a < b for a, b in zip(pts, pts[1:])) and end > pts[-1],
            "Native PTS must increase strictly before a physical endpoint")
    if "first_original_pts_exact" in clock:
        origin = clock["first_original_pts_exact"]
        require(isinstance(origin, (str, int)) and not isinstance(origin, bool),
                "Original PTS origin must use an exact rational")
        origin = Fraction(origin)
    else:
        origin = None
    if "original_exact_pts" in clock:
        original = clock["original_exact_pts"]
        require(origin is not None and isinstance(original, list) and len(original) == len(pts) and
                all(isinstance(value, (str, int)) and not isinstance(value, bool) for value in original),
                "Original exact PTS require their explicit origin and complete native list")
        require([Fraction(value) - origin for value in original] == pts,
                "Original PTS origin/normalization differs from the registered native clock")
    if "physical_endpoint_evidence" in clock:
        witness = clock["physical_endpoint_evidence"]
        require(isinstance(witness, dict) and
                witness.get("kind") == "LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION",
                "Explicit positive last-native-frame duration evidence required")
        for name in ("last_normalized_pts_exact", "last_frame_duration_exact"):
            require(isinstance(witness.get(name), (str, int)) and not isinstance(witness.get(name), bool),
                    "Physical endpoint evidence must use exact rationals")
        duration = Fraction(witness["last_frame_duration_exact"])
        require(Fraction(witness["last_normalized_pts_exact"]) == pts[-1] and duration > 0 and
                pts[-1] + duration == end,
                "Physical endpoint differs from its positive original native-duration witness")
    return pts, end


def validate_sources(sources, *, expected_count=426, verify_media=True):
    require(isinstance(sources, list) and len(sources) == expected_count,
            "The complete registered source denominator is required")
    ids = [source.get("video_id") for source in sources]
    require(all(isinstance(sid, str) and sid for sid in ids) and len(set(ids)) == len(ids),
            "Unique string video_id required")
    if expected_count == 426:
        require(set(ids) == {str(i) for i in range(426)}, "Official 426 IDs differ")
    clocks, documents = {}, {}
    for source in sources:
        for field in ("width", "height", "n_frames"):
            require(type(source.get(field)) is int and source[field] > 0,
                    "Positive native dimension/count required: " + field)
        ratio = source.get("targetRatioWH")
        require(isinstance(ratio, list) and len(ratio) == 2 and
                all(type(v) is int and v > 0 for v in ratio), "Positive integer target ratio required")
        if verify_media:
            checked(source["media"])
        else:
            require(_SHA.fullmatch(source["media"]["sha256"]), "Actual media SHA required")
        clock_ref = source["clock"]
        clock_path = checked(clock_ref)
        clock_key = (str(clock_path), clock_ref["sha256"])
        if clock_key not in documents:
            documents[clock_key] = strict_load(clock_path)
        clock = documents[clock_key]
        if "source_key" in clock_ref:
            require(clock_ref["source_key"] == source["video_id"], "Aggregate clock source key differs")
            require(isinstance(clock, dict) and clock_ref["source_key"] in clock,
                    "Source missing from exact aggregate clock")
            clock = clock[clock_ref["source_key"]]
        pts, end = native_clock(clock, source["media"]["sha256"])
        require(len(pts) == source["n_frames"], "Native clock frame count differs")
        row = source.get("index_row")
        if row is not None:
            require(row.get("video_id") == source["video_id"] and
                    row.get("targetRatioWH") == ratio, "Original index identity/ratio differs")
        clocks[source["video_id"]] = (pts, end)
    return clocks


def _logical_shape(parameter):
    state = getattr(parameter, "quant_state", None)
    if state is not None and getattr(state, "shape", None) is not None:
        shape = tuple(int(v) for v in state.shape)
    else:
        class_name = type(parameter).__name__.lower()
        require(not any(name in class_name for name in ("params4bit", "int8params", "quantized")),
                "Packed parameter has no verifiable original tensor shape")
        shape = tuple(int(v) for v in parameter.shape)
    require(all(v >= 0 for v in shape), "Negative parameter dimension")
    return shape


def inspect_loaded_parameters(module, component_id, weight_files, *, parameter_sources=None, include=None):
    """Inventory actual loaded tensors, including LoRA and logical packed sizes.

    ``parameter_sources`` maps runtime names to ``{weight_ref, tensor_name}`` from
    the actual checkpoint load mapping. This allows two adapter views to share
    a base tensor only when they identify the exact same source bytes and key.
    Without that mapping the composite weight-file identity is used: this may
    overcount across model views, but can never silently subtract a model.
    ``include(name)`` is only for a complete, separately inventoried component
    partition; the caller must inventory every inference dependency.
    """
    require(isinstance(component_id, str) and component_id, "Component identity required")
    require(weight_files, "Actual loaded checkpoint files are required")
    weight_files = [dict(value) for value in weight_files]
    for identity in weight_files:
        checked(identity)
    allowed = {identity["sha256"] for identity in weight_files}
    composite = stable_key(sorted((r["sha256"], r["bytes"]) for r in weight_files))
    named = list(module.named_parameters(remove_duplicate=False))
    groups = {}
    for name, parameter in named:
        if include is not None and not include(name):
            continue
        shape = _logical_shape(parameter)
        elements = math.prod(shape)
        try:
            storage = parameter.untyped_storage()
            key = (parameter.device.type, parameter.device.index, storage.data_ptr(),
                   parameter.storage_offset(), parameter.numel(), str(parameter.dtype))
            require(storage.data_ptr() != 0 or elements == 0,
                    "Meta/unmaterialized parameters cannot prove actual loaded identity")
        except (AttributeError, RuntimeError):
            key = ("object", id(parameter))
        if key in groups:
            groups[key]["aliases"].append(name)
            continue
        source = (parameter_sources or {}).get(name)
        if source is not None:
            require(source["weight_ref"]["sha256"] in allowed,
                    "Tensor checkpoint source is outside this actual component")
            checked(source["weight_ref"])
            tensor_source = {"weight_sha256": source["weight_ref"]["sha256"],
                             "tensor_name": source["tensor_name"]}
        else:
            tensor_source = {"weight_sha256": composite, "tensor_name": name}
        require(isinstance(tensor_source["tensor_name"], str) and tensor_source["tensor_name"],
                "Exact checkpoint tensor name required")
        groups[key] = {"name": name, "aliases": [name], "shape": list(shape),
                       "elements": elements, "source": tensor_source}
    tensors = sorted(groups.values(), key=lambda row: row["name"])
    require(tensors, "Empty model component cannot establish a parameter inventory")
    return {"schema": "AIC_FINAL_PARAMETERS_V1", "origin": "actual_loaded",
            "component_id": component_id, "model_class": type(module).__module__ + "." + type(module).__name__,
            "weight_files": weight_files, "tensors": tensors,
            "total_elements": sum(t["elements"] for t in tensors),
            "quantization_does_not_reduce_parameters": True}


def total_parameters(receipt_refs):
    require(isinstance(receipt_refs, list) and receipt_refs, "Actual model inventories required")
    unique, names, receipts = {}, {}, []
    for identity in receipt_refs:
        value = strict_load(checked(identity))
        require(value.get("schema") == "AIC_FINAL_PARAMETERS_V1" and value.get("origin") == "actual_loaded",
                "Only actual loaded tensor inventories are accepted")
        require(value.get("quantization_does_not_reduce_parameters") is True, "Logical tensor accounting required")
        require(isinstance(value.get("component_id"), str) and value["component_id"], "Component ID required")
        files = value.get("weight_files")
        require(isinstance(files, list) and files, "Actual checkpoint identity list required")
        for file_ref in files:
            checked(file_ref)
        permitted = {r["sha256"] for r in files}
        permitted.add(stable_key(sorted((r["sha256"], r["bytes"]) for r in files)))
        tensors = value.get("tensors")
        require(isinstance(tensors, list) and tensors, "Actual tensor inventory required")
        declared = 0
        seen = set()
        for tensor in tensors:
            shape = tensor.get("shape")
            require(isinstance(shape, list) and all(type(v) is int and v >= 0 for v in shape),
                    "Tensor logical shape invalid")
            elements = math.prod(shape)
            require(type(tensor.get("elements")) is int and tensor["elements"] == elements,
                    "Tensor count is inconsistent with its logical shape")
            source = tensor.get("source", {})
            require(source.get("weight_sha256") in permitted and
                    isinstance(source.get("tensor_name"), str) and source["tensor_name"],
                    "Tensor must identify exact checkpoint bytes and original key")
            key = (source["weight_sha256"], source["tensor_name"])
            require(key not in seen, "Duplicate logical tensor within one component inventory")
            seen.add(key)
            require(key not in unique or unique[key] == tuple(shape),
                    "Shared tensor logical shape disagrees across model views")
            unique[key] = tuple(shape)
            declared += elements
        require(type(value.get("total_elements")) is int and declared == value["total_elements"],
                "Model total differs from actual tensor inventory")
        names.setdefault(value["component_id"], []).append(identity)
        receipts.append(identity)
    total = sum(math.prod(shape) for shape in unique.values())
    require(0 < total <= MAX_PARAMETERS, "Actual distinct main+aux parameters exceed 9B")
    return {"total_elements": total, "distinct_tensors": len(unique),
            "components": sorted(names), "receipt_refs": receipts,
            "sharing_rule": "identical_checkpoint_SHA_and_tensor_key_and_logical_shape"}
