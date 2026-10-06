"""Frozen weak-dev temporal inference with the historical query-free prompt.

Run on training clips only.  Raw answers and parser failures are retained;
teacher-derived scores are computed separately after both arms finish.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

R5 = Path("/home/inspur/aic_video_work/temporal_round5")
sys.path.insert(0, str(R5 / "scripts"))
import temporal_common as tc

BASE_MODEL = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
S2_ADAPTER = Path("/home/inspur/aic_video_work/temporal_round5/runs/S2_WARM_epochs3_v2/epoch_3")
VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(arm: str, manifest_name: str, output_name: str) -> int:
    if arm not in {"BASE", "S2"}:
        raise ValueError("arm must be BASE or S2")
    manifest, output = Path(manifest_name), Path(output_name)
    rows = [json.loads(s) for s in manifest.read_text(encoding="utf-8").splitlines() if s.strip()]
    if len(rows) != 82 or len({r["video_id"] for r in rows}) != len(rows):
        raise ValueError("frozen dev universe changed")
    if output.exists() or output.with_suffix(output.suffix + ".partial").exists():
        raise RuntimeError("refusing to overwrite prior temporal output")
    for row in rows:
        source = Path(row["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents:
            raise ValueError("non-training source path")

    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    started = time.monotonic()
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        str(BASE_MODEL), torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    if arm == "S2":
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(S2_ADAPTER), is_trainable=False)
    model.eval()
    load_seconds = round(time.monotonic() - started, 3)
    processor = AutoProcessor.from_pretrained(
        str(BASE_MODEL), min_pixels=tc.MAX_PIXELS, max_pixels=tc.MAX_PIXELS)
    # Initialize CUDA before importing decord on this training host.
    torch.cuda.synchronize()
    import decord  # noqa: F401

    prompt = processor.apply_chat_template(
        [{"role": "user", "content": [{"type": "text", "text": tc.PROMPT}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    prompt = prompt.replace("<|im_start|>user\n",
                            "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    failures, peak_mib = 0, 0.0
    with partial.open("w", encoding="utf-8") as stream:
        for index, row in enumerate(rows, 1):
            duration = float(row["clip_end_sec"] - row["clip_start_sec"])
            rec = {"arm": arm, "video_id": row["video_id"],
                   "youtube_id": row["youtube_id"], "row_index": row["row_index"],
                   "clip_duration_sec": duration, "label_status": "WEAK_TEACHER"}
            one_start = time.monotonic()
            try:
                arr, md, info = tc.build_virtual_clip(
                    row["source_path"], row["clip_start_sec"], row["clip_end_sec"])
                video = torch.from_numpy(arr).permute(0, 3, 1, 2)
                inputs = processor(text=[prompt], videos=[video], video_metadata=[md],
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
                rec.update(raw_output=raw, parsed_segments=parsed,
                           parse_errors=errors, parse_warnings=warnings,
                           output_valid=parsed is not None, sampled_frames=info["n_sampled"],
                           peak_memory_mib=round(torch.cuda.max_memory_allocated() / 2**20, 2))
            except Exception as exc:
                rec.update(raw_output="", parsed_segments=None, output_valid=False,
                           parse_errors=[f"{type(exc).__name__}: {exc}"],
                           peak_memory_mib=None)
            rec["seconds"] = round(time.monotonic() - one_start, 3)
            failures += not rec["output_valid"]
            peak_mib = max(peak_mib, rec["peak_memory_mib"] or 0)
            stream.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            if index % 10 == 0:
                print(f"{arm} {index}/{len(rows)} invalid={failures}", flush=True)
    partial.replace(output)
    report = {"status": "COMPLETED_WEAK_DEV_TEMPORAL_BASELINE", "arm": arm,
              "manifest_sha256": sha256(manifest), "output_sha256": sha256(output),
              "temporal_common_sha256": sha256(R5 / "scripts" / "temporal_common.py"),
              "adapter_sha256": sha256(S2_ADAPTER / "adapter_model.safetensors") if arm == "S2" else None,
              "rows": len(rows), "invalid": failures, "model_load_seconds": load_seconds,
              "total_wall_seconds": round(time.monotonic() - started, 3),
              "peak_memory_mib": peak_mib, "official_status": "NOT_OFFICIAL_SCORE"}
    output.with_suffix(".run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
