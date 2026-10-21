"""Explicit PLAN62 transfer: final vision63 + frozen original TIME, 43+43.

Imports are CPU/lazy.  There is no training, processor, decoder, production,
package or automatic continuation entry point in this module.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
from types import SimpleNamespace

sys.dont_write_bytecode = True
INPUT_KEYS = {"input_ids", "attention_mask", "pixel_values_videos", "video_grid_thw"}
ROLES = ("real", "shift")
FULL_PARAMETERS = 8_783_303_945
DIAGNOSTIC_PURPOSE = "USER_REQUESTED_TIME43_DIAGNOSTIC_AFTER_PRESERVED_PAIR_STOP"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def reference(path):
    path = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=h.hexdigest())


def checked(ref, workspace):
    path = Path(ref["path"]).resolve(strict=True)
    require(path.is_relative_to(workspace) and reference(path) == ref, "Bound file identity/path differs: " + str(path))
    return path


def readref(ref, workspace):
    return json.loads(checked(ref, workspace).read_text(encoding="utf-8-sig"))


def validate_pilot_scope(reg, review):
    """A separately registered diagnostic never changes the failed pair gate."""
    if review["status"] == "ELIGIBLE_FOR_TIME43":
        require(not review["stop_reasons"], "Eligible pilot cannot have failed conditions")
        return
    require(review["status"] == "STOP" and bool(review["stop_reasons"])
            and reg.get("purpose") == DIAGNOSTIC_PURPOSE
            and reg.get("pilot_pair_gate") == "STOP"
            and reg.get("automatic426") is False,
            "Failed pilot cannot silently pass; only explicit user-requested transfer diagnostic is allowed")


def install_inventory_guard(module, inventory):
    """Validate roles without returning replacement positional arguments to Torch."""
    def before_forward(_module, _args):
        inventory(False)
    return module.register_forward_pre_hook(before_forward)


def save(path, value):
    with Path(path).open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    return reference(path)


def derived_request(original, role, signature):
    """Own the transformed signature without claiming shifted native truth."""
    require(role in ROLES and set(signature) == INPUT_KEYS, "Explicit role/four-tensor signature")
    require(role != "real" or signature == original["input_signature"], "Real input must be byte-identical")
    result = json.loads(json.dumps(original))
    result.update(input_signature=signature, transfer_role=role, labels_read=False,
                  original_input_signature=original["input_signature"],
                  transformation="IDENTITY" if role == "real" else "HALF_TEMPORAL_GROUP_CIRCULAR_SHIFT_PER_VIEW",
                  truthful_native_observation=role == "real")
    return result


def complete_unions(rows, expected_uids, source_ids):
    require(set(rows) == set(ROLES), "Both registered roles are required")
    result, empty = {}, {}
    for role in ROLES:
        seen, unions, empty_windows = set(), {sid: set() for sid in source_ids}, 0
        for row in rows[role]:
            uid, sid = row["uid"], row["source_id"]
            require(uid in expected_uids and uid not in seen and sid in unions and row["role"] == role
                    and row["status"] == "ACCEPTED", "Duplicate/foreign/missing/failed output is not empty")
            chosen = row["selected_ordinals"]
            require(chosen == sorted(set(chosen)) and row["legal_empty"] is (not chosen), "Native membership/empty identity")
            unions[sid].update(chosen); seen.add(uid); empty_windows += int(not chosen)
        require(seen == set(expected_uids), "Every original window must execute successfully")
        result[role], empty[role] = unions, empty_windows
    return result, empty


def transfer_reasons(report, greedy, real):
    macro, effects = report["macro"], report["effects"]["vision_real"]
    reasons = []
    if macro["vision_real"]["f1"] <= macro["greedy"]["f1"]: reasons.append("REAL_NOT_BETTER_THAN_ORIGINAL_TIME")
    if macro["vision_real"]["f1"] <= macro["protected_proxy"]["f1"]: reasons.append("REAL_NOT_BETTER_THAN_PROTECTED40_47_PROXY")
    if macro["vision_real"]["f1"] <= macro["vision_shift"]["f1"]: reasons.append("REAL_NOT_BETTER_THAN_FIXED_CONTENT_SHIFT")
    if effects["source_wins"] < 2: reasons.append("FEWER_THAN_TWO_SOURCES_IMPROVED_VS_ORIGINAL_TIME")
    if any(greedy[sid] and not real[sid] for sid in greedy): reasons.append("NEW_COMPLETE_SOURCE_EMPTY")
    return reasons


def partition_parameters(named, time_parameters, visual_parameters):
    """Do not apply the old language-only LoRA regex to visual matrices."""
    time_ids, visual_ids = {id(p) for p in time_parameters}, {id(p) for p in visual_parameters}
    require(not (time_ids & visual_ids), "TIME and visual adapter ownership overlaps")
    counts, seen = dict(base=0, TIME=0, visual=0), set()
    for name, parameter in named:
        if id(parameter) in seen: continue
        seen.add(id(parameter))
        require(not parameter.requires_grad and parameter.grad is None, "All transfer parameters must be frozen")
        role = "TIME" if id(parameter) in time_ids else "visual" if id(parameter) in visual_ids else "base"
        require(role != "base" or "lora_" not in name, "Unregistered low-rank parameter: " + name)
        require(role == "base" or str(parameter.dtype) == "torch.float32", "Both adapter roles must remain FP32")
        counts[role] += parameter.numel()
    require(time_ids | visual_ids <= seen, "Registered adapter parameter disappeared")
    return counts


def context(root, phase):
    n = Path(root).resolve(strict=True); w = n.parent.parent
    require(n.parent == w / "evidence_reset_goal_20261020_v1"
            and n.name in {"time_transfer66", "time_transfer_remaining67"}, "Explicit independent transfer root")
    admission = json.loads((n / ({"prepare": "prepare_admission66.json", "generate": "gpu_admission66.json",
                                 "review": "review_admission66.json"}[phase])).read_text())
    require(admission.get("approved") is True, "Explicit phase admission required")
    reg = readref(admission["registration_ref"], w)
    require(reg["schema"] == "VISION_TIME_TRANSFER66_V1" and checked(reg["code_ref"], w) == Path(__file__).resolve(), "Exact transfer implementation")
    require(reg["expected_cases"] == 43 and reg["expected_sources"] == 8 and reg["max_generations"] == 86,
            "Fixed43real plus43shift workload")
    require(reg["max_gpu_seconds"] > 0 and reg["planned_output_bytes"] > 0, "Finite concrete budgets")
    for ref in reg["pr3_code_refs"].values(): checked(ref, w)
    code_root = Path(reg["pr3_code_root"]).resolve(strict=True)
    require(code_root.is_relative_to(w), "Bound original code workspace")
    sys.path.insert(0, str(code_root))
    modules = {name: importlib.import_module("improvement." + name) for name in
               ["native_preference_v1.inputs", "native_preference_v1.runtime", "native_preference_v1.run",
                "content_choice_v1.runtime", "content_choice_v1.run", "content_choice_v1.adoption", "content_choice_v1.evaluate"]}
    bound_paths = {str(checked(ref, w)) for ref in reg["pr3_code_refs"].values()}
    require(all(str(Path(module.__file__).resolve()) in bound_paths for module in modules.values()), "Actual imported PR3 modules must be bound")
    manifest = readref(reg["asset_manifest_ref"], w)
    require(Path(manifest["workspace_root"]).resolve() == w, "Original asset workspace")
    complete63, review63 = readref(reg["completion63_ref"], w), readref(reg["review63_ref"], w)
    validate_pilot_scope(reg, review63)
    require(complete63["status"] == "ENGINEERING_COMPLETE_VISUAL_ATTENTION63_NOT_QUALITY_OR_TIME43_ADMISSION"
            and review63["unique_ledger"] == "PASS" and review63["gpu_completion_ref"] == reg["completion63_ref"]
            and complete63["final_adapter_ref"] == review63["final_adapter_ref"] == reg["final_adapter_ref"],
            "Exact pilot engineering/review and separately registered transfer scope must be bound")
    require(complete63["base_before"] == complete63["base_after"] and complete63["TIME_updates"] == 0
            and complete63["language_updates"] == complete63["merger_updates"] == 0, "63 protected roles changed")
    checked(reg["final_adapter_ref"], w)
    restore = readref(reg["restore64_completion_ref"], w)
    require(restore["status"] == "COMPLETE_EXPLICIT_CLEANUP_ERROR_CACHE_RESTORE_ORIGINAL_BYTES"
            and len(restore["restored_original_refs"]) == 287, "Exact input repair must complete before transfer")
    # The repair completion is adopted; only the original files are opened by the
    # input store.  No old decode, processor, model or first-QA stage is invoked.
    visual_path = checked(reg["visual_module_ref"], w)
    spec = importlib.util.spec_from_file_location("vision_attention63_for_transfer66", visual_path)
    visual = importlib.util.module_from_spec(spec); sys.modules[spec.name] = visual; spec.loader.exec_module(visual)
    return n, w, reg, admission, manifest, modules, visual, complete63


class Budget:
    def __init__(self, root, reg):
        self.root, self.reg, self.started, self.forwards = root, reg, time.monotonic(), 0

    def check(self, *, forward=False):
        if forward: self.forwards += 1
        require(time.monotonic() - self.started < self.reg["max_gpu_seconds"], "Finite transfer GPU phase")

    def save(self, path, value):
        blob = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
        total = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
        require(total + len(blob) + 65536 <= self.reg["planned_output_bytes"]
                and shutil.disk_usage(self.root).free >= len(blob) + 65536, "Actual next transfer output cannot fit")
        require(Path(path).parent.resolve().is_relative_to(self.root), "New transfer outputs only")
        with Path(path).open("xb") as stream:
            stream.write(blob); stream.flush(); os.fsync(stream.fileno())
        return reference(path)


def prepare(root):
    n, w, reg, admission, manifest, modules, visual, _ = context(root, "prepare")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CPU-only exact input adoption")
    store = modules["native_preference_v1.inputs"].NativeInputStore(manifest, "check")
    old = readref(reg["original_collection_ref"], w)
    require(old["status"] == "COMPLETE_CANDIDATE_COLLECTION_NOT_ADMITTED" and old["source_count"] == 8
            and old["window_count"] == old["control_windows_adopted"] == 43
            and set(old["window_refs"]) == set(store.case_ids), "Exact successful original43 controls")
    folder = n / "inputs66"; folder.mkdir()
    refs = {role: {} for role in ROLES}
    try:
        for uid in sorted(store.case_ids):
            request, values, _ = store.case(uid)
            prior = readref(old["window_refs"][uid], w)
            require(prior["status"] == "ACCEPTED" and prior["input_signature"] == request["input_signature"]
                    and prior["request_ref"] == store.request_refs[uid], "Original successful input/control identity")
            shifted = modules["content_choice_v1.runtime"].permute_visual(values)
            signatures = {"real": visual.tensor_signature(values), "shift": visual.tensor_signature(shifted)}
            require(signatures["shift"] == prior["counterfactual_input_signature"], "Adopt exact prior half-group shift input")
            for role in ROLES:
                derived = derived_request(request, role, signatures[role])
                derived.update(original_request_ref=store.request_refs[uid], original_window_ref=old["window_refs"][uid])
                refs[role][uid] = save(folder / (uid + "." + role + ".json"), derived)
            del values, shifted
    finally:
        store.close()
    return save(n / "input_acceptance66.json", dict(status="PASS_EXACT43_REAL_AND43_OLD_SHIFT_INPUT_ADOPTION",
         case_refs=refs, logical_inputs=86, native_windows=43, source_ids=sorted(store.source_ids),
         registration_ref=admission["registration_ref"], original_collection_ref=reg["original_collection_ref"],
         source_clock_refs={sid: store.sources[sid]["clock_ref"] for sid in store.source_ids},
         new_decoder_calls=0, new_processor_calls=0, new_model_calls=0, old_model_outputs_repeated=False))


def runtime_class(choice, inherited, visual):
    class VisionTimeRuntime(choice.QwenChoiceRuntime):
        def __init__(self, model_spec, final_ref, workspace, **kwargs):
            super().__init__(model_spec, **kwargs)
            self.final_ref, self.workspace, self.visual_ready = final_ref, workspace, False

        def _inventory(self, training=False):
            if not self.visual_ready:
                return super()._inventory(training)
            require(training is False, "Transfer never trains")
            params = visual.lora_parameters(self.native)
            expected = {f"model.visual.blocks.{i}.attn.{kind}.lora_{side}" for i in range(27)
                        for kind in ("qkv", "proj") for side in ("A", "B")}
            require(set(params) == expected and len(params) == 108, "Exact visual adapter ownership")
            counts = partition_parameters(self.model.named_parameters(), self._policy_parameters, params.values())
            require(counts == dict(base=inherited.BASE_PARAMETERS, TIME=inherited.ADAPTER_PARAMETERS, visual=746496),
                    "Actual BASE/TIME/vision parameter inventory differs")
            require(self.model.active_adapter == inherited.ADAPTER_NAME and len(self._adapter_layers) == 144 and all(
                not layer.disable_adapters and list(layer.active_adapters) == [inherited.ADAPTER_NAME]
                and set(layer.lora_A) == set(layer.lora_B) == {inherited.ADAPTER_NAME} for layer in self._adapter_layers),
                "All original144 TIME modules must remain enabled")
            return dict(**counts, visual_matrices=108, TIME_matrices=288,
                        physical_resident=sum(counts.values()), conservative_full_pipeline=FULL_PARAMETERS,
                        semantic_baseline_dependency_counted=True, head53_used=False, trainable_parameters=0)

        def load(self):
            super().load()  # Exact original BASE load and FP32 TIME restoration, no forward.
            state = self.torch.load(checked(self.final_ref, self.workspace), map_location="cpu", weights_only=True)
            visual.attach_visual_lora(self.native)
            visual.load_lora_state(self.native, state["adapter_state_dict"])
            for parameter in self.model.parameters(): parameter.requires_grad_(False)
            self.model.eval(); self.model.gradient_checkpointing_disable()
            self.visual_signature = visual.tensor_signature(visual.lora_state(self.native))
            require(self.visual_signature == visual.tensor_signature(state["adapter_state_dict"]), "All108 final visual matrices loaded bit exactly")
            self.visual_ready = True
            self.mode = "ORIGINAL_TIME_PLUS_FINAL_VISION63"
            self._inventory(False)
            self._vision_role_hook = install_inventory_guard(self.native.model, self._inventory)
            self._event("visual_adapter_loaded", runtime=self.identity(), inventory=self._inventory(False))
            return self.identity()

        def identity(self):
            result = super().identity()
            if not self.visual_ready:
                result["transfer_stage"] = "ORIGINAL_TIME_LOADED_NO_GENERATION_VISUAL_ATTACHMENT_PENDING"
                return result
            for key in ["sampling", "projection", "feature_state"]: result.pop(key, None)
            result.update(schema="VISION_TIME_TRANSFER66_RUNTIME_V1", active_weights="ORIGINAL_TIME_PLUS_FINAL_VISION63",
                          visual_adapter_ref=self.final_ref, visual_adapter_signature=self.visual_signature,
                          transfer_runtime_ref=reference(__file__), conservative_full_pipeline_parameters=FULL_PARAMETERS,
                          original_TIME_unchanged=True, head53_used=False, feature_scoring_used=False,
                          resident_adapters=2, resident_PEFT_adapters=1, visual_custom_adapters=1,
                          generation=dict(do_sample=False, num_beams=1, max_new_tokens=512, allow_empty=True, max_segments=6),
                          optimizer_updates=0)
            return result

        def generate(self, values, constraint):
            require(self.visual_ready and self.counts["generation_calls"] < 86, "Exactly bounded final visual transfer generation")
            self._inventory(False)
            return super().generate(values, constraint)

        def verify_frozen(self):
            self._assert_frozen_state(); inventory = self._inventory(False)
            base = inherited.canonical_frozen_hash(self.model, self.torch)
            require(base == self.base_before, "Original BF16 BASE/mergers/language changed")
            original, _ = self._original_files()
            from safetensors.torch import load_file
            choice.assert_original_adapter_unchanged(self.torch, self._adapter_state(), load_file(str(original), device="cpu"))
            require(visual.tensor_signature(visual.lora_state(self.native)) == self.visual_signature, "Final108 visual matrices changed during transfer")
            checked(self.final_ref, self.workspace)
            return dict(status="PASS_FROZEN_BASE_TIME288_AND_FINAL_VISUAL108", base=base, inventory=inventory,
                        TIME_unchanged=True, visual_signature=self.visual_signature, counts=dict(self.counts), runtime=self.identity())
    return VisionTimeRuntime


def generate(root):
    n, w, reg, admission, manifest, modules, visual, _ = context(root, "generate")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") not in (None, "", "-1"), "Explicit reserved GPU child")
    accepted = readref(admission["input_acceptance_ref"], w)
    require(admission["input_acceptance_ref"] == reference(n / "input_acceptance66.json")
            and accepted["registration_ref"] == admission["registration_ref"], "Exact adopted86 inputs")
    # The controller owns the unique wrapper/ledger; verify its live reservation
    # explicitly because the adopted PR3 loader itself only checks CUDA/version.
    contract_path = checked(reg["gpu_contract_ref"], w)
    sys.path.insert(0, str(contract_path.parent))
    contract_spec = importlib.util.spec_from_file_location("transfer66_live_gpu_contract", contract_path)
    contract = importlib.util.module_from_spec(contract_spec)
    sys.modules[contract_spec.name] = contract
    contract_spec.loader.exec_module(contract)
    contract.verify_live_gpu_reservation()
    visual.configure_threads()
    budget = Budget(n, reg)
    raw_dir, output_dir = n / "raw66", n / "outputs66"
    raw_dir.mkdir(); output_dir.mkdir()
    current = {}
    def on_event(kind, payload):
        if kind == "generation_raw":
            require(current, "Raw output must have an explicit role and original uid")
            budget.save(raw_dir / (current["uid"] + "." + current["role"] + ".json"),
                        dict(event=kind, **current, payload=payload))
        else:
            with (n / "events66.jsonl").open("a", encoding="utf8") as stream:
                stream.write(json.dumps(dict(event=kind, payload=payload), allow_nan=False) + "\n")
                stream.flush(); os.fsync(stream.fileno())
    cls = runtime_class(modules["content_choice_v1.runtime"], modules["native_preference_v1.runtime"], visual)
    runtime = cls(manifest["model_spec"], reg["final_adapter_ref"], w, check_budget=budget.check, on_event=on_event)
    runtime.load()
    grammar = modules["native_preference_v1.run"].grammar_module(manifest)
    vocabulary = grammar.ascii_token_candidates(runtime.tokenizer)
    store = modules["native_preference_v1.inputs"].NativeInputStore(manifest, "check")
    refs = {role: [] for role in ROLES}
    try:
        for uid in sorted(store.case_ids):
            original, values, clock = store.case(uid)
            shifted = modules["content_choice_v1.runtime"].permute_visual(values)
            for role, actual in [("real", values), ("shift", shifted)]:
                case_ref = accepted["case_refs"][role][uid]; case = readref(case_ref, w)
                require(case == dict(derived_request(original, role, visual.tensor_signature(actual)),
                                     original_request_ref=store.request_refs[uid], original_window_ref=case["original_window_ref"]),
                        "Actual role/input bytes differ from prepared derived request")
                current.clear(); current.update(uid=uid, role=role)
                constraint = modules["content_choice_v1.run"].constraint_for(runtime, grammar, vocabulary, actual, case)
                generated = runtime.generate(actual, constraint)  # Raw is durably saved by on_event BEFORE QA.
                primary = dict(role=role, uid=uid, source_id=original["sid"], case_ref=case_ref,
                               raw_ref=reference(raw_dir / (uid + "." + role + ".json")),
                               original_request_ref=store.request_refs[uid], clock_ref=store.sources[original["sid"]]["clock_ref"], **generated)
                primary_ref = budget.save(output_dir / (uid + "." + role + ".primary.json"), primary)
                chosen = modules["content_choice_v1.adoption"].validate_answer(runtime, case, clock,
                           generated["text"], generated["ids"], grammar, vocabulary)
                require(generated["input_signature"] == case["input_signature"], "Generation role signature differs")
                refs[role].append(budget.save(output_dir / (uid + "." + role + ".json"),
                     dict(**primary, primary_ref=primary_ref, status="ACCEPTED", selected_ordinals=chosen, legal_empty=not chosen)))
            del values, shifted
    finally:
        store.close()
    require(runtime.counts["generation_calls"] == runtime.counts["generations_completed"] == 86 and
            runtime.counts["backward_calls"] == runtime.counts["optimizer_steps"] == runtime.counts["sequence_score_calls"] == 0,
            "Exactly86 fresh greedy generations and no hidden TF/training")
    verification_ref = budget.save(n / "frozen_verification66.json", runtime.verify_frozen())
    return budget.save(n / "gpu_completion66.json", dict(status="ENGINEERING_COMPLETE_TIME_TRANSFER66_NOT_QUALITY",
         output_refs=refs, input_acceptance_ref=admission["input_acceptance_ref"], counts=dict(runtime.counts),
         runtime=runtime.identity(), frozen_verification_ref=verification_ref, seconds=time.monotonic() - budget.started,
         registration_ref=admission["registration_ref"], new_model_generations=86, new_updates=0,
         automatic_production=False, new_ZIP=0, official_submissions=0))


def review(root):
    n, w, reg, admission, manifest, modules, visual, _ = context(root, "review")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CPU-only independent output review")
    save(n / "review_claim66.json", dict(registration_ref=admission["registration_ref"],
                                         automatic_retry=False, pid=os.getpid()))
    require(admission["natural_wrapper_exit_code"] == 0 and admission["unique_ledger"] == "PASS"
            and checked(admission["gpu_completion_ref"], w) == n / "gpu_completion66.json", "Unique natural GPU completion before evaluation")
    resource = readref(admission["resource_ref"], w)
    require(resource["status"] == "completed" and resource["exit_code"] == 0, "Natural wrapper terminal")
    done = readref(admission["gpu_completion_ref"], w)
    require(done["status"] == "ENGINEERING_COMPLETE_TIME_TRANSFER66_NOT_QUALITY"
            and done["registration_ref"] == admission["registration_ref"], "Exact generated final weights")
    verified = readref(done["frozen_verification_ref"], w)
    require(verified["status"] == "PASS_FROZEN_BASE_TIME288_AND_FINAL_VISUAL108", "All model roles must be immutable")
    accepted = readref(done["input_acceptance_ref"], w)
    store = modules["native_preference_v1.inputs"].NativeInputStore(manifest, "check")
    tokenizer = modules["native_preference_v1.runtime"].load_tokenizer(manifest["model_spec"])
    reader = SimpleNamespace(tokenizer=tokenizer, eos=tokenizer.convert_tokens_to_ids("<|im_end|>"))
    grammar = modules["native_preference_v1.run"].grammar_module(manifest)
    vocabulary = grammar.ascii_token_candidates(tokenizer)
    rows = {role: [] for role in ROLES}
    for role in ROLES:
        for rr in done["output_refs"][role]:
            row = readref(rr, w); uid = row["uid"]
            require(row["case_ref"] == accepted["case_refs"][role][uid] and row["role"] == role
                    and row["original_request_ref"] == store.request_refs[uid], "Independent derived role/request binding")
            case = readref(row["case_ref"], w); original = store.requests[uid]
            require(case["original_input_signature"] == original["input_signature"] and
                    row["input_signature"] == case["input_signature"], "Independent original/transformed tensor identity")
            primary = readref(row["primary_ref"], w)
            require(all(row[k] == v for k, v in primary.items()), "Accepted output differs from first primary")
            raw = readref(row["raw_ref"], w)
            require(raw["uid"] == uid and raw["role"] == role and raw["payload"]["ids"] == row["ids"]
                    and raw["payload"]["input_signature"] == row["input_signature"]
                    and raw["payload"]["raw_text"] == tokenizer.decode(row["ids"], skip_special_tokens=False,
                                                        clean_up_tokenization_spaces=False),
                    "First raw-before-QA output differs from accepted tokens/role/signature")
            chosen = modules["content_choice_v1.adoption"].validate_answer(reader, case, store.clocks[original["sid"]],
                       row["text"], row["ids"], grammar, vocabulary)
            require(chosen == row["selected_ordinals"], "First independent token/grammar/native membership differs")
            rows[role].append(row)
    selections, empty_windows = complete_unions(rows, store.case_ids, store.source_ids)
    old = readref(reg["original_collection_ref"], w)
    require(set(old["sources"]) == set(store.source_ids), "Fixed all-eight old control denominator")
    greedy = {sid: set(old["sources"][sid]["candidates"][0]["selected_ordinals"]) for sid in store.source_ids}
    humans = modules["content_choice_v1.run"].source_humans(store)
    report = modules["content_choice_v1.evaluate"].compare_selections(humans, greedy,
                 {"vision_real": selections["real"], "vision_shift": selections["shift"]})
    reasons = transfer_reasons(report, greedy, selections["real"])
    report_ref = save(n / "full_source_report66.json", report)
    pilot_review = readref(reg["review63_ref"], w)
    positive_status = ("DIAGNOSTIC_GAIN_REQUIRES_SEPARATE_REVIEW" if pilot_review["status"] == "STOP"
                       else "ELIGIBLE_FOR_SEPARATE_PRODUCTION_REVIEW")
    return save(n / "review66.json", dict(status="STOP_TIME_TRANSFER66" if reasons else positive_status,
         stop_reasons=reasons, report_ref=report_ref, macro=report["macro"], effects=report["effects"],
         legal_empty_windows=empty_windows, legal_empty_sources={r: [sid for sid, s in selections[r].items() if not s] for r in ROLES},
         first_independent_output_QA="ALL86_ROLE_TOKEN_GRAMMAR_NATIVE_PASS", native_sources=8, native_windows=43,
         original_controls_adopted=43, gpu_completion_ref=admission["gpu_completion_ref"], resource_ref=admission["resource_ref"],
         fixed_content_shift_is_not_prepost_DID=True, historically_exposed_summary_proxy=True,
         official_joint_score="UNKNOWN", spatial_role_changed=False, head53_used_for_time_selection=False,
         pilot_pair_gate_preserved=pilot_review["status"], purpose=reg.get("purpose"), production_admitted=False,
         automatic_production=False, new_ZIP=0, official_submissions=0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--run-root", required=True)
    parser.add_argument("--phase", choices=["prepare", "generate", "review"], required=True)
    args = parser.parse_args()
    try:
        globals()[args.phase](args.run_root)
    except BaseException:
        path = Path(args.run_root) / ("failure_" + args.phase + "66.json")
        if not path.exists(): save(path, dict(status="ACTUAL_FAILURE_KEEP_RAW_SUCCESS_NO_AUTOMATIC_RETRY",
             traceback=traceback.format_exc(), automatic_retry=False, failed_output_to_empty=False))
        raise
