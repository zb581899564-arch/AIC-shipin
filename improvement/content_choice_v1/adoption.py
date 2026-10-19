"""Explicit adoption of successful original TIME answers, never latest lookup."""
from __future__ import annotations

from fractions import Fraction

from improvement.native_preference_v1.reference_adoption import adopt_reference
from improvement.native_preference_v1.run import validate_token_path
from improvement.native_preference_v1.preference import native_selection, parse_answer
from .contracts import checked, reference, require, same_reference, save_new, strict_load


def validate_answer(runtime, request, clock, text, ids, grammar, vocabulary):
    require(isinstance(ids, list) and ids and ids[-1] == runtime.eos and runtime.eos not in ids[:-1],
            "An actual complete answer with terminal EOS is required")
    require(runtime.tokenizer.decode(ids[:-1], skip_special_tokens=False,
                clean_up_tokenization_spaces=False) == text, "Actual token/text identity differs")
    start, end = request["plan"]["window_start_exact"], request["plan"]["window_end_exact"]
    duration = Fraction(end) - Fraction(start)
    validate_token_path(runtime.tokenizer, ids, text, duration, grammar, vocabulary)
    return sorted(native_selection(parse_answer(text, duration), clock["normalized_exact_pts"], start, end))


def adopt_check(runtime, store, manifest, directory, journal, budget, grammar, vocabulary):
    out = directory / "adopted_original_time"
    out.mkdir(exist_ok=False)
    refs = adopt_reference(runtime, store, list(store.case_ids), manifest, out,
                           journal, budget, grammar, vocabulary)
    result = {strict_load(checked(ref, store.workspace))["uid"]: ref for ref in refs}
    require(set(result) == set(store.case_ids), "Missing historical check controls")
    return result


def adopt_formal(runtime, store, manifest, qa_path, directory, journal, budget, grammar, vocabulary):
    """Bind the successful v41 TIME522, including raw, first QA and natural exit.

    BASE answers and the five stopped set-fusion outputs are not candidates.
    Following references inside this explicit first-QA file is not discovery of
    another version or a new production authorization.
    """
    require(store.scope == "production" and len(store.source_ids) == 426 and len(store.case_ids) == 522,
            "Exact accepted426/522 formal store required")
    workspace = store.workspace
    qa_ref = reference(qa_path)
    qa = strict_load(checked(qa_ref, workspace))
    require(qa.get("status") == "PASS_BOTH_ROLES_FIRST_INDEPENDENT_TOKEN_GRAMMAR_NATIVE_QA_41"
            and qa.get("unique_ledger_equal") is True and qa.get("invalid_outputs") == 0
            and qa.get("sources") == 426 and qa.get("windows_per_role") == 522
            and qa.get("total_outputs") == 1044 and set(qa["roles"]) == {"TIME", "BASE"},
            "Successful unchanged formal first-QA evidence required")
    resource = strict_load(checked(qa["resource_ref"], workspace))
    require(resource.get("status") == "completed" and resource.get("exit_code") == 0,
            "Adopt only the naturally completed formal job")
    reg = strict_load(checked(qa["registration_ref"], workspace))
    top = strict_load(checked(qa["completion_ref"], workspace))
    weights = manifest["model_spec"]["adapter_weights"]
    acceptance = manifest["scopes"]["production"]["input_acceptance_ref"]
    require(top.get("status") == "PASS_BOTH_ORIGINAL_TIME_BASE_FORMAL_GENERATIONS_41"
            and top.get("optimizer_updates") == 0 and top.get("labels_read") is False
            and top.get("sources") == 426 and top.get("windows_per_role") == 522
            and top.get("roles") == ["TIME", "BASE"]
            and same_reference(top["original_TIME_ref"], weights)
            and same_reference(top["registration_ref"], qa["registration_ref"])
            and same_reference(reg["first_input_acceptance_ref"], acceptance)
            and same_reference(reg["original_TIME_ref"], weights),
            "Adopted formal model/input/role identity differs")
    cfg = strict_load(checked(reg["model_config_ref"], workspace))
    require(cfg["expected_base_sha256"] == manifest["model_spec"]["base_sha256"],
            "Adopted formal BASE differs")
    role = qa["roles"]["TIME"]
    complete_ref = role["completion_ref"]
    complete = strict_load(checked(complete_ref, workspace))
    role_refs = top["role_completion_refs"]
    if isinstance(role_refs, dict):
        role_refs = list(role_refs.values())
    require(any(same_reference(ref, complete_ref) for ref in role_refs), "TIME completion absent from formal job")
    require(complete.get("status") == "PASS_ALL426_FORMAL_SUMMARY_GENERATIONS_41"
            and complete.get("model_role") == "TIME" and complete.get("sources") == 426
            and complete.get("windows") == 522 and complete.get("optimizer_updates") == 0
            and complete.get("labels_read") is False and complete.get("role_terminal") == "completed"
            and complete.get("role_exit_code") == 0 and complete.get("adapter_disabled_actual_forward") is False
            and all(complete.get(key) is True for key in ("old_TIME_unchanged", "all_parameter_flags_unchanged",
                        "original_TIME_exact_FP32_bits_unchanged", "TIME_flags_restored"))
            and complete["base_fingerprint"] == runtime.base_before
            and same_reference(complete["model_weights_ref"], weights)
            and same_reference(complete["input_acceptance_ref"], acceptance)
            and same_reference(complete["registration_ref"], qa["registration_ref"])
            and complete["outputs"] == role["outputs"],
            "Formal originalTIME did not complete with the same frozen parameters")
    restoration = strict_load(checked(complete["TIME_frozen_flag_restoration_ref"], workspace))
    require(restoration.get("status") == "PASS_ORIGINAL_TIME_ROLE_AND_FROZEN_FLAGS_RESTORED_41"
            and restoration.get("restored_trainable_parameters") == 0
            and restoration.get("restored_disabled_layers") == 0
            and restoration.get("all144_TIME_layers_enabled") is True,
            "Historical formal adapter role was not restored")
    details = {row["uid"]: row for row in role["details"]}
    require(len(complete["outputs"]) == len(details) == len(role["details"]) == 522
            and set(details) == set(store.case_ids), "All522 historical raw controls are required")
    directory = directory / "adopted_original_time"
    directory.mkdir(exist_ok=False)
    outputs = {}
    for index, old_ref in enumerate(complete["outputs"]):
        budget.check()
        old = strict_load(checked(old_ref, workspace))
        uid = old["uid"]
        require(uid in store.requests and uid not in outputs, "Duplicate or foreign formal control")
        request = store.requests[uid]
        require(old["sid"] == request["sid"] and old["model_role"] == "TIME"
                and old.get("adapter_disabled_actual_forward") is False
                and old.get("forward_role_flag_checks", 0) > 0
                and same_reference(old["request_ref"], store.request_refs[uid])
                and same_reference(old["model_weights_ref"], weights)
                and same_reference(details[uid]["output_ref"], old_ref),
                "Historical formal answer uses another input/model")
        raw = strict_load(checked(old["raw_token_ref"], workspace))
        require(all(raw[k] == old[k] for k in
                    ("uid", "sid", "request_ref", "generated_ids", "model_role", "model_weights_ref"))
                and raw["actual_prefix_signature"] == raw["expected_prefix_signature"]
                    == {"input_ids": request["input_signature"]["input_ids"]},
                "Formal retained raw token/prefix identity changed")
        chosen = validate_answer(runtime, request, store.clocks[request["sid"]],
                                 old["raw_text"], old["generated_ids"], grammar, vocabulary)
        qa_chosen = sorted({i for lo, hi in details[uid]["native_ranges"] for i in range(lo, hi)})
        require(chosen == qa_chosen, "Reparsed formal native selection differs from first QA")
        record = dict(status="ACCEPTED", uid=uid, source_id=request["sid"],
            request_ref=store.request_refs[uid], clock_ref=store.sources[request["sid"]]["clock_ref"],
            input_signature=request["input_signature"], text=old["raw_text"], ids=old["generated_ids"],
            selected_ordinals=chosen, legal_empty=not chosen,
            historical_output_ref=old_ref, historical_raw_token_ref=old["raw_token_ref"],
            historical_completion_ref=complete_ref, historical_first_output_qa_ref=qa_ref,
            adopted_historical_model_call=True, new_model_calls=0, actual_model_call=False,
            labels_read=False)
        outputs[uid] = save_new(directory / (str(index).zfill(4) + ".json"), record)
        journal("formal_control_adopted", dict(uid=uid, historical_ref=old_ref, new_model_calls=0))
    require(set(outputs) == set(store.case_ids), "Missing formal controls cannot be regenerated silently")
    return outputs
