#!/usr/bin/env python3
"""Pick a video codec this ffmpeg build can write AND decord can read
losslessly enough for a machine-readable frame label."""
import json, subprocess, sys
import numpy as np
from PIL import Image
from pathlib import Path

TMP = Path("/home/inspur/aic_video_work/orarl_round2/frames/codec_probe")
TMP.mkdir(parents=True, exist_ok=True)
FFMPEG = "/usr/local/bin/ffmpeg"

# 60 frames, 30 fps; frame n has an n-dependent binary block pattern
W, H = 160, 90
BLOCKS = [(8 + 24 * k, 8) for k in range(5)]   # 5 bit blocks, 20x20
BS = 20
for n in range(60):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
    val = n // 2  # 0..29
    for k, (x, y) in enumerate(BLOCKS):
        on = (val >> k) & 1
        d.rectangle([x, y, x + BS - 1, y + BS - 1],
                    fill=(255, 255, 255) if on else (0, 0, 0))
    img.save(TMP / f"p_{n:04d}.png")

def try_codec(name, args, ext):
    out = TMP / f"probe_{name}.{ext}"
    cmd = [FFMPEG, "-nostdin", "-y", "-v", "error", "-framerate", "30",
           "-i", str(TMP / "p_%04d.png")] + args + [str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  {name:12s} ENCODE FAIL: {r.stderr.strip()[:90]}")
        return None
    try:
        import decord
        vr = decord.VideoReader(str(out))
        n = len(vr)
        ok = 0
        for i in range(n):
            fr = vr[i].asnumpy()
            v = 0
            for k, (x, y) in enumerate(BLOCKS):
                blk = fr[y + 4:y + BS - 4, x + 4:x + BS - 4].mean()
                if blk > 128:
                    v |= (1 << k)
            if v == i // 2:
                ok += 1
        fps = vr.get_avg_fps()
        print(f"  {name:12s} OK  frames={n} fps={fps:.3f} labels_correct={ok}/{n} "
              f"size={out.stat().st_size/1e6:.2f}MB")
        return {"codec": name, "frames": n, "fps": float(fps),
                "labels_correct": ok, "size_bytes": out.stat().st_size, "path": str(out)}
    except Exception as e:
        print(f"  {name:12s} DECORD FAIL: {type(e).__name__}: {str(e)[:80]}")
        return None

print("probing codecs:")
res = []
res.append(try_codec("mpeg4", ["-c:v", "mpeg4", "-q:v", "1", "-pix_fmt", "yuv420p"], "mp4"))
res.append(try_codec("ffv1", ["-c:v", "ffv1", "-pix_fmt", "rgb24"], "mkv"))
res.append(try_codec("rawvideo", ["-c:v", "rawvideo", "-pix_fmt", "rgb24"], "avi"))
res = [r for r in res if r]
print()
print(json.dumps(res, indent=1))
best = max(res, key=lambda r: r["labels_correct"]) if res else None
print("BEST:", best["codec"] if best else None)
Path("/home/inspur/aic_video_work/orarl_round2/no_gpu_tests/codec_probe.json").write_text(
    json.dumps(res, indent=2) + "\n")
