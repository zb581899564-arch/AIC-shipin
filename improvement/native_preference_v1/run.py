"""Explicit, separately claimed CPU preparation, bounded pilot, review and production.

This entry point never discovers latest files, downloads models, retries a failed
stage, turns an execution failure into [], or chains a pilot into production.
"""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "improvement.native_preference_v1"

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

from .contracts import (BASE_COMMIT, StageBudget, checked, claim_stage, digest,
    reference, require, same_reference, save_new, strict_load,
    successful_source_selections, utc_now, validate_admission, validate_config)
from . import assets as asset_api
from .inputs import NativeInputStore, _bound_module
from .preference import make_preference_pairs, native_selection, parse_answer


HERE = Path(__file__).resolve().parent
ROLES = ("reference", "policy")
PREPARED_STATUS = "READY_FOR_BOUNDED_PILOT"
PILOT_STATUS = "COMPLETE_PILOT_NOT_ADMITTED"
PRODUCTION_STATUS = "COMPLETE_PRODUCTION_NOT_PACKAGED"


def stable_key(*values):
    return hashlib.sha256(json.dumps(values, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def code_identity():
    """Verify the closed set of this release's Python files before doing work."""
    manifest_path = HERE / "code_manifest.json"
    manifest = strict_load(manifest_path)
    require(manifest.get("schema") == "AIC_NATIVE_PREFERENCE_CODE_V1"
            and manifest.get("base_commit") == BASE_COMMIT, "Wrong release code manifest")
    files = manifest["files"]
    require(isinstance(files, dict) and files
            and set(files) == {path.name for path in HERE.glob("*.py")},
            "Implementation Python file inventory differs from the release")
    for name, sha in files.items():
        require(Path(name).name == name and digest(HERE / name) == sha,
                "Release code bytes changed: " + name)
    return dict(base_commit=BASE_COMMIT, release_manifest_ref=reference(manifest_path),
                python_files=files)


def grammar_module(manifest):
    ref = manifest["input_code"]["summary_grammar6"]
    return _bound_module("aic_preference_grammar_" + ref["sha256"][:16],
                         ref, manifest["workspace_root"])


def validate_token_path(tokenizer, suffix, answer, duration, grammar, candidates):
    """Prove the actual suffix is reachable under the unchanged generation rule."""
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    require(suffix and suffix[-1] == eos and eos not in suffix[:-1],
            "Candidate must have exactly one terminal actual EOS")
    machine = grammar.BoundedSegmentsGrammar(duration, max_segments=6, allow_empty=True)
    previous = ""
    for index, token in enumerate(suffix[:-1], 1):
        require(token in candidates, "Candidate has a token outside the actual grammar vocabulary")
        text = tokenizer.decode(suffix[:index], skip_special_tokens=False,
                                clean_up_tokenization_spaces=False)
        require(text.startswith(previous) and text != previous and machine.valid_prefix(text),
                "Candidate is not prefix-reachable under the frozen grammar")
        previous = text
    require(previous == answer and machine.complete(previous),
            "Candidate does not end at an accepted grammar state")
    parse_answer(answer, duration)


def assert_binding(document, binding):
    for key in ("config_ref", "asset_manifest_ref"):
        require(same_reference(document[key], binding[key]), "Stale artifact " + key)
        checked(document[key])
    require(document.get("code_identity") == binding["code_identity"],
            "Artifact was produced by different implementation bytes")


def validate_prepared(document, config, binding):
    assert_binding(document, binding)
    require(document.get("status") == PREPARED_STATUS, "Complete preparation is required")
    train, check = document["train_pairs"], document["check_pairs"]
    require(len(train) == 32 and len(check) == 16
            and len(document["train_sources"]) == 8 and len(document["check_sources"]) == 8,
            "Registered pair/source denominator changed")
    require(len(set(document["check_case_ids"])) == len(document["check_case_ids"])
            and 0 < len(document["check_case_ids"]) <= config["max_check_windows"],
            "Complete finite check-case list required")
    for role, pairs, count in (("train", train, 4), ("check", check, 2)):
        require(Counter(p["source_id"] for p in pairs) ==
                Counter({sid: count for sid in document[role + "_sources"]}),
                "Fixed source weight differs")
        for pair in pairs:
            require(pair["scope"] == role and pair["input_key"] == role + ":" + pair["uid"]
                    and pair["token_length_equality_checked"] is True
                    and pair["equal_native_budget"] is True
                    and pair["chosen_ids"] != pair["rejected_ids"]
                    and 0 < len(pair["chosen_ids"]) == len(pair["rejected_ids"]) <= 512
                    and len(pair["chosen_selected"]) == len(pair["rejected_selected"]) == pair["budget"]
                    and pair["chosen_selected"] != pair["rejected_selected"],
                    "Frozen matched pair contract differs")
    require(len({p["pair_id"] for p in train + check}) == 48, "Duplicate frozen pair identity")
    return document


def torch_gate(path, workspace):
    report = strict_load(path)
    require(report.get("schema") == "AIC_NATIVE_PREFERENCE_TORCH_CPU_CHECKS_V1"
            and report.get("status") == "PASS" and report.get("torch_passed") is True
            and type(report.get("torch_checks")) is int and report["torch_checks"] >= 5,
            "Actual Linux Torch CPU checks must PASS before the GPU stage")
    for key, filename in (("runtime", "runtime.py"), ("torch_checks", "torch_checks.py")):
        require(same_reference(report["code_refs"][key], reference(HERE / filename)),
                "Torch CPU check report belongs to another code version")
        checked(report["code_refs"][key], workspace)
    return reference(path)


class Journal:
    def __init__(self, path):
        self.stream = Path(path).open("x", encoding="utf-8")
        self.context = {}
        self.events = 0

    def __call__(self, kind, payload):
        row = dict(event=kind, utc=utc_now(), context=dict(self.context), **payload)
        self.stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        self.stream.flush()
        self.events += 1

    def close(self):
        self.stream.flush()
        self.stream.close()


def prepare(config, manifest, binding, directory, budget, **_):
    from .runtime import load_tokenizer, tokenize_answer
    stores = {scope: NativeInputStore(manifest, scope) for scope in ("train", "check")}
    train_store, check_store = stores["train"], stores["check"]
    train_sources = sorted(train_store.source_ids,
        key=lambda sid: stable_key(config["seed"], train_store.sources[sid]["source_sha256"]))[:8]
    check_sources = sorted(check_store.source_ids,
        key=lambda sid: stable_key(config["seed"], check_store.sources[sid]["source_sha256"]))
    require(len(train_sources) == 8 and len(check_sources) == 8
            and len(check_store.case_ids) <= config["max_check_windows"],
            "This pilot requires eight fixed fit and all eight adopted check sources")
    source_plan = dict(train_sources=train_sources, check_sources=check_sources,
        selection_rule="hash(seed,source_sha256) BEFORE any candidate utility",
        source_replacement_allowed=False, max_seed_candidates_per_source=128)
    plan_ref = save_new(directory / "source_plan.json", source_plan)
    tokenizer, grammar = load_tokenizer(manifest["model_spec"]), grammar_module(manifest)
    candidates = frozenset(grammar.ascii_token_candidates(tokenizer))
    pairs_by_scope, diagnostics, case_signatures = {}, [], {}
    for scope, chosen_sources, wanted in (("train", train_sources, 4), ("check", check_sources, 2)):
        store, pairs = stores[scope], []
        for sid in chosen_sources:
            budget.check()
            human = store.source_supervision(sid)
            require(all(type(v) is bool and v for mask in human["known_masks"] for v in mask),
                    "UNKNOWN complete-source supervision cannot become a zero target")
            clock = human["clock"]["normalized_exact_pts"]
            opportunities = [(uid, rater) for uid in store.by_source[sid]
                             for rater in range(len(human["raters"]))]
            opportunities.sort(key=lambda item: stable_key(config["seed"], human["source_sha256"], *item))
            source_diag = dict(scope=scope, source_id=sid, source_sha256=human["source_sha256"],
                available_seed_opportunities=len(opportunities), attempts=[], accepted_pairs=[],
                selected_window_counts={}, selected_reviewer_counts={})
            prefix_cache, accepted, seen = {}, [], set()
            for uid, rater in opportunities[:128]:
                if len(accepted) == wanted:
                    break
                budget.check()
                request = store.requests[uid]
                plan = request["plan"]
                start, end = plan["window_start_exact"], plan["window_end_exact"]
                attempt = dict(uid=uid, reviewer_index=rater)
                source_diag["attempts"].append(attempt)
                candidates_here = make_preference_pairs([human["raters"][rater]],
                    human["raters"], human["baseline"], clock, start, end,
                    known_masks=human["known_masks"], max_segments=6)
                if not candidates_here:
                    attempt["status"] = "NO_DISTINCT_NON_TIED_REPRESENTABLE_REFLECTION"
                    continue
                pair = candidates_here[0]
                native_key = (uid, tuple(pair["chosen_selected"]), tuple(pair["rejected_selected"]))
                if native_key in seen:
                    attempt["status"] = "DUPLICATE_PAIR"
                    continue
                seen.add(native_key)
                if uid not in prefix_cache:
                    actual, values, _clock = store.case(uid)
                    require(actual == request, "Accepted input changed during preparation")
                    # Keep only tiny prefix tensors; the store retains at most one source of pixels.
                    prefix_cache[uid] = values["input_ids"]
                    case_signatures[scope + ":" + uid] = request["input_signature"]
                    tokenize_answer(tokenizer, prefix_cache[uid], '{"segments":[]}',
                                    request_text=request["text"]["expanded_text"])
                    del values
                try:
                    chosen = tokenize_answer(tokenizer, prefix_cache[uid], pair["chosen_answer"],
                                             request_text=request["text"]["expanded_text"])
                    rejected = tokenize_answer(tokenizer, prefix_cache[uid], pair["rejected_answer"],
                                               request_text=request["text"]["expanded_text"])
                    duration = Fraction(end) - Fraction(start)
                    validate_token_path(tokenizer, chosen, pair["chosen_answer"], duration, grammar, candidates)
                    validate_token_path(tokenizer, rejected, pair["rejected_answer"], duration, grammar, candidates)
                except ValueError as exc:
                    attempt.update(status="TOKEN_OR_GRAMMAR_REJECTION", reason=str(exc))
                    continue
                if len(chosen) != len(rejected):
                    attempt.update(status="UNEQUAL_ACTUAL_SUFFIX_TOKENS",
                                   chosen_tokens=len(chosen), rejected_tokens=len(rejected))
                    continue
                pair.update(scope=scope, source_id=sid, source_sha256=human["source_sha256"],
                    uid=uid, input_key=scope + ":" + uid, original_reviewer_index=rater,
                    input_signature=request["input_signature"], request_ref=store.request_refs[uid],
                    clock_ref=store.sources[sid]["clock_ref"],
                    supervision_ref=store.sources[sid]["supervision_ref"],
                    chosen_ids=chosen, rejected_ids=rejected,
                    token_length_equality_checked=True, suffix_includes_eos=True)
                pair["pair_id"] = stable_key(scope, sid, uid, chosen, rejected)
                attempt.update(status="ACCEPTED", pair_id=pair["pair_id"])
                accepted.append(pair)
            source_diag["accepted_pairs"] = [p["pair_id"] for p in accepted]
            source_diag["selected_window_counts"] = dict(Counter(p["uid"] for p in accepted))
            source_diag["selected_reviewer_counts"] = dict(Counter(
                str(p["original_reviewer_index"]) for p in accepted))
            source_diag["rejection_counts"] = dict(Counter(a["status"] for a in source_diag["attempts"]))
            diagnostics.append(source_diag)
            save_new(directory / ("source_" + stable_key(scope, sid)[:20] + ".json"), source_diag)
            require(len(accepted) == wanted,
                    "STOP_PREPARATION: fixed source " + sid + " has " + str(len(accepted)) +
                    "/" + str(wanted) + " eligible pairs; no source replacement or recipe relaxation")
            pairs.extend(accepted)
            store.close()
        pairs_by_scope[scope] = pairs
    # Check every adopted check input now, even when it did not seed a pair.
    for uid in check_store.case_ids:
        budget.check()
        request, values, _clock = check_store.case(uid)
        case_signatures["check:" + uid] = request["input_signature"]
        tokenize_answer(tokenizer, values, '{"segments":[]}',
                        request_text=request["text"]["expanded_text"])
    for store in stores.values():
        store.close()
    diagnostic_ref = save_new(directory / "pair_diagnostics.json", diagnostics)
    result = dict(schema="AIC_NATIVE_PREFERENCE_PREPARED_V1", status=PREPARED_STATUS,
        **binding, source_plan_ref=plan_ref, train_sources=train_sources, check_sources=check_sources,
        train_pairs=pairs_by_scope["train"], check_pairs=pairs_by_scope["check"],
        check_case_ids=list(check_store.case_ids), case_signatures=case_signatures,
        pair_diagnostics_ref=diagnostic_ref, generation_model_calls=0, optimizer_updates=0,
        official_sources_used_for_supervision=False, new_human_annotations_created=False,
        derived_preference_labels_created=True,
        historical_exposure=True, budget=budget.snapshot())
    validate_prepared(result, config, binding)
    return save_new(directory / "prepared.json", result)


def case_output(record, request, clock, *, eos):
    require(record.get("status") == "ACCEPTED" and record.get("actual_model_call") is True,
            "Execution failure or unexecuted request is not a legal empty prediction")
    require(record["uid"] == request["uid"] and record["source_id"] == request["sid"]
            and record["input_signature"] == request["input_signature"],
            "Actual generation/request identity mismatch")
    ids = record.get("ids")
    require(isinstance(ids, list) and 0 < len(ids) <= 512 and all(type(i) is int and i >= 0 for i in ids)
            and record.get("eos") is True and record.get("eos_token_id") == eos
            and ids[-1] == eos and eos not in ids[:-1], "Actual successful EOS termination required")
    start, end = request["plan"]["window_start_exact"], request["plan"]["window_end_exact"]
    selected = native_selection(parse_answer(record["text"], Fraction(end) - Fraction(start)),
                                clock["normalized_exact_pts"], start, end)
    require(record["selected_ordinals"] == sorted(selected)
            and record.get("legal_empty") is (len(selected) == 0),
            "Stored selection differs from independently parsed exact native output")
    return selected


def generate_cases(runtime, store, case_ids, role, directory, journal, budget, grammar, candidates):
    require(set(case_ids) == set(store.case_ids) and len(case_ids) == len(store.case_ids),
            "Free generation must include every complete-source check/production window")
    refs = []
    for number, uid in enumerate(case_ids):
        budget.check()
        journal.context = dict(action="free_generation", role=role, uid=uid)
        request, values, clock = store.case(uid)
        constraint = grammar.PrefixConstraint(runtime.tokenizer, values["input_ids"].shape[1],
            Fraction(request["plan"]["window_end_exact"]) -
                  Fraction(request["plan"]["window_start_exact"]),
            max_segments=6, candidate_token_ids=candidates,
            eos_token_ids=[runtime.eos], allow_empty=True)
        path = directory / (role + "_" + str(number).zfill(4) + ".json")
        row = dict(role=role, uid=uid, source_id=request["sid"], request_ref=store.request_refs[uid],
                   clock_ref=store.sources[request["sid"]]["clock_ref"])
        try:
            generated = runtime.generate(values, constraint)
            start, end = request["plan"]["window_start_exact"], request["plan"]["window_end_exact"]
            chosen = native_selection(parse_answer(generated["text"], Fraction(end) - Fraction(start)),
                                      clock["normalized_exact_pts"], start, end)
            row.update(**generated, status="ACCEPTED", selected_ordinals=sorted(chosen),
                       legal_empty=not chosen)
            case_output(row, request, clock, eos=runtime.eos)
        except BaseException as exc:
            row.update(status="FAILED", error_type=type(exc).__name__, error=str(exc),
                       failed_output_to_empty=False)
            save_new(path, row)
            raise
        refs.append(save_new(path, row))
    store.close()
    return refs


def read_generation(refs, store, *, eos, role):
    require(isinstance(refs, list) and len(refs) == len(store.case_ids), "Incomplete generation receipts")
    seen, unions, empty_windows = set(), {sid: set() for sid in store.source_ids}, 0
    for ref in refs:
        row = strict_load(checked(ref, store.workspace))
        uid = row["uid"]
        require(uid in store.requests and uid not in seen and row.get("role") == role,
                "Duplicate, foreign or wrong-role generation receipt")
        require(same_reference(row["request_ref"], store.request_refs[uid])
                and same_reference(row["clock_ref"], store.sources[row["source_id"]]["clock_ref"]),
                "Generation receipt is bound to another input/clock")
        request = store.requests[uid]
        selected = case_output(row, request, store.clocks[request["sid"]], eos=eos)
        seen.add(uid)
        unions[request["sid"]].update(selected)
        empty_windows += int(not selected)
    require(seen == set(store.case_ids), "Missing windows are not empty predictions")
    return ({sid: dict(status="ACCEPTED", selected_ordinals=sorted(selected))
             for sid, selected in unions.items()}, empty_windows)


def mean_metrics(selected, raters):
    require(isinstance(raters, list) and raters, "Complete source reviewers required")
    rows = []
    for truth in raters:
        common = len(selected & truth)
        both_empty = not selected and not truth
        rows.append(dict(f1=(2 * common / (len(selected) + len(truth)) if selected or truth else 1.0),
            precision=(common / len(selected) if selected else float(both_empty)),
            recall=(common / len(truth) if truth else float(both_empty))))
    return {key: sum(row[key] for row in rows) / len(rows) for key in ("f1", "precision", "recall")}


def preference_accuracy(rows, source_ids):
    """Raw model answer ordering; NOT sign of the DPO reference-adjusted margin."""
    grouped = {sid: [] for sid in source_ids}
    for row in rows:
        require(row["source_id"] in grouped, "Foreign preference evaluation source")
        margin = row["chosen_logprob"] - row["rejected_logprob"]
        require(all(type(row[key]) in (int, float) and math.isfinite(row[key])
                    for key in ("chosen_logprob", "rejected_logprob")), "Nonfinite candidate log probability")
        grouped[row["source_id"]].append(1.0 if margin > 0 else 0.0 if margin < 0 else 0.5)
    require(all(len(values) == 2 for values in grouped.values()), "Exactly two held-out pairs per source")
    scores = {sid: sum(values) / len(values) for sid, values in grouped.items()}
    return dict(source_macro=sum(scores.values()) / len(scores), per_source=scores,
                rule="raw chosen logp > raw rejected logp; exact tie=0.5")


def assess_mechanism(supervision, reference_selections, policy_selections, reference_pairs, policy_pairs):
    source_ids = list(supervision)
    successful_source_selections(reference_selections, source_ids)
    successful_source_selections(policy_selections, source_ids)
    pair_before = preference_accuracy(reference_pairs, source_ids)
    pair_after = preference_accuracy(policy_pairs, source_ids)
    rows, changed, collapsed = [], 0, []
    for sid, human in supervision.items():
        require(all(type(v) is bool and v for mask in human["known_masks"] for v in mask),
                "Incomplete references cannot supply a promotion metric")
        ref, policy, best = (set(reference_selections[sid]["selected_ordinals"]),
                            set(policy_selections[sid]["selected_ordinals"]), human["baseline"])
        changed += len(ref ^ policy)
        row = dict(source_id=sid, reference=mean_metrics(ref, human["raters"]),
            policy=mean_metrics(policy, human["raters"]), protected_proxy=mean_metrics(best, human["raters"]),
            reference_frames=len(ref), policy_frames=len(policy), protected_proxy_frames=len(best),
            added_vs_reference=len(policy-ref), deleted_vs_reference=len(ref-policy),
            added_vs_protected_proxy=len(policy-best), deleted_vs_protected_proxy=len(best-policy),
            reference_empty=not ref, policy_empty=not policy, protected_proxy_empty=not best)
        row["f1_delta_vs_reference"] = row["policy"]["f1"] - row["reference"]["f1"]
        row["f1_delta_vs_protected_proxy"] = row["policy"]["f1"] - row["protected_proxy"]["f1"]
        if not policy and ref and best and any(human["raters"]):
            collapsed.append(sid)
        rows.append(row)
    macro = {role: {metric: sum(row[role][metric] for row in rows)/len(rows)
                    for metric in ("f1", "precision", "recall")}
             for role in ("reference", "policy", "protected_proxy")}
    stops = []
    if not changed:
        stops.append("NO_CHANGE_IN_ACTUAL_GENERATED_SELECTION")
    if pair_after["source_macro"] <= pair_before["source_macro"]:
        stops.append("RAW_HELDOUT_PAIR_ORDERING_DID_NOT_IMPROVE")
    if macro["policy"]["f1"] <= macro["reference"]["f1"]:
        stops.append("FULL_SOURCE_GENERATION_DID_NOT_BEAT_ORIGINAL_TIME")
    if macro["policy"]["f1"] <= macro["protected_proxy"]["f1"]:
        stops.append("FULL_SOURCE_GENERATION_DID_NOT_BEAT_EXPOSED_40_47_PROXY")
    if collapsed:
        stops.append("NEW_FALSE_EMPTY_COMPLETE_SOURCE")
    return dict(status="STOP_MECHANISM" if stops else "ELIGIBLE_FOR_EXECUTION_REVIEW",
        stop_reasons=stops, macro=macro, per_source=rows,
        pair_accuracy=dict(reference=pair_before, policy=pair_after),
        changed_native_frames_vs_reference=changed, newly_false_empty_sources=collapsed,
        automatic_production=False, official_score="NOT_MEASURED",
        spatial_joint_utility="UNKNOWN_NO_BOUND_EXTERNAL_FROZEN_FIELD",
        historical_exposure=True, statistical_significance_claim=False)


def pilot(config, manifest, binding, directory, budget, *, args):
    from .runtime import QwenPreferenceRuntime
    prepared = validate_prepared(strict_load(args.prepared), config, binding)
    prepared_ref = reference(args.prepared)
    checks_ref = torch_gate(args.torch_checks, manifest["workspace_root"])
    historical_reference = manifest.get("reference_generation_origin") is not None
    require(historical_reference or manifest["model_spec"].get("synthetic_unit_test_only") is True,
            "Real deployment requires explicit historical reference generation adoption")
    stores = {scope: NativeInputStore(manifest, scope) for scope in ("train", "check")}
    require(set(prepared["check_case_ids"]) == set(stores["check"].case_ids), "Accepted check set changed")
    journal = Journal(directory / "events.jsonl")
    runtime = QwenPreferenceRuntime(manifest["model_spec"], budget.check, journal, seed=config["seed"])
    def get_input(key):
        scope, uid = key.split(":", 1)
        require(scope in stores, "Official data cannot enter training/reference interface")
        for other, store in stores.items():
            if other != scope:
                store.close()
        request, values, _clock = stores[scope].case(uid)
        require(request["input_signature"] == prepared["case_signatures"][key], "Prepared input changed")
        return values
    try:
        runtime.load()
        all_pairs = prepared["train_pairs"] + prepared["check_pairs"]
        for pair in all_pairs:
            values = get_input(pair["input_key"])
            for role in ("chosen", "rejected"):
                require(runtime.tokenize_answer(values, pair[role + "_answer"]) == pair[role + "_ids"],
                        "Frozen candidate tokenization changed after model load")
        journal.context = dict(action="fixed_reference_scoring")
        cache = runtime.cache_reference(all_pairs, get_input)
        cache_ref = save_new(directory / "fixed_reference.json", cache)
        grammar = grammar_module(manifest)
        candidates = grammar.ascii_token_candidates(runtime.tokenizer)
        if historical_reference:
            from .reference_adoption import adopt_reference
            before = adopt_reference(runtime, stores["check"], prepared["check_case_ids"],
                manifest, directory, journal, budget, grammar, candidates)
        else:
            before = generate_cases(runtime, stores["check"], prepared["check_case_ids"], "reference",
                                    directory, journal, budget, grammar, candidates)
        journal.context = dict(action="fixed_training")
        training = runtime.train_pairs(prepared["train_pairs"], get_input, cache,
            updates=16, grad_accum=2, lr=config["learning_rate"], beta=config["beta"])
        training_ref = save_new(directory / "training.json", training)
        final = runtime.save_policy((directory / "final_adapter").resolve())
        final_identity_ref = save_new(directory / "final_adapter_identity.json", final)
        runtime.load_policy(final["directory"], final["adapter_weights"]["sha256"])
        require(same_reference(final["adapter_config"],
                              reference(Path(final["directory"]) / "adapter_config.json")),
                "Final adapter config changed across save/reload")
        before_pairs, after_pairs = [], []
        for pair in prepared["check_pairs"]:
            budget.check()
            journal.context = dict(action="heldout_pair_score", pair_id=pair["pair_id"])
            values = get_input(pair["input_key"])
            original = cache["entries"][pair["pair_id"]]
            base_row = dict(source_id=pair["source_id"], pair_id=pair["pair_id"])
            before_pairs.append(dict(**base_row, chosen_logprob=original["chosen_logprob"],
                                     rejected_logprob=original["rejected_logprob"]))
            after_pairs.append(dict(**base_row,
                chosen_logprob=runtime.score(values, pair["chosen_ids"]),
                rejected_logprob=runtime.score(values, pair["rejected_ids"])))
        scores_ref = save_new(directory / "heldout_pair_scores.json",
                              dict(reference=before_pairs, policy=after_pairs))
        after = generate_cases(runtime, stores["check"], prepared["check_case_ids"], "policy",
                               directory, journal, budget, grammar, candidates)
        outputs_ref = save_new(directory / "generation_manifest.json", dict(reference=before, policy=after))
        verification_ref = save_new(directory / "final_verification.json", runtime.verify_final())
        expected_new_generations = (1 if historical_reference else 2) * len(prepared["check_case_ids"])
        require(runtime.counts["generation_calls"] == runtime.counts["generations_completed"] ==
                expected_new_generations and runtime.counts["optimizer_steps"] == 16
                and runtime.counts["backward_calls"] == runtime.counts["backwards_completed"] == 64
                and runtime.counts["sequence_score_calls"] == runtime.counts["sequence_scores_completed"] == 258
                and runtime.counts["top_level_forward_calls"] == budget.forward_count,
                "Actual pilot work is incomplete")
        budget.check(force_disk=True)
        journal.close()
        result = dict(schema="AIC_NATIVE_PREFERENCE_PILOT_V1", status=PILOT_STATUS,
            **binding, prepared_ref=prepared_ref, torch_checks_ref=checks_ref,
            reference_cache_ref=cache_ref, training_ref=training_ref,
            final_adapter_ref=final["adapter_weights"], final_adapter_config_ref=final["adapter_config"],
            final_adapter_identity_ref=final_identity_ref, heldout_pair_scores_ref=scores_ref,
            generation_manifest_ref=outputs_ref, final_verification_ref=verification_ref,
            event_journal_ref=reference(directory / "events.jsonl"), counts=runtime.counts,
            historical_reference_generations_adopted=len(before) if historical_reference else 0,
            new_reference_generation_calls=0 if historical_reference else len(before),
            runtime=runtime.identity(), budget=budget.snapshot(),
            peak_cuda_allocated_bytes=runtime.torch.cuda.max_memory_allocated(),
            peak_cuda_reserved_bytes=runtime.torch.cuda.max_memory_reserved(),
            no_automatic_production=True, official_score="NOT_MEASURED")
        return save_new(directory / "completion.json", result)
    finally:
        if not journal.stream.closed:
            journal.close()
        for store in stores.values():
            store.close()


def load_pilot(path, prepared_ref, binding):
    result = strict_load(path)
    assert_binding(result, binding)
    require(result.get("status") == PILOT_STATUS and same_reference(result["prepared_ref"], prepared_ref),
            "Complete matching pilot required; partial/failed work cannot be promoted")
    checked(result["prepared_ref"])
    for name in ("final_adapter_ref", "final_adapter_config_ref", "torch_checks_ref",
                 "final_adapter_identity_ref",
                 "final_verification_ref", "training_ref", "reference_cache_ref",
                 "generation_manifest_ref", "heldout_pair_scores_ref", "event_journal_ref"):
        checked(result[name])
    final_identity = strict_load(checked(result["final_adapter_identity_ref"]))
    require(final_identity.get("runtime") == result["runtime"]
            and same_reference(final_identity["adapter_weights"], result["final_adapter_ref"])
            and same_reference(final_identity["adapter_config"], result["final_adapter_config_ref"]),
            "Final checkpoint identity differs from the actual reviewed pilot")
    require(result["counts"]["optimizer_steps"] == 16 and result["counts"]["backwards_completed"] == 64,
            "Pilot receipt lacks the registered completed updates")
    return result


def review(config, manifest, binding, directory, budget, *, args):
    prepared = validate_prepared(strict_load(args.prepared), config, binding)
    completed = load_pilot(args.pilot, reference(args.prepared), binding)
    store = NativeInputStore(manifest, "check")
    require(set(prepared["check_case_ids"]) == set(store.case_ids), "Review check set changed")
    outputs = strict_load(checked(completed["generation_manifest_ref"], store.workspace))
    require(set(outputs) == set(ROLES), "Both matched actual-generation roles required")
    selections, empties = {}, {}
    for role in ROLES:
        selections[role], empties[role] = read_generation(outputs[role], store,
            eos=completed["runtime"]["eos_token_id"], role=role)
    scores = strict_load(checked(completed["heldout_pair_scores_ref"], store.workspace))
    expected = {pair["pair_id"]: pair["source_id"] for pair in prepared["check_pairs"]}
    require(set(scores) == set(ROLES), "Both candidate-score roles required")
    for rows in scores.values():
        require(len(rows) == 16 and {row["pair_id"]: row["source_id"] for row in rows} == expected,
                "Heldout pair receipts differ from the frozen candidate set")
    supervision = {sid: store.source_supervision(sid) for sid in prepared["check_sources"]}
    report = assess_mechanism(supervision, selections["reference"], selections["policy"],
                              scores["reference"], scores["policy"])
    report.update(schema="AIC_NATIVE_PREFERENCE_REVIEW_V1", **binding,
        prepared_ref=reference(args.prepared), pilot_completion_ref=reference(args.pilot),
        final_adapter_ref=completed["final_adapter_ref"],
        selection_refs={role: save_new(directory / (role + "_source_selections.json"),
                       dict(schema="AIC_NATIVE_PREFERENCE_SELECTION_V1", sources=selections[role]))
                       for role in ROLES},
        legal_empty_windows=empties, completed_model_calls=completed["counts"],
        instruction="Execution agent must review this exact result; this file is not an admission",
        production_field_exclusion_policy="STOP_IF_ANY_RAW_SELECTION_HAS_NO_FROZEN_FIELD",
        budget=budget.snapshot())
    return save_new(directory / "review.json", report)


def require_production_assets(original, production):
    require(original["workspace_root"] == production["workspace_root"], "Production workspace differs")
    for key in ("model_spec", "model_files", "input_code", "code_refs", "protected_baseline_ref",
                "inherited_baseline_head_ref", "actual_pipeline_parameters", "rights_declaration_ref",
                "source_registration_ref"):
        require(original[key] == production[key], "Production changed a pilot dependency: " + key)
    require(all(original["scopes"][scope] == production["scopes"][scope] for scope in ("train", "check")),
            "Production changed previously evaluated external assets")
    require("production" in production["scopes"] and production.get("renderer"),
            "Explicit accepted formal inputs and renderer assets required")


def production(config, manifest, binding, directory, budget, *, args):
    from .runtime import QwenPreferenceRuntime
    prepared = validate_prepared(strict_load(args.prepared), config, binding)
    completed = load_pilot(args.pilot, reference(args.prepared), binding)
    reviewed = strict_load(args.review)
    assert_binding(reviewed, binding)
    require(reviewed.get("schema") == "AIC_NATIVE_PREFERENCE_REVIEW_V1"
            and reviewed.get("status") == "ELIGIBLE_FOR_EXECUTION_REVIEW"
            and same_reference(reviewed["pilot_completion_ref"], reference(args.pilot))
            and same_reference(reviewed["prepared_ref"], reference(args.prepared))
            and same_reference(reviewed["final_adapter_ref"], completed["final_adapter_ref"]),
            "Only this exact completed directionally successful pilot can enter execution review")
    formal = asset_api.load_assets(args.production_assets or args.assets)
    require_production_assets(manifest, formal)
    formal_ref = formal["_asset_manifest_ref"]
    expected = dict(config_ref=binding["config_ref"], asset_manifest_ref=binding["asset_manifest_ref"],
        production_assets_ref=formal_ref, prepared_ref=reference(args.prepared),
        pilot_completion_ref=reference(args.pilot), review_ref=reference(args.review),
        final_adapter_ref=completed["final_adapter_ref"])
    validate_admission(strict_load(args.admission), "production", expected, root=manifest["workspace_root"])
    checks_ref = torch_gate(args.torch_checks, manifest["workspace_root"])
    asset_api.preflight_assets(formal, "production")
    store = NativeInputStore(formal, "production")
    require(0 < len(store.source_ids) <= config["max_production_sources"]
            and 0 < len(store.case_ids) <= config["max_production_windows"],
            "Formal work exceeds the explicitly finite production budget")
    journal = Journal(directory / "events.jsonl")
    runtime = QwenPreferenceRuntime(formal["model_spec"], budget.check, journal, seed=config["seed"])
    try:
        runtime.load()
        require(runtime.identity() == completed["runtime"],
                "Actual production runtime differs from the reviewed pilot environment")
        weights = checked(completed["final_adapter_ref"], store.workspace)
        require(checked(completed["final_adapter_config_ref"], store.workspace).parent == weights.parent,
                "Final policy files do not form the admitted directory")
        runtime.load_policy(weights.parent, completed["final_adapter_ref"]["sha256"])
        grammar = grammar_module(formal)
        refs = generate_cases(runtime, store, list(store.case_ids), "policy", directory,
            journal, budget, grammar, grammar.ascii_token_candidates(runtime.tokenizer))
        rows, empty_windows = read_generation(refs, store, eos=runtime.eos, role="policy")
        successful_source_selections(rows, store.source_ids)
        selection_ref = save_new(directory / "selection.json",
            dict(schema="AIC_NATIVE_PREFERENCE_SELECTION_V1", sources=rows))
        generation_ref = save_new(directory / "generation_manifest.json", dict(policy=refs))
        verification_ref = save_new(directory / "final_verification.json", runtime.verify_final())
        budget.check(force_disk=True)
        require(runtime.counts["generation_calls"] == runtime.counts["generations_completed"] ==
                len(store.case_ids) and runtime.counts["optimizer_steps"] == 0
                and runtime.counts["backward_calls"] == 0 and runtime.counts["sequence_score_calls"] == 0
                and runtime.counts["top_level_forward_calls"] == budget.forward_count,
                "Formal execution incomplete or illegally trained")
        journal.close()
        result = dict(schema="AIC_NATIVE_PREFERENCE_PRODUCTION_V1", status=PRODUCTION_STATUS,
            **binding, production_assets_ref=formal_ref, selection_ref=selection_ref,
            pilot_completion_ref=reference(args.pilot), review_ref=reference(args.review),
            final_adapter_ref=completed["final_adapter_ref"],
            final_adapter_config_ref=completed["final_adapter_config_ref"],
            admission_ref=reference(args.admission), torch_checks_ref=checks_ref,
            source_count=len(store.source_ids), window_count=len(store.case_ids),
            generation_manifest_ref=generation_ref, final_verification_ref=verification_ref,
            event_journal_ref=reference(directory / "events.jsonl"), legal_empty_windows=empty_windows,
            counts=runtime.counts, runtime=runtime.identity(), budget=budget.snapshot(),
            official_labels_or_pseudolabels_used=False, automatically_packaged=False)
        return save_new(directory / "completion.json", result)
    finally:
        if not journal.stream.closed:
            journal.close()
        store.close()


def package(config, manifest, binding, directory, budget, *, args):
    from .render import render_package
    completed = strict_load(args.production)
    assert_binding(completed, binding)
    require(completed.get("status") == PRODUCTION_STATUS, "Complete actual formal inference required")
    formal = asset_api.load_assets(args.production_assets or args.assets)
    require_production_assets(manifest, formal)
    require(same_reference(completed["production_assets_ref"], formal["_asset_manifest_ref"]),
            "Renderer assets changed after production")
    selections = strict_load(checked(completed["selection_ref"], formal["workspace_root"]))
    require(selections.get("schema") == "AIC_NATIVE_PREFERENCE_SELECTION_V1",
            "Explicit final source-selection schema required")
    successful_source_selections(selections["sources"],
        [source["id"] for source in formal["scopes"]["production"]["sources"]])
    budget.check()
    result = render_package(formal, selections["sources"], directory / "rendered",
        reference(args.admission), config_ref=binding["config_ref"],
        production_completion_ref=reference(args.production),
        python_executable=formal["runtime_python"])
    budget.check(force_disk=True)
    return save_new(directory / "completion.json", dict(schema="AIC_NATIVE_PREFERENCE_PACKAGE_RUN_V1",
        **binding, production_completion_ref=reference(args.production),
        result=result, budget=budget.snapshot(), automatic_submission=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True,
        choices=("preflight", "prepare", "pilot", "review", "production", "package"))
    parser.add_argument("--config", required=True)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--output", help="New explicit preflight report path only")
    parser.add_argument("--prepared")
    parser.add_argument("--pilot")
    parser.add_argument("--review")
    parser.add_argument("--torch-checks")
    parser.add_argument("--production-assets")
    parser.add_argument("--production")
    parser.add_argument("--admission")
    args = parser.parse_args(argv)
    required = dict(preflight=("output",), prepare=(), pilot=("prepared", "torch_checks"),
        review=("prepared", "pilot"),
        production=("prepared", "pilot", "review", "torch_checks", "admission"),
        package=("production", "admission"))
    for name in required[args.stage]:
        parser.error("--" + name.replace("_", "-") + " is required for " + args.stage) if not getattr(args, name) else None
    config = validate_config(strict_load(args.config))
    manifest = asset_api.load_assets(args.assets)
    workspace, root = Path(manifest["workspace_root"]).resolve(strict=True), Path(config["run_root"]).resolve()
    require(root.is_relative_to(workspace) and root != workspace and root.name == config["run_id"],
            "New run_root must be a named child of the registered Linux workspace")
    protected = Path(manifest["protected_baseline_ref"]["path"]).resolve().parent.parent
    require(not root.is_relative_to(protected), "Run output must not enter protected40.47 artifacts")
    for path in (manifest["model_spec"]["model_dir"],
                 Path(manifest["model_spec"]["adapter_weights"]["path"]).parent):
        require(not root.is_relative_to(Path(path).resolve()), "Output must not enter original model/adapter assets")
    binding = dict(config_ref=reference(args.config), asset_manifest_ref=reference(args.assets),
                   code_identity=code_identity())
    if args.stage == "preflight":
        output = Path(args.output).resolve()
        require(output.is_relative_to(root), "Preflight output must be inside this new run_root")
        output.parent.mkdir(parents=True, exist_ok=True)
        report = asset_api.preflight_assets(manifest)
        print(json.dumps(save_new(output, dict(**report, **binding)), ensure_ascii=False))
        return 0
    directory = claim_stage(root, args.stage, binding)
    seconds = config["max_pilot_seconds"] if args.stage == "pilot" else (
              config["max_production_seconds"] if args.stage == "production" else config["max_prepare_seconds"])
    forwards = config["max_production_top_level_forwards"] if args.stage == "production" else config["max_top_level_forwards"]
    budget = StageBudget(root, seconds, config["max_output_bytes"], forwards)
    try:
        # This verifies all local inventory bytes without loading a model.  Its
        # elapsed time is included in the finite claimed stage, not hidden setup.
        preflight = asset_api.preflight_assets(manifest)
        save_new(directory / "asset_preflight.json", preflight)
        budget.check(force_disk=True)
        result = globals()[args.stage](config, manifest, binding, directory, budget, args=args)
        budget.check(force_disk=True)
        print(json.dumps(dict(stage=args.stage, artifact_ref=result), ensure_ascii=False))
        if args.stage == "review" and strict_load(result["path"])["status"] != "ELIGIBLE_FOR_EXECUTION_REVIEW":
            return 3
        return 0
    except BaseException as exc:
        save_new(directory / "failure.json", dict(status="FAILED", stage=args.stage,
            error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc(),
            utc=utc_now(), **binding, budget=budget.snapshot(),
            automatic_retry=False, failed_output_to_empty=False))
        print(json.dumps(dict(status="FAILED", stage=args.stage, error=str(exc),
                              failure_path=str(directory / "failure.json")), ensure_ascii=False), file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == "__main__":
    raise SystemExit(main())
