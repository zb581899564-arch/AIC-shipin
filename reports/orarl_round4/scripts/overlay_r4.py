#!/usr/bin/env python3
"""ROUND 4 — overlay contact sheets (one per arm) + resource accounting."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
ARMS = R4 / "outputs/arms"
OUT = R4 / "outputs/overlays"
W_ROOT = Path("/home/inspur/aic_video_work")
BASE_WORK = 40063156224  # work-root bytes at the start of round 4


def rect(box, tw, th):
    x, y, w = float(box[0]), float(box[1]), float(box[2])
    return x, y, w, w * th / tw


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = [json.loads(l) for l in (R4 / "evidence/frozen_frames.jsonl").read_text().splitlines()
              if l.strip()]
    frozen = json.loads((R4 / "evidence/frozen_set.json").read_text())
    gmap = {g["group_key"]: g for g in frozen["groups"]}
    metrics = json.loads((R4 / "evidence/r4_metrics.json").read_text())
    per_frame = {r["frame_id"]: r for r in metrics["per_frame"]}

    def load(n):
        p = ARMS / n
        return {json.loads(l)["frame_id"]: json.loads(l)
                for l in p.read_text().splitlines() if l.strip()} if p.exists() else {}

    armbox = {
        "P0": None,   # centre-by-construction, drawn from the metrics record
        "P1": load("p1_qwen.jsonl"),
        "P2": load("p2_orarl.jsonl"),
        "P3": load("p3b_orarl.jsonl"),
    }

    for arm in ("P0", "P1", "P2", "P3"):
        tiles = []
        for gk, g in gmap.items():
            gf = sorted([f for f in frames if f["group_key"] == gk],
                        key=lambda f: f["moment_index"])
            for fr in gf:
                fid = f"{fr['group_key']}#m{fr['moment_index']}"
                im = Image.open(fr["image_path"]).convert("RGB")
                W, H = im.size
                tw, th = float(g["targetRatioWH"][0]), float(g["targetRatioWH"][1])
                d = ImageDraw.Draw(im)
                ref = fr["weak_proxy_crop_xywh"]
                d.rectangle([ref[0], ref[1], ref[0] + ref[2], ref[1] + ref[3]],
                            outline=(0, 255, 255), width=3)
                if arm == "P0":
                    cw = per_frame[fid]["max_legal_crop_w"]
                    box = [W / 2.0 - cw / 2.0, H / 2.0 - (cw * th / tw) / 2.0, cw]
                else:
                    box = (armbox[arm].get(fid) or {}).get("box_xyw")
                if box:
                    x, y, w, h = rect(box, tw, th)
                    d.rectangle([x, y, x + w, y + h], outline=(255, 60, 60), width=3)
                iou = per_frame[fid].get(f"WEAK_PROXY_IoU_{arm}")
                d.rectangle([0, 0, 250, 26], fill=(0, 0, 0))
                d.text((3, 2), f"{gk[:16]} m{fr['moment_index']}", fill=(255, 255, 0))
                d.text((3, 14), f"{arm} WEAK_PROXY_IoU={iou}", fill=(160, 255, 160))
                tiles.append(im.resize((320, int(H * 320 / W))))
        cols = 8
        rows = (len(tiles) + cols - 1) // cols
        tw_, th_ = tiles[0].size
        sheet = Image.new("RGB", (tw_ * cols, th_ * rows), (0, 0, 0))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * tw_, (i // cols) * th_))
        p = OUT / f"arm_{arm}_overlay.png"
        sheet.save(p)
        print("wrote", p, sheet.size)

    # ---------------- accounting ----------------
    recs = [json.loads(l) for l in (W_ROOT / "improvement_round1/gpu_ledger.jsonl")
            .read_text().splitlines() if l.strip()]
    mine = [r for r in recs if r["name"].startswith("r4")]
    charged = 7200 + sum(r.get("charged_seconds", 0) for r in recs)
    work = int(subprocess.check_output(
        f"du -s -B1 {W_ROOT}", shell=True, text=True).split()[0])
    free = int(subprocess.check_output(
        f"df -B1 {W_ROOT} | tail -1 | awk '{{print $4}}'", shell=True, text=True).strip())
    r4 = int(subprocess.check_output(f"du -s -B1 {R4}", shell=True, text=True).split()[0])
    acc = {
        "round4_gpu_jobs": [{"name": r["name"], "charged_seconds": round(r["charged_seconds"], 1),
                             "status": r["status"], "exit_code": r.get("exit_code"),
                             "sampled_peak_memory_mib": r.get("sampled_peak_memory_mib")}
                            for r in mine],
        "round4_gpu_seconds_total": round(sum(r["charged_seconds"] for r in mine), 1),
        "round4_gpu_cap_seconds": 3600,
        "campaign_records": len(recs),
        "campaign_charged_seconds": round(charged, 1),
        "campaign_charged_hours": round(charged / 3600, 4),
        "campaign_remaining_hours": round((86400 - charged) / 3600, 4),
        "disk": {"work_root_before_bytes": BASE_WORK, "work_root_now_bytes": work,
                 "round4_dir_bytes": r4, "round4_new_bytes": work - BASE_WORK,
                 "round4_new_gib": round((work - BASE_WORK) / 2 ** 30, 4),
                 "round4_cap_gib": 3, "project_work_cap_gib": 80,
                 "work_root_gib": round(work / 2 ** 30, 2),
                 "fs_free_bytes": free, "fs_free_gib": round(free / 2 ** 30, 2)},
    }
    (R4 / "evidence/r4_accounting.json").write_text(
        json.dumps(acc, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(acc, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
