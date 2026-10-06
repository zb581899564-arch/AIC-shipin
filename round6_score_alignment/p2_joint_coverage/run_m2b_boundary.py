"""Milestone-2 runner part B: boundary case catalog (CPU tests with literals).

Exercises the delivery path on *named* synthetic edge cases with hand-computed
expectations, independent of the dev data:

* temporal endpoints: interval touching 0 and duration; sub-frame tail;
* duplicate frames in a prediction file (N_pred accounting);
* shot boundaries: reuse refused across a declared cut;
* missing boxes: no source -> UNRESOLVABLE, not a center-crop fallback;
* 9:16 vs 16:9 legal geometry, including the exact illegal 169-wide 9:16 box;
* parse states through the full compose path (VALID_EMPTY preserved, INVALID
  never silently repaired).

Runs on CPU in well under a second.
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

from aic6 import provenance                                        # noqa: E402
from aic6.compose import CompositionMode, WindowRequest, compose   # noqa: E402
from aic6.coverage import (                                        # noqa: E402
    CoverageGate,
    CoverageState,
    audit_frames,
    legacy_copy_profile,
)
from aic6.scoring import Box, box_from_xyw, load_predictions       # noqa: E402
from aic6.segments import SegmentConstraint, SegmentState, parse_response  # noqa: E402
from aic6.timebase import (                                        # noqa: E402
    CfrTimeline,
    local_interval_to_absolute,
    select_frames_legacy_round_inclusive,
    select_frames_timestamp_halfopen,
)

RUN_ID_DEFAULT = "round6_p2_m2b_20260918T0000Z"
CONSTRAINT = SegmentConstraint(0, 5)


def case(name: str, passed: bool, detail: dict) -> dict:
    return {"case": name, "pass": bool(passed), "detail": detail}


def run_cases() -> list[dict]:
    cases: list[dict] = []

    # --- temporal endpoints --------------------------------------------------
    timeline = CfrTimeline(fps=30.0, n_frames=300)
    sel = select_frames_timestamp_halfopen(a_sec=0.0, b_sec=300.0, timeline=timeline)
    cases.append(case("endpoint_full_clip", sel.frames == tuple(range(300)),
                      {"n": len(sel.frames), "first": sel.first_frame, "last": sel.last_frame}))
    sel = select_frames_timestamp_halfopen(a_sec=0.0, b_sec=1 / 30, timeline=timeline)
    cases.append(case("endpoint_single_frame_interval", sel.frames == (0,),
                      {"frames": sel.frames}))
    sel = select_frames_timestamp_halfopen(a_sec=10.0 - 1 / 90, b_sec=10.0, timeline=timeline)
    # [9.9889, 10.0) contains no frame timestamp: half-open rule returns EMPTY
    # (frame 300 would be at exactly 10.0 but is out of range) — this is the
    # documented half-open edge behaviour, not a dropped frame
    cases.append(case("endpoint_subframe_tail_below_one_frame_is_empty", sel.frames == (),
                      {"frames": sel.frames}))
    # 10.0 s is frame 300 -> out of range for a 300-frame video; only frames 0..299
    sel = select_frames_timestamp_halfopen(a_sec=299 / 30, b_sec=10.0, timeline=timeline)
    # [299/30, 10.0) holds exactly frame 299: the half-open rule keeps it while
    # the legacy round-inclusive rule would also have to clamp at 299
    cases.append(case("endpoint_halfopen_last_frame_only", sel.frames == (299,),
                      {"frames": sel.frames}))
    sel_legacy = select_frames_legacy_round_inclusive(a_sec=299 / 30, b_sec=10.0,
                                                      fps=30.0, n_frames=300)
    cases.append(case("endpoint_legacy_round_inclusive_last_frame", sel_legacy.frames == (299, 300)[:1],
                      {"frames": sel_legacy.frames}))

    # --- duplicates ----------------------------------------------------------
    audit = audit_frames(selected_frames=[5, 5, 5], source_boxes={5: [1, 1, 10]},
                         n_frames=100, shots=None)
    cases.append(case("duplicate_selection_deduped", audit.counts[CoverageState.SAME_FRAME.value] == 1,
                      dict(audit.counts)))

    # --- shot boundaries ------------------------------------------------------
    audit = audit_frames(selected_frames=[35, 39, 41], source_boxes={30: [0, 0, 50]},
                         n_frames=100, shots=[(0, 40), (40, 100)], max_reuse_gap_frames=30)
    ok = (audit.counts[CoverageState.SHOT_NEAREST.value] == 2
          and audit.counts[CoverageState.NEEDS_INFERENCE.value] == 1
          and audit.rows[2].shot == (40, 100))
    cases.append(case("shot_boundary_blocks_reuse", ok,
                      {"rows": [r.as_dict() for r in audit.rows]}))

    # --- missing boxes --------------------------------------------------------
    audit = audit_frames(selected_frames=[7], source_boxes={}, n_frames=100, shots=[(0, 100)],
                         max_reuse_gap_frames=30)
    ok = audit.counts[CoverageState.UNRESOLVABLE.value] == 1 and audit.rows[0].box is None
    cases.append(case("missing_source_unresolvable_not_centercrop", ok,
                      {"rows": [r.as_dict() for r in audit.rows]}))

    audit = audit_frames(selected_frames=[7], source_boxes={3: [0, 0, 50]}, n_frames=100,
                         shots=None)
    cases.append(case("no_shot_info_needs_inference", audit.counts[CoverageState.NEEDS_INFERENCE.value] == 1,
                      {"rows": [r.as_dict() for r in audit.rows]}))

    # --- geometry --------------------------------------------------------------
    box = box_from_xyw([183, 0, 168], ratio_wh=[9, 16], width=534, height=300, location="c1")
    ok = abs(box.h - 298.6666666666667) < 1e-9
    cases.append(case("geometry_9x16_168_legal", ok, {"h": box.h}))
    try:
        box_from_xyw([183, 0, 169], ratio_wh=[9, 16], width=534, height=300, location="c2")
        illegal_raised = False
    except ValueError:
        illegal_raised = True
    cases.append(case("geometry_9x16_169_rejected", illegal_raised, {}))
    box = box_from_xyw([0, 875, 720], ratio_wh=[16, 9], width=720, height=1280, location="c3")
    ok = abs(box.h - 405.0) < 1e-9 and box.y + box.h <= 1280 + 1e-9
    cases.append(case("geometry_16x9_720x405_legal", ok, {"h": box.h, "y_plus_h": box.y + box.h}))

    # --- parse states through compose -------------------------------------------
    def window(raw: str) -> WindowRequest:
        return WindowRequest(video_id="9", index=0, start_sec=0.0, end_sec=10.0,
                             raw_output=raw)

    report = compose(requests=[window('{"segments":[]}')], spatial_source={},
                     fps_by_video={"9": 30.0}, n_frames_by_video={"9": 300},
                     constraint=CONSTRAINT, mode=CompositionMode.TRACEABLE)
    ok = (report["status"] == "OK_DELIVERABLE" and report["totals"]["empty_windows"] == 1
          and report["totals"]["frames_selected"] == 0)
    cases.append(case("compose_legal_empty_is_success", ok,
                      {"status": report["status"], "totals": report["totals"]}))

    report = compose(requests=[window("garbage")], spatial_source={},
                     fps_by_video={"9": 30.0}, n_frames_by_video={"9": 300},
                     constraint=CONSTRAINT, mode=CompositionMode.TRACEABLE)
    ok = report["status"] == "FAILED_INVALID_WINDOWS" and report["totals"]["invalid_windows"] == 1
    cases.append(case("compose_invalid_stays_failed", ok,
                      {"status": report["status"]}))

    report = compose(requests=[window('{"segments":[[1.0,3.0]]}')],
                     spatial_source={"9": {}},
                     fps_by_video={"9": 30.0}, n_frames_by_video={"9": 300},
                     constraint=CONSTRAINT, mode=CompositionMode.TRACEABLE)
    ok = (report["status"] == "NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE"
          and report["totals"]["needs_spatial_inference"]
          == report["totals"]["frames_selected"])
    cases.append(case("compose_all_frames_need_inference", ok,
                      {"status": report["status"], "totals": report["totals"]}))

    # --- strict prediction loader ----------------------------------------------
    tmp = Path(provenance.ROOT) / "reports/round6_score_alignment/p2_joint_coverage/_tmp_dup.jsonl"
    index = {"9": {"video_id": "9", "targetRatioWH": [9, 16], "width": 534, "height": 300,
                   "n_frames": 300}}
    rows = [
        {"video_id": "9", "targetRatioWH": [9, 16],
         "predictions": [{"frame": 5, "bboxes": [183, 0, 168]},
                         {"frame": 5, "bboxes": [100, 0, 168]},
                         {"frame": 400, "bboxes": [0, 0, 168]}]},
    ]
    tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    loaded = load_predictions(tmp, index)
    ok = (not loaded.ok
          and loaded.duplicate_frames["9"] == 1
          and loaded.n_pred_by_video["9"] == 3
          and len(loaded.rows["9"]) == 1)
    cases.append(case("loader_duplicate_counted_out_of_range_reported", ok,
                      {"validation": loaded.validation, "n_pred": loaded.n_pred_by_video["9"],
                       "duplicates": loaded.duplicate_frames}))
    tmp.unlink()

    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "reports/round6_score_alignment/p2_joint_coverage"))
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    cases = run_cases()
    failures = [c for c in cases if not c["pass"]]
    result = {
        "schema": "aic6_p2_m2b_boundary_cases_v1",
        "run_id": args.run_id,
        "official_status": "NOT_OFFICIAL_SCORE",
        "counts": {"total": len(cases), "pass": len(cases) - len(failures), "fail": len(failures)},
        "cases": cases,
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    provenance.write_json(out_dir / f"{args.run_id}.json", result)
    print(f"OK: {result['counts']}")
    for c in cases:
        if not c["pass"]:
            print("FAIL:", c["case"], json.dumps(c["detail"])[:300])
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
