#!/usr/bin/env python3
"""Extend the candidate pool (indices 8..15) and build their 4-frame strip sheet.
Same rule as select_samples.py; only the index window changes."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
DEV = Path("/home/inspur/aic_video_work/improvement_round1/frozen_data/dev.jsonl")
FFMPEG = "/usr/local/bin/ffmpeg"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
LO, HI = 8, 16


def main():
    rows = [json.loads(l) for l in DEV.read_text().splitlines() if l.strip()]
    seen, cands = set(), []
    for r in rows:
        if r["source_group"] in seen:
            continue
        seen.add(r["source_group"])
        cands.append(r)

    out_meta = []
    tiles = []
    for i in range(LO, min(HI, len(cands))):
        r = cands[i]
        src = Path(r["video_path"])
        if not src.exists():
            continue
        clip = R2 / f"clips/round2sel_{i:02d}_{r['source_group']}_off0_len32.mp4"
        if not clip.exists():
            subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", "0",
                            "-i", str(src), "-t", "32", "-c", "copy",
                            "-avoid_negative_ts", "make_zero", str(clip)], check=True)
        pr = json.loads(subprocess.check_output(
            [FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,nb_frames",
             "-show_entries", "format=duration", "-of", "json", str(clip)], text=True))
        dur = float(pr["format"]["duration"])
        ims = []
        for t in (0, 8, 16, 24):
            f = R2 / f"frames/sel/c{i:02d}_t{t}.jpg"
            subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", str(t),
                            "-i", str(clip), "-frames:v", "1", str(f)], check=True,
                           stdin=subprocess.DEVNULL)
            ims.append(Image.open(f).convert("RGB"))
        out_meta.append({"idx": i, "sample_id": f"sel{i:02d}",
                         "source_group": r["source_group"], "clip": str(clip),
                         "duration_sec": dur, "query": r["query"]})
        FW = 340
        TH = int(FW * ims[0].height / ims[0].width)
        row = Image.new("RGB", (FW * 4, TH + 30), (12, 12, 12))
        d0 = ImageDraw.Draw(row)
        d0.rectangle([0, 0, FW * 4, 14], fill=(0, 0, 0))
        d0.text((4, 2), f"[{i}] {r['source_group']}  dur={dur:.2f}", fill=(0, 255, 255))
        d0.rectangle([0, 15, FW * 4, 29], fill=(0, 0, 0))
        d0.text((4, 17), f"query: {r['query'][:96]}", fill=(255, 255, 0))
        for j, im in enumerate(ims):
            im2 = im.resize((FW, TH))
            dd = ImageDraw.Draw(im2)
            w, h = im2.size
            for k in range(0, 1001, 100):
                x, y = k / 1000 * w, k / 1000 * h
                col = (255, 0, 0) if k % 500 == 0 else (255, 180, 0)
                dd.line([(x, 0), (x, h)], fill=col, width=1)
                dd.line([(0, y), (w, y)], fill=col, width=1)
            dd.rectangle([0, h - 13, 46, h], fill=(0, 0, 0))
            dd.text((3, h - 12), f"t={[0,8,16,24][j]}s", fill=(255, 255, 255))
            row.paste(im2, (j * FW, 30))
        tiles.append(row)
        print(f"  [{i}] {r['source_group']:12s} dur={dur:.3f} query={r['query'][:60]}")

    if tiles:
        sheet = Image.new("RGB", (tiles[0].width, tiles[0].height * len(tiles)), (0, 0, 0))
        for i, t in enumerate(tiles):
            sheet.paste(t, (0, i * t.height))
        out = R2 / "frames/sel/selection_sheet_b.png"
        sheet.save(out)
        print("wrote", out, sheet.size)
    (R2 / "evidence/selection_candidates_b.json").write_text(
        json.dumps(out_meta, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
