#!/usr/bin/env python3
"""ROUND 3 — build the S0/S1/S2 case files.

S0  constant baseline: the ground-truth FIRST-frame box held for the whole clip.
    Analytic, no model. Computed by analyze_r3.py.
S1  OraRL tracking under the author protocol, given the GT first-frame box.
S2  OraRL independent spatial grounding on fixed key frames (8 per synthetic
    clip), no previous-frame box. Also used for the 10 public RefCOCO images.

Key frames are FIXED HERE, before any model output:
    synthetic clips: frame indices 10, 50, 90, 130, 170, 210, 250, 290
    (t = 1, 5, 9, 13, 17, 21, 25, 29 s at 10 fps -> exactly representable)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

R3 = Path("/home/inspur/aic_video_work/orarl_round3")
FFMPEG = "/usr/local/bin/ffmpeg"
KEYFRAMES = [10, 50, 90, 130, 170, 210, 250, 290]
TRACK_SAMPLING = {"fps": 1, "max_frames": 32, "min_pixels": 4096,
                  "max_pixels": 786432, "total_pixels": 8388608}
SG_SAMPLING = {"min_pixels": 65536, "max_pixels": 1048576}


def bbox_literal(box):
    return "[" + ",".join(str(int(round(v))) for v in box) + "]"


def main():
    syn = json.loads((R3 / "evidence/synthetic_manifest.json").read_text())
    ref = json.loads((R3 / "evidence/refcoco_frozen.json").read_text())
    (R3 / "cases").mkdir(exist_ok=True)
    (R3 / "frames/kf").mkdir(parents=True, exist_ok=True)

    s2, s1, s0 = [], [], {}

    # ---------- synthetic ----------
    for name, info in syn["clips"].items():
        gt = json.loads(Path(info["gt_file"]).read_text())
        clip = info["path"]
        # S0: GT first-frame box held constant
        s0[name] = {
            "clip": clip, "kind": "synthetic", "box_norm1000": gt["gt_first_frame_norm1000"],
            "definition": "ground-truth FIRST-frame box, held constant for all 32 seconds",
            "gt_box_norm1000_per_frame": gt["gt_box_norm1000_per_frame"],
            "gt_index_to_seconds": gt["gt_index_to_seconds"],
            "fps": gt["fps"], "n_frames": gt["n_frames"],
        }
        # S1: tracking with the GT first-frame box as the prompt anchor
        s1.append({
            "case_id": f"s1_{name}", "sample_id": name, "task": "tracking",
            "condition": "S1_tracking_with_gt_first_box",
            "video": clip, "sampling": dict(TRACK_SAMPLING),
            "question": (f"Given the bounding box "
                         f"{bbox_literal(gt['gt_first_frame_norm1000'])} of the target object, "
                         f"please track this object throughout the video."),
            "init_box_norm1000": gt["gt_first_frame_norm1000"],
            "init_box_source": "ground_truth_first_frame (analytic, from the generator)",
            "is_test_set": False,
            "gt_file": info["gt_file"],
        })
        # S2: independent spatial grounding on fixed key frames
        for kf in KEYFRAMES:
            png = R3 / f"frames/kf/{name}_n{kf:03d}.png"
            if not png.exists():
                subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error",
                                "-i", clip, "-vf", f"select=eq(n\\,{kf})",
                                "-vsync", "0", "-frames:v", "1", str(png)], check=True,
                               stdin=subprocess.DEVNULL)
            s2.append({
                "case_id": f"s2_{name}_n{kf:03d}", "sample_id": name,
                "task": "spatial_grounding", "condition": "S2_keyframe_grounding",
                "expression": "the red rectangle",
                "image": str(png), "sampling": dict(SG_SAMPLING),
                "is_test_set": False,
                "gt_box_norm1000": gt["gt_box_norm1000_per_frame"][kf],
                "gt_frame_index": kf, "gt_time_sec": gt["gt_index_to_seconds"][kf],
                "gt_source": "analytic generator ground truth",
            })

    # ---------- public RefCOCO images (spatial grounding only) ----------
    for s in ref["samples"]:
        s2.append({
            "case_id": f"s2_{s['sample_id']}", "sample_id": s["sample_id"],
            "task": "spatial_grounding", "condition": "S2_public_refcoco",
            "expression": s["expression"], "image": s["image_file"],
            "sampling": dict(SG_SAMPLING), "is_test_set": False,
            "gt_box_norm1000": s["gt_bbox_norm1000"],
            "gt_source": "RefCOCO val annotation via rhymes-ai/RefCOCO (public)",
            "refcoco": {k: s[k] for k in ("image_name", "url", "annotation_hw",
                                          "actual_image_wh", "hw_matches_image",
                                          "image_sha256")},
        })

    def wl(p, rows):
        Path(p).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    wl(R3 / "cases/cases_s2.jsonl", s2)
    wl(R3 / "cases/cases_s1.jsonl", s1)
    (R3 / "evidence/s0_baseline.json").write_text(
        json.dumps(s0, indent=2, ensure_ascii=False) + "\n")

    print(f"S0 baselines: {len(s0)} synthetic clips (analytic)")
    print(f"S1 tracking cases: {len(s1)}")
    print(f"S2 grounding cases: {len(s2)} "
          f"({sum(1 for c in s2 if c['condition']=='S2_keyframe_grounding')} synthetic keyframes"
          f" + {sum(1 for c in s2 if c['condition']=='S2_public_refcoco')} public RefCOCO)")
    print(f"keyframes fixed at frames {KEYFRAMES} (t = "
          f"{[round(k/10,1) for k in KEYFRAMES]} s)")
    print("wrote cases/cases_s1.jsonl, cases/cases_s2.jsonl, evidence/s0_baseline.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
