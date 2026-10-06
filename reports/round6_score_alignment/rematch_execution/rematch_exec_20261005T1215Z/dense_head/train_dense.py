#!/usr/bin/env python3
"""Formal C training preparation. Current STOP data gate refuses before runtime I/O."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time
import traceback

from formal_contract import AdmissionRejected, admit, require, sha256


def prepare_window(processor, row, config, index, torch, decode):
    from dense_time import query_text, resolve_queries
    from exact_pts import exact_source_pts
    frames, decoded_pts = decode(row, config, index)
    video = torch.from_numpy(frames).permute(0, 3, 1, 2)
    count = len(row["grid"])
    messages = [{"role": "user", "content": [{"type": "text", "text":
                query_text(count, config["grid_seconds"], config["window_seconds"])}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=False,
                                           enable_thinking=False)
    prefix = "<|im_start|>user\n"
    require(prompt.count(prefix) == 1, "unexpected formal processor chat template")
    prompt = prompt.replace(prefix, prefix + "<|vision_start|><|video_pad|><|vision_end|>", 1)
    metadata = {"fps": index["source_avg_fps"], "frames_indices": row["frame_ids"],
                "total_num_frames": len(index["frame_pts"])}
    with exact_source_pts(processor, row["frame_ids"], row["exact_frame_pts"],
                          row["window_start_pts"], index["source_avg_fps"]) as pts_record:
        encoded = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                            padding=True, truncation=False, do_sample_frames=False, return_tensors="pt")
    contract = resolve_queries(encoded, processor.tokenizer, count, processor.video_token_id)
    require(contract.sequence_length <= config["max_sequence_length"], "expanded formal window exceeds frozen length; no silent truncation")
    temporal_calls = pts_record["processor_calls"]
    require(int(encoded["video_grid_thw"][0, 0]) == len(temporal_calls[0]["exact_temporal_patch_local_pts"]),
            "processor video temporal patches differ from exact source PTS")
    record = {"window_id": row["window_id"], "source_group": row["source_group"],
              "source_path": row["source_path"], "source_sha256": row["source_sha256"],
              "pts_index_sha256": row["pts_index"]["sha256"], "decoded_frame_pts": decoded_pts,
              "processor_pts": pts_record, "query_positions": contract.positions,
              "query_marker_token_ids": contract.marker_token_ids,
              "last_video_position": contract.last_video_position, "sequence_length": contract.sequence_length,
              "source_grid_replay": row["grid"], "video_grid_thw": encoded["video_grid_thw"].tolist()}
    return {k: v.to("cuda:0") for k, v in encoded.items()}, torch.tensor([contract.positions], device="cuda:0"), record


def execute(contract: dict, report: dict, config_path: Path, admission_path: Path):
    # This function is called ONLY after the stdlib-only admission contract passed.
    import os
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    config = contract["config"]
    initial_source_hashes = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")}
    report["source_hashes_at_start"] = initial_source_hashes
    output = Path(config["out_dir"])
    require(not output.exists() or not any(output.iterdir()), "refusing nonempty formal training output")
    output.mkdir(parents=True, exist_ok=True)
    report["out_dir"] = str(output)
    # Media hashes are verified before CUDA/model/decoder initialization.
    source_stats = {}
    for path_string, expected_hash in contract["sources"].items():
        source = Path(path_string)
        require(source.is_file() and sha256(source) == expected_hash, "source media changed after admission")
        stat = source.stat()
        source_stats[path_string] = (stat.st_size, stat.st_mtime_ns)
    require(sha256(Path(config["model_receipt"]["path"])) == config["model_receipt"]["sha256"],
            "model receipt changed after admission")
    import numpy as np
    import torch
    import transformers
    import peft
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from dense_time import (DenseTimeModel, REVISION, UpdateCounters, accumulation_update,
                            fingerprint_parameters, language_targets, parameter_inventory, unique_parameters)
    from probe_8b import gradient_evidence, verify_receipt
    require(transformers.__version__ == "4.57.1" and peft.__version__ == "0.17.1", "unreviewed formal runtime versions")
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.set_device(0)
    torch.cuda.init()
    torch.cuda.manual_seed_all(config["seed"])
    # Initialize torch CUDA before importing decord; decoding itself uses CPU.
    import decord
    report["environment"] = {"python": sys.version, "executable": sys.executable, "torch": torch.__version__,
                             "transformers": transformers.__version__, "peft": peft.__version__,
                             "decord": decord.__version__, "numpy": np.__version__}
    report["model_receipt"] = verify_receipt(Path(config["model_dir"]), Path(config["model_receipt"]["path"]))
    model_started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    base = Qwen3VLForConditionalGeneration.from_pretrained(config["model_dir"], revision=REVISION,
        local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation=config["attn_implementation"])
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    base.config.use_cache = False
    processor = AutoProcessor.from_pretrained(config["model_dir"], revision=REVISION, local_files_only=True,
                                              min_pixels=config["max_pixels"], max_pixels=config["max_pixels"])
    lora = LoraConfig(r=config["lora_rank"], lora_alpha=config["lora_alpha"], lora_dropout=config["lora_dropout"],
                      bias="none", target_modules=language_targets(base), modules_to_save=None, task_type="CAUSAL_LM")
    backbone = get_peft_model(base, lora)
    backbone.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model = DenseTimeModel(backbone).to("cuda:0")
    report["parameter_inventory"] = parameter_inventory(backbone, model.head)
    frozen_before = fingerprint_parameters(backbone, lambda name, p: "lora_" not in name)
    report["frozen_base_before"] = frozen_before
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=config["lr"],
                                  weight_decay=config["weight_decay"],
                                  betas=(config["adam_beta1"], config["adam_beta2"]), eps=config["adam_eps"])
    def schedule(step):
        warmup, total = config["warmup_optimizer_steps"], config["max_optimizer_steps"]
        if warmup and step < warmup:
            return (step + 1) / warmup
        progress = min(1.0, max(0.0, (step - warmup) / (total - warmup)))
        return config["min_lr_ratio"] + (1 - config["min_lr_ratio"]) * (1 - progress)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, schedule)
    counters = UpdateCounters()
    model.train()
    def reject_lm_head(module, inputs):
        raise RuntimeError("formal dense forward called lm_head")
    lm_guard = base.lm_head.register_forward_pre_hook(reject_lm_head)
    # Bounded decoder lifetime: each selected window has its own CPU reader.
    def decode(row, frozen_config, index):
        source = Path(row["source_path"])
        stat = source.stat()
        require((stat.st_size, stat.st_mtime_ns) == source_stats[row["source_path"]], "source changed during training")
        reader = decord.VideoReader(str(source), ctx=decord.cpu(0), num_threads=frozen_config["decoder_threads"])
        require(len(reader) == len(index["frame_pts"]), "decoded frame count differs from audited PTS index")
        actual = reader.get_frame_timestamp(row["frame_ids"])
        actual = actual.asnumpy() if hasattr(actual, "asnumpy") else np.asarray(actual)
        expected = np.stack((row["exact_frame_pts"], row["exact_frame_end_pts"]), axis=1)
        require(actual.shape == expected.shape and np.isfinite(actual).all()
                and float(np.abs(actual - expected).max()) <= frozen_config["decoder_pts_tolerance_seconds"],
                "decoded frame timestamps differ from exact audited source PTS")
        pixels = reader.get_batch(row["frame_ids"]).asnumpy()
        require(pixels.shape[0] == len(row["frame_ids"]) and pixels.ndim == 4 and pixels.shape[-1] == 3,
                "decoder returned mismatched selected frames")
        return pixels, actual.tolist()
    records = output / "source_processor_identity.jsonl"
    update_log = output / "updates.jsonl"
    rows = contract["rows"]
    completed_epochs, stopped = 0, None
    gradient_guards = []
    for epoch in range(config["epochs"]):
        order = list(range(len(rows)))
        random.Random(config["seed"] + epoch).shuffle(order)
        for start in range(0, len(order), config["grad_accum"]):
            require(time.monotonic() - model_started < config["max_wall_seconds"], "frozen wall-time stop reached")
            microbatches = []
            for j in order[start:start + config["grad_accum"]]:
                row = rows[j]
                microbatches.append({"row": row,
                    "targets": torch.tensor([[cell["target"] if cell["known"] else float("nan") for cell in row["grid"]]], device="cuda:0"),
                    "known_mask": torch.tensor([[cell["known"] for cell in row["grid"]]], dtype=torch.bool, device="cuda:0")})
            def forward(batch):
                row = batch["row"]
                index = contract["source_pts_indices"][json.dumps(row["pts_index"], sort_keys=True)]
                encoded, positions, record = prepare_window(processor, row, config, index, torch, decode)
                with records.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps({"epoch": epoch, **record}, separators=(",", ":")) + "\n")
                return model(encoded, positions)
            def gradient_guard():
                if counters.optimizer_steps < 3:
                    evidence = gradient_evidence(model, torch)
                    gradient_guards.append(evidence)
                    if counters.optimizer_steps == 0:
                        require(evidence["head"]["nonzero_tensors"] > 0 and evidence["lora_B"]["nonzero_tensors"] > 0,
                                "formal first update has no head/LoRA B gradient")
                    if counters.optimizer_steps == 2:
                        require(any(item["lora_A"]["nonzero_tensors"] > 0 for item in gradient_guards[1:]),
                                "formal LoRA A remained disconnected after B updates")
                    return evidence
                return None
            result = accumulation_update(model, microbatches, optimizer, scheduler, counters, forward,
                                         before_step=gradient_guard, clip_norm=config["grad_clip_norm"])
            with update_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"epoch": epoch, **result}, separators=(",", ":")) + "\n")
            report["counters"] = vars(counters).copy()
            if counters.optimizer_steps >= config["max_optimizer_steps"]:
                stopped = "MAX_STEPS"
                break
        if stopped:
            break
        completed_epochs += 1
    if config["stop_condition"] == "MAX_STEPS":
        require(counters.optimizer_steps == config["max_optimizer_steps"], "epoch bound exhausted before frozen optimizer step count")
    else:
        require(completed_epochs == config["epochs"] and stopped is None, "optimizer cap reached before frozen epochs")
    require(counters.optimizer_steps >= 3, "fewer than three formal updates cannot establish training gradient guard")
    require(gradient_guards[0]["head"]["nonzero_tensors"] > 0 and gradient_guards[0]["lora_B"]["nonzero_tensors"] > 0
            and any(record["lora_A"]["nonzero_tensors"] > 0 for record in gradient_guards[1:]), "formal head/LoRA gradient disconnection")
    frozen_after = fingerprint_parameters(backbone, lambda name, p: "lora_" not in name)
    report["frozen_base_after"] = frozen_after
    require(frozen_before == frozen_after, "formal training changed frozen base/visual bytes")
    require(sha256(config_path) == contract["config_sha256"] and sha256(admission_path) == contract["admission_sha256"],
            "admission or run config changed during formal training")
    source_hashes = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")}
    require(source_hashes == initial_source_hashes, "training source files changed during the run")
    lm_guard.remove()
    # Save ONLY small learned modules and reproducibility evidence, never the base.
    backbone.save_pretrained(str(output / "adapter"))
    torch.save(model.head.state_dict(), output / "dense_head.pt")
    (output / "run_config.json").write_bytes(config_path.read_bytes())
    (output / "admission.json").write_bytes(admission_path.read_bytes())
    (output / "environment.json").write_text(json.dumps(report["environment"], indent=2) + "\n", encoding="utf-8")
    (output / "source_hashes.json").write_text(json.dumps(source_hashes, indent=2) + "\n", encoding="utf-8")
    report.update(status="COMPLETED_FORMAL_C_WEAK_TRAINING_NOT_QUALITY_ACCEPTANCE",
                  completed_epochs=completed_epochs, stop_reason=stopped or "EPOCHS",
                  counters=vars(counters), gpu_wall_seconds=time.monotonic() - model_started,
                  peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
                  peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved(), source_hashes=source_hashes,
                  artifact_hashes={"adapter_model.safetensors": sha256(output / "adapter" / "adapter_model.safetensors"),
                                   "dense_head.pt": sha256(output / "dense_head.pt")},
                  dev_confirm_labels_read=False, model_quality_evaluated=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--admission-check-only", action="store_true")
    args = parser.parse_args()
    report = {"status": "CHECKING_FORMAL_ADMISSION", "started_runtime": False,
              "scope": "train only; no dev/confirm/test inference or quality evaluation"}
    started = time.monotonic()
    try:
        contract = admit(args.admission, args.config)
        report["admission_contract"] = {key: contract[key] for key in
            ("admission_sha256", "config_sha256", "manifest_sha256", "frozen_train_manifest_sha256",
             "train_source_groups_sha256", "known_cells", "negative_supported_cells", "dev_confirm_labels_read")}
        if args.admission_check_only:
            report["status"] = "PASS_FORMAL_ADMISSION_ONLY_NO_RUNTIME"
        else:
            report["started_runtime"] = True
            execute(contract, report, args.config, args.admission)
    except AdmissionRejected as exc:
        report["status"] = "REJECTED_FORMAL_ADMISSION_OR_CONTRACT"
        report["failure"] = str(exc)
    except Exception as exc:
        report["status"] = "FAILED_FORMAL_C_TRAINING"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    report["wall_seconds"] = time.monotonic() - started
    if report.get("out_dir"):
        (Path(report["out_dir"]) / "training_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report["status"].startswith(("COMPLETED_", "PASS_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
