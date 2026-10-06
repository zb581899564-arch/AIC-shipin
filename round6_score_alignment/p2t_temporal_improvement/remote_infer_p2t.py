#!/usr/bin/env python3
"""Inference for a frozen P2-T manifest with an explicit adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if args.output.exists() or args.output.with_suffix(args.output.suffix + ".partial").exists():
        raise RuntimeError("refusing to overwrite inference output")
    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines()
            if x.strip()]
    if args.limit:
        rows = rows[:args.limit]
    if not rows or len({r["video_id"] for r in rows}) != len(rows):
        raise ValueError("empty or duplicate inference manifest")

    import torch
    from peft import PeftModel
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    started = time.monotonic()
    base = Qwen3VLForConditionalGeneration.from_pretrained(
        str(BASE_MODEL), torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(base, str(args.adapter), is_trainable=False)
    model.eval()
    processor = AutoProcessor.from_pretrained(
        str(BASE_MODEL), min_pixels=tc.MAX_PIXELS, max_pixels=tc.MAX_PIXELS)
    torch.cuda.synchronize()
    import decord  # noqa: F401
    messages = [{"role": "user", "content": [{"type": "text", "text": tc.PROMPT}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True,
                                           enable_thinking=False)
    prompt = prompt.replace("<|im_start|>user\n",
                            "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = args.output.with_suffix(args.output.suffix + ".partial")
    failures = 0
    peak = 0.0
    with partial.open("x", encoding="utf-8") as stream:
        for row in rows:
            duration = float(row["clip_end_sec"] - row["clip_start_sec"])
            rec = {"arm": "P2T_FRESH", "video_id": row["video_id"],
                   "youtube_id": row["youtube_id"], "row_index": row["row_index"],
                   "clip_duration_sec": duration, "label_status": "WEAK_TEACHER"}
            one = time.monotonic()
            try:
                arr, metadata, info = tc.build_virtual_clip(
                    row["source_path"], row["clip_start_sec"], row["clip_end_sec"])
                video = torch.from_numpy(arr).permute(0, 3, 1, 2)
                inputs = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                                   padding=True, do_sample_frames=False,
                                   return_tensors="pt").to("cuda")
                torch.cuda.reset_peak_memory_stats()
                with torch.inference_mode():
                    generated = model.generate(**inputs, do_sample=False, max_new_tokens=256)
                torch.cuda.synchronize()
                trimmed = [g[len(inputs["input_ids"][0]):] for g in generated]
                raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                             clean_up_tokenization_spaces=False)[0]
                parsed, errors, warnings = tc.parse_segments(raw, duration)
                rec.update(raw_output=raw, parsed_segments=parsed, parse_errors=errors,
                           parse_warnings=warnings, output_valid=parsed is not None,
                           sampled_frames=info["n_sampled"],
                           peak_memory_mib=round(torch.cuda.max_memory_allocated() / 2**20, 2))
            except Exception as exc:
                rec.update(raw_output="", parsed_segments=None, output_valid=False,
                           parse_errors=[f"{type(exc).__name__}: {exc}"],
                           parse_warnings=[], peak_memory_mib=None)
            rec["seconds"] = round(time.monotonic() - one, 3)
            failures += not rec["output_valid"]
            peak = max(peak, rec["peak_memory_mib"] or 0.0)
            stream.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
    partial.replace(args.output)
    report = {"status": "INFERENCE_COMPLETED_WEAK_DEV", "rows": len(rows),
              "invalid": failures, "valid_rate": (len(rows) - failures) / len(rows),
              "manifest_sha256": sha256(args.manifest),
              "adapter_model_sha256": sha256(args.adapter / "adapter_model.safetensors"),
              "output_sha256": sha256(args.output),
              "wall_seconds": round(time.monotonic() - started, 3),
              "peak_memory_mib": peak, "environment": sys.executable}
    args.output.with_suffix(args.output.suffix + ".run.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    # Parse-invalid model answers are quality outcomes, not execution errors.
    # They stay in the completed output and the downstream metric denominator.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
