"""Milestone-2c/3 runner: paired old-chain vs new-chain comparison on the frozen dev set.

Arms (temporal output fixed: the recorded round-6 S2 predictions; only the
spatial sourcing differs):
* ``NEW_CHAIN``  — four-state coverage audit; SAME_FRAME reuses the frozen
  keyframe box; every other frame uses the *real* unfused-model spatial
  inference collected in ``gap_predictions.jsonl`` (856 NEEDS_INFERENCE + 7
  controls).  No unbounded copying, no cross-shot copying, no center-crop
  fallback.
* ``LEGACY_CHAIN`` — the historical rule: every selected frame without a
  same-frame source copies the nearest old box anywhere in the clip
  (reproduced here from the same spatial source, not re-run on GPU).

Diagnostics computed from the frozen weak ROIs (all 9:16):
* primary: frame-level weak IoU on the 272 frozen keyframes that the selection
  hits (sparse — reported as SPARSE_DIAGNOSTIC semantics, never a joint score);
* secondary: coverage / legality / call counts / wall time / peak memory.

The paired unit is the dev clip (82 clips, 74 source groups); invalid results
stay in the denominator.  No official score is produced or claimed.
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
from aic6.coverage import (                                    # noqa: E402
    CoverageGate,
    CoverageState,
    audit_frames,
    legacy_copy_profile,
)
from aic6.segments import SegmentConstraint, parse_response    # noqa: E402
from aic6.timebase import (                                    # noqa: E402
    CfrTimeline,
    local_interval_to_absolute,
    select_frames_legacy_round_inclusive,
    select_frames_timestamp_halfopen,
)

RUN_ID_DEFAULT = "round6_p2_m3_20260918T0000Z"
CONSTRAINT = SegmentConstraint(0, 5)
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"
P2 = ROOT / "reports/round6_score_alignment/p2_joint_coverage"
BOOT = 10000
SEED = 20260918


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def weak_iou(pred_xywh, roi_xywh, height: int, tw: float, th: float) -> float:
    """Weak-IoU convention reproduced from weak_dev_pilot: h = min(w*th/tw, H)."""
    px, py, pw = pred_xywh
    gx, gy, gw = roi_xywh[:3]
    ph = min(pw * th / tw, float(height))
    gh = min(gw * th / tw, float(height))
    ix = max(0.0, min(px + pw, gx + gw) - max(px, gx))
    iy = max(0.0, min(py + ph, gy + gh) - max(py, gy))
    inter = ix * iy
    union = pw * ph + gw * gh - inter
    return inter / union if union > 1e-12 else 0.0


def bootstrap_ci(diffs: dict[str, float], groups: dict[str, str],
                 seed: int = SEED, draws: int = BOOT) -> tuple[float, float]:
    import random
    rng = random.Random(seed)
    by_group: dict[str, list[float]] = {}
    for vid, d in diffs.items():
        by_group.setdefault(groups[vid], []).append(d)
    keys = sorted(by_group)
    means = []
    for _ in range(draws):
        total, n = 0.0, 0
        for _k in keys:
            rows = by_group[_k]
            m = sum(rng.choice(rows) for _ in rows) / len(rows)
            total += m
            n += 1
        means.append(total / n)
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    return lo, hi


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "reports/round6_score_alignment/p2_joint_coverage"))
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    protected_before = provenance.snapshot_protected()
    pinned_problems = provenance.verify_pinned_protected_inputs()
    if pinned_problems:
        print(f"FAIL pinned inputs: {pinned_problems}", file=sys.stderr)
        return 2

    dev_temporal = load_jsonl(WEAK / "dev_temporal.jsonl")
    dev_frames = load_jsonl(WEAK / "dev_frames.jsonl")
    s2_rows = {row["video_id"]: row for row in load_jsonl(WEAK / "temporal_S2.jsonl")}
    gap_rows = load_jsonl(P2 / "gap_predictions.jsonl")
    gap_meta = json.loads((P2 / "gap_predictions.run.json").read_text(encoding="utf-8"))
    if sha256_file(P2 / "gap_predictions.jsonl") != gap_meta["output_sha256"]:
        print("FAIL: gap_predictions.jsonl hash mismatch", file=sys.stderr)
        return 2

    # youtube/source groups for the paired bootstrap
    groups = {row["video_id"]: row["youtube_id"] for row in dev_temporal}

    # frozen keyframe boxes per video (weak ROI = box source, never truth)
    frames_by_vid: dict[str, dict[int, dict]] = {}
    for frame in dev_frames:
        frames_by_vid.setdefault(frame["video_id"], {})[int(frame["clip_frame"])] = frame

    # per-clip geometry and both selections
    clip_meta: dict[str, dict] = {}
    for row in dev_temporal:
        vid = row["video_id"]
        frame0 = next(f for f in dev_frames if f["video_id"] == vid)
        fps = float(frame0["clip_fps"])
        width, height = int(frame0["source_width"]), int(frame0["source_height"])
        n_clip = int(math.floor(row["clip_end_sec"] * fps)) - int(math.ceil(row["clip_start_sec"] * fps)) + 1
        clip_meta[vid] = {"fps": fps, "n": n_clip, "width": width, "height": height,
                          "ws": float(row["clip_start_sec"]), "we": float(row["clip_end_sec"])}

    sel_new: dict[str, set[int]] = {}
    sel_old: dict[str, set[int]] = {}
    for vid, meta in clip_meta.items():
        s2 = s2_rows[vid]
        outcome = parse_response(s2["raw_output"], duration_sec=s2["clip_duration_sec"],
                                 constraint=CONSTRAINT)
        if not outcome.is_usable or not outcome.segments:
            continue
        fps, n = meta["fps"], meta["n"]
        timeline = CfrTimeline(fps=fps, n_frames=n)
        new, old = sel_new.setdefault(vid, set()), sel_old.setdefault(vid, set())
        for a_local, b_local in outcome.segments:
            _a, _b, origin = local_interval_to_absolute(
                a_local_sec=a_local, b_local_sec=b_local, window_start_sec=meta["ws"],
                fps=fps, n_frames=n, use_sampling_origin=True)
            new.update(select_frames_timestamp_halfopen(
                a_sec=a_local, b_sec=b_local, timeline=timeline, origin_frame=origin).frames)
            old.update(select_frames_legacy_round_inclusive(
                a_sec=meta["ws"] + a_local, b_sec=meta["ws"] + b_local,
                fps=fps, n_frames=n).frames)

    gap_by_key = {(row["video_id"], int(row["clip_frame"])): row for row in gap_rows}

    # ---------------- per-clip arm metrics -----------------------------------
    per_clip = []
    totals = {
        "new": {"selected": 0, "same_frame": 0, "real_inference": 0, "legacy_copy": 0,
                "invalid": 0},
        "legacy": {"selected": 0, "same_frame": 0, "legacy_copy": 0, "max_copy_distance": 0},
    }
    iou_new_frame: list[float] = []       # frame-level sparse weak IoU, NEW chain
    iou_legacy_frame: list[float] = []    # frame-level sparse weak IoU, LEGACY chain
    for vid in sorted(clip_meta, key=lambda v: int(v.split("_")[1])):
        meta = clip_meta[vid]
        frozen = frames_by_vid.get(vid, {})
        boxes = {f: item["weak_roi_xywh"][:3] for f, item in frozen.items()}
        frames_new = sorted(sel_new.get(vid, set()))

        # NEW chain: coverage audit + real inference for gaps
        audit = audit_frames(selected_frames=frames_new, source_boxes=boxes,
                             n_frames=meta["n"], shots=None, max_reuse_gap_frames=None)
        gate = CoverageGate(allow_bounded_within_shot=False).judge(audit)
        new_frame_iou = []
        real_calls = 0
        invalid_new = 0
        for row in audit.rows:
            f = row.frame
            if row.state == CoverageState.SAME_FRAME.value:
                pred = boxes[f]
                if f in frozen:
                    iou = weak_iou(pred, frozen[f]["weak_roi_xywh"], meta["height"], 9, 16)
                    new_frame_iou.append(iou)
            else:
                record = gap_by_key.get((vid, f))
                real_calls += 1
                if record is None or not record.get("output_valid"):
                    invalid_new += 1
                    new_frame_iou.append(0.0)
                    continue
                if f in frozen:
                    iou = weak_iou(record["box_xywh"], frozen[f]["weak_roi_xywh"],
                                   meta["height"], 9, 16)
                    new_frame_iou.append(iou)
        iou_new_frame.extend(new_frame_iou)
        totals["new"]["selected"] += len(frames_new)
        totals["new"]["same_frame"] += audit.counts[CoverageState.SAME_FRAME.value]
        totals["new"]["real_inference"] += real_calls
        totals["new"]["invalid"] += invalid_new

        # LEGACY chain: nearest old box anywhere in the clip
        legacy = legacy_copy_profile(selected_frames=frames_new, source_boxes=boxes,
                                     n_frames=meta["n"], shots=None)
        legacy_frame_iou = []
        legacy_invalid = 0
        for f in frames_new:
            if f in boxes:
                pred = boxes[f]
            else:
                position = min(boxes, key=lambda b: (abs(b - f), b)) if boxes else None
                pred = boxes[position] if position is not None else None
            if pred is None:
                legacy_invalid += 1
                legacy_frame_iou.append(0.0)
                continue
            if f in frozen:
                iou = weak_iou(pred, frozen[f]["weak_roi_xywh"], meta["height"], 9, 16)
                legacy_frame_iou.append(iou)
        iou_legacy_frame.extend(legacy_frame_iou)
        totals["legacy"]["selected"] += len(frames_new)
        totals["legacy"]["same_frame"] += legacy["n_same_frame"]
        totals["legacy"]["legacy_copy"] += legacy["n_copied"]
        totals["legacy"]["max_copy_distance"] = max(
            totals["legacy"]["max_copy_distance"], legacy["distance_max"] or 0)

        per_clip.append({
            "video_id": vid, "youtube_id": groups[vid],
            "n_selected": len(frames_new),
            "new_counts": audit.counts, "new_verdict": gate["verdict"],
            "new_real_calls": real_calls, "new_invalid": invalid_new,
            "new_frames_with_frozen_label": sum(1 for f in frames_new if f in frozen),
            "new_iou_sum_on_frozen": round(sum(new_frame_iou), 9),
            "legacy_copied": legacy["n_copied"],
            "legacy_max_distance": legacy["distance_max"],
            "legacy_iou_sum_on_frozen": round(sum(legacy_frame_iou), 9),
        })

    # paired per-clip mean IoU over *frozen frames actually selected* (sparse):
    # clips whose selection touches no frozen keyframe contribute nothing to the
    # sparse diagnostic and are counted separately.
    diffs = {}
    for clip in per_clip:
        if clip["new_frames_with_frozen_label"] > 0:
            n = clip["new_frames_with_frozen_label"]
            diffs[clip["video_id"]] = (clip["new_iou_sum_on_frozen"]
                                       - clip["legacy_iou_sum_on_frozen"]) / n
    lo, hi = bootstrap_ci(diffs, groups)
    mean_diff = sum(diffs.values()) / len(diffs) if diffs else None

    n_frozen_hit = sum(c["new_frames_with_frozen_label"] for c in per_clip)
    sparse_new = sum(iou_new_frame) / len(iou_new_frame) if iou_new_frame else None
    sparse_legacy = sum(iou_legacy_frame) / len(iou_legacy_frame) if iou_legacy_frame else None

    result = {
        "schema": "aic6_p2_m3_paired_comparison_v1",
        "run_id": args.run_id,
        "official_status": "INTERNAL_WEAK_DIAGNOSTIC_NOT_OFFICIAL_SCORE",
        "labels_are_weak_teacher": True,
        "temporal_fixed_to": "recorded round-6 S2 outputs on 82 frozen dev clips",
        "only_changed_component": "spatial box sourcing (the audited coverage gate)",
        "arms": {
            "NEW_CHAIN": "SAME_FRAME reuse + real unfused-model inference for every other "
                         "selected frame; no cross-shot copy; no unbounded copy; no center fallback",
            "LEGACY_CHAIN": "nearest old box anywhere in the clip (historical rule)",
        },
        "totals": totals,
        "gap_inference_cost": {
            "rows": gap_meta["rows"], "invalid": gap_meta["invalid"],
            "wall_seconds": gap_meta["total_wall_seconds"],
            "model_load_seconds": gap_meta["model_load_seconds"],
            "peak_memory_mib": gap_meta["peak_memory_mib"],
            "mean_per_frame_seconds": round(
                sum(r["seconds"] for r in gap_rows) / len(gap_rows), 3),
            "requests_sha256": gap_meta["requests_sha256"],
            "output_sha256": gap_meta["output_sha256"],
        },
        "sparse_weak_diagnostic": {
            "status": "SPARSE_DIAGNOSTIC",
            "frozen_keyframes_total": len(dev_frames),
            "frozen_keyframes_selected_by_s2": n_frozen_hit,
            "not_evaluated": len(dev_frames) - n_frozen_hit,
            "frame_mean_weak_iou_new_chain": round(sparse_new, 9) if sparse_new is not None else None,
            "frame_mean_weak_iou_legacy_chain": round(sparse_legacy, 9) if sparse_legacy is not None else None,
            "paired_clip_mean_diff_new_minus_legacy": (
                round(mean_diff, 9) if mean_diff is not None else None),
            "bootstrap_ci95": [round(lo, 9), round(hi, 9)],
            "paired_clips": len(diffs),
            "source_groups": len({groups[v] for v in diffs}),
            "bootstrap_seed": SEED, "bootstrap_draws": BOOT,
            "note": ("sparse: only frozen keyframes hit by the temporal selection can be "
                     "evaluated; unhit keyframes and unselected time are unverifiable. "
                     "This is NOT a joint score and NOT an official number."),
        },
        "per_clip": per_clip,
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }

    protected_after = provenance.snapshot_protected()
    problems = provenance.assert_protected_unchanged(protected_before, protected_after)
    result["protected_inputs_unchanged"] = not problems

    provenance.write_json(out_dir / f"{args.run_id}.json", result)
    print(f"OK: wrote {out_dir / (args.run_id + '.json')}")
    print(json.dumps(result["totals"], indent=1))
    print(json.dumps(result["sparse_weak_diagnostic"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
