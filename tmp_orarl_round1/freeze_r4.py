#!/usr/bin/env python3
"""ROUND 4 — freeze the real-video diagnostic set BEFORE any model output.

Strata are the ones fixed by the round-4 brief on `clip.free_axis_travel`:
    <= 0.05 ; (0.05, 0.25) ; >= 0.25
Each stratum: sort candidates by sha256(provenance.source_group), take the first
10 that also satisfy the extra conditions. Empty strata are reported as 0 and
are NOT backfilled from other strata.

Extra conditions enforced here:
    * quality.status == "accepted"
    * spatial coverage complete (timeline_coverage == trajectory_coverage == 1.0)
      and cropRois present
    * target ratio legal (targetRatioWH parses, both > 0)
    * source video uniquely readable (already guaranteed by the mapping gate)
    * at least 3 spatial evaluation moments inside a selected highlight segment
    * no two chosen groups may come from the same SOURCE VIDEO (deduped by the
      YouTube id embedded in source_vid, since one source video can appear as
      several window names)
Each group gets at most 4 evaluation moments: in-segment crop_keyframes first,
then uniform points inside segments. Hard cap 120 frames overall.

Writes evidence/frozen_set.json + frames/<group>/<moment>.jpg + evidence/frozen_frames.jsonl
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
FFMPEG = "/usr/local/bin/ffmpeg"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
LABELS = Path("/home/inspur/aic_video_data/labels/train.jsonl")

STRATA = [("low_le_0.05", lambda v: v <= 0.05),
          ("mid_0.05_0.25", lambda v: 0.05 < v < 0.25),
          ("high_ge_0.25", lambda v: v >= 0.25)]
PER_STRATUM = 10
MAX_MOMENTS = 4
MAX_FRAMES = 120
MIN_IN_SEGMENT = 3


def sha256_str(s):
    return hashlib.sha256(s.encode()).hexdigest()


def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def snap_fps(x):
    for c in (23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0):
        if x and abs(c - x) / x < 0.01:
            return c
    return x


def robust_fps(row):
    pairs = []
    for k in (row.get("crop_keyframes") or []):
        f, t = k.get("frame"), k.get("time_sec")
        if isinstance(f, (int, float)) and isinstance(t, (int, float)) and f > 0 and t > 0:
            pairs.append((float(f), float(t)))
    if len(pairs) < 2:
        for s in (row.get("segments") or []):
            for fk, tk in (("start_frame", "start_sec"), ("end_frame", "end_sec")):
                f, t = s.get(fk), s.get(tk)
                if isinstance(f, (int, float)) and isinstance(t, (int, float)) and f > 0 and t > 0:
                    pairs.append((float(f), float(t)))
    if len(pairs) < 2:
        return None
    ratios = sorted(f / t for f, t in pairs)
    med = ratios[len(ratios) // 2]
    fps = min((23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0),
              key=lambda c: abs(c - med))
    if abs(fps - med) / med >= 0.02:
        fps = med
    if max(abs(f - t * fps) for f, t in pairs) > 1.5:
        return None
    return fps


def probe(path):
    d = json.loads(subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate",
         "-show_entries", "format=duration", "-of", "json", str(path)], text=True))
    st = d["streams"][0]
    n, dn = (st.get("avg_frame_rate") or "0/1").split("/")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "fps": float(n) / float(dn) if float(dn) else None,
            "duration_sec": float(d["format"]["duration"])}


def main():
    rep = json.loads((R4 / "evidence/mapping_report.json").read_text())
    rows_all = [json.loads(l) for l in (R4 / "evidence/mapping_rows.jsonl").read_text().splitlines()
                if l.strip()]
    usable = {r["row_index"]: r for r in rows_all if r["status"] == "usable"}
    labels = [json.loads(l) for l in LABELS.read_text().splitlines() if l.strip()]
    print(f"usable mapping rows: {len(usable)}")

    # ---- build candidates with the extra conditions ----
    cands = []
    rejected = Counter()
    for idx, m in usable.items():
        r = labels[idx]
        q = r.get("quality") or {}
        c = r["clip"]
        tr = r.get("targetRatioWH")
        if q.get("status") != "accepted":
            rejected["quality_not_accepted"] += 1; continue
        if not (q.get("timeline_coverage") == 1.0 and q.get("trajectory_coverage") == 1.0):
            rejected["coverage_incomplete"] += 1; continue
        rois = r.get("cropRois") or []
        if not rois:
            rejected["no_cropRois"] += 1; continue
        if not (isinstance(tr, (list, tuple)) and len(tr) == 2 and tr[0] > 0 and tr[1] > 0):
            rejected["bad_target_ratio"] += 1; continue
        pro = probe(Path(m["source_path"]))
        if not pro.get("duration_sec") or not pro.get("fps"):
            rejected["source_unreadable"] += 1; continue
        # weak-proxy boxes must fit the source frame
        maxx = max(x for _, b in rois for x in (b[0] + b[2],))
        maxy = max(b[1] + b[3] for _, b in rois)
        if maxx > pro["width"] + 1 or maxy > pro["height"] + 1:
            rejected["cropRois_outside_source_frame"] += 1
            continue
        fps = robust_fps(r)
        if fps is None:
            rejected["fps_not_recoverable"] += 1; continue
        segs = r.get("segments") or []
        if not segs:
            rejected["no_segments"] += 1; continue
        seg_src = [(s["source_start_sec"], s["source_end_sec"]) for s in segs
                   if s.get("source_start_sec") is not None]

        def in_seg(src_t):
            return any(a - 1e-6 <= src_t <= b + 1e-6 for a, b in seg_src)

        kfs = []
        for k in (r.get("crop_keyframes") or []):
            f, t = k.get("frame"), k.get("time_sec")
            if not isinstance(f, (int, float)) or not isinstance(t, (int, float)):
                continue
            st = t + c["start_sec"]
            kfs.append({"clip_frame": int(round(f)), "clip_time": float(t),
                        "source_time": st, "in_segment": in_seg(st)})
        n_in = sum(1 for k in kfs if k["in_segment"])
        if n_in < MIN_IN_SEGMENT and not seg_src:
            rejected["lt3_in_segment_moments"] += 1; continue
        if n_in < MIN_IN_SEGMENT:
            # allow uniform segment points to make up the difference, but the
            # brief requires >=3 IN-SEGMENT spatial moments, so require it
            rejected["lt3_in_segment_moments"] += 1; continue
        cands.append({**m, "label": r, "fps": fps, "probe": pro, "kfs": kfs,
                      "n_in": n_in, "seg_src": seg_src, "rois": rois,
                      "group_key": m["source_group"],
                      "group_sha": sha256_str(m["source_group"])})

    print(f"candidates passing extra conditions: {len(cands)}")
    print("rejections:", dict(rejected))

    # ---- stratify, sort by sha256(source_group), take first 10 with distinct YT ids ----
    frozen, taken_yt = [], set()
    stratum_report = {}
    for sname, pred in STRATA:
        pool = [c for c in cands if pred(c["free_axis_travel"])]
        pool.sort(key=lambda c: c["group_sha"])
        picked = []
        for c in pool:
            if len(picked) >= PER_STRATUM:
                break
            if c["youtube_id"] in taken_yt:
                continue
            taken_yt.add(c["youtube_id"])
            picked.append(c)
        stratum_report[sname] = {
            "available_candidates": len(pool),
            "selected": len(picked),
            "note": ("threshold fixed by the brief; count is as-found, not backfilled"
                     if len(pool) else
                     "NO candidates in this stratum; recorded as 0 and NOT backfilled"),
        }
        frozen.extend(picked)
        print(f"  {sname:16s} candidates={len(pool):4d} selected={len(picked)}")

    # ---- choose moments per group ----
    frames_dir = R4 / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frozen_frames, gsum = [], []
    for c in frozen:
        r = c["label"]
        c["label"] = None
        c.pop("label", None)
        row = labels[c["row_index"]]
        cclip = row["clip"]
        fps = c["fps"]
        pool = [k for k in c["kfs"] if k["in_segment"]]
        pool.sort(key=lambda k: k["clip_frame"])
        # dedupe by clip frame
        seen, uniq = set(), []
        for k in pool:
            if k["clip_frame"] in seen:
                continue
            seen.add(k["clip_frame"]); uniq.append(k)
        pool = uniq
        if len(pool) >= MAX_MOMENTS:
            picks = [pool[round(i * (len(pool) - 1) / (MAX_MOMENTS - 1))]
                     for i in range(MAX_MOMENTS)]
        else:
            picks = list(pool)
            # top up with uniform points inside segments
            for a, b in c["seg_src"]:
                if len(picks) >= MAX_MOMENTS:
                    break
                for j in range(1, MAX_MOMENTS + 1):
                    if len(picks) >= MAX_MOMENTS:
                        break
                    st = a + (b - a) * j / (MAX_MOMENTS + 1)
                    if any(abs(st - p["source_time"]) < 1e-6 for p in picks):
                        continue
                    picks.append({"clip_frame": int(round((st - cclip["start_sec"]) * fps)),
                                  "clip_time": st - cclip["start_sec"],
                                  "source_time": st, "in_segment": True,
                                  "origin": "uniform_in_segment"})
        seen2, final = set(), []
        for p in picks:
            if p["clip_frame"] in seen2:
                continue
            seen2.add(p["clip_frame"]); final.append(p)
        if len(final) > MAX_MOMENTS:
            final = final[:MAX_MOMENTS]
        if len(final) < MIN_IN_SEGMENT:
            print(f"  !! {c['group_key']} only {len(final)} moments; skipped")
            continue

        gdir = frames_dir / f"g{len(gsum):02d}_{c['youtube_id']}"
        gdir.mkdir(parents=True, exist_ok=True)
        rois = {int(f): b for f, b in c["rois"]}
        roi_frames = sorted(rois)
        gframes = []
        for mi, p in enumerate(final):
            cf = p["clip_frame"]
            # nearest cropRoi frame (weak proxy)
            near = min(roi_frames, key=lambda f: abs(f - cf))
            wb = rois[near]
            out = gdir / f"m{mi}_cf{cf}_sf{int(round(p['source_time']*c['probe']['fps']))}.jpg"
            if not out.exists():
                subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error",
                                "-ss", f"{p['source_time']:.6f}", "-i", c["source_path"],
                                "-frames:v", "1", "-q:v", "2", str(out)],
                               check=True, stdin=subprocess.DEVNULL)
            gframes.append({
                "group_key": c["group_key"], "youtube_id": c["youtube_id"],
                "moment_index": mi,
                "clip_local_frame": cf, "clip_local_time_sec": round(p["clip_time"], 6),
                "source_time_sec": round(p["source_time"], 6),
                "source_frame": int(round(p["source_time"] * c["probe"]["fps"])),
                "clip_fps": fps, "source_fps": c["probe"]["fps"],
                "moment_origin": p.get("origin", "crop_keyframe_in_segment"),
                "weak_proxy_crop_xywh": wb,
                "weak_proxy_from_roi_frame": near,
                "weak_proxy_roi_frame_delta": abs(near - cf),
                "image_path": str(out), "image_sha256": sha256_file(out),
                "image_bytes": out.stat().st_size,
                "WEAK_PROXY": True,
            })
        if not gframes:
            continue
        frozen_frames.extend(gframes)
        gsum.append({
            "group_index": len(gsum), "group_key": c["group_key"],
            "youtube_id": c["youtube_id"], "source_path": c["source_path"],
            "source_probe": c["probe"], "clip_fps": fps,
            "clip_start_sec": cclip["start_sec"], "clip_end_sec": cclip["end_sec"],
            "free_axis": cclip.get("free_axis"),
            "free_axis_travel": cclip.get("free_axis_travel"),
            "targetRatioWH": row.get("targetRatioWH"),
            "quality_status": (row.get("quality") or {}).get("status"),
            "n_in_segment_keyframes": c["n_in"],
            "n_moments": len(gframes),
            "group_sha256": c["group_sha"],
            "label_video_sha256": c.get("label_video_sha256"),
            "segments_source": c["seg_src"],
        })
        print(f"  g{len(gsum)-1:02d} {c['youtube_id']:14s} travel={c['free_axis_travel']:.4f} "
              f"fps={fps:g} moments={len(gframes)}")

    frozen_frames = frozen_frames[:MAX_FRAMES]
    out = {
        "frozen_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
        "frozen_before_any_model_output": True,
        "strata_definition": "clip.free_axis_travel <= 0.05 / (0.05,0.25) / >= 0.25",
        "selection_rule": ("per stratum sort by sha256(provenance.source_group), take first 10 "
                           "with DISTINCT YouTube ids (one source video may appear as several "
                           "window names)"),
        "stratum_counts": stratum_report,
        "max_moments_per_group": MAX_MOMENTS,
        "min_in_segment_moments": MIN_IN_SEGMENT,
        "max_frames": MAX_FRAMES,
        "n_groups": len(gsum),
        "n_frames": len(frozen_frames),
        "rejections": dict(rejected),
        "weak_proxy_note": ("cropRois are Seed-model weak spatial labels -> WEAK_PROXY. They are "
                            "used for EVALUATION ONLY and are never placed into a model prompt."),
        "groups": gsum,
    }
    (R4 / "evidence/frozen_set.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    with (R4 / "evidence/frozen_frames.jsonl").open("w") as f:
        for fr in frozen_frames:
            f.write(json.dumps(fr, ensure_ascii=False) + "\n")

    print(f"\nfrozen groups: {len(gsum)}  frozen frames: {len(frozen_frames)}")
    print("stratum counts:", json.dumps(stratum_report, ensure_ascii=False))
    print("wrote evidence/frozen_set.json, evidence/frozen_frames.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
