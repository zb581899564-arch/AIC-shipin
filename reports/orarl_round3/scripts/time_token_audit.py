#!/usr/bin/env python3
"""ROUND 3 — corrected time audit.

Round 2 claimed "the model's final input contains NO explicit per-frame
timestamps". That was WRONG. This script proves what actually reaches the model.

For a FIXED video it:
  1. runs the real Qwen3VLProcessor and decodes the FINAL input_ids with special
     tokens retained, extracting the literal "<X.X seconds>" strings;
  2. saves the sampled frame indices, the video metadata handed to the processor,
     the processor's own _calculate_timestamps output, and the decoded text;
  3. reports REAL decoded PTS (from the container, via ffprobe) SEPARATELY from
     index/fps arithmetic, and never calls the latter "real PTS";
  4. for the bit-labelled known-time video, checks which REAL second each
     temporal patch actually contains, so "frame N sits in second bin B" and
     "output key N means real second N" stay distinct claims.

CPU only. No GPU.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
R3 = Path("/home/inspur/aic_video_work/orarl_round3")
MODEL = Path("/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B")
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")

# bit-block decoding of the known-time video (round-2 generator)
BLOCKS = [(8 + 26 * k, 8) for k in range(5)]
BS = 22

TARGETS = {
    "known_time_32s_30fps": {
        "path": str(R2 / "clips/known_time_32s_30fps.mkv"),
        "labelled": True,
        "note": "32.000 s / 30 fps / 960 frames, each frame bit-encodes its second",
    },
    "round1_clip_32p2s": {
        "path": str(Path("/home/inspur/aic_video_work/orarl_round1/clips/"
                         "src_wk2CeU_DcBo_60_210_off0_len32.mp4")),
        "labelled": False,
        "note": "32.200 s / 962 frames, the round-1 clip",
    },
}


def probe(path):
    d = json.loads(subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", path], text=True))
    st = d["streams"][0]
    n, dn = (st.get("avg_frame_rate") or "0/1").split("/")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "avg_fps": float(n) / float(dn) if float(dn) else None,
            "r_fps": st.get("r_frame_rate"),
            "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "duration_sec": float(d["format"]["duration"])}


def real_pts(path):
    """TRUE timestamps from the container (not index/fps).

    `frame=pts_time` comes back empty for ffv1/mkv with this ffprobe build, so
    fall back to `best_effort_timestamp_time`, which is the decoder's best
    reconstruction of presentation time.
    """
    for field in ("pts_time", "best_effort_timestamp_time"):
        o = subprocess.check_output(
            [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_frames",
             "-show_entries", f"frame={field}", "-of", "csv=p=0", path], text=True)
        out = []
        for line in o.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                out.append(float(line))
            except ValueError:
                pass
        if out:
            return out, field
    return [], None


def decode_second(frame_rgb):
    v = 0
    for k, (x, y) in enumerate(BLOCKS):
        if frame_rgb[y + 5:y + BS - 5, x + 5:x + BS - 5].mean() > 128:
            v |= (1 << k)
    return v


def main():
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from qwen_vl_utils import process_vision_info
    import decord

    processor = AutoProcessor.from_pretrained(
        MODEL, padding_side="left", do_resize=False, trust_remote_code=True)
    tok = processor.tokenizer
    special = {v: k for k, v in tok.get_vocab().items()}

    profile = dict(fps=1, max_frames=32, min_pixels=4096,
                   max_pixels=786432, total_pixels=8388608)
    out = {"model": str(MODEL),
           "processor_file": str(Path(
               "/home/inspur/aic_video_work/orarl_round1/env/orarl_hf/lib/python3.11/"
               "site-packages/transformers/models/qwen3_vl/processing_qwen3_vl.py")),
           "sampling_profile": profile,
           "round2_wrong_claim": ("'the model's final input contains NO explicit per-frame "
                                  "timestamps' -- round 2 inspected the PRE-processor text and "
                                  "hard-coded any_numeric_timestamp_list=False, and only listed "
                                  "processor output TENSOR keys, never decoding input_ids"),
           "videos": {}}

    for name, spec in TARGETS.items():
        path = spec["path"]
        if not Path(path).exists():
            out["videos"][name] = {"error": "missing file", "path": path}
            print(f"!! missing {path}")
            continue
        pr = probe(path)
        pts, pts_field = real_pts(path)
        vr = decord.VideoReader(path)

        item = {"type": "video", "video": path, **profile}
        messages = [{"role": "user", "content": [
            item, {"type": "text", "text": "Track the object."}]}]
        text_pre = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        _, videos, vkw = process_vision_info(
            messages, image_patch_size=16, return_video_kwargs=True,
            return_video_metadata=True)
        videos, vmd = zip(*videos)
        videos, vmd = list(videos), list(vmd)
        g = (lambda k: vmd[0].get(k)) if isinstance(vmd[0], dict) \
            else (lambda k: getattr(vmd[0], k, None))
        fi = g("frames_indices")
        fi = fi.tolist() if hasattr(fi, "tolist") else list(fi)
        mfps = g("fps")
        total = g("total_num_frames")

        inputs = processor(text=[text_pre], images=None, videos=videos,
                           video_metadata=vmd, padding=True, return_tensors="pt", **vkw)
        ids = inputs["input_ids"][0].tolist()
        decoded = tok.decode(ids, skip_special_tokens=False)

        # the processor's own timestamp arithmetic
        calc = processor._calculate_timestamps(
            list(fi), float(mfps), processor.video_processor.temporal_patch_size)

        # every "<X.X seconds>" literal that really ended up in input_ids
        found = [(m.start(), m.group(1)) for m in re.finditer(r"<([0-9]+\.[0-9]) seconds>",
                                                             decoded)]
        vpad = tok.convert_tokens_to_ids("<|video_pad|>")

        # how many video_pad ids sit between consecutive time strings
        positions = [i for i, t in enumerate(ids) if special.get(t) == "<|video_pad|>"]
        time_positions = []
        for m in re.finditer(r"<([0-9]+\.[0-9]) seconds>", decoded):
            # locate the token index of this literal by tokenising the prefix
            pass

        # real second actually inside each temporal patch (labelled video only)
        patch_seconds = None
        if spec["labelled"]:
            tps = processor.video_processor.temporal_patch_size
            patch_seconds = []
            for p in range(0, len(fi), tps):
                chunk = fi[p:p + tps]
                secs = [decode_second(vr[i].asnumpy()) for i in chunk]
                patch_seconds.append({"patch": p // tps,
                                      "frame_indices": chunk,
                                      "real_seconds_in_patch": secs})

        rec = {
            "path": path, "labelled": spec["labelled"], "note": spec["note"],
            "container": pr,
            "n_real_pts": len(pts),
            "real_pts_available": bool(pts),
            "real_pts_field_used": pts_field,
            "sampling": {
                "frames_indices": fi,
                "metadata_fps": mfps,
                "metadata_total_num_frames": total,
                "video_backend": g("video_backend"),
            },
            "processor_time_computation": {
                "formula": ("_calculate_timestamps: t=idx/fps then averaged over each "
                            "temporal patch: (t[i]+t[i+merge-1])/2"),
                "temporal_patch_size": processor.video_processor.temporal_patch_size,
                "timestamps": [round(float(x), 4) for x in calc],
                "n_timestamps": len(calc),
                "IS_real_pts": False,
                "is_nominal_index_over_fps": True,
            },
            "index_over_fps_nominal_sec": [round(i / float(mfps), 4) for i in fi],
            "real_container_pts_sec_for_sampled_frames": (
                [round(pts[i], 6) for i in fi] if pts and max(fi) < len(pts) else None),
            "final_input_ids": {
                "length": len(ids),
                "n_video_pad_tokens": len(positions),
                "video_pad_token_id": vpad,
                "time_literals_in_decoded_text": [t for _, t in found],
                "n_time_literals": len(found),
            },
            "decoded_text_head": decoded[:400],
            "patch_real_seconds": patch_seconds,
        }
        # separation of the two claims
        if pts and max(fi) < len(pts) and mfps:
            nominal = [i / float(mfps) for i in fi]
            realp = [pts[i] for i in fi]
            d = [round(r - n, 6) for n, r in zip(nominal, realp)]
            mx = max(abs(x) for x in d) if d else None
            rec["nominal_vs_real_pts"] = {
                "max_abs_diff_sec": mx,
                "mean_diff_sec": round(sum(d) / len(d), 6) if d else None,
                "identical_within_1ms": bool(mx is not None and mx < 1e-3),
                "note": (
                    "index/fps happens to coincide with container PTS within 1 ms for THIS file"
                    if (mx is not None and mx < 1e-3) else
                    f"index/fps does NOT equal container PTS for this file: differs by up to "
                    f"{mx:.6f} s (mean {sum(d)/len(d):+.6f} s). Round 2 labelled index/fps "
                    f"values as 'real decoded timestamps', which is incorrect in general and "
                    f"measurably wrong here."),
            }
        out["videos"][name] = rec

        print(f"\n=== {name} ===")
        print(f"  container: {pr['width']}x{pr['height']} avg_fps={pr['avg_fps']} "
              f"nb_frames={pr['nb_frames']} dur={pr['duration_sec']}")
        print(f"  sampled: n={len(fi)} first6={fi[:6]} metadata_fps={mfps} total={total}")
        print(f"  processor timestamps n={len(calc)} first6="
              f"{[round(float(x),3) for x in calc[:6]]}")
        print(f"  FINAL input_ids len={len(ids)}  video_pad tokens={len(positions)}")
        print(f"  >>> TIME LITERALS REALLY IN input_ids: n={len(found)}")
        print(f"      first6={[t for _, t in found[:6]]}")
        print(f"      last2={[t for _, t in found[-2:]]}")
        print(f"  decoded head: {decoded[:150]!r}")
        if rec.get("nominal_vs_real_pts"):
            print(f"  nominal vs container PTS: {rec['nominal_vs_real_pts']}")
        if patch_seconds:
            print(f"  patch real seconds (first4): {patch_seconds[:4]}")

    dest = R3 / "evidence/time_token_audit.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("\nwrote", dest)

    # verdict
    any_time = any(v.get("final_input_ids", {}).get("n_time_literals", 0) > 0
                   for v in out["videos"].values() if isinstance(v, dict))
    print("\nVERDICT: time literals present in final input_ids:", any_time)
    print("Round-2 claim 'no temporal information in the final input' is",
          "REFUTED" if any_time else "not refuted")
    return 0 if any_time else 1


if __name__ == "__main__":
    sys.exit(main())
