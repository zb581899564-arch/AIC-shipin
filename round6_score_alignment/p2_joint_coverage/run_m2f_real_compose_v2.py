"""Milestone-2f runner (supervisor fix 2, corrected): real-inference composition
on the SOURCE-frame grid.

Builds the delivery-shape per-frame prediction file for the 82 frozen dev clips
from two real input classes — no simulation, no new inference:

* ``REAL_INFERENCE``: the recorded v2 unfused-model outputs on the source-frame
  grid (``gap_predictions_v2_subset.jsonl``), covering the budget-bounded
  subset (6,186 of the 13,777 selected source frames; subset seed 20260918);
* ``WEAK_ROI_SAME_FRAME``: the frozen weak-ROI box at the identical frame for
  the 186 frozen keyframes the selection hits — a **link-check only** input
  that is NOT obtainable at deployment time;
* ``NOT_INFERRED_BUDGET``: selected frames outside the bounded subset.  These
  are reported with an explicit placeholder status in the manifest (never a
  box) so the composed file contains ONLY verified boxes.

The composed file is re-validated with the strict loader (video ids, source
frame numbers, box legality, duplicates, missing, empty results) and hashed.
The raw v1/v2 prediction files are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import provenance                                    # noqa: E402
from aic6.coverage import CoverageState, audit_frames          # noqa: E402
from aic6.scoring import load_predictions                      # noqa: E402
from aic6.segments import SegmentConstraint, parse_response    # noqa: E402

RUN_ID_DEFAULT = "round6_p2_m2f_20260918T0000Z"
CONSTRAINT = SegmentConstraint(0, 5)
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"
P2 = ROOT / "reports/round6_score_alignment/p2_joint_coverage"
SUBSET_SEED = 20260918


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(P2))
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()
    started = time.monotonic()

    dev_temporal = load_jsonl(WEAK / "dev_temporal.jsonl")
    dev_frames = load_jsonl(WEAK / "dev_frames.jsonl")
    s2_rows = {row["video_id"]: row for row in load_jsonl(WEAK / "temporal_S2.jsonl")}
    v2_rows = load_jsonl(P2 / "gap_predictions_v2_subset.jsonl")
    v2_meta = json.loads((P2 / "gap_predictions_v2_subset.run.json").read_text(encoding="utf-8"))
    if sha256_file(P2 / "gap_predictions_v2_subset.jsonl") != v2_meta["output_sha256"]:
        print("FAIL: v2 output hash mismatch", file=sys.stderr)
        return 2
    full_requests = load_jsonl(P2 / "p2_infer_requests_v2_source_grid.jsonl")
    subset_requests = load_jsonl(P2 / "p2_infer_requests_v2_subset.jsonl")
    if sha256_file(P2 / "p2_infer_requests_v2_subset.jsonl") != v2_meta["requests_sha256"]:
        print("FAIL: v2 request hash mismatch", file=sys.stderr)
        return 2
    request_key = lambda r: (r["video_id"], int(r["source_frame"]))
    full_keys = [request_key(r) for r in full_requests]
    subset_keys = [request_key(r) for r in subset_requests]
    output_keys = [request_key(r) for r in v2_rows]
    request_keys_valid = (len(full_keys) == len(set(full_keys))
                          and len(subset_keys) == len(set(subset_keys))
                          and len(output_keys) == len(set(output_keys))
                          and set(subset_keys) <= set(full_keys)
                          and set(output_keys) == set(subset_keys))
    if not request_keys_valid:
        print("FAIL: duplicate, missing or extra v2 request/output key", file=sys.stderr)
        return 2

    frozen: dict[str, dict[int, dict]] = {}
    for frame in dev_frames:
        frozen.setdefault(frame["video_id"], {})[int(frame["source_frame"])] = frame

    # SOURCE-grid selection (same rule that produced the v2 request manifest)
    clip_meta: dict[str, dict] = {}
    selection: dict[str, set[int]] = {}
    first_frame = {}
    for frame in dev_frames:
        first_frame.setdefault(frame["video_id"], frame)
    for row in dev_temporal:
        vid = row["video_id"]
        frame0 = first_frame[vid]
        sfps = float(frame0["source_fps"])
        sf = math.ceil(row["clip_start_sec"] * sfps)
        ef = math.floor(row["clip_end_sec"] * sfps)
        clip_meta[vid] = {"sfps": sfps, "sf": sf,
                          "width": int(frame0["source_width"]),
                          "height": int(frame0["source_height"]),
                          "source_path": frame0["source_path"]}
        s2 = s2_rows[vid]
        outcome = parse_response(s2["raw_output"], duration_sec=s2["clip_duration_sec"],
                                 constraint=CONSTRAINT)
        frames: set[int] = set()
        if outcome.is_usable and outcome.segments:
            for a_local, b_local in outcome.segments:
                lo = math.ceil(a_local * sfps)
                hi = math.ceil(b_local * sfps)
                frames.update(range(sf + max(0, lo), sf + min(ef - sf + 1, hi)))
        selection[vid] = frames

    # verify the full request manifest matches this selection exactly
    manifest_keys = set(full_keys)
    selection_keys = {(vid, f) for vid, s in selection.items() for f in s}
    manifest_matches_selection = manifest_keys == selection_keys

    inferred = {(r["video_id"], int(r["source_frame"])): r for r in v2_rows}

    composed: dict[str, dict[int, dict]] = {}
    stats = {"REAL_INFERENCE": 0, "WEAK_ROI_SAME_FRAME": 0,
             "NOT_INFERRED_BUDGET": 0, "INVALID_INFERENCE": 0}
    coverage_counts = {state.value: 0 for state in CoverageState}
    for vid in sorted(clip_meta, key=lambda v: int(v.split("_")[1])):
        meta = clip_meta[vid]
        frames_sel = sorted(selection.get(vid, set()))
        boxes = {f: item["weak_roi_xywh"][:3] for f, item in frozen.get(vid, {}).items()}
        audit = audit_frames(selected_frames=frames_sel, source_boxes=boxes,
                             n_frames=max(frames_sel) + 1 if frames_sel else 1,
                             shots=None, max_reuse_gap_frames=None)
        for state, n in audit.counts.items():
            coverage_counts[state] += n
        slot = composed.setdefault(vid, {})
        for frame in frames_sel:
            if frame in boxes:
                # the recorded weak ROI width (169) can exceed the legal 9:16
                # maximum (floor(H*9/16)=168 for H=300); the delivery-shape file
                # needs a legal box, so clamp width/x and record the clamping
                x, y, w = (int(v) for v in boxes[frame])
                w_legal = min(w, int(math.floor(meta["height"] * 9 / 16 + 1e-12)))
                x_clamped = min(x, meta["width"] - w_legal)
                slot[frame] = {"box_xyw": [x_clamped, y, w_legal],
                               "source": "WEAK_ROI_SAME_FRAME",
                               "clamped_from_width": w} if w_legal != w else \
                    {"box_xyw": [x, y, w], "source": "WEAK_ROI_SAME_FRAME"}
                stats["WEAK_ROI_SAME_FRAME"] += 1
            elif (vid, frame) in inferred:
                record = inferred[(vid, frame)]
                if record.get("output_valid") and record.get("box_xywh"):
                    slot[frame] = {"box_xyw": [int(v) for v in record["box_xywh"]],
                                   "source": "REAL_INFERENCE"}
                    stats["REAL_INFERENCE"] += 1
                else:
                    slot[frame] = {"box_xyw": None, "source": "INVALID_INFERENCE"}
                    stats["INVALID_INFERENCE"] += 1
            else:
                slot[frame] = {"box_xyw": None, "source": "NOT_INFERRED_BUDGET"}
                stats["NOT_INFERRED_BUDGET"] += 1

    # delivery file contains ONLY verified boxes; frames without a box are listed
    # in the manifest, never filled
    out_path = out_dir / f"{args.run_id}.real_composed_predictions.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_path.exists() or (out_dir / f"{args.run_id}.json").exists():
        print("FAIL: refusing to overwrite a prior composition", file=sys.stderr)
        return 2
    with out_path.open("w", encoding="utf-8") as stream:
        for vid in sorted(clip_meta, key=lambda v: int(v.split("_")[1])):
            preds = [{"frame": int(f), "bboxes": list(item["box_xyw"]),
                      "source": item["source"]}
                     for f, item in sorted(composed[vid].items()) if item["box_xyw"]]
            stream.write(json.dumps({"video_id": vid, "targetRatioWH": [9, 16],
                                     "predictions": preds}, ensure_ascii=False) + "\n")

    temporal_by_vid = {row["video_id"]: row for row in dev_temporal}
    index = {vid: {"video_id": vid, "targetRatioWH": [9.0, 16.0],
                   "width": meta["width"], "height": meta["height"],
                   "n_frames": math.floor(
                       temporal_by_vid[vid]["clip_end_sec"] * meta["sfps"]) + 1}
             for vid, meta in clip_meta.items()}
    loaded = load_predictions(out_path, index)
    n_boxes = sum(len(v) for v in loaded.rows.values())
    n_selected = len(selection_keys)
    selection_complete = (n_boxes == n_selected
                          and stats["NOT_INFERRED_BUDGET"] == 0
                          and stats["INVALID_INFERENCE"] == 0)
    deployable = (loaded.ok and manifest_matches_selection and selection_complete
                  and stats["WEAK_ROI_SAME_FRAME"] == 0)
    delivery_status = ("OK_DELIVERABLE" if deployable else
                       "NOT_DELIVERABLE_BUDGET" if not selection_complete else
                       "NOT_DELIVERABLE_LABEL_SOURCE")

    result = {
        "schema": "aic6_p2_m2f_real_composition_v2",
        "run_id": args.run_id,
        "official_status": "NOT_OFFICIAL_SCORE",
        "grid": "source-frame grid (decord avg fps); supersedes the v1 clip-grid naming",
        "inputs": {
            "v2_output_sha256": sha256_file(P2 / "gap_predictions_v2_subset.jsonl"),
            "v2_meta": {"rows": v2_meta["rows"], "invalid": v2_meta["invalid"],
                        "total_wall_seconds": v2_meta["total_wall_seconds"],
                        "peak_memory_mib": v2_meta["peak_memory_mib"]},
            "full_request_manifest_sha256": sha256_file(P2 / "p2_infer_requests_v2_source_grid.jsonl"),
            "subset_request_manifest_sha256": sha256_file(P2 / "p2_infer_requests_v2_subset.jsonl"),
        },
        "manifest_matches_selection": manifest_matches_selection,
        "request_keys_valid": request_keys_valid,
        "format_valid": loaded.ok,
        "selection_complete": selection_complete,
        "deployable": deployable,
        "delivery_status": delivery_status,
        "selection_totals": {
            "selected_source_frames": sum(len(s) for s in selection.values()),
            "videos_with_selection": sum(1 for s in selection.values() if s),
        },
        "coverage_counts_of_selection": coverage_counts,
        "composition": {
            "path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(out_path),
            "n_boxes": n_boxes,
            "source_counts": stats,
            "strict_validation_ok": loaded.ok,
            "n_issue_codes": loaded.validation["n_issue_codes"],
            "issues_first_10": loaded.validation["issues"][:10],
        },
        "budget_subset": {
            "subset_frames": v2_meta["rows"],
            "full_selection_frames": sum(len(s) for s in selection.values()),
            "subset_seed": SUBSET_SEED,
            "note": "subset bounded by the remaining P2 GPU budget (seed-frozen sample)",
        },
        "notes": [
            "WEAK_ROI_SAME_FRAME boxes reuse the frozen weak ROI at the identical source "
            "frame: a LINK CHECK ONLY, not obtainable at deployment",
            "REAL_INFERENCE boxes are recorded unfused-model outputs on the source-frame grid",
            "frames without a verified box are excluded from the delivery file and counted "
            "as NOT_INFERRED_BUDGET in the manifest; nothing is auto-filled",
            "dev-only composition; never a competition submission",
        ],
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    provenance.write_json(out_dir / f"{args.run_id}.json", result)
    print(f"{delivery_status}: wrote {out_dir / (args.run_id + '.json')}")
    print(json.dumps({k: result[k] for k in ("selection_totals", "composition",
                                             "budget_subset")}, indent=1))
    ok = (loaded.ok and manifest_matches_selection and request_keys_valid
          and stats["REAL_INFERENCE"] > 0)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
