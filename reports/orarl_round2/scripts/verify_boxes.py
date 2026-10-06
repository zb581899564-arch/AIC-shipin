#!/usr/bin/env python3
"""Render proposed agent-reviewed first-frame boxes onto each clip's t=0 frame
so the boxes can be visually accepted or corrected BEFORE any model run.

usage: verify_boxes.py boxes.json
boxes.json: {"clip1": {"clip": "...", "box": [x1,y1,x2,y2], "target": "..."}, ...}
writes anchor_boxes_check.png next to it.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
FFMPEG = "/usr/local/bin/ffmpeg"


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    tiles = []
    for cid, d in spec.items():
        f = R2 / f"frames/grid/check_{cid}_t0.jpg"
        subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", "0",
                        "-i", d["clip"], "-frames:v", "1", str(f)], check=True,
                       stdin=subprocess.DEVNULL)
        im = Image.open(f).convert("RGB")
        W = 620
        H = int(im.height * W / im.width)
        im = im.resize((W, H))
        dd = ImageDraw.Draw(im)
        for k in range(0, 1001, 100):
            x, y = k / 1000 * W, k / 1000 * H
            col = (255, 0, 0) if k % 500 == 0 else (200, 140, 0)
            dd.line([(x, 0), (x, H)], fill=col, width=1)
            dd.line([(0, y), (W, y)], fill=col, width=1)
            if k % 200 == 0:
                dd.text((x + 2, 2), str(k), fill=(0, 255, 255))
                dd.text((2, y + 2), str(k), fill=(0, 255, 255))
        b = d["box"]
        px = [b[0] / 1000 * W, b[1] / 1000 * H, b[2] / 1000 * W, b[3] / 1000 * H]
        dd.rectangle(px, outline=(0, 255, 0), width=3)
        dd.rectangle([0, H - 32, W, H], fill=(0, 0, 0))
        dd.text((4, H - 30), f"{cid}  box={b}", fill=(0, 255, 0))
        dd.text((4, H - 17), f"target: {d['target'][:74]}", fill=(255, 255, 0))
        tiles.append(im)
    cols = 2
    rows = (len(tiles) + cols - 1) // cols
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (tw * cols, th * rows), (0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    out = R2 / "frames/grid/anchor_boxes_check.png"
    sheet.save(out)
    print("wrote", out, sheet.size)
    for cid, d in spec.items():
        print(f"  {cid:8s} {d['box']}  {d['target'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
