"""Decode a frozen training-only sample by sequential source-frame order.

Run on the training host. Input/output live in a derived work directory; source
videos are opened read-only. No competition test media is accepted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np


VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos").resolve()


def main(manifest_path: str, output_path: str) -> None:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    out = Path(output_path)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for sample in manifest:
        source = Path(sample["source_path"]).resolve(strict=True)
        if VIDEO_ROOT not in source.parents or source.suffix.lower() != ".mp4":
            raise ValueError(f"source outside training videos: {source}")
        cap = cv2.VideoCapture(str(source))
        if not cap.isOpened():
            raise RuntimeError(f"cannot decode {source}")
        wanted = {int(f["source_frame_estimate"]): f for f in sample["frames"]}
        if len(wanted) != len(sample["frames"]):
            raise ValueError(f"duplicate mapped frame for {sample['video_id']}")
        last = max(wanted)
        picked = {}
        for index in range(last + 1):
            success, frame = cap.read()
            if not success:
                break
            if index not in wanted:
                continue
            item = wanted[index]
            x, y, w, h = [int(v) for v in item["roi_xywh"]]
            actual_h, actual_w = frame.shape[:2]
            if (actual_w, actual_h) != (sample["source_width"], sample["source_height"]):
                raise ValueError(f"unexpected dimensions at {sample['video_id']} frame {index}")
            if not (0 <= x and 0 <= y and x + w <= actual_w and y + h <= actual_h):
                raise ValueError(f"ROI out of bounds at {sample['video_id']} frame {index}")
            cv2.rectangle(frame, (x, y), (x + w - 1, y + h - 1), (0, 0, 255), 3)
            cv2.putText(frame, f"{sample['video_id']}  src#{index}  clip#{item['clip_frame']}",
                        (5, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"t={item['source_time_sec']:.2f}s", (5, actual_h - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2, cv2.LINE_AA)
            picked[index] = {"frame": frame, "item": item,
                             "cv2_pos_msec_after_read": cap.get(cv2.CAP_PROP_POS_MSEC)}
            if len(picked) == len(wanted):
                break
        cap.release()
        if len(picked) != len(wanted):
            raise RuntimeError(f"decoded only {len(picked)}/{len(wanted)} selected frames for {sample['video_id']}")
        ordered = [picked[int(f["source_frame_estimate"])] for f in sample["frames"]]
        contact = np.hstack([o["frame"] for o in ordered])
        name = f"{sample['row_index']:04d}_{sample['video_id']}.jpg"
        cv2.imwrite(str(out / name), contact, [cv2.IMWRITE_JPEG_QUALITY, 90])
        results.append({"row_index": sample["row_index"], "video_id": sample["video_id"],
                        "stratum": sample["stratum"], "contact": name,
                        "frames": [{"clip_frame": o["item"]["clip_frame"],
                                    "mapped_source_frame": o["item"]["source_frame_estimate"],
                                    "mapped_source_time_sec": o["item"]["source_time_sec"],
                                    "cv2_pos_msec_after_read": o["cv2_pos_msec_after_read"]}
                                   for o in ordered]})
        print(f"{sample['video_id']} {name}", flush=True)
    (out / "decode_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_samples.py MANIFEST OUTPUT_DIR")
    main(sys.argv[1], sys.argv[2])
