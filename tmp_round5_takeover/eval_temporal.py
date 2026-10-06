#!/usr/bin/env python3
"""temporal_round5 — WEAK_TEACHER temporal metrics, stratification, bootstrap.

Every label-derived number is named WEAK_TEACHER temporal F1. It is a weak-label
internal metric used ONLY to select a candidate; it is NOT an AIC official score.

Rules:
  * invalid / empty predictions score 0 and STAY IN THE DENOMINATOR
  * union-based interval precision / recall / F1 against the weak label segments
  * clip-duration quartile stratification
  * paired bootstrap over youtube_id (the split unit)
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

R5 = Path("/home/inspur/aic_video_work/temporal_round5")
sys.path.insert(0, str(R5 / "scripts"))
import temporal_common as tc  # noqa: E402

SEED = 20260916


def load(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def summarize(rows):
    n = len(rows)
    if not n:
        return {}
    return {
        "n_rows": n,
        "valid_rate": round(sum(1 for r in rows if r["output_valid"]) / n, 4),
        "empty_rate": round(sum(1 for r in rows if r["empty_prediction"]) / n, 4),
        "WEAK_TEACHER_temporal_mean_f1": round(sum(r["metrics"]["f1"] for r in rows) / n, 6),
        "WEAK_TEACHER_temporal_median_f1": round(
            statistics.median([r["metrics"]["f1"] for r in rows]), 6),
        "mean_precision": round(sum(r["metrics"]["precision"] for r in rows) / n, 6),
        "mean_recall": round(sum(r["metrics"]["recall"] for r in rows) / n, 6),
        "mean_pred_duration_ratio": round(sum(r["pred_duration_ratio"] for r in rows) / n, 6),
    }


def quartile_edges(vals):
    v = sorted(vals)
    n = len(v)

    def q(p):
        return v[min(n - 1, max(0, int(round(p * (n - 1)))))]
    return [q(0.25), q(0.5), q(0.75)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--t0", default=str(R5 / "outputs/T0_BASE_dev.json"))
    ap.add_argument("--t1", default=str(R5 / "outputs/T1_QVH_LORA_dev.json"))
    ap.add_argument("--t2", default=str(R5 / "outputs/T2_ORARL_TEMPORAL_dev.json"))
    ap.add_argument("--cand", default="", help="selected-arm output to compare against T1")
    ap.add_argument("--out", default=str(R5 / "evidence/phase_b_metrics.json"))
    ap.add_argument("--bootstrap", type=int, default=10000)
    args = ap.parse_args()

    arms = {}
    for name, p in (("T0_BASE", args.t0), ("T1_QVH_LORA", args.t1),
                    ("T2_ORARL_TEMPORAL", args.t2)):
        d = load(p)
        if d:
            arms[name] = d
    if args.cand:
        d = load(args.cand)
        if d:
            arms[d.get("arm", "CAND")] = d
    if not arms:
        print("no arm outputs found")
        return 2

    # index by sample_id
    idx = {name: {r["sample_id"]: r for r in d["rows"]} for name, d in arms.items()}
    base = "T1_QVH_LORA"
    keys = sorted(set.intersection(*[set(v) for v in idx.values()])) if idx else []
    print(f"arms={list(arms)} common_rows={len(keys)}")

    out = {"split": args.split, "common_rows": len(keys),
           "metric_name": "WEAK_TEACHER temporal F1 (union intervals)",
           "note": ("weak-label internal metric for candidate selection only; NOT an AIC "
                    "official score"),
           "invalid_outputs_kept_in_denominator": True,
           "arms": {}, "pairwise_vs_T1": {}, "stratified_by_clip_duration": {}}

    for name, d in arms.items():
        rows = [idx[name][k] for k in keys]
        out["arms"][name] = summarize(rows)
        out["arms"][name]["model"] = d.get("model")
        out["arms"][name]["adapter"] = d.get("adapter")
        out["arms"][name]["summary_from_run"] = d.get("summary")

    # duration quartiles from the weak labels
    durs = {k: idx[base][k]["clip_duration_sec"] for k in keys}
    e1, e2, e3 = quartile_edges(list(durs.values()))

    def qname(v):
        return "Q1" if v <= e1 else "Q2" if v <= e2 else "Q3" if v <= e3 else "Q4"

    strata = defaultdict(list)
    for k in keys:
        strata[qname(durs[k])].append(k)
    for s in sorted(strata):
        blk = {"n_rows": len(strata[s]), "arms": {}}
        for name in arms:
            rows = [idx[name][k] for k in strata[s]]
            blk["arms"][name] = {"mean_f1": round(
                sum(r["metrics"]["f1"] for r in rows) / len(rows), 6),
                "valid_rate": round(sum(1 for r in rows if r["output_valid"]) / len(rows), 4)}
        if base in arms:
            for name in arms:
                if name == base:
                    continue
                blk["arms"][name]["delta_vs_T1"] = round(
                    blk["arms"][name]["mean_f1"] - blk["arms"][base]["mean_f1"], 6)
        out["stratified_by_clip_duration"][s] = blk

    # paired bootstrap over youtube_id
    by_group = defaultdict(list)
    for k in keys:
        by_group[idx[base][k]["youtube_id"]].append(k)
    groups = sorted(by_group)
    rng = random.Random(SEED)
    for name in arms:
        if name == base:
            continue
        # per-group mean F1 difference
        gdiff = []
        for g in groups:
            ks = by_group[g]
            a = sum(idx[name][k]["metrics"]["f1"] for k in ks) / len(ks)
            b = sum(idx[base][k]["metrics"]["f1"] for k in ks) / len(ks)
            gdiff.append(a - b)
        n = len(gdiff)
        boot = []
        for _ in range(args.bootstrap):
            boot.append(sum(gdiff[rng.randrange(n)] for _ in range(n)) / n)
        boot.sort()
        out["pairwise_vs_T1"][name] = {
            "unit": "youtube_id (paired)",
            "n_groups": n, "n_bootstrap": args.bootstrap, "seed": SEED,
            "observed_mean_diff": round(statistics.mean(gdiff), 6),
            "ci95_low": round(boot[int(0.025 * args.bootstrap)], 6),
            "ci95_high": round(boot[int(0.975 * args.bootstrap)], 6),
            "frac_gt_0": round(sum(1 for x in boot if x > 0) / args.bootstrap, 4),
            "n_groups_positive": sum(1 for x in gdiff if x > 0),
            "group_win_rate": round(sum(1 for x in gdiff if x > 0) / n, 4),
        }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print(f"\n=== WEAK_TEACHER temporal F1 by arm ({args.split}) ===")
    for name, s in out["arms"].items():
        print(f"  {name:20s} F1={s['WEAK_TEACHER_temporal_mean_f1']:.4f} "
              f"med={s['WEAK_TEACHER_temporal_median_f1']:.4f} P={s['mean_precision']:.4f} "
              f"R={s['mean_recall']:.4f} valid={s['valid_rate']} empty={s['empty_rate']} "
              f"durratio={s['mean_pred_duration_ratio']}")
    print("\n=== stratified by clip duration ===")
    for s, b in out["stratified_by_clip_duration"].items():
        parts = " ".join(f"{n}={b['arms'][n]['mean_f1']:.4f}" for n in arms)
        print(f"  {s} n={b['n_rows']:3d}  {parts}")
    print("\n=== paired bootstrap vs T1 ===")
    for n, b in out["pairwise_vs_T1"].items():
        print(f"  {n:20s} mean={b['observed_mean_diff']:+.4f} "
              f"95%CI=[{b['ci95_low']:+.4f},{b['ci95_high']:+.4f}] "
              f"winrate={b['group_win_rate']}")
    print("\nwrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
