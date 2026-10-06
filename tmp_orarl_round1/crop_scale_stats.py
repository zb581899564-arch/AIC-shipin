#!/usr/bin/env python3
"""ROUND 4 section 7 — READ-ONLY crop-scale statistics.

Answers:
  * distribution of target ratio in the 987 weak labels
  * cropRois width relative to the MAXIMUM LEGAL crop width
    (compute_crop_size from the frozen baseline entry)
  * target-ratio distribution in the current train/test metadata
  * whether the weak labels basically always use the maximum legal width
  * how much the cropRois x actually MOVES inside a source group (this decides
    whether the weak proxy can discriminate between crop arms at all)

No GPU, no model.
"""
from __future__ import annotations

import json
import importlib.util
import statistics
import sys
from collections import Counter
from pathlib import Path

R4 = Path("/home/inspur/aic_video_work/orarl_round4")
LABELS = Path("/home/inspur/aic_video_data/labels/train.jsonl")
BASELINE = Path("/home/inspur/aic_video_work/inference/baseline_qwen3vl.py")


def load_baseline_module():
    """Import the FROZEN baseline entry read-only, to reuse compute_crop_size."""
    spec = importlib.util.spec_from_file_location("r4_baseline", BASELINE)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)   # imports cv2/torch lazily inside class only
    except Exception:
        # module-level import of cv2 may fail on system python; fall back to a
        # verbatim copy of the function extracted from the file
        src = BASELINE.read_text()
        start = src.index("def compute_crop_size")
        end = src.index("def center_to_box")
        ns = {"math": __import__("math"),
              "Tuple": __import__("typing").Tuple}
        exec(src[start:end], ns)      # noqa: S102 - pinned local file
        return ns
    return vars(mod)


def main():
    ns = load_baseline_module()
    compute_crop_size = ns["compute_crop_size"]

    rows = [json.loads(l) for l in LABELS.read_text().splitlines() if l.strip()]
    mrows = [json.loads(l) for l in (R4 / "evidence/mapping_rows.jsonl").read_text().splitlines()
             if l.strip()]
    usable = {m["row_index"]: m for m in mrows if m["status"] == "usable"}

    rep = {
        "labels_file": str(LABELS),
        "baseline_entry": str(BASELINE),
        "baseline_entry_sha256": __import__("hashlib").sha256(BASELINE.read_bytes()).hexdigest(),
        "n_label_rows": len(rows),
        "n_usable_mapping_rows": len(usable),
        "target_ratio_all_labels": {str(list(k)): v for k, v in Counter(
            tuple(r.get("targetRatioWH") or []) for r in rows).items()},
        "conclusion": {},
    }

    widths, ratios, xranges = [], [], []
    xrange_norm = []
    per_group_static = 0
    groups_checked = 0
    for idx, m in usable.items():
        r = rows[idx]
        tr = r.get("targetRatioWH")
        if not (isinstance(tr, (list, tuple)) and len(tr) == 2 and min(tr) > 0):
            continue
        pro = m.get("source_probe") or {}
        W, H = pro.get("width"), pro.get("height")
        if not W or not H:
            continue
        cw, hf = compute_crop_size(W, H, float(tr[0]), float(tr[1]))
        rois = r.get("cropRois") or []
        if not rois:
            continue
        ws = [b[2] for _, b in rois]
        xs = [b[0] for _, b in rois]
        wmed = statistics.median(ws)
        widths.append(wmed / cw if cw else None)
        ratios.append(statistics.median(ws) / statistics.median([b[3] for _, b in rois])
                      if any(b[3] for _, b in rois) else None)
        rng = max(xs) - min(xs)
        xranges.append(rng)
        legal = max(1, W - cw)
        xrange_norm.append(rng / legal)
        groups_checked += 1
        if rng <= 1:
            per_group_static += 1

    widths = [w for w in widths if w is not None]
    xrange_norm = [x for x in xrange_norm if x is not None]
    rep["cropRois_width_over_max_legal_width"] = {
        "n": len(widths),
        "min": round(min(widths), 4), "max": round(max(widths), 4),
        "median": round(statistics.median(widths), 4),
        "mean": round(statistics.mean(widths), 4),
        "frac_exactly_max_legal": round(sum(1 for w in widths if w >= 0.999) / len(widths), 4),
        "frac_within_2pct_of_max": round(sum(1 for w in widths if w >= 0.98) / len(widths), 4),
    }
    rep["cropRois_x_travel_px"] = {
        "n": len(xranges),
        "min": min(xranges), "max": max(xranges),
        "median": statistics.median(xranges),
        "mean": round(statistics.mean(xranges), 2),
        "n_groups_with_x_range_le_1px": per_group_static,
        "groups_checked": groups_checked,
        "frac_groups_static_in_x": round(per_group_static / groups_checked, 4),
    }
    rep["cropRois_x_travel_normalized_by_legal_range"] = {
        "min": round(min(xrange_norm), 4), "max": round(max(xrange_norm), 4),
        "median": round(statistics.median(xrange_norm), 4),
        "mean": round(statistics.mean(xrange_norm), 4),
        "frac_groups_travel_le_0.05": round(
            sum(1 for v in xrange_norm if v <= 0.05) / len(xrange_norm), 4),
        "frac_groups_travel_le_0.25": round(
            sum(1 for v in xrange_norm if v <= 0.25) / len(xrange_norm), 4),
    }

    # does the weak proxy use the maximum legal width almost always?
    frac_max = rep["cropRois_width_over_max_legal_width"]["frac_exactly_max_legal"]
    rep["conclusion"]["uses_max_legal_width_almost_always"] = bool(frac_max >= 0.95)
    rep["conclusion"]["dynamic_scale_supported_by_weak_labels"] = bool(frac_max < 0.5)
    rep["conclusion"]["weak_proxy_x_is_static"] = bool(
        rep["cropRois_x_travel_normalized_by_legal_range"]["frac_groups_travel_le_0.05"] >= 0.5)
    rep["conclusion"]["note"] = (
        "If the weak proxy almost always uses the maximum legal width, a dynamic-scale "
        "experiment cannot be justified from these labels. If the weak x barely moves, the "
        "weak proxy cannot discriminate between crop arms that only differ in centre.")

    (R4 / "evidence/crop_scale_stats.json").write_text(
        json.dumps(rep, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    print("\nwrote evidence/crop_scale_stats.json")


if __name__ == "__main__":
    main()
