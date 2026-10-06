#!/usr/bin/env python3
"""P1b: create a tiny SYNTHETIC video for tool testing (no real media involved).

60 frames, 10 fps, 160x120, a moving bright square plus a frame-index bar.
Written to round6_score_alignment/p1b/synthetic/synthetic_pilot.mp4
"""
from __future__ import annotations

import json
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "round6_score_alignment/p1b/synthetic"
WIDTH, HEIGHT, FPS, N = 160, 120, 10, 60


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "synthetic_pilot.mp4"
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=FPS)
        stream.width, stream.height = WIDTH, HEIGHT
        stream.pix_fmt = "yuv420p"
        for i in range(N):
            img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            img[:, :, 2] = 40                                  # dark blue background
            x = int(10 + (WIDTH - 40) * i / (N - 1))
            img[30:70, x:x + 30] = (255, 200, 0)                # moving square
            bar = int((WIDTH - 20) * i / (N - 1))
            img[5:12, 10:10 + bar] = (0, 255, 0)                # progress bar
            img[HEIGHT - 12:HEIGHT - 4, 10:20] = (255, 0, 0) if i % 2 else (0, 0, 0)
            frame = av.VideoFrame.from_ndarray(img, format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    meta = {"schema": "p1b_synthetic_media_v1", "file_name": path.name,
            "width": WIDTH, "height": HEIGHT, "fps": FPS, "n_frames": N,
            "purpose": "tool testing only; never a diagnostic sample",
            "bytes": path.stat().st_size}
    (OUT_DIR / "synthetic_manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
