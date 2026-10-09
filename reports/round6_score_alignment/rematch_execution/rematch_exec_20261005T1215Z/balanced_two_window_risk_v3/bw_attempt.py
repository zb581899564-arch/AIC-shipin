"""Original attempt algorithm with its existing Fraction duration interface."""
import contextlib,math,time,traceback
from pathlib import Path
import bw_common as c
cc=c.helpers()[2]
raw_write=c.save
def attempt(model, processor, encoded, evidence, window, raw_path, *, overview=False,
            allow_empty=True, local_candidates=None, event_candidates=None):
    import torch
    from constrained_json import make_prefix_constraint
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    from fractions import Fraction
    exact_duration=Fraction(window['exact_raw_end'])-Fraction(window['exact_raw_start'])
    prefix = int(encoded["input_ids"].shape[1])
    eos = model.generation_config.eos_token_id
    constraint = (OverviewPrefix(processor.tokenizer, prefix,
        len(window["planned_actual_pts_sec"]), event_candidates, eos) if overview else
        make_prefix_constraint(processor.tokenizer, prefix, exact_duration,
            candidate_token_ids=local_candidates, eos_token_ids=eos, allow_empty=allow_empty))
    started = time.monotonic()
    try:
        with (model.disable_adapter() if overview else contextlib.nullcontext()), torch.inference_mode():
            generated = model.generate(**encoded.to("cuda"), do_sample=False,
                max_new_tokens=1280 if overview else 256, prefix_allowed_tokens_fn=constraint,
                return_dict_in_generate=True, output_scores=True)
        torch.cuda.synchronize()
        ids = generated.sequences[0, prefix:]
        raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        selected_scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
        # Save the exact model answer before ANY completeness or validity check.
        receipt = {"raw_output": raw, "output_token_ids": ids.tolist(),
            "selected_token_scores": [x if math.isfinite(x) else str(x) for x in selected_scores], "input_tokens": prefix,
            "actual_model_call": True, "overview_adapter_disabled": overview,
            "window": window, "video_identity": evidence,
            "generation_seconds": time.monotonic() - started, "constraint_stats": constraint.stats}
        raw_write(raw_path, receipt)
        cc.require(selected_scores and all(math.isfinite(x) for x in selected_scores), "nonfinite actual selected token scores")
        if overview:
            value = cc.validate_overview(raw, window["planned_actual_pts_sec"])
            result = {"status": "LEGAL_EMPTY_EVENTS" if not value["events"] else "MODEL_OK_EVENTS",
                "output_valid": True, "events": value, "sparse_not_complete_observation": True,
                "descriptions_are_model_claims_not_semantic_truth": True}
        else:
            constraint.assert_complete(ids)
            segments, errors, warnings = parse_segments(raw, exact_duration, allow_empty=allow_empty)
            cc.require(segments is not None and not errors, "local parse rejected: " + repr(errors))
            ranges = native_segment_ranges(segments, evidence["window_source_pts_sec"],
                window["window_pts_start_sec"], exact_duration)
            result = {"status": "MODEL_OK" if segments else "LEGAL_EMPTY", "output_valid": True,
                "parsed_segments": segments, "parse_errors": errors, "parse_warnings": warnings,
                "native_frame_realizability": {"status": "PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY", "ranges": [list(pair) for pair in ranges],
                    "not_limited_to_64_teacher_samples": True}}
        result.update(raw_output=raw, raw_receipt=str(raw_path), video_identity=evidence,
            constraint_stats=constraint.stats, generation_time_constraint=True,
            input_tokens=prefix, output_tokens=len(ids), generation_seconds=time.monotonic() - started)
        return result
    except Exception as error:
        failure = {"status": "STOP_ACTUAL_GENERATION_OR_VALIDATION_FAILURE", "failure_converted_to_empty": False,
            "error": type(error).__name__ + ": " + str(error), "traceback": traceback.format_exc(),
            "raw_receipt_exists": Path(raw_path).exists()}
        raw_write(str(raw_path) + ".failure.json", failure)
        raise
