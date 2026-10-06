#!/usr/bin/env python3
"""Render a large t=0 norm1000 grid sheet for the selected clips so the
agent-reviewed first-frame boxes can be read off and frozen."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
FFMPEG = "/usr/local/bin/ffmpeg"
SEL = {"sel01": "RoripwjYFp8", "sel02": "ioWAoEVYaP0", "sel03": "ACMKgn5w2HY",
       "sel04": "lwNho_1tKrc", "sel06": "iH1-Z6eB2cY", "sel07": "JlWjckrziyw"}


def main():
    cands = json.loads((R2 / "evidence/selection_candidates.json").read_text())["candidates"]
    by_group = {c["source_group"]: c for c in cands}
    tiles, labels = [], []
    for sid, group in SEL.items():
        c = by_group[group]
        clip = c["clip"]
        f = R2 / f"frames/grid/{sid}_t0.jpg"
        subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", "0",
                        "-i", clip, "-frames:v", "1", str(f)], check=True,
                       stdin=subprocess.DEVNULL)
        im = Image.open(f).convert("RGB")
        W = 640
        H = int(im.height * W / im.width)
        im = im.resize((W, H))
        d = ImageDraw.Draw(im)
        for k in range(0, 1001, 100):
            x, y = k / 1000 * W, k / 1000 * H
            col = (255, 0, 0) if k % 500 == 0 else (255, 180, 0)
            d.line([(x, 0), (x, H)], fill=col, width=1)
            d.line([(0, y), (W, y)], fill=col, width=1)
            if k % 200 == 0:
                d.text((x + 2, 2), str(k), fill=(0, 255, 255))
                d.text((2, y + 2), str(k), fill=(0, 255, 255))
        d.rectangle([0, H - 30, W, H], fill=(0, 0, 0))
        d.text((4, H - 28), f"{sid}  {group}", fill=(255, 255, 0))
        d.text((4, H - 15), f"query: {c['query'][:78]}", fill=(255, 255, 255))
        tiles.append(im)
        labels.append(sid)

    cols = 2
    rows = (len(tiles) + cols - 1) // cols
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (tw * cols, th * rows), (0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    out = R2 / "frames/grid/anchor_sheet_t0.png"
    sheet.save(out)
    print("wrote", out, sheet.size, labels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
