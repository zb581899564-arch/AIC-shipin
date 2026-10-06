#!/usr/bin/env python3
"""R7 source-disjoint temporal LoRA training on the PTS-audited pool."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import temporal_common as tc

BASE_MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def answer_string(segments: list[list[float]]) -> str:
    return json.dumps({"segments": [[round(a, 4), round(b, 4)] for a, b in segments]},
                      separators=(",", ":"))


def build_example(processor, row, torch):
    arr, metadata, info = tc.build_virtual_clip(
        row["source_path"], row["clip_start_sec"], row["clip_end_sec"])
    answer = answer_string(row["segments_clip_local"])
    messages = [{"role": "user", "content": [{"type": "text", "text": tc.PROMPT}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True,
                                           enable_thinking=False)
    prompt = prompt.replace("<|im_start|>user\n",
                            "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
    video = torch.from_numpy(arr).permute(0, 3, 1, 2)
    full = prompt + answer + "<|im_end|>\n"
    encoded = processor(text=[full], videos=[video], video_metadata=[metadata],
                        padding=True, do_sample_frames=False, return_tensors="pt")
    prompt_encoded = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                               padding=True, do_sample_frames=False, return_tensors="pt")
    ids = encoded["input_ids"][0]
    prompt_len = int(prompt_encoded["input_ids"].shape[-1])
    if not torch.equal(ids[:prompt_len], prompt_encoded["input_ids"][0]):
        raise ValueError(f"prompt boundary mismatch: {row['sample_id']}")
    labels = ids.clone()
    labels[:prompt_len] = -100
    answer_tokens = int(ids.shape[-1]) - prompt_len
    if answer_tokens < 1:
        raise ValueError(f"empty answer tokens: {row['sample_id']}")
    keep = max(2, answer_tokens + 1)
    encoded["labels"] = labels[-keep:].unsqueeze(0)
    encoded["_logits_to_keep"] = keep
    if int((encoded["labels"] != -100).sum()) != answer_tokens:
        raise ValueError(f"answer mask mismatch: {row['sample_id']}")
    return encoded, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--epochs", type=int, required=True)
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20260921)
    args = ap.parse_args()
    if args.epochs < 1 or args.grad_accum < 1 or args.max_steps < 0:
        raise ValueError("invalid training bounds")
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise RuntimeError("refusing to overwrite nonempty output directory")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines()
            if x.strip()]
    if not rows or len({r["video_id"] for r in rows}) != len(rows):
        raise ValueError("empty or duplicate training manifest")
    if any(r.get("split") != "train" or r.get("label_status") != "WEAK_TEACHER"
           or r.get("pts_audit_status") != "PASS" for r in rows):
        raise ValueError("non-training or non-weak row in manifest")
    if len({r["youtube_id"] for r in rows}) < 16:
        raise ValueError("training manifest has fewer than 16 source groups")

    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    import numpy as np
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        str(BASE_MODEL), torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    processor = AutoProcessor.from_pretrained(
        str(BASE_MODEL), min_pixels=tc.MAX_PIXELS, max_pixels=tc.MAX_PIXELS)
    for _, parameter in model.named_parameters():
        parameter.requires_grad_(False)
    config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                        task_type="CAUSAL_LM")
    model = get_peft_model(model, config)
    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    if not trainable or not all("lora_" in n for n, _ in trainable):
        raise RuntimeError("unexpected trainable parameter set")
    if any("visual" in n for n, _ in trainable):
        raise RuntimeError("vision parameter became trainable")
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=args.lr)
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    started = time.monotonic()
    optimizer.zero_grad(set_to_none=True)
    step = 0
    examples_seen = 0
    loss_log = []
    completed_epochs = 0
    stop_reason = None
    torch.cuda.reset_peak_memory_stats()
    for epoch in range(args.epochs):
        order = list(range(len(rows)))
        random.Random(args.seed + epoch).shuffle(order)
        micro = 0
        for row_index in order:
            row = rows[row_index]
            encoded, _ = build_example(processor, row, torch)
            encoded = {k: (v.to("cuda") if hasattr(v, "to") else v)
                       for k, v in encoded.items()}
            keep = encoded.pop("_logits_to_keep")
            output = model(**encoded, logits_to_keep=keep)
            loss = output.loss
            if not torch.isfinite(loss):
                raise RuntimeError(f"nonfinite loss at {row['sample_id']}")
            (loss / args.grad_accum).backward()
            micro += 1
            examples_seen += 1
            if micro == args.grad_accum:
                torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1.0)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                micro = 0
                step += 1
                loss_log.append({"epoch": epoch, "optimizer_step": step,
                                 "loss": round(float(loss.item()), 6),
                                 "elapsed_seconds": round(time.monotonic() - started, 3)})
                print(f"epoch={epoch} step={step} loss={loss_log[-1]['loss']}", flush=True)
                if args.max_steps and step >= args.max_steps:
                    stop_reason = f"max_steps_{args.max_steps}"
                    break
        if micro and not (args.max_steps and step >= args.max_steps):
            for _, p in trainable:
                if p.grad is not None:
                    p.grad.mul_(args.grad_accum / micro)
            torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            step += 1
            loss_log.append({"epoch": epoch, "optimizer_step": step,
                             "loss": round(float(loss.item()), 6),
                             "elapsed_seconds": round(time.monotonic() - started, 3),
                             "partial_accumulation": micro})
        completed_epochs += 1
        if stop_reason:
            break
    if args.max_steps and step != args.max_steps:
        raise RuntimeError(f"expected exactly {args.max_steps} optimizer steps, got {step}")
    if not args.max_steps and completed_epochs != args.epochs:
        raise RuntimeError("incomplete fixed epoch training")
    adapter = args.out_dir / "adapter"
    model.save_pretrained(str(adapter))
    adapter_hash = sha256(adapter / "adapter_model.safetensors")
    base_after_training = model.unload()
    reloaded = PeftModel.from_pretrained(
        base_after_training, str(adapter), is_trainable=False)
    reload_succeeded = reloaded is not None
    elapsed = time.monotonic() - started
    report = {
        "status": "R7_TRAINING_COMPLETED_WEAK_TEACHER_ONLY",
        "manifest": str(args.manifest), "manifest_sha256": sha256(args.manifest),
        "rows": len(rows), "source_groups": len({r["youtube_id"] for r in rows}),
        "epochs_requested": args.epochs, "epochs_completed": completed_epochs,
        "max_steps": args.max_steps, "optimizer_steps": step,
        "examples_seen": examples_seen, "stop_reason": stop_reason,
        "lr": args.lr, "grad_accum": args.grad_accum, "seed": args.seed,
        "lora": {"rank": 16, "alpha": 32, "dropout": 0.05,
                 "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"]},
        "trainable_params": sum(p.numel() for _, p in trainable),
        "vision_frozen": True, "base_frozen": True,
        "loss_finite": all(math.isfinite(x["loss"]) for x in loss_log),
        "loss_log": loss_log,
        "wall_seconds": round(elapsed, 3),
        "peak_memory_allocated_mib": round(torch.cuda.max_memory_allocated() / 2**20, 2),
        "adapter_model_sha256": adapter_hash,
        "adapter_reload_succeeded": reload_succeeded,
        "environment": sys.executable,
    }
    (args.out_dir / "train_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
