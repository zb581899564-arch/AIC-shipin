#!/usr/bin/env python3
"""temporal_round5 — Phase C: query-free temporal LoRA (S1_FRESH / S2_WARM).

Design (fixed by the brief, not tuned here):
  * the training target contains ONLY the query-free prompt and the weak-label
    `segments`; the loss covers ONLY the assistant answer tokens
  * vision tower and the original language weights are FROZEN; only LoRA on the
    language attention projections q_proj / k_proj / v_proj / o_proj is trained
  * BF16, rank 16, alpha 32, dropout 0.05, batch 1, grad-accum 16, fixed seed
  * S1_FRESH starts a new LoRA from the base model at lr 5e-5
  * S2_WARM continues the current adapter at lr 2e-5 with its own rank /
    target modules / alpha / dropout preserved

The answer string is the same unified JSON the evaluator parses:
  {"segments": [[start_sec, end_sec], ...]}   (clip-local seconds)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

R5 = Path("/home/inspur/aic_video_work/temporal_round5")
sys.path.insert(0, str(R5 / "scripts"))
import temporal_common as tc  # noqa: E402

BASE_MODEL = "/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct"
CURRENT_ADAPTER = "/home/inspur/aic_video_work/training_round2_20260910/formal_v1/best"
SEED = 20260916


def answer_string(segments):
    return json.dumps({"segments": [[round(a, 4), round(b, 4)] for a, b in segments]},
                      separators=(",", ":"))


def build_example(processor, row, torch):
    """Return (inputs, labels) with labels masked to the assistant answer only."""
    arr, md, info = tc.build_virtual_clip(
        row["source_path"], row["clip_start_sec"], row["clip_end_sec"])
    ans = answer_string(row["segments_clip_local"])
    msgs = [{"role": "user", "content": [{"type": "text", "text": tc.PROMPT}]}]
    text = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                        enable_thinking=False)
    text = text.replace("<|im_start|>user\n",
                        "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
    tensor = torch.from_numpy(arr).permute(0, 3, 1, 2)
    # prompt-only forward gives the prompt length; full text gives the target
    full = text + ans + "<|im_end|>\n"
    enc = processor(text=[full], videos=[tensor], video_metadata=[md], padding=True,
                    do_sample_frames=False, return_tensors="pt")
    prompt_enc = processor(text=[text], videos=[tensor], video_metadata=[md], padding=True,
                           do_sample_frames=False, return_tensors="pt")
    ids = enc["input_ids"][0]
    labels = ids.clone()
    plen = int(prompt_enc["input_ids"].shape[-1])
    labels[:plen] = -100
    # `logits_to_keep=k` truncates ONLY the logits, so the labels must be sliced
    # to the same tail length k. The internal shift-by-one then drops the single
    # leading prompt token and every remaining label is an answer token.
    n_answer = int(ids.shape[-1]) - plen
    k = max(2, n_answer + 1)
    enc["labels"] = labels[-k:].unsqueeze(0)
    enc["_logits_to_keep"] = k
    return enc, plen, int(ids.shape[-1]), info, ans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["S1_FRESH", "S2_WARM"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-samples", type=int, default=0, help="0 = full split")
    ap.add_argument("--max-steps", type=int, default=0, help="0 = no step cap")
    ap.add_argument("--lr", type=float, default=0.0)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--max-seconds", type=int, default=0, help="wall-clock stop")
    args = ap.parse_args()

    if args.lr == 0.0:
        args.lr = 5e-5 if args.arm == "S1_FRESH" else 2e-5

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = tc.load_split("train", R5)
    if args.max_samples:
        rows = rows[: args.max_samples]
    print(f"{args.arm}: train rows={len(rows)} lr={args.lr} epochs={args.epochs} "
          f"grad_accum={args.grad_accum} max_steps={args.max_steps or 'none'}")

    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    torch.manual_seed(args.seed)
    import random
    import numpy as np
    random.seed(args.seed)
    np.random.seed(args.seed)

    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    processor = AutoProcessor.from_pretrained(
        BASE_MODEL, min_pixels=tc.MAX_PIXELS, max_pixels=tc.MAX_PIXELS)

    # freeze the vision tower explicitly
    visual_names = [n for n, _ in model.named_parameters() if "visual" in n]
    for n, p in model.named_parameters():
        p.requires_grad_(False)

    from peft import LoraConfig, get_peft_model, PeftModel
    cfg = dict(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
               target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
               task_type="CAUSAL_LM")
    if args.arm == "S2_WARM":
        ac = json.loads((Path(CURRENT_ADAPTER) / "adapter_config.json").read_text())
        cfg = {"r": ac["r"], "lora_alpha": ac["lora_alpha"],
               "lora_dropout": ac["lora_dropout"], "bias": ac.get("bias", "none"),
               "target_modules": ac["target_modules"], "task_type": ac["task_type"]}
        model = PeftModel.from_pretrained(model, CURRENT_ADAPTER, is_trainable=True)
        print("warm start config from adapter:", json.dumps(cfg))
    else:
        model = get_peft_model(model, LoraConfig(**cfg))

    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    n_train = sum(p.numel() for _, p in trainable)
    base_hash = hashlib.sha256()
    for n, p in sorted(model.named_parameters()):
        if not p.requires_grad:
            base_hash.update(n.encode())
    print(f"trainable tensors={len(trainable)} params={n_train}")
    assert all(("lora_" in n) for n, _ in trainable), "non-LoRA tensor is trainable"
    assert not any(("visual" in n) for n, _ in trainable), "vision tower is trainable!"

    opt = torch.optim.AdamW([p for _, p in trainable], lr=args.lr)
    # gradient checkpointing keeps activations for 64-frame clips affordable;
    # frozen embeddings need input grads enabled for it to work under PEFT
    try:
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False})
        print("gradient checkpointing enabled")
    except Exception as exc:
        print("gradient checkpointing unavailable:", exc)
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    model.train()
    t_start = time.time()
    log = []
    step = 0
    stop_reason = None
    for ep in range(args.epochs):
        opt.zero_grad(set_to_none=True)
        micro = 0
        for i, r in enumerate(rows):
            if args.max_seconds and (time.time() - t_start) > args.max_seconds:
                stop_reason = f"wall clock {args.max_seconds}s reached"
                break
            try:
                enc, plen, tlen, info, ans = build_example(processor, r, torch)
            except Exception as exc:
                log.append({"epoch": ep, "i": i, "sample": r["sample_id"],
                            "skipped": f"{type(exc).__name__}: {exc}"})
                continue
            enc = {k: (v.to("cuda") if hasattr(v, "to") else v) for k, v in enc.items()}
            ltk = enc.pop("_logits_to_keep", None)
            fwd = dict(enc)
            if ltk:
                fwd["logits_to_keep"] = ltk
            outs = model(**fwd)
            loss = outs.loss / args.grad_accum
            if not torch.isfinite(loss):
                log.append({"epoch": ep, "i": i, "sample": r["sample_id"],
                            "nonfinite_loss": float(loss)})
                opt.zero_grad(set_to_none=True)
                micro = 0
                continue
            loss.backward()
            micro += 1
            if micro == args.grad_accum:
                torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1.0)
                opt.step()
                opt.zero_grad(set_to_none=True)
                micro = 0
                step += 1
                log.append({"epoch": ep, "optimizer_step": step,
                            "loss": round(float(loss.item()) * args.grad_accum, 6),
                            "elapsed_s": round(time.time() - t_start, 1)})
                if step % 5 == 0:
                    print(f"  ep{ep} step{step} loss={log[-1]['loss']:.4f} "
                          f"elapsed={log[-1]['elapsed_s']}s")
                if args.max_steps and step >= args.max_steps:
                    stop_reason = f"max_steps {args.max_steps} reached"
                    break
            if i % 50 == 0:
                print(f"  [{ep} {i}/{len(rows)}] micro={micro} step={step}")
        if stop_reason:
            break
        # flush any partial accumulation at epoch end
        if micro > 0 and not (args.max_steps and step >= args.max_steps):
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
        ckpt = out / f"epoch_{ep+1}"
        model.save_pretrained(str(ckpt))
        print(f"  saved {ckpt} (steps={step})")

    final = out / "final"
    model.save_pretrained(str(final))
    (out / "train_report.json").write_text(json.dumps({
        "arm": args.arm, "lr": args.lr, "epochs": args.epochs,
        "max_samples": args.max_samples, "max_steps": args.max_steps,
        "grad_accum": args.grad_accum, "seed": args.seed,
        "lora_config": cfg, "trainable_params": n_train,
        "trainable_tensors": len(trainable),
        "frozen_base_names_hashed": base_hash.hexdigest(),
        "optimizer_steps": step, "stop_reason": stop_reason,
        "wall_seconds": round(time.time() - t_start, 1),
        "loss_log": log, "n_train_rows": len(rows),
        "final_checkpoint": str(final),
        "env": sys.executable,
        "versions": {"torch": torch.__version__,
                     "transformers": __import__("transformers").__version__,
                     "peft": __import__("peft").__version__},
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"DONE arm={args.arm} steps={step} stop={stop_reason} "
          f"wall={round(time.time()-t_start,1)}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
