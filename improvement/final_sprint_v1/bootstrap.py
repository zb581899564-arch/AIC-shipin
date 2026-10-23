"""Derive the final sprint binding from exact existing Linux registrations.

This command reads the existing registrations, never imports their launchers,
never searches for a latest experiment, and does not copy a model or media.
``prepare`` writes four complete CPU inventory specifications. ``inventory``
strictly loads their real parameter tensors and publishes mapping.json only
when all four registered dependencies have measured inventories. Historical
training, prediction and quality gates are never executed or rewritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import time

from .contracts import (atomic_new, checked, iter_refs, protected_baselines, ref,
                        require, stable_key, strict_load, total_parameters, utc_now)

TIME_SHA256 = "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23"
BASE_FROZEN_SHA256 = "74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59"
BASE_PARAMETERS = 8_767_123_696
TIME_PARAMETERS = 15_335_424
SEMANTIC_PARAMETERS = 98_329
AUX_PARAMETERS = 34_252_497
FULL_PARAMETERS = 8_816_809_946
COMPONENTS = ("original_time", "semantic_residual", "i3d", "sport_umt")


def registered_ref(value, label):
    """Keep an original registered SHA; add only a missing measured byte count."""
    require(isinstance(value, dict) and isinstance(value.get("path"), str) and
            Path(value["path"]).is_absolute() and
            isinstance(value.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]),
            label + " must contain its original absolute path and SHA256")
    path = Path(value["path"]).resolve(strict=True)
    identity = {"path": str(path), "sha256": value["sha256"],
                "bytes": value.get("bytes", path.stat().st_size)}
    checked(identity)
    return identity


def _code_root(path, *, package=None):
    root = Path(path).resolve(strict=True)
    require(root.is_dir(), "Existing exact code root is required: " + str(root))
    search = root / package if package else root
    require(search.is_dir(), "Original constructor import package is missing: " + str(search))
    # An inventory inside one exact root is not experiment/model selection.
    # Do not read tensors, caches, media or datasets while binding source code.
    files = sorted(p for p in search.rglob("*") if p.is_file() and
                   p.suffix in {".py", ".so", ".pyd"} and
                   not {".git", "__pycache__"}.intersection(p.relative_to(root).parts))
    require(files, "No original importable source files in " + str(search))
    return {"path": str(root), "files": [ref(p) for p in files]}


def _original_runtime(engineering, umt_registration_ref):
    """Use routing_production60's explicit source lock, not an import search."""
    lock_path = Path(umt_registration_ref["path"]).parent / "source_input_lock.json"
    lock_ref = ref(lock_path)
    lock = strict_load(checked(lock_ref))
    registered = registered_ref(lock["registration"], "UMT source lock registration")
    require(registered == umt_registration_ref, "UMT source lock belongs to another registration")
    dependencies = lock.get("dependencies")
    require(isinstance(dependencies, dict), "Original UMT source lock dependencies are required")
    exact = (Path(engineering) / "runtime.py").resolve(strict=True)
    matches = [identity for identity in dependencies.values()
               if isinstance(identity, dict) and Path(identity.get("path", "")).resolve() == exact]
    require(len(matches) == 1, "Original source lock must bind exactly ENGINEERING/runtime.py")
    runtime_ref = registered_ref(matches[0], "Original I3D/UMT constructor")
    return runtime_ref, lock_ref


def _original_semantic_roots(semantic):
    # production_semantic_apply10 inserts SEM before SEM/code. These are the
    # two explicit original import roots, not a scan through historical runs.
    code = Path(semantic) / "code"
    roots = [_code_root(code)]
    package = Path(semantic) / "score_residual_head_v1"
    if package.is_dir():
        roots.insert(0, _code_root(semantic, package="score_residual_head_v1"))
    else:
        require((code / "score_residual_head_v1").is_dir(),
                "Original SEM/score_residual_head_v1 or SEM/code/score_residual_head_v1 is missing")
    return roots


def _factory_spec(component, module, roots, checkpoint, state_path, args, selector, provenance,
                  expected=None):
    value = {"schema": "AIC_FINAL_INVENTORY_FACTORY_V1", "component_id": component,
             "factory": {"module_ref": module,
                         "callable": "ResidualHead" if component == "semantic_residual" else "make_models",
                         "args": args, "kwargs": {}, "output_selector": selector},
             "code_roots": roots, "dependency_refs": list(provenance["registration_refs"].values()),
             "checkpoint": {"ref": checkpoint, "format": "torch_weights_only", "state_path": state_path},
             "baseline_provenance": provenance}
    if expected is not None:
        value["expected_parameters"] = expected
    return value


def _registered_assets(config_path, package_inputs, semantic_registration, i3d_acceptance,
                       umt_registration, baseline_40_48, baseline_40_47):
    paths = {"config": config_path, "package_inputs": package_inputs,
             "semantic_registration": semantic_registration, "i3d_acceptance": i3d_acceptance,
             "umt_registration": umt_registration}
    registrations = {name: ref(path) for name, path in paths.items()}
    config, sem, i3d, umt = [strict_load(checked(registrations[key])) for key in
                            ("config", "semantic_registration", "i3d_acceptance", "umt_registration")]
    baselines = {"40.48": ref(baseline_40_48), "40.47": ref(baseline_40_47)}
    protected_baselines(baselines)
    require(config.get("b_adapter_sha256") == TIME_SHA256 and
            config.get("expected_base_sha256") == BASE_FROZEN_SHA256,
            "Original exact BASE/TIME identity differs; no trained or substitute adapter is accepted")
    adapter = Path(config["b_adapter"]).resolve(strict=True)
    time_weight = registered_ref({"path": str(adapter / "adapter_model.safetensors"),
                                  "sha256": config["b_adapter_sha256"]}, "Original TIME safetensors")
    require(sem.get("selected_view") == "LM" and sem.get("feature_dimension") == 12289 and
            sem.get("actual_resident_parameters") == BASE_PARAMETERS + TIME_PARAMETERS + SEMANTIC_PARAMETERS,
            "The registered40.47 semantic head dimensions/view/physical count differ")
    semantic_weight = registered_ref(sem["selected_head"], "Original semantic selected_head")
    i3d_weight = registered_ref(i3d, "Original I3D weight acceptance")
    require(i3d_weight["bytes"] == 224733497, "Original accepted I3D checkpoint byte size differs")
    require(umt.get("physical_base_and_TIME_semantic_parameters") ==
            BASE_PARAMETERS + TIME_PARAMETERS + SEMANTIC_PARAMETERS and
            umt.get("actual_aux_expected_parameters") == AUX_PARAMETERS,
            "Original routing production dependency counts differ")
    umt_weight = registered_ref(umt["expert_checkpoint"], "Original routed UMT expert_checkpoint")
    require(registered_ref(umt["protected_baseline"], "UMT protected baseline") == baselines["40.47"],
            "UMT registration is not rooted in the exact protected40.47 archive")
    engineering = Path(registrations["i3d_acceptance"]["path"]).parent
    semantic = Path(registrations["semantic_registration"]["path"]).parent
    runtime_ref, runtime_lock = _original_runtime(engineering, registrations["umt_registration"])
    registrations["umt_source_input_lock"] = runtime_lock
    weights = {"original_time": time_weight, "semantic_residual": semantic_weight,
               "i3d": i3d_weight, "sport_umt": umt_weight}
    provenance = {"schema": "AIC_FINAL_BASELINE_DEPENDENCIES_V1",
                  "registration_refs": registrations, "protected_baselines": baselines,
                  "checkpoint_refs": weights,
                  "registered_fields": {"original_time": "config.b_adapter/adapter_model.safetensors + b_adapter_sha256",
                    "semantic_residual": "semantic_registration.selected_head",
                    "i3d": "i3d_acceptance.path + sha256", "sport_umt": "umt_registration.expert_checkpoint"},
                  "expected_aux_union_parameters": TIME_PARAMETERS + SEMANTIC_PARAMETERS + AUX_PARAMETERS,
                  "expected_complete_parameters_with_actual_raw_base": FULL_PARAMETERS,
                  "counts_are_expectations_until_actual_CPU_inventory": True}
    semantic_roots = _original_semantic_roots(semantic)
    engineering_roots = [_code_root(engineering / path) for path in
                         ("dependencies", "sources/pytorchvideo", "sources/UMT")]
    specs = {"original_time": {"schema": "AIC_FINAL_LORA_INVENTORY_V1", "component_id": "original_time",
                    "checkpoint_ref": time_weight, "expected_parameters": TIME_PARAMETERS,
                    "baseline_provenance": provenance},
        "semantic_residual": _factory_spec("semantic_residual", ref(semantic / "code/monotone_head06.py"),
                    semantic_roots, semantic_weight, [], [sem["feature_dimension"], 8], [], provenance,
                    SEMANTIC_PARAMETERS),
        "i3d": _factory_spec("i3d", runtime_ref, engineering_roots, i3d_weight, ["model_state"],
                    [str(engineering)], [0], provenance),
        "sport_umt": _factory_spec("sport_umt", runtime_ref, engineering_roots, umt_weight, ["model"],
                    [str(engineering)], [1], provenance)}
    model = Path(config["model_dir"]).resolve(strict=True)
    require(model.is_dir() and (model / "config.json").is_file(), "Exact existing BASE model directory is missing")
    revision = config.get("model_revision")
    require(isinstance(revision, str) and revision.strip(), "Original BASE model_revision must be explicit")
    qwen = {"model_dir": str(model), "revision": revision,
            "expected_base_sha256": config["expected_base_sha256"]}
    # Bind original aggregate input identities without splitting/copying clocks.
    package = strict_load(checked(registrations["package_inputs"]))
    for field in ("metadata", "source_clocks"):
        registered_ref(package[field], "package_inputs." + field)
    directories = [semantic, engineering, adapter, model]
    return {"registrations": registrations, "provenance": provenance, "specs": specs,
            "baselines": baselines, "qwen": qwen, "protected_directories": list(map(str, directories)),
            "inferred_workspace": str(semantic.parent)}


def _publish(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(strict_load(path) == value, "Existing bootstrap artifact has a different binding: " + str(path))
        return ref(path)
    return atomic_new(path, value)


def prepare(*, config, package_inputs, semantic_registration, i3d_acceptance, umt_registration,
            baseline_40_48, baseline_40_47, run_root, deadline, scratch_dir,
            workspace_root=None, output_dir=None, planned_output_bytes=1 << 30,
            planned_scratch_bytes=2 << 30, disk_reserve_bytes=128 << 20,
            ram_reserve_bytes=4 << 30, required_gpu_memory_bytes=30 << 30,
            gpu_index=0, shared_gpu_grant=None):
    adopted = _registered_assets(config, package_inputs, semantic_registration, i3d_acceptance,
                                 umt_registration, baseline_40_48, baseline_40_47)
    workspace = Path(workspace_root or adopted["inferred_workspace"]).resolve(strict=True)
    root = Path(run_root).resolve()
    directory = Path(output_dir).resolve() if output_dir else root.with_name(root.name + "_binding")
    scratch = Path(scratch_dir).resolve(strict=True)
    require(workspace.is_dir() and scratch.is_dir(), "Existing workspace/scratch directories are required")
    require(root != workspace and root.is_relative_to(workspace) and
            directory != workspace and directory.is_relative_to(workspace), "New roots must stay inside the explicit workspace")
    require(not root.is_relative_to(directory) and not directory.is_relative_to(root),
            "Bootstrap inputs and production run-root must be disjoint directories")
    protected = [Path(path).resolve() for path in adopted["protected_directories"]]
    for output in (root, directory):
        require(not any(output.is_relative_to(path) or path.is_relative_to(output) for path in protected),
                "A new output may not replace, contain or enter a protected dependency tree")
        for identity in iter_refs(adopted):
            require(not Path(identity["path"]).is_relative_to(output), "New output contains an adopted original asset")
    end = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    require(end.tzinfo is not None and 0 < (end - datetime.now(timezone.utc)).total_seconds() <= 86400,
            "Supply the actual timezone-aware deadline inside the user's remaining24h window")
    resources = {"planned_output_bytes": planned_output_bytes, "planned_scratch_bytes": planned_scratch_bytes,
                 "disk_reserve_bytes": disk_reserve_bytes, "ram_reserve_bytes": ram_reserve_bytes,
                 "planned_ram_bytes": planned_scratch_bytes, "required_gpu_memory_bytes": required_gpu_memory_bytes,
                 "scratch_dir": str(scratch), "cpu_threads": 2, "gpu_index": gpu_index,
                 "finalization_reserve_seconds": 4 * 3600, "total_execution_seconds": 18 * 3600}
    require(all(type(resources[key]) is int and resources[key] > 0 for key in resources
                if key not in {"scratch_dir", "gpu_index"}) and type(gpu_index) is int and gpu_index >= 0,
            "All resource bounds must be positive integers; explicit GPU index must be nonnegative")
    if shared_gpu_grant:
        resources["shared_gpu_grant"] = ref(shared_gpu_grant)
    mapping = {"schema": "AIC_FINAL_SPRINT_MAPPING_V1", "workspace_root": str(workspace),
               "run_root": str(root), "deadline": deadline, "protected_baselines": adopted["baselines"],
               "package_inputs": adopted["registrations"]["package_inputs"], "qwen": adopted["qwen"],
               "color_repairs": adopted["registrations"]["config"], "resources": resources,
               "protected_directories": adopted["protected_directories"],
               "baseline_registration_provenance": adopted["provenance"]}
    owner = {"schema": "AIC_FINAL_BOOTSTRAP_OWNER_V1", "output_dir": str(directory),
             "binding_sha256": stable_key(mapping, adopted["specs"]),
             "implementation_ref": ref(__file__)}
    if directory.exists():
        require(directory.is_dir(), "Bootstrap output is not a directory")
        marker = directory / "owner.json"
        require(marker.exists() or not any(directory.iterdir()), "Existing bootstrap directory is not owned by this binding")
        if marker.exists():
            require(strict_load(marker) == owner, "Existing bootstrap output belongs to another exact registration/code")
    directory.mkdir(parents=True, exist_ok=True)
    _publish(directory / "owner.json", owner)
    spec_refs = {component: _publish(directory / "specs" / (component + ".json"), adopted["specs"][component])
                 for component in COMPONENTS}
    preparation = {"schema": "AIC_FINAL_BOOTSTRAP_PREPARATION_V1", "output_dir": str(directory),
                   "owner": ref(directory / "owner.json"), "specs": spec_refs,
                   "mapping_without_parameter_receipts": mapping,
                   "baseline_provenance": adopted["provenance"],
                   "actual_inventory_required_before_mapping_publication": True,
                   "models_loaded": 0, "media_decodes": 0, "training_updates": 0,
                   "quality_validation_performed": False}
    prepared = _publish(directory / "preparation.json", preparation)
    return {"status": "EXACT_FOUR_DEPENDENCY_SPECS_PREPARED_NO_MODEL_CALLS", "preparation": prepared,
            "next_command": "CUDA_VISIBLE_DEVICES='' python -m improvement.final_sprint_v1.bootstrap inventory --preparation " + str(directory / "preparation.json")}


def _validate_receipt(value, spec, path):
    proof_key = "spec_sha256" if spec["component_id"] == "original_time" else "factory_spec_sha256"
    require(value.get("schema") == "AIC_FINAL_PARAMETERS_V1" and value.get("origin") == "actual_loaded" and
            value.get("component_id") == spec["component_id"] and
            value.get("loading_proof", {}).get(proof_key) == stable_key(spec),
            "Dependency receipt did not load this exact registered factory/checkpoint")
    require(value.get("baseline_provenance") == spec["baseline_provenance"],
            "Dependency receipt is not bound to its original baseline registrations")
    expected = spec["baseline_provenance"]["checkpoint_refs"][spec["component_id"]]
    require(value.get("weight_files") == [expected], "Dependency receipt contains an unexpected checkpoint")
    for identity in iter_refs(value):
        checked(identity)
    total_parameters([ref(path)])


def inventory(preparation_path):
    from .inventory import inventory_factory, inventory_lora_adapter
    prepared_ref = ref(preparation_path)
    preparation = strict_load(checked(prepared_ref))
    require(preparation.get("schema") == "AIC_FINAL_BOOTSTRAP_PREPARATION_V1", "Wrong bootstrap preparation schema")
    directory = Path(preparation["output_dir"]).resolve(strict=True)
    owner = strict_load(checked(preparation["owner"]))
    require(owner["output_dir"] == str(directory) and owner["implementation_ref"] == ref(__file__),
            "Bootstrap preparation belongs to another directory or implementation")
    require(set(preparation["specs"]) == set(COMPONENTS), "Exactly four baseline dependency specs are required")
    specs = {component: strict_load(checked(preparation["specs"][component])) for component in COMPONENTS}
    require(owner["binding_sha256"] == stable_key(preparation["mapping_without_parameter_receipts"], specs),
            "Bootstrap mapping/specifications changed after ownership registration")
    for identity in iter_refs(preparation["baseline_provenance"]):
        checked(identity)
    receipts_dir = directory / "inventories"
    receipts_dir.mkdir(exist_ok=True)
    # Lock only this new CPU inventory namespace; never signals any process.
    with (directory / "inventory.lock").open("a+b") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another CPU bootstrap inventory owns this exact output") from error
        identities, counts = [], {}
        for component in COMPONENTS:
            spec = specs[component]
            require(spec["component_id"] == component and
                    spec["baseline_provenance"] == preparation["baseline_provenance"],
                    "Component registration provenance differs")
            output = receipts_dir / (component + ".json")
            if not output.exists():
                require(os.environ.get("CUDA_VISIBLE_DEVICES") in ("", "-1"),
                        "Use CUDA_VISIBLE_DEVICES='' for CPU dependency inventory")
                started = time.monotonic()
                function = inventory_lora_adapter if component == "original_time" else inventory_factory
                value = function(spec)
                value["baseline_provenance"] = spec["baseline_provenance"]
                value["bootstrap_preparation_ref"] = prepared_ref
                value["cpu_inventory_wall_seconds"] = time.monotonic() - started
                atomic_new(output, value)
            value = strict_load(output)
            _validate_receipt(value, spec, output)
            require(value.get("bootstrap_preparation_ref") == prepared_ref, "Inventory used a different preparation")
            identities.append(ref(output))
            counts[component] = value["total_elements"]
        require(counts["original_time"] == TIME_PARAMETERS and counts["semantic_residual"] == SEMANTIC_PARAMETERS and
                counts["i3d"] + counts["sport_umt"] == AUX_PARAMETERS,
                "Actual CPU dependency counts differ from the original complete40.48 pipeline")
        total = total_parameters(identities)
        require(total["total_elements"] == TIME_PARAMETERS + SEMANTIC_PARAMETERS + AUX_PARAMETERS,
                "Actual auxiliary union differs; missing, duplicate or unexpected tensors")
        completion = {"schema": "AIC_FINAL_BOOTSTRAP_INVENTORY_COMPLETION_V1",
                      "status": "ALL_FOUR_ACTUAL_CPU_DEPENDENCIES_COMPLETE_BASE_GPU_INVENTORY_PENDING",
                      "preparation_ref": prepared_ref, "baseline_provenance": preparation["baseline_provenance"],
                      "parameter_receipts": identities, "actual_dependency_parameters": total["total_elements"],
                      "component_counts": counts, "expected_complete_parameters": FULL_PARAMETERS,
                      "raw_BASE_actual_inventory_still_required": True,
                      "quality_validation_performed": False, "inference_calls": 0, "training_updates": 0}
        complete_ref = _publish(directory / "inventory_completion.json", completion)
        mapping = dict(preparation["mapping_without_parameter_receipts"], baseline_parameter_receipts=identities,
                       baseline_inventory_completion=complete_ref)
        mapping_ref = _publish(directory / "mapping.json", mapping)
        return {"status": completion["status"], "mapping": mapping_ref,
                "inventory_completion": complete_ref, "actual_dependency_parameters": total["total_elements"],
                "raw_BASE_inventory_and_real_smoke_pending": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare", help="Derive exact specs from existing registrations; no model/media calls")
    for name in ("config", "package-inputs", "semantic-registration", "i3d-acceptance", "umt-registration",
                 "baseline-40-48", "baseline-40-47", "run-root", "deadline", "scratch-dir"):
        prepare_parser.add_argument("--" + name, required=True)
    for name in ("workspace-root", "output-dir", "shared-gpu-grant"):
        prepare_parser.add_argument("--" + name)
    for name, default in (("planned-output-bytes", 1 << 30), ("planned-scratch-bytes", 2 << 30),
                          ("disk-reserve-bytes", 128 << 20), ("ram-reserve-bytes", 4 << 30),
                          ("required-gpu-memory-bytes", 30 << 30), ("gpu-index", 0)):
        prepare_parser.add_argument("--" + name, type=int, default=default)
    prepare_parser.add_argument("--inventory", action="store_true", help="Then load four real dependencies on CPU and write mapping.json")
    inventory_parser = sub.add_parser("inventory", help="Resume exact CPU inventories and publish ready mapping.json")
    inventory_parser.add_argument("--preparation", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    if command == "prepare":
        perform_inventory = args.pop("inventory")
        result = prepare(**args)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)
        if perform_inventory:
            result = inventory(result["preparation"]["path"])
            print(json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)
    else:
        result = inventory(args["preparation"])
        print(json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
