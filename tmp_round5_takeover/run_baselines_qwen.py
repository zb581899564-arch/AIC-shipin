#!/usr/bin/env python3
"""temporal_round5 — Phase B: T0_BASE and T1_QVH_LORA on the dev split.

Both arms use the SAME virtual clip, the SAME query-free prompt, the SAME
max-64-frame sampling and the SAME strict parser. Only the adapter differs.

  T0_BASE      : base Qwen3-VL, no adapter
  T1_QVH_LORA  : the current 43.4800 adapter (rank 16, alpha 32, dropout 0.05,
                 target modules q/k/v/o_proj)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

R5 = Path("/home/inspur/aic_video_work/temporal_round5")
sys.path.insert(0, str(R5 / "scripts"))
import temporal_common as tc  # noqa: E402

BASE_MODEL = "/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct"
ADAPTER = "/home/inspur/aic_video_work/training_round2_20260910/formal_v1/best"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["T0_BASE", "T1_QVH_LORA"])
    ap.add_argument("--split", default="dev")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--probe-one", action="store_true",
                    help="run a single row and dump the timestamps the model receives")
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = tc.load_split(args.split, R5)
    if args.limit:
        rows = rows[: args.limit]
    print(f"{args.arm}: split={args.split} rows={len(rows)}")

    import torch
    from transformers import AutoProcessor
    from transformers import Qwen3VLForConditionalGeneration

    t0 = time.time()
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    if args.arm == "T1_QVH_LORA":
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, ADAPTER, is_trainable=False)
    model.eval()
    load_s = round(time.time() - t0, 2)
    processor = AutoProcessor.from_pretrained(
        BASE_MODEL, min_pixels=tc.MAX_PIXELS, max_pixels=tc.MAX_PIXELS)
    print(f"loaded in {load_s}s; adapter={ADAPTER if args.arm=='T1_QVH_LORA' else None}")

    # frozen visual / base-weight hashes for the "weights unchanged" gate
    def visual_hash():
        import hashlib
        h = hashlib.sha256()
        for n, p in sorted(model.named_parameters()):
            if ".visual." in n or "vision" in n:
                h.update(n.encode())
                h.update(p.detach().to("cpu").float().numpy().tobytes()[:4096])
        return h.hexdigest()

    res = {"arm": args.arm, "split": args.split, "model": BASE_MODEL,
           "adapter": ADAPTER if args.arm == "T1_QVH_LORA" else None,
           "prompt": tc.PROMPT, "max_frames": tc.MAX_FRAMES,
           "max_pixels": tc.MAX_PIXELS, "load_seconds": load_s,
           "env": sys.executable,
           "started_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"],
                                                  text=True).strip(),
           "visual_hash": visual_hash(), "rows": []}

    from PIL import Image
    per_row = []
    for i, r in enumerate(rows):
        rec = {"sample_id": r["sample_id"], "youtube_id": r["youtube_id"],
               "row_index": r["row_index"], "source_path": r["source_path"],
               "clip_start_sec": r["clip_start_sec"], "clip_end_sec": r["clip_end_sec"],
               "clip_duration_sec": r["clip_duration_sec"],
               "gt_segments_clip_local": r["segments_clip_local"],
               "label_status": r["label_status"]}
        try:
            arr, md, info = tc.build_virtual_clip(
                r["source_path"], r["clip_start_sec"], r["clip_end_sec"])
            rec["clip_info"] = info
            messages = [{"role": "user", "content": [
                {"type": "text", "text": tc.PROMPT}]}]
            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
                enable_thinking=False)
            # insert the video placeholder ahead of the text
            text = text.replace("<|im_start|>user\n",
                                "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)
            tensor = torch.from_numpy(arr).permute(0, 3, 1, 2)     # T,C,H,W
            # The video processor defaults to do_sample_frames=True and would
            # re-sample the 64 frames we already selected (indexing past the
            # tensor). We supply the sampling ourselves, so it must be off; the
            # timestamps still come from video_metadata.
            model_inputs = processor(text=[text], videos=[tensor],
                                     video_metadata=[md], padding=True,
                                     do_sample_frames=False,
                                     return_tensors="pt")
            rec["input_ids_len"] = int(model_inputs["input_ids"].shape[-1])
            rec["video_grid_thw"] = model_inputs.get("video_grid_thw").tolist() \
                if "video_grid_thw" in model_inputs else None
            if args.probe_one:
                ids = model_inputs["input_ids"][0].tolist()
                dec = processor.tokenizer.decode(ids, skip_special_tokens=False)
                import re as _re
                rec["time_literals_in_input"] = _re.findall(
                    r"<[0-9]+\.[0-9] seconds>", dec)
                rec["decoded_head"] = dec[:300]
            model_inputs = model_inputs.to("cuda")
            torch.cuda.reset_peak_memory_stats()
            ts = time.time()
            with torch.inference_mode():
                out = model.generate(**model_inputs, do_sample=False,
                                     max_new_tokens=args.max_new_tokens)
            torch.cuda.synchronize()
            rec["seconds"] = round(time.time() - ts, 2)
            rec["peak_memory_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
            trimmed = [o[len(model_inputs["input_ids"][0]):] for o in out]
            raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                        clean_up_tokenization_spaces=False)[0]
            rec["raw_output"] = raw
            segs, errs, warns = tc.parse_segments(raw, r["clip_duration_sec"])
            rec["parsed_segments"] = segs
            rec["parse_errors"] = errs
            rec["parse_warnings"] = warns
            rec["output_valid"] = segs is not None
            m = tc.interval_metrics(segs or [], r["segments_clip_local"],
                                    r["clip_duration_sec"])
            rec["metrics"] = m
            rec["pred_duration_ratio"] = round(
                tc.union_length(segs or []) / r["clip_duration_sec"], 6)
            rec["empty_prediction"] = bool(not segs)
        except Exception as exc:
            import traceback
            rec.update(output_valid=False, parsed_segments=None,
                       parse_errors=[f"{type(exc).__name__}: {exc}"],
                       traceback=traceback.format_exc(), raw_output="",
                       metrics={"precision": 0.0, "recall": 0.0, "f1": 0.0},
                       pred_duration_ratio=0.0, empty_prediction=True)
        per_row.append(rec)
        if args.probe_one or i % 10 == 0:
            print(f"  [{i+1}/{len(rows)}] {rec['sample_id']} valid={rec['output_valid']} "
                  f"f1={rec['metrics'].get('f1')} raw={rec.get('raw_output','')[:80]!r}")
        if args.probe_one:
            break

    res["rows"] = per_row
    res["finished_utc"] = subprocess.check_output(["date", "-u", "+%FT%TZ"],
                                                 text=True).strip()
    n = len(per_row)
    res["summary"] = {
        "n_rows": n,
        "valid_rate": round(sum(1 for r in per_row if r["output_valid"]) / n, 4) if n else None,
        "empty_rate": round(sum(1 for r in per_row if r["empty_prediction"]) / n, 4) if n else None,
        "mean_f1": round(sum(r["metrics"]["f1"] for r in per_row) / n, 6) if n else None,
        "mean_precision": round(sum(r["metrics"]["precision"] for r in per_row) / n, 6) if n else None,
        "mean_recall": round(sum(r["metrics"]["recall"] for r in per_row) / n, 6) if n else None,
        "mean_pred_duration_ratio": round(
            sum(r["pred_duration_ratio"] for r in per_row) / n, 6) if n else None,
        "total_generate_seconds": round(sum(r.get("seconds", 0) for r in per_row), 1),
        "peak_memory_mib": max((r.get("peak_memory_mib") or 0) for r in per_row) if n else None,
    }
    Path(args.out).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(res["summary"], indent=2, ensure_ascii=False))
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
