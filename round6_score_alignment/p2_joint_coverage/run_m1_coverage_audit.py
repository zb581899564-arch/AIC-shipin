"""Milestone-1 runner: frame-level spatial coverage audit of the round-5 chain.

Rebuilds the round-5 temporal selection under the frozen TIMESTAMP_HALFOPEN
policy (the same frozen conventions as P1a), then classifies every selected
frame into the four coverage states against the recorded spatial base
(``qwen3vl_lora_reader_20260912/predictions.jsonl`` — a *box source*, never
ground truth).  Produces:

1. the per-frame four-state audit (no boxes invented, no frames dropped);
2. the historical contrast profile: what the legacy nearest-anywhere rule would
   have copied, with distances and declared-shot crossings;
3. a declared whole-video-shot variant with an explicitly declared gap limit
   (the only shot structure the recorded data supports without a shot detector).

No quality score, no ground truth, no test video content, no submission file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]          # HERE = <root>/round6_score_alignment/p2_joint_coverage
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import provenance                                    # noqa: E402
from aic6.compose import load_spatial_source, load_windows     # noqa: E402
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
    select_frames_timestamp_halfopen,
)

RUN_ID_DEFAULT = "round6_p2_m1_20260918T0000Z"
CONSTRAINT = SegmentConstraint(0, 5)
DECLARED_GAP_FRAMES = 30   # pre-declared round number (~1 s at 30 fps), not fitted from data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def code_manifest() -> dict:
    files = {}
    for path in sorted(list((HERE / "aic6").rglob("*.py")) + list((HERE / "tests").rglob("*.py"))
                       + [HERE / "run_m1_coverage_audit.py"]):
        if "__pycache__" in path.parts:
            continue
        files[str(path.relative_to(HERE)).replace("\\", "/")] = sha256_file(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "reports/round6_score_alignment/p2_joint_coverage"))
    parser.add_argument("--run-id", default=RUN_ID_DEFAULT)
    parser.add_argument("--rows-embedded", action="store_true",
                        help="embed per-frame rows for all videos (large); default keeps "
                             "per-video counts plus full rows only for the ten worst videos")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    protected_before = provenance.snapshot_protected()
    pinned_problems = provenance.verify_pinned_protected_inputs()
    if pinned_problems:
        print(f"FAIL: pinned protected inputs changed: {pinned_problems}", file=sys.stderr)
        return 2

    temporal_raw = provenance.PROTECTED_INPUTS["round5_temporal_raw"][0]
    spatial_base = provenance.PROTECTED_INPUTS["spatial_base_lora_reader"][0]

    requests, fps_by_video, n_frames_by_video = load_windows(temporal_raw)
    spatial_source = load_spatial_source(spatial_base)

    # ---- rebuild the frozen new-policy selection per video -------------------
    selection: dict[str, set[int]] = {}
    parse_states: dict[str, int] = {}
    for request in requests:
        vid = request.video_id
        fps = float(fps_by_video[vid])
        n_frames = int(n_frames_by_video[vid])
        outcome = parse_response(request.raw_output, duration_sec=request.duration_sec,
                                 constraint=CONSTRAINT)
        parse_states[outcome.state.value] = parse_states.get(outcome.state.value, 0) + 1
        if not outcome.is_usable or not outcome.segments:
            continue
        slot = selection.setdefault(vid, set())
        timeline = CfrTimeline(fps=fps, n_frames=n_frames)
        for a_local, b_local in outcome.segments:
            _a, _b, origin = local_interval_to_absolute(
                a_local_sec=a_local, b_local_sec=b_local, window_start_sec=request.start_sec,
                fps=fps, n_frames=n_frames, use_sampling_origin=True)
            slot.update(select_frames_timestamp_halfopen(
                a_sec=a_local, b_sec=b_local, timeline=timeline, origin_frame=origin).frames)

    # ---- four-state audit per video -----------------------------------------
    videos = []
    totals = {state.value: 0 for state in CoverageState}
    totals["n_selected"] = 0
    legacy_totals = {"n_copied": 0, "n_over_30_frames": 0, "n_over_300_frames": 0,
                     "n_crossing_declared_shot_boundary": 0}
    legacy_distances_all: list[int] = []

    for vid in sorted(selection, key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else v)):
        frames = sorted(selection[vid])
        n_frames = int(n_frames_by_video[vid])
        boxes = {int(f): [int(x) for x in b] for f, b in (spatial_source.get(vid) or {}).items()}

        # no shot detector exists for these videos: shots undeclared (fail closed)
        audit = audit_frames(selected_frames=frames, source_boxes=boxes, n_frames=n_frames,
                             shots=None, max_reuse_gap_frames=None)
        gate = CoverageGate(allow_bounded_within_shot=False).judge(audit)
        counts = audit.counts
        for state, n in counts.items():
            totals[state] += n
        totals["n_selected"] += len(frames)

        profile = legacy_copy_profile(selected_frames=frames, source_boxes=boxes,
                                      n_frames=n_frames, shots=None)
        legacy_totals["n_copied"] += profile["n_copied"]
        legacy_totals["n_over_30_frames"] += profile["n_over_30_frames"]
        legacy_totals["n_over_300_frames"] += profile["n_over_300_frames"]

        # declared whole-video shot with the pre-declared 30-frame limit: the only
        # declarable shot structure without a shot detector (audit variant)
        audit_shot = audit_frames(selected_frames=frames, source_boxes=boxes, n_frames=n_frames,
                                  shots=[(0, n_frames)], max_reuse_gap_frames=DECLARED_GAP_FRAMES)
        gate_shot = CoverageGate(allow_bounded_within_shot=True,
                                 max_reuse_gap_frames=DECLARED_GAP_FRAMES).judge(audit_shot)

        entry = {
            "video_id": vid,
            "n_selected": len(frames),
            "counts_no_shots": counts,
            "gate_no_shots": gate,
            "counts_single_declared_shot": audit_shot.counts,
            "gate_single_declared_shot": gate_shot,
            "legacy_contrast": profile,
        }
        embed_rows = args.rows_embedded or gate["counts"][CoverageState.NEEDS_INFERENCE.value] > 0 and len(frames) > 0
        if len(videos) < 10 or entry["counts_no_shots"][CoverageState.NEEDS_INFERENCE.value] > 0:
            entry["rows_no_shots_first_50"] = [row.as_dict() for row in audit.rows[:50]]
        videos.append(entry)

    for profile in (v["legacy_contrast"] for v in videos):
        legacy_totals["n_crossing_declared_shot_boundary"] += 0  # shots undeclared: N/A

    result = {
        "schema": "aic6_p2_m1_coverage_audit_v1",
        "run_id": args.run_id,
        "official_status": "NOT_OFFICIAL_SCORE",
        "structural_counts_only": True,
        "no_ground_truth_used": True,
        "no_quality_score_computed": True,
        "inputs": {
            "temporal_raw": str(temporal_raw.relative_to(ROOT)).replace("\\", "/"),
            "spatial_base": str(spatial_base.relative_to(ROOT)).replace("\\", "/"),
            "n_requests": len(requests),
            "n_videos_selected": len(selection),
            "parse_states": parse_states,
            "declared_gap_frames_single_shot_variant": DECLARED_GAP_FRAMES,
        },
        "totals": {
            **totals,
            "videos_with_needs_inference": sum(
                1 for v in videos
                if v["counts_no_shots"][CoverageState.NEEDS_INFERENCE.value] > 0),
            "videos_fully_resolved_no_shots": sum(
                1 for v in videos if v["gate_no_shots"]["deliverable"]),
            "videos_fully_resolved_single_declared_shot": sum(
                1 for v in videos if v["gate_single_declared_shot"]["deliverable"]),
        },
        "legacy_contrast_totals": legacy_totals,
        "gate_policy": {
            "no_shots": "same-frame only; any reuse refused (fail closed)",
            "single_declared_shot": "nearest within the one declared shot, <= 30 frames",
        },
        "videos": videos,
        "python": platform.python_version(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }

    protected_after = provenance.snapshot_protected()
    problems = provenance.assert_protected_unchanged(protected_before, protected_after)
    result["protected_inputs_unchanged"] = not problems
    result["protected_input_problems"] = problems

    payload_path = out_dir / f"{args.run_id}.json"
    provenance.write_json(payload_path, result)
    manifest = {
        "run_id": args.run_id,
        "code_files": code_manifest(),
        "protected_inputs_before": protected_before,
        "protected_inputs_after": protected_after,
        "output_sha256": sha256_file(payload_path),
    }
    provenance.write_json(out_dir / f"{args.run_id}.manifest.json", manifest)
    print(f"OK: wrote {payload_path}")
    print(json.dumps(result["totals"], indent=1))
    print(json.dumps(result["legacy_contrast_totals"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
