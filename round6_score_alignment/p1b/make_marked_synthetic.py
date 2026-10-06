#!/usr/bin/env python3
"""P1b-fix: synthetic test media with a MACHINE-READABLE frame index.

Each frame carries:
  * large human-readable digits of the frame index (PIL default font, scaled);
  * an 8-bit binary marker in a fixed block (bit i = white when set), so a verifier
    can decode the frame index straight out of the pixels;
  * a moving bar so frames are visually distinct.

This media is ONLY for tool verification.  It is not a diagnostic sample and it
carries no semantic annotation.

Usage: python p1b/make_marked_synthetic.py [--frames 120] [--fps 10] [--size 320x240]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont

P1B = Path(__file__).resolve().parent
OUT_DIR = P1B / "synthetic"
MARKER_ORIGIN = (8, 8)          # (x, y) of the marker block
MARKER_BLOCK = 10               # size of one bit block
MARKER_BITS = 8


def frame_index_from_marker(img: Image.Image) -> int:
    """Decode the binary marker back to a frame index (used by the verifier)."""
    x0, y0 = MARKER_ORIGIN
    value = 0
    gray = img.convert("L")
    for bit in range(MARKER_BITS):
        x = x0 + bit * MARKER_BLOCK + MARKER_BLOCK // 2
        y = y0 + MARKER_BLOCK // 2
        if gray.getpixel((x, y)) > 127:
            value |= (1 << bit)
    return value


def draw_frame(index: int, size: tuple[int, int], total: int) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, (18, 22, 30))
    d = ImageDraw.Draw(img)
    # binary marker (little-endian)
    x0, y0 = MARKER_ORIGIN
    for bit in range(MARKER_BITS):
        on = (index >> bit) & 1
        d.rectangle([x0 + bit * MARKER_BLOCK, y0, x0 + bit * MARKER_BLOCK + MARKER_BLOCK - 2,
                     y0 + MARKER_BLOCK - 2],
                    fill=(255, 255, 255) if on else (0, 0, 0),
                    outline=(120, 120, 120))
    # human readable index
    try:
        font = ImageFont.load_default(size=64)
    except TypeError:                      # older Pillow has no size argument
        font = ImageFont.load_default()
    text = f"F{index}"
    bbox = d.textbbox((0, 0), text, font=font)
    d.text(((w - (bbox[2] - bbox[0])) / 2, (h - (bbox[3] - bbox[1])) / 2 - 10),
           text, fill=(240, 240, 240), font=font)
    # moving bar for visual distinctness
    bar_w = int((w - 40) * (index / max(1, total - 1)))
    d.rectangle([20, h - 26, 20 + bar_w, h - 14], fill=(70, 200, 120))
    d.rectangle([20, h - 26, w - 20, h - 14], outline=(90, 90, 90))
    return img


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--size", default="320x240")
    args = parser.parse_args()
    w, h = (int(x) for x in args.size.lower().split("x"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "synthetic_marked.mp4"
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=args.fps)
        stream.width, stream.height = w, h
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "18"}
        for i in range(args.frames):
            img = draw_frame(i, (w, h), args.frames)
            frame = av.VideoFrame.from_ndarray(np.asarray(img, dtype=np.uint8), format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)

    # verify the marker round-trips before declaring the media usable
    checks = []
    with av.open(str(path)) as container:
        for i, frame in enumerate(container.decode(video=0)):
            if i in (0, 1, 7, args.frames // 2, args.frames - 1):
                decoded = frame.to_image()
                checks.append({"frame": i, "marker": frame_index_from_marker(decoded),
                               "match": frame_index_from_marker(decoded) == i})
    meta = {"schema": "p1b_synthetic_marked_v1", "file_name": path.name,
            "width": w, "height": h, "fps": args.fps, "n_frames": args.frames,
            "marker_origin_xy": MARKER_ORIGIN, "marker_block_px": MARKER_BLOCK,
            "marker_bits": MARKER_BITS, "marker_encoding": "little-endian binary, white=1",
            "purpose": "tool verification only; never a diagnostic sample",
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "marker_roundtrip_checks": checks,
            "all_markers_match": all(c["match"] for c in checks)}
    (OUT_DIR / "synthetic_marked_manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    return 0 if meta["all_markers_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
