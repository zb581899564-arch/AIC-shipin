#!/usr/bin/env python3
"""ROUND 3 overlays: GT (green) vs prediction (red) vs anchor (blue)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

R3 = Path("/home/inspur/aic_video_work/orarl_round3")
FFMPEG = "/usr/local/bin/ffmpeg"
OUT = R3 / "outputs/overlays"


def px(b, w, h):
    return [b[0] / 1000 * w, b[1] / 1000 * h, b[2] / 1000 * w, b[3] / 1000 * h]


def label(d, xy, s, fill, bg=(0, 0, 0)):
    d.rectangle([xy[0], xy[1], xy[0] + 6 * len(s) + 4, xy[1] + 11], fill=bg)
    d.text(xy, s, fill=fill)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s2 = json.loads((R3 / "outputs/r3s2/run_status.json").read_text())
    s1 = json.loads((R3 / "outputs/r3s1/run_status.json").read_text())
    case_gt = {}
    for line in (R3 / "cases/cases_s2.jsonl").read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            case_gt[d["case_id"]] = d.get("gt_box_norm1000")
    metrics = json.loads((R3 / "evidence/r3_metrics.json").read_text())
    miou = {}
    for k in ("synthetic_keyframe", "public_refcoco"):
        for c in metrics["s2"][k]["per_case"]:
            miou[c["case_id"]] = c["iou"]

    # ---------- S2 synthetic: one sheet, 4 clips x 8 keyframes ----------
    rows = []
    for clip in ("syn1_translate_x", "syn2_translate_xy", "syn3_scale_up",
                 "syn4_translate_scale"):
        tiles = []
        for c in s2["cases"]:
            if c["sample_id"] != clip or c["condition"] != "S2_keyframe_grounding":
                continue
            im = Image.open(c["video"]).convert("RGB")
            d = ImageDraw.Draw(im)
            gt = case_gt[c["case_id"]]
            d.rectangle(px(gt, im.width, im.height), outline=(0, 255, 0), width=2)
            pr = (c.get("parsed") or {}).get("boxes_norm1000")
            if pr:
                d.rectangle(px(pr[0], im.width, im.height), outline=(255, 0, 0), width=2)
            label(d, (2, 2), f"{c['case_id'].split('_')[-1]} IoU={miou[c['case_id']]}",
                  (255, 255, 0))
            tiles.append(im)
        W = 240
        H = int(tiles[0].height * W / tiles[0].width)
        row = Image.new("RGB", (W * len(tiles), H), (0, 0, 0))
        for i, t in enumerate(tiles):
            row.paste(t.resize((W, H)), (i * W, 0))
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), (0, 0, 0))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height
    sheet.save(OUT / "s2_synthetic_keyframes.png")
    print("wrote s2_synthetic_keyframes.png", sheet.size)

    # ---------- S2 public RefCOCO ----------
    tiles = []
    for c in s2["cases"]:
        if c["condition"] != "S2_public_refcoco":
            continue
        im = Image.open(c["video"]).convert("RGB")
        W = 300
        H = int(im.height * W / im.width)
        im = im.resize((W, H))
        d = ImageDraw.Draw(im)
        gt = case_gt[c["case_id"]]
        d.rectangle(px(gt, W, H), outline=(0, 255, 0), width=2)
        pr = (c.get("parsed") or {}).get("boxes_norm1000")
        if pr:
            d.rectangle(px(pr[0], W, H), outline=(255, 0, 0), width=2)
        label(d, (2, 2), f"{c['case_id']} IoU={miou[c['case_id']]}", (255, 255, 0))
        tiles.append(im)
    cols = 5
    rws = (len(tiles) + cols - 1) // cols
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (tw * cols, th * rws), (0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(OUT / "s2_public_refcoco.png")
    print("wrote s2_public_refcoco.png", sheet.size)

    # ---------- S1 tracking ----------
    syn = json.loads((R3 / "evidence/synthetic_manifest.json").read_text())
    rows = []
    for c in s1["cases"]:
        sid = c["sample_id"]
        gt = json.loads(Path(syn["clips"][sid]["gt_file"]).read_text())
        gtf = gt["gt_box_norm1000_per_frame"]
        boxes = {int(k): v for k, v in ((c.get("parsed") or {})
                                       .get("boxes_norm1000") or {}).items()}
        anchor = c.get("init_box_norm1000")
        so = c.get("sampling_observed") or {}
        fi = so.get("frames_indices") or []
        tiles = []
        for N in (1, 5, 9, 13, 17, 21, 25, 29):
            idx = 10 * (N - 1)
            f = OUT / f"_s1_{sid}_{N}.jpg"
            subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-i", c["video"],
                            "-vf", f"select=eq(n\\,{idx})", "-vsync", "0",
                            "-frames:v", "1", str(f)], check=True,
                           stdin=subprocess.DEVNULL)
            im = Image.open(f).convert("RGB")
            d = ImageDraw.Draw(im)
            d.rectangle(px(gtf[idx], im.width, im.height), outline=(0, 255, 0), width=2)
            if anchor:
                d.rectangle(px(anchor, im.width, im.height), outline=(0, 128, 255), width=1)
            if N in boxes:
                d.rectangle(px(boxes[N], im.width, im.height), outline=(255, 0, 0), width=2)
            from analyze_r3 import iou
            label(d, (2, 2), f"N={N} t={idx/10:.0f}s IoU={round(iou(boxes[N], gtf[idx]),3) if N in boxes else 'NA'}",
                  (255, 255, 0))
            tiles.append(im)
        W = 240
        H = int(tiles[0].height * W / tiles[0].width)
        row = Image.new("RGB", (W * len(tiles), H), (0, 0, 0))
        for i, t in enumerate(tiles):
            row.paste(t.resize((W, H)), (i * W, 0))
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), (0, 0, 0))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height
    sheet.save(OUT / "s1_tracking.png")
    print("wrote s1_tracking.png", sheet.size)

    # ---------- S1 detail dump ----------
    det = []
    for c in s1["cases"]:
        boxes = {int(k): v for k, v in ((c.get("parsed") or {})
                                       .get("boxes_norm1000") or {}).items()}
        anchor = c.get("init_box_norm1000")
        vals = [boxes[k] for k in sorted(boxes)]
        eq = sum(1 for v in vals if anchor and all(abs(v[i] - anchor[i]) <= 1 for i in range(4)))
        det.append({"case_id": c["case_id"], "task_success": c["task_success"],
                    "protocol_complete": c["protocol_complete"],
                    "n_boxes": len(vals), "distinct_boxes": len({tuple(v) for v in vals}),
                    "boxes_equal_anchor": eq,
                    "frac_equal_anchor": round(eq / len(vals), 4) if vals else None,
                    "whole_segment_is_anchor_copy": bool(vals and eq == len(vals)),
                    "anchor": anchor})
        print(f"  {c['case_id']:26s} n={len(vals)} distinct={det[-1]['distinct_boxes']} "
              f"=anchor {eq}/{len(vals)} whole={det[-1]['whole_segment_is_anchor_copy']}")
    (R3 / "evidence/s1_detail.json").write_text(json.dumps(det, indent=2) + "\n")
    print("\nwrote evidence/s1_detail.json")


if __name__ == "__main__":
    main()
