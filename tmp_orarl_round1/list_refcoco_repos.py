#!/usr/bin/env python3
"""List file layouts of candidate public RefCOCO mirrors to find one we can
consume WITHOUT adding heavy dependencies (prefer json + individual images)."""
from __future__ import annotations

import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from huggingface_hub import HfApi  # noqa: E402

api = HfApi(endpoint="https://hf-mirror.com")

for repo in ("jxu124/refcoco", "lmms-lab-encoder/RefCOCO", "Kangheng/refcoco",
             "lucasjin/refcoco", "sionic-ai/refcoco_object_detection",
             "rhymes-ai/RefCOCO"):
    print(f"\n=== {repo} ===")
    try:
        info = api.dataset_info(repo, files_metadata=True)
        sibs = sorted(info.siblings, key=lambda s: (s.rfilename.count("/"), s.rfilename))
        print(f"  files: {len(sibs)}")
        for s in sibs[:25]:
            print(f"    {s.rfilename:70s} {s.size if s.size is not None else '?'}")
        if len(sibs) > 25:
            print(f"    ... and {len(sibs)-25} more")
            exts = {}
            for s in sibs:
                e = s.rfilename.rsplit(".", 1)[-1].lower()
                exts[e] = exts.get(e, 0) + 1
            print("    extension histogram:", exts)
    except Exception as e:
        print("  FAILED:", type(e).__name__, str(e)[:160])
