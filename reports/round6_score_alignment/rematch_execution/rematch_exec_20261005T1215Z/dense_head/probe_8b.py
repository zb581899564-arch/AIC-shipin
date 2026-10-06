#!/usr/bin/env python3
"""Bounded real-8B engineering probe, synthetic media/labels only. No downloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback

from dense_time import (DenseTimeModel, MODEL_ID, REVISION, UpdateCounters,
                        accumulation_update, clear_model_cache, fingerprint_parameters,
                        language_targets, masked_bce_sum, parameter_inventory,
                        query_text, resolve_queries, unique_parameters)
from grid_targets import grid_targets_from_source_frames


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_receipt(model_dir: Path, receipt_path: Path, metadata_only: bool = False) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    controller_receipt = "completed" in receipt
    repo_id = receipt.get("repo") if controller_receipt else receipt.get("repo_id")
    if repo_id != MODEL_ID or receipt.get("revision") != REVISION:
        raise RuntimeError("model receipt does not identify the pinned Qwen 8B revision")
    if controller_receipt and not metadata_only and receipt.get("status") != "COMPLETE_HASH_VERIFIED":
        raise RuntimeError("controller model download receipt is not COMPLETE_HASH_VERIFIED")
    if controller_receipt:
        recorded_model_path = receipt.get("model_path")
        if not recorded_model_path and not metadata_only:
            raise RuntimeError("complete controller receipt requires model_path")
        if recorded_model_path and Path(recorded_model_path).resolve() != model_dir.resolve():
            raise RuntimeError("controller receipt model_path differs from requested model directory")
    entries = receipt.get("completed") if controller_receipt else receipt.get("files")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("receipt requires [{path,sha256,size_bytes}, ...]")
    declared = set()
    for entry in entries:
        relative = Path(entry["name"] if controller_receipt else entry["path"])
        if metadata_only and relative.suffix == ".safetensors":
            continue
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe receipt path")
        path = model_dir / relative
        if path.resolve().parent != model_dir.resolve() or not path.is_file():
            raise ValueError("model receipt must list existing root files only")
        if relative.as_posix() in declared:
            raise ValueError("duplicate model receipt file")
        declared.add(relative.as_posix())
        size = entry["bytes"] if controller_receipt else entry["size_bytes"]
        digest = file_sha256(path)
        if path.stat().st_size != size or digest != entry["sha256"]:
            raise RuntimeError(f"model file receipt mismatch: {relative}")
        if controller_receipt:
            mode = entry["verification"]
            if mode == "lfs_sha256":
                official_digest = digest
            elif mode == "git_blob_sha1":
                h = hashlib.sha1()
                h.update(f"blob {size}\0".encode("ascii"))
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(8 << 20), b""):
                        h.update(chunk)
                official_digest = h.hexdigest()
            else:
                raise RuntimeError(f"unknown official verification mode: {mode}")
            if official_digest != entry["official_content_hash"]:
                raise RuntimeError(f"pinned official content hash mismatch: {relative}")
    suffixes = (".json", ".txt", ".model", ".jinja") if metadata_only else (".json", ".safetensors", ".txt", ".model", ".jinja")
    required = {p.name for p in model_dir.iterdir() if p.is_file() and p.suffix in suffixes}
    if metadata_only:
        required.update(("config.json", "tokenizer.json", "tokenizer_config.json", "preprocessor_config.json", "video_preprocessor_config.json"))
    if not required.issubset(declared) or (not metadata_only and not any(n.endswith(".safetensors") for n in declared)):
        raise RuntimeError(f"receipt missing model/config/tokenizer files: {sorted(required - declared)}")
    return {"repo_id": MODEL_ID, "revision": REVISION, "receipt_sha256": file_sha256(receipt_path),
            "verified_files": len(declared), "metadata_only": metadata_only,
            "authority": "controller-provided pinned-download receipt"}


def synthetic_video(torch, mismatch: bool = False):
    frames = torch.zeros(8, 3, 224, 224, dtype=torch.uint8)
    for i in range(8):
        x = 16 + 12 * i
        frames[i, 0 if not mismatch else 2, 64:144, x:x + 48] = 255
        frames[i, 1, :, :] = 32 if not mismatch else 160
    return frames


def encode_video(processor, torch, text: str, video, add_generation_prompt: bool = False, **text_options):
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=add_generation_prompt, enable_thinking=False)
    prefix = "<|im_start|>user\n"
    if prompt.count(prefix) != 1:
        raise ValueError("unexpected chat template user boundary")
    prompt = prompt.replace(prefix, prefix + "<|vision_start|><|video_pad|><|vision_end|>", 1)
    metadata = {"fps": 2.0, "frames_indices": list(range(8)), "total_num_frames": 8}
    options = {"padding": True, "truncation": False, **text_options}
    encoded = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                        do_sample_frames=False, return_tensors="pt", **options)
    if "pixel_values_videos" not in encoded or "video_grid_thw" not in encoded:
        raise RuntimeError("processor omitted video tensors")
    return dict(encoded)


def gradient_evidence(model, torch) -> dict:
    groups = {"head": [], "lora_A": [], "lora_B": []}
    for name, p in unique_parameters(model):
        if not p.requires_grad:
            continue
        key = "head" if name.startswith("head.") else "lora_A" if "lora_A" in name else "lora_B"
        if p.grad is None:
            raise RuntimeError(f"missing gradient: {name}")
        groups[key].append({"name": name, "norm": float(p.grad.float().norm()),
                            "nonzero_elements": int(torch.count_nonzero(p.grad))})
    return {key: {"tensor_count": len(rows), "nonzero_tensors": sum(r["nonzero_elements"] > 0 for r in rows),
                  "norm_sum": sum(r["norm"] for r in rows), "tensors": rows}
            for key, rows in groups.items()}


def capture_trainable(model):
    return {name: p.detach().cpu().clone() for name, p in unique_parameters(model) if p.requires_grad}


def capture_gradients(model):
    return {name: None if p.grad is None else p.grad.detach().cpu().clone()
            for name, p in unique_parameters(model) if p.requires_grad}


def compare_gradients(left: dict, right: dict, torch) -> dict:
    require_names = set(left) == set(right)
    if not require_names:
        raise RuntimeError("gradient comparison parameter sets differ")
    rows = []
    for name in left:
        a, b = left[name], right[name]
        if a is None or b is None:
            rows.append({"name": name, "exact_equal": False, "missing_gradient": True,
                         "max_abs_diff": None, "different_elements": None})
            continue
        if a.shape != b.shape or not torch.isfinite(a).all() or not torch.isfinite(b).all():
            raise RuntimeError(f"invalid gradient comparison tensor: {name}")
        delta = (a.float() - b.float()).abs()
        rows.append({"name": name, "exact_equal": torch.equal(a, b),
                     "max_abs_diff": float(delta.max()), "different_elements": int(torch.count_nonzero(delta)),
                     "left_norm": float(a.float().norm()), "right_norm": float(b.float().norm())})
    return {"all_exact_equal": all(row["exact_equal"] for row in rows),
            "different_tensor_count": sum(not row["exact_equal"] for row in rows),
            "max_abs_diff": max((row["max_abs_diff"] for row in rows if row["max_abs_diff"] is not None), default=0.0),
            "per_tensor": rows}


def spatial_signature(base, encoded, torch) -> dict:
    clear_model_cache(base)
    with torch.no_grad():
        output = base(**encoded, use_cache=False, past_key_values=None, logits_to_keep=1,
                      output_hidden_states=False, output_attentions=False, return_dict=True)
        logits = output.logits.detach().cpu()
        if output.logits.shape[1] != 1 or output.past_key_values is not None:
            raise RuntimeError("spatial signature unexpectedly produced full logits/cache")
        clear_model_cache(base)
        tokens = base.generate(**encoded, max_new_tokens=3, do_sample=False, use_cache=False,
                               logits_to_keep=1, output_hidden_states=False, output_attentions=False)
    clear_model_cache(base)
    return {"last_token_logits": logits, "greedy_ids": tokens.detach().cpu()}


def run(args, report: dict) -> None:
    import numpy as np
    import torch
    import transformers
    import peft
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    report["environment"] = {"python": sys.version, "executable": sys.executable,
                             "torch": torch.__version__, "transformers": transformers.__version__,
                             "peft": peft.__version__}
    if transformers.__version__ != "4.57.1" or peft.__version__ != "0.17.1":
        raise RuntimeError("this entry point is reviewed against transformers4.57.1 / peft0.17.1")
    if not torch.cuda.is_available():
        raise RuntimeError("real model probe requires controller-approved CUDA execution")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    report["model_receipt"] = verify_receipt(args.model_dir, args.model_receipt)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    base = Qwen3VLForConditionalGeneration.from_pretrained(
        str(args.model_dir), revision=REVISION, local_files_only=True,
        torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    if base.config.model_type != "qwen3_vl" or base.config.text_config.hidden_size != 4096:
        raise RuntimeError("loaded architecture is not the approved dense-head 8B")
    for p in base.parameters():
        p.requires_grad_(False)
    base.config.use_cache = False
    processor = AutoProcessor.from_pretrained(str(args.model_dir), revision=REVISION,
                                              local_files_only=True, min_pixels=224 * 224,
                                              max_pixels=224 * 224)
    original_vocab_size = len(processor.tokenizer)
    raw = encode_video(processor, torch, query_text(4, 1.0, 4.0), synthetic_video(torch))
    mismatch_raw = encode_video(processor, torch, query_text(4, 1.0, 4.0), synthetic_video(torch, True))
    contract = resolve_queries(raw, processor.tokenizer, 4, processor.video_token_id)
    if len(processor.tokenizer) != original_vocab_size:
        raise RuntimeError("processor vocabulary was expanded")
    report["query_contract"] = {"markers": contract.markers, "positions": contract.positions,
                                "marker_token_ids": contract.marker_token_ids,
                                "last_video_position": contract.last_video_position,
                                "processor_sequence_length": contract.sequence_length,
                                "vocabulary_size_before_after": [original_vocab_size, len(processor.tokenizer)],
                                "head_reads": "final token of each fixed marker in processor-expanded IDs"}
    encoded = {k: v.to("cuda:0") for k, v in raw.items()}
    positions = torch.tensor([contract.positions], dtype=torch.long, device="cuda:0")
    spatial_raw = encode_video(processor, torch,
                               "Locate the main subject for a video crop. Respond with its center.",
                               synthetic_video(torch), add_generation_prompt=True)
    spatial_encoded = {k: v.to("cuda:0") for k, v in spatial_raw.items()}
    base.eval()
    reference = spatial_signature(base, spatial_encoded, torch)
    targets = language_targets(base)
    config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                        target_modules=targets, modules_to_save=None, task_type="CAUSAL_LM")
    backbone = get_peft_model(base, config)
    backbone.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    # Non-reentrant checkpointing supports frozen embeddings. No embedding-grad
    # hook is added: it would mask the very disconnection being tested.
    model = DenseTimeModel(backbone).to("cuda:0")
    report["parameter_inventory"] = parameter_inventory(backbone, model.head)
    report["lora"] = {"rank": 16, "alpha": 32, "dropout": 0.05,
                      "exact_language_target_modules": targets, "modules_to_save": None,
                      "gradient_checkpointing_use_reentrant": False,
                      "embedding_requires_grad": base.get_input_embeddings().weight.requires_grad}
    if base.get_input_embeddings().weight.requires_grad:
        raise RuntimeError("embedding was unfrozen")
    before_base = fingerprint_parameters(backbone, lambda n, p: "lora_" not in n)
    before_visual = fingerprint_parameters(backbone, lambda n, p: "visual" in n)
    before_trainable = capture_trainable(model)
    frame_states = [1, 1, -1, -1, 0, 0, 1, 0]
    grid = grid_targets_from_source_frames(list(range(8)), [i / 2 for i in range(8)],
                                          [(i + 1) / 2 for i in range(8)], frame_states,
                                          [(i, i + 1) for i in range(4)], [(0, 4)])
    report["synthetic_grid_replay"] = grid["replay"]
    batch = {"targets": grid["targets"].to("cuda"), "known_mask": grid["known_mask"].to("cuda")}
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=args.lr, weight_decay=0.0)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: 1.0)
    counters = UpdateCounters()
    # Hard guard proves the dense path cannot silently materialize LM logits.
    def reject_lm_head(module, inputs):
        raise RuntimeError("dense forward unexpectedly called lm_head")
    guard = base.lm_head.register_forward_pre_hook(reject_lm_head)
    model.train()
    logs = []
    for _ in range(args.updates):
        logs.append(accumulation_update(model, [batch, batch], optimizer, scheduler, counters,
                                       lambda b: model(encoded, positions),
                                       before_step=lambda: gradient_evidence(model, torch)))
    report["updates"] = logs
    first = logs[0]["gradient_evidence"]
    if first["head"]["nonzero_tensors"] == 0 or first["lora_B"]["nonzero_tensors"] == 0:
        raise RuntimeError("head or LoRA B had no first-step gradient")
    if not any(log["gradient_evidence"]["lora_A"]["nonzero_tensors"] > 0 for log in logs[1:]):
        raise RuntimeError("LoRA A remained disconnected after B updates")
    report["lora_A_first_step"] = {"zero_gradient_tensors": first["lora_A"]["tensor_count"] - first["lora_A"]["nonzero_tensors"],
                                   "explanation": "LoRA B starts at zero; first-step A zero gradient is expected, later nonzero gradient is required"}
    after_trainable = capture_trainable(model)
    changes = {name: not torch.equal(value, after_trainable[name]) for name, value in before_trainable.items()}
    report["trainable_changes"] = changes
    for kind in ("head.", "lora_A", "lora_B"):
        if not any(changed and kind in name for name, changed in changes.items()):
            raise RuntimeError(f"no actual parameter change in {kind}")
    after_base = fingerprint_parameters(backbone, lambda n, p: "lora_" not in n)
    after_visual = fingerprint_parameters(backbone, lambda n, p: "visual" in n)
    report["freeze_evidence"] = {"base_before": before_base, "base_after": after_base,
                                "visual_before": before_visual, "visual_after": after_visual}
    if before_base != after_base or before_visual != after_visual:
        raise RuntimeError("frozen base/vision parameter bytes changed")
    # A repeated same-label control diagnoses backend nondeterminism independently
    # of masks. The acceptance comparison then uses deterministic math SDPA only.
    model.eval()
    altered = batch["targets"].clone()
    altered[~batch["known_mask"]] = -999.0
    cpu_rng, cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
    def label_backward(labels):
        torch.set_rng_state(cpu_rng)
        torch.cuda.set_rng_state_all(cuda_rng)
        model.zero_grad(set_to_none=True)
        loss, count = masked_bce_sum(model(encoded, positions), labels, batch["known_mask"])
        assert loss is not None
        (loss / count).backward()
        return float(loss.detach()), capture_gradients(model)
    control_a = label_backward(batch["targets"])
    control_b = label_backward(batch["targets"])
    report["same_label_default_backend_control"] = {
        "losses": [control_a[0], control_b[0]],
        "gradient_comparison": compare_gradients(control_a[1], control_b[1], torch),
        "same_rng_and_encoded_inputs": True}
    default_equal = report["same_label_default_backend_control"]["gradient_comparison"]["all_exact_equal"]
    report["same_label_default_backend_control"]["interpretation"] = (
        "same-label CUDA gradient nondeterminism observed with default backend" if not default_equal else
        "no default-backend nondeterminism observed in this repeat; original failure cause not uniquely attributed")
    del control_a, control_b
    previous_deterministic = torch.are_deterministic_algorithms_enabled()
    previous_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    from torch.nn.attention import SDPBackend, sdpa_kernel
    torch.use_deterministic_algorithms(True, warn_only=False)
    try:
        with sdpa_kernel(backends=[SDPBackend.MATH]):
            strict_a = label_backward(batch["targets"])
            strict_same = label_backward(batch["targets"])
            strict_altered = label_backward(altered)
    finally:
        torch.use_deterministic_algorithms(previous_deterministic, warn_only=previous_warn_only)
    same_comparison = compare_gradients(strict_a[1], strict_same[1], torch)
    masked_comparison = compare_gradients(strict_a[1], strict_altered[1], torch)
    losses = [strict_a[0], strict_same[0], strict_altered[0]]
    report["masked_label_invariance"] = {"losses": losses,
        "all_trainable_gradients_exact_equal": masked_comparison["all_exact_equal"],
        "same_label_strict_control": same_comparison, "masked_label_gradient_comparison": masked_comparison,
        "backend": "SDPBackend.MATH only; flash/efficient/cuDNN SDPA disabled",
        "deterministic_algorithms": True, "same_rng_and_encoded_inputs": True,
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        "unknown_before": "NaN", "unknown_after": -999.0,
        "tolerance": "none; exact elementwise equality required"}
    del strict_a, strict_same, strict_altered
    if losses[0] != losses[1] or not same_comparison["all_exact_equal"]:
        raise RuntimeError("same-label control is not exact under deterministic math SDPA")
    if losses[0] != losses[2] or not masked_comparison["all_exact_equal"]:
        raise RuntimeError("UNKNOWN labels affected loss/gradients")
    report["masked_label_invariance"]["interpretation"] = "mask invariance established under exact deterministic math-SDPA comparison"
    snapshot = capture_trainable(model)
    optimizer_state_step = [float(state["step"]) for state in optimizer.state.values()]
    scheduler_epoch = scheduler.last_epoch
    unknown = {"targets": torch.full_like(batch["targets"], float("nan")),
               "known_mask": torch.zeros_like(batch["known_mask"])}
    skipped = accumulation_update(model, [unknown, unknown], optimizer, scheduler, counters,
                                  lambda b: (_ for _ in ()).throw(RuntimeError("UNKNOWN batch ran forward")))
    unchanged = all(torch.equal(p.detach().cpu(), snapshot[n]) for n, p in unique_parameters(model) if p.requires_grad)
    report["all_unknown_skip"] = {"result": skipped, "trainable_unchanged": unchanged,
                                   "optimizer_state_steps_unchanged": optimizer_state_step == [float(s["step"]) for s in optimizer.state.values()],
                                   "scheduler_epoch_unchanged": scheduler_epoch == scheduler.last_epoch,
                                   "counters": vars(counters)}
    if not unchanged or scheduler_epoch != scheduler.last_epoch or counters.optimizer_steps != args.updates:
        raise RuntimeError("all-UNKNOWN accumulation advanced training")
    if optimizer_state_step != [float(s["step"]) for s in optimizer.state.values()]:
        raise RuntimeError("all-UNKNOWN accumulation advanced optimizer state")
    if not torch.equal(raw["input_ids"], mismatch_raw["input_ids"]) or not torch.equal(raw["video_grid_thw"], mismatch_raw["video_grid_thw"]):
        raise RuntimeError("visual diagnostic must keep IDs/geometry fixed")
    mismatched = dict(encoded)
    mismatched["pixel_values_videos"] = mismatch_raw["pixel_values_videos"].to("cuda")
    with torch.no_grad():
        normal_logits = model(encoded, positions)
        mismatch_logits = model(mismatched, positions)
    visual_delta = float((normal_logits - mismatch_logits).abs().max())
    report["mismatched_visual_diagnostic"] = {"max_abs_query_logit_difference": visual_delta,
                                             "normal_logits": normal_logits.cpu().tolist(),
                                             "mismatch_logits": mismatch_logits.cpu().tolist(),
                                             "same_ids_and_grid": True,
                                             "meaning": "visual sensitivity on synthetic pixels, no semantic accuracy claim"}
    if visual_delta == 0 or not torch.isfinite(mismatch_logits).all():
        raise RuntimeError("query head is insensitive to distinct visual input or nonfinite")
    guard.remove()
    with model.spatial_base() as original_base:
        if model.head_enabled or model.external_caches:
            raise RuntimeError("time head/cache remained enabled for spatial session")
        def reject_time_head(module, inputs):
            raise RuntimeError("spatial path called time head")
        head_guard = model.head.register_forward_pre_hook(reject_time_head)
        restored = spatial_signature(original_base, spatial_encoded, torch)
        head_guard.remove()
    exact_logits = torch.equal(reference["last_token_logits"], restored["last_token_logits"])
    exact_tokens = torch.equal(reference["greedy_ids"], restored["greedy_ids"])
    report["spatial_original_base_restoration"] = {"last_token_logits_exact_equal": exact_logits,
                                                  "greedy_tokens_exact_equal": exact_tokens,
                                                  "greedy_ids_before": reference["greedy_ids"].tolist(),
                                                  "greedy_ids_after": restored["greedy_ids"].tolist(),
                                                  "cache_cleared": not model.external_caches,
                                                  "adapters": "disable_adapter context; no merge",
                                                  "head_forward": "blocked by hook throughout spatial test"}
    if not exact_logits or not exact_tokens:
        raise RuntimeError("adapter-off spatial output differs from original raw base")
    model.backbone.save_pretrained(str(args.out_dir / "synthetic_adapter"))
    torch.save(model.head.state_dict(), args.out_dir / "synthetic_head.pt")
    report["saved_artifacts"] = {p.name: file_sha256(p) for p in (args.out_dir / "synthetic_adapter").iterdir() if p.is_file()}
    report["saved_artifacts"]["synthetic_head.pt"] = file_sha256(args.out_dir / "synthetic_head.pt")
    report["resources"] = {"wall_seconds_after_load_started": time.monotonic() - started,
                            "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(),
                            "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved()}
    report["status"] = "PASS_REAL_8B_SYNTHETIC_ENGINEERING_ONLY"
    report["not_established"] = ["training-data permission/observation/negative supervision",
                                 "source-video PTS/decoder replay on real non-test media",
                                 "32s-window train/inference/space throughput and peak memory",
                                 "highlight quality, composition quality, official score"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--model-receipt", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--engineering-only", action="store_true", required=True)
    ap.add_argument("--updates", type=int, default=3)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--seed", type=int, default=20261005)
    args = ap.parse_args()
    if not 3 <= args.updates <= 5 or not 0 < args.lr <= 1e-3:
        raise ValueError("engineering probe requires 3..5 updates and bounded positive learning rate")
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise RuntimeError("refusing to overwrite nonempty probe output")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    if os.environ["CUBLAS_WORKSPACE_CONFIG"] not in (":4096:8", ":16:8"):
        raise RuntimeError("strict gradient invariance requires a deterministic CUBLAS workspace config")
    report = {"status": "RUNNING_SYNTHETIC_ENGINEERING_ONLY", "model_id": MODEL_ID,
              "revision": REVISION, "updates_requested": args.updates,
              "scope": "synthetic pixels and synthetic labels only; not formal C training"}
    began = time.monotonic()
    try:
        run(args, report)
    except Exception as exc:
        report["status"] = "FAIL_REAL_8B_SYNTHETIC_ENGINEERING_ONLY"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    report["wall_seconds_total"] = time.monotonic() - began
    (args.out_dir / "probe_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.out_dir / "probe_report.json"),
                      "failure": report.get("failure", {}).get("message")}, ensure_ascii=False), flush=True)
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
