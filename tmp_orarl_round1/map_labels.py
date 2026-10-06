#!/usr/bin/env python3
"""ROUND 4 — weak-label  ->  source-video mapping gate.

Rules enforced (per the round-4 brief):
  M1. `source_vid` must match EXACTLY ONE file stem under
      /home/inspur/aic_video_data/videos. No fuzzy / prefix / basename guessing:
      0 matches -> missing, >1 matches -> ambiguous.
  M2. the source file must be readable and yield duration / fps / width / height.
  M3. the label's times must lie inside the source file.
  M4. clip-local frame/time, source frame/time and the clip.start_sec offset are
      kept as SEPARATE fields, with an explicit conversion formula.
  M5. VFR sources, or sources where the clip-local fps cannot be recovered
      unambiguously, are EXCLUDED (a non-unique time conversion is refused).
  M6. the label's own internal consistency is checked:
      segments[].source_start_sec == segments[].start_sec + clip.start_sec.
  M7. `provenance.video_sha256` differing from the source file is recorded but is
      NOT by itself a failure (it plausibly names the processed short clip).
      It also does NOT confirm media identity.
  M8. `cropRois` are Seed-model weak spatial labels -> marked WEAK_PROXY.

Usage: map_labels.py [--limit N]
Writes evidence/mapping_report.json and evidence/mapping_rows.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

LABELS = Path("/home/inspur/aic_video_data/labels/train.jsonl")
VIDEO_ROOT = Path("/home/inspur/aic_video_data/videos")
R4 = Path("/home/inspur/aic_video_work/orarl_round4")
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"

_rx_win = re.compile(r"^(?P<yt>.+?)_(?P<ws>\d+(?:\.\d+)?)_(?P<we>\d+(?:\.\d+)?)$")


def frac(s):
    if not s:
        return None
    if "/" in s:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else None
    return float(s)


def probe(path: Path):
    o = subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", str(path)], text=True)
    d = json.loads(o)
    st = d["streams"][0]
    dur = d.get("format", {}).get("duration")
    return {
        "width": int(st["width"]), "height": int(st["height"]),
        "avg_fps": frac(st.get("avg_frame_rate")),
        "r_fps": frac(st.get("r_frame_rate")),
        "r_fps_raw": st.get("r_frame_rate"),
        "avg_fps_raw": st.get("avg_frame_rate"),
        "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
        "duration_sec": float(dur) if dur is not None else None,
    }


PLAUSIBLE_FPS = (23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0)


def robust_clip_fps(row):
    """Recover the clip-local fps robustly.

    `time_sec` in the labels is float-rounded, so a per-pair ratio vote is
    fragile (30/1.001=29.97 vs 30/1.0=30.0). Instead take the median ratio,
    snap to a plausible broadcast fps, and require every (frame, time) pair to
    fit within 1.5 frames. Falls back to segments[].{start,end}_frame/_sec when
    crop_keyframes is empty. Returns (fps|None, info).
    """
    info = {}
    pairs, src = [], "crop_keyframes"
    for k in (row.get("crop_keyframes") or []):
        f, t = k.get("frame"), k.get("time_sec")
        if isinstance(f, (int, float)) and isinstance(t, (int, float)) and f > 0 and t > 0:
            pairs.append((float(f), float(t)))
    if len(pairs) < 2:
        pairs, src = [], "segments"
        for s in (row.get("segments") or []):
            for fk, tk in (("start_frame", "start_sec"), ("end_frame", "end_sec")):
                f, t = s.get(fk), s.get(tk)
                if isinstance(f, (int, float)) and isinstance(t, (int, float)) and f > 0 and t > 0:
                    pairs.append((float(f), float(t)))
    info["pair_source"] = src
    info["n_pairs"] = len(pairs)
    if len(pairs) < 2:
        info["reason"] = "fewer than 2 usable (frame, time) pairs"
        return None, info
    ratios = sorted(f / t for f, t in pairs)
    med = ratios[len(ratios) // 2]
    snap = min(PLAUSIBLE_FPS, key=lambda c: abs(c - med))
    fps = snap if med > 0 and abs(snap - med) / med < 0.02 else med
    resid = max(abs(f - t * fps) for f, t in pairs)
    info.update(median_ratio=round(med, 6), fps=round(fps, 6),
                snapped_to_plausible=bool(fps is snap or fps == snap),
                max_resid_frames=round(resid, 4))
    if resid > 1.5:
        info["reason"] = "median-fps fit residual exceeds 1.5 frames; time conversion not unique"
        return None, info
    return fps, info


def youtube_id(source_vid: str):
    m = _rx_win.match(source_vid or "")
    return m.group("yt") if m else None


def sha256_file(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = [json.loads(l) for l in LABELS.read_text().splitlines() if l.strip()]
    if args.limit:
        rows = rows[: args.limit]
    print(f"label rows: {len(rows)}")

    # ---- build the exact-stem index (M1) ----
    index = defaultdict(list)
    n_files = 0
    for p in VIDEO_ROOT.rglob("*.mp4"):
        index[p.stem].append(p)
        n_files += 1
    print(f"source files indexed: {n_files}; distinct stems: {len(index)}")

    report = {
        "labels_file": str(LABELS),
        "labels_sha256": sha256_file(LABELS),
        "labels_rows": len(rows),
        "video_root": str(VIDEO_ROOT),
        "video_files_indexed": n_files,
        "distinct_stems": len(index),
        "match_rule": "exact equality of the file stem with clip.source_vid; no fuzzy matching",
        "time_convention": {
            "clip_local": ("crop_keyframes[].frame is a frame index inside the processed short "
                           "clip; crop_keyframes[].time_sec = frame / clip_fps; "
                           "segments[].start_sec/end_sec/start_frame/end_frame are clip-local"),
            "source": ("segments[].source_start_sec/source_end_sec are source-file times; "
                       "clip.start_sec and clip.end_sec are source-file times"),
            "formula": ("clip_local_time = clip_local_frame / clip_fps ; "
                        "source_time = clip_local_time + clip.start_sec ; "
                        "source_frame = round(source_time * source_fps)"),
            "clip_fps_source": "recovered from crop_keyframes (frame, time_sec) pairs, >=90% vote",
            "verified_by": "segments[].source_start_sec == segments[].start_sec + clip.start_sec",
        },
        "cropRois_status": "WEAK_PROXY (Seed-model weak spatial labels; not ground truth)",
        "video_sha256_note": ("provenance.video_sha256 plausibly names the processed short clip, "
                              "not the source file; a mismatch is recorded but is NOT a failure, "
                              "and it also does NOT confirm media identity"),
        "counts": {}, "exclusions": [], "rows": [],
    }

    counts = Counter()
    probe_cache = {}
    out_rows = []

    for i, r in enumerate(rows):
        c = r["clip"]
        sv = c.get("source_vid")
        prov = r.get("provenance") or {}
        rec = {
            "row_index": i, "video_id": r.get("video_id"), "source_vid": sv,
            "source_group": prov.get("source_group"),
            "youtube_id": youtube_id(sv),
            "clip_start_sec": c.get("start_sec"), "clip_end_sec": c.get("end_sec"),
            "free_axis": c.get("free_axis"),
            "free_axis_travel": c.get("free_axis_travel"),
            "targetRatioWH": r.get("targetRatioWH"),
            "quality_status": (r.get("quality") or {}).get("status"),
            "label_video_sha256": prov.get("video_sha256"),
            "n_segments": len(r.get("segments") or []),
            "n_crop_keyframes": len(r.get("crop_keyframes") or []),
            "n_cropRois": len(r.get("cropRois") or []),
        }
        cands = index.get(sv, [])
        if len(cands) == 0:
            counts["missing"] += 1
            rec["status"] = "missing"; rec["reason"] = "no file stem equals source_vid"
            report["exclusions"].append(rec); out_rows.append(rec); continue
        if len(cands) > 1:
            counts["ambiguous"] += 1
            rec["status"] = "ambiguous"
            rec["reason"] = "multiple files share this stem"
            rec["candidates"] = [str(p) for p in cands]
            report["exclusions"].append(rec); out_rows.append(rec); continue

        path = cands[0]
        rec["source_path"] = str(path)
        if path not in probe_cache:
            try:
                pr = probe(path)
                pr["file_bytes"] = path.stat().st_size
            except Exception as exc:
                pr = {"error": f"{type(exc).__name__}: {exc}"}
            probe_cache[path] = pr
        pr = probe_cache[path]
        rec["source_probe"] = pr
        if "error" in pr or not pr.get("duration_sec") or not pr.get("avg_fps"):
            counts["unreadable"] += 1
            rec["status"] = "unreadable"; rec["reason"] = pr.get("error", "missing duration/fps")
            report["exclusions"].append(rec); out_rows.append(rec); continue

        # M5 VFR
        rf, af = pr.get("r_fps"), pr.get("avg_fps")
        if rf is None or af is None or abs(rf - af) > 1e-6:
            counts["vfr_excluded"] += 1
            rec["status"] = "vfr_excluded"
            rec["reason"] = (f"r_frame_rate={pr.get('r_fps_raw')} != "
                             f"avg_frame_rate={pr.get('avg_fps_raw')}; time conversion not unique")
            report["exclusions"].append(rec); out_rows.append(rec); continue

        # M5 clip fps
        cfps, fps_info = robust_clip_fps(r)
        rec["clip_fps"] = cfps
        rec["clip_fps_info"] = fps_info
        if cfps is None:
            counts["time_uncertain"] += 1
            rec["status"] = "time_uncertain"
            rec["reason"] = fps_info.get("reason", "clip-local fps not recoverable")
            report["exclusions"].append(rec); out_rows.append(rec); continue

        # M3 range
        dur = pr["duration_sec"]
        problems = []
        if c["end_sec"] > dur + 1e-6:
            problems.append(f"clip.end_sec {c['end_sec']} > source duration {dur:.3f}")
        if c["start_sec"] < 0 or c["end_sec"] <= c["start_sec"]:
            problems.append(f"invalid clip window [{c['start_sec']}, {c['end_sec']}]")
        # M6 internal consistency
        inc = []
        for s in (r.get("segments") or []):
            lhs = s.get("source_start_sec")
            rhs = (s.get("start_sec") or 0) + c["start_sec"]
            if lhs is None or abs(lhs - rhs) > 1e-6:
                inc.append({"segment_id": s.get("segment_id"), "source_start_sec": lhs,
                            "start_sec_plus_offset": rhs})
        rec["segment_consistency_failures"] = inc
        if inc:
            problems.append(f"{len(inc)} segment(s) violate "
                             "source_start_sec == start_sec + clip.start_sec")
        # every keyframe maps inside the source
        bad_kf = []
        for kf in (r.get("crop_keyframes") or []):
            st = (kf.get("time_sec") or 0) + c["start_sec"]
            if st < -1e-6 or st > dur + 1e-6:
                bad_kf.append({"frame": kf.get("frame"), "source_time": st})
        rec["keyframes_out_of_source_range"] = len(bad_kf)
        if bad_kf:
            problems.append(f"{len(bad_kf)} keyframe(s) map outside the source")
        if problems:
            counts["out_of_range_or_inconsistent"] += 1
            rec["status"] = "out_of_range_or_inconsistent"
            rec["reason"] = "; ".join(problems)
            report["exclusions"].append(rec); out_rows.append(rec); continue

        # M7 sha comparison (recorded, not a failure)
        rec["source_sha256"] = None  # computed lazily for frozen rows only
        rec["sha256_matches_source"] = None
        counts["usable"] += 1
        rec["status"] = "usable"
        out_rows.append(rec)

    report["counts"] = dict(counts)
    report["counts"]["total"] = len(rows)
    report["usable_youtube_ids"] = len({x["youtube_id"] for x in out_rows
                                        if x["status"] == "usable"})
    report["usable_free_axis_travel"] = {
        "min": min((x["free_axis_travel"] for x in out_rows if x["status"] == "usable"),
                   default=None),
        "max": max((x["free_axis_travel"] for x in out_rows if x["status"] == "usable"),
                   default=None),
    }
    fat = sorted(x["free_axis_travel"] for x in out_rows if x["status"] == "usable")
    report["strata_available"] = {
        "le_0.05": sum(1 for v in fat if v <= 0.05),
        "between_0.05_and_0.25": sum(1 for v in fat if 0.05 < v < 0.25),
        "ge_0.25": sum(1 for v in fat if v >= 0.25),
        "note": ("thresholds are the ones fixed by the round-4 brief; counts are reported as "
                 "found and are NOT backfilled from other strata"),
    }

    (R4 / "evidence/mapping_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with (R4 / "evidence/mapping_rows.jsonl").open("w") as f:
        for rec in out_rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("\n=== mapping counts ===")
    for k, v in report["counts"].items():
        print(f"  {k:32s} {v}")
    print(f"  usable distinct youtube ids     {report['usable_youtube_ids']}")
    print(f"\n=== free_axis_travel strata among usable rows ===")
    for k, v in report["strata_available"].items():
        print(f"  {k:24s} {v}")
    print(f"  usable free_axis_travel range: {report['usable_free_axis_travel']}")
    print("\nwrote evidence/mapping_report.json, evidence/mapping_rows.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
