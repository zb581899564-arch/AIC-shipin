#!/usr/bin/env python3
"""Analyse the round-2 A/B/C tracking results.

Descriptive statistics only, plus an explicit anchor-copy test, because the
brief warns that "number of distinct boxes" is not by itself a quality metric.

For every case:
  * protocol states (from run_status.json)
  * distinct box count (descriptive)
  * exact-copy rate against the anchor box that was supplied in the prompt
  * mean IoU against the anchor box
  * per-second box trajectory summary
  * failure class

Failure classes used (from the brief):
  input_protocol_error, time_mapping_error, output_incomplete,
  target_switch, box_after_target_left, static_output, none_detected
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

R2 = Path("/home/inspur/aic_video_work/orarl_round2")
OUT = R2 / "outputs/r2tr"
ANALYSIS = R2 / "evidence/tracking_analysis.json"


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    aa = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    ab = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    u = aa + ab - inter
    return inter / u if u > 1e-12 else 0.0


def main():
    st = json.loads((OUT / "run_status.json").read_text())
    run = st["run"]
    cases = st["cases"]
    frozen = json.loads((R2 / "evidence/samples_frozen.json").read_text())
    fmap = {s["sample_id"]: s for s in frozen["samples"]}

    proc = {}
    for c in cases:
        sid = c["sample_id"]
        cond = c["condition"]
        p = c.get("parsed") or {}
        boxes = p.get("boxes_norm1000") or {}
        boxes = {int(k): v for k, v in boxes.items()}
        anchor = c.get("init_box_norm1000")
        rec = {
            "case_id": c["case_id"], "sample_id": sid, "condition": cond,
            "stratum": fmap.get(sid, {}).get("stratum"),
            "target": fmap.get(sid, {}).get("target"),
            "output_parseable": c["output_parseable"],
            "protocol_complete": c["protocol_complete"],
            "task_success": c["task_success"],
            "quality": c["quality"],
            "parse_errors": c["parse_errors"],
            "parse_warnings": c["parse_warnings"],
            "raw_output": c["raw_output"],
            "generate_seconds": c.get("generate_seconds"),
            "peak_memory_allocated_mib": c.get("peak_memory_allocated_mib"),
            "init_box_source": c.get("init_box_source"),
            "anchor_box": anchor,
            "n_keys_expected": len((c.get("expected") or {}).get("expected_seconds", [])),
            "n_keys_returned": len(boxes),
            "missing_seconds_n": len(p.get("missing_expected_seconds") or []),
            "sampling": {
                "n_sampled": (c.get("sampling_observed") or {}).get("n_sampled"),
                "second_bins": (c.get("sampling_observed") or {}).get("second_bin_per_slot"),
                "frames_indices": (c.get("sampling_observed") or {}).get("frames_indices"),
                "backend": (c.get("sampling_observed") or {}).get("video_backend"),
            },
        }
        if boxes:
            vals = [boxes[k] for k in sorted(boxes)]
            rec["distinct_boxes_n"] = len({tuple(v) for v in vals})
            rec["first_box"] = vals[0]
            rec["last_box"] = vals[-1]
            rec["median_box"] = [round(statistics.median(v[i] for v in vals), 1)
                                 for i in range(4)]
            rec["coord_stdev"] = [round(statistics.pstdev([v[i] for v in vals]), 2)
                                  for i in range(4)]
            if anchor:
                same = sum(1 for v in vals if all(abs(v[i] - anchor[i]) <= 1 for i in range(4)))
                rec["boxes_equal_to_anchor_n"] = same
                rec["boxes_equal_to_anchor_frac"] = round(same / len(vals), 3)
                rec["mean_iou_pred_vs_anchor"] = round(
                    sum(iou(v, anchor) for v in vals) / len(vals), 4)
            # how many times does the box change between consecutive seconds
            rec["n_box_changes"] = sum(1 for a, b in zip(vals, vals[1:])
                                       if any(abs(a[i] - b[i]) > 1 for i in range(4)))
        # ---- failure classes ----
        fc = []
        if c.get("execution_error"):
            fc.append("execution_error")
        if not c["output_parseable"]:
            fc.append("output_unparseable")
        if c["output_parseable"] and not c["protocol_complete"]:
            fc.append("output_incomplete")
        if rec.get("distinct_boxes_n") == 1:
            fc.append("static_output")
        bins = rec["sampling"].get("second_bins")
        if bins and any(b != i for i, b in enumerate(bins)):
            fc.append("time_mapping_error")
        rec["failure_classes"] = fc or ["none_detected"]
        proc[c["case_id"]] = rec

    # ---- A vs B vs C per sample ----
    per_sample = {}
    for sid in fmap:
        row = {"stratum": fmap[sid]["stratum"], "target": fmap[sid]["target"],
               "agent_box": fmap[sid]["box"], "conditions": {}}
        for cond in ("A", "B", "C"):
            r = proc.get(f"tr_{sid}_{cond}")
            if not r:
                continue
            row["conditions"][cond] = {
                k: r.get(k) for k in
                ("task_success", "protocol_complete", "n_keys_returned",
                 "distinct_boxes_n", "n_box_changes", "median_box",
                 "coord_stdev", "boxes_equal_to_anchor_frac",
                 "mean_iou_pred_vs_anchor", "anchor_box", "init_box_source",
                 "failure_classes")
            }
        per_sample[sid] = row

    out = {
        "run": {k: run.get(k) for k in
                ("run_id", "exit_code", "n_cases", "n_task_success", "n_failed",
                 "model_load_seconds", "of")},
        "note": ("'distinct_boxes_n' and 'n_box_changes' are DESCRIPTIVE only. Without a "
                 "trusted ground truth no accuracy metric can be computed, so quality stays "
                 "NOT_COMPUTABLE for every case."),
        "cases": proc,
        "per_sample": per_sample,
    }
    ANALYSIS.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print(f"run exit_code={run['exit_code']} n_failed={run['n_failed']}/{run['n_cases']}")
    print()
    hdr = f"{'case':16s} {'strat':26s} {'ok':5s} {'proto':5s} {'keys':4s} {'dist':4s} " \
          f"{'chg':4s} {'=anchor':7s} {'IoUanc':6s} {'failures'}"
    print(hdr)
    print("-" * len(hdr))
    for cid in sorted(proc, key=lambda k: (proc[k]["sample_id"], proc[k]["condition"])):
        r = proc[cid]
        print(f"{cid:16s} {str(r['stratum'])[:26]:26s} "
              f"{str(r['task_success']):5s} {str(r['protocol_complete']):5s} "
              f"{r['n_keys_returned']:4d} {str(r.get('distinct_boxes_n')):4s} "
              f"{str(r.get('n_box_changes')):4s} "
              f"{str(r.get('boxes_equal_to_anchor_frac')):7s} "
              f"{str(r.get('mean_iou_pred_vs_anchor')):6s} {','.join(r['failure_classes'])}")
        if r["parse_errors"]:
            print(f"      errors: {r['parse_errors'][:2]}")
    print("\nwrote", ANALYSIS)


if __name__ == "__main__":
    main()
