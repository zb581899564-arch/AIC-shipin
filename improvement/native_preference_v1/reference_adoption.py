"""First new-purpose adoption of the existing, accepted INIT_TIME answers.

This checks retained bytes, tokens and native membership without input tensor
loading or another model call. Historical QA remains a historical receipt.
"""
from fractions import Fraction

from .contracts import checked, require, same_reference, save_new, strict_load
from .preference import native_selection, parse_answer


def adopt_reference(runtime, store, case_ids, manifest, directory, journal, budget, grammar, candidates):
    from .run import case_output, validate_token_path

    origin = manifest["reference_generation_origin"]
    root = store.workspace
    completion = strict_load(checked(origin["completion_ref"], root))
    qa = strict_load(checked(origin["first_output_qa_ref"], root))
    expected = set(store.case_ids)
    require(len(expected) == len(case_ids) == 43 and set(case_ids) == expected
            and len(store.source_ids) == 8, "Historical adoption requires every accepted43 check window/8 sources")
    weights = manifest["model_spec"]["adapter_weights"]
    checked(weights, root)
    require(completion.get("status") == "PASS_ALL43_MATCHED_SUMMARY_GENERATIONS"
            and completion.get("model_role") == "INIT_TIME"
            and type(completion.get("optimizer_updates")) is int and completion["optimizer_updates"] == 0
            and completion.get("old_TIME_unchanged") is True
            and same_reference(completion["model_weights_ref"], weights)
            and same_reference(completion["input_acceptance_ref"], manifest["scopes"]["check"]["input_acceptance_ref"]),
            "Historical reference role/weights/input identity differs")
    checked(completion["input_acceptance_ref"], root)
    base = completion["base_fingerprint"]
    require(base == runtime.base_before and base["sha256"] == manifest["model_spec"]["base_sha256"]
            and base["parameters"] == 8767123696, "Historical reference base fingerprint differs")
    require(qa.get("status") == "PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA"
            and qa.get("model_role") == "INIT_TIME" and qa.get("windows") == 43
            and qa.get("sources") == 8 and qa.get("invalid_outputs") == 0
            and qa.get("unique_ledger_equal") is True
            and same_reference(qa["completion_ref"], origin["completion_ref"])
            and qa["outputs"] == completion["outputs"], "Historical reference first output QA differs")
    checked(qa["completion_ref"], root)
    resource = strict_load(checked(qa["resource_ref"], root))
    require(resource.get("status") == "completed" and resource.get("exit_code") == 0,
            "Historical reference resource did not naturally complete")
    outputs = completion["outputs"]
    details = qa["details"]
    require(isinstance(outputs, list) and len(outputs) == 43 and isinstance(details, list)
            and len(details) == 43 and len({d["uid"] for d in details}) == 43,
            "Historical reference output/QA denominator differs")
    detail_by_uid = {row["uid"]: row for row in details}
    seen, refs = set(), []
    for number, output_ref in enumerate(outputs):
        budget.check()
        old = strict_load(checked(output_ref, root))
        uid = old["uid"]
        require(uid in expected and uid not in seen and uid in detail_by_uid,
                "Missing, duplicate or foreign historical reference window")
        seen.add(uid)
        request = store.requests[uid]
        require(strict_load(checked(store.request_refs[uid], root)) == request,
                "Accepted historical request metadata changed")
        require(old["sid"] == request["sid"] and old["model_role"] == "INIT_TIME"
                and same_reference(old["model_weights_ref"], weights)
                and same_reference(old["request_ref"], store.request_refs[uid])
                and detail_by_uid[uid]["sid"] == request["sid"]
                and same_reference(detail_by_uid[uid]["output_ref"], output_ref),
                "Historical output/request/QA identity differs")
        raw = strict_load(checked(old["raw_token_ref"], root))
        require(all(raw[key] == old[key] for key in
                    ("uid", "sid", "request_ref", "generated_ids", "model_role", "model_weights_ref")),
                "Historical raw token receipt differs from accepted output")
        ids, text = old["generated_ids"], old["raw_text"]
        require(isinstance(ids, list) and 0 < len(ids) <= 512
                and all(type(token) is int and token >= 0 for token in ids),
                "Historical reference token sequence is invalid")
        require(runtime.tokenizer.decode(ids[:-1], skip_special_tokens=False,
                    clean_up_tokenization_spaces=False) == text,
                "Historical reference tokenizer/raw text differs")
        start, end = request["plan"]["window_start_exact"], request["plan"]["window_end_exact"]
        duration = Fraction(end) - Fraction(start)
        validate_token_path(runtime.tokenizer, ids, text, duration, grammar, candidates)
        clock = store.clocks[request["sid"]]
        selected = native_selection(parse_answer(text, duration), clock["normalized_exact_pts"], start, end)
        row = dict(role="reference", uid=uid, source_id=request["sid"],
            request_ref=store.request_refs[uid], clock_ref=store.sources[request["sid"]]["clock_ref"],
            input_signature=request["input_signature"], status="ACCEPTED", text=text, ids=ids,
            eos=True, eos_token_id=runtime.eos, actual_model_call=True,
            adopted_historical_model_call=True, new_model_calls=0,
            historical_output_ref=output_ref, historical_raw_token_ref=old["raw_token_ref"],
            historical_completion_ref=origin["completion_ref"],
            historical_first_output_qa_ref=origin["first_output_qa_ref"],
            selected_ordinals=sorted(selected), legal_empty=not selected)
        case_output(row, request, clock, eos=runtime.eos)
        journal.context = dict(action="adopt_historical_reference", role="reference", uid=uid)
        journal("historical_model_call_adopted", dict(output_ref=output_ref, new_model_calls=0))
        refs.append(save_new(directory / ("reference_" + str(number).zfill(4) + ".json"), row))
    require(seen == expected == set(detail_by_uid), "Missing historical windows are not empty predictions")
    store.close()
    return refs
