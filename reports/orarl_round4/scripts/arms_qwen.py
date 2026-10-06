#!/usr/bin/env python3
"""ROUND 4 — arm A (current Qwen3-VL environment).

Runs, on the FROZEN frames only, using the FROZEN baseline entry read-only:
  P1 : official `Qwen3VL.predict_focus` (verbatim prompt + verbatim
       `parse_focus_norm` + verbatim `center_to_box`), max legal crop width
  P3a: the SAME model asked for a single-subject referring expression
       ({"target": ...}); its output is consumed later by arm B.

Nothing here writes a prompt, parser or post-process of its own for P1.
Writes outputs/arms/p1_qwen.jsonl and p3a_target.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")

P3_PROMPT = (
    "Below is a video frame to be re-framed (cropped) to {tw}:{th}.\n"
    "Name the SINGLE most important subject or region to keep in the crop.\n"
    "Requirements:\n"
    "- output a short unambiguous referring expression (a few words) that identifies "
    "exactly ONE subject or region visible in this image\n"
    "- do not output coordinates, numbers or boxes\n"
    "- if several subjects are present, choose the one that matters most for the crop\n"
    'Output ONLY JSON (no other text): {{"target": "a short unambiguous referring expression"}}'
)


def load_baseline():
    spec = importlib.util.spec_from_file_location("baseline_qwen3vl", BASELINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


_TARGET_RE = re.compile(r'\{\s*"target"\s*:\s*"(?P<t>[^"]*)"\s*\}')


def parse_target(raw):
    """Strict: exactly one {"target": "..."} object, non-empty, no second object.

    Returns (target|None, error). Empty / multiple / unparseable => failure.
    """
    if not isinstance(raw, str) or not raw.strip():
        return None, "empty model output"
    objs = re.findall(r"\{[^{}]*\}", raw, re.S)
    found = []
    for o in objs:
        try:
            d = json.loads(o)
        except Exception:
            continue
        if isinstance(d, dict) and "target" in d:
            found.append(d["target"])
    if not found:
        return None, "no {\"target\": ...} object found"
    if len(found) > 1:
        return None, f"ambiguous: {len(found)} target objects"
    t = found[0]
    if not isinstance(t, str) or not t.strip():
        return None, "target is empty"
    t = t.strip()
    if len(t) > 120:
        return None, f"target implausibly long ({len(t)} chars)"
    if re.search(r"\d", t):
        return None, f"target contains digits (likely a coordinate leak): {t!r}"
    return t, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
    ap.add_argument("--out-dir", default=str(R4 / "outputs/arms"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = [json.loads(l) for l in (R4 / "evidence/frozen_frames.jsonl").read_text().splitlines()
              if l.strip()]
    frozen = json.loads((R4 / "evidence/frozen_set.json").read_text())
    gmap = {g["group_key"]: g for g in frozen["groups"]}
    print(f"frozen frames: {len(frames)}")

    bl = load_baseline()
    print("baseline entry sha256:", sha256_file(BASELINE))
    print("DEFAULT_MAX_PIXELS:", bl.DEFAULT_MAX_PIXELS,
          "DEFAULT_CROP_TOKENS:", bl.DEFAULT_CROP_TOKENS)

    run = {"arm": "A", "model": args.model, "env": sys.executable,
           "baseline_entry": str(BASELINE), "baseline_entry_sha256": sha256_file(BASELINE),
           "n_frames": len(frames),
           "started_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()}

    t0 = time.time()
    model = bl.Qwen3VL(args.model)
    run["model_load_seconds"] = round(time.time() - t0, 2)
    print(f"model loaded in {run['model_load_seconds']}s")

    from PIL import Image

    p1_rows, p3a_rows = [], []
    for i, fr in enumerate(frames):
        g = gmap[fr["group_key"]]
        W, H = g["source_probe"]["width"], g["source_probe"]["height"]
        tw, th = float(g["targetRatioWH"][0]), float(g["targetRatioWH"][1])
        cw, h_float = bl.compute_crop_size(W, H, tw, th)
        pil = Image.open(fr["image_path"]).convert("RGB")
        if pil.size != (W, H):
            print(f"  !! frame size {pil.size} != source {(W, H)} for {fr['image_path']}")

        # ---- P1: verbatim official call path ----
        rec = {"frame_id": f"{fr['group_key']}#m{fr['moment_index']}",
               "group_key": fr["group_key"], "youtube_id": fr["youtube_id"],
               "moment_index": fr["moment_index"], "image_path": fr["image_path"],
               "image_sha256": fr["image_sha256"], "W": W, "H": H,
               "targetRatioWH": [tw, th], "max_legal_crop_w": cw,
               "crop_h_float": h_float}
        model.reset_peak_memory()
        t = time.time()
        try:
            raw = model.predict_focus(pil, (tw, th), max_new_tokens=bl.DEFAULT_CROP_TOKENS)
            rec["raw_output"] = raw
            center = bl.parse_focus_norm(raw, W, H)
            if center is None:
                rec["parse_ok"] = False
                rec["output_valid"] = False
                box = bl.center_to_box(0.5, 0.5, W, H, cw, h_float)
                rec["fallback_used"] = True
            else:
                rec["parse_ok"] = True
                rec["center_norm"] = [round(center[0], 6), round(center[1], 6)]
                box = bl.center_to_box(center[0], center[1], W, H, cw, h_float)
                rec["output_valid"] = bl.validate_box(box, W, H, tw, th)
                rec["fallback_used"] = False
            rec["box_xyw"] = box
            rec["box_geometry_valid"] = bl.validate_box(box, W, H, tw, th)
        except Exception as exc:
            rec.update(raw_output="", parse_ok=False, output_valid=False, fallback_used=True,
                       error=f"{type(exc).__name__}: {exc}",
                       box_xyw=bl.center_to_box(0.5, 0.5, W, H, cw, h_float))
        rec["seconds"] = round(time.time() - t, 2)
        rec["peak_memory_mib"] = round(model.peak_memory_mib(), 1)
        p1_rows.append(rec)

        # ---- P3a: single-subject referring expression ----
        prompt = P3_PROMPT.format(tw=int(tw), th=int(th))
        msg = [{"role": "user", "content": [
            {"type": "image", "image": pil, "max_pixels": bl.DEFAULT_MAX_PIXELS},
            {"type": "text", "text": prompt}]}]
        t = time.time()
        try:
            raw3 = model._generate(msg, bl.DEFAULT_CROP_TOKENS)
            target, err = parse_target(raw3)
        except Exception as exc:
            raw3, target, err = "", None, f"{type(exc).__name__}: {exc}"
        p3a_rows.append({
            "frame_id": rec["frame_id"], "group_key": fr["group_key"],
            "youtube_id": fr["youtube_id"], "moment_index": fr["moment_index"],
            "image_path": fr["image_path"], "image_sha256": fr["image_sha256"],
            "prompt": prompt, "raw_output": raw3,
            "target": target, "parse_error": err,
            "output_valid": target is not None,
            "seconds": round(time.time() - t, 2),
        })
        if i % 10 == 0:
            print(f"  [{i+1}/{len(frames)}] {rec['frame_id']} p1_valid={rec['output_valid']} "
                  f"target={target!r} err={err}")

    with (out_dir / "p1_qwen.jsonl").open("w") as f:
        for r in p1_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "p3a_target.jsonl").open("w") as f:
        for r in p3a_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    run.update(finished_utc=subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
               n_p1=len(p1_rows), n_p3a=len(p3a_rows),
               p1_valid=sum(1 for r in p1_rows if r["output_valid"]),
               p3a_valid=sum(1 for r in p3a_rows if r["output_valid"]),
               peak_memory_mib=max(r["peak_memory_mib"] for r in p1_rows),
               total_seconds=round(sum(r["seconds"] for r in p1_rows)
                                   + sum(r["seconds"] for r in p3a_rows), 1))
    (out_dir / "arm_a_run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(run, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
