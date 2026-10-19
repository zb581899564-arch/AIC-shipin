"""Independent CPU re-reading of saved outputs and frozen execution receipts.

No Qwen instance or media decoder is created here. The local tokenizer is used
to verify real token paths; changed observations are rebuilt from retained
patches and their saved prefix before they may be evaluated or packaged.
"""
from fractions import Fraction
from types import SimpleNamespace

from .adoption import validate_answer
from .contracts import checked, require, same_reference, strict_load, FROZEN_PIPELINE


def answer_reader(manifest, identity):
    from improvement.native_preference_v1.runtime import load_tokenizer
    from improvement.native_preference_v1.run import grammar_module
    tokenizer = load_tokenizer(manifest["model_spec"])
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    require(eos == identity["eos_token_id"], "Saved answer uses another tokenizer EOS")
    grammar = grammar_module(manifest)
    return SimpleNamespace(tokenizer=tokenizer, eos=eos), grammar, grammar.ascii_token_candidates(tokenizer)


def frozen_receipt(value, workspace):
    """Require actual counts and immutable original parameters, not a PASS word."""
    frozen = strict_load(checked(value["frozen_verification_ref"], workspace))
    identity, counts = value["runtime"], value["counts"]
    require(frozen.get("schema") == "AIC_CONTENT_CHOICE_FROZEN_VERIFICATION_V1"
            and frozen["runtime"] == identity and frozen["counts"] == counts
            and frozen.get("original_TIME_files_unchanged") is True
            and frozen.get("changed_adapter_matrices") == 0
            and frozen.get("optimizer_steps") == frozen.get("backward_calls") == 0,
            "Frozen verification and actual runtime/counters disagree")
    require(identity.get("schema") == "AIC_CONTENT_CHOICE_RUNTIME_V1"
            and identity.get("active_weights") == "ORIGINAL_TIME_UNCHANGED"
            and identity.get("optimizer_updates") == 0
            and identity.get("conservative_full_pipeline_parameters") == FROZEN_PIPELINE
            and frozen["inventory"]["conservative_full_pipeline"] == FROZEN_PIPELINE
            and frozen["base"]["sha256"] == identity["base_sha256"],
            "Original TIME/full-pipeline identity differs")
    require(all(type(v) is int and v >= 0 for v in counts.values())
            and all(counts[key] == 0 for key in ("optimizer_steps", "backward_calls", "backwards_completed"))
            and counts["sequence_score_calls"] == counts["sequence_scores_completed"]
                == counts["feature_score_calls"] == counts["feature_scores_completed"]
            and counts["generation_calls"] == counts["generations_completed"]
            and counts["sample_generation_calls"] == counts["samples_completed"] <= counts["generation_calls"]
            and counts["top_level_forward_calls"] >= counts["generation_calls"] + counts["sequence_score_calls"],
            "Actual frozen generation/TF counters are incomplete or include forbidden updates")
    checked(value["event_journal_ref"], workspace)
    checked(value["torch_checks_ref"], workspace)
    return frozen


def validate_window_outputs(row, request, clock, reader):
    runtime, grammar, vocabulary = reader
    for slot in row["slots"]:
        require(slot.get("status") == "ACCEPTED" and len(slot["ids"]) <= 512,
                "Incomplete or over-budget candidate answer")
        selected = validate_answer(runtime, request, clock, slot["text"], slot["ids"], grammar, vocabulary)
        require(selected == slot["selected_ordinals"] and slot["legal_empty"] == (not selected),
                "Saved actual token/grammar/native selection does not reparse independently")
        if slot["slot"] == 3:
            require(slot["text"] == '{"segments":[]}', "Explicit empty action text changed")
    return True


def collection_call_counts(windows, *, adopted):
    """Count deduplicated real calls from suffix identity, never from alias rows."""
    generation = len(windows) * (2 if adopted else 3)
    scores = 0
    for row in windows.values():
        unique = {tuple(slot["ids"]) for slot in row["slots"]}
        same = row["counterfactual_identical_input"]
        require(type(same) is bool, "Explicit counterfactual byte-identity decision required")
        shifted = row["counterfactual"] is not None
        scores += len(unique) * (2 if shifted and not same else 1)
        if shifted:
            signature = row["counterfactual_input_signature"]
            require(set(signature) == set(row["input_signature"])
                    and same == (signature == row["input_signature"])
                    and all(signature[key] == row["input_signature"][key] for key in
                            ("input_ids", "attention_mask", "video_grid_thw")),
                    "Counterfactual must retain text/grid and report actual byte identity")
        else:
            require(row["counterfactual_input_signature"] is None and not same,
                    "An uncomputed counterfactual cannot claim identity adoption")
        seen = {}
        for slot in row["slots"]:
            key = tuple(slot["ids"])
            first = seen.setdefault(key, slot["slot"])
            require(slot["score_cache_first_slot"] == first,
                    "TF cache alias is not the first identical suffix in this exact input")
            if first != slot["slot"]:
                original = row["slots"][first]
                require(slot["real"] == original["real"] and slot["permuted"] == original["permuted"],
                        "Reused TF cache changed feature or log probability")
            require(slot["real"].get("actual_model_call") is True,
                    "Every unique real suffix needs an actual completed TF score")
            if shifted:
                require(slot["permuted"].get("actual_model_call") is (not same),
                        "Counterfactual call/identity reuse accounting differs")
                if same:
                    require(all(slot["permuted"][k] == slot["real"][k]
                                for k in ("logprob", "feature", "suffix_tokens", "feature_position")),
                            "Identical-input score alias changed the actual feature or score")
            else:
                require(slot["permuted"] is None, "Uncalled counterfactual acquired a score")
    return dict(generation_calls=generation, sample_generation_calls=2 * len(windows), sequence_score_calls=scores)


def check_call_counts(counts, expected):
    require(all(counts[key] == value for key, value in expected.items()),
            "Actual calls disagree with complete windows and exact-token cache reuse")


def original_request_core_equal(request, original):
    # New provenance keys are allowed; every original field, including native
    # plan/text/prefix/four-tensor signature, must remain equal.
    return all(key in request and request[key] == value for key, value in original.items())


def verify_saved_observation(store, uid, request, *, processor=None):
    """Rebuild all four tensors from saved native plan/prefix; no Qwen call."""
    import torch
    from .observation import pack_selected_pixels
    original = store.requests[uid]
    sid = original["sid"]
    require(request["uid"] == uid and request["sid"] == sid
            and request["source_sha256"] == original["source_sha256"]
            and same_reference(request["source_clock_ref"], store.sources[sid]["clock_ref"])
            and request["grid_hw"] == original["grid_hw"]
            and all(Fraction(request["plan"][key]) == Fraction(original["plan"][key]) for key in
                    ("window_start_exact", "window_end_exact")),
            "Changed observation must retain exact source/native clock/window/grid ownership")
    checked(request["source_clock_ref"], store.workspace)
    checked(request["old_input_ref"], store.workspace)
    require(same_reference(request["old_input_ref"], store.request_refs[uid])
            and same_reference(request["old_prefix_ref"], original["prefix_ref"]),
            "Changed observation origin references differ")
    prefix = torch.load(checked(request["prefix_ref"], store.workspace), map_location="cpu", weights_only=True)
    require(isinstance(prefix, dict) and set(prefix) == {"input_ids", "attention_mask"}
            and all(v.device.type == "cpu" and v.dtype == torch.int64 and v.ndim == 2 and v.shape[0] == 1
                    for v in prefix.values())
            and prefix["input_ids"].shape == prefix["attention_mask"].shape
            and prefix["input_ids"].shape[1] == request["text"]["prefix_tokens"]
            and bool((prefix["attention_mask"] == 1).all()),
            "Saved changed prefix must be the actual unpadded CPU token pair")
    frames, grid, ordinals = store._source_pixels(sid)
    clock, plan = store.clocks[sid], request["plan"]
    cells = [video["cells"] for video in plan["videos"]]
    pixels, rebuilt = pack_selected_pixels(frames, grid, ordinals, clock["normalized_exact_pts"],
        plan["window_start_exact"], plan["window_end_exact"],
        dict(source_id=sid, source_sha256=request["source_sha256"]), cells)
    require(rebuilt == plan, "Saved observation plan differs from actual cached pixel construction")
    contract = store._helpers()
    contract.independent_pixels(frames, grid, pixels, plan, ordinals, clock["normalized_exact_pts"])
    values = dict(**pixels, **prefix)
    require(contract.signature(values) == request["input_signature"],
            "Saved/reloaded observation four-tensor bytes differ from the actual generation input")
    require(request["text"]["prompt"] == original["text"]["prompt"]
            and request["text"]["raw_template"] == original["text"]["raw_template"],
            "Changed observation question/template differs")
    if processor is not None:
        contract.independent_text(processor, plan, values, request["text"])
    return values
