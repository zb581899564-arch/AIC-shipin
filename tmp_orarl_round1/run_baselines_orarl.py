#!/usr/bin/env python3
"""temporal_round5 — Phase B: T2_ORARL_TEMPORAL on the dev split.

Uses Video-ORA-4B's temporal-grounding interface with the author's temporal
prompt verbatim (eval/task/eval_prompt.py TEMPORAL_GROUNDING_PROMPT) and the
author's temporal sampling preferences, subject to the round-5 rule that every
arm uses the SAME virtual clip with a 64-frame cap.

One FIXED expression is used, no prompt search:
  "the moments most worth retaining in a short highlight edit"

The author's protocol returns a single span; it is parsed and then converted to
the unified JSON {"segments": [[start, end]]}.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

R5 = Path("/home/inspur/aic_video_work/temporal_round5")
sys.path.insert(0, str(R5 / "scripts"))
import temporal_common as tc  # noqa: E402

MODEL = "/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B"
EXPRESSION = "the moments most worth retaining in a short highlight edit"
TEMPORAL_GROUNDING_PROMPT = (
    'To accurately pinpoint the event "{}" in the video, '
    "determine the precise time period of the event. "
    "Provide the start and end times (in seconds) "
    'in the format "start time to end time" within <answer> </answer> tags. '
    "Example: <answer> 12 to 18 </answer>"
)
_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)"
_SPAN_RE = re.compile(r"^\s*(" + _NUM + r")\s*(?:to|until|through|-|–|—|,|~)\s*(" + _NUM + r")\s*$",
                      re.I)


def parse_span(raw):
    """Strict: exactly one <answer> block containing exactly two numbers."""
    if not isinstance(raw, str) or not raw.strip():
        return None, ["empty model output"]
    blocks = re.findall(r"<answer>(.*?)</answer>", raw, re.S | re.I)
    if len(blocks) == 0:
        return None, ["no <answer> block"]
    if len(blocks) > 1:
        return None, [f"ambiguous: {len(blocks)} <answer> blocks"]
    body = blocks[0].strip()
    nums = re.findall(_NUM, body)
    if len(nums) != 2:
        return None, [f"expected exactly 2 numbers, found {len(nums)} in {body!r}"]
    m = _SPAN_RE.match(body)
    if not m:
        return None, [f"body is not '<start> to <end>': {body!r}"]
    return [float(m.group(1)), float(m.group(2))], []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    args = ap.parse_args()

    os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")
    rows = tc.load_split(args.split, R5)
    if args.limit:
        rows = rows[: args.limit]
    print(f"T2_ORARL_TEMPORAL: split={args.split} rows={len(rows)}")

    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    t0 = time.time()
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL, dtype=torch.bfloat16, attn_implementation="sdpa",
        device_map={"": "cuda:0"}).eval()
    load_s = round(time.time() - t0, 2)
    processor = AutoProcessor.from_pretrained(
        MODEL, padding_side="left", do_resize=False, trust_remote_code=True)
    print(f"OraRL loaded in {load_s}s")

    prompt = TEMPORAL_GROUNDING_PROMPT.format(EXPRESSION)
    res = {"arm": "T2_ORARL_TEMPORAL", "split": args.split, "model": MODEL,
           "expression": EXPRESSION, "prompt": prompt,
           "sampling": {"fps_preference": 4, "max_frames": tc.MAX_FRAMES,
                        "max_pixels": 409600, "note": "64-frame cap per round-5 rule"},
           "load_seconds": load_s, "env": sys.executable,
           "started_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"],
                                                  text=True).strip(),
           "rows": []}
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
                {"type": "text", "text": prompt}]}]
            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
                enable_thinking=False)
            # Qwen3.5's video processor rejects a directly supplied frame tensor
            # (round-4 G4). Materialize ONE temporary clip file whose timeline
            # starts at 0 and route it through process_vision_info.
            tmp = R5 / "frames/tmpclip" / f"{r['sample_id']}.mp4"
            try:
                tc.materialize_clip_file(r["source_path"], r["clip_start_sec"],
                                         r["clip_end_sec"], tmp)
                from qwen_vl_utils import process_vision_info
                msgs = [{"role": "user", "content": [
                    {"type": "video", "video": str(tmp), "fps": 4,
                     "max_frames": tc.MAX_FRAMES, "min_pixels": 4096,
                     "max_pixels": 409600, "total_pixels": 8388608},
                    {"type": "text", "text": prompt}]}]
                text = processor.apply_chat_template(
                    msgs, tokenize=False, add_generation_prompt=True,
                    enable_thinking=False)
                images, videos, vkw = process_vision_info(
                    msgs, image_patch_size=16, return_video_kwargs=True,
                    return_video_metadata=True)
                vmd = None
                if videos:
                    videos, vmd = zip(*videos)
                    videos, vmd = list(videos), list(vmd)
                rec["clip_file"] = str(tmp)
                inputs = processor(text=[text], images=images, videos=videos,
                                   video_metadata=vmd, padding=True,
                                   return_tensors="pt", **vkw)
                if vmd:
                    g = (lambda k: vmd[0].get(k)) if isinstance(vmd[0], dict) \
                        else (lambda k: getattr(vmd[0], k, None))
                    fi = g("frames_indices")
                    fi = fi.tolist() if hasattr(fi, "tolist") else fi
                    rec["model_frames_indices"] = fi
                    rec["model_fps"] = g("fps")
            finally:
                try:
                    tmp.unlink()
                except Exception:
                    pass
            rec["input_ids_len"] = int(inputs["input_ids"].shape[-1])
            inputs = inputs.to("cuda")
            torch.cuda.reset_peak_memory_stats()
            ts = time.time()
            with torch.inference_mode():
                out = model.generate(**inputs, do_sample=False,
                                     max_new_tokens=args.max_new_tokens)
            torch.cuda.synchronize()
            rec["seconds"] = round(time.time() - ts, 2)
            rec["peak_memory_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
            trimmed = [o[len(inputs["input_ids"][0]):] for o in out]
            raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                        clean_up_tokenization_spaces=False)[0]
            rec["raw_output"] = raw
            span, errs = parse_span(raw)
            if span is None:
                rec.update(parsed_segments=None, parse_errors=errs, output_valid=False)
            else:
                a, b = span
                if not (0 <= a < b <= r["clip_duration_sec"] + 1e-3):
                    rec.update(parsed_segments=None, output_valid=False,
                               parse_errors=[f"span [{a},{b}] outside clip "
                                             f"[0,{r['clip_duration_sec']}]"])
                else:
                    segs = [[round(a, 4), round(min(b, r["clip_duration_sec"]), 4)]]
                    rec.update(parsed_segments=segs, parse_errors=[], output_valid=True,
                               unified_json={"segments": segs})
            m = tc.interval_metrics(rec.get("parsed_segments") or [],
                                    r["segments_clip_local"], r["clip_duration_sec"])
            rec["metrics"] = m
            rec["pred_duration_ratio"] = round(
                tc.union_length(rec.get("parsed_segments") or []) / r["clip_duration_sec"], 6)
            rec["empty_prediction"] = bool(not rec.get("parsed_segments"))
        except Exception as exc:
            import traceback
            rec.update(output_valid=False, parsed_segments=None,
                       parse_errors=[f"{type(exc).__name__}: {exc}"],
                       traceback=traceback.format_exc(), raw_output="",
                       metrics={"precision": 0.0, "recall": 0.0, "f1": 0.0},
                       pred_duration_ratio=0.0, empty_prediction=True)
        per_row.append(rec)
        if i % 10 == 0:
            print(f"  [{i+1}/{len(rows)}] {rec['sample_id']} valid={rec['output_valid']} "
                  f"f1={rec['metrics'].get('f1')} raw={rec.get('raw_output','')[:70]!r}")

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
