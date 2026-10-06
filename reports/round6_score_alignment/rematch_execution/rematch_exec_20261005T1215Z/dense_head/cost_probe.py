#!/usr/bin/env python3
"""One fixed real non-test 32s cost probe; synthetic labels, never formal BCE."""
from __future__ import annotations

import argparse
from bisect import bisect_left
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import subprocess
import sys
import time
import traceback

from formal_contract import PINNED_REVISION, bound_json, require, sha256

MANIFEST_SHA256 = "7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a"
VIDEO_ID = "qvh_000056_9x16"
SOURCE_PATH = "/home/inspur/aic_video_data/videos/y/y9Whbu4J-cs_660.0_810.0.mp4"
SOURCE_SHA256 = "b255c19a7aec1f2544f700e25d0b721879f3fa23349349158581adacf78667bc"
MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"
RUN_ROOT = PurePosixPath("/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z")


def validate_config(config: dict):
    fixed = {"schema": "aic_dense_cost_run_v1", "model_id": MODEL_ID, "revision": PINNED_REVISION,
        "selected_video_id": VIDEO_ID, "selected_source_path": SOURCE_PATH,
        "selected_source_sha256": SOURCE_SHA256, "non_test_manifest_sha256": MANIFEST_SHA256,
        "window_start_pts": 0.0, "window_seconds": 32.0, "grid_seconds": 2.0,
        "max_frames": 64, "max_pixels": 131072, "updates": 3, "precision": "bf16",
        "attn_implementation": "sdpa", "lora_rank": 16, "lora_alpha": 32,
        "lora_dropout": 0.05, "gradient_checkpointing_use_reentrant": False,
        "optimizer": "AdamW", "weight_decay": 0.0, "scheduler": "constant",
        "label_status": "SYNTHETIC_ENGINEERING_ONLY", "save_checkpoint": False,
        "spatial_measurement": "RAW_BASE_RESTORATION_SIGNATURE_3_TOKENS_ONLY"}
    for name, value in fixed.items():
        require(config.get(name) == value and type(config.get(name)) is type(value), f"cost fixed recipe changed: {name}")
    for name in ("seed", "max_sequence_length"):
        require(type(config.get(name)) is int and config[name] > 0, f"invalid explicit cost {name}")
    require(type(config.get("decoder_threads")) is int and config["decoder_threads"] >= 0,
            "invalid cost decoder_threads (0 preserves Decord automatic selection)")
    for name in ("max_wall_seconds", "lr", "adam_eps", "grad_clip_norm", "decoder_pts_tolerance_seconds"):
        value = config.get(name)
        require(type(value) in (int, float) and math.isfinite(value) and value > 0, f"invalid explicit cost {name}")
    require(config["lr"] <= 1e-3 and config["decoder_pts_tolerance_seconds"] <= 1e-3, "cost LR/PTS bound changed")
    for name in ("adam_beta1", "adam_beta2"):
        require(type(config.get(name)) is float and 0 < config[name] < 1, f"invalid explicit cost {name}")
    for name in ("out_dir", "model_dir", "non_test_manifest", "ffprobe_path"):
        value = config.get(name)
        require(isinstance(value, str) and value, f"missing cost path: {name}")
        path = PurePosixPath(value)
        require(path.is_absolute() and ".." not in path.parts, f"unsafe cost path: {name}")
        if name != "ffprobe_path":
            require(RUN_ROOT in path.parents, f"cost {name} outside fixed execution directory")
    require(isinstance(config.get("run_id"), str) and config["run_id"] == PurePosixPath(config["out_dir"]).name,
            "cost run_id/output basename mismatch")
    extra = {"run_id", "seed", "decoder_threads", "max_sequence_length", "max_wall_seconds", "lr",
        "adam_eps", "grad_clip_norm", "decoder_pts_tolerance_seconds", "adam_beta1", "adam_beta2",
        "out_dir", "model_dir", "non_test_manifest", "ffprobe_path", "model_receipt"}
    require(set(config) == set(fixed) | extra, "unexpected/missing cost config fields; semantic label inputs forbidden")


def validate_admission(config_path: Path, admission: dict):
    require(admission.get("schema") == "aic_dense_cost_admission_v1"
            and admission.get("scope") == "ONE_FIXED_REAL_NONTEST_32S_SYNTHETIC_COST_ONLY"
            and admission.get("cost_probe_admitted") is True and admission.get("formal_c_bce_admitted") is False
            and admission.get("semantic_labels_read") is False and admission.get("contest_media_read") is False,
            "missing engineering-only cost admission; formal STOP remains")
    require(admission.get("config_sha256") == sha256(config_path), "cost config not frozen to admission")


def source_plan(config: dict, manifest_path: Path | None = None) -> tuple[dict, dict]:
    manifest = manifest_path or Path(config["non_test_manifest"])
    require(sha256(manifest) == MANIFEST_SHA256 == config["non_test_manifest_sha256"], "frozen non-test metadata manifest changed")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    require(data.get("kind") == "NONTEST_FROZEN8" and data.get("expected_count") == 8
            and len(data.get("records", [])) == 8, "not the fixed non-test eight source manifest")
    require(data.get("input_contract", {}).get("status") == "APPROVED_METADATA_ONLY"
            and data["input_contract"].get("contest_jsonl_values_used") is False, "non-test metadata permission missing")
    source = data["records"][0]
    require(source["video_id"] == VIDEO_ID == config["selected_video_id"]
            and source["source_path"] == SOURCE_PATH == config["selected_source_path"]
            and source["source_sha256"] == SOURCE_SHA256 == config["selected_source_sha256"], "fixed first source changed")
    require((source["n_frames"], source["fps_num"], source["fps_den"], source["width"], source["height"])
            == (3750, 25, 1, 534, 300), "fixed full-source metadata changed")
    roots = [PurePosixPath(root) for root in data["allowed_source_roots"]]
    path = PurePosixPath(source["source_path"])
    require(path.is_absolute() and ".." not in path.parts and any(root in path.parents for root in roots),
            "source path outside approved non-test media root")
    return source, {"status": "PLANNED_FIXED_SOURCE_ONLY", "manifest_sha256": MANIFEST_SHA256,
        "selection": "frozen first record; full source-relative [0,32); no labels/content selection",
        "source": source, "historical_a_short_scope_used": False, "exact_source_duration_not_yet_verified": True}


def parse_native_pts(source: dict, data: dict) -> dict:
    require(len(data.get("streams", [])) == 1, "ffprobe source timebase ambiguous")
    stream = data["streams"][0]
    base = Fraction(stream["time_base"])
    require(base > 0 and (stream["width"], stream["height"]) == (source["width"], source["height"]),
            "native source geometry/timebase differs from frozen identity")
    require(Fraction(stream["avg_frame_rate"]) == Fraction(source["fps_num"], source["fps_den"]),
            "native source metadata FPS differs; no processor metadata fabrication")
    frames = data.get("frames", [])
    require(len(frames) == source["n_frames"] and len(frames) >= 2, "native source frame count differs from frozen identity")
    require(all("best_effort_timestamp" in frame for frame in frames), "missing native frame PTS; avg-fps fallback forbidden")
    native = [int(frame["best_effort_timestamp"]) for frame in frames]
    exact = [value * base for value in native]
    require(all(a < b for a, b in zip(exact, exact[1:])) and exact[0] == 0,
            "source PTS not strictly monotone/zero-origin; fixed start=0 cannot be redefined")
    durations = [int(frame.get("pkt_duration", 0)) for frame in frames]
    require(all(d > 0 for d in durations), "native packet duration missing; no fps duration fabrication")
    ends = [pts + duration * base for pts, duration in zip(exact, durations)]
    require(ends[:-1] == exact[1:], "native frame durations do not form contiguous exact source spans")
    require(ends[-1] == 150, "fixed full source duration differs from 150s")
    selected = []
    for i in range(64):
        desired = Fraction(i, 2)
        pos = bisect_left(exact, desired)
        candidates = [j for j in (pos - 1, pos) if 0 <= j < len(exact)]
        selected.append(min(candidates, key=lambda j: (abs(exact[j] - desired), j)))
    require(selected == sorted(set(selected)) and all(0 <= exact[j] < 32 for j in selected),
            "64 exact-PTS nearest samples duplicated/outside [0,32)")
    return {"status": "PASS", "source_sha256": source["source_sha256"], "source_frame_ids": list(range(len(exact))),
        "frame_pts": [float(p) for p in exact], "frame_end_pts": [float(p) for p in ends],
        "native_frame_pts_ticks": native, "native_frame_duration_ticks": durations, "native_time_base": str(base),
        "source_avg_fps": float(Fraction(stream["avg_frame_rate"])), "actual_source_duration_rational": str(ends[-1]),
        "selected_frame_ids": selected, "selected_exact_pts_rational": [str(exact[j]) for j in selected],
        "selected_exact_end_pts_rational": [str(ends[j]) for j in selected],
        "clock": "ffprobe best_effort_timestamp * exact stream time_base; no FPS time inference"}


def native_pts_index(source: dict, ffprobe: str) -> dict:
    path = Path(source["source_path"])
    require(path.is_file() and sha256(path) == source["source_sha256"], "fixed source byte identity failed")
    process = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_frames", "-show_streams",
        "-show_entries", "stream=time_base,avg_frame_rate,width,height:frame=best_effort_timestamp,pkt_duration",
        "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return parse_native_pts(source, json.loads(process.stdout))


def synthetic_window(source: dict, index: dict, index_spec: dict) -> dict:
    grids = []
    for i in range(16):
        a, b = Fraction(2 * i), Fraction(2 * (i + 1))
        ids = [j for j, tick in enumerate(index["native_frame_pts_ticks"])
               if a <= tick * Fraction(index["native_time_base"]) < b]
        require(ids, "empty synthetic source grid")
        grids.append({"start_pts": float(a), "end_pts_exclusive": float(b), "source_frame_ids": ids,
            "known": True, "target": float(i % 2), "label_provenance": "SYNTHETIC_ENGINEERING_ONLY"})
    chosen = index["selected_frame_ids"]
    return {"window_id": source["video_id"] + "__cost_start0_32s", "source_group": source["source_group"],
        "source_path": source["source_path"], "source_sha256": source["source_sha256"], "pts_index": index_spec,
        "window_start_pts": 0.0, "window_end_pts": 32.0, "frame_ids": chosen,
        "exact_frame_pts": [index["frame_pts"][j] for j in chosen],
        "exact_frame_end_pts": [index["frame_end_pts"][j] for j in chosen], "grid": grids,
        "label_status": "SYNTHETIC_ENGINEERING_ONLY", "formal_training_eligible": False}


class TimedProcessor:
    """Instrumentation only: delegate exact-PTS override and the formal helper unchanged."""
    def __init__(self, processor):
        object.__setattr__(self, "processor", processor)
        object.__setattr__(self, "last_call_seconds", 0.0)

    def __getattr__(self, name):
        return getattr(self.processor, name)

    def __setattr__(self, name, value):
        if name in ("processor", "last_call_seconds"):
            object.__setattr__(self, name, value)
        else:
            setattr(self.processor, name, value)

    def __call__(self, *args, **kwargs):
        started = time.monotonic()
        value = self.processor(*args, **kwargs)
        self.last_call_seconds = time.monotonic() - started
        return value


def dump(path: Path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def prior_gate(admission: dict, metadata_root: Path | None = None) -> dict:
    spec = dict(admission.get("engineering_gate") or {})
    if metadata_root is not None:
        spec["path"] = str(metadata_root / "controller" / "probe8b_02_report.json")
    gate = bound_json(spec, "prior real 8B engineering gate")
    require(gate.get("status") == "PASS_REAL_8B_SYNTHETIC_ENGINEERING_ONLY", "prior real 8B core probe not passed")
    strict = gate.get("masked_label_invariance", {})
    require(strict.get("all_trainable_gradients_exact_equal") is True and strict.get("deterministic_algorithms") is True
            and strict.get("same_rng_and_encoded_inputs") is True
            and strict.get("backend") == "SDPBackend.MATH only; flash/efficient/cuDNN SDPA disabled",
            "prior exact UNKNOWN invariance gate missing; tolerance relaxation forbidden")
    require(gate.get("spatial_original_base_restoration", {}).get("last_token_logits_exact_equal") is True
            and gate["spatial_original_base_restoration"].get("greedy_tokens_exact_equal") is True,
            "prior adapter-off raw-base restoration gate missing")
    return {"status": gate["status"], "sha256": spec["sha256"], "strict_unknown_gate_reused": True,
            "strict_unknown_32s_rerun": False, "cost_default_sdpa_is_not_an_invariance_test": True}


def run(config: dict, report: dict, output: Path):
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run_started = time.monotonic()
    report["source_hashes_at_start"] = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")}
    def checkpoint(phase):
        report["phase"] = phase
        dump(output / "cost_probe_report.json", report)
    def wall_check():
        require(time.monotonic() - run_started < config["max_wall_seconds"], "cost wall stop reached")
    source, report["source_plan"] = source_plan(config)
    checkpoint("VERIFYING_REAL_SOURCE_PTS")
    started = time.monotonic()
    index = native_pts_index(source, config["ffprobe_path"])
    report["native_pts_and_source_hash_seconds"] = time.monotonic() - started
    index_path = output / "native_source_pts_index.json"
    dump(index_path, index)
    row = synthetic_window(source, index, {"path": str(index_path), "sha256": sha256(index_path)})
    dump(output / "synthetic_window.json", row)
    report["synthetic_label_contract"] = {"rule": "alternating 0/1 by grid index, unrelated to source content",
        "provenance": "SYNTHETIC_ENGINEERING_ONLY", "formal_training_eligible": False}
    report["sample_identity"] = {"frame_ids": row["frame_ids"], "source_pts_rational": index["selected_exact_pts_rational"],
        "source_end_pts_rational": index["selected_exact_end_pts_rational"], "source_sha256": SOURCE_SHA256,
        "index_sha256": sha256(index_path), "native_time_base": index["native_time_base"]}
    import numpy as np
    import torch
    import peft
    import transformers
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from dense_time import (DenseTimeModel, REVISION, UpdateCounters, accumulation_update, fingerprint_parameters,
                            language_targets, parameter_inventory, clear_model_cache)
    from probe_8b import capture_trainable, gradient_evidence, spatial_signature, verify_receipt
    from train_dense import prepare_window
    require(transformers.__version__ == "4.57.1" and peft.__version__ == "0.17.1", "unreviewed cost runtime")
    require(torch.cuda.is_available(), "cost requires controller-approved CUDA execution")
    report["started_runtime"] = True
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.set_device(0)
    torch.cuda.init()
    torch.cuda.manual_seed_all(config["seed"])
    import decord  # CUDA MUST be initialized first to avoid Decord random_device failure.
    report["environment"] = {"python": sys.version, "executable": sys.executable, "torch": torch.__version__,
        "transformers": transformers.__version__, "peft": peft.__version__, "decord": decord.__version__,
        "numpy": np.__version__, "cuda_device": torch.cuda.get_device_name(0)}
    report["model_receipt"] = verify_receipt(Path(config["model_dir"]), Path(config["model_receipt"]["path"]))
    checkpoint("LOADING_MODEL")
    wall_check()
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    base = Qwen3VLForConditionalGeneration.from_pretrained(config["model_dir"], revision=REVISION, local_files_only=True,
        torch_dtype=torch.bfloat16, device_map={"": "cuda:0"}, low_cpu_mem_usage=True, attn_implementation="sdpa")
    require(base.config.model_type == "qwen3_vl" and base.config.text_config.hidden_size == 4096, "wrong 8B architecture")
    for p in base.parameters():
        p.requires_grad_(False)
    base.config.use_cache = False
    torch.cuda.synchronize()
    report["model_load"] = {"seconds": time.monotonic() - started, "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved()}
    started = time.monotonic()
    processor = TimedProcessor(AutoProcessor.from_pretrained(config["model_dir"], revision=REVISION, local_files_only=True,
        min_pixels=config["max_pixels"], max_pixels=config["max_pixels"]))
    report["processor_load_seconds"] = time.monotonic() - started
    original_vocab = len(processor.tokenizer)
    stat = Path(SOURCE_PATH).stat()
    source_stat = (stat.st_size, stat.st_mtime_ns)
    decode_measurement = {}
    def decode(window, cfg, full_index):
        tick = time.monotonic()
        now = Path(SOURCE_PATH).stat()
        require((now.st_size, now.st_mtime_ns) == source_stat, "source changed during cost probe")
        reader = decord.VideoReader(SOURCE_PATH, ctx=decord.cpu(0), num_threads=cfg["decoder_threads"])
        require(len(reader) == len(full_index["frame_pts"]), "Decord source frame count mismatch")
        actual = reader.get_frame_timestamp(window["frame_ids"])
        actual = actual.asnumpy() if hasattr(actual, "asnumpy") else np.asarray(actual)
        expected = np.stack((window["exact_frame_pts"], window["exact_frame_end_pts"]), axis=1)
        require(actual.shape == expected.shape and np.isfinite(actual).all()
                and float(np.abs(actual - expected).max()) <= cfg["decoder_pts_tolerance_seconds"],
                "Decord selected IDs/PTS mismatch native ffprobe clock")
        pixels = reader.get_batch(window["frame_ids"]).asnumpy()
        require(pixels.shape == (64, source["height"], source["width"], 3) and pixels.dtype == np.uint8,
                "Decord cost pixel geometry/dtype mismatch")
        decode_measurement.update(decode_seconds=time.monotonic() - tick,
            max_pts_error_seconds=float(np.abs(actual - expected).max()))
        tick = time.monotonic()
        hashes = [hashlib.sha256(memoryview(frame)).hexdigest() for frame in pixels]
        decode_measurement["pixel_hash_seconds"] = time.monotonic() - tick
        if "rgb_uint8_sha256_per_frame" in report["sample_identity"]:
            require(report["sample_identity"]["rgb_uint8_sha256_per_frame"] == hashes, "decoded frame pixels changed across replays")
        report["sample_identity"]["rgb_uint8_sha256_per_frame"] = hashes
        return pixels, actual.tolist()
    def prepare():
        wall_check()
        torch.cuda.synchronize()
        tick = time.monotonic()
        encoded, positions, identity = prepare_window(processor, row, config, index, torch, decode)
        torch.cuda.synchronize()
        total = time.monotonic() - tick
        require(len(processor.tokenizer) == original_vocab and len(identity["query_positions"]) == 16, "vocabulary/query contract changed")
        timing = {**decode_measurement, "preprocess_seconds": processor.last_call_seconds,
            "prepare_total_seconds": total,
            "query_contract_and_transfer_seconds": total - decode_measurement["decode_seconds"]
                - decode_measurement["pixel_hash_seconds"] - processor.last_call_seconds}
        return encoded, positions, identity, timing
    def signature(encoded, label):
        wall_check()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        tick = time.monotonic()
        value = spatial_signature(base, encoded, torch)
        torch.cuda.synchronize()
        report.setdefault("space_signatures", {})[label] = {"seconds": time.monotonic() - tick,
            "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(), "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved(),
            "new_tokens": 3, "prompt": "same dense-window query prompt; restoration signature only",
            "production_crop_throughput_established": False}
        return value
    base.eval()
    checkpoint("PREPARING_REFERENCE")
    encoded, positions, identity, timing = prepare()
    report["initial_prepare"] = {"timing": timing, "identity": identity}
    reference = signature(encoded, "raw_base_before_lora")
    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", target_modules=language_targets(base),
                      modules_to_save=None, task_type="CAUSAL_LM")
    backbone = get_peft_model(base, lora)
    backbone.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model = DenseTimeModel(backbone).to("cuda:0")
    report["parameter_inventory"] = parameter_inventory(backbone, model.head)
    report["lora"] = {"rank": 16, "alpha": 32, "dropout": 0.05, "gradient_checkpointing_use_reentrant": False,
        "embedding_requires_grad": base.get_input_embeddings().weight.requires_grad}
    frozen = fingerprint_parameters(backbone, lambda n, p: "lora_" not in n)
    visual = fingerprint_parameters(backbone, lambda n, p: "visual" in n)
    initial = capture_trainable(model)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=config["lr"],
        betas=(config["adam_beta1"], config["adam_beta2"]), eps=config["adam_eps"], weight_decay=0.0)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
    counters = UpdateCounters()
    def reject_lm_head(module, inputs):
        raise RuntimeError("cost dense path called lm_head")
    guard = base.lm_head.register_forward_pre_hook(reject_lm_head)
    model.train()
    report["updates"] = []
    for update in range(3):
        checkpoint(f"UPDATE_{update + 1}_STARTED")
        del encoded, positions  # Avoid retaining the preceding window's CUDA input allocation during preparation.
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        baseline_allocated = torch.cuda.memory_allocated()
        tick = time.monotonic()
        encoded, positions, identity, timing = prepare()
        prepared = time.monotonic()
        batch = {"targets": torch.tensor([[c["target"] for c in row["grid"]]], device="cuda:0"),
                 "known_mask": torch.ones(1, 16, dtype=torch.bool, device="cuda:0")}
        measured = {}
        def forward(batch):
            torch.cuda.synchronize()
            forward_started = time.monotonic()
            logits = model(encoded, positions)
            torch.cuda.synchronize()
            measured["forward_seconds"] = time.monotonic() - forward_started
            return logits
        result = accumulation_update(model, [batch], optimizer, scheduler, counters, forward,
            before_step=lambda: gradient_evidence(model, torch), clip_norm=config["grad_clip_norm"])
        torch.cuda.synchronize()
        finished = time.monotonic()
        record = {"update": update + 1, **result, **measured, **timing,
            "update_seconds": finished - prepared, "total_step_seconds": finished - tick,
            "backward_gradient_checks_optimizer_seconds": finished - prepared - measured["forward_seconds"],
            "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved(), "baseline_cuda_allocated_bytes": baseline_allocated,
            "peak_cuda_allocated_increment_bytes": torch.cuda.max_memory_allocated() - baseline_allocated,
            "expanded_tokens": identity["sequence_length"], "identity": identity}
        report["updates"].append(record)
        dump(output / "updates_and_cost.json", report["updates"])
        checkpoint(f"UPDATE_{update + 1}_COMPLETED")
    current = capture_trainable(model)
    changes = {n: not torch.equal(v, current[n]) for n, v in initial.items()}
    report["trainable_changes"] = changes
    for kind in ("head.", "lora_A", "lora_B"):
        require(any(kind in n and changed for n, changed in changes.items()), f"32s updates did not change {kind}")
    steps = report["updates"]
    require(steps[0]["gradient_evidence"]["head"]["nonzero_tensors"] > 0
            and steps[0]["gradient_evidence"]["lora_B"]["nonzero_tensors"] > 0
            and any(r["gradient_evidence"]["lora_A"]["nonzero_tensors"] > 0 for r in steps[1:]), "32s gradient disconnection")
    model.eval()
    wall_check()
    clear_model_cache(backbone)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    with torch.no_grad():
        inference_logits = model(encoded, positions)
    torch.cuda.synchronize()
    report["dense_time_inference"] = {"seconds": time.monotonic() - started,
        "query_count": 16, "expanded_tokens": identity["sequence_length"],
        "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(), "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved(),
        "logits": inference_logits.detach().cpu().tolist(), "semantic_quality_evaluated": False}
    del inference_logits
    frozen_after = fingerprint_parameters(backbone, lambda n, p: "lora_" not in n)
    visual_after = fingerprint_parameters(backbone, lambda n, p: "visual" in n)
    report["freeze_evidence"] = {"base_before": frozen, "base_after": frozen_after,
        "visual_before": visual, "visual_after": visual_after}
    require(frozen == frozen_after and visual == visual_after, "32s probe changed frozen base/vision")
    guard.remove()
    def reject_time_head(module, inputs):
        raise RuntimeError("time head called during spatial restoration")
    head_guard = model.head.register_forward_pre_hook(reject_time_head)
    checkpoint("VERIFYING_SPATIAL_RESTORATION")
    with model.spatial_base() as original:
        require(original is base and model.head_enabled is False, "spatial path did not restore shared raw base")
        restored = signature(encoded, "adapter_off_after_updates")
    head_guard.remove()
    logits_equal = torch.equal(reference["last_token_logits"], restored["last_token_logits"])
    tokens_equal = torch.equal(reference["greedy_ids"], restored["greedy_ids"])
    report["spatial_original_base_restoration"] = {"last_token_logits_exact_equal": logits_equal,
        "greedy_tokens_exact_equal": tokens_equal, "adapter_off": True, "head_forward_guarded": True,
        "cache_cleared": not model.external_caches, "generated_suffix_before": reference["greedy_ids"][:, -3:].tolist(),
        "generated_suffix_after": restored["greedy_ids"][:, -3:].tolist()}
    require(logits_equal and tokens_equal, "32s adapter-off raw base not restored exactly")
    require(sha256(Path(SOURCE_PATH)) == SOURCE_SHA256, "source changed by probe completion")
    report["source_hashes_at_end"] = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")}
    require(report["source_hashes_at_start"] == report["source_hashes_at_end"], "probe code changed during runtime")
    wall_check()
    report.update(status="PASS_REAL_32S_NONTEST_COST_SYNTHETIC_LABELS_ONLY", optimizer_steps=counters.optimizer_steps,
        run_seconds=time.monotonic() - run_started, formal_training_started=False, quality_evaluated=False,
        reusable_formal_checkpoint=False, not_established=["formal BCE data permission/negative semantics",
        "strict UNKNOWN invariance at 32s (prior 4s exact gate reused)", "production crop/anchor throughput",
        "full-video or 426-video cost", "highlight/composition quality and official score"])
    checkpoint("COMPLETED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--metadata-root", type=Path, help="local metadata mirror, plan-only; never changes frozen config")
    parser.add_argument("--report", type=Path, help="new local JSON path, plan-only")
    args = parser.parse_args()
    report = {"status": "CHECKING_COST_PROBE_ADMISSION", "started_runtime": False, "formal_training_started": False,
        "scope": "one fixed non-test source; synthetic labels; no train/dev/confirm/test semantic labels"}
    output = None
    started = time.monotonic()
    try:
        require(args.plan_only or (args.metadata_root is None and args.report is None), "metadata/report overrides are plan-only")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        admission = json.loads(args.admission.read_text(encoding="utf-8"))
        validate_config(config)
        validate_admission(args.config, admission)
        report.update(config_sha256=sha256(args.config), admission_sha256=sha256(args.admission), run_id=config["run_id"])
        if args.plan_only:
            manifest = args.metadata_root / "baseline_a/inputs/non_test_frozen8.json" if args.metadata_root else None
            _, report["source_plan"] = source_plan(config, manifest)
            report["prior_engineering_gate"] = prior_gate(admission, args.metadata_root)
            report["status"] = "PLANNED_COST_ONLY_NO_RUNTIME"
        else:
            candidate = Path(config["out_dir"])
            candidate.mkdir(parents=True, exist_ok=False)  # Even an empty prior run directory must remain untouched.
            output = candidate
            report.update(out_dir=str(output), status="RUNNING_NONTEST_COST_PROBE")
            (output / "frozen_config.json").write_bytes(args.config.read_bytes())
            (output / "frozen_admission.json").write_bytes(args.admission.read_bytes())
            dump(output / "cost_probe_report.json", report)
            report["prior_engineering_gate"] = prior_gate(admission)
            receipt = bound_json(config.get("model_receipt"), "cost model receipt")
            require(receipt.get("status") == "COMPLETE_HASH_VERIFIED" and receipt.get("model_path") == config["model_dir"]
                    and receipt.get("revision") == PINNED_REVISION and receipt.get("repo") == MODEL_ID,
                    "cost model download not complete/pinned/path-bound")
            run(config, report, output)
    except Exception as exc:
        report["status"] = "FAIL_NONTEST_COST_PROBE"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    report["wall_seconds_total"] = time.monotonic() - started
    if output is not None:
        dump(output / "cost_probe_report.json", report)
    if args.report:
        try:
            with args.report.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
        except Exception as exc:
            report["status"] = "FAIL_NONTEST_COST_PROBE"
            report["report_write_failure"] = str(exc)
    # Early admission/output failures have no trusted new output path: the complete JSON goes to controller log.
    print(json.dumps(report, allow_nan=False), flush=True)
    return 0 if report["status"].startswith(("PASS_", "PLANNED_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
