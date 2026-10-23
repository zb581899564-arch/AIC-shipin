"""Opt-in, lossless BF16 weight expansion for isolated FP32 inference.

No model clone is made. Each owned tensor replaces only its own storage, and
the original BF16 canonical identity is proved again from bounded round trips.
"""
from __future__ import annotations

import hashlib
import json


LOSSLESS_FP32_PROFILE = "LOSSLESS_BF16_WEIGHTS_FP32_ARITHMETIC_V1"
_CHUNK_ELEMENTS = 1 << 22


def _require(value, message):
    if not value:
        raise ValueError(message)


def requested_profile(spec):
    profile = spec.get("arithmetic_profile")
    _require(profile in (None, LOSSLESS_FP32_PROFILE), "Unknown Qwen arithmetic profile")
    _require(not (profile and spec.get("adapter_dir")),
             "Lossless FP32 arithmetic profile refuses the TIME adapter")
    return profile


def _owned_tensors(model):
    """Keep tensor references, never copies; distinguish aliases from views."""
    groups, storage = {}, {}
    for kind, named in (("parameter", model.named_parameters(remove_duplicate=False)),
                        ("buffer", model.named_buffers(remove_duplicate=False))):
        for name, tensor in named:
            if id(tensor) in groups:
                _require(groups[id(tensor)]["kind"] == kind, "Tensor aliases cross parameter/buffer roles")
                groups[id(tensor)]["aliases"].append(name)
                continue
            _require(tensor.device.type != "meta", "Unmaterialized tensor cannot prove FP32 conversion")
            pointer = (str(tensor.device), tensor.untyped_storage().data_ptr())
            if tensor.numel():
                _require(pointer not in storage, "Distinct tensor objects share storage during FP32 conversion")
                storage[pointer] = name
            _require(not tensor.requires_grad and tensor.grad is None,
                     "FP32 conversion requires frozen tensors without gradients")
            groups[id(tensor)] = dict(kind=kind, name=name, aliases=[name], tensor=tensor,
                                     shape=list(tensor.shape), numel=tensor.numel(),
                                     device=str(tensor.device), dtype=str(tensor.dtype))
    return list(groups.values())


def _layout(rows):
    fields = ("kind", "name", "aliases", "shape", "numel", "device")
    return [{**{key: row[key] for key in fields}, "object_id": id(row["tensor"])} for row in rows]


def _chunks(tensor):
    flat = tensor.detach().reshape(-1)
    for offset in range(0, flat.numel(), _CHUNK_ELEMENTS):
        yield flat[offset:offset + _CHUNK_ELEMENTS]


def _update_bytes(digest, tensor, torch, *, original_dtype=None):
    for chunk in _chunks(tensor):
        if original_dtype is not None:
            restored = chunk.to(dtype=original_dtype)
            _require(bool(torch.equal(chunk, restored.to(dtype=chunk.dtype))),
                     "FP32 values are not an exact expansion of the original tensor dtype")
            chunk = restored
        digest.update(chunk.contiguous().view(torch.uint8).cpu().numpy().tobytes())


def bf16_roundtrip_identity(model, torch):
    """Use the inherited canonical ordering, names, shapes and BF16 byte format."""
    parameters, seen = {}, set()
    for name, parameter in model.named_parameters(remove_duplicate=False):
        if id(parameter) in seen:
            continue
        seen.add(id(parameter))
        _require("lora_" not in name and not parameter.requires_grad and parameter.grad is None,
                 "FP32 profile requires only frozen BASE parameters")
        _require(parameter.dtype == torch.float32, "FP32 profile retained a non-FP32 parameter")
        canonical = name.removeprefix("base_model.model.").replace(".base_layer.", ".")
        _require(canonical not in parameters, "Ambiguous canonical frozen parameter")
        parameters[canonical] = parameter
    digest, count = hashlib.sha256(), 0
    for name, parameter in sorted(parameters.items()):
        digest.update(name.encode())
        digest.update(str(tuple(parameter.shape)).encode())
        digest.update(str(torch.bfloat16).encode())
        _update_bytes(digest, parameter, torch, original_dtype=torch.bfloat16)
        count += parameter.numel()
    return dict(sha256=digest.hexdigest(), parameters=count,
                method="sorted canonical names and all unique frozen parameter bytes")


def _buffer_identity(rows, torch, *, roundtrip=False):
    digest = hashlib.sha256()
    for row in sorted((row for row in rows if row["kind"] == "buffer"), key=lambda row: row["name"]):
        digest.update(json.dumps({key: row[key] for key in
                                  ("name", "aliases", "shape", "numel", "dtype")},
                                 sort_keys=True, separators=(",", ":")).encode())
        original_dtype = torch.bfloat16 if roundtrip and row["dtype"] == str(torch.bfloat16) else None
        _update_bytes(digest, row["tensor"], torch, original_dtype=original_dtype)
    return digest.hexdigest()


def _cast_owned_tensors(rows, torch):
    # Frozen inference tensors have no autograd history to preserve. Updating
    # their storage preserves Parameter/Tensor objects and every tied alias.
    with torch.no_grad():
        for row in rows:
            tensor = row["tensor"]
            if tensor.is_floating_point() and tensor.dtype != torch.float32:
                tensor.data = tensor.data.to(dtype=torch.float32)


def configure_fp32_backend(torch):
    # The authorized CLI owns this inference process/thread. Image generation
    # keeps its original implementation and inherits this explicit setting.
    torch.set_autocast_enabled(False)
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    _require(not torch.is_autocast_enabled(), "CUDA autocast remains enabled for FP32 inference")
    return dict(float32_matmul_precision=torch.get_float32_matmul_precision(),
                cuda_matmul_allow_tf32=bool(torch.backends.cuda.matmul.allow_tf32),
                cudnn_allow_tf32=bool(torch.backends.cudnn.allow_tf32),
                cuda_autocast_enabled=bool(torch.is_autocast_enabled()))


def lossless_fp32_conversion(model, torch, original_identity):
    """Convert only after the runtime has verified its strict original identity."""
    _require(original_identity.get("verified_before_adapter") is True
             and original_identity.get("expected_sha256") == original_identity.get("sha256"),
             "Verified original BF16 canonical identity is required before FP32 conversion")
    rows = _owned_tensors(model)
    for row in rows:
        tensor = row["tensor"]
        _require(not tensor.is_complex(), "Complex tensors are outside the FP32 arithmetic profile")
        if row["kind"] == "parameter":
            _require(tensor.dtype == torch.bfloat16 and "lora_" not in row["name"],
                     "FP32 profile requires original BF16 BASE weights and no adapter")
        elif tensor.is_floating_point():
            _require(tensor.dtype in (torch.bfloat16, torch.float32),
                     "Unexpected floating buffer dtype in BF16 BASE")
    parameters = [row for row in rows if row["kind"] == "parameter"]
    _require(parameters and sum(row["numel"] for row in parameters) == original_identity["parameters"],
             "Original BASE parameter count changed before FP32 conversion")
    before_layout = _layout(rows)
    buffer_sha256 = _buffer_identity(rows, torch)
    backend = configure_fp32_backend(torch)
    _cast_owned_tensors(rows, torch)
    after = _owned_tensors(model)
    _require(_layout(after) == before_layout, "FP32 conversion changed tensor objects, aliases, shapes or counts")
    _require(all(row["tensor"].dtype == torch.float32 for row in after
                 if row["tensor"].is_floating_point()), "FP32 conversion left lower-precision arithmetic tensors")
    roundtrip = bf16_roundtrip_identity(model, torch)
    _require(roundtrip["sha256"] == original_identity["sha256"]
             and roundtrip["parameters"] == original_identity["parameters"],
             "FP32 round-trip canonical BASE identity differs from original BF16 weights")
    _require(_buffer_identity(rows, torch, roundtrip=True) == buffer_sha256,
             "FP32 conversion changed original buffer bytes or aliases")
    return dict(schema="AIC_LOSSLESS_FP32_ARITHMETIC_PROOF_V1", arithmetic_profile=LOSSLESS_FP32_PROFILE,
                source_parameter_dtype=str(torch.bfloat16), materialized_parameter_dtype=str(torch.float32),
                original_BF16_identity_verified_before_conversion=True, roundtrip_BASE_identity=roundtrip,
                exact_original_values_preserved=True, original_buffer_inventory_sha256=buffer_sha256,
                unique_parameter_tensors=len(parameters), unique_buffers=len(rows) - len(parameters),
                tensor_objects_aliases_shapes_counts_unchanged=True, all_tensors_frozen=True,
                conversion="OWNED_TENSOR_STORAGE_REPLACEMENT_NO_MODEL_COPY", backend=backend,
                inference_autocast_disabled=True, training_updates=0)
