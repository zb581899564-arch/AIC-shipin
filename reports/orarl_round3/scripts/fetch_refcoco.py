#!/usr/bin/env python3
"""Fetch the RefCOCO val refs (small jsonl) and test whether the official COCO
image host serves the referenced images."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

R3 = Path("/home/inspur/aic_video_work/orarl_round3")
DATA = R3 / "data"
DATA.mkdir(parents=True, exist_ok=True)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

REPO = "rhymes-ai/RefCOCO"
FILE = "val.jsonl"
URL = f"https://hf-mirror.com/datasets/{REPO}/resolve/main/{FILE}"
OUT = DATA / "refcoco_val.jsonl"

if not OUT.exists():
    print("downloading", URL)
    o = subprocess.run(["curl", "-sSL", "--max-time", "300", "-o", str(OUT), URL],
                       capture_output=True, text=True)
    print("rc:", o.returncode, o.stderr[:200])
print("size:", OUT.stat().st_size)

lines = OUT.read_text(errors="replace").splitlines()
print("rows:", len(lines))
print("\n=== first 3 rows (truncated) ===")
for l in lines[:3]:
    d = json.loads(l)
    print(" keys:", sorted(d.keys()))
    for k, v in d.items():
        s = json.dumps(v, ensure_ascii=False)
        print(f"   {k}: {s[:200]}")
    print(" ---")

# find image reference fields
d0 = json.loads(lines[0])
print("\n=== look for image fields ===")
for k, v in d0.items():
    if isinstance(v, str) and (".jpg" in v.lower() or "coco" in v.lower() or "/" in v):
        print("  candidate:", k, "=", v[:150])
    if isinstance(v, dict):
        print("  dict field:", k, "keys:", sorted(v.keys())[:12])

# test COCO image fetch
print("\n=== test official COCO image host ===")
for u in ("http://images.cocodataset.org/val2017/000000039769.jpg",
          "http://images.cocodataset.org/val2017/000000000139.jpg"):
    o = subprocess.run(["curl", "-sS", "-m", "30", "-o", "/dev/null", "-w",
                        "%{http_code} %{size_download}", u], capture_output=True, text=True)
    print(f"  {u} -> {o.stdout}  rc={o.returncode}")
