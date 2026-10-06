"""Gated spatial LoRA on frozen training-only weak crop centres.

Smoke uses 16 different source groups, repeated for at most 20 optimizer steps.
Full mode uses each of the frozen training frames once.  No dev/holdout/test
image is ever read by this trainer.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
MAX_PIXELS = 128 * 32 * 32
SEED = 20260917


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def focus_prompt(tw: float, th: float) -> str:
    # Same bytes as baseline_qwen3vl.Qwen3VL.predict_focus.
    return (
        "Below is a video frame to be re-framed (cropped) to %d:%d.\n"
        "Point out the center of the most important subject or region to "
        "keep. Use normalized integer coordinates in range 0~1000: x is "
        "horizontal (0=left, 1000=right), y is vertical (0=top, "
        "1000=bottom).\n"
        "Output ONLY JSON (no other text): {\"center\": [x, y]}"
        % (int(tw), int(th))
    )


def build_example(processor, image_path: Path, row: dict, torch):
    from PIL import Image
    from qwen_vl_utils import process_vision_info

    with Image.open(image_path) as opened:
        image = opened.convert("RGB")
    if image.size != (row["source_width"], row["source_height"]):
        raise RuntimeError("training image geometry mismatch")
    tw, th = row["target_ratio_wh"]
    x, y, w, h = row["weak_roi_xywh"]
    cx = round(1000 * (x + w / 2) / image.width)
    cy = round(1000 * (y + h / 2) / image.height)
    if not (0 <= cx <= 1000 and 0 <= cy <= 1000):
        raise ValueError("weak centre outside normalized image")
    answer = json.dumps({"center": [cx, cy]}, separators=(",", ":"))
    messages = [{"role": "user", "content": [
        {"type": "image", "image": image, "max_pixels": MAX_PIXELS},
        {"type": "text", "text": focus_prompt(tw, th)}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True,
                                           enable_thinking=False)
    images, videos, kwargs = process_vision_info(
        messages, return_video_kwargs=True, return_video_metadata=True,
        image_patch_size=16)
    if not images or videos:
        raise RuntimeError("training vision processor did not return one image")
    full = prompt + answer + "<|im_end|>\n"
    common = dict(images=images, videos=None, padding=True, return_tensors="pt", **kwargs)
    encoded = processor(text=[full], **common)
    prefix = processor(text=[prompt], **common)
    ids = encoded["input_ids"][0]
    plen = int(prefix["input_ids"].shape[-1])
    if not torch.equal(ids[:plen], prefix["input_ids"][0]):
        raise RuntimeError("answer mask prefix mismatch")
    n_answer = int(ids.shape[-1]) - plen
    if n_answer < 1:
        raise RuntimeError("empty answer after processor")
    labels = ids.clone()
    labels[:plen] = -100
    k = n_answer + 1
    encoded["labels"] = labels[-k:].unsqueeze(0)
    if int((encoded["labels"] != -100).sum()) != n_answer:
        raise RuntimeError("answer token mask mismatch")
    return encoded, k, answer


def main(mode: str, manifest_name: str, extracted_name: str, out_name: str) -> int:
    if mode not in {"smoke", "full"}:
        raise ValueError("mode must be smoke or full")
    manifest, extracted_file, out = Path(manifest_name), Path(extracted_name), Path(out_name)
    rows, extracted = load_jsonl(manifest), load_jsonl(extracted_file)
    required = 16 if mode == "smoke" else 1260
    if len(rows) != required or len({r["sample_key"] for r in rows}) != required:
        raise RuntimeError("frozen training manifest changed")
    if any(r["split"] != "train" or r["label_status"] != "WEAK_TEACHER" for r in rows):
        raise RuntimeError("non-training or non-weak row")
    if mode == "smoke" and len({r["youtube_id"] for r in rows}) != 16:
        raise RuntimeError("smoke sources are not independent")
    image_by_key = {r["sample_key"]: r for r in extracted}
    if len(image_by_key) != required or set(image_by_key) != {r["sample_key"] for r in rows}:
        raise RuntimeError("extraction universe mismatch")
    gate = json.loads((extracted_file.parent / "pts_gate.json").read_text(encoding="utf-8"))
    if gate["status"] != "PTS_GATE_PASS" or gate["manifest_sha256"] != sha256(manifest):
        raise RuntimeError("training PTS gate missing or mismatched")
    for image in extracted:
        if sha256(Path(image["image_path"])) != image["image_sha256"]:
            raise RuntimeError("training image hash mismatch")
    if out.exists() and any(out.iterdir()):
        raise RuntimeError("refusing to overwrite nonempty training output")
    out.mkdir(parents=True, exist_ok=True)

    import numpy as np
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    started = time.monotonic()
    base = Qwen3VLForConditionalGeneration.from_pretrained(
        str(MODEL), torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    for _, parameter in base.named_parameters():
        parameter.requires_grad_(False)
    cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                     task_type="CAUSAL_LM")
    model = get_peft_model(base, cfg)
    trainable = [(name, p) for name, p in model.named_parameters() if p.requires_grad]
    if not trainable or any("lora_" not in n or "visual" in n or "vision" in n
                            for n, _ in trainable):
        raise RuntimeError("trainable tensors are not exclusively language LoRA")
    processor = AutoProcessor.from_pretrained(str(MODEL),
                                              min_pixels=MAX_PIXELS, max_pixels=MAX_PIXELS)
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = torch.optim.AdamW([p for _, p in trainable], lr=5e-5)
    accumulation = 16
    sequence = rows * 20 if mode == "smoke" else rows
    max_steps = 20 if mode == "smoke" else math.ceil(len(rows) / accumulation)
    seen, steps, micro, loss_log = 0, 0, 0, []
    optimizer.zero_grad(set_to_none=True)
    for index, row in enumerate(sequence, 1):
        item = image_by_key[row["sample_key"]]
        enc, keep, answer = build_example(
            processor, Path(item["image_path"]), row, torch)
        enc = enc.to("cuda")
        result = model(**enc, logits_to_keep=keep)
        raw_loss = result.loss
        if not torch.isfinite(raw_loss):
            raise RuntimeError(f"nonfinite loss on {row['sample_key']}")
        (raw_loss / accumulation).backward()
        seen += 1
        micro += 1
        if micro == accumulation or index == len(sequence):
            if micro != accumulation:
                for _, parameter in trainable:
                    if parameter.grad is not None:
                        parameter.grad.mul_(accumulation / micro)
            torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            steps += 1
            micro = 0
            loss_log.append({"step": steps, "sample_key": row["sample_key"],
                             "loss": float(raw_loss.item()),
                             "elapsed_seconds": round(time.monotonic() - started, 3)})
            print(f"{mode} step={steps}/{max_steps} seen={seen} loss={raw_loss.item():.5f}",
                  flush=True)
    if seen != len(sequence) or steps != max_steps:
        raise RuntimeError("training skipped samples or steps")
    adapter = out / "adapter"
    model.save_pretrained(str(adapter))
    if not (adapter / "adapter_model.safetensors").is_file():
        raise RuntimeError("adapter save failed")
    report = {"status": "SPATIAL_WEAK_LORA_TRAINED_NEEDS_RELOAD_AND_DEV_COMPARISON",
              "mode": mode, "base_model": str(MODEL),
              "manifest_sha256": sha256(manifest),
              "extracted_sha256": sha256(extracted_file),
              "adapter_sha256": sha256(adapter / "adapter_model.safetensors"),
              "training_rows": len(rows), "examples_seen": seen,
              "optimizer_steps": steps, "loss_finite": all(math.isfinite(x["loss"]) for x in loss_log),
              "loss_log": loss_log,
              "config": {"dtype": "bf16", "r": 16, "alpha": 32, "dropout": 0.05,
                         "lr": 5e-5, "batch": 1, "gradient_accumulation": 16,
                         "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
                         "seed": SEED},
              "trainable_parameter_count": sum(p.numel() for _, p in trainable),
              "peak_memory_mib": round(torch.cuda.max_memory_allocated() / 2**20, 2),
              "wall_seconds": round(time.monotonic() - started, 3)}
    (out / "train_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "loss_log"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
