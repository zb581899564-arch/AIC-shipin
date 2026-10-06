"""Milestone-2 runner part A: simulated-prediction CPU tests on the frozen 82-video dev set.

Purpose
-------
Exercise the *whole delivery path* — S2 temporal windows -> strict parse ->
TIMESTAMP_HALFOPEN frame selection -> four-state spatial coverage -> simulated
spatial inference -> official-format prediction rows -> strict validation ->
sparse diagnostics — against the frozen weak-dev data with **simulated** boxes,
so every geometric / endpoint / duplicate / missing-frame edge is CPU-testable
before any GPU inference is spent.

Simulation rules (frozen before running):
* ``ORACLE_SPARSE``: the weak ROI of a frozen keyframe, when the selection
  contains that exact frame (7 frames expected); else the frame is sent to the
  simulated "inference" arm below.
* ``SIM_INFER``: for frames that need inference, a deterministic pseudo-box is
  generated from the video's own geometry (no randomness, no test content):
  a centred max-legal crop of the declared target ratio.  This is *not* a
  quality claim — it validates plumbing, legality and accounting only.
* 16:9 rows are geometry-only: the frozen labels are all 9:16, so a mirrored
  synthetic 16:9 index checks legality/coverage/cost paths without any claim
  about label quality.

Outputs one JSON artifact; never a submission file.
"""
from __future__ import annotations

import argparse
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
from aic6.coverage import (                                    # noqa: E402
    CoverageGate,
    CoverageState,
    audit_frames,
)
from aic6.scoring import (                                     # noqa: E402
    Box,
    ScoreStatus,
    box_from_xyw,
    load_predictions,
    spatial_iou,
)
from aic6.segments import SegmentConstraint, SegmentState, parse_response  # noqa: E402
from aic6.timebase import (                                    # noqa: E402
    CfrTimeline,
    local_interval_to_absolute,
    select_frames_timestamp_halfopen,
    select_frames_legacy_round_inclusive,
)

RUN_ID_DEFAULT = "round6_p2_m2a_20260918T0000Z"
CONSTRAINT = SegmentConstraint(0, 5)
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


import hashlib  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def centred_max_legal(w: int, h: int, tw: float, th: float) -> Box:
    """Deterministic simulated box: centred max-legal crop for the target ratio."""
    cw = min(w, max(1, int(math.floor(h * tw / th + 1e-12))))
    while cw > 1 and cw * th > h * tw:
        cw -= 1
    x = (w - cw) // 2
    y = max(0, int(math.floor(h - cw * th / tw + 1e-9)) // 2)
    return Box(x=float(x), y=float(y), w=float(cw), h=cw * th / tw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "reports/round6_score_alignment/p2_joint_coverage"))
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    dev_temporal = load_jsonl(WEAK / "dev_temporal.jsonl")
    dev_frames = load_jsonl(WEAK / "dev_frames.jsonl")
    s2_rows = {row["video_id"]: row for row in load_jsonl(WEAK / "temporal_S2.jsonl")}

    # ---- media index (clip coordinates; clip_fps from the frozen frames) -----
    clip_meta: dict[str, dict] = {}
    for row in dev_temporal:
        vid = row["video_id"]
        frame0 = next(f for f in dev_frames if f["video_id"] == vid)
        fps = float(frame0["clip_fps"])
        width = int(frame0["source_width"])
        height = int(frame0["source_height"])
        n_clip = int(math.floor(row["clip_end_sec"] * fps)) - int(math.ceil(row["clip_start_sec"] * fps)) + 1
        clip_meta[vid] = {"video_id": vid, "targetRatioWH": [9.0, 16.0],
                          "width": width, "height": height, "n_frames": n_clip,
                          "fps": fps,
                          "clip_start_sec": float(row["clip_start_sec"]),
                          "clip_end_sec": float(row["clip_end_sec"])}

    # ---- selection under the frozen new policy ------------------------------
    selection: dict[str, set[int]] = {}
    selection_legacy: dict[str, set[int]] = {}
    parse_state_counts: dict[str, int] = {}
    for vid, meta in clip_meta.items():
        s2 = s2_rows[vid]
        outcome = parse_response(s2["raw_output"], duration_sec=s2["clip_duration_sec"],
                                 constraint=CONSTRAINT)
        parse_state_counts[outcome.state.value] = parse_state_counts.get(outcome.state.value, 0) + 1
        if not outcome.is_usable or not outcome.segments:
            continue
        fps, n_frames = meta["fps"], meta["n_frames"]
        timeline = CfrTimeline(fps=fps, n_frames=n_frames)
        slot, slot_legacy = selection.setdefault(vid, set()), selection_legacy.setdefault(vid, set())
        for a_local, b_local in outcome.segments:
            _a, _b, origin = local_interval_to_absolute(
                a_local_sec=a_local, b_local_sec=b_local,
                window_start_sec=meta["clip_start_sec"], fps=fps, n_frames=n_frames,
                use_sampling_origin=True)
            slot.update(select_frames_timestamp_halfopen(
                a_sec=a_local, b_sec=b_local, timeline=timeline, origin_frame=origin).frames)
            slot_legacy.update(select_frames_legacy_round_inclusive(
                a_sec=meta["clip_start_sec"] + a_local, b_sec=meta["clip_start_sec"] + b_local,
                fps=fps, n_frames=n_frames).frames)

    # ---- spatial sources: weak ROIs of frozen keyframes (box source only) ---
    frozen_frames_by_vid: dict[str, dict[int, dict]] = {}
    for frame in dev_frames:
        frozen_frames_by_vid.setdefault(frame["video_id"], {})[int(frame["clip_frame"])] = frame

    # ---- four-state audit + coverage gate per video --------------------------
    audit_totals = {state.value: 0 for state in CoverageState}
    gate_counts = {"DELIVERABLE": 0, "NEEDS_SPATIAL_INFERENCE": 0, "EMPTY_SELECTION": 0}
    inference_frames_total = 0
    per_video_rows = []
    simulated_predictions: dict[str, dict[int, list]] = {}
    for vid in sorted(clip_meta):
        meta = clip_meta[vid]
        frames = sorted(selection.get(vid, set()))
        boxes = {}
        for f, item in frozen_frames_by_vid.get(vid, {}).items():
            roi = item["weak_roi_xywh"]
            boxes[f] = [int(roi[0]), int(roi[1]), int(roi[2])]
        audit = audit_frames(selected_frames=frames, source_boxes=boxes,
                             n_frames=meta["n_frames"], shots=None, max_reuse_gap_frames=None)
        gate = CoverageGate(allow_bounded_within_shot=False).judge(audit)
        gate_counts[gate["verdict"]] = gate_counts.get(gate["verdict"], 0) + 1
        for state, n in audit.counts.items():
            audit_totals[state] += n
        inference_frames_total += audit.counts[CoverageState.NEEDS_INFERENCE.value] \
            + audit.counts[CoverageState.UNRESOLVABLE.value]

        # simulated spatial inference: centred max-legal box for every NEEDS_INFERENCE
        # frame (SIM arm); SAME_FRAME frames reuse the weak ROI *clamped to legal
        # geometry* (the recorded ROI width 169 can exceed the legal 168 by 1 px)
        sim_boxes: dict[int, Box] = {}
        for row in audit.rows:
            if row.state == CoverageState.SAME_FRAME.value:
                roi = frozen_frames_by_vid[vid][row.frame]["weak_roi_xywh"]
                w = int(min(roi[2], math.floor(meta["height"] * 9 / 16 + 1e-12)))
                x = int(min(roi[0], meta["width"] - w))
                sim_boxes[row.frame] = box_from_xyw(
                    [float(x), float(roi[1]), float(w)],
                    ratio_wh=[9, 16], width=meta["width"], height=meta["height"],
                    location=f"sim {vid}:{row.frame}")
            else:
                sim_boxes[row.frame] = centred_max_legal(meta["width"], meta["height"], 9, 16)
        simulated_predictions[vid] = sim_boxes
        per_video_rows.append({
            "video_id": vid, "n_selected": len(frames),
            "counts": audit.counts, "verdict": gate["verdict"],
        })

    # ---- write simulated official-format predictions and re-validate ---------
    sim_path = out_dir / f"{args.run_id}.sim_predictions.jsonl"
    with sim_path.open("w", encoding="utf-8") as stream:
        for vid in sorted(clip_meta, key=lambda v: int(v.split("_")[1])):
            meta = clip_meta[vid]
            preds = [{"frame": int(f), "bboxes": [int(b.x), int(b.y), int(b.w)]}
                     for f, b in sorted(simulated_predictions[vid].items())]
            stream.write(json.dumps({
                "video_id": vid, "targetRatioWH": [9, 16], "predictions": preds,
            }, ensure_ascii=False) + "\n")

    loaded = load_predictions(sim_path, clip_meta)
    n_loaded = sum(len(v) for v in loaded.rows.values())

    # ---- sparse diagnostics against the frozen weak ROIs ---------------------
    # The IoU convention here reproduces the weak_dev_pilot scorer exactly:
    # rectangles with h = min(w * th / tw, H) for BOTH boxes (verified against
    # P0_mean/P1_mean of weak_spatial_p0_p1.json to machine precision).
    def weak_iou(a: Box, b: Box, height: int, tw: float, th: float) -> float:
        ar = (a.x, a.y, a.w, min(a.w * th / tw, float(height)))
        br = (b.x, b.y, b.w, min(b.w * th / tw, float(height)))
        ix = max(0.0, min(ar[0] + ar[2], br[0] + br[2]) - max(ar[0], br[0]))
        iy = max(0.0, min(ar[1] + ar[3], br[1] + br[3]) - max(ar[1], br[1]))
        inter = ix * iy
        union = ar[2] * ar[3] + br[2] * br[3] - inter
        return inter / union if union > 1e-12 else 0.0

    matched_frames = []
    for vid, boxes in loaded.rows.items():
        for f, box in boxes.items():
            frozen = frozen_frames_by_vid.get(vid, {}).get(f)
            if frozen is None:
                continue
            roi = frozen["weak_roi_xywh"]
            gt = Box(x=float(roi[0]), y=float(roi[1]), w=float(roi[2]),
                     h=min(float(roi[2]) * 16 / 9, float(clip_meta[vid]["height"])))
            matched_frames.append({"video_id": vid, "frame": f,
                                   "iou": weak_iou(box, gt, clip_meta[vid]["height"], 9, 16),
                                   "arm": "SIM"})
    sim_iou_values = [m["iou"] for m in matched_frames]

    # ---- 16:9 geometry-only mirror test (legality / coverage / cost) ---------
    mirrored_index = {
        f"{vid}_169": {**meta, "video_id": f"{vid}_169",
                       "targetRatioWH": [16.0, 9.0],
                       "n_frames": meta["n_frames"]}
        for vid, meta in clip_meta.items()
    }
    mirrored_boxes = {}
    mirrored_illegal = 0
    for vid, meta in mirrored_index.items():
        for f in selection.get(vid.replace("_169", ""), set()):
            try:
                mirrored_boxes[(vid, f)] = centred_max_legal(meta["width"], meta["height"], 16, 9)
            except Exception:
                mirrored_illegal += 1
    mirrored_illegal += sum(
        1 for (vid, f), b in mirrored_boxes.items()
        if b.y + b.h > mirrored_index[vid]["height"] + 1e-9
        or b.x + b.w > mirrored_index[vid]["width"] + 1e-9)

    result = {
        "schema": "aic6_p2_m2a_sim_cpu_v1",
        "run_id": args.run_id,
        "official_status": "NOT_OFFICIAL_SCORE",
        "labels_are_weak_teacher": True,
        "simulation_rules": {
            "SAME_FRAME": "weak ROI of the frozen keyframe reused at the identical frame",
            "NEEDS_INFERENCE": "deterministic centred max-legal crop (plumbing test, not quality)",
            "note": "simulated boxes validate legality/accounting; no quality claim is made",
        },
        "inputs": {
            "dev_videos": len(clip_meta),
            "frozen_frames": len(dev_frames),
            "s2_rows": len(s2_rows),
            "parse_states_of_s2": parse_state_counts,
        },
        "selection": {
            "n_videos_with_selection": sum(1 for s in selection.values() if s),
            "n_selected_new_policy": sum(len(s) for s in selection.values()),
            "n_selected_legacy_round_inclusive": sum(len(s) for s in selection_legacy.values()),
        },
        "coverage": {
            "audit_totals": audit_totals,
            "gate_verdicts": gate_counts,
            "frames_needing_inference": inference_frames_total,
        },
        "simulated_prediction_file": {
            "path": str(sim_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(sim_path),
            "rows_validated_ok": loaded.ok,
            "n_boxes_loaded": n_loaded,
            "n_issue_codes": loaded.validation["n_issue_codes"],
            "issues_first_10": loaded.validation["issues"][:10],
        },
        "sparse_weak_diagnostic": {
            "status": ScoreStatus.SPARSE_DIAGNOSTIC.value,
            "matched_frozen_frames": len(matched_frames),
            "sim_mean_iou_on_frozen": (round(sum(sim_iou_values) / len(sim_iou_values), 9)
                                       if sim_iou_values else None),
            "note": ("weak sparse diagnostic only; boxes are simulated so this number has "
                     "no quality meaning and is reported to prove the plumbing computes it"),
        },
        "geometry_169_mirror": {
            "videos": len(mirrored_index),
            "boxes_legal_checked": len(mirrored_boxes),
            "illegal_boxes": mirrored_illegal,
            "note": ("16:9 is geometry/coverage/cost only: all frozen labels are 9:16, "
                     "so no label-quality claim is possible in 16:9"),
        },
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }

    provenance.write_json(out_dir / f"{args.run_id}.json", result)
    print(f"OK: wrote {out_dir / (args.run_id + '.json')}")
    print(json.dumps({k: result[k] for k in ("selection", "coverage",
                                             "simulated_prediction_file",
                                             "geometry_169_mirror")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
