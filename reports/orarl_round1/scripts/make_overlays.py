#!/usr/bin/env python3
"""Render predicted norm1000 boxes and predicted time spans back onto real
frames so every claim in the report can be checked by eye.

CPU only. Reads run_status.json + sample_manifest.json, writes PNGs.
No box is repaired or nudged: whatever the model emitted is what is drawn.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

FFMPEG = "/usr/local/bin/ffmpeg"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"


def probe(path):
    out = subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", path], text=True)
    d = json.loads(out)
    st = d["streams"][0]
    fr = st.get("avg_frame_rate") or "0/1"
    n, dn = fr.split("/")
    fps = float(n) / float(dn) if float(dn) else 0.0
    dur = d.get("format", {}).get("duration")
    return dict(w=int(st["width"]), h=int(st["height"]), fps=fps,
                nb=int(st["nb_frames"]) if st.get("nb_frames") else None,
                dur=float(dur) if dur is not None else None)


def grab(video, t, out):
    subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", f"{t:.4f}",
                    "-i", video, "-frames:v", "1", out], check=True,
                   stdin=subprocess.DEVNULL)
    return out


def norm1000_to_px(box, w, h):
    return [box[0] / 1000 * w, box[1] / 1000 * h,
            box[2] / 1000 * w, box[3] / 1000 * h]


def draw_box(img, box_px, colour=(255, 0, 0), width=3, label=None):
    d = ImageDraw.Draw(img)
    d.rectangle(box_px, outline=colour, width=width)
    if label:
        d.rectangle([box_px[0], max(0, box_px[1] - 14), box_px[0] + 8 * len(label),
                     box_px[1]], fill=colour)
        d.text((box_px[0] + 2, max(0, box_px[1] - 13)), label, fill=(255, 255, 255))
    return img


def main():
    R = Path("/home/inspur/aic_video_work/orarl_round1")
    run = json.load(open(R / "outputs/run_status.json"))
    man = json.load(open(R / "evidence/sample_manifest.json"))
    ov = R / "outputs/overlays"
    ov.mkdir(parents=True, exist_ok=True)
    summary = {}

    # ---------- spatial grounding ----------
    sg = run["tasks"].get("spatial_grounding", {})
    if sg.get("parsed"):
        src = man["tasks"]["spatial_grounding_image"]["input_image"]
        p = probe(src)
        img = Image.open(src).convert("RGB")
        made = []
        for i, b in enumerate(sg["parsed"]["boxes_norm1000"]):
            px = norm1000_to_px(b, p["w"], p["h"])
            draw_box(img, px, (255, 0, 0), 3, f"pred{i}")
            made.append({"norm1000": b, "px": [round(v, 2) for v in px]})
        out = ov / "spatial_grounding_overlay.png"
        img.save(out)
        summary["spatial_grounding"] = {
            "image": src, "image_wh": [p["w"], p["h"]],
            "expression": man["tasks"]["spatial_grounding_image"]["expression"],
            "boxes": made, "overlay": str(out),
        }
        print("spatial overlay ->", out, made)

    # ---------- tracking ----------
    tr = run["tasks"].get("tracking", {})
    if tr.get("parsed"):
        clip = man["tasks"]["tracking_video"]["input_video"]
        p = probe(clip)
        fi = (tr.get("sampled_frames") or {}).get("frames_indices") or []
        boxes = {int(k): v for k, v in tr["parsed"]["boxes_norm1000"].items()}
        tiles, made = [], []
        for sec in sorted(boxes):
            # second N  <-> N-th sampled frame (fps=1 sampling)
            if 1 <= sec <= len(fi):
                idx = fi[sec - 1]
                t = idx / p["fps"] if p["fps"] else sec - 1
            else:
                t = sec - 1
                idx = None
            f = ov / f"_tr_{sec:02d}.jpg"
            grab(clip, t, str(f))
            img = Image.open(f).convert("RGB")
            px = norm1000_to_px(boxes[sec], img.width, img.height)
            draw_box(img, px, (255, 0, 0), 3, f"t={sec}s")
            img.save(ov / f"tracking_sec_{sec:02d}.png")   # drawn tile, checkable
            tiles.append(img)
            made.append({"second": sec, "sampled_frame_index": idx,
                         "t_sec": round(t, 4), "norm1000": boxes[sec],
                         "px_in_frame": [round(v, 2) for v in px]})
        if tiles:
            tw = 320
            th = int(tiles[0].height * tw / tiles[0].width)
            cols = 6
            rows = (len(tiles) + cols - 1) // cols
            sheet = Image.new("RGB", (tw * cols, th * rows), (20, 20, 20))
            for i, t in enumerate(tiles):
                sheet.paste(t.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
            out = ov / "tracking_overlay_sheet.png"
            sheet.save(out)
            summary["tracking"] = {
                "clip": clip, "clip_wh": [p["w"], p["h"]], "clip_fps": p["fps"],
                "target": man["tasks"]["tracking_video"]["target_description"],
                "per_second": made, "overlay_sheet": str(out),
            }
            print("tracking overlay ->", out, "n=", len(made))

    # ---------- temporal grounding ----------
    tg = run["tasks"].get("temporal_grounding", {})
    if tg.get("parsed"):
        clip = man["tasks"]["temporal_grounding_video"]["input_video"]
        p = probe(clip)
        st, en = tg["parsed"]["span_sec"]
        stored = man["tasks"]["temporal_grounding_video"]["stored_label_window_sec"]
        items = [("pred_start", st), ("pred_mid", (st + en) / 2), ("pred_end", en),
                 ("stored_start", stored[0]), ("stored_end", stored[1])]
        tiles = []
        for name, t in items:
            t = max(0.0, min(t, max(0.0, p["dur"] - 1.0 / max(p["fps"], 1))))
            f = ov / f"_tg_{name}.jpg"
            grab(clip, t, str(f))
            img = Image.open(f).convert("RGB")
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, 260, 16], fill=(0, 0, 0))
            d.text((3, 3), f"{name} t={t:.2f}s", fill=(255, 255, 0))
            tiles.append(img)
        tw = 400
        th = int(tiles[0].height * tw / tiles[0].width)
        sheet = Image.new("RGB", (tw * len(tiles), th), (20, 20, 20))
        for i, t in enumerate(tiles):
            sheet.paste(t.resize((tw, th)), (i * tw, 0))
        out = ov / "temporal_grounding_frames.png"
        sheet.save(out)
        summary["temporal_grounding"] = {
            "clip": clip, "clip_duration_sec": p["dur"],
            "predicted_span_sec": [st, en],
            "stored_label_window_sec": stored,
            "diagnostic_iou_vs_stored_window": round(
                max(0.0, min(en, stored[1]) - max(st, stored[0])) /
                max(1e-9, max(en, stored[1]) - min(st, stored[0])), 4),
            "diagnostic_note": ("temporal IoU against a label whose identity is UNTRUSTED "
                                "(trusted_identity=false). Diagnostic juxtaposition only - "
                                "NOT an accuracy metric."),
            "frames_png": str(out),
        }
        print("temporal overlay ->", out)

    json.dump(summary, open(R / "outputs/overlay_manifest.json", "w"),
              indent=2, ensure_ascii=False)
    print("\nwrote", R / "outputs/overlay_manifest.json")


if __name__ == "__main__":
    main()
