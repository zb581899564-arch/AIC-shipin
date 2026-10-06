#!/usr/bin/env python3
"""ROUND 3 — programmatic recount of the B/C anchor-copy behaviour.

Round 2 wrote things like "B/C copy the anchor verbatim in 5/7 clips". That
phrasing conflates "some frames equal the anchor" with "the whole segment is a
copy". This script recomputes, per case:

  * whole-segment copy: EVERY returned box equals the anchor (within tol)
  * per-segment equality ratio: (#boxes == anchor) / (#boxes returned)
  * near-but-not-equal: max coordinate deviation among non-equal boxes
  * also vs the case's own first box (self-constancy), which is what "static"
    should mean when there is no anchor (condition A)

Tolerance: reported at tol=0 (exact integers) and tol=1 (rounding-level).
"""
from __future__ import annotations

import json
from pathlib import Path

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
OUT = R2 / "outputs/r2tr/run_status.json"
DEST = Path("/home/inspur/aic_video_work/orarl_round3/evidence/bc_copy_recount.json")


def eq(a, b, tol):
    return all(abs(float(a[i]) - float(b[i])) <= tol for i in range(4))


def main():
    st = json.loads(OUT.read_text())
    rows = []
    for c in st["cases"]:
        if c["task"] != "tracking":
            continue
        boxes = {int(k): v for k, v in ((c.get("parsed") or {})
                                        .get("boxes_norm1000") or {}).items()}
        if not boxes:
            rows.append({"case_id": c["case_id"], "condition": c["condition"],
                         "sample_id": c["sample_id"], "n_boxes": 0,
                         "no_boxes": True,
                         "parse_errors": c["parse_errors"]})
            continue
        ks = sorted(boxes)
        vals = [boxes[k] for k in ks]
        anchor = c.get("init_box_norm1000")
        first = vals[0]
        rec = {
            "case_id": c["case_id"], "sample_id": c["sample_id"],
            "condition": c["condition"], "n_boxes": len(vals),
            "distinct_boxes_n": len({tuple(v) for v in vals}),
            "anchor_box": anchor,
            "anchor_source": c.get("init_box_source"),
            "task_success": c["task_success"],
        }
        for tol in (0, 1):
            sfx = "" if tol == 0 else "_tol1"
            if anchor:
                m = sum(1 for v in vals if eq(v, anchor, tol))
                rec[f"boxes_equal_anchor{sfx}"] = m
                rec[f"frac_equal_anchor{sfx}"] = round(m / len(vals), 4)
                rec[f"WHOLE_SEGMENT_IS_ANCHOR_COPY{sfx}"] = (m == len(vals))
                ne = [v for v in vals if not eq(v, anchor, tol)]
                if ne:
                    dev = max(max(abs(float(v[i]) - float(anchor[i])) for i in range(4))
                              for v in ne)
                    rec[f"max_coord_deviation_of_non_equal{sfx}"] = round(dev, 1)
                    rec[f"NEAR_BUT_NOT_EQUAL{sfx}"] = bool(dev <= 50)
                else:
                    rec[f"max_coord_deviation_of_non_equal{sfx}"] = None
                    rec[f"NEAR_BUT_NOT_EQUAL{sfx}"] = False
            # self-constancy (meaningful for condition A, which has no anchor)
            m2 = sum(1 for v in vals if eq(v, first, tol))
            rec[f"boxes_equal_own_first{sfx}"] = m2
            rec[f"frac_equal_own_first{sfx}"] = round(m2 / len(vals), 4)
            rec[f"WHOLE_SEGMENT_CONSTANT{sfx}"] = (m2 == len(vals))
        rows.append(rec)

    # aggregates
    b = [r for r in rows if r["condition"] == "B" and r.get("anchor_box")]
    c_ = [r for r in rows if r["condition"] == "C" and r.get("anchor_box")]
    a_ = [r for r in rows if r["condition"] == "A"]
    agg = {
        "B": {
            "n_cases": len(b),
            "n_whole_segment_anchor_copy_tol1": sum(1 for r in b
                                                    if r.get("WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1")),
            "per_case_frac_equal_anchor_tol1": {r["sample_id"]: r.get("frac_equal_anchor_tol1")
                                                for r in b},
            "cases_whole_segment_copy": [r["sample_id"] for r in b
                                         if r.get("WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1")],
            "cases_partial_copy": [r["sample_id"] for r in b
                                   if r.get("boxes_equal_anchor_tol1") and
                                   not r.get("WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1")],
            "cases_no_copy": [r["sample_id"] for r in b
                              if not r.get("boxes_equal_anchor_tol1")],
            "cases_near_but_not_equal": [r["sample_id"] for r in b if r.get("NEAR_BUT_NOT_EQUAL_tol1")],
        },
        "C": {
            "n_cases": len(c_),
            "n_whole_segment_anchor_copy_tol1": sum(1 for r in c_
                                                    if r.get("WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1")),
            "per_case_frac_equal_anchor_tol1": {r["sample_id"]: r.get("frac_equal_anchor_tol1")
                                                for r in c_},
            "cases_whole_segment_copy": [r["sample_id"] for r in c_
                                         if r.get("WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1")],
            "cases_partial_copy": [r["sample_id"] for r in c_
                                   if r.get("boxes_equal_anchor_tol1") and
                                   not r.get("WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1")],
            "cases_no_copy": [r["sample_id"] for r in c_
                              if not r.get("boxes_equal_anchor_tol1")],
            "cases_near_but_not_equal": [r["sample_id"] for r in c_ if r.get("NEAR_BUT_NOT_EQUAL_tol1")],
        },
        "A": {
            "n_cases": len(a_),
            "n_whole_segment_constant_tol1": sum(1 for r in a_
                                                 if r.get("WHOLE_SEGMENT_CONSTANT_tol1")),
            "cases_whole_segment_constant": [r["sample_id"] for r in a_
                                             if r.get("WHOLE_SEGMENT_CONSTANT_tol1")],
        },
    }

    out = {
        "source": str(OUT),
        "tolerance_note": ("tol1 = per-coordinate absolute difference <= 1 norm1000 unit, i.e. "
                           "rounding level; tol0 = exact integer equality"),
        "correction_of_round2_wording": (
            "Round 2 said things like 'B/C copy the anchor verbatim in 5/7 clips'. The "
            "recount below separates WHOLE-SEGMENT copy (every box equals the anchor) from "
            "PARTIAL copy (some boxes equal it) and from NEAR-BUT-NOT-EQUAL. Only the "
            "whole-segment numbers may be described as 'the whole segment is a copy'."
        ),
        "per_case": rows,
        "aggregate": agg,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    for cond in ("B", "C", "A"):
        a = agg[cond]
        print(f"\n=== condition {cond} ===")
        for k, v in a.items():
            print(f"  {k}: {v}")
    print("\n=== per-case detail (tol=1) ===")
    hdr = (f"{'case':14s} {'n':>3s} {'dist':>4s} {'=anchor':>7s} {'frac':>6s} "
           f"{'WHOLE':>5s} {'near':>5s} {'maxdev':>7s} {'const':>5s}")
    print(hdr)
    for r in sorted(rows, key=lambda x: x["case_id"]):
        print(f"{r['case_id']:14s} {r['n_boxes']:3d} {r.get('distinct_boxes_n',0):4d} "
              f"{str(r.get('boxes_equal_anchor_tol1')):>7s} "
              f"{str(r.get('frac_equal_anchor_tol1')):>6s} "
              f"{str(r.get('WHOLE_SEGMENT_IS_ANCHOR_COPY_tol1')):>5s} "
              f"{str(r.get('NEAR_BUT_NOT_EQUAL_tol1')):>5s} "
              f"{str(r.get('max_coord_deviation_of_non_equal_tol1')):>7s} "
              f"{str(r.get('WHOLE_SEGMENT_CONSTANT_tol1')):>5s}")
    print("\nwrote", DEST)


if __name__ == "__main__":
    main()
