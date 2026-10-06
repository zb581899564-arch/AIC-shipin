#!/usr/bin/env python3
"""Round-2 overlays: for every sample, one sheet with 3 rows (conditions A/B/C)
and 8 sampled seconds (1,5,9,13,17,21,25,29).

Red  = the model's predicted box for that second.
Blue = the anchor box that was supplied in the prompt (conditions B/C only).
Each tile is the frame the model ACTUALLY saw for that second bin, so the
prediction can be checked against the real content.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
OUT = R2 / "outputs/r2tr"
OVER = R2 / "outputs/overlays"
FFMPEG = "/usr/local/bin/ffmpeg"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
PICK = [1, 5, 9, 13, 17, 21, 25, 29]


def probe(p):
    d = json.loads(subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate",
         "-show_entries", "format=duration", "-of", "json", p], text=True))
    st = d["streams"][0]
    n, dn = (st.get("avg_frame_rate") or "0/1").split("/")
    return {"w": int(st["width"]), "h": int(st["height"]),
            "fps": float(n) / float(dn) if float(dn) else 30.0,
            "dur": float(d["format"]["duration"])}


def grab(video, t, out):
    subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error", "-ss", f"{max(0.0,t):.4f}",
                    "-i", video, "-frames:v", "1", str(out)], check=True,
                   stdin=subprocess.DEVNULL)
    return out


def px(box, w, h):
    return [box[0] / 1000 * w, box[1] / 1000 * h, box[2] / 1000 * w, box[3] / 1000 * h]


def main():
    OVER.mkdir(parents=True, exist_ok=True)
    st = json.loads((OUT / "run_status.json").read_text())
    frozen = json.loads((R2 / "evidence/samples_frozen.json").read_text())
    fmap = {s["sample_id"]: s for s in frozen["samples"]}
    by = {(c["sample_id"], c["condition"]): c for c in st["cases"]}

    made = {}
    for sid, s in fmap.items():
        video = s["clip"]
        pm = probe(video)
        sofps = None
        rows = []
        for cond in ("A", "B", "C"):
            c = by.get((sid, cond))
            if not c:
                continue
            so = c.get("sampling_observed") or {}
            fi = so.get("frames_indices") or []
            fps = so.get("decoded_at_fps") or pm["fps"]
            boxes = {int(k): v for k, v in ((c.get("parsed") or {})
                                            .get("boxes_norm1000") or {}).items()}
            anchor = c.get("init_box_norm1000")
            tiles = []
            for sec in PICK:
                if 1 <= sec <= len(fi):
                    t = fi[sec - 1] / fps
                else:
                    t = sec - 1
                f = OVER / f"_r2_{sid}_{cond}_{sec}.jpg"
                grab(video, t, f)
                im = Image.open(f).convert("RGB")
                d = ImageDraw.Draw(im)
                if anchor:
                    d.rectangle(px(anchor, im.width, im.height),
                                outline=(0, 128, 255), width=2)
                if sec in boxes:
                    d.rectangle(px(boxes[sec], im.width, im.height),
                                outline=(255, 0, 0), width=3)
                d.rectangle([0, im.height - 26, 150, im.height], fill=(0, 0, 0))
                d.text((3, im.height - 24), f"{cond} sec={sec} t={t:.1f}",
                       fill=(255, 255, 0))
                if sec in boxes:
                    d.text((3, im.height - 12), f"box={[int(v) for v in boxes[sec]]}",
                           fill=(255, 120, 120))
                tiles.append(im)

            tw = 300
            th = int(tiles[0].height * tw / tiles[0].width)
            row = Image.new("RGB", (tw * len(tiles), th), (0, 0, 0))
            for i, t in enumerate(tiles):
                row.paste(t.resize((tw, th)), (i * tw, 0))
            rows.append(row)
        if not rows:
            continue
        W = rows[0].width
        sheet = Image.new("RGB", (W, sum(r.height for r in rows)), (0, 0, 0))
        y = 0
        for r in rows:
            sheet.paste(r, (0, y))
            y += r.height
        dest = OVER / f"abc_{sid}.png"
        sheet.save(dest)
        made[sid] = {"sheet": str(dest), "size": list(sheet.size),
                     "target": s["target"], "stratum": s["stratum"]}
        print(f"  {sid:7s} -> {dest.name}  {sheet.size}  target={s['target'][:44]}")

    (R2 / "evidence/overlay_manifest_r2.json").write_text(
        json.dumps(made, indent=2, ensure_ascii=False) + "\n")
    print("\nwrote", R2 / "evidence/overlay_manifest_r2.json")

    # compact trajectory dump
    print("\n=== trajectories (median / first / last box per case) ===")
    for (sid, cond), c in sorted(by.items()):
        p = c.get("parsed") or {}
        b = {int(k): v for k, v in (p.get("boxes_norm1000") or {}).items()}
        if not b:
            print(f"  {sid:7s} {cond}  NO BOXES  errors={c['parse_errors'][:1]}")
            continue
        ks = sorted(b)
        print(f"  {sid:7s} {cond}  n={len(b):2d} first={[int(x) for x in b[ks[0]]]} "
              f"mid={[int(x) for x in b[ks[len(ks)//2]]]} last={[int(x) for x in b[ks[-1]]]}"
              + (f"  anchor={[int(x) for x in c['init_box_norm1000']]}"
                 if c.get("init_box_norm1000") else ""))


if __name__ == "__main__":
    main()
