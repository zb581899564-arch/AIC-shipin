#!/usr/bin/env python3
"""ROUND 4 — arm B (OraRL environment).

Runs on the SAME frozen frames:
  P2 : Video-ORA-4B spatial grounding with a fixed referring expression,
       bbox centre -> the CURRENT AIC crop geometry (same max legal width as P1)
  P3b: OraRL spatial grounding using the target string produced by arm A
       (P3a). No label summary / query / human description is used.

Only the bbox CENTRE from OraRL is used; the crop width stays identical to P1.
Weak-proxy boxes are never placed into a prompt.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")
QWEN_SG_PROMPT = ('Locate "{}" in the image. Output its bounding box in JSON format '
                  'within <answer>...</answer> tags. '
                  'Example: <answer>[{{"bbox_2d": [123, 30, 404, 846]}}]</answer>')

FIXED_EXPRESSION_VERTICAL = (
    "the most important visual subject or region to preserve in a vertical highlight crop")
FIXED_EXPRESSION_HORIZONTAL = (
    "the most important visual subject or region to preserve in a horizontal highlight crop")


def _compute_crop_size_from_file():
    """Load compute_crop_size from the frozen baseline WITHOUT importing torch/cv2."""
    src = BASELINE.read_text()
    start = src.index("def compute_crop_size")
    end = src.index("def center_to_box")
    ns = {"math": math, "Tuple": __import__("typing").Tuple}
    exec(src[start:end], ns)     # noqa: S102 - pinned local read-only file
    return ns["compute_crop_size"]


def _center_to_box_from_file():
    src = BASELINE.read_text()
    start = src.index("def center_to_box")
    end = src.index("def validate_box")
    ns = {"math": math, "Sequence": __import__("typing").Sequence,
          "List": __import__("typing").List,
          "Optional": __import__("typing").Optional}
    exec(src[start:end], ns)     # noqa: S102
    return ns["center_to_box"]


def _parse_sg(raw):
    """Strict parse of the OraRL spatial-grounding answer -> first bbox or (None, err)."""
    if not isinstance(raw, str) or not raw.strip():
        return None, "empty output"
    blocks = re.findall(r"<answer>(.*?)</answer>", raw, re.S | re.I)
    if len(blocks) == 0:
        return None, "no <answer> block"
    if len(blocks) > 1:
        return None, f"ambiguous: {len(blocks)} <answer> blocks"
    try:
        obj = json.loads(blocks[0].strip())
    except Exception as exc:
        return None, f"not JSON: {exc}"
    if not isinstance(obj, list) or not obj:
        return None, "not a non-empty list"
    item = obj[0]
    if not isinstance(item, dict) or "bbox_2d" not in item:
        return None, "first item lacks bbox_2d"
    b = item["bbox_2d"]
    if not (isinstance(b, list) and len(b) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in b)):
        return None, f"bbox_2d is not 4 numbers: {b!r}"
    bb = [float(v) for v in b]
    if min(bb) < 0 or max(bb) > 1000:
        return None, f"bbox outside norm1000: {bb}"
    if bb[2] <= bb[0] or bb[3] <= bb[1]:
        return None, f"bbox non-positive extent: {bb}"
    return bb, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B")
    ap.add_argument("--attn", default="sdpa")
    ap.add_argument("--max-new-tokens", type=int, default=1024)
    ap.add_argument("--out-dir", default=str(R4 / "outputs/arms"))
    args = ap.parse_args()

    os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = [json.loads(l) for l in (R4 / "evidence/frozen_frames.jsonl").read_text().splitlines()
              if l.strip()]
    frozen = json.loads((R4 / "evidence/frozen_set.json").read_text())
    gmap = {g["group_key"]: g for g in frozen["groups"]}
    targets = {}
    p3a_path = out_dir / "p3a_target.jsonl"
    if p3a_path.exists():
        for l in p3a_path.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                targets[d["frame_id"]] = d
    print(f"frozen frames: {len(frames)}; arm-A targets available: {len(targets)}")

    compute_crop_size = _compute_crop_size_from_file()
    center_to_box = _center_to_box_from_file()

    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from qwen_vl_utils import process_vision_info
    from PIL import Image

    t0 = time.time()
    model = AutoModelForImageTextToText.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation=args.attn,
        device_map={"": "cuda:0"}).eval()
    load_s = round(time.time() - t0, 2)
    processor = AutoProcessor.from_pretrained(
        args.model, padding_side="left", do_resize=False, trust_remote_code=True)
    print(f"OraRL loaded in {load_s}s")

    def ground(image_source, expression):
        """Mirror the proven round-3 spatial-grounding input path.

        The image must go through `process_vision_info` (as round 3's 42/42
        successful grounding cases did). Passing a PIL image straight to the
        processor makes qwen3_5 reshape it on the video/temporal-patch path and
        raises `shape '[1, 1, 2, 3, 9, 2, 16, 16, 2, 16]' is invalid`.
        """
        messages = [{"role": "user", "content": [
            {"type": "image", "image": image_source,
             "min_pixels": 65536, "max_pixels": 1048576},
            {"type": "text", "text": QWEN_SG_PROMPT.format(expression)}]}]
        text = processor.apply_chat_template(messages, tokenize=False,
                                            add_generation_prompt=True, enable_thinking=False)
        images, videos, video_kwargs = process_vision_info(
            messages, image_patch_size=16, return_video_kwargs=True,
            return_video_metadata=True)
        vmd = None
        if videos:
            videos, vmd = zip(*videos)
            videos, vmd = list(videos), list(vmd)
        inputs = processor(text=[text], images=images, videos=videos,
                           video_metadata=vmd, padding=True, return_tensors="pt",
                           **video_kwargs)
        inputs = inputs.to("cuda")
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=args.max_new_tokens)
        trimmed = [o[len(inputs["input_ids"][0]):] for o in out]
        return processor.batch_decode(trimmed, skip_special_tokens=True,
                                      clean_up_tokenization_spaces=False)[0]

    run = {"arm": "B", "model": args.model, "env": sys.executable,
           "attn": args.attn, "n_frames": len(frames),
           "fixed_expression": {"vertical": FIXED_EXPRESSION_VERTICAL,
                                "horizontal": FIXED_EXPRESSION_HORIZONTAL},
           "model_load_seconds": load_s,
           "started_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()}

    p2_rows, p3b_rows = [], []
    for i, fr in enumerate(frames):
        g = gmap[fr["group_key"]]
        W, H = g["source_probe"]["width"], g["source_probe"]["height"]
        tw, th = float(g["targetRatioWH"][0]), float(g["targetRatioWH"][1])
        cw, h_float = compute_crop_size(W, H, tw, th)
        pil = Image.open(fr["image_path"]).convert("RGB")
        frame_id = f"{fr['group_key']}#m{fr['moment_index']}"
        expr_fixed = FIXED_EXPRESSION_VERTICAL if th > tw else FIXED_EXPRESSION_HORIZONTAL

        # ---- P2 ----
        torch.cuda.reset_peak_memory_stats()
        t = time.time()
        try:
            raw = ground(pil, expr_fixed)
            bb, err = _parse_sg(raw)
        except Exception as exc:
            raw, bb, err = "", None, f"{type(exc).__name__}: {exc}"
        rec = {"frame_id": frame_id, "group_key": fr["group_key"],
               "youtube_id": fr["youtube_id"], "moment_index": fr["moment_index"],
               "image_path": fr["image_path"], "image_sha256": fr["image_sha256"],
               "W": W, "H": H, "targetRatioWH": [tw, th],
               "max_legal_crop_w": cw, "crop_h_float": h_float,
               "expression": expr_fixed, "raw_output": raw,
               "bbox_norm1000": bb, "parse_error": err,
               "output_valid": bb is not None,
               "seconds": round(time.time() - t, 2)}
        if bb is None:
            rec["center_norm"] = None
            rec["box_xyw"] = center_to_box(0.5, 0.5, W, H, cw, h_float)
            rec["fallback_used"] = True
        else:
            cx = (bb[0] + bb[2]) / 2.0 / 1000.0
            cy = (bb[1] + bb[3]) / 2.0 / 1000.0
            rec["center_norm"] = [round(cx, 6), round(cy, 6)]
            rec["box_xyw"] = center_to_box(cx, cy, W, H, cw, h_float)
            rec["fallback_used"] = False
        rec["peak_memory_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
        p2_rows.append(rec)

        # ---- P3b ----
        tgt = targets.get(frame_id, {})
        target = tgt.get("target")
        if not target:
            p3b_rows.append({"frame_id": frame_id, "group_key": fr["group_key"],
                             "youtube_id": fr["youtube_id"], "moment_index": fr["moment_index"],
                             "image_path": fr["image_path"], "image_sha256": fr["image_sha256"],
                             "W": W, "H": H, "targetRatioWH": [tw, th],
                             "max_legal_crop_w": cw, "crop_h_float": h_float,
                             "expression": None, "raw_output": "",
                             "bbox_norm1000": None,
                             "parse_error": f"upstream target unavailable/failed: "
                                            f"{tgt.get('parse_error')}",
                             "output_valid": False, "fallback_used": True,
                             "center_norm": None,
                             "box_xyw": center_to_box(0.5, 0.5, W, H, cw, h_float),
                             "seconds": 0.0, "peak_memory_mib": None})
            continue
        t = time.time()
        try:
            raw = ground(pil, target)
            bb, err = _parse_sg(raw)
        except Exception as exc:
            raw, bb, err = "", None, f"{type(exc).__name__}: {exc}"
        rec3 = {"frame_id": frame_id, "group_key": fr["group_key"],
                "youtube_id": fr["youtube_id"], "moment_index": fr["moment_index"],
                "image_path": fr["image_path"], "image_sha256": fr["image_sha256"],
                "W": W, "H": H, "targetRatioWH": [tw, th],
                "max_legal_crop_w": cw, "crop_h_float": h_float,
                "expression": target, "raw_output": raw, "bbox_norm1000": bb,
                "parse_error": err, "output_valid": bb is not None,
                "seconds": round(time.time() - t, 2)}
        if bb is None:
            rec3["center_norm"] = None
            rec3["box_xyw"] = center_to_box(0.5, 0.5, W, H, cw, h_float)
            rec3["fallback_used"] = True
        else:
            cx = (bb[0] + bb[2]) / 2.0 / 1000.0
            cy = (bb[1] + bb[3]) / 2.0 / 1000.0
            rec3["center_norm"] = [round(cx, 6), round(cy, 6)]
            rec3["box_xyw"] = center_to_box(cx, cy, W, H, cw, h_float)
            rec3["fallback_used"] = False
        rec3["peak_memory_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
        p3b_rows.append(rec3)
        if i % 10 == 0:
            print(f"  [{i+1}/{len(frames)}] {frame_id} p2_valid={rec['output_valid']} "
                  f"p3_target={target!r} p3b_valid={rec3['output_valid']}")

    for name, rows in (("p2_orarl.jsonl", p2_rows), ("p3b_orarl.jsonl", p3b_rows)):
        with (out_dir / name).open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    run.update(finished_utc=subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
               n_p2=len(p2_rows), n_p3b=len(p3b_rows),
               p2_valid=sum(1 for r in p2_rows if r["output_valid"]),
               p3b_valid=sum(1 for r in p3b_rows if r["output_valid"]),
               peak_memory_mib=max(r["peak_memory_mib"] or 0 for r in p2_rows + p3b_rows),
               total_seconds=round(sum(r["seconds"] for r in p2_rows)
                                   + sum(r["seconds"] for r in p3b_rows), 1))
    (out_dir / "arm_b_run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(run, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
