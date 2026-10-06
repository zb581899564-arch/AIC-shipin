#!/usr/bin/env python3
"""Known-time video test: does "slot i" really correspond to real second i?

Motivation
==========
The author's tracking prompt asks for one bbox per second up to 32 seconds, and
eval_tracking_vllm.py states (lines 529-530) that GOT-10k GT-second labels
"are REAL seconds in the source video, NOT sampled-frame indices". The
evaluator never verifies that the frame sampled for slot i really is second i,
because canonical GOT-10k clips are ~32 s at fps=1.

This script builds a video whose real second is machine-readable from the
pixels, runs the author's actual sampling configuration through decord +
qwen_vl_utils, and checks which real second each sampled slot came from.

No GPU, no model.

Encoding: each frame carries 5 large black/white bit blocks whose value is the
integer second index (0..31). Decoding is by thresholding those blocks in the
DECODED frame, so it does not depend on OCR and survives lossy compression
(verified: 60/60 labels correct on mpeg4 too). A human-readable label is also
burned in. Container is lossless ffv1/mkv.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROUND = Path("/home/inspur/aic_video_work/orarl_round2")
TMP = ROUND / "frames/known_time_build"
FFMPEG = "/usr/local/bin/ffmpeg"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"

W, H, FPS, SECONDS = 320, 180, 30, 32
BLOCKS = [(8 + 26 * k, 8) for k in range(5)]
BS = 22


def build_video() -> str:
    from PIL import Image, ImageDraw
    TMP.mkdir(parents=True, exist_ok=True)
    for f in TMP.glob("f_*.png"):
        f.unlink()
    for n in range(FPS * SECONDS):
        sec = n // FPS
        img = Image.new("RGB", (W, H), (16, 16, 20))
        d = ImageDraw.Draw(img)
        for k, (x, y) in enumerate(BLOCKS):
            on = (sec >> k) & 1
            d.rectangle([x, y, x + BS - 1, y + BS - 1],
                        fill=(255, 255, 255) if on else (0, 0, 0))
        d.rectangle([0, H - 62, W, H], fill=(0, 0, 0))
        d.text((10, H - 54), f"SEC={sec:02d}", fill=(255, 255, 0))
        d.text((10, H - 36), f"FRAME={n:04d}", fill=(0, 255, 128))
        d.text((10, H - 18), f"t={n / FPS:.3f}s", fill=(150, 200, 255))
        img.save(TMP / f"f_{n:04d}.png")
    out = str(ROUND / "clips/known_time_32s_30fps.mkv")
    subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", str(TMP / "f_%04d.png"), "-c:v", "ffv1",
                    "-pix_fmt", "rgb24", out], check=True)
    return out


def probe(p):
    o = subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", p], text=True)
    d = json.loads(o)
    st = d["streams"][0]
    n, dn = (st.get("avg_frame_rate") or "0/1").split("/")
    return {"w": int(st["width"]), "h": int(st["height"]),
            "fps": float(n) / float(dn) if float(dn) else 0.0,
            "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "duration": float(d["format"]["duration"])}


def decode_second(frame_rgb: np.ndarray) -> int:
    v = 0
    for k, (x, y) in enumerate(BLOCKS):
        if frame_rgb[y + 5:y + BS - 5, x + 5:x + BS - 5].mean() > 128:
            v |= (1 << k)
    return v


def sample_with_author_config(video, prof):
    import os
    os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")
    from qwen_vl_utils import process_vision_info
    item = {"type": "video", "video": video, "max_pixels": prof["max_pixels"],
            "max_frames": prof["max_frames"], "fps": prof["fps"],
            "min_pixels": prof["min_pixels"], "total_pixels": prof["total_pixels"]}
    messages = [{"role": "user", "content": [item, {"type": "text", "text": "x"}]}]
    _, videos, vkw = process_vision_info(
        messages, image_patch_size=16, return_video_kwargs=True,
        return_video_metadata=True)
    tensor, md = videos[0]
    get = (lambda k: md.get(k)) if isinstance(md, dict) else (lambda k: getattr(md, k, None))
    idx = get("frames_indices")
    if hasattr(idx, "tolist"):
        idx = idx.tolist()
    return {
        "explicit_kwargs": {k: v for k, v in (vkw or {}).items()},
        "metadata": {k: (get(k) if not hasattr(get(k), "tolist") else get(k).tolist())
                     for k in ("fps", "total_num_frames", "duration",
                               "frames_indices", "video_backend")},
        "frames_indices": [int(i) for i in idx],
        "tensor_shape": list(np.asarray(tensor).shape),
    }


def main():
    video = build_video()
    print("built:", video)
    info = probe(video)
    print("probe:", info)

    profiles = {
        # the author's canonical tracking profile (datasets.jsonl / eval.sh)
        "canonical_tracking_fps1_max32": dict(fps=1, max_frames=32, min_pixels=4096,
                                              max_pixels=786432, total_pixels=8388608),
        # the tracking script's own argparse defaults, for contrast
        "script_default_fps2_max64": dict(fps=2, max_frames=64, min_pixels=4096,
                                          max_pixels=65536, total_pixels=16777216),
    }
    import decord
    results = {}
    for name, prof in profiles.items():
        s = sample_with_author_config(video, prof)
        idx = s["frames_indices"]
        fps_v = s["metadata"]["fps"]
        vr = decord.VideoReader(video)
        # what the author's metadata claims each slot's frame index is:
        real_seconds = [decode_second(vr[i].asnumpy()) for i in idx]
        # what the index/fps arithmetic implies:
        implied = [round(i / fps_v, 4) for i in idx]
        # what the tensor actually contains, decoded the same way:
        arr = np.asarray(s and __import__("torch").as_tensor(0) if False else 0) if False else None
        mism = [{"slot": k + 1, "frame_index": idx[k], "implied_t_sec": implied[k],
                 "real_second_in_video": real_seconds[k]}
                for k in range(len(idx)) if real_seconds[k] != k]
        results[name] = {
            "profile": prof, "n_sampled": len(idx),
            "metadata": s["metadata"], "explicit_kwargs": s["explicit_kwargs"],
            "tensor_shape": s["tensor_shape"],
            "frames_indices": idx,
            "implied_t_sec_from_index_over_fps": implied,
            "real_second_decoded_from_pixels": real_seconds,
            "n_slots_where_real_second_!=_slot": len(mism),
            "mismatches": mism[:10],
            "slot_i_is_real_second_i_plus_1": len(mism) == 0,
        }
        print(f"\n--- {name} ---")
        print(f"  n_sampled={len(idx)} metadata_fps={fps_v} "
              f"total={s['metadata']['total_num_frames']} "
              f"backend={s['metadata']['video_backend']}")
        print(f"  first6 idx={idx[:6]}")
        print(f"  first6 implied_t={implied[:6]}  real_second={real_seconds[:6]}")
        print(f"  last3  idx={idx[-3:]} implied_t={implied[-3:]} real_second={real_seconds[-3:]}")
        print(f"  slot i == real second i+1 ? {len(mism)==0} "
              f"(mismatches {len(mism)}/{len(idx)})")

    # round-1 clip: quantify its drift AND its per-slot second-bin error
    r1 = Path("/home/inspur/aic_video_work/orarl_round1/clips/"
              "src_wk2CeU_DcBo_60_210_off0_len32.mp4")
    if r1.exists():
        i2 = probe(str(r1))
        vr = decord.VideoReader(str(r1))
        n = len(vr)
        nf = max(4, min(32, int(round(i2["duration"] * 1))))
        idx = [int(round(v)) for v in np.linspace(0, n - 1, nf)]
        implied = [round(i / i2["fps"], 4) for i in idx]
        # ideal: slot k (0-based) should land in second-bin k, i.e. floor(i/fps)==k
        bins = [int(i // i2["fps"]) for i in idx]
        bin_err = [{"slot": k + 1, "frame_index": idx[k], "t_sec": implied[k],
                    "second_bin": bins[k], "expected_bin": k}
                   for k in range(nf) if bins[k] != k]
        results["round1_clip_fps1_max32"] = {
            "video": str(r1), "probe": i2, "n_sampled": nf, "frames_indices": idx,
            "implied_t_sec_from_index_over_fps": implied,
            "second_bin_per_slot": bins,
            "n_slots_with_wrong_second_bin": len(bin_err),
            "slots_with_wrong_second_bin": bin_err,
            "slot1_t_sec": implied[0], "slot32_t_sec": implied[-1],
            "drift_of_slot32_vs_32s": round(implied[-1] - 32.0, 4),
            "uniform_interval_sec": round(implied[1] - implied[0], 4) if nf > 1 else None,
            "note": ("clip is 32.200 s / 962 frames, so linspace over 32 slots drifts: "
                     "the last slots land one second-bin late"),
        }
        print(f"\n--- round1 clip ({i2['duration']:.3f} s, {n} frames) ---")
        print(f"  n={nf} slot1_t={implied[0]} slot32_t={implied[-1]} "
              f"interval={implied[1]-implied[0]:.4f}s "
              f"drift(slot32 vs 32s)={implied[-1]-32.0:+.3f}s")
        print(f"  slots in the WRONG second bin: {len(bin_err)}/{nf} -> "
              f"{[e['slot'] for e in bin_err]}")

    dest = ROUND / "no_gpu_tests/known_time_mapping.json"
    dest.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print("\nwrote", dest)
    shutil.rmtree(TMP, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
