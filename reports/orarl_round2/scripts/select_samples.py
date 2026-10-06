#!/usr/bin/env python3
"""Select and freeze the round-2 sample list.

SELECTION RULE — written and applied BEFORE any model output is inspected:

 R1. Source pool = /home/inspur/aic_video_data/videos/**  (the project's own
     read-only source pool). The AIC test set
     (/home/inspur/aic_video_data/test) is EXCLUDED and never touched.
 R2. Candidates come from improvement_round1/frozen_data/dev.jsonl, taking the
     first row of each distinct `source_group`, in file order.
 R3. Every clip is a 32.000 s window at offset 0.0 built with
     `ffmpeg -ss 0 -t 32 -c copy` (stream copy, no re-encode), so that
     duration == 32 s and the author's canonical fps=1/max_frames=32 sampling
     lands one frame per one-second bin (verified in known_time_mapping.json).
     The round-1 clip (32.200 s) is kept separately as the non-ideal case.
 R4. Stratum assignment uses ONLY pre-model information: the row's `query`
     text, plus a 4-frame visual strip (t = 0, 8, 16, 24). A candidate is
     skipped and its reason recorded if the stratum is ambiguous.
 R5. Strata (2 clips each):
       S1 target continuously visible, marked position change
       S2 scale change or occlusion
       S3 scene cut, or target leaves the frame
 R6. Target = the most prominent subject named in the query text. Its
     first-frame box is read off a norm1000 grid overlay by the executing
     agent -> init_box_source = "agent-reviewed" (NOT human ground truth).
 R7. No trusted annotation is obtained, so quality metrics stay
     NOT_COMPUTABLE for every clip.

This script only BUILDS the contact sheet used for R4. Nothing is run on GPU.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROUND2 = Path("/home/inspur/aic_video_work/orarl_round2")
DEV = Path("/home/inspur/aic_video_work/improvement_round1/frozen_data/dev.jsonl")
SRC_ROOT = Path("/home/inspur/aic_video_data/videos")
FFMPEG = "/usr/local/bin/ffmpeg"
TAG = "round2sel"

GRID_EVERY = 100


def grab(video, t, out):
    subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", f"{t:.4f}",
                    "-i", str(video), "-frames:v", "1", str(out)], check=True,
                   stdin=subprocess.DEVNULL)
    return out


def text_safe(d, xy, s, fill=(255, 255, 255), bg=(0, 0, 0)):
    w = 7 * len(s) + 4
    d.rectangle([xy[0], xy[1], xy[0] + w, xy[1] + 12], fill=bg)
    d.text(xy, s, fill=fill)


def main():
    rows = [json.loads(l) for l in DEV.read_text().splitlines() if l.strip()]
    seen, cands = set(), []
    for r in rows:
        sg = r["source_group"]
        if sg in seen:
            continue
        seen.add(sg)
        cands.append(r)
    print(f"distinct source_groups in dev.jsonl: {len(cands)}")

    (ROUND2 / "clips").mkdir(parents=True, exist_ok=True)
    (ROUND2 / "frames/sel").mkdir(parents=True, exist_ok=True)

    tiles_meta = []
    for i, r in enumerate(cands[:8]):
        src = Path(r["video_path"])
        if not src.exists():
            print(f"  [{i}] MISSING {src}")
            continue
        clip = ROUND2 / f"clips/{TAG}_{i:02d}_{r['source_group']}_off0_len32.mp4"
        if not clip.exists():
            subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", "0",
                            "-i", str(src), "-t", "32", "-c", "copy",
                            "-avoid_negative_ts", "make_zero", str(clip)], check=True)
        # probe duration
        o = subprocess.check_output(
            ["/home/inspur/anaconda3/envs/Andy/bin/ffprobe", "-v", "error",
             "-select_streams", "v:0", "-show_entries", "stream=width,height,nb_frames",
             "-show_entries", "format=duration", "-of", "json", str(clip)], text=True)
        pr = json.loads(o)
        dur = float(pr["format"]["duration"])
        st = pr["streams"][0]
        tiles = []
        for t in (0, 8, 16, 24):
            f = ROUND2 / f"frames/sel/c{i:02d}_t{t}.jpg"
            grab(clip, t, f)
            tiles.append(Image.open(f).convert("RGB"))
        tiles_meta.append({
            "idx": i, "sample_id": f"sel{i:02d}", "source_group": r["source_group"],
            "source_path": str(src), "clip": str(clip),
            "duration_sec": dur, "width": int(st["width"]), "height": int(st["height"]),
            "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "query": r["query"], "tiles": tiles,
        })
        print(f"  [{i}] {r['source_group']:14s} dur={dur:.3f} "
              f"{st['width']}x{st['height']}  query={r['query'][:62]}")

    # contact sheet: one row per candidate, 4 frames, with a norm1000 grid
    FW = 340
    TH = int(FW * 300 / 534)
    rows_img = []
    for c in tiles_meta:
        row = Image.new("RGB", (FW * 4, TH + 30), (12, 12, 12))
        d0 = ImageDraw.Draw(row)
        text_safe(d0, (4, 2), f"[{c['idx']}] {c['sample_id']} {c['source_group']} "
                             f"dur={c['duration_sec']:.2f}", (0, 255, 255))
        text_safe(d0, (4, 15), f"query: {c['query'][:88]}", (255, 255, 0))
        for j, im in enumerate(c["tiles"]):
            im2 = im.resize((FW, TH))
            dd = ImageDraw.Draw(im2)
            w, h = im2.size
            for k in range(0, 1001, GRID_EVERY):
                x, y = k / 1000 * w, k / 1000 * h
                col = (255, 0, 0) if k % 500 == 0 else (255, 180, 0)
                dd.line([(x, 0), (x, h)], fill=col, width=1)
                dd.line([(0, y), (w, y)], fill=col, width=1)
            text_safe(dd, (3, h - 13), f"t={[0,8,16,24][j]}s", (255, 255, 255))
            row.paste(im2, (j * FW, 30))
        rows_img.append(row)

    W = FW * 4
    sheet = Image.new("RGB", (W, (TH + 30) * len(rows_img)), (0, 0, 0))
    for i, r in enumerate(rows_img):
        sheet.paste(r, (0, i * (TH + 30)))
    out = ROUND2 / "frames/sel/selection_sheet.png"
    sheet.save(out)
    print("\nwrote", out, sheet.size)

    meta = [{k: v for k, v in c.items() if k != "tiles"} for c in tiles_meta]
    (ROUND2 / "evidence/selection_candidates.json").write_text(
        json.dumps({"rule": __doc__, "candidates": meta}, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
