#!/usr/bin/env python3
"""Run the frozen P2-T2 adapter on the official test index without manual review."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

TEMPORAL_ROOT = Path("/home/inspur/aic_video_work/temporal_round5")
sys.path.insert(0, str(TEMPORAL_ROOT / "scripts"))
import temporal_common as tc  # noqa: E402

BASE_MODEL = "/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct"
INDEX = Path("/home/inspur/aic_video_work/inference/test_index.json")
WINDOW_SEC = 30.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-index-sha256", required=True)
    parser.add_argument("--expected-adapter-sha256", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()
    import hashlib
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if sha(INDEX) != args.expected_index_sha256:
        raise RuntimeError("test index hash changed")
    adapter_file = args.adapter / "adapter_model.safetensors"
    if sha(adapter_file) != args.expected_adapter_sha256:
        raise RuntimeError("P2-T2 adapter hash changed")
    if args.output.exists():
        raise FileExistsError("refusing to overwrite temporal output")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    items = json.loads(INDEX.read_text(encoding="utf-8"))
    if len(items) != 174 or len({str(x["video_id"]) for x in items}) != 174:
        raise RuntimeError("expected 174 unique test videos")

    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    from peft import PeftModel
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(model, str(args.adapter), is_trainable=False)
    model.eval()
    processor = AutoProcessor.from_pretrained(BASE_MODEL, min_pixels=tc.MAX_PIXELS,
                                              max_pixels=tc.MAX_PIXELS)
    import decord
    messages = [{"role": "user", "content": [{"type": "text", "text": tc.PROMPT}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True, enable_thinking=False)
    prompt = prompt.replace("<|im_start|>user\n",
                            "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
    started = time.monotonic()
    total_windows = invalid_windows = 0
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for item_index, item in enumerate(items, 1):
            video_id = str(item["video_id"])
            vr = decord.VideoReader(item["video_path"])
            n_frames = len(vr)
            fps = float(vr.get_avg_fps())
            if n_frames <= 1 or fps <= 0:
                raise RuntimeError(f"invalid video metadata for {video_id}")
            duration = n_frames / fps
            windows = []
            start = 0.0
            while start < duration - 1e-6:
                end = min(start + WINDOW_SEC, duration)
                if end - start >= 0.2:
                    windows.append((start, end))
                start = end
            result = {
                "video_id": video_id, "arm": "P2T2_FINAL_FROZEN",
                "targetRatioWH": item["targetRatioWH"], "video_path": item["video_path"],
                "n_frames": n_frames, "fps": fps, "duration_sec": duration,
                "window_sec": WINDOW_SEC, "adapter": str(args.adapter), "windows": [],
            }
            for window_index, (start, end) in enumerate(windows):
                total_windows += 1
                row = {"index": window_index, "start_sec": round(start, 6),
                       "end_sec": round(end, 6), "duration_sec": round(end - start, 6)}
                try:
                    array, metadata, info = tc.build_virtual_clip(item["video_path"], start, end)
                    video = torch.from_numpy(array).permute(0, 3, 1, 2)
                    inputs = processor(text=[prompt], videos=[video], video_metadata=[metadata],
                                       padding=True, do_sample_frames=False,
                                       return_tensors="pt").to("cuda")
                    torch.cuda.reset_peak_memory_stats()
                    one_started = time.monotonic()
                    with torch.inference_mode():
                        generated = model.generate(**inputs, do_sample=False,
                                                   max_new_tokens=args.max_new_tokens)
                    torch.cuda.synchronize()
                    trimmed = [value[len(inputs["input_ids"][0]):] for value in generated]
                    raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                                 clean_up_tokenization_spaces=False)[0]
                    parsed, errors, warnings = tc.parse_segments(raw, end - start)
                    row.update(seconds=round(time.monotonic() - one_started, 6),
                               peak_memory_mib=round(torch.cuda.max_memory_allocated() / 2**20, 2),
                               raw_output=raw, parsed_segments=parsed, parse_errors=errors,
                               parse_warnings=warnings, output_valid=parsed is not None,
                               n_sampled=info["n_sampled"])
                except Exception as exc:
                    row.update(raw_output="", parsed_segments=None,
                               parse_errors=[f"{type(exc).__name__}: {exc}"],
                               parse_warnings=[], output_valid=False)
                invalid_windows += int(not row["output_valid"])
                result["windows"].append(row)
            stream.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"[{item_index}/174] video={video_id} windows={len(windows)} "
                  f"valid={sum(x['output_valid'] for x in result['windows'])}", flush=True)
    summary = {
        "status": "COMPLETED", "videos": 174, "windows": total_windows,
        "invalid_windows": invalid_windows,
        "invalid_window_rate": invalid_windows / total_windows if total_windows else 1.0,
        "wall_seconds": time.monotonic() - started, "output_sha256": sha(args.output),
        "adapter_sha256": sha(adapter_file), "index_sha256": sha(INDEX),
    }
    args.output.with_suffix(args.output.suffix + ".run.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
