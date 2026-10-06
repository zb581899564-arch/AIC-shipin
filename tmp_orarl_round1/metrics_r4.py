#!/usr/bin/env python3
"""ROUND 4 — metrics and paired bootstrap for the four crop arms.

All label-derived quantities are named WEAK_PROXY_* and are computed against the
Seed weak spatial labels (`cropRois`), which are WEAK_PROXY, not ground truth.

Rules:
  * invalid outputs score 0 and STAY IN THE DENOMINATOR
  * every group contributes the same number of moments (4)
  * stratified reporting by motion stratum (only the high stratum is populated)
  * paired bootstrap over SOURCE GROUPS for P2-P1 and P3-P1
  * gate criteria applied exactly as written in the brief
"""
from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
ARMS = R4 / "outputs/arms"
BOOT = 10000
SEED = 20260916


def rect(box_xyw, tw, th):
    x, y, w = float(box_xyw[0]), float(box_xyw[1]), float(box_xyw[2])
    h = w * float(th) / float(tw)
    return x, y, w, h


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    u = aw * ah + bw * bh - inter
    return inter / u if u > 1e-12 else 0.0


def load_jsonl(p):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def main():
    frames = load_jsonl(R4 / "evidence/frozen_frames.jsonl")
    frozen = json.loads((R4 / "evidence/frozen_set.json").read_text())
    gmap = {g["group_key"]: g for g in frozen["groups"]}
    p1 = {r["frame_id"]: r for r in load_jsonl(ARMS / "p1_qwen.jsonl")}
    p2 = {r["frame_id"]: r for r in load_jsonl(ARMS / "p2_orarl.jsonl")}
    p3a = {r["frame_id"]: r for r in load_jsonl(ARMS / "p3a_target.jsonl")}
    p3b = {r["frame_id"]: r for r in load_jsonl(ARMS / "p3b_orarl.jsonl")}

    groups = {}
    for fr in frames:
        groups.setdefault(fr["group_key"], []).append(fr)

    per_frame, per_group = [], []
    for gk, frs in groups.items():
        g = gmap[gk]
        W, H = g["source_probe"]["width"], g["source_probe"]["height"]
        tw, th = float(g["targetRatioWH"][0]), float(g["targetRatioWH"][1])
        from_cw = None
        grows = []
        for fr in sorted(frs, key=lambda f: f["moment_index"]):
            fid = f"{fr['group_key']}#m{fr['moment_index']}"
            ref_stored = fr["weak_proxy_crop_xywh"]
            ref = rect(ref_stored, tw, th)
            cw = (p1.get(fid) or p2.get(fid) or {}).get("max_legal_crop_w")
            if cw is None:
                raise SystemExit(f"missing max_legal_crop_w for {fid}")
            # P0: centre of the frame at the max legal crop width
            from_cw = cw
            p0_box = [round(W / 2.0 - cw / 2.0), round(H / 2.0 - (cw * th / tw) / 2.0), cw]
            arms = {
                "P0": {"box": p0_box, "valid": True},
                "P1": {"box": (p1.get(fid) or {}).get("box_xyw"),
                       "valid": bool((p1.get(fid) or {}).get("output_valid"))},
                "P2": {"box": (p2.get(fid) or {}).get("box_xyw"),
                       "valid": bool((p2.get(fid) or {}).get("output_valid"))},
                "P3": {"box": (p3b.get(fid) or {}).get("box_xyw"),
                       "valid": bool((p3a.get(fid) or {}).get("output_valid"))
                                and bool((p3b.get(fid) or {}).get("output_valid"))},
            }
            row = {"frame_id": fid, "group_key": gk, "youtube_id": fr["youtube_id"],
                   "moment_index": fr["moment_index"], "W": W, "H": H,
                   "targetRatioWH": [tw, th], "max_legal_crop_w": cw,
                   "weak_proxy_ref_xywh": ref_stored,
                   "weak_proxy_ref_xyw": [ref_stored[0], ref_stored[1], ref_stored[2]],
                   "ref_h_stored_vs_derived": [ref_stored[3], round(ref[3], 3)]}
            for aname, a in arms.items():
                valid = a["valid"] and a["box"] is not None
                if valid:
                    pr = rect(a["box"], tw, th)
                    row[f"{aname}_valid"] = True
                    row[f"WEAK_PROXY_IoU_{aname}"] = round(iou(pr, ref), 4)
                    pcx, pcy = pr[0] + pr[2] / 2.0, pr[1] + pr[3] / 2.0
                    rcx, rcy = ref[0] + ref[2] / 2.0, ref[1] + ref[3] / 2.0
                    row[f"WEAK_PROXY_hcenter_abs_err_{aname}"] = round(abs(pcx - rcx) / W, 4)
                    row[f"WEAK_PROXY_vcenter_abs_err_{aname}"] = round(abs(pcy - rcy) / H, 4)
                    row[f"center_x_norm_{aname}"] = round(pcx / W, 6)
                    row[f"center_y_norm_{aname}"] = round(pcy / H, 6)
                else:
                    # invalid stays in the denominator with 0 score
                    row[f"{aname}_valid"] = False
                    row[f"WEAK_PROXY_IoU_{aname}"] = 0.0
                    row[f"WEAK_PROXY_hcenter_abs_err_{aname}"] = None
                    row[f"WEAK_PROXY_vcenter_abs_err_{aname}"] = None
                    row[f"center_x_norm_{aname}"] = None
                    row[f"center_y_norm_{aname}"] = None
            per_frame.append(row)
            grows.append(row)

        # group-level aggregates
        grec = {"group_key": gk, "youtube_id": g["youtube_id"],
                "free_axis_travel": g["free_axis_travel"],
                "stratum": ("high_ge_0.25" if g["free_axis_travel"] >= 0.25 else
                            "mid_0.05_0.25" if g["free_axis_travel"] > 0.05 else "low_le_0.05"),
                "n_moments": len(grows)}
        for aname in ("P0", "P1", "P2", "P3"):
            vals = [r[f"WEAK_PROXY_IoU_{aname}"] for r in grows]
            grec[f"WEAK_PROXY_IoU_{aname}_mean"] = round(statistics.mean(vals), 4)
            grec[f"valid_{aname}"] = sum(1 for r in grows if r[f"{aname}_valid"])
            # trajectory variation on the crop centre x
            seq = [r[f"center_x_norm_{aname}"] for r in grows]
            if all(v is not None for v in seq):
                tv = sum(abs(seq[i + 1] - seq[i]) for i in range(len(seq) - 1))
                jit = ([abs(seq[i + 1] - 2 * seq[i] + seq[i - 1])
                        for i in range(1, len(seq) - 1)])
                grec[f"path_total_variation_{aname}"] = round(tv, 6)
                grec[f"second_order_jitter_{aname}"] = (round(statistics.mean(jit), 6)
                                                        if jit else 0.0)
            else:
                grec[f"path_total_variation_{aname}"] = None
                grec[f"second_order_jitter_{aname}"] = None
        for aname in ("P2", "P3"):
            grec[f"delta_vs_P1_{aname}"] = round(
                grec[f"WEAK_PROXY_IoU_{aname}_mean"] - grec["WEAK_PROXY_IoU_P1_mean"], 4)
            grec[f"wins_vs_P1_{aname}"] = bool(
                grec[f"WEAK_PROXY_IoU_{aname}_mean"] > grec["WEAK_PROXY_IoU_P1_mean"] + 1e-9)
        per_group.append(grec)

    # ---------------- aggregates ----------------
    def agg(rows, aname, key="WEAK_PROXY_IoU_"):
        vals = [r[f"{key}{aname}"] for r in rows]
        return {"mean": round(statistics.mean(vals), 4),
                "median": round(statistics.median(vals), 4),
                "min": round(min(vals), 4), "max": round(max(vals), 4)}

    overall = {"n_frames": len(per_frame), "n_groups": len(per_group),
               "by_arm": {a: agg(per_frame, a) for a in ("P0", "P1", "P2", "P3")},
               "valid_rate_by_arm": {
                   a: round(sum(1 for r in per_frame if r[f"{a}_valid"]) / len(per_frame), 4)
                   for a in ("P0", "P1", "P2", "P3")},
               "invalid_kept_in_denominator": True}
    for a in ("P0", "P2", "P3"):
        for k in ("mean", "median"):
            overall[f"{a}_minus_P1_{k}"] = round(
                overall["by_arm"][a][k] - overall["by_arm"]["P1"][k], 4)
    overall["group_win_rate_vs_P1"] = {
        a: round(sum(1 for g in per_group if g[f"wins_vs_P1_{a}"]) / len(per_group), 4)
        for a in ("P2", "P3")}

    # stratified (only the high stratum is populated)
    strata = {}
    for s in ("low_le_0.05", "mid_0.05_0.25", "high_ge_0.25"):
        grp = [g for g in per_group if g["stratum"] == s]
        fr_ids = {g["group_key"] for g in grp}
        rows = [r for r in per_frame if r["group_key"] in fr_ids]
        strata[s] = {"n_groups": len(grp), "n_frames": len(rows),
                     "by_arm": {a: agg(rows, a) for a in ("P0", "P1", "P2", "P3")} if rows else {}}

    # ---------------- paired bootstrap over source groups ----------------
    rng = random.Random(SEED)
    boot = {}
    for a in ("P2", "P3"):
        diffs = [g[f"delta_vs_P1_{a}"] for g in per_group]
        n = len(diffs)
        means = []
        for _ in range(BOOT):
            samp = [diffs[rng.randrange(n)] for _ in range(n)]
            means.append(sum(samp) / n)
        means.sort()
        boot[a] = {
            "n_groups": n, "n_bootstrap": BOOT, "seed": SEED,
            "observed_mean_diff": round(statistics.mean(diffs), 4),
            "ci95_low": round(means[int(0.025 * BOOT)], 4),
            "ci95_high": round(means[int(0.975 * BOOT)], 4),
            "frac_bootstrap_gt_0": round(sum(1 for m in means if m > 0) / BOOT, 4),
            "unit": "source group (paired)",
        }

    # ---------------- gate ----------------
    gate = {}
    for a in ("P2", "P3"):
        gi = per_group
        jit_p1 = [g["second_order_jitter_P1"] for g in gi if g["second_order_jitter_P1"] is not None]
        jit_a = [g[f"second_order_jitter_{a}"] for g in gi if g[f"second_order_jitter_{a}"] is not None]
        mp1 = statistics.mean(jit_p1) if jit_p1 else None
        ma = statistics.mean(jit_a) if jit_a else None
        # P1's crop centre can be exactly constant within a group, making the
        # ratio undefined; in that case require the candidate to also be zero.
        if mp1 is None or ma is None:
            ratio, jitter_ok = None, None
        elif mp1 == 0:
            ratio, jitter_ok = (float("inf") if ma > 0 else 1.0), (ma == 0)
        else:
            ratio, jitter_ok = ma / mp1, (ma / mp1 <= 1.25)
        checks = {
            "valid_output_rate_100pct": overall["valid_rate_by_arm"][a] >= 1.0,
            "iou_mean_gain_ge_0.03": overall[f"{a}_minus_P1_mean"] >= 0.03,
            "median_not_lower": overall[f"{a}_minus_P1_median"] >= 0.0,
            "win_rate_ge_0.60": overall["group_win_rate_vs_P1"][a] >= 0.60,
            "high_motion_not_worse": (strata["high_ge_0.25"]["by_arm"][a]["mean"]
                                      >= strata["high_ge_0.25"]["by_arm"]["P1"]["mean"] - 1e-9)
                                     if strata["high_ge_0.25"]["n_groups"] else None,
            "jitter_le_1.25x_P1": jitter_ok,
        }
        gate[a] = {"checks": checks,
                   "all_pass": all(v for v in checks.values() if v is not None),
                   "jitter_ratio_vs_P1": (round(ratio, 4) if ratio is not None
                                          and ratio != float("inf") else ratio),
                   "mean_second_order_jitter": {"P1": (round(mp1, 6) if mp1 is not None else None),
                                                a: (round(ma, 6) if ma is not None else None)},
                   "jitter_note": ("P1's crop centre is exactly constant within every group, so "
                                   "the 1.25x ratio is undefined; the criterion is then read as "
                                   "'candidate jitter must also be zero'"
                                   if mp1 == 0 else
                                   "ratio computed against P1's mean second-order jitter"),
                   "threshold_note": ("these thresholds only decide whether the route is worth "
                                      "continuing; they do not imply an official score gain")}

    # centre-motion diagnostics (how much each arm's crop centre moves per group)
    centre_motion = {}
    for a in ("P0", "P1", "P2", "P3"):
        xs = [g["path_total_variation_" + a] for g in per_group
              if g.get("path_total_variation_" + a) is not None]
        jj = [g["second_order_jitter_" + a] for g in per_group
              if g.get("second_order_jitter_" + a) is not None]
        centre_motion[a] = {
            "mean_path_total_variation": round(statistics.mean(xs), 6) if xs else None,
            "median_path_total_variation": round(statistics.median(xs), 6) if xs else None,
            "n_groups_with_zero_total_variation": sum(1 for v in xs if v == 0),
            "n_groups": len(xs),
            "mean_second_order_jitter": round(statistics.mean(jj), 6) if jj else None,
        }
    overall["centre_motion_by_arm"] = centre_motion
    overall["P3_minus_P2_mean"] = round(overall["by_arm"]["P3"]["mean"]
                                        - overall["by_arm"]["P2"]["mean"], 4)
    overall["P3_minus_P2_median"] = round(overall["by_arm"]["P3"]["median"]
                                          - overall["by_arm"]["P2"]["median"], 4)

    # ---------------- cost ----------------
    armA = json.loads((ARMS / "arm_a_run.json").read_text()) if (ARMS / "arm_a_run.json").exists() else {}
    armB = json.loads((ARMS / "arm_b_run.json").read_text()) if (ARMS / "arm_b_run.json").exists() else {}
    p3_targets = load_jsonl(ARMS / "p3a_target.jsonl")
    cost = {
        "arm_A": {k: armA.get(k) for k in ("model_load_seconds", "n_p1", "p1_valid",
                                           "n_p3a", "p3a_valid", "peak_memory_mib",
                                           "total_seconds")},
        "arm_B": {k: armB.get(k) for k in ("model_load_seconds", "n_p2", "p2_valid",
                                           "n_p3b", "p3b_valid", "peak_memory_mib",
                                           "total_seconds")},
        "model_calls_total": (armA.get("n_p1", 0) + armA.get("n_p3a", 0)
                              + armB.get("n_p2", 0) + armB.get("n_p3b", 0)),
        "model_calls_P3_extra_vs_P1": len(p3_targets) + armB.get("n_p3b", 0),
        "p3_target_failure_rate": (round(sum(1 for t in p3_targets if not t["output_valid"])
                                         / len(p3_targets), 4) if p3_targets else None),
        "p3_end_to_end_failure_rate": (round(sum(1 for r in per_frame if not r["P3_valid"])
                                             / len(per_frame), 4) if per_frame else None),
        "p3_extra_seconds_per_frame": (round(statistics.mean(
            [t["seconds"] for t in p3_targets]), 2) if p3_targets else None),
    }

    out = {"WEAK_PROXY_note": ("all label-derived numbers use the Seed weak spatial labels "
                              "(cropRois) as a WEAK_PROXY reference; they are NOT official, "
                              "NOT human ground truth and NOT an AIC accuracy"),
           "strata_definition": "clip.free_axis_travel <=0.05 / (0.05,0.25) / >=0.25",
           "overall": overall, "strata": strata, "bootstrap": boot, "gate": gate,
           "cost": cost, "per_group": per_group, "per_frame": per_frame}
    (R4 / "evidence/r4_metrics.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    # ---------------- console ----------------
    print("=========== WEAK_PROXY_IoU by arm (all frames, invalid = 0) ===========")
    for a in ("P0", "P1", "P2", "P3"):
        s = overall["by_arm"][a]
        print(f"  {a}: mean={s['mean']:.4f} median={s['median']:.4f} "
              f"min={s['min']:.4f} max={s['max']:.4f}  valid={overall['valid_rate_by_arm'][a]:.3f}")
    print(f"\n  group win rate vs P1: {overall['group_win_rate_vs_P1']}")
    print(f"  P2-P1 mean={overall['P2_minus_P1_mean']:+.4f} median={overall['P2_minus_P1_median']:+.4f}")
    print(f"  P3-P1 mean={overall['P3_minus_P1_mean']:+.4f} median={overall['P3_minus_P1_median']:+.4f}")
    print("\n=========== stratified ===========")
    for s, v in strata.items():
        if not v["n_groups"]:
            print(f"  {s}: NO groups")
            continue
        print(f"  {s}: groups={v['n_groups']} frames={v['n_frames']} " +
              " ".join(f"{a}={v['by_arm'][a]['mean']:.4f}" for a in ("P0", "P1", "P2", "P3")))
    print("\n=========== paired bootstrap over source groups ===========")
    for a, b in boot.items():
        print(f"  {a}-P1: mean={b['observed_mean_diff']:+.4f} "
              f"95%CI=[{b['ci95_low']:+.4f}, {b['ci95_high']:+.4f}] "
              f"P(>0)={b['frac_bootstrap_gt_0']:.3f}")
    print("\n=========== gate ===========")
    for a, g in gate.items():
        print(f"  {a}: all_pass={g['all_pass']} jitter_ratio={g['jitter_ratio_vs_P1']}")
        for k, v in g["checks"].items():
            print(f"      {'OK ' if v else 'NO '} {k}: {v}")
    print("\n=========== cost ===========")
    print(json.dumps(cost, indent=2, ensure_ascii=False))
    print("\nwrote evidence/r4_metrics.json")


if __name__ == "__main__":
    main()
