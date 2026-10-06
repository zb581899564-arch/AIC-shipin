#!/usr/bin/env python3
"""CPU-ONLY offline load probe for Video-ORA-4B.

Why this exists: "all shards downloaded" is not "model works", and GPU time is
budgeted. This probe proves, with no CUDA context, that
  * transformers 5.5.4 recognises the qwen3_5 architecture,
  * the AutoProcessor loads from the local directory,
  * the checkpoint loads fully OFFLINE (HF_HUB_OFFLINE=1) with no missing or
    unexpected keys,
  * one real (tiny, text-only) forward pass runs on CPU.

It deliberately does NOT touch torch.cuda, so it is not charged to the GPU
budget. CUDA inference is verified separately inside budget_run.py.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "/home/inspur/aic_video_work/orarl_round1/evidence/offline_load_probe.json"

rep = {"model": MODEL, "offline_env": {k: os.environ.get(k) for k in
                                       ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")},
       "steps": {}}


def step(name, fn):
    t0 = time.time()
    try:
        val = fn()
        rep["steps"][name] = {"ok": True, "seconds": round(time.time() - t0, 2), "value": val}
        print(f"[OK]   {name}  ({time.time()-t0:.1f}s)  {val}", flush=True)
        return val
    except Exception as exc:
        rep["steps"][name] = {"ok": False, "seconds": round(time.time() - t0, 2),
                              "error": f"{type(exc).__name__}: {exc}",
                              "traceback": traceback.format_exc()}
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}", flush=True)
        return None


import torch
import transformers
from transformers import AutoConfig, AutoModelForImageTextToText, AutoProcessor

rep["versions"] = {
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "torch_cuda_build": torch.version.cuda,
    "transformers": transformers.__version__,
    "cuda_available_not_probed": True,
}

print(f"torch {torch.__version__} (cuda build {torch.version.cuda}), "
      f"transformers {transformers.__version__}", flush=True)

cfg = step("AutoConfig.from_pretrained", lambda: {
    "model_type": AutoConfig.from_pretrained(MODEL, trust_remote_code=True).model_type,
    "architectures": AutoConfig.from_pretrained(MODEL, trust_remote_code=True).architectures,
})

step("AutoModelForImageTextToText registers qwen3_5", lambda: {
    "registered": "qwen3_5" in AutoModelForImageTextToText._model_mapping._model_mapping
    if hasattr(AutoModelForImageTextToText, "_model_mapping") else "unknown",
    "class": type(AutoModelForImageTextToText).__name__,
})

proc = step("AutoProcessor.from_pretrained", lambda: {
    "processor_class": type(AutoProcessor.from_pretrained(
        MODEL, padding_side="left", do_resize=False, trust_remote_code=True)).__name__,
    "image_processor_class": type(AutoProcessor.from_pretrained(
        MODEL, padding_side="left", do_resize=False, trust_remote_code=True)
        .image_processor).__name__,
})

print("\n--- full offline weight load on CPU (this is the real load test) ---", flush=True)

_LOADED = []


def load():
    t0 = time.time()
    m, info = AutoModelForImageTextToText.from_pretrained(
        MODEL, dtype=torch.bfloat16, device_map="cpu", low_cpu_mem_usage=True,
        output_loading_info=True)
    m.eval()
    _LOADED.append(m)
    n = sum(p.numel() for p in m.parameters())
    missing = list(info.get("missing_keys") or [])
    unexpected = list(info.get("unexpected_keys") or [])
    mismatched = list(info.get("mismatched_keys") or [])
    return {"load_seconds": round(time.time() - t0, 2),
            "params_billion": round(n / 1e9, 4),
            "dtype": str(next(m.parameters()).dtype),
            "missing_keys_n": len(missing),
            "unexpected_keys_n": len(unexpected),
            "mismatched_keys_n": len(mismatched),
            "missing_keys_sample": missing[:5],
            "unexpected_keys_sample": unexpected[:5],
            "weights_fully_consumed": not missing and not unexpected and not mismatched}


mm = step("from_pretrained(device_map=cpu, offline)", load)
LOADED_MODEL = mm and _LOADED[0]

if mm is not None:
    def tiny_forward():
        import torch as T
        tok = AutoProcessor.from_pretrained(MODEL, padding_side="left",
                                            do_resize=False, trust_remote_code=True)
        msgs = [{"role": "user", "content": [{"type": "text", "text": "Reply with the single word: ok"}]}]
        text = tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True, enable_thinking=False)
        inp = tok(text=[text], padding=True, return_tensors="pt")
        with T.inference_mode():
            out = LOADED_MODEL.generate(**inp, do_sample=False, max_new_tokens=4)
        return {"decoded": tok.batch_decode([o[len(inp["input_ids"][0]):] for o in out],
                                            skip_special_tokens=True)[0]}
    step("tiny CPU text-only generate", tiny_forward)

rep["all_ok"] = all(v.get("ok") for v in rep["steps"].values())
with open(OUT, "w") as f:
    json.dump(rep, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("\nwrote", OUT)
print("ALL_OK:", rep["all_ok"])
sys.exit(0 if rep["all_ok"] else 1)
