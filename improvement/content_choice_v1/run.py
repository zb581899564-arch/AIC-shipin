"""Explicit bounded stages for three independent content-choice mechanisms.

No import starts CUDA, downloads, decodes media or trains. Production and
packaging each require a separate candidate-specific execution-agent review.
"""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "improvement.content_choice_v1"

import argparse
from fractions import Fraction
from pathlib import Path
import sys
import traceback

from improvement.native_preference_v1 import assets as asset_api
from improvement.native_preference_v1.inputs import NativeInputStore
from improvement.native_preference_v1.run import Journal, grammar_module, require_production_assets
from .adoption import adopt_check, adopt_formal, validate_answer
from .admission import production_refs, package_refs
from .contracts import (CANDIDATES, StageBudget, admission_gate, bind_artifact, checked,
    claim, code_identity, ordered_cases, pipeline_parameters, reference, require,
    same_reference, sample_seed, save_new, source_plan, strict_load, utc_now, validate_config)
from .critic import fit_with_loso, full_utility, score_source
from .evaluate import admission_reasons, compare_selections, evaluate_pool
from .selection import aggregate_source, choose, fixed_scores, validate_source_candidates
from .verification import (answer_reader, frozen_receipt, validate_window_outputs,
    collection_call_counts, check_call_counts, original_request_core_equal, verify_saved_observation)


def required(args, *names):
    for name in names:
        require(getattr(args, name, None) is not None, "Explicit --" + name.replace("_", "-") + " is required")


def load_plan(path, binding, manifest):
    value = strict_load(checked(reference(path), manifest["workspace_root"]))
    bind_artifact(value, binding)
    require(value.get("schema") == "AIC_CONTENT_CHOICE_PLAN_V1"
            and value.get("status") == "READY_FOR_EXPLICIT_BOUNDED_STAGES", "Complete new source plan required")
    for scope in ("train", "check"):
        store = NativeInputStore(manifest, scope)
        require(source_plan(store) == value["scopes"][scope], "Frozen complete-source scope changed")
    return value


def plan(config, manifest, binding, directory, budget, args):
    scopes = {}
    for scope in ("train", "check"):
        store = NativeInputStore(manifest, scope)
        require(len(store.source_ids) == config[scope + "_sources"]
                and len(store.case_ids) == config[scope + "_windows"], "Adopted source/window denominator differs")
        scopes[scope] = source_plan(store)
    train_hash = set(scopes["train"]["source_sha256"].values())
    check_hash = set(scopes["check"]["source_sha256"].values())
    require(len(train_hash) == 25 and len(check_hash) == 8 and not train_hash & check_hash,
            "Complete source byte duplicates or split intersection")
    require(manifest.get("reference_generation_origin"), "Original successful43 controls must be explicitly adopted")
    value = dict(schema="AIC_CONTENT_CHOICE_PLAN_V1", status="READY_FOR_EXPLICIT_BOUNDED_STAGES",
        **binding, scopes=scopes, source_selection="All25 SumMe and all8 historical VideoXum; no replacement",
        original_DPO_STOP_unchanged=True, source_candidates=4,
        targets_read=False, model_calls=0, automatic_production=False, budget=budget.snapshot())
    return save_new(directory / "plan.json", value)


def constraint_for(runtime, grammar, vocabulary, values, request):
    return grammar.PrefixConstraint(runtime.tokenizer, values["input_ids"].shape[1],
        Fraction(request["plan"]["window_end_exact"]) - Fraction(request["plan"]["window_start_exact"]),
        max_segments=6, candidate_token_ids=vocabulary, eos_token_ids=[runtime.eos], allow_empty=True)


def make_slot(runtime, grammar, vocabulary, request, clock, generated, slot):
    require(isinstance(generated, dict) and isinstance(generated.get("text"), str),
            "Actual generated/adopted answer required")
    selected = validate_answer(runtime, request, clock, generated["text"], generated["ids"], grammar, vocabulary)
    if "selected_ordinals" in generated:
        require(generated["selected_ordinals"] == selected, "Adopted candidate native membership changed")
    return dict(status="ACCEPTED", slot=slot, text=generated["text"], ids=generated["ids"],
        selected_ordinals=selected, legal_empty=not selected,
        origin="EXPLICIT_EMPTY_ACTION" if slot == 3 else "ADOPTED_ORIGINAL_TIME" if
            generated.get("adopted_historical_model_call") else "NEW_ORIGINAL_TIME_GENERATION",
        historical_output_ref=generated.get("historical_output_ref"),
        sample_seed=sample_seed(request["source_sha256"], request["uid"], slot) if slot in (1, 2) else None)


def collect_core(runtime, store, manifest, directory, journal, budget, *, controls=None,
                 counterfactual=True):
    """Actual common generator/feature path, used unchanged by pilot and production."""
    from .runtime import permute_visual
    from improvement.native_preference_v1.runtime import tensor_signature
    grammar = grammar_module(manifest)
    vocabulary = grammar.ascii_token_candidates(runtime.tokenizer)
    controls = {} if controls is None else controls
    require(set(controls) <= set(store.case_ids), "Control cache contains a foreign window")
    if store.scope in ("check", "production"):
        require(set(controls) == set(store.case_ids), "Do not repeat already successful original TIME controls")
    rows, source_rows = {}, {}
    for number, uid in enumerate(ordered_cases(store)):
        budget.check()
        request, values, clock = store.case(uid)
        journal.context = dict(uid=uid, scope=store.scope, source_id=request["sid"])
        candidates = []
        for slot in range(4):
            if slot == 0 and uid in controls:
                generated = strict_load(checked(controls[uid], store.workspace))
                require(generated.get("status") == "ACCEPTED"
                        and same_reference(generated["request_ref"], store.request_refs[uid])
                        and generated["input_signature"] == request["input_signature"],
                        "Retained greedy control input identity differs")
            elif slot == 3:
                text = '{"segments":[]}'
                generated = dict(text=text, ids=runtime.tokenize_answer(values, text,
                                         request_text=request["text"]["expanded_text"]))
            else:
                constraint = constraint_for(runtime, grammar, vocabulary, values, request)
                generated = (runtime.generate(values, constraint) if slot == 0 else
                    runtime.generate_sample(values, constraint,
                        sample_seed(request["source_sha256"], uid, slot)))
                require(generated["input_signature"] == request["input_signature"], "Actual generated input changed")
            candidates.append(make_slot(runtime, grammar, vocabulary, request, clock, generated, slot))
        # One actual score per distinct exact suffix, with cache aliases within
        # this immutable input only. Native-equal but token-different answers
        # remain distinct observations; references do not determine this cache.
        score_cache = {}
        rotated = permute_visual(values) if counterfactual else None
        rotated_signature = tensor_signature(runtime.torch, rotated) if counterfactual else None
        identical = counterfactual and rotated_signature == request["input_signature"]
        for candidate in candidates:
            key = tuple(candidate["ids"])
            if key not in score_cache:
                real = runtime.score_features(values, candidate["ids"])
                shifted = (dict(real, actual_model_call=False, identity_cache_alias=True) if identical else
                           runtime.score_features(rotated, candidate["ids"]) if counterfactual else None)
                score_cache[key] = (real, shifted, candidate["slot"])
            real, shifted, first_slot = score_cache[key]
            candidate.update(real=real, permuted=shifted, score_cache_first_slot=first_slot)
        row = dict(schema="AIC_CONTENT_CHOICE_WINDOW_V1", status="ACCEPTED", uid=uid,
            source_id=request["sid"], source_sha256=request["source_sha256"], scope=store.scope,
            request_ref=store.request_refs[uid], clock_ref=store.sources[request["sid"]]["clock_ref"],
            input_signature=request["input_signature"], slots=candidates, labels_read=False,
            counterfactual="HALF_TEMPORAL_GROUP_CIRCULAR_SHIFT_PER_VIEW" if counterfactual else None,
            counterfactual_input_signature=rotated_signature, counterfactual_identical_input=identical,
            control_ref=controls.get(uid))
        row_ref = save_new(directory / ("window_" + str(number).zfill(4) + ".json"), row)
        rows[uid] = row_ref
        journal("window_complete", dict(window_ref=row_ref, scores=len(score_cache), labels_read=False))
    for sid in store.source_ids:
        requests = {uid: store.requests[uid] for uid in store.by_source[sid]}
        windows = {uid: strict_load(checked(rows[uid], store.workspace)) for uid in requests}
        source = aggregate_source(sid, store.sources[sid]["source_sha256"], store.clocks[sid], requests, windows)
        source_rows[sid] = source
    require(set(rows) == set(store.case_ids) and set(source_rows) == set(store.source_ids), "Collection incomplete")
    expected_counts = collection_call_counts(
        {uid: strict_load(checked(ref, store.workspace)) for uid, ref in rows.items()}, adopted=bool(controls))
    check_call_counts(runtime.counts, expected_counts)
    return dict(window_refs=rows, sources=source_rows,
        source_count=len(source_rows), window_count=len(rows),
        control_windows_adopted=len(controls), expected_actual_calls=expected_counts, all_references_unread=True)


def load_collection(path, binding, manifest, store):
    value = strict_load(checked(reference(path), store.workspace))
    bind_artifact(value, binding)
    expected_status = ("COMPLETE_PRODUCTION_NOT_PACKAGED" if store.scope == "production"
                       else "COMPLETE_CANDIDATE_COLLECTION_NOT_ADMITTED")
    require(value.get("status") == expected_status
            and (value.get("scope") == store.scope or store.scope == "production")
            and value.get("labels_read") is False,
            "Complete matching reference-free candidate collection required")
    require(set(value["window_refs"]) == set(store.case_ids), "Collection lost an accepted window")
    windows, reader = {}, answer_reader(manifest, value["runtime"])
    for uid, ref in value["window_refs"].items():
        row = strict_load(checked(ref, store.workspace))
        require(row.get("status") == "ACCEPTED" and row["uid"] == uid
                and row["input_signature"] == store.requests[uid]["input_signature"]
                and same_reference(row["request_ref"], store.request_refs[uid])
                and row["source_id"] == store.requests[uid]["sid"]
                and row["source_sha256"] == store.requests[uid]["source_sha256"]
                and row["labels_read"] is False and row["scope"] == store.scope
                and same_reference(row["clock_ref"], store.sources[row["source_id"]]["clock_ref"]),
                "Collection window/input/native identity changed")
        if row.get("control_ref"):
            checked(row["control_ref"], store.workspace)
        validate_window_outputs(row, store.requests[uid], store.clocks[row["source_id"]], reader)
        windows[uid] = row
    for sid in store.source_ids:
        actual = aggregate_source(sid, store.sources[sid]["source_sha256"], store.clocks[sid],
            {uid: store.requests[uid] for uid in store.by_source[sid]},
            {uid: windows[uid] for uid in store.by_source[sid]})
        require(actual == value["sources"][sid], "Stored source features/selections differ from full window recomposition")
    require(set(value["sources"]) == set(store.source_ids), "Collection source denominator mismatch")
    expected = collection_call_counts(windows, adopted=store.scope != "train")
    require(expected == value["expected_actual_calls"], "Saved count expectation changed")
    check_call_counts(value["counts"], expected)
    require(value["source_count"] == len(store.source_ids) and value["window_count"] == len(windows)
            and value["control_windows_adopted"] == (0 if store.scope == "train" else len(windows)),
            "Source/window/control denominator changed")
    frozen_receipt(value, store.workspace)
    return value


def runtime_context(manifest, directory, budget, torch_report):
    from .runtime import QwenChoiceRuntime
    from .torch_checks import validate_report
    gate = validate_report(torch_report, manifest["workspace_root"])
    journal = Journal(directory / "events.jsonl")
    runtime = QwenChoiceRuntime(manifest["model_spec"], budget.check, journal, seed=20261019)
    return runtime, journal, gate


def collect(config, manifest, binding, directory, budget, args):
    required(args, "plan", "partition", "torch_checks")
    load_plan(args.plan, binding, manifest)
    store = NativeInputStore(manifest, args.partition)
    prior = None
    if store.scope == "train":
        required(args, "collect_check")
        prior = load_collection(args.collect_check, binding, manifest, NativeInputStore(manifest, "check"))
    runtime, journal, gate = runtime_context(manifest, directory, budget, args.torch_checks)
    try:
        runtime.load()
        if prior is not None:
            require(runtime.identity() == prior["runtime"],
                    "Train collection must use the already checked original TIME runtime environment")
        grammar = grammar_module(manifest)
        controls = adopt_check(runtime, store, manifest, directory, journal, budget,
            grammar, grammar.ascii_token_candidates(runtime.tokenizer)) if store.scope == "check" else {}
        result = collect_core(runtime, store, manifest, directory, journal, budget, controls=controls)
        frozen = save_new(directory / "frozen_verification.json", runtime.verify_frozen())
        journal.close()
        budget.check(force_disk=True)
        return save_new(directory / "completion.json", dict(schema="AIC_CONTENT_CHOICE_COLLECTION_V1",
            status="COMPLETE_CANDIDATE_COLLECTION_NOT_ADMITTED", **binding,
            scope=store.scope, plan_ref=reference(args.plan), **result,
            collect_check_ref=reference(args.collect_check) if prior is not None else None,
            frozen_verification_ref=frozen, event_journal_ref=reference(directory / "events.jsonl"),
            runtime=runtime.identity(), counts=dict(runtime.counts), torch_checks_ref=gate,
            budget=budget.snapshot(), labels_read=False, automatic_production=False))
    finally:
        if not journal.stream.closed:
            journal.close()
        store.close()


def source_humans(store):
    require(store.scope in ("train", "check"), "Official data has no reference/fit interface")
    result = {sid: store.source_supervision(sid) for sid in store.source_ids}
    for human in result.values():
        full_utility([], human)
    return result


def fit(config, manifest, binding, directory, budget, args):
    required(args, "plan", "collect_train")
    load_plan(args.plan, binding, manifest)
    store = NativeInputStore(manifest, "train")
    collected = load_collection(args.collect_train, binding, manifest, store)
    require(len(collected["sources"]) == 25, "Fit uses all25 predeclared original SumMe sources")
    human = source_humans(store)
    result = fit_with_loso(collected["sources"], human)
    weights_ref = save_new(directory / "critic_weights.json", result["heads"]["content"])
    # Verify that the actual deployed score is exactly the reloaded131 weights.
    reloaded = strict_load(checked(weights_ref, store.workspace))
    require(all(score_source(reloaded, source) == score_source(result["heads"]["content"], source)
                for source in collected["sources"].values()), "Saved critic changes actual decisions")
    maps = {"critic": result["out_of_fold_scores"]["content"],
            "shape": result["out_of_fold_scores"]["shape"], "permuted": result["out_of_fold_scores"]["permuted"],
            "raw": {sid: fixed_scores(s, "raw") for sid, s in collected["sources"].items()}}
    oof, _ = evaluate_pool(collected["sources"], human, maps)
    budget.check(force_disk=True)
    return save_new(directory / "completion.json", dict(**result, **binding,
        status="COMPLETE_CRITIC_FIT_NOT_ADMITTED", plan_ref=reference(args.plan),
        collect_train_ref=reference(args.collect_train), weights_ref=weights_ref,
        out_of_fold_evaluation=oof, budget=budget.snapshot(),
        actual_new_qwen_calls=0, actual_gpu_updates=0, historical_exposure=True))


def load_fit(path, binding, manifest):
    value = strict_load(checked(reference(path), manifest["workspace_root"]))
    bind_artifact(value, binding)
    require(value.get("status") == "COMPLETE_CRITIC_FIT_NOT_ADMITTED"
            and value.get("actual_linear_solves") == 78 and value.get("learned_deployed_parameters") == 131,
            "Complete25-source fit plus75 source-exclusive control folds required")
    weights = strict_load(checked(value["weights_ref"], manifest["workspace_root"]))
    require(weights == value["heads"]["content"], "Frozen deployed head differs from fitted head")
    checked(value["collect_train_ref"], manifest["workspace_root"])
    return value


def observation_core(runtime, store, manifest, controls, directory, journal, budget):
    from transformers import AutoProcessor
    from .observation import build_observation_case
    import torch
    processor = AutoProcessor.from_pretrained(manifest["model_spec"]["model_dir"],
        revision=manifest["model_spec"]["revision"], local_files_only=True, trust_remote_code=False)
    require(set(controls) == set(store.case_ids), "Every original greedy control must exist")
    grammar = grammar_module(manifest)
    vocabulary = grammar.ascii_token_candidates(runtime.tokenizer)
    cache, rows, selected, changed = {}, {}, {sid: set() for sid in store.source_ids}, 0
    for index, uid in enumerate(ordered_cases(store)):
        budget.check()
        journal.context = dict(uid=uid, scope=store.scope, action="independent_observation_candidate")
        request, values, clock, diagnostic = build_observation_case(store, uid, processor, cache)
        diagnostic_ref = save_new(directory / ("diagnostic_" + str(index).zfill(4) + ".json"), diagnostic)
        if diagnostic["status"] == "NO_EFFECT":
            require(original_request_core_equal(request, store.requests[uid])
                    and diagnostic["old_success_can_be_adopted"] is True,
                    "Discarded observation must restore the entire original input before adopting its answer")
            generated = strict_load(checked(controls[uid], store.workspace))
            require(generated.get("status") == "ACCEPTED"
                    and generated["input_signature"] == request["input_signature"], "NO_EFFECT control input differs")
            request_ref = store.request_refs[uid]
        else:
            require(diagnostic["status"] == "PASS_FIRST_CHANGED_OBSERVATION_CPU_QA"
                    and diagnostic["old_visual_tokens"] == diagnostic["new_visual_tokens"],
                    "Changed observation must pass independent fixed-visual-budget input QA")
            prefix_path = directory / ("prefix_" + str(index).zfill(4) + ".pt")
            with prefix_path.open("xb") as stream:
                torch.save({key: values[key] for key in ("input_ids", "attention_mask")}, stream)
            request["prefix_ref"] = reference(prefix_path)
            restored = verify_saved_observation(store, uid, request, processor=processor)
            require(store._helpers().signature(restored) == store._helpers().signature(values),
                    "Saved prefix/plan must reconstruct this actual generation input")
            request_ref = save_new(directory / ("request_" + str(index).zfill(4) + ".json"), request)
            generated = runtime.generate(values, constraint_for(runtime, grammar, vocabulary, values, request))
            require(generated["input_signature"] == request["input_signature"], "Actual observation generation input differs")
            changed += 1
        chosen = validate_answer(runtime, request, clock, generated["text"], generated["ids"], grammar, vocabulary)
        selected[request["sid"]].update(chosen)
        row = dict(status="ACCEPTED", uid=uid, source_id=request["sid"], request_ref=request_ref,
            original_request_ref=store.request_refs[uid], input_signature=request["input_signature"],
            text=generated["text"], ids=generated["ids"], selected_ordinals=chosen,
            legal_empty=not chosen, diagnostic_ref=diagnostic_ref,
            original_control_ref=controls[uid], new_model_call=diagnostic["status"] != "NO_EFFECT")
        rows[uid] = save_new(directory / ("answer_" + str(index).zfill(4) + ".json"), row)
    check_call_counts(runtime.counts, dict(generation_calls=changed, sequence_score_calls=0, sample_generation_calls=0))
    return dict(output_refs=rows, selections={sid: sorted(values) for sid, values in selected.items()},
        changed_input_windows=changed, adopted_unchanged_windows=len(rows) - changed,
        original_inputs_overwritten=False, source_count=len(store.source_ids), window_count=len(rows))


def observation(config, manifest, binding, directory, budget, args):
    required(args, "plan", "collect_check", "torch_checks")
    load_plan(args.plan, binding, manifest)
    store = NativeInputStore(manifest, "check")
    collected = load_collection(args.collect_check, binding, manifest, store)
    controls = {uid: strict_load(checked(ref, store.workspace))["control_ref"]
                for uid, ref in collected["window_refs"].items()}
    runtime, journal, gate = runtime_context(manifest, directory, budget, args.torch_checks)
    try:
        runtime.load()
        require(runtime.identity() == collected["runtime"],
                "Observation runtime differs from the bound original control/candidate collection")
        result = observation_core(runtime, store, manifest, controls, directory, journal, budget)
        frozen = save_new(directory / "frozen_verification.json", runtime.verify_frozen())
        journal.close()
        budget.check(force_disk=True)
        return save_new(directory / "completion.json", dict(schema="AIC_CONTENT_CHOICE_OBSERVATION_V1",
            status="COMPLETE_OBSERVATION_NOT_ADMITTED", **binding, **result,
            plan_ref=reference(args.plan), collect_check_ref=reference(args.collect_check),
            runtime=runtime.identity(), counts=dict(runtime.counts), torch_checks_ref=gate,
            frozen_verification_ref=frozen, event_journal_ref=reference(directory / "events.jsonl"),
            budget=budget.snapshot(), labels_read=False, automatic_production=False))
    finally:
        if not journal.stream.closed:
            journal.close()
        store.close()


def read_observation(path, binding, store):
    value = strict_load(checked(reference(path), store.workspace))
    bind_artifact(value, binding)
    expected_status = ("COMPLETE_PRODUCTION_NOT_PACKAGED" if store.scope == "production"
                       else "COMPLETE_OBSERVATION_NOT_ADMITTED")
    require(value.get("status") == expected_status
            and set(value["output_refs"]) == set(store.case_ids), "Complete independent observation result required")
    selections = {sid: set() for sid in store.source_ids}
    reader, grammar, vocabulary = answer_reader(store.manifest, value["runtime"])
    changed = 0
    for uid, ref in value["output_refs"].items():
        row = strict_load(checked(ref, store.workspace))
        req = strict_load(checked(row["request_ref"], store.workspace))
        diagnostic = strict_load(checked(row["diagnostic_ref"], store.workspace))
        checked(row["original_control_ref"], store.workspace)
        checked(req["prefix_ref"], store.workspace)
        require(row.get("status") == "ACCEPTED" and row["uid"] == uid
                and same_reference(row["original_request_ref"], store.request_refs[uid])
                and row["source_id"] == req["sid"] == store.requests[uid]["sid"]
                and req["input_signature"] == row["input_signature"]
                and row["ids"][-1] == value["runtime"]["eos_token_id"]
                and value["runtime"]["eos_token_id"] not in row["ids"][:-1],
                "Observation answer/input/source/EOS identity mismatch")
        if not row["new_model_call"]:
            require(diagnostic["status"] == "NO_EFFECT" and req == store.requests[uid],
                    "An unchanged-answer adoption must retain original coordinates/input")
        else:
            require(diagnostic["status"] == "PASS_FIRST_CHANGED_OBSERVATION_CPU_QA"
                    and all(diagnostic[k] is True for k in ("same_budget", "changed_pixel_bytes",
                        "independent_pixel_QA", "independent_processor_text_QA"))
                    and diagnostic["new_visual_tokens"] == diagnostic["old_visual_tokens"],
                    "Changed observation lost its real fixed-budget input QA")
            verify_saved_observation(store, uid, req)
            changed += 1
        clock = store.clocks[req["sid"]]
        chosen = validate_answer(reader, req, clock, row["text"], row["ids"], grammar, vocabulary)
        require(chosen == row["selected_ordinals"] and row["legal_empty"] == (not chosen),
                "Independent observation native parse differs")
        selections[req["sid"]].update(chosen)
    require({sid: sorted(v) for sid, v in selections.items()} == value["selections"], "Complete observation union differs")
    require(changed == value["changed_input_windows"]
            and len(store.case_ids) - changed == value["adopted_unchanged_windows"]
            and value["source_count"] == len(store.source_ids) and value["window_count"] == len(store.case_ids),
            "Observation actual/adopted call denominator differs")
    check_call_counts(value["counts"], dict(generation_calls=changed, sequence_score_calls=0, sample_generation_calls=0))
    frozen_receipt(value, store.workspace)
    return value, selections


def review(config, manifest, binding, directory, budget, args):
    required(args, "plan", "candidate", "collect_check")
    load_plan(args.plan, binding, manifest)
    store = NativeInputStore(manifest, "check")
    collected = load_collection(args.collect_check, binding, manifest, store)
    human = source_humans(store)
    refs = dict(plan_ref=reference(args.plan), collect_check_ref=reference(args.collect_check))
    oof, observation_evidence = None, None
    if args.candidate == "observation":
        required(args, "observation_run")
        observation_evidence, selected = read_observation(args.observation_run, binding, store)
        require(same_reference(observation_evidence["collect_check_ref"], refs["collect_check_ref"]),
                "Observation uses another control collection")
        require(observation_evidence["runtime"] == collected["runtime"], "Observation/control runtime drift")
        refs["observation_ref"] = reference(args.observation_run)
        greedy = {sid: set(value["candidates"][0]["selected_ordinals"]) for sid, value in collected["sources"].items()}
        cross = compare_selections(human, greedy, {"observation": selected})
    else:
        scores = {"raw": {sid: fixed_scores(s, "raw") for sid, s in collected["sources"].items()}}
        if args.candidate == "contrast":
            scores["contrast"] = {sid: fixed_scores(s, "contrast") for sid, s in collected["sources"].items()}
        else:
            required(args, "fit_run")
            fitted = load_fit(args.fit_run, binding, manifest)
            refs.update(fit_ref=reference(args.fit_run), weights_ref=fitted["weights_ref"],
                        collect_train_ref=fitted["collect_train_ref"])
            train_store = NativeInputStore(manifest, "train")
            train = load_collection(fitted["collect_train_ref"]["path"], binding, manifest, train_store)
            require(train["runtime"] == collected["runtime"]
                    and same_reference(train["collect_check_ref"], refs["collect_check_ref"]),
                    "Critic train/check feature extractor or sampling environment differs")
            require(set(fitted["heads"]["content"]["fit_source_sha256"].values())
                    == {s["source_sha256"] for s in train["sources"].values()}, "Fitted source identity changed")
            require(not set(fitted["heads"]["content"]["fit_source_sha256"].values())
                    & {s["source_sha256"] for s in collected["sources"].values()}, "Source train/check leakage")
            for name, kind in (("critic", "content"), ("shape", "shape"), ("permuted", "permuted")):
                scores[name] = {sid: score_source(fitted["heads"][kind], source)
                                for sid, source in collected["sources"].items()}
            oof = fitted["out_of_fold_evaluation"]
        cross, all_selected = evaluate_pool(collected["sources"], human, scores)
        selected = all_selected[args.candidate]
    stops = admission_reasons(args.candidate, cross, oof=oof, observation_evidence=observation_evidence)
    selection_ref = save_new(directory / "external_selection.json", dict(
        schema="AIC_CONTENT_CHOICE_SELECTION_V1",
        sources={sid: dict(status="ACCEPTED", selected_ordinals=sorted(values)) for sid, values in selected.items()}))
    budget.check(force_disk=True)
    return save_new(directory / "review.json", dict(schema="AIC_CONTENT_CHOICE_REVIEW_V1",
        status="STOP_MECHANISM" if stops else "ELIGIBLE_FOR_EXECUTION_REVIEW", **binding,
        candidate=args.candidate, **refs, selection_ref=selection_ref, stop_reasons=stops,
        runtime=collected["runtime"],
        cross_source_evaluation=cross, out_of_fold_evaluation=oof,
        observation_evidence_summary=({key: observation_evidence[key] for key in
            ("changed_input_windows", "adopted_unchanged_windows")} if observation_evidence else None),
        actual_pipeline_parameters=pipeline_parameters(args.candidate), budget=budget.snapshot(),
        DPO_STOP_unchanged=True, automatic_production=False, official_score="NOT_MEASURED"))


def load_review(path, binding, manifest, candidate):
    value = strict_load(checked(reference(path), manifest["workspace_root"]))
    bind_artifact(value, binding)
    require(value.get("schema") == "AIC_CONTENT_CHOICE_REVIEW_V1"
            and value.get("candidate") == candidate and value.get("status") == "ELIGIBLE_FOR_EXECUTION_REVIEW"
            and value.get("stop_reasons") == [], "A stopped/incomplete candidate cannot enter production review")
    require(not admission_reasons(candidate, value["cross_source_evaluation"],
        oof=value["out_of_fold_evaluation"], observation_evidence=value["observation_evidence_summary"]),
        "Review metrics no longer pass the predeclared mechanism conditions")
    for key in ("plan_ref", "collect_check_ref", "selection_ref", "fit_ref", "weights_ref",
                "collect_train_ref", "observation_ref"):
        if key in value:
            checked(value[key], manifest["workspace_root"])
    return value


def production(config, manifest, binding, directory, budget, args):
    if getattr(args, "production_pool", None) is not None:
        from .reuse import production_from_pool
        return production_from_pool(config, manifest, binding, directory, budget, args)
    required(args, "candidate", "review_run", "production_assets", "formal_qa", "admission", "torch_checks")
    reviewed = load_review(args.review_run, binding, manifest, args.candidate)
    formal = asset_api.load_assets(args.production_assets, verify_files=True)
    require_production_assets(manifest, formal)
    save_new(directory / "formal_asset_preflight.json", dict(status="PASS_FORMAL_ASSET_BYTES_BEFORE_MODEL",
        production_assets_ref=reference(args.production_assets), model_loaded=False,
        report=asset_api.preflight_assets(formal, "production", verify_files=False)))
    budget.check(force_disk=True)
    expected = production_refs(binding, reviewed, args.review_run, args.production_assets, args.formal_qa)
    admission = strict_load(checked(reference(args.admission), manifest["workspace_root"]))
    require("production_pool_ref" not in admission,
            "CPU pool reuse admission cannot authorize a new model run; pass its explicit --production-pool")
    admission_gate(admission, "production", args.candidate, expected, manifest["workspace_root"])
    store = NativeInputStore(formal, "production")
    require(len(store.source_ids) == config["max_production_sources"] == 426
            and len(store.case_ids) == config["max_production_windows"] == 522,
            "Exact admitted formal426/522 denominator required")
    runtime, journal, gate = runtime_context(formal, directory, budget, args.torch_checks)
    try:
        runtime.load()
        require(runtime.identity() == reviewed["runtime"],
                "Production feature extractor/sampler differs from the exact reviewed pilot runtime")
        grammar = grammar_module(formal)
        controls = adopt_formal(runtime, store, formal, args.formal_qa, directory, journal, budget,
                               grammar, grammar.ascii_token_candidates(runtime.tokenizer))
        if args.candidate == "observation":
            result = observation_core(runtime, store, formal, controls, directory, journal, budget)
            selected = result["selections"]
        else:
            result = collect_core(runtime, store, formal, directory, journal, budget,
                                  controls=controls, counterfactual=args.candidate == "contrast")
            if args.candidate == "critic":
                fitted = load_fit(reviewed["fit_ref"]["path"], binding, manifest)
                head = fitted["heads"]["content"]
                scores = {sid: score_source(head, source) for sid, source in result["sources"].items()}
            else:
                scores = {sid: fixed_scores(source, "contrast") for sid, source in result["sources"].items()}
            selected = {sid: choose(source, scores[sid])["selected_ordinals"] for sid, source in result["sources"].items()}
        frozen = save_new(directory / "frozen_verification.json", runtime.verify_frozen())
        selection_ref = save_new(directory / "selection.json", dict(schema="AIC_CONTENT_CHOICE_SELECTION_V1",
            sources={sid: dict(status="ACCEPTED", selected_ordinals=values)
                                               for sid, values in selected.items()}))
        journal.close()
        budget.check(force_disk=True)
        return save_new(directory / "completion.json", dict(schema="AIC_CONTENT_CHOICE_PRODUCTION_V1",
            status="COMPLETE_PRODUCTION_NOT_PACKAGED", **binding, **result,
            candidate=args.candidate, production_assets_ref=reference(args.production_assets),
            review_ref=reference(args.review_run), formal_qa_ref=reference(args.formal_qa),
            admission_ref=reference(args.admission), selection_ref=selection_ref,
            actual_pipeline_parameters=pipeline_parameters(args.candidate), frozen_verification_ref=frozen,
            event_journal_ref=reference(directory / "events.jsonl"), runtime=runtime.identity(),
            counts=dict(runtime.counts), torch_checks_ref=gate, labels_read=False,
            budget=budget.snapshot(), automatic_package=False, website_submitted=False))
    finally:
        if not journal.stream.closed:
            journal.close()
        store.close()


def package(config, manifest, binding, directory, budget, args):
    from .render import render_candidate
    from .reuse import MODE as REUSE_MODE, load_reused_production
    required(args, "candidate", "production_assets", "production_run", "admission")
    formal = asset_api.load_assets(args.production_assets, verify_files=True)
    require_production_assets(manifest, formal)
    complete_ref = reference(args.production_run)
    complete = strict_load(checked(complete_ref, manifest["workspace_root"]))
    bind_artifact(complete, binding)
    require(complete.get("candidate") == args.candidate and complete.get("status") == "COMPLETE_PRODUCTION_NOT_PACKAGED"
            and same_reference(complete["production_assets_ref"], reference(args.production_assets)),
            "Separate complete candidate production required")
    reviewed = load_review(complete["review_ref"]["path"], binding, manifest, args.candidate)
    require(complete["runtime"] == reviewed["runtime"]
            and complete["actual_pipeline_parameters"] == pipeline_parameters(args.candidate),
            "Completed production differs from its reviewed environment/parameter count")
    require(complete.get("execution_mode") in (None, REUSE_MODE), "Unknown production execution mode")
    require(complete.get("execution_mode") != REUSE_MODE or args.candidate == "critic",
            "CPU contrast-pool reuse can only package the independently reviewed critic")
    evidence = ("event_journal_ref", "admission_ref", "formal_qa_ref")
    evidence += (("cpu_reuse_verification_ref",) if complete.get("execution_mode") == REUSE_MODE
                 else ("frozen_verification_ref",))
    for key in evidence:
        checked(complete[key], manifest["workspace_root"])
    selected = strict_load(checked(complete["selection_ref"], manifest["workspace_root"]))
    store = NativeInputStore(formal, "production")
    if args.candidate == "observation":
        _, reproduced = read_observation(args.production_run, binding, store)
    else:
        pool = (load_reused_production(complete, binding, manifest, formal, store, reviewed)
                if complete.get("execution_mode") == REUSE_MODE else
                load_collection(args.production_run, binding, formal, store))
        if args.candidate == "critic":
            head = load_fit(reviewed["fit_ref"]["path"], binding, manifest)["heads"]["content"]
            reproduced = {sid: score_source(head, source) for sid, source in pool["sources"].items()}
        else:
            reproduced = {sid: fixed_scores(source, "contrast") for sid, source in pool["sources"].items()}
        reproduced = {sid: set(choose(pool["sources"][sid], scores)["selected_ordinals"])
                      for sid, scores in reproduced.items()}
    require(selected == dict(schema="AIC_CONTENT_CHOICE_SELECTION_V1", sources={sid:
        dict(status="ACCEPTED", selected_ordinals=sorted(values)) for sid, values in reproduced.items()}),
        "Independent formal token/native/whole-source decision review changed packaged selections")
    save_new(directory / "independent_production_output_qa.json", dict(
        status="PASS_REREAD_ALL522_OUTPUTS_AND426_SOURCE_DECISIONS", model_calls=0,
        source_count=len(store.source_ids), window_count=len(store.case_ids),
        production_completion_ref=complete_ref, selection_ref=complete["selection_ref"]))
    store.close()
    expected = package_refs(binding, complete, args.production_run, args.production_assets)
    admission_ref = reference(args.admission)
    admitted = strict_load(checked(admission_ref, manifest["workspace_root"]))
    admission_gate(admitted, "package", args.candidate, expected, manifest["workspace_root"])
    result = render_candidate(formal, selected, directory / "rendered", candidate=args.candidate,
        parameter_count=pipeline_parameters(args.candidate), admission=admitted, expected_refs=expected)
    budget.check(force_disk=True)
    return save_new(directory / "completion.json", dict(schema="AIC_CONTENT_CHOICE_PACKAGE_V1",
        **binding, candidate=args.candidate, receipt=result, budget=budget.snapshot(), website_submitted=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("preflight", "plan", "diagnose-dpo", "collect",
                                                         "fit", "observation", "review", "production", "package"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--candidate", choices=CANDIDATES)
    parser.add_argument("--partition", choices=("train", "check"))
    for name in ("plan", "collect-train", "collect-check", "fit-run", "observation-run", "review-run",
                 "production-assets", "production-run", "formal-qa", "admission", "torch-checks",
                 "dpo-completion", "dpo-review", "production-pool"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args(argv)
    require(args.production_pool is None or (args.stage == "production" and args.candidate == "critic"),
            "--production-pool is only valid for explicit critic production")
    config = validate_config(strict_load(args.config))
    identity = code_identity()
    manifest = asset_api.load_assets(args.assets, verify_files=False)
    binding = dict(config_ref=reference(args.config), asset_manifest_ref=reference(args.assets), code_identity=identity)
    stage = args.stage.replace("-", "_")
    if args.stage == "collect":
        required(args, "partition")
        stage += "_" + args.partition
    if args.stage in ("review", "production", "package"):
        required(args, "candidate")
        stage += "_" + args.candidate
    seconds, forwards = config["max_cpu_seconds"], 0
    if args.stage == "collect":
        seconds = config["max_collect_" + args.partition + "_seconds"]
        windows = config[args.partition + "_windows"]
        forwards = windows * ((3 if args.partition == "train" else 2) * 512 + 8)
    elif args.stage == "observation":
        seconds, forwards = config["max_observation_seconds"], config["check_windows"] * 512
    elif args.stage == "production" and args.production_pool is None:
        seconds = config["max_production_seconds"]
        forwards = config["max_production_windows"] * (512 if args.candidate == "observation" else
                   (2 * 512 + (8 if args.candidate == "contrast" else 4)))
    directory = claim(config, manifest, stage, binding)
    budget = StageBudget(Path(config["run_root"]), seconds, config["max_output_bytes"], forwards)
    try:
        asset_report = asset_api.preflight_assets(manifest)
        save_new(directory / "asset_preflight.json", dict(status="PASS_ASSET_BYTES_ONLY", report=asset_report,
            model_loaded=False, original_DPO_result_not_reassessed=True))
        budget.check(force_disk=True)
        if args.stage == "preflight":
            result = save_new(directory / "completion.json", dict(status="PASS_ASSET_BYTES_ONLY", **binding,
                actual_new_qwen_calls=0, budget=budget.snapshot()))
        elif args.stage == "diagnose-dpo":
            from .dpo_diagnostic import diagnose
            required(args, "dpo_completion", "dpo_review")
            result = save_new(directory / "diagnostic.json", dict(**binding,
                **diagnose(args.dpo_completion, args.dpo_review, manifest["workspace_root"])))
        else:
            function = {"plan": plan, "collect": collect, "fit": fit, "observation": observation,
                        "review": review, "production": production, "package": package}[args.stage]
            result = function(config, manifest, binding, directory, budget, args)
        report = strict_load(result["path"])
        print(__import__("json").dumps(dict(status=report.get("status", "COMPLETE_EXPLICIT_STAGE"),
                                           output=result, actual_gpu_execution=args.stage in
                                           ("collect", "observation", "production")
                                           and args.production_pool is None), ensure_ascii=False))
        return 3 if report.get("status") == "STOP_MECHANISM" else 0
    except BaseException as error:
        save_new(directory / "failure.json", dict(status="FAILED", error_type=type(error).__name__,
            error=str(error), traceback=traceback.format_exc(), utc=utc_now(), **binding,
            budget=budget.snapshot(), failure_to_empty=False, automatic_retry=False,
            all_previous_success_failure_raw_and_cost_preserved=True))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
