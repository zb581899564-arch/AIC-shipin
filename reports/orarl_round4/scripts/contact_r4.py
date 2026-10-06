#!/usr/bin/env python3
"""ROUND 4 — contact sheet for the AGENT-REVIEWED mapping spot check.

This is an agent-reviewed consistency check between the label's
`teacher_signals.summary` and the actual frame at the computed source time.
It is NOT independent ground-truth confirmation.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
LABELS = Path("/home/inspur/aic_video_data/labels/train.jsonl")


def main():
    frozen = json.loads((R4 / "evidence/frozen_set.json").read_text())
    frames = [json.loads(l) for l in (R4 / "evidence/frozen_frames.jsonl").read_text().splitlines()
              if l.strip()]
    rows = [json.loads(l) for l in LABELS.read_text().splitlines() if l.strip()]

    by_group = {}
    for fr in frames:
        by_group.setdefault(fr["group_key"], []).append(fr)

    outdir = R4 / "outputs/contact"
    outdir.mkdir(parents=True, exist_ok=True)

    review = []
    for gi, g in enumerate(frozen["groups"]):
        gk = g["group_key"]
        row = next((r for r in rows
                    if r["clip"]["source_vid"] == gk), None)
        summary = ((row or {}).get("teacher_signals") or {}).get("summary", "")
        used = (row or {}).get("clip", {}).get("used_window")
        gfr = sorted(by_group.get(gk, []), key=lambda f: f["moment_index"])
        if not gfr:
            continue
        tiles = []
        for fr in gfr:
            im = Image.open(fr["image_path"]).convert("RGB")
            W = 420
            H = int(im.height * W / im.width)
            im = im.resize((W, H))
            d = ImageDraw.Draw(im)
            b = fr["weak_proxy_crop_xywh"]
            sc = W / g["source_probe"]["width"]
            d.rectangle([b[0] * sc, b[1] * sc, (b[0] + b[2]) * sc, (b[1] + b[3]) * sc],
                        outline=(0, 255, 255), width=2)
            d.rectangle([0, H - 30, W, H], fill=(0, 0, 0))
            d.text((3, H - 28), f"{gk[:18]} m{fr['moment_index']} "
                                f"srcT={fr['source_time_sec']:.2f}s", fill=(255, 255, 0))
            d.text((3, H - 14), f"weakROI={b} d={fr['weak_proxy_roi_frame_delta']}",
                   fill=(120, 255, 200))
            tiles.append(im)
        # stack group tiles vertically; one group per column
        tw, th = tiles[0].size
        col = Image.new("RGB", (tw, th * len(tiles) + 46), (0, 0, 0))
        dd = ImageDraw.Draw(col)
        dd.text((3, 2), f"[g{gi:02d}] {gk}  travel={g['free_axis_travel']:.3f} "
                        f"clipFps={g['clip_fps']:g}", fill=(0, 255, 255))
        dd.text((3, 16), f"src={Path(g['source_path']).name} "
                         f"{g['source_probe']['width']}x{g['source_probe']['height']}",
                fill=(200, 200, 200))
        dd.text((3, 30), f"teacher summary: {summary[:60]}", fill=(255, 200, 120))
        for i, t in enumerate(tiles):
            col.paste(t, (0, 46 + i * th))
        col.save(outdir / f"contact_g{gi:02d}_{gk[:20]}.png")
        review.append({"group_index": gi, "group_key": gk,
                       "teacher_summary": summary,
                       "used_window": used,
                       "source_path": g["source_path"],
                       "n_moments": len(gfr),
                       "sheet": str(outdir / f"contact_g{gi:02d}_{gk[:20]}.png"),
                       "frame_origin": [f["moment_origin"] for f in gfr],
                       "source_times_sec": [f["source_time_sec"] for f in gfr],
                       "weak_proxy_roi_frame_delta": [f["weak_proxy_roi_frame_delta"] for f in gfr]})

    # combined sheet (first 5 groups side by side, then next 5)
    sheets = sorted(outdir.glob("contact_g*.png"))
    for half in (0, 1):
        part = sheets[half * 5: half * 5 + 5]
        if not part:
            continue
        ims = [Image.open(p) for p in part]
        H = max(i.height for i in ims)
        W = sum(i.width for i in ims)
        sh = Image.new("RGB", (W, H), (0, 0, 0))
        x = 0
        for i in ims:
            sh.paste(i, (x, 0)); x += i.width
        sh.save(outdir / f"contact_sheet_{half+1}.png")
        print("wrote", outdir / f"contact_sheet_{half+1}.png", sh.size)

    (R4 / "evidence/contact_review.json").write_text(json.dumps({
        "status": "AGENT_REVIEWED (not independent ground-truth confirmation)",
        "method": ("contact sheet per group showing the frame at the computed source time with "
                   "the WEAK_PROXY cropRoi drawn; compared by eye against the label's "
                   "teacher_signals.summary"),
        "warning": ("a visual match does not prove the clip->source offset is correct for every "
                    "frame, and a mismatch may reflect summary vagueness rather than a bad "
                    "mapping"),
        "groups": review,
    }, indent=2, ensure_ascii=False) + "\n")
    for r in review:
        print(f"  g{r['group_index']:02d} {r['group_key'][:22]:22s} moments={r['n_moments']} "
              f"srcT={r['source_times_sec']} roi_delta={r['weak_proxy_roi_frame_delta']}")
    print("\nwrote evidence/contact_review.json")
    return 0


if __name__ == "__main__":
    main()
