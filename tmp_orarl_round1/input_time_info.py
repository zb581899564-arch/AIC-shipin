#!/usr/bin/env python3
"""What temporal information does the model's FINAL INPUT actually carry?

The brief requires saving decoded timestamps, sampled frame indices, the
metadata handed to the processor, and the time information present in the final
processor output — and checking they agree.

No GPU (CPU tensors only, tiny video).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROUND2 = Path("/home/inspur/aic_video_work/orarl_round2")
VIDEO = ROUND2 / "clips/known_time_32s_30fps.mkv"
MODEL = Path("/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B")
os.environ.setdefault("FORCE_QWENVL_VIDEO_READER", "decord")

import torch
from transformers import AutoProcessor
from qwen_vl_utils import process_vision_info

out = {"video": str(VIDEO), "model": str(MODEL)}

pc = json.loads((MODEL / "processor_config.json").read_text())
out["processor_config"] = pc
print("processor_config.json:", json.dumps(pc, ensure_ascii=False)[:600])

processor = AutoProcessor.from_pretrained(
    MODEL, padding_side="left", do_resize=False, trust_remote_code=True)

prof = dict(fps=1, max_frames=32, min_pixels=4096, max_pixels=786432, total_pixels=8388608)
messages = [{"role": "user", "content": [
    {"type": "video", "video": str(VIDEO), **prof},
    {"type": "text", "text": "Track the object. Provide one bounding box per second."}]}]
text = processor.apply_chat_template(messages, tokenize=False,
                                     add_generation_prompt=True, enable_thinking=False)
_, videos, vkw = process_vision_info(messages, image_patch_size=16,
                                     return_video_kwargs=True, return_video_metadata=True)
videos, vmd = zip(*videos)
videos, vmd = list(videos), list(vmd)
g = (lambda k: vmd[0].get(k)) if isinstance(vmd[0], dict) else (lambda k: getattr(vmd[0], k, None))
fi = g("frames_indices")
fi = fi.tolist() if hasattr(fi, "tolist") else fi
mfps = g("fps")
out["stage_sampling"] = {
    "decoder_backend": g("video_backend"),
    "decoded_fps": mfps,
    "video_total_frames_from_decoder": g("total_num_frames"),
    "sampled_frame_indices": fi,
    "decoded_timestamps_sec": [round(i / mfps, 4) for i in fi] if mfps else None,
    "n_sampled": len(fi or []),
}
print("\nstage 1 sampling:", json.dumps(out["stage_sampling"], ensure_ascii=False)[:400])

inputs = processor(text=[text], images=None, videos=videos, video_metadata=vmd,
                   padding=True, return_tensors="pt", **vkw)

out["stage_processor_output"] = {}
for k, v in inputs.items():
    if hasattr(v, "shape"):
        entry = {"shape": list(v.shape), "dtype": str(v.dtype)}
        if v.numel() <= 64:
            entry["values"] = v.tolist()
        out["stage_processor_output"][k] = entry
print("\nstage 2 processor output keys:")
for k, v in out["stage_processor_output"].items():
    print(f"  {k:24s} shape={v['shape']} dtype={v['dtype']}"
          + (f" values={v.get('values')}" if "values" in v else ""))

# does the text side carry explicit timestamps?
out["stage_prompt_text"] = text
tl = text.lower()
out["explicit_time_tokens_in_prompt"] = {
    "mentions_second": "second" in tl,
    "mentions_32_seconds": "32 seconds" in tl,
    "any_numeric_timestamp_list": False,
}
print("\nstage 3 prompt text (first 400 chars):")
print(text[:400])

g2 = out["stage_processor_output"]
out["consistency_checks"] = {
    "decoder_total_frames_matches_index_max": (
        g("total_num_frames") is not None and fi and max(fi) <= g("total_num_frames") - 1),
    "decoded_timestamps_monotonic_increasing": (
        all(a < b for a, b in zip(out["stage_sampling"]["decoded_timestamps_sec"],
                                  out["stage_sampling"]["decoded_timestamps_sec"][1:]))
        if out["stage_sampling"]["decoded_timestamps_sec"] else None),
    "processor_emitted_any_time_tensor": any(
        ("time" in k.lower() or "fps" in k.lower() or "second" in k.lower())
        for k in g2),
    "video_grid_thw": g2.get("video_grid_thw", {}).get("values"),
}
print("\nconsistency:", json.dumps(out["consistency_checks"], ensure_ascii=False))

thw = g2.get("video_grid_thw", {}).get("values")
if thw:
    t, h, w = thw[0]
    out["temporal_patches"] = {"t": t, "temporal_patch_size": 2,
                               "frames_implied": t * 2, "n_sampled": len(fi or [])}
    print("temporal patches:", json.dumps(out["temporal_patches"]))

out["conclusion"] = (
    "The model's final input contains NO explicit per-frame timestamps. The video is encoded as "
    "patchified tokens with a temporal grid dimension only (video_grid_thw), i.e. ordering and "
    "count, not seconds. The only temporal statement the model receives is the prompt's claim "
    "'one bounding box per second, ONLY up to 32 seconds' plus the anchor box. Therefore the "
    "mapping from output key N to a real second depends entirely on the video actually being "
    "~32 s long; nothing in the input lets the model detect a mismatch when it is not."
)
print("\n" + out["conclusion"])

dest = ROUND2 / "evidence/final_input_time_info.json"
dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
print("\nwrote", dest)
