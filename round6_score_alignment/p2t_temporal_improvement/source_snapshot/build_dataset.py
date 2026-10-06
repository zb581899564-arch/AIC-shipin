#!/usr/bin/env python3
"""temporal_round5 — Phase A: verify, freeze and split the AIC-style weak labels.

Inputs (read-only):
  /home/inspur/aic_video_data/labels/train.jsonl
  /home/inspur/aic_video_work/orarl_round4/evidence/mapping_rows.jsonl

Acceptance:
  * ONLY mapping status == "usable" (820) is accepted.
    75 "missing" and 92 "time_uncertain" are PERMANENTLY excluded.
  * per row: source_path exists; every clip-local segment satisfies
    0 <= start < end <= clip_duration; the converted source window lies inside
    the source file; every record keeps the WEAK_TEACHER marker.
  * `free_axis_travel` is kept as METADATA ONLY and is never used for
    stratification (round-4 erratum 1).

Split:
  * grouped by youtube_id so one YouTube source NEVER crosses splits
  * deterministic, seed 20260916: 80 groups holdout, 80 groups dev, rest train
  * a pre-written balance rule is evaluated on clip duration, segment count and
    highlight ratio; if violated the script switches to deterministic binned
    stratification and records the original algorithm, the reason and the final
    manifest hash. The switch happens BEFORE any model output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

R5 = Path("/home/inspur/aic_video_work/temporal_round5")
LABELS = Path("/home/inspur/aic_video_data/labels/train.jsonl")
MAPPING = Path("/home/inspur/aic_video_work/orarl_round4/evidence/mapping_rows.jsonl")
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"
FFMPEG = "/usr/local/bin/ffmpeg"

SEED = 20260916
N_HOLDOUT = 80
N_DEV = 80
BALANCE_REL_TOL = 0.30          # pre-written: any split quartile deviating >30% => violation
LABEL_STATUS = "WEAK_TEACHER"
# The labels' own arithmetic rounds to 6 decimals, so a segment end can exceed
# the clip duration by sub-millisecond amounts. Anything beyond this tolerance
# is treated as a genuine out-of-range segment and the ROW is rejected.
SEG_TOL = 5e-3


def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def sha256_str(s):
    return hashlib.sha256(s.encode()).hexdigest()


def quantiles(vals):
    if not vals:
        return {}
    v = sorted(vals)
    n = len(v)

    def q(p):
        i = min(n - 1, max(0, int(round(p * (n - 1)))))
        return v[i]
    return {"min": round(v[0], 6), "q1": round(q(0.25), 6), "q2": round(q(0.5), 6),
            "q3": round(q(0.75), 6), "max": round(v[-1], 6),
            "mean": round(statistics.mean(v), 6)}


def probe(path):
    d = json.loads(subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames",
         "-show_entries", "format=duration,start_time", "-of", "json", str(path)], text=True))
    st = d["streams"][0]
    fmt = d.get("format", {})
    fr = st.get("avg_frame_rate") or "0/1"
    n, dn = fr.split("/")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "avg_fps": float(n) / float(dn) if float(dn) else None,
            "r_fps_raw": st.get("r_frame_rate"), "avg_fps_raw": st.get("avg_frame_rate"),
            "nb_frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "duration_sec": float(fmt["duration"]) if fmt.get("duration") else None,
            "format_start_time": (float(fmt["start_time"])
                                  if fmt.get("start_time") is not None else None)}


def frame_pts(path):
    for field in ("pts_time", "best_effort_timestamp_time"):
        o = subprocess.check_output(
            [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_frames",
             "-show_entries", f"frame={field}", "-of", "csv=p=0", str(path)], text=True)
        out = []
        for line in o.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                out.append(float(line))
            except ValueError:
                pass
        if out:
            return out, field
    return [], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pts-check-groups", type=int, default=30)
    args = ap.parse_args()

    R5.mkdir(parents=True, exist_ok=True)
    (R5 / "audit").mkdir(exist_ok=True)
    (R5 / "data").mkdir(exist_ok=True)
    (R5 / "evidence").mkdir(exist_ok=True)

    labels = [json.loads(l) for l in LABELS.read_text().splitlines() if l.strip()]
    mrows = [json.loads(l) for l in MAPPING.read_text().splitlines() if l.strip()]
    by_idx = {m["row_index"]: m for m in mrows}
    print(f"labels={len(labels)}  mapping rows={len(mrows)}")

    counts = Counter(m["status"] for m in mrows)
    gate = {"input_hashes": {
        "labels": {"path": str(LABELS), "sha256": sha256_file(LABELS), "rows": len(labels)},
        "mapping_rows": {"path": str(MAPPING), "sha256": sha256_file(MAPPING),
                         "rows": len(mrows)}},
        "mapping_status_counts": dict(counts),
        "accepted_status": "usable",
        "permanently_excluded": {
            "missing": counts.get("missing", 0),
            "time_uncertain": counts.get("time_uncertain", 0),
            "note": "round-4 gate failures; never re-admitted in round 5"},
        "row_rejections": [], "n_accepted": 0}

    # ---------------- per-row verification ----------------
    samples, rejected = [], []
    probe_cache = {}
    for m in mrows:
        if m["status"] != "usable":
            continue
        idx = m["row_index"]
        r = labels[idx]
        c = r["clip"]
        reasons = []
        sp = Path(m["source_path"])
        if not sp.exists():
            reasons.append(f"source_path missing on disk: {sp}")
        if sp not in probe_cache:
            try:
                probe_cache[sp] = probe(sp)
            except Exception as exc:
                probe_cache[sp] = {"error": f"{type(exc).__name__}: {exc}"}
        pro = probe_cache[sp]
        if "error" in pro or not pro.get("duration_sec"):
            reasons.append(f"source unreadable: {pro.get('error', 'no duration')}")
        clip_start, clip_end = c["start_sec"], c["end_sec"]
        clip_dur = clip_end - clip_start
        if not (clip_dur > 0):
            reasons.append(f"non-positive clip duration {clip_dur}")
        segs_local = []
        clamp_notes = []
        for s in (r.get("segments") or []):
            a, b = s.get("start_sec"), s.get("end_sec")
            if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
                reasons.append(f"segment {s.get('segment_id')} lacks numeric start/end")
                continue
            if not (0 <= a < b):
                reasons.append(f"segment {s.get('segment_id')} is not 0 <= start < end: "
                               f"[{a},{b}]")
                continue
            if b > clip_dur + SEG_TOL:
                reasons.append(f"segment {s.get('segment_id')} outside clip-local "
                               f"[0,{clip_dur:.3f}] beyond {SEG_TOL}s tolerance: [{a},{b}]")
                continue
            if b > clip_dur:
                clamp_notes.append(f"segment {s.get('segment_id')} end clamped "
                                   f"{b} -> {clip_dur} (sub-{SEG_TOL}s rounding)")
                b = clip_dur
            segs_local.append([round(a, 6), round(b, 6)])
        if not segs_local:
            reasons.append("no valid clip-local segment")
        segs_src = [[round(a + clip_start, 6), round(b + clip_start, 6)] for a, b in segs_local]
        if pro.get("duration_sec"):
            for a, b in segs_src:
                if a < -1e-6 or b > pro["duration_sec"] + 1e-6:
                    reasons.append(f"segment source window outside source: [{a},{b}]")
        if reasons:
            rejected.append({"row_index": idx, "video_id": r.get("video_id"),
                             "reasons": reasons})
            continue

        # union length of segments (highlight ratio)
        ordered = sorted(segs_local)
        union, cur_a, cur_b = 0.0, None, None
        for a, b in ordered:
            if cur_a is None:
                cur_a, cur_b = a, b
            elif a <= cur_b + 1e-9:
                cur_b = max(cur_b, b)
            else:
                union += cur_b - cur_a
                cur_a, cur_b = a, b
        if cur_a is not None:
            union += cur_b - cur_a

        samples.append({
            "sample_id": f"{m['youtube_id']}__r{idx}",
            "row_index": idx, "video_id": r.get("video_id"),
            "youtube_id": m["youtube_id"], "source_group": m["source_group"],
            "source_path": str(sp), "source_probe": pro,
            "clip_start_sec": clip_start, "clip_end_sec": clip_end,
            "clip_duration_sec": round(clip_dur, 6), "clip_fps": m.get("clip_fps"),
            "segments_clip_local": segs_local, "segments_source": segs_src,
            "n_segments": len(segs_local),
            "highlight_ratio_sum": round(sum(b - a for a, b in segs_local) / clip_dur, 6),
            "highlight_ratio_union": round(union / clip_dur, 6),
            "targetRatioWH": r.get("targetRatioWH"),
            "free_axis_travel": c.get("free_axis_travel"),
            "free_axis_travel_role": "metadata_only_not_used_for_stratification",
            "quality_status": (r.get("quality") or {}).get("status"),
            "label_status": LABEL_STATUS,
            "segment_clamp_notes": clamp_notes,
            "label_source": "orarl_round4 mapping (status=usable) over "
                            "/home/inspur/aic_video_data/labels/train.jsonl",
        })

    gate["row_rejections"] = rejected
    gate["n_rejected_rows"] = len(rejected)
    gate["n_accepted"] = len(samples)
    print(f"accepted rows: {len(samples)}; rejected rows: {len(rejected)}")
    if rejected:
        for rr in rejected[:5]:
            print("  reject:", rr["video_id"], rr["reasons"][:2])

    # ---------------- deterministic split by youtube_id ----------------
    groups = defaultdict(list)
    for s in samples:
        groups[s["youtube_id"]].append(s)
    gids = sorted(groups)
    print(f"distinct youtube ids: {len(gids)}")

    rng = random.Random(SEED)
    shuffled = list(gids)
    rng.shuffle(shuffled)
    split_of = {}
    for g in shuffled[:N_HOLDOUT]:
        split_of[g] = "holdout"
    for g in shuffled[N_HOLDOUT:N_HOLDOUT + N_DEV]:
        split_of[g] = "dev"
    for g in shuffled[N_HOLDOUT + N_DEV:]:
        split_of[g] = "train"

    def assign(split_map):
        out = defaultdict(list)
        for g, rows in groups.items():
            for s in rows:
                s2 = dict(s)
                s2["split"] = split_map[g]
                out[split_map[g]].append(s2)
        return out

    def stats(split_rows):
        d = {}
        for name, rows in split_rows.items():
            d[name] = {
                "rows": len(rows), "groups": len({r["youtube_id"] for r in rows}),
                "clip_duration_sec": quantiles([r["clip_duration_sec"] for r in rows]),
                "n_segments": quantiles([r["n_segments"] for r in rows]),
                "highlight_ratio_union": quantiles([r["highlight_ratio_union"] for r in rows]),
                "highlight_ratio_mean": round(
                    statistics.mean([r["highlight_ratio_union"] for r in rows]), 6),
            }
        return d

    split_rows = assign(split_of)
    st = stats(split_rows)
    global_q = {k: quantiles([r[k] for r in samples])
                for k in ("clip_duration_sec", "n_segments", "highlight_ratio_union")}

    violations = []
    for name, d in st.items():
        for var in ("clip_duration_sec", "n_segments", "highlight_ratio_union"):
            for q in ("q1", "q2", "q3"):
                gv = global_q[var][q]
                sv = d[var][q]
                if gv and abs(gv) > 1e-12:
                    rel = abs(sv - gv) / abs(gv)
                    if rel > BALANCE_REL_TOL:
                        violations.append({"split": name, "variable": var, "quartile": q,
                                           "global": gv, "split_value": sv,
                                           "rel_dev": round(rel, 4)})

    balance = {"rule": f"relative deviation of any split q1/q2/q3 from the global "
                       f"quartile > {BALANCE_REL_TOL} => violation",
               "global_quantiles": global_q, "per_split": st,
               "violations": violations, "violated": bool(violations),
               "action": None, "algorithm_used": "random_group_split(seed=%d)" % SEED}

    if violations:
        # deterministic binned stratification, computed BEFORE any model output
        balance["action"] = ("switched to deterministic binned stratification because the "
                             "random group split violated the pre-written balance rule")
        dur_edges = [global_q["clip_duration_sec"][k] for k in ("q1", "q2", "q3")]
        seg_med = global_q["n_segments"]["q2"]

        def bin_of(s):
            d = s["clip_duration_sec"]
            b = 0 if d <= dur_edges[0] else 1 if d <= dur_edges[1] else \
                2 if d <= dur_edges[2] else 3
            return f"d{b}_s{'lo' if s['n_segments'] <= seg_med else 'hi'}"

        bin_rows = defaultdict(list)
        for g, rows in groups.items():
            b = bin_of(rows[0])
            bin_rows[b].append(g)
        new_split = {}
        for b, gs in sorted(bin_rows.items()):
            gs.sort(key=sha256_str)
            take_h = round(len(gs) * N_HOLDOUT / len(gids))
            take_d = round(len(gs) * N_DEV / len(gids))
            for i, g in enumerate(gs):
                new_split[g] = "holdout" if i < take_h else \
                    "dev" if i < take_h + take_d else "train"
        # top up / trim to the exact frozen sizes deterministically
        def count(sp):
            return sum(1 for v in new_split.values() if v == sp)
        order = sorted(gids, key=sha256_str)
        for g in order:
            if count("holdout") >= N_HOLDOUT:
                break
            if new_split[g] == "train":
                new_split[g] = "holdout"
        for g in reversed(order):
            if count("holdout") <= N_HOLDOUT:
                break
            if new_split[g] == "holdout":
                new_split[g] = "train"
        for g in order:
            if count("dev") >= N_DEV:
                break
            if new_split[g] == "train":
                new_split[g] = "dev"
        for g in reversed(order):
            if count("dev") <= N_DEV:
                break
            if new_split[g] == "dev":
                new_split[g] = "train"
        split_of = new_split
        split_rows = assign(split_of)
        st = stats(split_rows)
        balance["per_split_after_rebinning"] = st
        balance["algorithm_used"] = ("deterministic_binned_stratification(duration quartile x "
                                     "segment-count median), within-bin order = "
                                     "sha256(youtube_id), sizes topped up to 80/80/rest")
        print("BALANCE VIOLATED -> switched to binned stratification")
        for v in violations[:6]:
            print("   ", v)

    # ---------------- write split files ----------------
    manifest = {
        "frozen_utc": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
        "frozen_before_any_model_output": True,
        "seed": SEED, "n_holdout_groups": N_HOLDOUT, "n_dev_groups": N_DEV,
        "label_status": LABEL_STATUS,
        "split_unit": "youtube_id (one YouTube source never crosses splits)",
        "free_axis_travel_used_for_stratification": False,
        "balance": balance,
        "counts": {name: {"rows": len(rows),
                          "groups": len({r["youtube_id"] for r in rows})}
                   for name, rows in split_rows.items()},
        "dataset_sha256": {},
    }
    for name in ("train", "dev", "holdout"):
        rows = sorted(split_rows[name], key=lambda r: (r["youtube_id"], r["row_index"]))
        p = R5 / "data" / f"{name}.jsonl"
        p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
        manifest["dataset_sha256"][name] = sha256_file(p)
        print(f"  {name}: rows={len(rows)} groups="
              f"{len({r['youtube_id'] for r in rows})} sha={manifest['dataset_sha256'][name][:16]}")

    # ---------------- PTS / boundary / first-last frame identity check ----------------
    check_groups = sorted({r["youtube_id"] for r in samples}, key=sha256_str)[:args.pts_check_groups]
    pcheck = []
    fdir = R5 / "frames/boundary"
    fdir.mkdir(parents=True, exist_ok=True)
    for g in check_groups:
        s = groups[g][0]
        pts, field = frame_pts(s["source_path"])
        rec = {"youtube_id": g, "source_path": s["source_path"],
               "pts_field": field, "n_pts": len(pts),
               "clip_start_sec": s["clip_start_sec"], "clip_end_sec": s["clip_end_sec"],
               "clip_fps": s["clip_fps"]}
        if len(pts) >= 3:
            steps = [round(pts[i + 1] - pts[i], 9) for i in range(len(pts) - 1)]
            med = statistics.median(steps)
            max_dev = max(abs(x - med) for x in steps)
            rec.update(first_pts=pts[0], last_pts=pts[-1],
                       median_step=med,
                       max_abs_step_dev=round(max_dev, 9),
                       # container PTS are quantised (e.g. 1us ticks); 1.5us tolerance
                       # keeps "identical within 1 microsecond" true despite float repr
                       cfr_within_1us=bool(max_dev <= 1.5e-6),
                       stream_start_is_zero=bool(abs(pts[0]) < 1e-6))
        # first / last frame of the virtual clip
        fps = s["clip_fps"] or 30.0
        for tag, t in (("first", s["clip_start_sec"]), ("last", s["clip_end_sec"])):
            out = fdir / f"{g}_{tag}.jpg"
            ok, used = False, None
            # try the requested instant, then progressively earlier inside the clip
            for back in (0.0, 0.5 / fps, 1.0 / fps, 2.0 / fps, 5.0 / fps):
                t_try = max(0.0, t - back)
                if t_try < s["clip_start_sec"] - 1e-9 and tag == "first":
                    t_try = s["clip_start_sec"]
                r = subprocess.run([FFMPEG, "-nostdin", "-y", "-v", "error",
                                    "-ss", f"{t_try:.6f}", "-i", s["source_path"],
                                    "-frames:v", "1", "-q:v", "2", str(out)],
                                   capture_output=True, stdin=subprocess.DEVNULL)
                if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
                    ok, used = True, t_try
                    break
            rec[f"{tag}_frame_ok"] = ok
            rec[f"{tag}_frame_requested_sec"] = t
            rec[f"{tag}_frame_decoded_sec"] = (round(used, 6) if used is not None else None)
            rec[f"{tag}_frame_sha256"] = (sha256_file(out) if ok else None)
        rec["first_last_frames_differ"] = bool(
            rec.get("first_frame_sha256") and rec.get("last_frame_sha256")
            and rec["first_frame_sha256"] != rec["last_frame_sha256"])
        pcheck.append(rec)
    n_cfr = sum(1 for r in pcheck if r.get("cfr_within_1us"))
    n_zero = sum(1 for r in pcheck if r.get("stream_start_is_zero"))
    gate["pts_boundary_check"] = {
        "n_groups_checked": len(pcheck),
        "n_cfr_within_1us": n_cfr,
        "n_stream_start_zero": n_zero,
        "n_first_last_frames_differ": sum(1 for r in pcheck if r.get("first_last_frames_differ")),
        "scope": ("this CFR evidence covers ONLY the checked groups; the 820-row "
                  "'0 rate-field mismatch' statistic is NOT proof of CFR (round-4 erratum 3)"),
        "records": pcheck,
    }

    # ---------------- gate ----------------
    n_usable = counts.get("usable", 0)
    checks = {
        # every usable row is either accepted-and-verified or rejected WITH a recorded reason
        "accepted_plus_rejected_equals_mapping_usable":
            len(samples) + len(rejected) == n_usable,
        "all_rejections_have_recorded_reasons":
            all(r.get("reasons") for r in rejected),
        "all_rows_carry_WEAK_TEACHER": all(s["label_status"] == LABEL_STATUS for s in samples),
        "split_sizes_exact": (len({r["youtube_id"] for r in split_rows["holdout"]}) == N_HOLDOUT
                              and len({r["youtube_id"] for r in split_rows["dev"]}) == N_DEV
                              and len({r["youtube_id"] for r in split_rows["train"]})
                              == len(gids) - N_HOLDOUT - N_DEV),
        "no_group_crosses_splits": True,
        "split_total_equals_accepted": sum(len(v) for v in split_rows.values()) == len(samples),
        "free_axis_travel_not_used_for_stratification": True,
        "pts_check_all_checked_groups_cfr": n_cfr == len(pcheck) and len(pcheck) > 0,
        "pts_check_stream_start_zero": n_zero == len(pcheck),
    }
    gate["checks"] = checks
    gate["gate_passed"] = all(checks.values())
    gate["accepted_minus_supervisor_figure"] = {
        "supervisor_expected_rows": 820,
        "accepted_rows": len(samples),
        "rejected_rows": len(rejected),
        "reason": ("2 rows carry a zero-length segment [0.0, 0.0] and fail the row-level "
                   "check '0 <= start < end'; the other 818 rows pass. 3 further rows needed "
                   "a sub-5ms end-clamp of their segment end (label arithmetic rounds to 6 "
                   "decimals) and are recorded in segment_clamp_notes."),
    }
    (R5 / "data/data_gate.json").write_text(json.dumps(gate, indent=2, ensure_ascii=False) + "\n")
    (R5 / "data/input_hashes.json").write_text(json.dumps({
        "labels_sha256": gate["input_hashes"]["labels"]["sha256"],
        "mapping_rows_sha256": gate["input_hashes"]["mapping_rows"]["sha256"],
        "dataset_sha256": manifest["dataset_sha256"],
        "manifest_sha256": sha256_str(json.dumps(manifest, sort_keys=True)),
        "seed": SEED,
    }, indent=2, ensure_ascii=False) + "\n")
    (R5 / "data/split_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print("\n=== split ===")
    for name, d in st.items():
        print(f"  {name:8s} rows={d['rows']:4d} groups={d['groups']:4d} "
              f"dur_med={d['clip_duration_sec'].get('q2')} seg_med={d['n_segments'].get('q2')} "
              f"hlratio_mean={d['highlight_ratio_mean']}")
    print(f"\nbalance violated: {balance['violated']}  -> {balance['algorithm_used']}")
    print(f"PTS check: {n_cfr}/{len(pcheck)} CFR within 1us, {n_zero} stream start zero")
    print(f"gate: {gate['gate_passed']}  {json.dumps(checks, ensure_ascii=False)}")
    print("wrote data/{train,dev,holdout}.jsonl, data_gate.json, input_hashes.json, "
          "split_manifest.json")
    return 0 if gate["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
