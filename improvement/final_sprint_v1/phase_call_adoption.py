"""Explicit FP32 phase evidence adoption, isolated from BF16/image journals.

Only original083d successful phase packets are reused. A stopped production
wrapper additionally needs its exact owned route-amendment intervention.
This module reads metadata and original proofs; it never reruns inference/QA.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path
import re
import shlex

from .contracts import atomic_new, checked, ref, require, stable_key, strict_load, strict_loads, total_parameters
from .prepare_pure_adoption import HERE, _dump, _identity, _node, source_files
from .pure_call_adoption import PureCallJournal, validate_row

SCHEMA = "AIC_FINAL_FP32_PHASE_ADOPTION_V1"
PARENT_COMMIT = "083d437e2ea3f0b12e83e0d11f982252b7bdc83d"
PROFILE = "LOSSLESS_BF16_WEIGHTS_FP32_ARITHMETIC_V1"
BASE_SHA = "74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59"
BASE_PARAMETERS = 8767123696
AMENDMENT_STATE = "OWNED_R_PRODUCTION_SUPERVISE_STOP_REQUESTED_FOR_REGISTERED_TEMPORAL_ISOLATION"
PHASE_METHODS = ("phase_clip", "_encode_clip", "_suffixes", "_reference_words", "_arithmetic_context")


def _source_audit(old, directory, new_sources, candidate):
    before = source_files(directory, old["source_commit"]["code"]["files"])
    trees = [ast.parse(checked(files["qwen_runtime.py"]).read_text(encoding="utf-8")) for files in (before, new_sources)]
    require(_dump(trees[0]) == _dump(trees[1]), "FP32 phase runtime/helper AST changed")
    fingerprints = {name: stable_key(_dump(_node(trees[0], "QwenRuntime." + name))) for name in PHASE_METHODS}
    for name in ("numeric_precision.py", "observation.py", "temporal.py"):
        require(before[name]["sha256"] == new_sources[name]["sha256"], "FP32 phase dependency changed: " + name)
        checked(new_sources[name])
    for dotted in ("Engine.phases", "phase_options"):
        nodes = [_node(ast.parse(checked(files["runner.py"]).read_text(encoding="utf-8")), dotted)
                 for files in (before, new_sources)]
        require(_dump(nodes[0]) == _dump(nodes[1]), "FP32 native phase caller changed: " + dotted)
    old_candidate = strict_load(checked(before["candidates.json"]))["candidates"]["r_phase_event"]
    new_candidate = strict_load(checked(new_sources["candidates.json"]))["candidates"][candidate]
    new_configuration = dict(new_candidate["configuration"])
    spatial_policy = new_configuration.pop("spatial_policy", None)
    require(spatial_policy in (None, "FROZEN_EXISTING_SOURCE_FIELD")
            and old_candidate["configuration"] == new_configuration
            and old_candidate["configuration"]["arithmetic_profile"] == PROFILE
            and new_candidate["selection"] == old_candidate["selection"] == "phase_event",
            "New temporal/arithmetic options differ from original FP32 event recipe")
    return dict(old_sources=before, runtime_AST_sha256=stable_key(_dump(trees[0])),
                phase_method_fingerprints=fingerprints, phase_configuration=old_candidate["configuration"])


def _parameter_proof(identity, assets):
    path = checked(identity)
    require(path == Path(assets["run_root"]).resolve() / "model_parameters/qwen_base.json", "Wrong parent parameter receipt path")
    receipt = strict_load(path)
    require(receipt.get("component_id") == "qwen_base" and receipt.get("total_elements") == BASE_PARAMETERS
            and total_parameters([identity])["total_elements"] == BASE_PARAMETERS,
            "Actual parent BASE parameter inventory differs")
    proof = receipt["loading_proof"]
    original, conversion = proof["original_base_identity"], proof["arithmetic_conversion"]
    require(all(proof.get(key) is True for key in ("local_only", "strict_BASE_loading_info_checked", "all_runtime_parameter_keys_bound"))
            and proof.get("optional_TIME_loaded") is False and proof["revision"] == assets["qwen"]["revision"]
            and original.get("verified_before_adapter") is True
            and original.get("sha256") == original.get("expected_sha256") == BASE_SHA
            and original.get("parameters") == BASE_PARAMETERS,
            "Original canonical BASE/loading proof differs")
    require(conversion.get("schema") == "AIC_LOSSLESS_FP32_ARITHMETIC_PROOF_V1"
            and conversion.get("arithmetic_profile") == PROFILE
            and conversion.get("source_parameter_dtype") == "torch.bfloat16"
            and conversion.get("materialized_parameter_dtype") == "torch.float32"
            and conversion.get("roundtrip_BASE_identity", {}).get("sha256") == BASE_SHA
            and conversion["roundtrip_BASE_identity"]["parameters"] == BASE_PARAMETERS
            and conversion.get("training_updates") == 0
            and all(conversion.get(key) is True for key in
                    ("exact_original_values_preserved", "all_tensors_frozen", "original_BF16_identity_verified_before_conversion",
                     "tensor_objects_aliases_shapes_counts_unchanged", "inference_autocast_disabled"))
            and conversion.get("backend") == dict(cuda_autocast_enabled=False, cuda_matmul_allow_tf32=False,
                                                  cudnn_allow_tf32=False, float32_matmul_precision="highest"),
            "Actual lossless FP32 arithmetic/roundtrip proof differs")


def _argv(value, module, assets, action, expected_commit=None):
    args = shlex.split(value) if isinstance(value, str) else value
    require(isinstance(args, list) and all(isinstance(item, str) for item in args), "Exact original command argv required")
    require(args[1:3] == ["-m", module], "Unexpected owned wrapper command module")
    def option(name):
        require(args.count(name) == 1 and args.index(name) + 1 < len(args), "Missing/duplicate original command option")
        return args[args.index(name) + 1]
    require(Path(option("--assets")).resolve() == checked(assets)
            and option("--candidate") == "r_phase_event", "Owned command uses another asset/candidate")
    require((args[3] == action if module.endswith(".cli") else option("--action") == action), "Owned command action differs")
    if expected_commit is not None:
        require(option("--expected-commit") == expected_commit, "Owned command source commit differs")


def _parent(parent):
    assets, wrapper = [strict_load(checked(parent[key])) for key in ("old_assets", "wrapper")]
    require(assets["source_commit"]["commit"] == PARENT_COMMIT and not assets["qwen"].get("adapter_dir")
            and assets["qwen"].get("arithmetic_profile", PROFILE) == PROFILE, "Only original083d FP32 BASE assets permitted")
    require(wrapper.get("schema") == "AIC_FINAL_OWNED_WRAPPER_V1" and wrapper.get("asset_lock") == parent["old_assets"]
            and wrapper.get("work_terminated") is True and wrapper.get("no_external_task_signaled") is True
            and wrapper.get("termination_basis") == "owned_wrapper_terminal", "Exact owned terminal required")
    claim_ref = ref(Path(parent["wrapper"]["path"]).parent / "claim.json")
    owner = strict_load(checked(claim_ref))
    require(owner["wrapper_id"] == wrapper["owned_wrapper_id"] and owner["asset_lock"] == parent["old_assets"], "Wrapper claim ownership differs")
    action = "run" if wrapper.get("stopped_owned_process") else "smoke"
    _argv(owner["command"], "improvement.final_sprint_v1.cli", parent["old_assets"], action, PARENT_COMMIT)
    if action == "smoke":
        require(wrapper.get("stopped_owned_process") is False and wrapper.get("stop_reason") is None
                and wrapper.get("child_exit_code") == 0, "Original FP32 smoke must complete naturally")
    else:
        amendment = strict_load(checked(parent["route_amendment"]))
        require(wrapper.get("stopped_owned_process") is True and wrapper.get("stop_reason") == "OwnedWrapperStop"
                and wrapper.get("child_exit_code") == -15 and amendment.get("state") == AMENDMENT_STATE
                and Path(amendment["wrapper"]).resolve() == Path(parent["wrapper"]["path"]).parent.resolve()
                and amendment.get("wrapper_id") == wrapper["owned_wrapper_id"]
                and amendment.get("owned_child") == owner["child_pid"] and amendment.get("no_external_signal") is True
                and amendment.get("do_not_repeat_successful_calls") is True, "Unproved route-amendment owned stop")
        _argv(amendment["supervisor_argv"], "improvement.final_sprint_v1.supervise", parent["old_assets"], "run", PARENT_COMMIT)
    _parameter_proof(parent["parameter_receipt"], assets)
    smoke = strict_load(checked(parent["smoke_receipt"]))
    require(smoke.get("status") == "REAL_ENGINEERING_SMOKE_PASS"
            and smoke.get("binding") == dict(asset_lock=parent["old_assets"], code=assets["source_commit"], family="phase")
            and parent["parameter_receipt"] in smoke.get("parameter_receipts", [])
            and smoke.get("phase_reference_forwards", 0) > 0 and smoke.get("phase_clips", 0) > 0,
            "Original complete independent FP32 smoke evidence required")
    return assets, wrapper, owner, smoke, action


def _phase_packet(row, assets, configuration, smoke):
    from .observation import plan_clips
    entry = validate_row(row)
    call = entry["call_binding"]
    require(set(call) == {"source", "clock", "clip", "model", "algorithm"}
            and call["algorithm"] == "NATIVE_ACTION_PHASE_SEMANTIC_WORDS_V2"
            and call["model"] == assets["qwen"]["asset_tree"], "Phase request model/algorithm differs")
    sources = [source for source in assets["sources"] if source["media"] == call["source"] and source["clock"] == call["clock"]]
    require(len(sources) == 1, "Exact phase native source/clock missing")
    source = sources[0]
    clock = strict_load(checked(source["clock"]))
    clock = clock[source["clock"]["source_key"]] if "source_key" in source["clock"] else clock
    plans = plan_clips(dict(source, normalized_exact_pts=clock["normalized_exact_pts"], physical_end_exact=clock["physical_end_exact"]),
                       clip_seconds=configuration["clip_seconds"], samples_per_clip=configuration["samples_per_clip"])
    require(call["clip"] in plans and row["task_id"] == "phase_" + source["video_id"] + "_" + call["clip"]["clip_id"], "Native phase clip differs")
    result = strict_load(checked(row["returned"]))["result"]
    phases, proof = result["phases"], result["input_proof"]
    require(result["clip"] == call["clip"] and result["role"] == "base" and result["parameter_count"] == BASE_PARAMETERS
            and result["status"] in ("LEGAL_EMPTY", "MODEL_OK")
            and type(result.get("gpu_seconds")) in (int, float) and math.isfinite(result["gpu_seconds"]) and result["gpu_seconds"] >= 0
            and result["score_definition"] == "MEAN_COMPLETE_SEMANTIC_WORD_AND_LF_FULL_VOCAB_LOGPROB"
            and result["no_global_source_prefix"] is True and result["training_updates"] == 0
            and len(phases) == len(call["clip"]["cells"]) and phases
            and all(part["cell"] == cell and part["phase"] in ("ordinary", "setup", "apex", "resolution")
                    for part, cell in zip(phases, call["clip"]["cells"]))
            and result["raw_text"] == "\n".join(part["phase"] for part in phases) + "\n"
            and proof["physical_source_sha256"] == source["media"]["sha256"]
            and proof["local_input"]["native_ordinals"] == call["clip"]["sample_ordinals"]
            and proof["local_input"]["sample_pts_exact"] == call["clip"]["sample_pts_exact"]
            and proof["local_input"]["source_id"] == source["video_id"]
            and proof["local_input"]["source_sha256"] == source["media"]["sha256"]
            and proof["local_input"]["pixel_sha256"] == proof["pixel_sha256"]
            and all(re.fullmatch(r"[0-9a-f]{64}", value) for value in proof["pixel_sha256"])
            and len(proof["pixel_sha256"]) == len(call["clip"]["sample_ordinals"])
            and re.fullmatch(r"[0-9a-f]{64}", proof["input_identity"]["sha256"]), "Complete native/token phase proof differs")
    for part in phases:
        alternatives = part["alternatives"]
        require([value["phase"] for value in alternatives] == ["ordinary", "setup", "apex", "resolution"], "Complete semantic alternatives required")
        for value in alternatives:
            tokens, scores = value["token_ids"], value["token_log_probabilities"]
            require(0 < len(tokens) <= 8 and len(tokens) == len(scores)
                    and all(type(token) is int and token >= 0 for token in tokens)
                    and all(type(score) in (int, float) and math.isfinite(score) for score in scores),
                    "Original complete word/LF token proof missing")
    if smoke:
        checks = result["independent_unpadded_reference_checks"]
        require(checks and result["independent_reference_forwards"] == 4 * len(checks)
                and all(check["status"] == "PASS_CACHED_VS_UNPADDED_REFERENCE"
                        and check["token_absolute_tolerance"] == .20 and check["mean_score_absolute_tolerance"] == .08
                        and check["no_reference_substitution"] is True for check in checks),
                "Old smoke phase lacks its original independent QA")
    entry["validated_arithmetic_profile"] = PROFILE
    return entry


def _collect(parent, index, configuration):
    assets, wrapper, owner, smoke, action = _parent(parent)
    rows, excluded = [], []
    for item in wrapper["task_terminals"]:
        task = item["task_id"]
        if not task.startswith("phase_"):
            excluded.append(dict(parent=index, task_id=task, reason="NOT_PHASE"))
            continue
        proof = strict_load(checked(item["terminal_ref"]))
        claim_ref = proof["claim_ref"]
        claim = strict_load(checked(claim_ref))
        binding = claim["binding"]
        require(proof.get("task_id") == claim.get("task_id") == task
                and proof.get("claim_sha256") == claim_ref["sha256"]
                and proof.get("owned_wrapper_id") == claim.get("owned_wrapper_id") == wrapper["owned_wrapper_id"]
                and claim["pid"] == owner["child_pid"] and proof.get("work_terminated") is True
                and proof.get("no_external_task_signaled") is True and proof.get("termination_basis") == "owned_wrapper_terminal"
                and binding == dict(base=dict(asset_lock=parent["old_assets"], code=assets["source_commit"], no_training=True, seed=20261023),
                                    call=binding["call"], journal_schema="AIC_FINAL_CALL_V1"), "FP32 phase claim/owned binding differs")
        directory = Path(claim_ref["path"]).parent
        if not all((directory / name).is_file() for name in ("success.json", "returned_result.json")):
            excluded.append(dict(parent=index, task_id=task, reason="NO_DURABLE_SUCCESS"))
            continue
        row = dict(parent=index, task_id=task, terminal=item["terminal_ref"], claim=claim_ref,
                   success=ref(directory / "success.json"), returned=ref(directory / "returned_result.json"))
        _phase_packet(row, assets, configuration, action == "smoke")
        if action == "smoke":
            require(row["returned"] in smoke["evidence_refs"], "Smoke phase packet absent from original PASS evidence")
        rows.append(row)
    return rows, excluded, action


def prepare_manifest(specifications, expected_commit, new_candidate, source_dir=HERE):
    require(re.fullmatch(r"[0-9a-f]{40}", expected_commit) and specifications, "Exact new commit/ordered parents required")
    new_sources, parents, rows, excluded, smoke_seen = source_files(source_dir), [], [], [], False
    for index, spec in enumerate(specifications):
        parent = {key: _identity(spec[key]) for key in ("old_assets", "wrapper", "parameter_receipt", "smoke_receipt")}
        parent["source_dir"] = str(Path(spec["source_dir"]).resolve(strict=True))
        if spec.get("route_amendment"):
            parent["route_amendment"] = _identity(spec["route_amendment"])
        old = strict_load(checked(parent["old_assets"]))
        parent["source_audit"] = _source_audit(old, parent["source_dir"], new_sources, new_candidate)
        found, omitted, action = _collect(parent, index, parent["source_audit"]["phase_configuration"])
        smoke_seen |= action == "smoke" and bool(found)
        parents.append(parent)
        rows.extend(found)
        excluded.extend(omitted)
    require(smoke_seen and rows and all(parent["old_assets"] == parents[0]["old_assets"] for parent in parents),
            "One exact naturally passed FP32 smoke and same original assets required")
    return dict(schema=SCHEMA, new_implementation=expected_commit, new_candidate=new_candidate,
                new_sources=new_sources, parents=parents, rows=rows, excluded=excluded,
                new_inference_calls=0, independent_QA_adopted_not_repeated=True)


def validate_manifest(assets, identity):
    manifest = strict_load(checked(identity))
    require(manifest.get("schema") == SCHEMA and manifest["new_implementation"] == assets["source_commit"]["commit"]
            and {name: value["sha256"] for name, value in manifest["new_sources"].items()} == assets["source_commit"]["code"]["files"],
            "FP32 phase adoption implementation differs")
    regenerated = prepare_manifest(manifest["parents"], manifest["new_implementation"], manifest["new_candidate"],
                                   Path(manifest["new_sources"]["qwen_runtime.py"]["path"]).parent)
    require(regenerated == manifest, "FP32 phase adoption inventory/source proof differs")
    result = {}
    for parent in manifest["parents"]:
        old = strict_load(checked(parent["old_assets"]))
        require(not assets["qwen"].get("adapter_dir") and all(old[key] == assets[key] for key in
                ("qwen", "sources", "protected_baselines", "baseline_parameter_receipts")), "FP32 phase inputs/model changed")
    for row in manifest["rows"]:
        parent = manifest["parents"][row["parent"]]
        entry = _phase_packet(row, strict_load(checked(parent["old_assets"])), parent["source_audit"]["phase_configuration"], False)
        previous = result.setdefault(row["task_id"], entry)
        require(previous["call_binding"] == entry["call_binding"] and previous["semantic_sha256"] == entry["semantic_sha256"],
                "Conflicting duplicate FP32 phase success")
    return result


class PhaseCallJournal(PureCallJournal):
    def __init__(self, delegate, entries):
        require(entries and all(name.startswith("phase_") and item.get("validated_arithmetic_profile") == PROFILE
                               for name, item in entries.items()), "FP32-only validated phase entries required")
        super().__init__(delegate, entries)

    def _entry(self, task_id, call_binding):
        entry = self.entries.get(task_id)
        if entry is not None:
            require(task_id.startswith("phase_") and entry["call_binding"] == call_binding,
                    "Adopted FP32 phase source/native clip/model/algorithm changed")
            checked(entry["returned"])
        return entry


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("expected-commit", "new-candidate", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--parent", action="append", required=True)
    parser.add_argument("--source-dir", default=str(HERE))
    args = parser.parse_args(argv)
    specs = [strict_loads(item) if item.lstrip().startswith("{") else strict_load(item) for item in args.parent]
    value = prepare_manifest(specs, args.expected_commit, args.new_candidate, args.source_dir)
    print(json.dumps(dict(status="FP32_PHASE_EVIDENCE_ADOPTED_NO_NEW_INFERENCE_OR_QA", manifest=atomic_new(args.output, value))))


if __name__ == "__main__":
    main()
