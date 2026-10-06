"""Milestone-2d runner (supervisor fix 2): real-inference frame composition.

Composes the *delivery-shape* per-frame prediction file for the 82 frozen dev
clips from already-frozen inputs, without any new inference:

* `SAME_FRAME` rows reuse the frozen weak-ROI box at the identical frame and
  are flagged ``source: WEAK_ROI_SAME_FRAME`` — a **link-check only** input
  that is NOT obtainable at deployment time (the weak ROI is a label);
* `NEEDS_INFERENCE` rows use the recorded real unfused-model output from
  ``gap_predictions.jsonl`` (flagged ``source: REAL_INFERENCE``).

The composed file is then re-validated with the strict loader (video ids,
frame numbers, box legality against source geometry, duplicates, missing,
empty results) and hashed.  The raw ``gap_predictions.jsonl`` is never
modified.  No submission file for the competition is produced; this file
exists so the supervisor can verify the real delivery chain end to end.
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
from aic6.timebase import (                                    # noqa: E402
    CfrTimeline,
    local_interval_to_absolute,
    select_frames_timestamp_halfopen,
)

RUN_ID_DEFAULT = "round6_p2_m2d_20260918T0000Z"
CONSTRAINT = SegmentConstraint(0, 5)
WEAK = ROOT / "reports/round6_score_alignment/weak_dev_pilot"
P2 = ROOT / "reports/round6_score_alignment/p2_joint_coverage"


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
    out_dir = Path(args.out_dir)
    started = time.monotonic()

    dev_temporal = load_jsonl(WEAK / "dev_temporal.jsonl")
    dev_frames = load_jsonl(WEAK / "dev_frames.jsonl")
    s2_rows = {row["video_id"]: row for row in load_jsonl(WEAK / "temporal_S2.jsonl")}
    gap_rows = load_jsonl(P2 / "gap_predictions.jsonl")
    gap_meta = json.loads((P2 / "gap_predictions.run.json").read_text(encoding="utf-8"))
    if sha256_file(P2 / "gap_predictions.jsonl") != gap_meta["output_sha256"]:
        print("FAIL: gap_predictions.jsonl hash mismatch", file=sys.stderr)
        return 2
    requests = load_jsonl(P2 / "p2_infer_requests.jsonl")
    requests_sha = sha256_file(P2 / "p2_infer_requests.jsonl")

    frozen: dict[str, dict[int, dict]] = {}
    for frame in dev_frames:
        frozen.setdefault(frame["video_id"], {})[int(frame["clip_frame"])] = frame

    clip_meta: dict[str, dict] = {}
    for row in dev_temporal:
        vid = row["video_id"]
        frame0 = next(f for f in dev_frames if f["video_id"] == vid)
        fps = float(frame0["clip_fps"])
        clip_meta[vid] = {
            "fps": fps,
            "n": int(math.floor(row["clip_end_sec"] * fps))
                - int(math.ceil(row["clip_start_sec"] * fps)) + 1,
            "width": int(frame0["source_width"]), "height": int(frame0["source_height"]),
            "ws": float(row["clip_start_sec"]),
        }

    # rebuild the frozen selection and classify with the FIXED audit
    gap_by_key = {(row["video_id"], int(row["clip_frame"])): row for row in gap_rows}
    composed: dict[str, dict[int, dict]] = {}
    coverage_counts = {state.value: 0 for state in CoverageState}
    missing_real: list[str] = []
    for vid, meta in clip_meta.items():
        s2 = s2_rows[vid]
        outcome = parse_response(s2["raw_output"], duration_sec=s2["clip_duration_sec"],
                                 constraint=CONSTRAINT)
        frames: set[int] = set()
        if outcome.is_usable and outcome.segments:
            timeline = CfrTimeline(fps=meta["fps"], n_frames=meta["n"])
            for a_local, b_local in outcome.segments:
                _a, _b, origin = local_interval_to_absolute(
                    a_local_sec=a_local, b_local_sec=b_local, window_start_sec=meta["ws"],
                    fps=meta["fps"], n_frames=meta["n"], use_sampling_origin=True)
                frames.update(select_frames_timestamp_halfopen(
                    a_sec=a_local, b_sec=b_local, timeline=timeline, origin_frame=origin).frames)
        boxes = {f: item["weak_roi_xywh"][:3] for f, item in frozen.get(vid, {}).items()}
        audit = audit_frames(selected_frames=sorted(frames), source_boxes=boxes,
                             n_frames=meta["n"], shots=None, max_reuse_gap_frames=None)
        for state, n in audit.counts.items():
            coverage_counts[state] += n
        slot = composed.setdefault(vid, {})
        for row in audit.rows:
            if row.state == CoverageState.SAME_FRAME.value:
                slot[row.frame] = {"box_xyw": [int(v) for v in row.box],
                                   "source": "WEAK_ROI_SAME_FRAME"}
            else:
                record = gap_by_key.get((vid, row.frame))
                if record is None or not record.get("output_valid") or not record.get("box_xywh"):
                    missing_real.append(f"{vid}:{row.frame}")
                    continue
                slot[row.frame] = {"box_xyw": [int(v) for v in record["box_xywh"]],
                                   "source": "REAL_INFERENCE"}

    out_path = out_dir / f"{args.run_id}.real_composed_predictions.jsonl"
    with out_path.open("w", encoding="utf-8") as stream:
        for vid in sorted(clip_meta, key=lambda v: int(v.split("_")[1])):
            meta = clip_meta[vid]
            preds = [{"frame": int(f), "bboxes": list(item["box_xyw"]),
                      "source": item["source"]}
                     for f, item in sorted(slot.items())]
            stream.write(json.dumps({"video_id": vid, "targetRatioWH": [9, 16],
                                     "predictions": preds}, ensure_ascii=False) + "\n")

    # strict re-validation of the composed file (source field is metadata, the
    # loader checks ids / frames / legality / duplicates / missing)
    index = {vid: {"video_id": vid, "targetRatioWH": [9.0, 16.0],
                   "width": meta["width"], "height": meta["height"],
                   "n_frames": meta["n"]}
             for vid, meta in clip_meta.items()}
    loaded = load_predictions(out_path, index)
    n_boxes = sum(len(v) for v in loaded.rows.values())
    source_counts = {"WEAK_ROI_SAME_FRAME": 0, "REAL_INFERENCE": 0}
    for line in out_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        for pred in json.loads(line)["predictions"]:
            source_counts[pred["source"]] = source_counts.get(pred["source"], 0) + 1

    # expected-universe check: every request row must appear exactly once in the
    # composed file (856 real + 7 same-frame), no frame invented or dropped
    expected_keys = {(r["video_id"], int(r["clip_frame"])) for r in requests}
    composed_keys = {(vid, f) for vid, slot in composed.items() for f in slot}
    n_selected_total = coverage_counts["SAME_FRAME"] + coverage_counts["NEEDS_INFERENCE"] \
        + coverage_counts["UNRESOLVABLE"]

    result = {
        "schema": "aic6_p2_m2d_real_composition_v1",
        "run_id": args.run_id,
        "official_status": "NOT_OFFICIAL_SCORE",
        "inputs": {
            "gap_predictions_sha256": sha256_file(P2 / "gap_predictions.jsonl"),
            "requests_sha256": requests_sha,
        },
        "coverage_counts_of_selection": coverage_counts,
        "n_selected_total": n_selected_total,
        "composed": {
            "path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(out_path),
            "n_boxes": n_boxes,
            "source_counts": source_counts,
            "strict_validation_ok": loaded.ok,
            "n_issue_codes": loaded.validation["n_issue_codes"],
            "issues_first_10": loaded.validation["issues"][:10],
            "missing_real_inference_rows": missing_real[:20],
            "n_missing_real": len(missing_real),
        },
        "universe_check": {
            "expected_keys": len(expected_keys),
            "composed_keys": len(composed_keys),
            "exact_match": expected_keys == composed_keys,
        },
        "notes": [
            "WEAK_ROI_SAME_FRAME boxes reuse the frozen weak ROI at the identical frame: "
            "a LINK CHECK ONLY, not obtainable at deployment time",
            "REAL_INFERENCE boxes are the recorded unfused-model outputs; the raw "
            "gap_predictions.jsonl is left untouched",
            "this is a dev-only delivery-shape file, never a competition submission",
        ],
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    provenance.write_json(out_dir / f"{args.run_id}.json", result)
    print(f"OK: wrote {out_dir / (args.run_id + '.json')}")
    print(json.dumps({k: result[k] for k in ("coverage_counts_of_selection", "composed",
                                             "universe_check")}, indent=1))
    return 0 if (loaded.ok and not missing_real
                 and expected_keys == composed_keys) else 1


if __name__ == "__main__":
    sys.exit(main())
