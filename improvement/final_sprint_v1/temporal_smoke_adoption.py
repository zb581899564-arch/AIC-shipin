"""Adopt actual temporal smoke plus the separately validated frozen spatial field.

No model is loaded and no old parameter receipt is copied into the new root.
Old temporal/load timings remain conservative evidence, never new GPU charges.
"""
from __future__ import annotations

from fractions import Fraction
import math
from pathlib import Path
import time

from . import assets as asset_api
from .contracts import atomic_new, checked, ref, require, stable_key, strict_load, total_parameters, utc_now
from .frozen_field import load_cache

POLICY = "FROZEN_EXISTING_SOURCE_FIELD"
AUXILIARIES = {"original_time", "semantic_residual", "i3d", "sport_umt"}
EXPECTED_PARAMETERS = {"phase": 8_816_809_946, "specialist": 8_980_108_294}


def _natural_smoke_wrapper(directory, old_ref, old, family):
    path = Path(directory)
    require(path.is_absolute(), "Explicit absolute original smoke wrapper directory required")
    wrapper_ref, claim_ref = ref(path / "completion.json"), ref(path / "claim.json")
    wrapper, claim = strict_load(checked(wrapper_ref)), strict_load(checked(claim_ref))
    require(wrapper.get("schema") == "AIC_FINAL_OWNED_WRAPPER_V1" and wrapper.get("asset_lock") == old_ref
            and wrapper.get("work_terminated") is True and wrapper.get("no_external_task_signaled") is True
            and wrapper.get("termination_basis") == "owned_wrapper_terminal"
            and wrapper.get("stopped_owned_process") is False and wrapper.get("stop_reason") is None
            and type(wrapper.get("child_exit_code")) is int and wrapper["child_exit_code"] == 0
            and claim.get("wrapper_id") == wrapper.get("owned_wrapper_id") and claim.get("asset_lock") == old_ref,
            "Original temporal smoke must have exact naturally successful owned wrapper")
    args = claim["command"]
    require(isinstance(args, list) and args[1:4] == ["-m", "improvement.final_sprint_v1.cli", "smoke"],
            "Original owned command is not the registered smoke")
    def option(name):
        require(args.count(name) == 1 and args.index(name) + 1 < len(args), "Invalid original smoke command option")
        return args[args.index(name) + 1]
    require(Path(option("--assets")).resolve() == checked(old_ref)
            and option("--expected-commit") == old["source_commit"]["commit"]
            and option("--candidate") == ("r_phase_event" if family == "phase" else "m_specialist"),
            "Original smoke command model/recipe/source differs")
    return wrapper_ref, claim_ref


def _temporal_evidence(assets, family, old_ref, wrapper_ref, old_smoke):
    if family == "phase":
        from .phase_call_adoption import validate_manifest
        identity = assets["phase_call_adoption"]
        required = ("phase_",)
    else:
        from .pure_call_adoption import validate_manifest
        identity = assets["pure_call_adoption"]
        required = ("query_", "clip_features_", "specialist_source_")
    entries = validate_manifest(assets, identity)
    manifest = strict_load(checked(identity))
    require(any(parent["old_assets"] == old_ref and parent["wrapper"] == wrapper_ref for parent in manifest["parents"]),
            "Original smoke wrapper is outside explicit audited adoption parents")
    references = []
    for prefix in required:
        matches = [entry for task, entry in entries.items() if task.startswith(prefix)
                   and entry["returned"] in old_smoke["evidence_refs"]
                   and entry["call_binding"].get("source", {}).get("sha256") == old_smoke["source_sha256"]]
        require(matches, "Original temporal smoke is missing audited " + prefix + " evidence")
        references.extend(entry["returned"] for entry in matches)
    return identity, references


def _field_evidence(assets):
    identity = assets["frozen_spatial_field"]
    receipt = strict_load(checked(identity))
    require(receipt.get("status") == "CPU_FIELD_RENDERED_DOMAIN_LOCKED", "Frozen field CPU acceptance incomplete")
    cache = load_cache(receipt, assets)
    metadata = cache["metadata"]
    sources = {source["video_id"]: source for source in assets["sources"]}
    require(len(sources) == len(assets["sources"]) == 426 and set(sources) == {str(index) for index in range(426)}
            and set(cache["support"]) == set(metadata["sources"]) == set(sources)
            and metadata["new_model_calls"] == metadata["new_media_decodes"] == 0
            and metadata["native_frames"] == sum(source["n_frames"] for source in sources.values())
            and metadata["unsupported_policy"] == "UNKNOWN_NO_BOX_NO_ACTION", "Frozen field full426 CPU/source contract differs")
    for sid, source in sources.items():
        proof = metadata["sources"][sid]
        require(proof["source_sha256"] == source["media"]["sha256"] and proof["native_frames"] == source["n_frames"]
                and proof["supported_frames"] == len(cache["support"][sid]) > 0
                and proof["all_supported_native_pts_equal"] is True, "Frozen field native CPU proof differs: " + sid)
    require(set(metadata["baseline_overlap"]) == {"40.48", "40.47"}
            and all(proof["all_frames_supported"] is True and proof["all_boxes_exact"] is True
                    for proof in metadata["baseline_overlap"].values()), "Frozen field does not preserve original baselines")
    references = [identity] + [cache[key] for key in ("spec_ref", "cache_ref", "metadata_ref")]
    references += [cache[key] for key in ("field_frames_ref", "provenance_ref") if key in cache]
    return references, metadata


def smoke(assets, assets_path, candidate_id):
    started = time.monotonic()
    registry = asset_api.candidate_registry()["candidates"]
    require(candidate_id in registry and registry[candidate_id]["implementation_status"] == "IMPLEMENTED"
            and registry[candidate_id].get("spatial_policy",
                registry[candidate_id]["configuration"].get("spatial_policy")) == POLICY,
            "Registered uniform frozen-field temporal candidate required")
    require(candidate_id.startswith(("r_", "m_")), "Only registered R/M temporal families may adopt smoke")
    family = "phase" if candidate_id.startswith("r_") else "specialist"
    config = assets["temporal_smoke_adoption"]
    old = strict_load(checked(config["old_assets"]))
    prior = strict_load(checked(config["smoke_receipt"]))
    require(prior.get("status") == "REAL_ENGINEERING_SMOKE_PASS"
            and prior.get("binding") == dict(asset_lock=config["old_assets"], code=old["source_commit"], family=family)
            and old["sources"] == assets["sources"] and old["protected_baselines"] == assets["protected_baselines"],
            "Original actual smoke/input binding differs")
    for identity in prior["evidence_refs"]:
        checked(identity)
    source = [source for source in assets["sources"] if source["media"]["sha256"] == prior["source_sha256"]]
    require(len(source) == 1 and prior["source_native_frames"] == source[0]["n_frames"]
            and Fraction(prior["source_duration_exact"]) > 0, "Original smoke native source differs")
    for key in ("phase_seconds", "specialist_seconds", "model_initialization_seconds"):
        require(type(prior.get(key)) in (int, float) and math.isfinite(prior[key]) and prior[key] >= 0,
                "Original actual temporal/load cost missing: " + key)
    require(prior["phase_seconds" if family == "phase" else "specialist_seconds"] > 0,
            "Original temporal smoke has no measured work")
    wrapper_ref, claim_ref = _natural_smoke_wrapper(config["wrapper"], config["old_assets"], old, family)
    adoption_ref, temporal_refs = _temporal_evidence(assets, family, config["old_assets"], wrapper_ref, prior)
    field_refs, field_metadata = _field_evidence(assets)
    auxiliaries = asset_api.validate_baseline_auxiliaries(assets)
    require(set(auxiliaries["components"]) == AUXILIARIES, "All four actual baseline auxiliaries required")
    original_models = total_parameters(prior["parameter_receipts"])
    primary_names = {"qwen_base"} | ({"clip_vit_b32", "cg_detr"} if family == "specialist" else set())
    require(set(original_models["components"]) == primary_names, "Original smoke main-model inventory differs")
    parameters = prior["parameter_receipts"] + assets["baseline_parameter_receipts"]
    actual = total_parameters(parameters)
    require(actual["total_elements"] == EXPECTED_PARAMETERS[family]
            and set(actual["components"]) == primary_names | AUXILIARIES, "Full temporal+field main/auxiliary inventory differs")
    expected = dict(asset_lock=ref(assets_path), code=assets["source_commit"], family=family)
    output = Path(assets["run_root"]) / "smoke" / family / "completion.json"
    if output.exists():
        result = strict_load(output)
        require(result["binding"] == expected and result["status"] == "REAL_ENGINEERING_SMOKE_PASS"
                and result["adopted_actual_temporal_smoke"] == config["smoke_receipt"]
                and result["frozen_spatial_field_CPU_receipt"] == assets["frozen_spatial_field"]
                and result["new_gpu_model_calls"] == 0, "Existing adopted smoke has different evidence")
        return result
    result = dict(prior)
    for key in ("spatial_seconds", "spatial_frames", "spatial_ground_calls", "ground_model_seconds",
                "adopted_ground_calls", "adopted_historical_gpu_seconds_not_new_charges"):
        result[key] = 0
    references = [config["smoke_receipt"], wrapper_ref, claim_ref, adoption_ref, *temporal_refs, *field_refs]
    result.update(binding=expected, candidate_id=candidate_id, parameter_receipts=parameters,
        evidence_refs=list({stable_key(identity): identity for identity in references}.values()),
        smoke_origin="ADOPTED_ACTUAL_TEMPORAL_SMOKE_AND_NEW_FULL426_FROZEN_FIELD_CPU_ACCEPTANCE",
        adopted_actual_temporal_smoke=config["smoke_receipt"], original_first_QA_evidence_refs=temporal_refs,
        frozen_spatial_field_CPU_receipt=assets["frozen_spatial_field"], spatial_policy=POLICY,
        cpu_field_validated_sources=426, cpu_field_validated_frames=field_metadata["field_frames"],
        new_gpu_model_calls=0, new_model_inference_calls=0, new_independent_reference_forwards=0,
        actual_parameters=actual["total_elements"], new_parameter_files_copied=0,
        accounting=dict(cost_basis="CPU_METADATA_ADOPTION_ONLY; old temporal/load estimates retained, not new charges",
            physical_model_calls=0, new_gpu_calls=0, cpu_wall_seconds=time.monotonic() - started,
            original_smoke_accounting=prior.get("accounting")), completed_at=utc_now())
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_new(output, result)
    return result
