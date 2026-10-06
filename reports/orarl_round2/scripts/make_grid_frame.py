#!/usr/bin/env python3
"""Render frames with a norm1000 coordinate grid so box coordinates can be read
off visually and frozen BEFORE any model output is seen.

usage: make_grid_frame.py OUT.png VIDEO T1 [T2 ...]
       make_grid_frame.py OUT.png --image IN.png
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

FFMPEG = "/usr/local/bin/ffmpeg"


def grab(video, t, out):
    subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", f"{t:.4f}",
                    "-i", video, "-frames:v", "1", str(out)], check=True,
                   stdin=subprocess.DEVNULL)
    return out


def grid(img, label):
    d = ImageDraw.Draw(img)
    w, h = img.size
    for k in range(0, 1001, 100):
        x = k / 1000 * w
        y = k / 1000 * h
        col = (255, 0, 0) if k % 500 == 0 else (255, 200, 0)
        d.line([(x, 0), (x, h)], fill=col, width=1)
        d.line([(0, y), (w, y)], fill=col, width=1)
        if k % 200 == 0:
            d.text((x + 2, 2), str(k), fill=(0, 255, 255))
            d.text((2, y + 2), str(k), fill=(0, 255, 255))
    d.rectangle([0, h - 14, w, h], fill=(0, 0, 0))
    d.text((3, h - 13), label, fill=(255, 255, 255))
    return img


def main():
    out = Path(sys.argv[1])
    if sys.argv[2] == "--image":
        frames = [(sys.argv[3], f"image {sys.argv[3]}")]
    else:
        video = sys.argv[2]
        frames = []
        for t in sys.argv[3:]:
            tmp = out.with_name(f"_tmp_{out.stem}_{t}.jpg")
            grab(video, float(t), tmp)
            frames.append((str(tmp), f"t={t}s  {Path(video).name}"))
    tiles = []
    for path, label in frames:
        im = Image.open(path).convert("RGB")
        tiles.append(grid(im, label))
    if len(tiles) == 1:
        tiles[0].save(out)
    else:
        tw = tiles[0].width
        th = tiles[0].height
        sheet = Image.new("RGB", (tw, th * len(tiles)), (10, 10, 10))
        for i, t in enumerate(tiles):
            sheet.paste(t, (0, i * th))
        sheet.save(out)
    for path, _ in frames:
        if path.startswith(str(out.with_name("_tmp_"))):
            Path(path).unlink(missing_ok=True)
    print("wrote", out, tiles[0].size)


if __name__ == "__main__":
    main()
