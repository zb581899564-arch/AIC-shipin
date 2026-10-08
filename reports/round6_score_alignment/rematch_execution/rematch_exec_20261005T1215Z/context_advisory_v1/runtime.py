"""C-advisory inference, binding frozen V14 native decoder and B adapter.

All output attempts first receive an exclusive raw receipt. Validation never
overwrites an attempt, fills an event, repairs a boundary or converts failure
to empty. Overview inference disables B's adapter; local inference enables it.
"""
import contextlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
sys.path.insert(0, str(HERE))
import context_contract as cc

OVERVIEW_TEXT = (
    "Describe visible activities in this sparse overview of one source video. "
    "This is factual context, not a highlight selection. Number the actual supplied "
    "video frames from 0 in their displayed order. Return ONLY canonical JSON "
    '{"events":[{"first":0,"last":1,"description":"brief visible activity"}]}. '
    "Use 0 to 8 events. Each first and last is an actual supplied frame number, "
    "0 <= first <= last < the supplied frame count. Use concise English descriptions "
    "of at most 80 characters. Include only activities directly visible in those "
    'frames; do not infer unseen actions or label highlights. If none can be described, '
    'return {"events":[]}. Sparse frames can miss short events.'
)
ADVISORY_TEXT = (
    "\nAdditional sparse source-video context follows. It describes sampled visible "
    "activities, not highlight labels. It can be incomplete or irrelevant. Judge "
    "the current local video visually; a missing event is not a negative example. "
    "Do not let this context exclude any visible local event. Source times in the "
    "table are not clip-local output boundaries. Output boundaries still follow "
    "the original clip-local rules above.\nSOURCE_CONTEXT_JSON:\n"
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bind_helpers():
    student = load(RUN / "teacher_student_autopilot_v14/train_student.py", "cad_v14_student")
    student.helper_paths(RUN)
    # production_t imports train_student by its public name.
    sys.modules["train_student"] = student
    production = load(RUN / "teacher_student_autopilot_v14/production_t.py", "cad_v14_production")
    student, common, frame_contract, source = production.helpers()
    return student, common, frame_contract, production


def raw_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def prompt(processor, text):
    value = processor.apply_chat_template([{"role": "user", "content": [{"type": "text", "text": text}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return value.replace("<|im_start|>user\n", "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)


def encode_decoded(processor, decoded, text):
    import torch
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    student = sys.modules["train_student"]
    arr, metadata, plan, evidence = decoded
    with exact_native_pts(processor, plan, metadata["fps"]) as native:
        encoded = encode(processor, text=[prompt(processor, text)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=student.VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**evidence, native_processor_identity=native,
        **identity(processor, encoded, len(arr)), registered_prompt_sha256=cc.digest(text))


def overview_candidates(tokenizer):
    alphabet = cc.DESCRIPTION_CHARS | frozenset('{}[]"0123456789,')
    # The same documented ASCII advisory prefilter used by the local grammar.
    result = []
    for token in sorted(set(tokenizer.get_vocab().values())):
        piece = tokenizer.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= alphabet:
            result.append((token, piece))
    return tuple(result)


class OverviewPrefix:
    def __init__(self, tokenizer, prompt_length, frames, candidates, eos):
        self.tokenizer, self.prompt_length = tokenizer, prompt_length
        self.grammar = cc.OverviewGrammar(frames)
        self.eos = [eos] if isinstance(eos, int) else list(eos)
        self.candidates = [(i, p) for i, p in candidates if i not in self.eos]
        self.cache = {}
        self.pieces = dict(self.candidates)
        self.stats = {"calls": 0, "candidate_count": len(self.candidates), "full_context_decodes": 0}

    def decode(self, ids):
        self.stats["full_context_decodes"] += 1
        return self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)

    def __call__(self, batch, input_ids):
        ids = tuple(input_ids.tolist()[self.prompt_length:])
        self.stats["calls"] += 1
        if ids in self.cache:
            return self.cache[ids]
        text = self.decode(list(ids))
        cc.require(text == "".join(self.pieces[i] for i in ids),
            "actual full-context ASCII token decoding not additive; STOP")
        if self.grammar.complete(text):
            allowed = self.eos
        else:
            cc.require(self.grammar.valid_prefix(text), "invalid overview prefix; no recovery")
            self.grammar.prepare(text)
            allowed = []
            for token, piece in self.candidates:
                # Incremental ASCII automaton; the actual selected HF prefix is
                # whole-context decoded and checked for additivity on every call.
                if self.grammar.can_extend(piece):
                    allowed.append(token)
        cc.require(allowed, "overview generation dead end; no output repair")
        self.cache[ids] = allowed
        return allowed


def attempt(model, processor, encoded, evidence, window, raw_path, *, overview=False,
            allow_empty=True, local_candidates=None, event_candidates=None):
    import torch
    from constrained_json import make_prefix_constraint
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    prefix = int(encoded["input_ids"].shape[1])
    eos = model.generation_config.eos_token_id
    constraint = (OverviewPrefix(processor.tokenizer, prefix,
        len(window["planned_actual_pts_sec"]), event_candidates, eos) if overview else
        make_prefix_constraint(processor.tokenizer, prefix, window["window_duration_sec"],
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
            segments, errors, warnings = parse_segments(raw, window["window_duration_sec"], allow_empty=allow_empty)
            cc.require(segments is not None and not errors, "local parse rejected: " + repr(errors))
            ranges = native_segment_ranges(segments, evidence["window_source_pts_sec"],
                window["window_pts_start_sec"], window["window_duration_sec"])
            result = {"status": "MODEL_OK" if segments else "LEGAL_EMPTY", "output_valid": True,
                "parsed_segments": segments, "parse_errors": errors, "parse_warnings": warnings,
                "native_frame_realizability": {"status": "PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY", "ranges": ranges,
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
