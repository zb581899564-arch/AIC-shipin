"""One admitted T run: continue B, inspect update 20, select on weak open dev.

All model imports are deferred until authority/data/semantic admission passes.
This engine never downloads, transfers, opens confirm/test, or starts a GPU job.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import statistics
import subprocess
import sys
import time
import traceback

REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
INITIAL_SHA = "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23"
APPROVED_MANIFEST_SHA = {"train": "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf",
                         "dev": "53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700"}
VIDEO_SIZE = {"shortest_edge": 4096, "longest_edge": 25165824}
INPUT_CONTRACT = {
    "max_frames": 64, "video_size": VIDEO_SIZE, "max_input_tokens": 16384,
    "clock": "REAL_SOURCE_PRESENTATION_PTS_RELATIVE_TO_WINDOW_START",
    "sampling": "SELECTED_WINDOW_INTEGER_FLOOR_ENDPOINTS",
    "decoder": "SEQUENTIAL_PYAV_RGB24_WITH_ACTUAL_PTS_AND_PIXEL_SHA",
    "allow_empty": True, "prompt": "NEXT_ROUND_0_TO_5", "truncation": False,
    "same_contract_train_dev_production": True,
}
REQUIRED_HELPERS = (
    "next_round_v1/common.py", "next_round_v1/contracts.py", "next_round_v1/video_contract.py",
    "next_round_v1/training_target.py", "next_round_v1/engine.py",
    "teacher_student_autopilot_v5/supervision/validate_teacher.py", "teacher_student_autopilot_v5/supervision/select_windows.py",
    "teacher_student_autopilot_v5/supervision/teacher_prompt.txt", "teacher_student_autopilot_v5/supervision/teacher_metadata_20261007.json",
    "teacher_student_autopilot_v5/supervision/teacher_response.schema.json", "next_round_v1/constrained_json.py",
    "baseline_a_pts_v1/exact_pts.py", "baseline_a_pts_v1/native_frames.py", "baseline_a_pts_v1/pts_contract.py",
    "baseline_a_pts_v1/a_contract.py", "temporal_sft8b_v1/sft_contract.py",
    "temporal_sft8b_v1/train_sft.py", "temporal_sft8b_v1/verify_saved_smoke.py",
    "baseline_a_pts_v1/vendor/temporal_common.py",
)
_VERIFIED_SOURCE_STATS = {}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def record_sha(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def bound(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "missing bound file reference")
    path = Path(ref["path"]).resolve(strict=True)
    require(path.is_file() and sha(path) == ref["sha256"], "bound file changed: " + str(path))
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def helper_paths(run):
    # Frozen modules import each other by their historical names.
    paths = [run / "next_round_v1", run / "baseline_a_pts_v1", run / "baseline_a_pts_v1/vendor",
             run / "temporal_sft8b_v1", run / "teacher_student_autopilot_v5/supervision"]
    sys.path[:0] = list(map(str, paths))


def schedule(n, epochs=3, batch=16, seed=20261007):
    require(type(n) is int and n > 0 and type(epochs) is int and 1 <= epochs <= 3, "invalid training schedule")
    rng = random.Random(seed)
    result = []
    for epoch in range(1, epochs + 1):
        order = list(range(n))
        rng.shuffle(order)
        for offset in range(0, n, batch):
            result.append({"epoch": epoch, "indices": order[offset:offset + batch],
                           "epoch_last": offset + batch >= n})
    require(len(result) >= 20, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return result


def floor_indices(first, stop, max_frames=64):
    require(type(first) is int and type(stop) is int and 0 <= first < stop and max_frames == 64,
            "invalid T source ordinal window")
    count = stop - first
    if count <= max_frames:
        return list(range(first, stop))
    return [first + i * (count - 1) // (max_frames - 1) for i in range(max_frames)]


def window_from_pts(source_path, source_sha256, points, start, end, window_id, **identity):
    """Public T production planner; points are raw presentation seconds.

    The controller supplies a SHA-bound full source PTS table and natural
    windows, including the packet-duration endpoint. It must preserve raw
    origin in start/end; this function never derives timestamps from FPS.
    """
    from bisect import bisect_left
    require(points and all(math.isfinite(t) for t in points) and all(b > a for a, b in zip(points, points[1:])),
            "full source native PTS required")
    require(math.isfinite(start) and math.isfinite(end) and start < end and end - start <= 30 + 1e-6,
            "invalid T natural time window")
    first, stop = bisect_left(points, start), bisect_left(points, end)
    ids = floor_indices(first, stop)
    return dict(identity, source_path=str(source_path), source_sha256=source_sha256, window_id=window_id,
        window_pts_start_sec=start, window_pts_end_exclusive_sec=end, window_duration_sec=end - start,
        planned_source_frame_ordinals=ids, planned_actual_pts_sec=[points[i] for i in ids],
        eligible_source_frame_count=stop - first, source_total_frames=len(points))


def validate_isolation(train, dev):
    require(train and dev and len(train) <= 512 and len(dev) <= 64, "invalid eligible train/dev denominator")
    all_ids = [r["window"]["window_id"] for r in train + dev]
    require(len(set(all_ids)) == len(all_ids), "duplicate eligible window")
    for split, values in (("train", train), ("dev", dev)):
        for row in values:
            w = row["window"]
            require(w.get("split") == split and w.get("source_group") == w.get("youtube_id"), "wrong split/source unit")
            p = PurePosixPath(w.get("source_path", ""))
            require(p.is_absolute() and ".." not in p.parts and
                    PurePosixPath("/home/inspur/aic_video_data/videos") in p.parents, "confirm/test/outside-media path rejected")
    for key in ("youtube_id", "source_path", "source_sha256"):
        require(not ({r["window"][key] for r in train} & {r["window"][key] for r in dev}), "train/dev leakage: " + key)


def validate_lineage(eligible, approved, split):
    identities = {(r["source_path"], r["youtube_id"]): set() for r in approved}
    for row in approved:
        require(row.get("split") == split, "approved manifest split changed")
        identities[(row["source_path"], row["youtube_id"])].add(row["sample_id"])
    for row in eligible:
        window = row["window"]
        key = (window["source_path"], window["youtube_id"])
        parents = window.get("parent_sample_ids")
        require(key in identities and isinstance(parents, list) and parents and
                set(parents) <= identities[key], "eligible source/parent not in approved original " + split + " registry")


def validate_raw_semantic(item, original):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate raw semantic review JSON key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("nonfinite raw semantic review JSON: " + value)
    value = json.loads(item["raw_response"], object_pairs_hook=pairs, parse_constant=invalid_constant)
    require(isinstance(value, dict) and set(value) == {"window_id", "observation_scope", "semantics_consistent", "uncertain", "reason", "issues"},
            "raw semantic review response schema changed")
    require(value["window_id"] == original["window_id"] and value["semantics_consistent"] is True and
            value["uncertain"] is False and value["issues"] == [] and value["reason"] == item["reason"] and
            isinstance(value["reason"], str) and value["reason"].strip(), "raw semantic review does not support receipt PASS")
    scope = value["observation_scope"]
    require(isinstance(scope, dict) and set(scope) == {"window_pts_start_sec", "window_pts_end_exclusive_sec", "sampled_pts_sec", "all_provided_frames_reviewed"}
            and scope["all_provided_frames_reviewed"] is True, "raw semantic review observation scope changed")
    window = original["window"]; observation = original["actual_observation"]
    for key in ("window_pts_start_sec", "window_pts_end_exclusive_sec"):
        require(type(scope[key]) in (int, float) and math.isfinite(scope[key]) and abs(scope[key] - window[key]) <= 1e-6,
                "raw semantic review window extent differs")
    points = scope["sampled_pts_sec"]
    require(isinstance(points, list) and len(points) == len(observation["actual_pts_sec"]) and
            all(type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= 1e-6 for a, b in zip(points, observation["actual_pts_sec"])),
            "raw semantic review did not observe same actual PTS")
    require(item.get("parsed_response") == value and item.get("source_frame_pixel_sha256") == observation["frame_pixel_sha256"] and
            item.get("source_frame_ordinals") == observation["source_frame_ordinals"] and item.get("actual_pts_sec") == observation["actual_pts_sec"],
            "semantic review raw/frame identity differs from teacher observation")


def verify_semantic(review, validation_sha, file_hashes, eligible, records):
    require(review.get("schema") == "aic_automated_weak_semantic_review_v1" and
            review.get("status") == "PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW" and
            review.get("mode") == "AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH" and
            review.get("manual_ground_truth") is False and review.get("confirm_opened") is False and
            review.get("contest_assets_opened") is False, "STOP_T_SEMANTIC_REVIEW_REQUIRED")
    require(review.get("validation_receipt_sha256") == validation_sha and review.get("files") == file_hashes,
            "semantic review does not bind actual supervision files")
    for key in ("positive_reviewed", "explicit_empty_reviewed", "multisegment_and_boundary_reviewed_without_fabrication"):
        require(review.get(key) is True, "semantic supervision gate missing: " + key)
    expected = {r["teacher_record_sha256"] for r in eligible}
    require(set(review.get("reviewed_teacher_record_sha256", [])) == expected, "eligible semantics not exhaustively reviewed")
    raw_path = bound(review["raw_review_receipts"])
    raw = rows(raw_path)
    indexed = {r.get("teacher_record_sha256"): r for r in raw}
    require(len(indexed) == len(raw) and expected <= set(indexed), "missing/duplicate real semantic reviews")
    for digest in expected:
        item = indexed[digest]
        require(item.get("window_id") == records[digest]["window_id"] and
                item.get("review_status") == "PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW" and
                item.get("all_provided_frames_reviewed") is True and item.get("uncertain") is False and
                item.get("semantics_consistent") is True and isinstance(item.get("reason"), str) and item["reason"].strip() and
                item.get("reviewer_model_id") == "Qwen/Qwen3-VL-32B-Instruct" and
                isinstance(item.get("raw_response"), str) and item["raw_response"].strip(),
                "STOP_T_UNEXPLAINABLE_OR_UNCERTAIN_SEMANTIC_REVIEW")
        require(item.get("raw_response_sha256") == hashlib.sha256(item["raw_response"].encode()).hexdigest(),
                "semantic review raw response not bound")
        validate_raw_semantic(item, records[digest])
    return raw_path


def owns(path, run):
    """All student stages must stay under this independent version, not v1."""
    return Path(run).resolve() / Path(__file__).resolve().parent.name in Path(path).resolve().parents


def admit(args):
    run = Path(args.run_dir).resolve(strict=True)
    labels = Path(args.labels_dir).resolve(strict=True)
    out = Path(args.out_dir).resolve()
    require(owns(out, run) and not out.exists(), "fresh owned output directory required")
    config_path = Path(args.config).resolve(strict=True)
    config = read(config_path)
    require(config.get("schema") == "aic_t_student_config_v1" and config.get("authorized") is True and
            config.get("formal_C_BCE_admitted") is False and config.get("official_upload_authorized") is False,
            "student execution authority/scope missing")
    require(config.get("input_contract") == INPUT_CONTRACT, "T train/dev/production input contract differs")
    opt = config["optimization"]
    expected = {"lr": 1e-5, "optimizer": "AdamW", "betas": [0.9, 0.999], "eps": 1e-8,
                "weight_decay": 0.0, "grad_clip_norm": 1.0, "effective_batch_windows": 16,
                "microbatch_windows": 1, "gradient_accumulation_steps": 16, "max_epochs": 3,
                "smoke_update_limit": 20, "seed": 20261007, "precision": "bf16", "attn_implementation": "sdpa",
                "gradient_checkpointing_use_reentrant": False}
    require(opt == expected, "frozen student optimization recipe changed")
    require(config.get("dev_stop_rule") == {"all_selected_fraction": 0.99, "widespread_degraded_group_fraction": 0.75,
                "widespread_macro_f1_drop": 0.05}, "undeclared developer stop rule")
    lock_path = bound(config["source_lock"])
    lock = read(lock_path)
    files = lock.get("files", {})
    require(files and isinstance(files, dict), "source lock files missing")
    def locked(path):
        absolute = str(Path(path).resolve(strict=True))
        require(absolute in files and sha(absolute) == files[absolute], "source helper outside dynamic source lock: " + absolute)
    for relative in REQUIRED_HELPERS:
        locked(run / relative)
    locked(__file__)
    for path, digest in files.items():
        require(sha(path) == digest, "source lock changed: " + path)
    helper_paths(run)
    import sft_contract as old
    validation_path = bound(config["data"]["validation_receipt"])
    require(validation_path == labels / "validation_receipt.json", "labels directory/validation reference differs")
    validation = read(validation_path)
    require(validation.get("schema") == "aic_complete_window_validation_receipt_v1" and
            validation.get("weak_teacher_only") is True and validation.get("confirm_opened") is False and
            validation.get("contest_assets_opened") is False and validation.get("unlabelled_windows_never_converted_to_empty") is True,
            "non-test weak supervision validation required")
    hashes = {name: sha(labels / name) for name in ("eligible_train.jsonl", "eligible_dev.jsonl", "validated_records.jsonl")}
    require(validation.get("files") == hashes, "eligible/raw validated supervision bytes changed")
    eligible = {split: rows(labels / ("eligible_" + split + ".jsonl")) for split in ("train", "dev")}
    validate_isolation(eligible["train"], eligible["dev"])
    approved_paths = {}
    for split in ("train", "dev"):
        ref = config["data"]["approved_" + split + "_manifest"]
        require(ref["sha256"] == APPROVED_MANIFEST_SHA[split], "original approved split registry changed")
        path = bound(ref); approved_paths[split] = path
        validate_lineage(eligible[split], rows(path), split)
    validator = load(run / "teacher_student_autopilot_v5/supervision/validate_teacher.py", "t_frozen_teacher_validator")
    validator.HERE = run / "teacher_student_autopilot_v5/supervision"
    actual_records = rows(labels / "validated_records.jsonl")
    records = {record_sha(r): r for r in actual_records}
    require(len(records) == len(actual_records), "duplicate validated record")
    sources = {}
    for split, targets in eligible.items():
        for target in targets:
            require(target.get("schema") == "aic_complete_window_sft_target_v1", "foreign target schema")
            original = records.get(target.get("teacher_record_sha256"))
            require(original is not None and original.get("status") == "PASS_WEAK_COMPLETE_WINDOW_TARGET" and
                    original.get("sft_eligible") is True and original.get("uncertain") is False and
                    original.get("label_status") == "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH", "target lacks eligible actual teacher record")
            require(original["window"] == target["window"] and original["target_json"] == target["target_json"] and
                    original["explicit_no_highlight"] == target["explicit_no_highlight"], "target projection differs from reviewed teacher")
            w, obs = original["window"], original["actual_observation"]
            validator.validate_window(w); validator.validate_observation(w, obs)
            validator.validate_teacher(original["teacher"], validator.prompt_for(w, obs))
            response = validator.strict_json(original["raw_answer"])
            validator.validate_response(w, obs, response)
            require(response == original["parsed_answer"] and original["split"] == split, "raw response differs from validator projection")
            from contracts import answer_string
            parsed = json.loads(target["target_json"])["segments"]
            require(parsed == [[s["start_sec"], s["end_sec"]] for s in response["retained_segments"]] and
                    target["explicit_no_highlight"] == response["explicit_no_highlight"],
                    "raw teacher answer/interval-only target projection differs")
            answer_string(parsed, w["window_duration_sec"], allow_empty=True)
            source = Path(w["source_path"]).resolve(strict=True)
            media_root = Path("/home/inspur/aic_video_data/videos").resolve(strict=True)
            require(media_root in source.parents and source.is_file(), "resolved source escapes approved media root")
            digest = w["source_sha256"]
            require(str(source) not in sources or sources[str(source)] == digest, "inconsistent media SHA")
            sources[str(source)] = digest
    for split, targets in eligible.items():
        require(any(t["explicit_no_highlight"] for t in targets) and any(not t["explicit_no_highlight"] for t in targets),
                "STOP_T_NEED_EXPLAINABLE_NATURAL_POSITIVE_AND_EXPLICIT_EMPTY_" + split.upper())
    review_path = bound(config["data"]["semantic_review_receipt"])
    raw_review_path = verify_semantic(read(review_path), sha(validation_path), hashes,
                                     eligible["train"] + eligible["dev"], records)
    model = config["model"]
    require(model.get("base_id") == "Qwen/Qwen3-VL-8B-Instruct" and model.get("base_revision") == REVISION and
            Path(model["base_model_dir"]).resolve() == run / "models/Qwen3-VL-8B-Instruct" and
            Path(model["initial_adapter_dir"]).resolve() == run / "temporal_sft8b_full_v1/train_01/adapter" and
            model.get("initial_adapter_model_sha256") == INITIAL_SHA and model.get("lora_rank") == 16 and
            model.get("lora_alpha") == 32 and model.get("lora_dropout") == .05,
            "pinned B continuation identity changed")
    initial = Path(model["initial_adapter_dir"])
    require(sha(initial / "adapter_model.safetensors") == INITIAL_SHA and
            sha(initial / "adapter_config.json") == model["initial_adapter_config_sha256"], "B adapter bytes changed")
    initial_recipe = read(initial / "adapter_config.json")
    require(initial_recipe["r"] == 16 and initial_recipe["lora_alpha"] == 32 and initial_recipe["lora_dropout"] == .05 and
            initial_recipe["bias"] == "none" and initial_recipe["modules_to_save"] is None, "initial B LoRA recipe changed")
    model_receipt = bound(model["model_receipt"])
    old.verify_model_receipt(Path(model["base_model_dir"]), read(model_receipt))
    batches = schedule(len(eligible["train"]))
    for path, digest in sources.items():
        require(sha(path) == digest, "source video changed: " + path)
        st = Path(path).stat()
        _VERIFIED_SOURCE_STATS[path] = (digest, st.st_size, st.st_mtime_ns)
    authorities = {str(p): sha(p) for p in (config_path, lock_path, validation_path, review_path, raw_review_path, model_receipt)}
    authorities.update({str(p): sha(p) for p in approved_paths.values()})
    authorities.update({str(initial / name): sha(initial / name) for name in ("adapter_model.safetensors", "adapter_config.json")})
    authorities.update({str(labels / name): digest for name, digest in hashes.items()})
    return dict(run=run, out=out, config=config, config_path=config_path, files=files, authorities=authorities,
                targets=eligible, records=records, sources=sources, batches=batches)


def decode_window(window, observation=None):
    """Public sequential T decoder, with optional teacher-observation equality.

    Return (numpy THWC RGB, video_metadata, exact_native_pts_plan, evidence).
    This function also handles contest windows when called by the separately
    admitted production job; training never manufactures such a window.
    """
    import av
    import numpy as np
    w = window
    ids, pts = w["planned_source_frame_ordinals"], w["planned_actual_pts_sec"]
    require(ids and len(ids) == len(pts) <= 64 and ids == sorted(set(ids)) and
            all(type(i) is int and i >= 0 for i in ids) and all(math.isfinite(t) for t in pts), "invalid T frame/PTS plan")
    if "eligible_source_frame_count" in w:
        require(ids == floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"]), "T sampling is not registered integer-floor rule")
    before = Path(w["source_path"]).stat()
    key = str(Path(w["source_path"]).resolve(strict=True))
    signature = (w["source_sha256"], before.st_size, before.st_mtime_ns)
    if _VERIFIED_SOURCE_STATS.get(key) != signature:
        require(sha(w["source_path"]) == w["source_sha256"], "T source byte identity changed")
        _VERIFIED_SOURCE_STATS[key] = signature
    frames, actual_pts, pixels = [], [], []
    with av.open(w["source_path"]) as container:
        require(len(container.streams.video) == 1, "ambiguous source video stream")
        stream = container.streams.video[0]
        rate = stream.average_rate
        require(rate is not None and float(rate) > 0, "actual source FPS unavailable")
        if observation is not None:
            require(observation["fps_num"] == rate.numerator and observation["fps_den"] == rate.denominator,
                    "student/teacher source average FPS metadata differs")
        wanted = iter(ids); current = next(wanted, None)
        for ordinal, frame in enumerate(container.decode(stream)):
            if current is None:
                break
            if ordinal != current:
                continue
            require(frame.pts is not None and frame.time_base is not None, "actual source frame PTS missing")
            point = float(frame.pts * frame.time_base)
            require(abs(point - pts[len(frames)]) <= 1e-6, "actual decoded ordinal PTS differs from teacher observation")
            image = frame.to_ndarray(format="rgb24")
            require(image.ndim == 3 and image.shape[-1] == 3, "source RGB geometry changed")
            if "height" in w and "width" in w:
                require(image.shape[:2] == (w["height"], w["width"]), "registered source geometry changed")
            digest = hashlib.sha256(image.tobytes(order="C")).hexdigest()
            if observation is not None:
                require(digest == observation["frame_pixel_sha256"][len(frames)], "student/teacher frame pixel SHA differs")
            frames.append(image); actual_pts.append(point); pixels.append(digest)
            current = next(wanted, None)
    after = Path(w["source_path"]).stat()
    require(len(frames) == len(ids) and (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            "source changed or a planned frame was not decoded")
    arr = np.stack(frames)
    plan = dict(source_frame_ids=ids, source_relative_pts=actual_pts, window_start=w["window_pts_start_sec"])
    total = observation["source_total_frames"] if observation is not None else w.get("source_total_frames", w.get("n_frames"))
    require(type(total) is int and total > ids[-1], "actual full-source frame count must be declared")
    metadata = dict(fps=float(rate), frames_indices=ids, total_num_frames=total, video_backend="pyav")
    from native_frames import prepare_native_processor_input
    arr, metadata = prepare_native_processor_input(arr, metadata, plan)
    return arr, metadata, plan, dict(window_id=w["window_id"], source_sha256=w["source_sha256"],
        source_frame_ids=ids, actual_pts_sec=actual_pts, frame_pixel_sha256=pixels,
        native_source_clock=True, explicit_lone_frame_copy=len(ids) == 1,
        teacher_pixel_identity_checked=observation is not None, source_fps_num=rate.numerator, source_fps_den=rate.denominator)


def decode_observed(target, record, np=None):
    return decode_window(target["window"], record["actual_observation"])


def production_encode(processor, window, observation=None):
    """Public T encode shared by fixed dev and full contest T inference."""
    import torch
    from engine import prompt_for
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    arr, metadata, plan, decoded = decode_window(window, observation)
    with exact_native_pts(processor, plan, metadata["fps"]) as native:
        encoded = encode(processor, text=[prompt_for(processor, True)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**decoded, native_processor_identity=native, **identity(processor, encoded, len(arr)))


def production_generate(model, processor, window, encoded, details, candidates=None):
    from engine import generate_window
    from constrained_json import ascii_token_candidates
    if candidates is None:
        candidates = ascii_token_candidates(processor.tokenizer)
    # Output remains window-local; the controller adds source-global start for packaging.
    return generate_window(model, processor, encoded, details, 0, window["window_duration_sec"], candidates, True)


def encode_example(processor, target, record, torch, np):
    from training_target import build_target, from_teacher_record
    from engine import prompt_for
    from video_contract import identity
    arr, metadata, plan, decoded = decode_observed(target, record, np)
    video = torch.from_numpy(arr).permute(0, 3, 1, 2)
    encoded, mask = build_target(processor, prompt_for(processor, True), video, metadata,
        from_teacher_record(record), target["window"]["window_duration_sec"], VIDEO_SIZE,
        max_input=16384, native_plan=plan, source_fps=metadata["fps"])
    return encoded, dict(**decoded, assistant_mask=mask, input_identity=identity(processor, encoded, len(arr)))


def encode_dev(processor, target, record, torch, np):
    return production_encode(processor, target["window"], record["actual_observation"])


def union(segments):
    result = []
    for start, end in sorted(segments):
        if not result or start > result[-1][1]:
            result.append([start, end])
        else:
            result[-1][1] = max(end, result[-1][1])
    return result


def temporal_stats(pred, truth):
    p, g = union(pred), union(truth)
    ps, gs = sum(b - a for a, b in p), sum(b - a for a, b in g)
    overlap = sum(max(0, min(b, d) - max(a, c)) for a, b in p for c, d in g)
    return dict(f1=2 * overlap / (ps + gs) if ps + gs else 1.0,
        precision=overlap / ps if ps else float(gs == 0), recall=overlap / gs if gs else float(ps == 0),
        pred_seconds=ps, truth_seconds=gs, intersection_seconds=overlap)


def bootstrap(values, seed=20261007, draws=10000):
    rng = random.Random(seed)
    sims = sorted(statistics.mean(rng.choice(values) for _ in values) for _ in range(draws))
    return [sims[int(.025 * draws)], sims[int(.975 * draws)]]


def prefix_resume_position(batches, completed_update, report):
    """Persist work pending *after* the optimizer update, including epoch dev."""
    require(0 < completed_update <= len(batches), "invalid prefix data position")
    batch = batches[completed_update - 1]
    next_batch = batches[completed_update] if completed_update < len(batches) else None
    return dict(completed_update=completed_update, next_schedule_index=completed_update,
        completed_epoch_checkpoints=copy.deepcopy(report.get("checkpoints", [])),
        completed_epoch_devmetrics=copy.deepcopy(report.get("devmetrics", [])),
        current_epoch=batch["epoch"], current_epoch_last_batch=bool(batch["epoch_last"]),
        pending_phase="EPOCH_END_CHECKPOINT_AND_DEV_PENDING" if batch["epoch_last"] else "NEXT_TRAIN_BATCH",
        pending_epoch_end=batch["epoch"] if batch["epoch_last"] else None,
        next_epoch=next_batch["epoch"] if next_batch else None,
        report_snapshot=copy.deepcopy(report), entire_schedule=copy.deepcopy(batches))


def rng_snapshot(torch, np, *, cuda=True):
    return dict(python_rng=random.getstate(), numpy_rng=np.random.get_state(),
        torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state_all() if cuda else [])


def assert_tree_equal(expected, actual, torch, np, location="state"):
    """Compare real checkpoint tensor bytes/dtypes and Python/NumPy metadata."""
    if isinstance(expected, torch.Tensor):
        require(isinstance(actual, torch.Tensor) and expected.dtype == actual.dtype and
                expected.shape == actual.shape and torch.equal(expected.detach().cpu(), actual.detach().cpu()),
                "checkpoint tensor roundtrip mismatch: " + location)
    elif isinstance(expected, np.ndarray):
        require(isinstance(actual, np.ndarray) and expected.dtype == actual.dtype and
                expected.shape == actual.shape and np.array_equal(expected, actual),
                "checkpoint NumPy roundtrip mismatch: " + location)
    elif isinstance(expected, dict):
        require(isinstance(actual, dict) and set(expected) == set(actual), "checkpoint mapping mismatch: " + location)
        for key in expected:
            assert_tree_equal(expected[key], actual[key], torch, np, location + "/" + str(key))
    elif isinstance(expected, (list, tuple)):
        require(type(expected) is type(actual) and len(expected) == len(actual), "checkpoint sequence mismatch: " + location)
        for index, (left, right) in enumerate(zip(expected, actual)):
            assert_tree_equal(left, right, torch, np, location + "/" + str(index))
    else:
        require(type(expected) is type(actual) and expected == actual, "checkpoint scalar mismatch: " + location)


def trusted_state_roundtrip(path, expected, optimizer, trainable, torch, np, *, cuda=True):
    """Read this job's just-written state without replacing active objects/RNG."""
    before_rng = rng_snapshot(torch, np, cuda=cuda)
    assert_tree_equal({key: expected[key] for key in before_rng}, before_rng, torch, np, "saved_current_rng")
    optimizer_identity = id(optimizer)
    parameter_ids = [id(p) for _, p in trainable]
    # It contains Python/NumPy RNG structures; only this SHA-bound own file is
    # trusted. Loading it on CPU avoids a second CUDA optimizer allocation.
    loaded = torch.load(path, map_location="cpu", weights_only=False)
    assert_tree_equal(expected, loaded, torch, np)
    assert_tree_equal(loaded["optimizer"], optimizer.state_dict(), torch, np, "active_optimizer")
    current = {name: p.detach().cpu() for name, p in trainable}
    assert_tree_equal(loaded["lora"], current, torch, np, "active_lora")
    assert_tree_equal(before_rng, rng_snapshot(torch, np, cuda=cuda), torch, np, "unchanged_active_rng")
    require(id(optimizer) == optimizer_identity and [id(p) for _, p in trainable] == parameter_ids,
            "prefix validation replaced active optimizer/parameters")
    return dict(status="PASS_TRUSTED_PREFIX_STATE_ROUNDTRIP", state_sha256=sha(path),
        optimizer_tensor_metadata_and_bytes_equal=True, lora_tensor_metadata_and_bytes_equal=True,
        python_numpy_torch_cuda_rng_equal=True, schedule_and_pending_epoch_state_equal=True,
        active_optimizer_reference_unchanged=True, active_parameter_references_unchanged=True,
        active_rng_unchanged=True, cuda_rng_checked=cuda, loaded_on="cpu", optimizer_updates_performed=0)


def prefix_cpu_reload(args):
    """Independent CPU process; cannot alter the active CUDA model/RNG."""
    run = Path(args.run_dir).resolve(strict=True)
    helper_paths(run)
    adapter = Path(args.prefix_adapter).resolve(strict=True)
    require(owns(adapter, run), "prefix adapter outside owned run")
    config = read(args.config)
    bound(config["source_lock"])
    for path, digest in read(config["source_lock"]["path"])["files"].items():
        require(sha(path) == digest, "prefix CPU reload source changed")
    require(sha(adapter / "adapter_model.safetensors") == args.expected_adapter_sha and
            sha(adapter / "adapter_config.json") == args.expected_adapter_config_sha, "prefix adapter changed before CPU reload")
    import torch
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    from safetensors.torch import load_file
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "independent adapter reload must be CPU-only")
    base = Qwen3VLForConditionalGeneration.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
        local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cpu"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    model = PeftModel.from_pretrained(base, adapter, is_trainable=False)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    inventory = sum(p.numel() for _, p in unique_parameters(model))
    require(inventory == 8782459120, "independent prefix model parameter inventory differs")
    targets = {name.removeprefix("base_model.model.") for name, module in model.named_modules()
               if hasattr(module, "lora_A") and "default" in module.lora_A}
    expected_targets = {f"model.language_model.layers.{i}.self_attn.{proj}" for i in range(36)
                        for proj in ("q_proj", "k_proj", "v_proj", "o_proj")}
    require(targets == expected_targets, "independent prefix LoRA target modules differ")
    saved = load_file(str(adapter / "adapter_model.safetensors"))
    actual = {name.replace(".default.", "."): p.detach().cpu() for name, p in unique_parameters(model) if "lora_" in name}
    require(len(actual) == 288 and set(actual) == set(saved) and all(
        actual[name].dtype == saved[name].dtype and torch.equal(actual[name], saved[name]) for name in actual),
        "independent prefix reload tensor bytes differ")
    frozen = canonical_frozen_hash(model, torch)
    with model.disable_adapter():
        adapter_off = canonical_frozen_hash(model, torch)
    require(frozen == adapter_off and frozen["sha256"] == args.expected_base_sha,
            "independent prefix CPU reload frozen base/vision differs")
    write(args.verification_report, dict(status="PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD",
        adapter_dir=str(adapter), adapter_model_sha256=args.expected_adapter_sha,
        adapter_config_sha256=args.expected_adapter_config_sha, logical_parameters=inventory,
        language_target_modules=len(targets), lora_tensors=len(actual), base_frozen=frozen, adapter_off=adapter_off,
        optimizer_updates=0, device="cpu", active_training_objects_accessed=False,
        checked_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    return 0


def verify_prefix_adapter_in_child(contract, adapter, model, trainable, frozen, torch, np):
    import psutil
    from train_sft import unique_parameters
    frozen_bytes = sum(p.numel() * p.element_size() for name, p in unique_parameters(model) if "lora_" not in name)
    lora_bytes = sum(p.numel() * p.element_size() for _, p in trainable)
    # Fresh CPU base plus PEFT/saved/actual adapter buffers. This estimate is
    # computed from actual tensors, never a fixed RAM quota or admission line.
    estimated_additional_bytes = frozen_bytes + 4 * lora_bytes
    available = psutil.virtual_memory().available
    require(available >= estimated_additional_bytes, "STOP_T_PREFIX_RELOAD_ACTUAL_RAM_CAPACITY_INSUFFICIENT")
    before_rng = rng_snapshot(torch, np)
    optimizer_parameters = [id(p) for _, p in trainable]
    result_path = contract["out"] / "prefix20_adapter_reload.json"
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "verify-prefix-adapter",
        "--run-dir", str(contract["run"]), "--config", str(contract["config_path"]),
        "--prefix-adapter", str(adapter), "--expected-adapter-sha", sha(adapter / "adapter_model.safetensors"),
        "--expected-adapter-config-sha", sha(adapter / "adapter_config.json"),
        "--expected-base-sha", frozen["sha256"], "--verification-report", str(result_path)]
    with (contract["out"] / "prefix20_adapter_reload.log").open("x", encoding="utf-8") as log:
        subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = read(result_path)
    require(result.get("status") == "PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD", "prefix CPU reload did not pass")
    assert_tree_equal(before_rng, rng_snapshot(torch, np), torch, np, "post_child_active_rng")
    require(optimizer_parameters == [id(p) for _, p in trainable], "CPU child replaced active training parameters")
    result.update(actual_ram_available_bytes=available, estimated_additional_cpu_bytes=estimated_additional_bytes,
        active_rng_unchanged=True, active_parameter_references_unchanged=True,
        verification_process="INDEPENDENT_CPU_SUBPROCESS_NO_ACTIVE_MODEL_MUTATION")
    write(result_path, result)
    return result


def dev_failure(summary, baseline, rule):
    if summary["legal_empty_windows"] == summary["windows"]:
        return "STOP_T_SYSTEMATIC_ALL_EMPTY_DEV"
    if summary["all_selected_windows"] == summary["windows"]:
        return "STOP_T_SYSTEMATIC_ALL_SELECTED_DEV"
    if baseline is not None:
        groups = summary["group_f1"]
        fraction = sum(groups[g] < baseline["group_f1"][g] for g in groups) / len(groups)
        if fraction >= rule["widespread_degraded_group_fraction"] and baseline["video_macro_f1"] - summary["video_macro_f1"] >= rule["widespread_macro_f1_drop"]:
            return "STOP_T_WIDESPREAD_OPEN_DEV_DEGRADATION"
    return None


def evaluate(model, processor, contract, out, name, torch, np):
    from constrained_json import ascii_token_candidates
    model.eval(); model.config.use_cache = True
    candidates = ascii_token_candidates(processor.tokenizer)
    values = []
    started = time.monotonic()
    with (out / (name + ".jsonl")).open("x", encoding="utf-8") as stream:
        for target in contract["targets"]["dev"]:
            w = target["window"]; record = contract["records"][target["teacher_record_sha256"]]
            encoded, details = encode_dev(processor, target, record, torch, np)
            result = production_generate(model, processor, w, encoded, details, candidates)
            # A parse/inference failure blocks this run; it never receives an [] score.
            stream.write(json.dumps(dict(window_id=w["window_id"], result=result), ensure_ascii=False) + "\n"); stream.flush()
            require(result["output_valid"], "STOP_T_DEV_PARSE_OR_INFERENCE_FAILURE")
            values.append(dict(window_id=w["window_id"], youtube_id=w["youtube_id"], source_path=w["source_path"],
                duration=w["window_duration_sec"], pred=result["parsed_segments"],
                truth=json.loads(target["target_json"])["segments"], status=result["status"]))
            del encoded
    videos = {}
    for value in values:
        video = videos.setdefault(value["source_path"], dict(youtube_id=value["youtube_id"], pred=[], truth=[], duration=0))
        # Each selected source has one natural window. Fail if later manifests introduce more without global clocks.
        require(not video["duration"], "multiple windows/video require a separately declared global-time metric")
        video.update(pred=value["pred"], truth=value["truth"], duration=value["duration"])
    scored = [{**v, "metrics": temporal_stats(v["pred"], v["truth"])} for v in videos.values()]
    groups = sorted({v["youtube_id"] for v in scored})
    group_f1 = {g: statistics.mean(v["metrics"]["f1"] for v in scored if v["youtube_id"] == g) for g in groups}
    result = dict(name=name, windows=len(values), videos=len(scored), groups=len(groups), group_f1=group_f1,
        video_macro_f1=statistics.mean(v["metrics"]["f1"] for v in scored), group_bootstrap_ci95=bootstrap(list(group_f1.values())),
        parse_failures=0, inference_failures=0, legal_empty_windows=sum(not v["pred"] for v in values),
        all_selected_windows=sum(temporal_stats(v["pred"], v["truth"])["pred_seconds"] / v["duration"] >= .99 for v in values),
        local_metric_role="WEAK_COMPLETE_WINDOW_DEVELOPER_SELECTION_NOT_OFFICIAL_SCORE",
        confirm_opened=False, contest_assets_opened=False, seconds=time.monotonic() - started,
        same_input_contract=INPUT_CONTRACT, production_generation_function="next_round_v1.engine.generate_window")
    write(out / (name + ".metrics.json"), result)
    model.config.use_cache = False; model.train()
    for module_name, module in model.named_modules():
        if module_name.endswith(".visual"):
            module.eval()
    return result


def execute(contract):
    out = contract["out"]; out.mkdir(parents=True)
    config = contract["config"]
    report = dict(status="RUNNING_T_STUDENT", schema="aic_t_student_completion_v1", optimizer_steps=0,
        backward_examples=0, prefix_updates=0, total_planned_updates=len(contract["batches"]),
        config_sha256=sha(contract["config_path"]), quality_claim=False, official_score=None,
        confirm_opened=False, contest_assets_opened=False, formal_C_BCE_admitted=False,
        input_contract=INPUT_CONTRACT, updates=[], devmetrics=[], checkpoints=[],
        teacher_truth_status="AUTOMATED_REVIEWED_WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH")
    started = time.monotonic(); write(out / "progress.json", report)
    try:
        import sft_contract as old
        old.verify_live_gpu_reservation()
        import numpy as np
        import torch
        import transformers
        import peft
        from peft import PeftModel
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        from train_sft import unique_parameters, gradient_evidence
        from verify_saved_smoke import canonical_frozen_hash
        require(transformers.__version__ == "4.57.1" and peft.__version__ == "0.17.1" and torch.cuda.is_available(),
                "pinned CUDA training runtime required")
        seed = config["optimization"]["seed"]
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        base = Qwen3VLForConditionalGeneration.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
            low_cpu_mem_usage=True, attn_implementation="sdpa")
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        model = PeftModel.from_pretrained(base, config["model"]["initial_adapter_dir"], is_trainable=True)
        trainable = [(name, p) for name, p in unique_parameters(model) if p.requires_grad]
        old.validate_trainable_names([name for name, _ in trainable])
        require(len(trainable) == 288 and sum(p.numel() for _, p in unique_parameters(model)) == 8782459120,
                "student logical parameter/LoRA inventory differs")
        targets = {name.removeprefix("base_model.model.") for name, module in model.named_modules()
                   if hasattr(module, "lora_A") and "default" in module.lora_A}
        expected_targets = {f"model.language_model.layers.{i}.self_attn.{proj}" for i in range(36)
                            for proj in ("q_proj", "k_proj", "v_proj", "o_proj")}
        require(targets == expected_targets, "student LoRA target inventory changed")
        processor = AutoProcessor.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
            local_files_only=True, min_pixels=131072, max_pixels=131072)
        require(processor.video_processor.size == VIDEO_SIZE, "legacy-equivalent processor size changed")
        frozen = canonical_frozen_hash(model, torch)
        report["base_frozen_evidence"] = {"before": frozen}
        model.eval(); model.config.use_cache = False
        # Genuine eligible empty/positive forward CE establishes both target
        # semantics and masks before any optimizer update. No synthetic label.
        real_ce = {}
        for kind, empty in (("explicit_empty", True), ("positive", False)):
            target = next(t for t in contract["targets"]["train"] if t["explicit_no_highlight"] is empty)
            record = contract["records"][target["teacher_record_sha256"]]
            encoded, evidence = encode_example(processor, target, record, torch, np)
            encoded = {key: value.to("cuda:0") if hasattr(value, "to") else value for key, value in encoded.items()}
            with torch.inference_mode():
                loss = model(**encoded).loss
            require(loss is not None and bool(torch.isfinite(loss)), "real empty/positive assistant CE is missing/nonfinite")
            real_ce[kind] = dict(loss=float(loss), window_id=target["window"]["window_id"],
                teacher_record_sha256=target["teacher_record_sha256"], evidence=evidence, optimizer_updates=0)
            del encoded, loss
        report["real_assistant_ce_acceptance"] = real_ce
        # Input B developer baseline is evaluated once on the same new weak dev before updates.
        baseline = evaluate(model, processor, contract, out, "initial_B_dev", torch, np)
        report["initial_B_dev"] = baseline
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        optimizer = torch.optim.AdamW([p for _, p in trainable], lr=1e-5, betas=(.9, .999), eps=1e-8, weight_decay=0)
        before_lora = {name: p.detach().cpu().clone() for name, p in trainable}
        torch.cuda.reset_peak_memory_stats()
        with (out / "example_evidence.jsonl").open("x", encoding="utf-8") as evidence_stream:
            # This is a single schedule; there is no restart at update 20.
            for update, batch in enumerate(contract["batches"], 1):
                optimizer.zero_grad(set_to_none=True); losses = []
                for index in batch["indices"]:
                    target = contract["targets"]["train"][index]
                    record = contract["records"][target["teacher_record_sha256"]]
                    encoded, evidence = encode_example(processor, target, record, torch, np)
                    encoded = {key: value.to("cuda:0") if hasattr(value, "to") else value for key, value in encoded.items()}
                    result = model(**encoded)
                    require(result.loss is not None and bool(torch.isfinite(result.loss)), "missing/nonfinite assistant CE")
                    (result.loss / len(batch["indices"])).backward()
                    loss = float(result.loss.detach().cpu()); losses.append(loss)
                    report["backward_examples"] += 1
                    evidence.update(epoch=batch["epoch"], optimizer_update=update, loss=loss,
                        accumulation_denominator=len(batch["indices"]), teacher_record_sha256=target["teacher_record_sha256"])
                    evidence_stream.write(json.dumps(evidence, ensure_ascii=False) + "\n"); evidence_stream.flush()
                    del result, encoded
                grads = gradient_evidence(trainable, torch, update)
                norm = torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1)
                require(bool(torch.isfinite(norm)) and float(norm) > 0, "invalid LoRA gradient norm")
                optimizer.step()
                current = {name: p.detach().cpu().clone() for name, p in trainable}
                changed = sum(not torch.equal(current[name], before_lora[name]) for name in current)
                require(changed > 0, "LoRA unchanged after genuine optimizer update")
                before_lora = current
                report["optimizer_steps"] = update
                report["prefix_updates"] = min(update, 20)
                report["updates"].append(dict(update=update, epoch=batch["epoch"], mean_loss=statistics.mean(losses),
                    windows=len(losses), gradient_norm=float(norm), changed_lora_tensors=changed, gradient_evidence=grads))
                if update == 20:
                    prefix_frozen = canonical_frozen_hash(model, torch)
                    require(prefix_frozen == frozen, "frozen base/vision changed before update-20 gate")
                    state_path = out / "update20_state.pt"
                    prefix_adapter = out / "prefix_20" / "adapter"
                    before_save_rng = rng_snapshot(torch, np)
                    model.save_pretrained(prefix_adapter, safe_serialization=True)
                    prefix_recipe = read(prefix_adapter / "adapter_config.json")
                    require(prefix_recipe["r"] == 16 and prefix_recipe["lora_alpha"] == 32 and prefix_recipe["lora_dropout"] == .05 and
                            prefix_recipe["bias"] == "none" and prefix_recipe["modules_to_save"] is None, "prefix adapter scalar recipe changed")
                    assert_tree_equal(before_save_rng, rng_snapshot(torch, np), torch, np, "prefix_adapter_save_rng")
                    state = dict(schema="aic_t_prefix20_recovery_state_v2", optimizer=optimizer.state_dict(), lora=current,
                        optimizer_parameter_name_order=[name for name, _ in trainable],
                        data_config_sha256=report["config_sha256"], bound_authorities=contract["authorities"],
                        frozen_base_identity=frozen, prefix_adapter_dir=str(prefix_adapter),
                        prefix_adapter_model_sha256=sha(prefix_adapter / "adapter_model.safetensors"),
                        prefix_adapter_config_sha256=sha(prefix_adapter / "adapter_config.json"),
                        **rng_snapshot(torch, np), **prefix_resume_position(contract["batches"], 20, report))
                    torch.save(state, state_path)
                    roundtrip = trusted_state_roundtrip(state_path, state, optimizer, trainable, torch, np)
                    independent_reload = verify_prefix_adapter_in_child(contract, prefix_adapter, model, trainable, frozen, torch, np)
                    assert_tree_equal(state["optimizer"], optimizer.state_dict(), torch, np, "optimizer_after_independent_reload")
                    report["prefix_gate"] = dict(status="PASS_SAME_RUN_20_UPDATE_PREFIX", completed_updates=20,
                        state_path=str(state_path), state_sha256=sha(state_path), base_frozen=prefix_frozen,
                        same_optimizer_rng_data_position=True, extra_epochs_started=False,
                        state_roundtrip=roundtrip, independent_adapter_reload=independent_reload,
                        pending_phase=state["pending_phase"], pending_epoch_end=state["pending_epoch_end"],
                        completed_epoch_checkpoints=state["completed_epoch_checkpoints"])
                    write(out / "prefix20_gate.json", report["prefix_gate"])
                    del state
                if batch["epoch_last"]:
                    epoch = batch["epoch"]
                    checkpoint = out / f"epoch_{epoch}"; model.save_pretrained(checkpoint, safe_serialization=True)
                    saved = read(checkpoint / "adapter_config.json")
                    require(saved["r"] == 16 and saved["lora_alpha"] == 32 and saved["lora_dropout"] == .05 and
                            saved["bias"] == "none" and saved["modules_to_save"] is None, "saved student LoRA recipe changed")
                    metrics = evaluate(model, processor, contract, out, f"epoch_{epoch}_dev", torch, np)
                    checkpoint_record = dict(epoch=epoch, completed_updates=update, adapter_dir=str(checkpoint),
                        adapter_model_sha256=sha(checkpoint / "adapter_model.safetensors"),
                        adapter_config_sha256=sha(checkpoint / "adapter_config.json"), video_macro_f1=metrics["video_macro_f1"])
                    report["devmetrics"].append(metrics); report["checkpoints"].append(checkpoint_record)
                    failure = dev_failure(metrics, baseline, config["dev_stop_rule"])
                    require(failure is None, failure or "developer gate failed")
                report["wall_seconds"] = time.monotonic() - started
                write(out / "progress.json", report)
                print(json.dumps(dict(stage="T_TRAINING", updates=update, total=len(contract["batches"]),
                                      backward_examples=report["backward_examples"])), flush=True)
        require(report["prefix_updates"] == 20 and report["optimizer_steps"] == len(contract["batches"]) and
                report["backward_examples"] == 3 * len(contract["targets"]["train"]) and len(report["checkpoints"]) == 3,
                "incomplete same-run 3-epoch schedule")
        final_frozen = canonical_frozen_hash(model, torch)
        require(final_frozen == frozen, "frozen base/vision changed during student training")
        selected = max(report["checkpoints"], key=lambda v: (v["video_macro_f1"], -v["epoch"]))
        # Semantic reload uses real saved adapter bytes and module identities.
        trained_selected_path = Path(selected["adapter_dir"])
        del optimizer, before_lora, current, trainable
        plain = model.unload(); del model
        reloaded = PeftModel.from_pretrained(plain, trained_selected_path, is_trainable=False)
        for parameter in reloaded.parameters():
            parameter.requires_grad_(False)
        actual_targets = {name.removeprefix("base_model.model.") for name, module in reloaded.named_modules()
                          if hasattr(module, "lora_A") and "default" in module.lora_A}
        require(actual_targets == expected_targets, "selected adapter reload modules changed")
        from safetensors.torch import load_file
        saved_tensors = load_file(str(trained_selected_path / "adapter_model.safetensors"))
        actual = {name.replace(".default.", "."): p.detach().cpu() for name, p in unique_parameters(reloaded) if "lora_" in name}
        require(set(actual) == set(saved_tensors) and all(torch.equal(actual[n], saved_tensors[n]) and
                actual[n].dtype == saved_tensors[n].dtype for n in actual), "selected adapter reload tensor bytes differ")
        reload_frozen = canonical_frozen_hash(reloaded, torch)
        with reloaded.disable_adapter():
            adapter_off_frozen = canonical_frozen_hash(reloaded, torch)
        require(reload_frozen == adapter_off_frozen == frozen, "selected reload/adapter-off base bytes changed")
        for path, digest in {**contract["files"], **contract["authorities"], **contract["sources"]}.items():
            require(sha(path) == digest, "bound data/source/authority changed during training: " + path)
        report["base_frozen_evidence"].update(after=final_frozen, selected_reload=reload_frozen, adapter_off=adapter_off_frozen)
        report.update(status="PASS_TRAINED_SELECTED_STUDENT_ADAPTER", selected_adapter_dir=selected["adapter_dir"],
            selected_adapter_sha256=selected["adapter_model_sha256"], selected_adapter_config_sha256=selected["adapter_config_sha256"],
            selected_epoch=selected["epoch"], selected_video_macro_f1=selected["video_macro_f1"],
            selection_rule="MAX_WEAK_VIDEO_MACRO_TEMPORAL_F1_THEN_LOWER_EPOCH", prefix_completed_updates=20,
            total_updates=report["optimizer_steps"], base_frozen=True, vision_frozen=True, adapter_reload_succeeded=True,
            actual_logical_parameters=8782459120, peak_memory_allocated_mib=torch.cuda.max_memory_allocated() / 2**20,
            student_training_completed=True, T_production_inference_started=False, ZIP_delivered=False)
    except Exception as exc:
        report.update(status="STOP_T_STUDENT", failure_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
    report.update(wall_seconds=time.monotonic() - started, checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    write(out / "student_completion.json", report); write(out / "progress.json", report)
    return 0 if report["status"] == "PASS_TRAINED_SELECTED_STUDENT_ADAPTER" else 4


def main():
    if sys.argv[1:2] == ["verify-prefix-adapter"]:
        parser = argparse.ArgumentParser(description="Independent trusted prefix adapter CPU reload")
        for field in ("run-dir", "config", "prefix-adapter", "expected-adapter-sha", "expected-adapter-config-sha", "expected-base-sha", "verification-report"):
            parser.add_argument("--" + field, required=True)
        return prefix_cpu_reload(parser.parse_args(sys.argv[2:]))
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("run-dir", "labels-dir", "out-dir", "config"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        contract = admit(args)
    except Exception as exc:
        failure = dict(schema="aic_t_student_completion_v1", status="STOP_T_BEFORE_RUNTIME_IMPORTS",
            failure=type(exc).__name__ + ": " + str(exc), training_started=False, optimizer_steps=0,
            checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        # Preserve a concrete failure receipt without overwriting an older run.
        output = Path(args.out_dir).resolve()
        owner = Path(args.run_dir).resolve() / "teacher_student_autopilot_v5"
        if not args.check_only and owns(output, args.run_dir) and not output.exists():
            output.mkdir(parents=True); write(output / "student_completion.json", failure)
        print(json.dumps(failure), flush=True)
        return 3
    if args.check_only:
        print(json.dumps(dict(status="PASS_T_AUTHORITY_INPUT_AND_WEAK_SEMANTIC_ADMISSION",
            train=len(contract["targets"]["train"]), dev=len(contract["targets"]["dev"]),
            total_updates=len(contract["batches"]), training_started=False)), flush=True)
        return 0
    return execute(contract)


if __name__ == "__main__":
    raise SystemExit(main())
