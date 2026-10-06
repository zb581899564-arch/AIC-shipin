#!/usr/bin/env python3
"""ROUND 3 — synthetic geometry diagnostic (fully known ground truth).

Generates 4 short videos whose single target moves on an analytic, pre-written
trajectory. Every frame's ground-truth box is computed by this code, so IoU is
exact. The target is ALWAYS fully visible: no cuts, no occlusion, no absence.

Frozen BEFORE any model output: canvas, seed, trajectories, frame count, fps.
Nothing here is selected after seeing model results.

Scope warning recorded in the manifest: synthetic clips test controlled
geometric response only. They say nothing about real-video tracking quality and
nothing about AIC score.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

R3 = Path("/home/inspur/aic_video_work/orarl_round3")
BUILD = R3 / "frames/synth_build"
FFMPEG = "/usr/local/bin/ffmpeg"

W, H = 320, 240
FPS = 10
SECONDS = 32
NFRAMES = FPS * SECONDS          # 320
SEED = 20260916                  # recorded; trajectories are analytic anyway


def box_from_center(cx, cy, s):
    return [cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2]


# --- trajectories: analytic, fixed in advance -----------------------------
TRAJECTORIES = {
    "syn1_translate_x": dict(
        desc="target translates left->right at constant size",
        size=lambda u: 60.0,
        cx=lambda u: 40.0 + 240.0 * u,
        cy=lambda u: 120.0),
    "syn2_translate_xy": dict(
        desc="target translates diagonally (left-top -> right-bottom)",
        size=lambda u: 50.0,
        cx=lambda u: 40.0 + 240.0 * u,
        cy=lambda u: 40.0 + 160.0 * u),
    "syn3_scale_up": dict(
        desc="target centred, grows in place",
        size=lambda u: 30.0 + 110.0 * u,
        cx=lambda u: 160.0,
        cy=lambda u: 120.0),
    "syn4_translate_scale": dict(
        desc="target translates left->right while shrinking",
        size=lambda u: 80.0 - 50.0 * u,
        cx=lambda u: 40.0 + 240.0 * u,
        cy=lambda u: 120.0),
}


def draw_frame(traj, n):
    u = n / (NFRAMES - 1)
    img = Image.new("RGB", (W, H), (24, 26, 30))
    d = ImageDraw.Draw(img)
    # static grid so a constant/loose box is visually obvious
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=(44, 48, 56), width=1)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=(44, 48, 56), width=1)
    # fixed corner marker (never the target)
    d.rectangle([4, 4, 20, 20], fill=(70, 70, 80))
    d.text((6, 6), "F", fill=(200, 200, 210))

    s = traj["size"](u)
    cx, cy = traj["cx"](u), traj["cy"](u)
    b = box_from_center(cx, cy, s)
    d.rectangle(b, fill=(230, 70, 60), outline=(255, 255, 255), width=2)

    d.rectangle([0, H - 24, W, H], fill=(0, 0, 0))
    d.text((3, H - 22), f"n={n:03d} t={n/FPS:.1f}s", fill=(255, 255, 0))
    d.text((3, H - 11), f"gt=[{b[0]:.0f},{b[1]:.0f},{b[2]:.0f},{b[3]:.0f}]",
           fill=(120, 255, 160))
    return img, b


def main():
    (R3 / "clips").mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = {
        "canvas_wh": [W, H], "fps": FPS, "seconds": SECONDS, "n_frames": NFRAMES,
        "seed": SEED,
        "target_always_visible": True,
        "no_cuts_no_occlusion_no_absence": True,
        "gt_source": "computed analytically by this generator; not annotated, not model-derived",
        "scope_warning": ("synthetic geometry only: this tests controlled response to translation "
                          "and scale change. It cannot support any claim about real-video "
                          "tracking quality or about AIC score."),
        "clips": {},
    }
    for name, traj in TRAJECTORIES.items():
        for f in BUILD.glob("f_*.png"):
            f.unlink()
        gt_px, gt_norm = [], []
        for n in range(NFRAMES):
            img, b = draw_frame(traj, n)
            img.save(BUILD / f"f_{n:04d}.png")
            gt_px.append([round(v, 3) for v in b])
            gt_norm.append([round(b[0] / W * 1000, 2), round(b[1] / H * 1000, 2),
                            round(b[2] / W * 1000, 2), round(b[3] / H * 1000, 2)])
        clip = R3 / f"clips/{name}.mkv"
        subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-framerate", str(FPS),
                        "-i", str(BUILD / "f_%04d.png"), "-c:v", "ffv1",
                        "-pix_fmt", "rgb24", str(clip)], check=True)
        (R3 / f"data/gt_{name}.json").write_text(json.dumps({
            "clip": str(clip), "fps": FPS, "n_frames": NFRAMES,
            "canvas_wh": [W, H], "trajectory": traj["desc"],
            "gt_box_px_per_frame": gt_px,
            "gt_box_norm1000_per_frame": gt_norm,
            "gt_first_frame_norm1000": gt_norm[0],
            "gt_index_to_seconds": [round(n / FPS, 4) for n in range(NFRAMES)],
        }, indent=2) + "\n")
        import hashlib
        h = hashlib.sha256(clip.read_bytes()).hexdigest()
        manifest["clips"][name] = {
            "path": str(clip), "sha256": h, "trajectory": traj["desc"],
            "gt_file": str(R3 / f"data/gt_{name}.json"),
            "first_frame_box_norm1000": gt_norm[0],
            "last_frame_box_norm1000": gt_norm[-1],
            "box_size_start_px": round(gt_px[0][2] - gt_px[0][0], 1),
            "box_size_end_px": round(gt_px[-1][2] - gt_px[-1][0], 1),
        }
        print(f"  {name:22s} {clip.stat().st_size/1e6:6.2f} MB  {traj['desc']}")
        print(f"      first={gt_norm[0]} last={gt_norm[-1]}")

    (R3 / "evidence/synthetic_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print("\nwrote", R3 / "evidence/synthetic_manifest.json")
    shutil.rmtree(BUILD, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
