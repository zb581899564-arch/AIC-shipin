#!/usr/bin/env python3
"""P1b step 4 (part 2): local decode analysis of the 8 frozen pilot files.

CPU only (PyAV + numpy), no GPU, no model, no network.  For every file:

* container/PTS evidence from demuxed packets (no decode): time base, first/last PTS,
  median step, maximum step deviation, CFR flag;
* a frame timetable (fps, n_frames, duration) for the annotation tool;
* sparse visual fingerprints: 12 evenly spaced decoded frames reduced to 16x16
  grayscale thumbnails, plus a whole-file fingerprint;
* pairwise near-duplicate distances across the 8 files.

Writes reports/round6_score_alignment/phase1b/media_verification.json
(plus the fingerprint table used by the tool).
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "round6_score_alignment/p1b/media"
OUT = ROOT / "reports/round6_score_alignment/phase1b/media_verification.json"
FP_OUT = ROOT / "round6_score_alignment/p1b/fingerprints.json"
SAMPLES = 12
THUMB = 16

FROZEN = [
    ("P01", "0ReDuH0_rpI_210.0_360.0.mp4", [16, 9], "0ReDuH0_rpI"),
    ("P02", "FQEW3xLOa9M_210.0_360.0.mp4", [16, 9], "FQEW3xLOa9M"),
    ("P03", "GYH6HdJ6nao_210.0_360.0.mp4", [16, 9], "GYH6HdJ6nao"),
    ("P04", "QPcwfuStFnU_210.0_360.0.mp4", [16, 9], "QPcwfuStFnU"),
    ("P05", "Snpclpo7Ono_210.0_360.0.mp4", [9, 16], "Snpclpo7Ono"),
    ("P06", "Xm1ouND-aiQ_210.0_360.0.mp4", [9, 16], "Xm1ouND-aiQ"),
    ("P07", "dEuxoRj0G5Y_210.0_360.0.mp4", [9, 16], "dEuxoRj0G5Y"),
    ("P08", "vvT-gqzwUxA_60.0_210.0.mp4", [9, 16], "vvT-gqzwUxA"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def demux_pts(path: Path) -> dict:
    """Packet timestamps only: cheap and independent of decoding.

    Packets are stored in decode order, so with B-frames the PTS sequence is NOT
    monotonic.  CFR has to be judged on the *sorted* presentation timestamps;
    the decode-order statistics are kept for transparency.
    """
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        tb = stream.time_base
        pts_raw, dts_raw = [], []
        for packet in container.demux(stream):
            if packet.pts is not None:
                pts_raw.append(packet.pts)
            if packet.dts is not None:
                dts_raw.append(packet.dts)
    # presentation order
    pts = sorted(float(p * tb) for p in pts_raw)
    steps = [round(b - a, 9) for a, b in zip(pts, pts[1:])]
    median = statistics.median(steps) if steps else None
    max_dev = max((abs(s - median) for s in steps), default=None)
    dts_steps = [d - c for c, d in zip(dts_raw, dts_raw[1:])]
    return {
        "time_base_seconds": float(tb),
        "packets_with_pts": len(pts_raw),
        "packets_with_dts": len(dts_raw),
        "first_pts_sec": pts[0] if pts else None,
        "last_pts_sec": pts[-1] if pts else None,
        "median_step_sec": median,
        "max_abs_step_deviation_sec": max_dev,
        "max_abs_step_deviation_ticks": (round(max_dev / float(tb), 3)
                                         if max_dev is not None else None),
        "presentation_order_sorted": True,
        "decode_order_monotonic_pts": all(b >= a for a, b in zip(pts_raw, pts_raw[1:])),
        "dts_monotonic": all(d >= 0 for d in dts_steps),
        "dts_max_step_deviation_ticks": (max((abs(float(d) - statistics.median(dts_steps))
                                              for d in dts_steps), default=0) if dts_steps else None),
        "cfr_within_1us": (max_dev is not None and max_dev <= 1.5e-6),
        "cfr_within_one_tick": (max_dev is not None and max_dev <= float(tb) + 1e-12),
        "stream_start_is_zero": (bool(pts) and abs(pts[0]) < 1e-6),
    }


def decode_fingerprints(path: Path, n_samples: int = SAMPLES) -> dict:
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        tb = float(stream.time_base)
        frames = []
        for frame in container.decode(stream):
            frames.append(frame)
    total = len(frames)
    if total == 0:
        return {"decoded_frames": 0}
    idx = [int(round(x)) for x in np.linspace(0, total - 1, min(n_samples, total))]
    thumbs, table = [], []
    for i in idx:
        frame = frames[i]
        arr = frame.to_ndarray(format="gray")
        small = np.asarray(av.VideoFrame.from_ndarray(arr, format="gray")
                           .reformat(width=THUMB, height=THUMB).to_ndarray(format="gray"),
                           dtype=np.uint8) if False else None
        # simple area resample with numpy (av reformat needs a frame context, keep it explicit)
        h, w = arr.shape
        ys = (np.linspace(0, h - 1, THUMB)).astype(int)
        xs = (np.linspace(0, w - 1, THUMB)).astype(int)
        small = arr[np.ix_(ys, xs)]
        thumbs.append(small.astype(np.float32))
        table.append({"index": i, "pts_sec": round(float(frame.pts * tb) if frame.pts is not None else i / float(stream.average_rate), 6),
                      "thumb_sha256": hashlib.sha256(small.tobytes()).hexdigest()[:16]})
    stack = np.stack(thumbs)
    per_frame_hash = hashlib.sha256(stack.astype(np.uint8).tobytes()).hexdigest()
    return {
        "decoded_frames": total,
        "sampled_indices": idx,
        "thumbnails": stack.astype(np.uint8).reshape(len(idx), -1).tolist(),
        "frame_table": table,
        "video_fingerprint": per_frame_hash,
        "mean_luma": round(float(stack.mean()), 4),
    }


def main() -> int:
    started = time.time()
    items, fps_table = [], {}
    for sample_id, name, ratio, yt in FROZEN:
        path = MEDIA / name
        entry = {"sample_id": sample_id, "file_name": name, "youtube_id": yt,
                 "target_ratio_wh": ratio, "local_path": str(path),
                 "local_bytes": path.stat().st_size,
                 "local_sha256": sha256(path)}
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            entry["decode_probe"] = {
                "width": stream.width, "height": stream.height,
                "average_rate": float(stream.average_rate) if stream.average_rate else None,
                "base_rate": float(stream.base_rate) if stream.base_rate else None,
                "frames": stream.frames,
                "duration_sec": float(stream.duration * stream.time_base) if stream.duration else None,
                "codec": stream.codec_context.name,
            }
        entry["pts"] = demux_pts(path)
        fp = decode_fingerprints(path)
        entry["fingerprint"] = {k: v for k, v in fp.items() if k != "thumbnails"}
        entry["_thumbs"] = np.asarray(fp["thumbnails"], dtype=np.float32).reshape(
            len(fp.get("sampled_indices", [])), -1) if fp.get("thumbnails") else None
        items.append(entry)
        fps_table[sample_id] = {
            "fps": entry["decode_probe"]["average_rate"],
            "n_frames": fp.get("decoded_frames"),
            "duration_sec": round(fp.get("decoded_frames", 0)
                                  / (entry["decode_probe"]["average_rate"] or 1), 6),
            "frame_table": fp.get("frame_table"),
        }
        print(f"[{sample_id}] {name}: {entry['decode_probe']['width']}x"
              f"{entry['decode_probe']['height']} fps={entry['decode_probe']['average_rate']:.4f} "
              f"frames={fp.get('decoded_frames')} cfr_1tick={entry['pts']['cfr_within_one_tick']} "
              f"start0={entry['pts']['stream_start_is_zero']}", flush=True)

    # pairwise near-duplicate distances between the 8 sources
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i]["_thumbs"], items[j]["_thumbs"]
            if a is None or b is None or a.shape != b.shape:
                continue
            d = float(np.abs(a - b).mean())
            pairs.append({"a": items[i]["sample_id"], "b": items[j]["sample_id"],
                          "mean_abs_thumb_diff": round(d, 4),
                          "near_duplicate": bool(d < 2.0)})
    for item in items:
        item.pop("_thumbs", None)

    result = {
        "schema": "p1b_media_verification_v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cpu_seconds": round(time.time() - started, 2),
        "decoder": f"PyAV {av.__version__} (CPU only)",
        "samples": SAMPLES,
        "thumb_size": THUMB,
        "items": items,
        "near_duplicate_check": {
            "method": "mean absolute difference of 12 x 16x16 grayscale thumbnails",
            "threshold_note": "a threshold of 2.0 gray levels is reported as 'near' for "
                              "visibility; no sample was dropped or replaced by this number",
            "pairs": pairs,
            "n_near_duplicate_pairs": sum(1 for p in pairs if p["near_duplicate"]),
        },
        "notes": [
            "PTS evidence comes from packet timestamps (demux only); fingerprints need decode",
            "hashing fixes media bytes only and does not prove alignment with historical labels",
            "no frame was sent to any external service",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FP_OUT.write_text(json.dumps(
        {"schema": "p1b_frame_timetable_v1",
         "note": "fps/frame/duration table used by the annotation page; times are derived from "
                 "the decoded frame index divided by the average frame rate",
         "videos": fps_table}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cpu_seconds": result["cpu_seconds"],
                      "n_near_duplicate_pairs": result["near_duplicate_check"]["n_near_duplicate_pairs"],
                      "all_cfr_within_1us": all(i["pts"]["cfr_within_1us"] for i in items),
                      "all_cfr_within_one_tick": all(i["pts"]["cfr_within_one_tick"] for i in items),
                      "all_start_zero": all(i["pts"]["stream_start_is_zero"] for i in items)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
