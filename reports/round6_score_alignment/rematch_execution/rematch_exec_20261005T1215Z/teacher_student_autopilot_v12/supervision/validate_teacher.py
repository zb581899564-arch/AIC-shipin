"""Stdlib-only validation: uncertain/invalid observations never become empty SFT labels.

No model imports, downloads or inference. Annotation receipts must come from a
separately admitted real teacher job, with decoded PTS/pixel identities attached.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

from select_windows import HERE, finite, require, output_directory, sha256, validate_isolation, write_jsonl

TEACHER_BASE = "Qwen/Qwen3-VL-32B-Instruct"
ALLOWED_TEACHERS = {TEACHER_BASE: "0cfaf48183f594c314753d30a4c4974bc75f3ccb",
    TEACHER_BASE + "-GGUF": "e3e1fe0c76de7ee58ea65db420c643adfe2e457c"}
MAX_TARGET_SEGMENTS = 5
KEYS = {"window_id", "observation_scope", "retained_segments", "explicit_no_highlight",
        "uncertain", "uncertainty_reasons", "decision_reason", "boundary_notes"}
SCOPE_KEYS = {"window_pts_start_sec", "window_pts_end_exclusive_sec", "sampled_pts_sec", "all_provided_frames_reviewed"}


def text_sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def exact_keys(value, keys, reason):
    require(isinstance(value, dict) and set(value) == keys, reason)


def nonempty_text(value):
    return isinstance(value, str) and bool(value.strip())


def same_numbers(actual, expected, reason):
    require(isinstance(actual, list) and len(actual) == len(expected)
            and all(finite(a) and finite(b) and abs(a - b) <= 1e-6 for a, b in zip(actual, expected)), reason)


def strict_json(raw):
    require(isinstance(raw, str) and raw.strip(), "empty real teacher response")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(token):
        raise ValueError("nonfinite JSON number: " + token)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def validate_window(window):
    require(window.get("schema") == "aic_complete_window_selection_v1" and window.get("split") in ("train", "dev"),
            "only new train/dev selected windows are allowed")
    require(window.get("source_group") == window.get("youtube_id") and nonempty_text(window.get("source_group")),
            "source group must be the YouTube leakage unit")
    path = PurePosixPath(window.get("source_path", ""))
    require(path.is_absolute() and ".." not in path.parts and PurePosixPath("/home/inspur/aic_video_data/videos") in path.parents,
            "teacher observation source outside approved non-test media root")
    require(is_sha(window.get("source_sha256")) and is_sha(window.get("clock_sequence_sha256")), "missing source/clock identity")
    start, end = window.get("window_pts_start_sec"), window.get("window_pts_end_exclusive_sec")
    require(finite(start) and finite(end) and end > start and end - start <= 30 + 1e-6, "invalid natural window extent")
    require(finite(window.get("window_duration_sec")) and abs(window["window_duration_sec"] - (end - start)) <= 1e-6,
            "window duration differs from actual source clock")
    points, indices = window.get("planned_actual_pts_sec"), window.get("planned_source_frame_ordinals")
    require(isinstance(points, list) and 1 <= len(points) <= 64 and all(finite(p) and start <= p < end for p in points),
            "invalid planned source PTS coverage")
    require(all(b > a for a, b in zip(points, points[1:])), "planned PTS out of order")
    require(isinstance(indices, list) and len(indices) == len(points) and all(type(i) is int and i >= 0 for i in indices)
            and all(b > a for a, b in zip(indices, indices[1:])), "invalid planned source frame ordinals")
    same_numbers([points[0], points[-1]], [window["first_eligible_pts_sec"], window["last_eligible_pts_sec"]],
                 "planned sampling does not reach both actual eligible endpoints")


def validate_observation(window, observation):
    require(isinstance(observation, dict) and observation.get("decode_status") == "PASS_REAL_SEQUENTIAL_DECODE"
            and observation.get("pixel_identity_status") == "PASS"
            and observation.get("all_planned_frames_delivered") is True,
            "actual sequential decoding/frame delivery receipt required")
    for key in ("window_id", "source_path", "source_sha256", "clock_sequence_sha256"):
        require(observation.get(key) == window.get(key), "observation identity mismatch: " + key)
    require(observation.get("source_frame_ordinals") == window["planned_source_frame_ordinals"], "actual source ordinals differ")
    same_numbers(observation.get("actual_pts_sec"), window["planned_actual_pts_sec"], "actual decoded PTS differ from selected clock")
    pixels = observation.get("frame_pixel_sha256")
    require(isinstance(pixels, list) and len(pixels) == len(window["planned_actual_pts_sec"])
            and all(is_sha(p) for p in pixels), "actual per-frame pixel SHA missing")
    require(is_sha(observation.get("input_contract_sha256")), "real processor input contract not bound")
    sizes = observation.get("actual_processed_pixels_per_frame")
    require(isinstance(sizes, list) and len(sizes) == len(pixels) and all(type(p) is int and p > 0 for p in sizes),
            "actual processed video pixel budget unavailable")
    for key in ("max_pixels_per_frame", "max_sequence_length", "input_sequence_length"):
        require(type(observation.get(key)) is int and observation[key] > 0, "explicit real processor limit required: " + key)
    require(max(sizes) <= observation["max_pixels_per_frame"]
            and observation["input_sequence_length"] <= observation["max_sequence_length"], "teacher input exceeded its admitted contract")
    require(observation.get("max_frames") == 64, "teacher sampling frame limit changed")


def prompt_for(window, observation):
    contract = {key: window[key] for key in ("window_id", "window_pts_start_sec", "window_pts_end_exclusive_sec", "window_duration_sec")}
    contract.update(sampled_pts_sec=observation["actual_pts_sec"],
                    pts_clock="SOURCE_PRESENTATION_SECONDS", output_clock="WINDOW_LOCAL_SECONDS",
                    sampled_only_not_all_source_frames=True,
                    actual_frame_count=len(observation["actual_pts_sec"]))
    template = (HERE / "teacher_prompt.txt").read_text(encoding="utf-8")
    require(template.count("{{WINDOW_CONTRACT_JSON}}") == 1, "prompt placeholder mismatch")
    return template.replace("{{WINDOW_CONTRACT_JSON}}", json.dumps(contract, ensure_ascii=False, sort_keys=True, allow_nan=False))


def validate_teacher(teacher, prompt):
    require(isinstance(teacher, dict) and teacher.get("inference_status") == "PASS_REAL_TEACHER_GENERATION",
            "real separately admitted teacher generation receipt required")
    require(teacher.get("base_model_id") == TEACHER_BASE and teacher.get("model_id") in ALLOWED_TEACHERS
            and teacher.get("model_revision") == ALLOWED_TEACHERS[teacher["model_id"]],
            "pinned stronger teacher identity mismatch; never silently substitute the same 8B")
    require(teacher.get("prompt_sha256") == text_sha(prompt), "actual teacher prompt binding differs")
    require(teacher.get("production_test_access") is False and teacher.get("capacity_admission_pass") is True,
            "offline non-test teacher capacity/production isolation receipt required")
    require(is_sha(teacher.get("job_source_lock_sha256")), "teacher job source lock missing")
    weights = teacher.get("weight_files")
    require(isinstance(weights, list) and weights and all(isinstance(w, dict) and nonempty_text(w.get("path"))
            and is_sha(w.get("sha256")) for w in weights), "pinned actual teacher weight identities missing")
    metadata = json.loads((HERE / "teacher_metadata_20261007.json").read_text(encoding="utf-8"))
    model_meta = next(m for m in metadata["models"] if m["repo"] == teacher["model_id"])
    expected_files = model_meta.get("selected_weight_files", model_meta.get("bf16_selected_weight_files"))
    expected = {f["path"]: f["lfs_sha256"] for f in expected_files}
    actual = {PurePosixPath(f["path"]).name: f["sha256"] for f in weights}
    require(len(actual) == len(weights) and actual == expected, "actual teacher weight set differs from pinned official recipe")
    require(nonempty_text(teacher.get("runtime_revision")) and nonempty_text(teacher.get("generated_utc")), "teacher runtime/time receipt missing")


def validate_response(window, observation, response):
    exact_keys(response, KEYS, "teacher JSON fields differ from schema")
    require(response["window_id"] == window["window_id"], "teacher window identity differs")
    scope = response["observation_scope"]
    exact_keys(scope, SCOPE_KEYS, "observation_scope fields differ from schema")
    same_numbers([scope["window_pts_start_sec"], scope["window_pts_end_exclusive_sec"]],
                 [window["window_pts_start_sec"], window["window_pts_end_exclusive_sec"]], "teacher observed scope differs")
    same_numbers(scope["sampled_pts_sec"], observation["actual_pts_sec"], "teacher sampled PTS differ from actual delivered frames")
    require(scope["all_provided_frames_reviewed"] is True, "teacher did not review every provided sample")
    require(type(response["uncertain"]) is bool and type(response["explicit_no_highlight"]) is bool, "decision flags must be booleans")
    require(nonempty_text(response["decision_reason"]), "complete-window judgment lacks explanation")
    for key in ("uncertainty_reasons", "boundary_notes"):
        require(isinstance(response[key], list) and all(nonempty_text(r) for r in response[key]), "invalid explanation list: " + key)
    require(bool(response["uncertainty_reasons"]) == response["uncertain"], "uncertainty flag/reasons disagree")
    segments = response["retained_segments"]
    require(isinstance(segments, list), "retained_segments must be a list")
    previous = 0.0
    for segment in segments:
        exact_keys(segment, {"start_sec", "end_sec", "reason"}, "retained segment fields differ")
        a, b = segment["start_sec"], segment["end_sec"]
        require(finite(a) and finite(b) and 0 <= a < b <= window["window_duration_sec"] and a >= previous,
                "invalid, out-of-window, unordered or overlapping retained segment; never clamp/merge")
        require(nonempty_text(segment["reason"]), "retained segment lacks observable-event/boundary explanation")
        previous = b
    if response["uncertain"]:
        require(response["explicit_no_highlight"] is False, "UNKNOWN cannot certify an empty negative")
    elif segments:
        require(response["explicit_no_highlight"] is False, "positive segments conflict with explicit no-highlight")
    else:
        require(response["explicit_no_highlight"] is True, "empty target lacks an explicit justified no-highlight judgment")


def make_record(window, observation, teacher, raw_answer):
    # Preserve every raw answer and rejected segment. No retry, clipping, sorting or fabricated empty target.
    record = {"schema": "aic_complete_window_teacher_record_v1", "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window": window, "source_group": window.get("source_group"), "source_sha256": window.get("source_sha256"),
        "split": window.get("split"), "window_id": window.get("window_id"), "actual_observation": observation,
        "teacher": teacher, "raw_answer": raw_answer,
        "raw_answer_sha256": text_sha(raw_answer) if isinstance(raw_answer, str) else None,
        "label_status": "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH",
        "cleaning_reasons": [], "validation_errors": [], "sft_eligible": False, "target_json": None,
        "full_window_judgment_under_sampled_protocol_only": True,
        "unobserved_gaps_not_proven_negative": True, "independent_reference_verified": False}
    try:
        validate_window(window)
        validate_observation(window, observation)
        prompt = prompt_for(window, observation)
        record.update(prompt_text=prompt, prompt_sha256=text_sha(prompt),
                      prompt_template_sha256=sha256(HERE / "teacher_prompt.txt"),
                      response_schema_sha256=sha256(HERE / "teacher_response.schema.json"))
        validate_teacher(teacher, prompt)
        response = strict_json(raw_answer)
        record["parsed_answer"] = response
        validate_response(window, observation, response)
        record.update(retained_segments=response["retained_segments"], explicit_no_highlight=response["explicit_no_highlight"],
                      uncertain=response["uncertain"], actual_pts_coverage_sec=[observation["actual_pts_sec"][0], observation["actual_pts_sec"][-1]])
        if raw_answer != raw_answer.strip():
            record["cleaning_reasons"].append("Outer whitespace accepted by JSON parser; raw answer retained unchanged")
        if response["uncertain"]:
            record.update(status="EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET")
            record["cleaning_reasons"].append("Uncertain complete list excluded; retained candidates and explanation remain in audit record")
        elif len(response["retained_segments"]) > MAX_TARGET_SEGMENTS:
            record.update(status="EXCLUDED_UNREPRESENTABLE_SEGMENT_COUNT")
            record["cleaning_reasons"].append("More than registered production maximum 5 segments; no segments removed to fit target")
        else:
            pairs = [[s["start_sec"], s["end_sec"]] for s in response["retained_segments"]]
            record.update(status="PASS_WEAK_COMPLETE_WINDOW_TARGET", sft_eligible=True,
                          target_json=json.dumps({"segments": pairs}, separators=(",", ":"), allow_nan=False))
            record["cleaning_reasons"].append("Strict validated weak response projected to interval-only JSON; event reasons remain in audit record")
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        record.update(status="INVALID_TEACHER_OR_INPUT_RECEIPT")
        record["validation_errors"].append(f"{type(exc).__name__}: {exc}")
    return record


def summarize(records):
    eligible = [r for r in records if r["sft_eligible"]]
    return {"record_count": len(records), "eligible_count": len(eligible),
        "status_counts": dict(Counter(r["status"] for r in records)),
        "eligible_by_split": {split: sum(r["split"] == split for r in eligible) for split in ("train", "dev")},
        "explicit_empty_by_split": {split: sum(r["split"] == split and r.get("explicit_no_highlight") is True for r in eligible)
                                    for split in ("train", "dev")},
        "positive_by_split": {split: sum(r["split"] == split and bool(r.get("retained_segments")) for r in eligible)
                              for split in ("train", "dev")},
        "multisegment_by_split": {split: sum(r["split"] == split and len(r.get("retained_segments", [])) > 1 for r in eligible)
                                  for split in ("train", "dev")},
        "weak_teacher_only": True, "semantic_training_admitted": False, "official_quality_claim": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-train", type=Path, required=True)
    parser.add_argument("--selected-dev", type=Path, required=True)
    parser.add_argument("--selection-receipt", type=Path, required=True)
    parser.add_argument("--annotation-receipts", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    selection = json.loads(args.selection_receipt.read_text(encoding="utf-8"))
    require(selection.get("status") == "PASS_CPU_SELECTION_UNLABELLED"
            and selection.get("confirm_opened") is False and selection.get("contest_assets_opened") is False,
            "successful non-test CPU selection receipt required")
    require(selection.get("files", {}).get("selected_train.jsonl") == sha256(args.selected_train)
            and selection.get("files", {}).get("selected_dev.jsonl") == sha256(args.selected_dev),
            "selected window bytes differ from CPU selection receipt")
    read = lambda path: [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    train, dev = read(args.selected_train), read(args.selected_dev)
    require(train and dev and all(r.get("split") == "train" for r in train) and all(r.get("split") == "dev" for r in dev),
            "selected files must contain their respective train/dev splits")
    require(len(train) <= 512 and len(dev) <= 64, "bounded supervision window limit exceeded")
    validate_isolation(train, dev)
    windows = {row["window_id"]: row for row in train + dev}
    require(len(windows) == len(train) + len(dev), "duplicate selected window id")
    for row in windows.values():
        validate_window(row)
    annotations = read(args.annotation_receipts)
    seen, records = set(), []
    for item in annotations:
        window_id = item.get("window_id")
        require(window_id in windows and window_id not in seen, "foreign/duplicate annotation; never include confirm/test")
        seen.add(window_id)
        records.append(make_record(windows[window_id], item.get("observation"), item.get("teacher"), item.get("raw_answer")))
    out = output_directory(args.out_dir)
    write_jsonl(out / "validated_records.jsonl", records)
    for split in ("train", "dev"):
        targets = [{"schema": "aic_complete_window_sft_target_v1", "window": r["window"], "target_json": r["target_json"],
            "teacher_record_sha256": text_sha(json.dumps(r, sort_keys=True, ensure_ascii=False, allow_nan=False)),
            "explicit_no_highlight": r["explicit_no_highlight"], "label_status": r["label_status"]}
            for r in records if r["sft_eligible"] and r["split"] == split]
        write_jsonl(out / ("eligible_" + split + ".jsonl"), targets)
    report = {"schema": "aic_complete_window_validation_receipt_v1", **summarize(records),
        "selected_window_count": len(windows), "unlabelled_window_count": len(windows) - len(seen),
        "unlabelled_windows_never_converted_to_empty": True,
        "annotation_receipts_sha256": sha256(args.annotation_receipts),
        "selection_receipt_sha256": sha256(args.selection_receipt),
        "selected_train_sha256": sha256(args.selected_train), "selected_dev_sha256": sha256(args.selected_dev),
        "confirm_opened": False, "contest_assets_opened": False, "gpu_used": False,
        "files": {name: sha256(out / name) for name in ("validated_records.jsonl", "eligible_train.jsonl", "eligible_dev.jsonl")}}
    (out / "validation_receipt.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
