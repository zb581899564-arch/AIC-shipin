"""CPU-only inventory of inherited, exact inference dependencies.

Factories instantiate the real classes and strictly load the registered
checkpoints before counting actual named_parameters. The LoRA helper loads
only exact adapter parameter tensors into a small ParameterDict. Neither path
performs inference/training, constructs a substitute model, nor infers counts
from a public nominal model size.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import sys

from .contracts import (atomic_new, checked, inspect_loaded_parameters, ref, require,
                        stable_key, strict_load, utc_now)


def _select(value, selectors):
    for selector in selectors:
        require(isinstance(selector, (str, int)) and not isinstance(selector, bool),
                "Explicit integer/key factory output selectors required")
        if isinstance(selector, int):
            require(isinstance(value, (list, tuple)), "Integer output selector needs tuple/list")
            value = value[selector]
        elif isinstance(value, dict):
            value = value[selector]
        else:
            value = getattr(value, selector)
    return value


def _validate_roots(spec):
    roots, files = [], {}
    for entry in spec.get("code_roots", []):
        root = Path(entry["path"]).resolve(strict=True)
        require(root.is_dir() and root.is_absolute(), "Exact code import root required")
        require(isinstance(entry.get("files"), list) and entry["files"],
                "Code import roots require an explicit SHA-bound file inventory")
        for identity in entry["files"]:
            path = checked(identity, root)
            require(path not in files or files[path] == identity, "Conflicting code file identities")
            files[path] = identity
        roots.append(root)
    module_path = checked(spec["factory"]["module_ref"])
    files[module_path] = spec["factory"]["module_ref"]
    for identity in spec.get("dependency_refs", []):
        files[checked(identity)] = identity
    return roots, files, module_path


@contextmanager
def _cpu_factory_environment(roots, code_files):
    require(os.environ.get("CUDA_VISIBLE_DEVICES") in ("", "-1"),
            "Run inventory in a separate CPU-only process with CUDA_VISIBLE_DEVICES='' before importing torch")
    import torch
    require(not torch.cuda.is_initialized(), "Inherited inventory must not share a running GPU process")
    torch.set_num_threads(2)
    before_path, before_modules = list(sys.path), set(sys.modules)
    old_offline = {name: os.environ.get(name) for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    prior_init = torch.cuda._lazy_init

    def deny_cuda(*args, **kwargs):
        raise RuntimeError("The inventory factory may not initialize CUDA")

    # This changes this short-lived inventory process only, never a host service.
    torch.cuda._lazy_init = deny_cuda
    for name in old_offline:
        os.environ[name] = "1"
    sys.path[:0] = [str(path) for path in roots]
    try:
        yield torch
        for module in list(sys.modules.values()):
            name = getattr(module, "__file__", None)
            if not name:
                continue
            path = Path(name).resolve()
            if path.suffix == ".pyc":
                try:
                    path = Path(importlib.util.source_from_cache(str(path))).resolve()
                except ValueError:
                    pass
            if any(path.is_relative_to(root) for root in roots):
                require(path in code_files, "Factory imported unbound local code: " + str(path))
                checked(code_files[path])
    finally:
        sys.path[:] = before_path
        torch.cuda._lazy_init = prior_init
        for name, value in old_offline.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        # Avoid old flat modules such as `runtime`/`models` poisoning another factory.
        for name in set(sys.modules) - before_modules:
            module = sys.modules.get(name)
            path = getattr(module, "__file__", None)
            if path and any(Path(path).resolve().is_relative_to(root) for root in roots):
                sys.modules.pop(name, None)


def _load_state(checkpoint, torch):
    path = checked(checkpoint["ref"])
    format_name = checkpoint.get("format")
    if format_name == "safetensors":
        from safetensors.torch import load_file
        state = load_file(str(path), device="cpu")
    elif format_name == "torch_weights_only":
        state = torch.load(path, map_location="cpu", weights_only=True)
    else:
        raise ValueError("Explicit safetensors or torch_weights_only checkpoint format required")
    state = _select(state, checkpoint.get("state_path", []))
    require(isinstance(state, dict) and state and all(isinstance(key, str) for key in state),
            "Checkpoint must resolve to an exact nonempty tensor state_dict")
    strip = checkpoint.get("strip_prefix", "")
    require(isinstance(strip, str), "Explicit checkpoint key prefix required")
    if strip:
        require(all(key.startswith(strip) for key in state), "Checkpoint strip-prefix does not cover every key")
        names = {key[len(strip):]: key for key in state}
        require(len(names) == len(state), "Checkpoint prefix transform creates duplicate keys")
        state = {name: state[old] for name, old in names.items()}
    else:
        names = {key: key for key in state}
    require(all(torch.is_tensor(value) for value in state.values()), "State dictionary contains non-tensor values")
    return state, names



def _adopt_existing(spec, output_path, proof_key, status):
    if output_path is None or not Path(output_path).exists():
        return None
    value = strict_load(output_path)
    require(value.get("schema") == "AIC_FINAL_PARAMETERS_V1" and
            value.get("origin") == "actual_loaded" and
            value.get("component_id") == spec.get("component_id") and
            value.get("loading_proof", {}).get(proof_key) == stable_key(spec),
            "Existing successful inventory has a different exact specification")
    for identity in value["weight_files"]:
        checked(identity)
    for identity in value["loading_proof"].get("code_refs", []):
        checked(identity)
    from .contracts import total_parameters
    total_parameters([ref(output_path)])
    return {"status": status, "inventory_ref": ref(output_path),
            "component_id": value["component_id"], "total_elements": value["total_elements"],
            "adopted_existing_success_no_model_reload": True}

def inventory_factory(spec, *, output_path=None):
    """Load one actual component from a registered constructor/checkpoint.

    Schema example::

      {
        "schema": "AIC_FINAL_INVENTORY_FACTORY_V1",
        "component_id": "sport_umt",
        "factory": {
          "module_ref": {"path": "/exact/code/runtime.py", "bytes": 123, "sha256": "..."},
          "callable": "make_models", "args": ["/exact/engineering/root"],
          "kwargs": {}, "output_selector": [1]
        },
        "code_roots": [{"path": "/exact/engineering/sources/UMT", "files": []}],
        "dependency_refs": [],
        "checkpoint": {"ref": {"path": "/exact/umt_final.pt", "bytes": 123, "sha256": "..."},
                       "format": "torch_weights_only", "state_path": ["model"]},
        "expected_parameters": 1
      }

    The displayed byte/count/SHA values are schema illustrations, not runnable
    asset claims. Bind real files in Linux. No factory is selected by latest,
    wildcard model path or checkpoint fallback. The returned report includes a
    complete callable/code/checkpoint proof as well as the parameter inventory.
    """
    require(spec.get("schema") == "AIC_FINAL_INVENTORY_FACTORY_V1", "Wrong inventory-factory schema")
    require(isinstance(spec.get("component_id"), str) and spec["component_id"], "Component ID required")
    adopted = _adopt_existing(spec, output_path, "factory_spec_sha256", "ACTUAL_CPU_DEPENDENCY_INVENTORY_COMPLETE")
    if adopted is not None:
        return adopted
    roots, code_files, module_path = _validate_roots(spec)
    factory = spec["factory"]
    require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", factory.get("callable", "")),
            "One explicit module-level constructor required")
    require(isinstance(factory.get("args", []), list) and isinstance(factory.get("kwargs", {}), dict),
            "JSON constructor args/kwargs required")
    with _cpu_factory_environment(roots, code_files) as torch:
        module_name = "aic_inventory_" + spec["factory"]["module_ref"]["sha256"][:16]
        module_spec = importlib.util.spec_from_file_location(module_name, module_path)
        require(module_spec is not None and module_spec.loader is not None, "Factory module cannot be loaded")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        try:
            module_spec.loader.exec_module(module)
            constructor = getattr(module, factory["callable"])
            require(callable(constructor), "Registered constructor is not callable")
            built = constructor(*factory.get("args", []), **factory.get("kwargs", {}))
            model = _select(built, factory.get("output_selector", []))
            require(isinstance(model, torch.nn.Module), "Factory selection must be the actual nn.Module")
            require(all(parameter.device.type == "cpu" for parameter in model.parameters()),
                    "Factory created a non-CPU inference dependency")
            state, original_names = _load_state(spec["checkpoint"], torch)
            model.load_state_dict(state, strict=True)
            model.eval().requires_grad_(False)
            # Validate exact values, not merely a non-strict accepted shape list.
            reloaded = model.state_dict()
            require(set(reloaded) == set(state), "Strict load state inventory differs")
            for name, value in reloaded.items():
                source = state[name]
                require(value.shape == source.shape and torch.equal(value.cpu(), source.to(dtype=value.dtype)),
                        "Actual loaded checkpoint tensor differs: " + name)
            weight_ref = spec["checkpoint"]["ref"]
            mapping = {}
            for name, parameter in model.named_parameters(remove_duplicate=False):
                require(name in original_names, "Actual parameter absent from strict checkpoint: " + name)
                mapping[name] = {"weight_ref": weight_ref, "tensor_name": original_names[name]}
            receipt = inspect_loaded_parameters(model, spec["component_id"], [weight_ref], parameter_sources=mapping)
            if spec.get("expected_parameters") is not None:
                require(type(spec["expected_parameters"]) is int and
                        receipt["total_elements"] == spec["expected_parameters"],
                        "Actual inherited parameter count differs from registered expectation")
            receipt["loading_proof"] = {"factory_spec_sha256": stable_key(spec),
                "factory_module": spec["factory"]["module_ref"],
                "callable": factory["callable"], "output_selector": factory.get("output_selector", []),
                "code_refs": [code_files[path] for path in sorted(code_files)],
                "checkpoint": spec["checkpoint"], "strict_state_load": True,
                "all_loaded_state_values_match": True, "counted_named_parameters_not_buffers": True,
                "cpu_only": True, "inference_calls": 0, "training_updates": 0,
                "torch_version": torch.__version__, "completed_at": utc_now()}
        finally:
            sys.modules.pop(module_name, None)
    if output_path is not None:
        identity = atomic_new(output_path, receipt)
        return {"status": "ACTUAL_CPU_DEPENDENCY_INVENTORY_COMPLETE", "inventory_ref": identity,
                "component_id": receipt["component_id"], "total_elements": receipt["total_elements"]}
    return receipt


def inventory_lora_adapter(spec, *, output_path=None):
    """Materialize the exact stored LoRA A/B tensors on CPU, excluding buffers.

    Input schema: AIC_FINAL_LORA_INVENTORY_V1, component_id, checkpoint_ref,
    expected_parameters; optional exact ``parameter_keys``. If keys are not
    given, every checkpoint key must be an A/B weight. Any extra key fails;
    no arbitrary training-state tensor is silently treated as a parameter.
    """
    require(spec.get("schema") == "AIC_FINAL_LORA_INVENTORY_V1", "Wrong LoRA inventory schema")
    adopted = _adopt_existing(spec, output_path, "spec_sha256", "ACTUAL_CPU_ADAPTER_INVENTORY_COMPLETE")
    if adopted is not None:
        return adopted
    require(os.environ.get("CUDA_VISIBLE_DEVICES") in ("", "-1"), "LoRA inventory requires explicit CPU-only process")
    import torch
    from safetensors.torch import load_file
    require(not torch.cuda.is_initialized(), "CPU inventory cannot share an active GPU runtime")
    path = checked(spec["checkpoint_ref"])
    tensors = load_file(str(path), device="cpu")
    actual = set(tensors)
    keys = spec.get("parameter_keys")
    if keys is not None:
        require(isinstance(keys, list) and len(set(keys)) == len(keys) and set(keys) == actual,
                "Exact declared adapter key set differs from checkpoint; no ignored tensors")
    else:
        keys = sorted(actual)
    pattern = re.compile(r".+\.lora_[AB](?:\.[A-Za-z0-9_-]+)?\.weight\Z")
    require(keys and all(pattern.fullmatch(name) for name in keys),
            "Only declared actual LoRA A/B weight tensors are supported by this helper")
    module = torch.nn.ParameterDict()
    sources, key_map = {}, {}
    for index, name in enumerate(keys):
        tensor = tensors[name]
        require(tensor.device.type == "cpu" and tensor.is_floating_point() and tensor.ndim == 2,
                "LoRA A/B must be actual floating CPU matrices")
        internal = f"tensor_{index:05d}"
        module[internal] = torch.nn.Parameter(tensor, requires_grad=False)
        sources[internal] = {"weight_ref": spec["checkpoint_ref"], "tensor_name": name}
        key_map[internal] = name
    receipt = inspect_loaded_parameters(module, spec["component_id"], [spec["checkpoint_ref"]],
                                        parameter_sources=sources)
    if spec.get("expected_parameters") is not None:
        require(type(spec["expected_parameters"]) is int and
                receipt["total_elements"] == spec["expected_parameters"], "Actual LoRA count differs")
    receipt["loading_proof"] = {"spec_sha256": stable_key(spec), "checkpoint": spec["checkpoint_ref"],
        "exact_checkpoint_parameter_key_map": key_map, "all_checkpoint_keys_accounted": True,
        "counted_actual_materialized_parameter_tensors": True, "cpu_only": True,
        "inference_calls": 0, "training_updates": 0, "completed_at": utc_now()}
    if output_path is not None:
        identity = atomic_new(output_path, receipt)
        return {"status": "ACTUAL_CPU_ADAPTER_INVENTORY_COMPLETE", "inventory_ref": identity,
                "component_id": receipt["component_id"], "total_elements": receipt["total_elements"]}
    return receipt


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec = strict_load(args.spec)
    if spec.get("schema") == "AIC_FINAL_LORA_INVENTORY_V1":
        result = inventory_lora_adapter(spec, output_path=args.output)
    else:
        result = inventory_factory(spec, output_path=args.output)
    import json
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
