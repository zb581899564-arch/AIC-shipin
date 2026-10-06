#!/usr/bin/env python3
"""ROUND 3 — freeze a small set of PUBLIC, trusted grounding samples.

Source of annotations: RefCOCO val split, as published in the HF dataset mirror
`rhymes-ai/RefCOCO` (file `val.jsonl`). RefCOCO is the same benchmark family the
author's spatial-grounding evaluator targets, so this is the author-traceable
public route the round-3 brief asks for.

Source of images: the official COCO image host images.cocodataset.org (the
RefCOCO images are COCO images referenced by filename).

SELECTION RULE — applied before any model output:
  R1. read val.jsonl in file order;
  R2. take the FIRST row of each distinct image (dedupe by image filename);
  R3. take the first 10 distinct images;
  R4. expression = the text after the fixed prompt prefix in `messages`;
  R5. ground truth = `bbox` (pixel xyxy) inside the `hw` frame, converted to
      norm1000 so it is comparable with the model's declared output space.
  R6. no row is dropped or swapped after seeing model output.
Everything is hashed. Nothing here is authored by the executing agent.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

R3 = Path("/home/inspur/aic_video_work/orarl_round3")
DATA = R3 / "data"
IMGDIR = DATA / "refcoco_images"
SRC = DATA / "refcoco_val.jsonl"
N_WANTED = 10
PREFIX_RE = re.compile(r"^Given the image,\s*provide the bounding box coordinate of the "
                       r"region this sentence describes:\s*", re.I)
COCO_BASE = "http://images.cocodataset.org"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def coco_url(fname):
    """COCO_train2014_<id>.jpg -> official train2014 URL."""
    m = re.search(r"(COCO_(train|val)2014_\d+)\.jpg", fname, re.I)
    if not m:
        return None
    split = m.group(2).lower() + "2014"
    return f"{COCO_BASE}/{split}/{m.group(1)}.jpg"


def main():
    IMGDIR.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in SRC.read_text(errors="replace").splitlines() if l.strip()]
    print(f"val rows: {len(rows)}")

    seen, picked = set(), []
    for r in rows:
        img = r["images"][0]
        if img in seen:
            continue
        seen.add(img)
        picked.append(r)
        if len(picked) >= N_WANTED:
            break
    print(f"picked {len(picked)} distinct images (rule R2/R3, file order)")

    out = {"annotation_source": {
        "what": "RefCOCO val split (referring-expression grounding)",
        "hf_mirror_repo": "rhymes-ai/RefCOCO",
        "file": "val.jsonl",
        "file_bytes": SRC.stat().st_size,
        "file_sha256": sha256(SRC),
        "url": "https://hf-mirror.com/datasets/rhymes-ai/RefCOCO/resolve/main/val.jsonl",
        "upstream": "RefCOCO (Kazemzadeh et al. / lichengunc/refer); images are COCO images",
    },
        "image_source": {
        "host": COCO_BASE,
        "split": "train2014 (from the COCO_train2014_* filenames)",
        "terms": ("COCO images are hosted by the COCO project; each image retains its own "
                  "Flickr licence. Annotations are RefCOCO's. Recorded for provenance; no "
                  "redistribution is performed by this round."),
    },
        "selection_rule": __doc__,
        "coordinate_system": {
        "annotation": "pixel xyxy inside the (h,w) frame declared by each row's `hw`",
        "model_space": "norm1000",
        "conversion": "x_norm1000 = x_px / width * 1000 ; y_norm1000 = y_px / height * 1000",
    },
        "samples": []}

    for i, r in enumerate(picked):
        fname = Path(r["images"][0]).name
        url = coco_url(fname)
        dst = IMGDIR / f"r3_{i:02d}_{fname}"
        if not dst.exists() and url:
            subprocess.run(["curl", "-sSL", "--max-time", "120", "-o", str(dst), url], check=True)
        h, w = r["hw"]
        bx = r["bbox"]
        expr = ""
        for m in r["messages"]:
            for c in m.get("content", []):
                if c.get("type") == "text" and c.get("text"):
                    expr = PREFIX_RE.sub("", c["text"]).strip()
        gt_norm = [round(bx[0] / w * 1000, 2), round(bx[1] / h * 1000, 2),
                   round(bx[2] / w * 1000, 2), round(bx[3] / h * 1000, 2)]
        from PIL import Image
        try:
            im = Image.open(dst)
            real_w, real_h = im.size
        except Exception as e:
            real_w = real_h = None
        rec = {
            "sample_id": f"ref{i:02d}", "image_file": str(dst), "image_name": fname,
            "url": url,
            "annotation_hw": [h, w], "actual_image_wh": ([real_w, real_h] if real_w else None),
            "hw_matches_image": (real_w == w and real_h == h) if real_w else None,
            "expression": expr,
            "gt_bbox_px_xyxy": bx,
            "gt_bbox_norm1000": gt_norm,
            "image_sha256": sha256(dst) if dst.exists() else None,
            "image_bytes": dst.stat().st_size if dst.exists() else 0,
            "is_test_set": False,
        }
        out["samples"].append(rec)
        flag = "OK " if rec["hw_matches_image"] else "HW-MISMATCH"
        print(f"  {rec['sample_id']:7s} {fname:36s} {real_w}x{real_h} {flag} "
              f"gt_norm={gt_norm} expr={expr[:44]!r}")

    n_ok = sum(1 for s in out["samples"] if s["hw_matches_image"])
    out["n_samples"] = len(out["samples"])
    out["n_hw_verified"] = n_ok
    out["identity_verification"] = (
        "Each downloaded image's decoded (w,h) was compared with the annotation row's "
        "declared (h,w). Mismatches would indicate the filename->image mapping is wrong, so "
        "they are reported rather than silently accepted.")
    (R3 / "evidence/refcoco_frozen.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"\nhw verified: {n_ok}/{len(out['samples'])}")
    print("wrote", R3 / "evidence/refcoco_frozen.json")
    return 0 if n_ok == len(out["samples"]) else 1


if __name__ == "__main__":
    sys.exit(main())
