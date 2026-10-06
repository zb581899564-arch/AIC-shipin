#!/usr/bin/env python3
"""ROUND 3 — metrics for the S0 / S1 / S2 comparison.

Rules enforced here:
  * INVALID outputs stay in the denominator. Nothing is silently dropped.
  * The initialisation frame is reported separately; the headline S1-vs-S0
    comparison EXCLUDES it.
  * S1 (tracking) key->time mapping is NOT assumed. Because the processor's
    real time labels are 16 patch-midpoints ~2.07 s apart while the requested
    keys are 1..32 at 1 s (see ERRATA 1), the primary S1 metric is
    NOT_COMPUTABLE; three candidate mappings are reported instead, and only a
    conclusion that holds under ALL of them is called robust.
  * predicted boxes are NOT AIC crop boxes. No crop candidate is produced.
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

R3 = Path("/home/inspur/aic_video_work/orarl_round3")


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    aa = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    ab = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    u = aa + ab - inter
    return inter / u if u > 1e-12 else 0.0


def center(b):
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)


def center_err(a, b):
    """centre distance in norm1000 units, normalised by the diagonal 1414.2."""
    ca, cb = center(a), center(b)
    return math.hypot(ca[0] - cb[0], ca[1] - cb[1]) / math.hypot(1000, 1000)


def area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def area_ratio(pred, gt):
    g = area(gt)
    return (area(pred) / g) if g > 1e-9 else None


# S1 key -> frame-index mappings for a 10 fps synthetic clip
MAPPINGS = {
    "M1_bin_start": lambda N: 10 * (N - 1),
    "M2_bin_mid": lambda N: 10 * (N - 1) + 5,
    "M3_bin_end": lambda N: 10 * N - 1,
}


def load(rid):
    p = R3 / f"outputs/{rid}/run_status.json"
    return json.loads(p.read_text()) if p.exists() else None


def main():
    s2 = load("r3s2")
    s1 = load("r3s1")
    s0 = json.loads((R3 / "evidence/s0_baseline.json").read_text())
    syn = json.loads((R3 / "evidence/synthetic_manifest.json").read_text())
    ref = json.loads((R3 / "evidence/refcoco_frozen.json").read_text())
    refmap = {s["sample_id"]: s for s in ref["samples"]}

    out = {
        "invalid_outputs_kept_in_denominator": True,
        "init_frame_reported_separately": True,
        "predicted_boxes_are_not_aic_crop_boxes": True,
        "s2": {}, "s1": {}, "s0": {},
    }

    # ================= S2 metrics =================
    # Ground truth is read from the FROZEN case files / manifests, not from the
    # run record (orarl_verify.py's per-case record does not carry custom fields).
    case_gt = {}
    for line in (R3 / "cases/cases_s2.jsonl").read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            case_gt[d["case_id"]] = d.get("gt_box_norm1000")

    cases = (s2 or {}).get("cases", [])
    groups = {"synthetic_keyframe": [], "public_refcoco": []}
    for c in cases:
        cond = c["condition"]
        key = "public_refcoco" if cond == "S2_public_refcoco" else "synthetic_keyframe"
        gt = case_gt.get(c["case_id"])
        preds = (c.get("parsed") or {}).get("boxes_norm1000")
        rec = {"case_id": c["case_id"], "sample_id": c["sample_id"],
               "protocol_complete": c["protocol_complete"],
               "task_success": c["task_success"],
               "gt_box": gt, "n_pred_boxes": len(preds) if preds else 0,
               "pred_boxes": preds,
               "raw_output": c.get("raw_output")}
        if preds and gt:
            p = preds[0]
            rec.update(pred_box=p, iou=round(iou(p, gt), 4),
                       center_err=round(center_err(p, gt), 4),
                       area_ratio=(round(area_ratio(p, gt), 3)
                                   if area_ratio(p, gt) is not None else None))
        else:
            rec.update(pred_box=None, iou=None, center_err=None, area_ratio=None,
                       invalid_reason=("no usable box" if not preds else "no gt"))
        groups[key].append(rec)

    for key, rows in groups.items():
        n = len(rows)                       # denominator includes failures
        n_valid = sum(1 for r in rows if r["iou"] is not None)
        ious = [r["iou"] for r in rows if r["iou"] is not None]
        ces = [r["center_err"] for r in rows if r["center_err"] is not None]
        ars = [r["area_ratio"] for r in rows if r["area_ratio"] is not None]
        out["s2"][key] = {
            "n_requested": n, "n_with_usable_box": n_valid,
            "valid_output_ratio": round(n_valid / n, 4) if n else None,
            "n_invalid_kept_in_denominator": n - n_valid,
            "iou_mean": round(statistics.mean(ious), 4) if ious else None,
            "iou_median": round(statistics.median(ious), 4) if ious else None,
            "iou_min": round(min(ious), 4) if ious else None,
            "iou_max": round(max(ious), 4) if ious else None,
            "iou_ge_0.5": sum(1 for v in ious if v >= 0.5),
            "iou_ge_0.25": sum(1 for v in ious if v >= 0.25),
            "center_err_mean": round(statistics.mean(ces), 4) if ces else None,
            "area_ratio_median": round(statistics.median(ars), 3) if ars else None,
            "per_case": rows,
        }

    # ================= S0 + S1 comparison =================
    for name, info in syn["clips"].items():
        gt = json.loads(Path(info["gt_file"]).read_text())
        gtf = gt["gt_box_norm1000_per_frame"]
        first = gt["gt_first_frame_norm1000"]
        # S0: first-frame box held constant, evaluated at the SAME points as S1
        s0_rows = {}
        for mname, fn in MAPPINGS.items():
            rows = []
            for N in range(1, 33):
                idx = min(max(fn(N), 0), len(gtf) - 1)
                rows.append({"N": N, "frame_index": idx, "t_sec": round(idx / 10.0, 3),
                             "iou": round(iou(first, gtf[idx]), 4),
                             "center_err": round(center_err(first, gtf[idx]), 4),
                             "area_ratio": round(area_ratio(first, gtf[idx]), 3)})
            ex = [r for r in rows if r["N"] != 1]
            s0_rows[mname] = {
                "per_slot": rows,
                "init_slot_iou": rows[0]["iou"],
                "mean_iou_excl_init": round(statistics.mean([r["iou"] for r in ex]), 4),
                "mean_iou_incl_init": round(statistics.mean([r["iou"] for r in rows]), 4),
            }
        out["s0"][name] = {"constant_box": first, "mappings": s0_rows}

    for c in (s1 or {}).get("cases", []):
        sid = c["sample_id"]
        gt = json.loads(Path(syn["clips"][sid]["gt_file"]).read_text())
        gtf = gt["gt_box_norm1000_per_frame"]
        boxes = {int(k): v for k, v in ((c.get("parsed") or {})
                                        .get("boxes_norm1000") or {}).items()}
        rec = {"case_id": c["case_id"], "protocol_complete": c["protocol_complete"],
               "task_success": c["task_success"],
               "n_keys_returned": len(boxes), "anchor": c.get("init_box_norm1000"),
               "anchor_source": c.get("init_box_source"),
               "raw_output": c.get("raw_output"),
               "mappings": {}}
        for mname, fn in MAPPINGS.items():
            rows = []
            for N in range(1, 33):
                idx = min(max(fn(N), 0), len(gtf) - 1)
                p = boxes.get(N)
                rows.append({"N": N, "frame_index": idx, "t_sec": round(idx / 10.0, 3),
                             "has_pred": p is not None,
                             "iou": (round(iou(p, gtf[idx]), 4) if p else 0.0),
                             "center_err": (round(center_err(p, gtf[idx]), 4) if p else None),
                             "area_ratio": (round(area_ratio(p, gtf[idx]), 3) if p else None)})
            ex = [r for r in rows if r["N"] != 1]
            rec["mappings"][mname] = {
                "per_slot": rows,
                "init_slot_iou": rows[0]["iou"],
                "mean_iou_excl_init": round(statistics.mean([r["iou"] for r in ex]), 4),
                "mean_iou_incl_init": round(statistics.mean([r["iou"] for r in rows]), 4),
            }
        rec["PRIMARY_METRIC"] = "NOT_COMPUTABLE"
        rec["primary_reason"] = (
            "The processor's real time labels are 16 patch-midpoint values ~2.07 s apart "
            "(ERRATA 1), while the output keys are requested as 1..32 at one per second. The "
            "key->real-second correspondence therefore cannot be established from the model's "
            "input. Three candidate mappings are reported instead; only a conclusion that holds "
            "under all three may be used.")
        out["s1"][sid] = rec

    # robust comparison S1 vs S0
    cmp_rows = []
    for sid, r in out["s1"].items():
        row = {"sample_id": sid, "init_slot_iou": r["mappings"]["M1_bin_start"]["init_slot_iou"],
               "anchor_equals_gt_first": r["anchor"] ==
               json.loads(Path(syn["clips"][sid]["gt_file"]).read_text())["gt_first_frame_norm1000"]}
        robust_never_better = True
        for m in MAPPINGS:
            s1v = r["mappings"][m]["mean_iou_excl_init"]
            s0v = out["s0"][sid]["mappings"][m]["mean_iou_excl_init"]
            row[f"S1_{m}"] = s1v
            row[f"S0_{m}"] = s0v
            row[f"S1_minus_S0_{m}"] = round(s1v - s0v, 4)
            if s1v > s0v + 1e-9:
                robust_never_better = False
        row["S1_never_exceeds_S0_under_ANY_mapping"] = robust_never_better
        row["S1_worse_or_equal_under_all_mappings"] = all(
            row[f"S1_minus_S0_{m}"] <= 1e-9 for m in MAPPINGS)
        cmp_rows.append(row)
    out["s1_vs_s0"] = cmp_rows

    # ============ MATCHED evaluation points: S0 vs S1 vs S2 ============
    # S0/S1 were scored over all 32 one-second slots, S2 only at the 8 fixed key
    # frames. To compare fairly, rescore all three at exactly the key-frame
    # instants. Key frames are t = 1,5,...,29 s -> frame 10,50,...,290; under
    # mapping M1 (key N <-> t = N-1) that slot is N = t+1, so N = 2,6,...,30.
    # None of these is the initialisation slot (N=1, t=0), so the initialisation
    # frame is excluded by construction.
    KEYF = [10, 50, 90, 130, 170, 210, 250, 290]
    s2map = {c["case_id"]: c for c in (s2 or {}).get("cases", [])}
    matched = []
    for sid in syn["clips"]:
        gt = json.loads(Path(syn["clips"][sid]["gt_file"]).read_text())
        gtf = gt["gt_box_norm1000_per_frame"]
        anchor = gt["gt_first_frame_norm1000"]
        s1c = next((c for c in (s1 or {}).get("cases", []) if c["sample_id"] == sid), None)
        s1boxes = {int(k): v for k, v in (((s1c or {}).get("parsed") or {})
                                          .get("boxes_norm1000") or {}).items()}
        rows = []
        for kf in KEYF:
            N = kf // 10 + 1
            cid = f"s2_{sid}_n{kf:03d}"
            s2c = s2map.get(cid)
            s2pred = ((s2c or {}).get("parsed") or {}).get("boxes_norm1000")
            rows.append({
                "frame_index": kf, "t_sec": round(kf / 10.0, 1), "slot_N": N,
                "S0_iou": round(iou(anchor, gtf[kf]), 4),
                "S1_iou": (round(iou(s1boxes[N], gtf[kf]), 4) if N in s1boxes else None),
                "S2_iou": (round(iou(s2pred[0], gtf[kf]), 4) if s2pred else None),
            })
        agg = {k: (round(statistics.mean([r[k] for r in rows if r[k] is not None]), 4)
                   if any(r[k] is not None for r in rows) else None)
               for k in ("S0_iou", "S1_iou", "S2_iou")}
        agg["n_points"] = len(rows)
        agg["n_s1_available"] = sum(1 for r in rows if r["S1_iou"] is not None)
        agg["n_s2_available"] = sum(1 for r in rows if r["S2_iou"] is not None)
        agg["S2_minus_S1"] = (round(agg["S2_iou"] - agg["S1_iou"], 4)
                              if agg["S2_iou"] is not None and agg["S1_iou"] is not None else None)
        agg["S2_minus_S0"] = (round(agg["S2_iou"] - agg["S0_iou"], 4)
                              if agg["S2_iou"] is not None else None)
        matched.append({"sample_id": sid, "per_point": rows, "mean_at_matched_points": agg})
    out["matched_points_S0_S1_S2"] = matched

    (R3 / "evidence/r3_metrics.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    # ---------------- console ----------------
    print("=========== S2: spatial grounding with ground truth ===========")
    for key, r in out["s2"].items():
        print(f"\n[{key}]  n={r['n_requested']}  usable={r['n_with_usable_box']}  "
              f"valid_ratio={r['valid_output_ratio']}  "
              f"invalid_kept={r['n_invalid_kept_in_denominator']}")
        print(f"   IoU mean={r['iou_mean']} median={r['iou_median']} "
              f"min={r['iou_min']} max={r['iou_max']}  "
              f"(>=0.5: {r['iou_ge_0.5']}, >=0.25: {r['iou_ge_0.25']})")
        print(f"   centre_err_mean={r['center_err_mean']}  area_ratio_median={r['area_ratio_median']}")
        for c in r["per_case"][:6]:
            print(f"     {c['case_id']:28s} IoU={c['iou']} ctr={c['center_err']} ar={c['area_ratio']}")
        if len(r["per_case"]) > 6:
            print(f"     ... {len(r['per_case'])-6} more in evidence/r3_metrics.json")

    print("\n=========== S1 tracking vs S0 constant baseline ===========")
    print(f"{'clip':24s} {'init_iou':>8s} {'S1_M1':>7s} {'S0_M1':>7s} {'d_M1':>7s} "
          f"{'d_M2':>7s} {'d_M3':>7s}  S1 never>S0?")
    for row in cmp_rows:
        print(f"{row['sample_id']:24s} {row['init_slot_iou']:8.3f} "
              f"{row['S1_M1_bin_start']:7.3f} {row['S0_M1_bin_start']:7.3f} "
              f"{row['S1_minus_S0_M1_bin_start']:+7.3f} "
              f"{row['S1_minus_S0_M2_bin_mid']:+7.3f} "
              f"{row['S1_minus_S0_M3_bin_end']:+7.3f}  "
              f"{row['S1_never_exceeds_S0_under_ANY_mapping']}")
    print("\n(mean IoU excluding the initialisation slot; mappings M1/M2/M3 = start/mid/end of "
          "each one-second bin)")

    print("\n=========== S0 / S1 / S2 at the SAME 8 key-frame instants ===========")
    print(f"{'clip':24s} {'n':>2s} {'S0':>7s} {'S1':>7s} {'S2':>7s} "
          f"{'S2-S0':>7s} {'S2-S1':>7s}")
    for m in matched:
        a = m["mean_at_matched_points"]
        print(f"{m['sample_id']:24s} {a['n_points']:2d} {a['S0_iou']:7.3f} "
              f"{a['S1_iou']:7.3f} {a['S2_iou']:7.3f} "
              f"{str(a['S2_minus_S0']):>7s} {str(a['S2_minus_S1']):>7s}")
    print("(identical clips, identical target, identical evaluation instants; "
          "the initialisation frame is not among them)")
    print("wrote", R3 / "evidence/r3_metrics.json")


if __name__ == "__main__":
    main()
