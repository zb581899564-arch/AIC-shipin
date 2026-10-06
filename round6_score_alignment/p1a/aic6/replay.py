"""CPU-only historical replay and convention comparison.

What this module does
---------------------
1. Rebuilds the recorded round-5 selection under ``LEGACY_ROUND_INCLUSIVE`` with
   the legacy nearest-box rule and compares it item by item with the packaged
   ``predictions.jsonl`` (frames *and* boxes).
2. Re-parses all recorded window texts with the three-state parser and compares
   the result with the recorded ``parsed_segments``.
3. Recomputes the same windows under the new ``TIMESTAMP_HALFOPEN`` policy (with
   the real sampling-origin frame) and reports the frame-set differences.
4. Runs the new traceable composer over the same windows to count frames whose
   spatial box would have to be re-inferred.

What this module does not do
----------------------------
No accuracy, no "temporal upper bound", no ground truth, no submission-shaped
output.  The recorded 174-row package is a *prediction*, never a reference; the
spatial source is a *box source*, never truth.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .compose import (
    CompositionMode,
    ShotMap,
    WindowRequest,
    compose,
    load_spatial_source,
    load_windows,
)
from .segments import SegmentConstraint, parse_response
from .timebase import (
    CfrTimeline,
    TimeConvention,
    local_interval_to_absolute,
    select_frames_legacy_ceil_halfopen,
    select_frames_legacy_round_inclusive,
    select_frames_timestamp_halfopen,
)


def _intervals(frames: Sequence[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for frame in sorted(int(f) for f in frames):
        if runs and frame == runs[-1][1] + 1:
            runs[-1][1] = frame
        else:
            runs.append([frame, frame])
    return runs


def _percentile(values: Sequence[float], p: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(round(p * (len(ordered) - 1)))))]


def load_packaged_predictions(path: Path | str) -> dict:
    """Read a recorded package as ``{video_id: {frame: [x, y, w]}}``."""
    out: dict[str, dict[int, list]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        vid = str(record["video_id"])
        out[vid] = {int(p["frame"]): [int(v) for v in p["bboxes"]]
                    for p in record.get("predictions") or []}
    return out


def replay_legacy_composition(
    *,
    requests: Sequence[WindowRequest],
    spatial_source: Mapping[str, Mapping[int, Sequence[int]]],
    fps_by_video: Mapping[str, float],
    n_frames_by_video: Mapping[str, int],
    constraint: SegmentConstraint,
    packaged: Mapping[str, Mapping[int, Sequence[int]]],
) -> dict:
    """Legacy rule replay; every frame and every box must match the package."""
    report = compose(requests=requests, spatial_source=spatial_source,
                     fps_by_video=fps_by_video, n_frames_by_video=n_frames_by_video,
                     constraint=constraint, mode=CompositionMode.LEGACY_REPLAY,
                     shot_map=None, legacy_invalid_fallback=True)

    videos: list[dict] = []
    identical = 0
    total_frames = 0
    total_box_mismatch = 0
    total_missing = 0
    total_extra = 0
    for entry in report["videos"]:
        vid = entry["video_id"]
        produced = {int(f["frame"]): f["box"] for f in entry["frames"]}
        expected = {int(k): list(v) for k, v in (packaged.get(vid) or {}).items()}
        missing = sorted(set(expected) - set(produced))
        extra = sorted(set(produced) - set(expected))
        box_mismatch = sorted(f for f in (set(expected) & set(produced))
                              if [int(x) for x in produced[f]] != [int(x) for x in expected[f]])
        total_frames += len(expected)
        total_box_mismatch += len(box_mismatch)
        total_missing += len(missing)
        total_extra += len(extra)
        if not missing and not extra and not box_mismatch:
            identical += 1
        videos.append({
            "video_id": vid,
            "packaged_frames": len(expected), "replayed_frames": len(produced),
            "missing_in_replay": len(missing), "extra_in_replay": len(extra),
            "box_mismatches": len(box_mismatch),
            "first_box_mismatch_example": (
                {"frame": box_mismatch[0], "packaged": expected[box_mismatch[0]],
                 "replayed": produced[box_mismatch[0]]} if box_mismatch else None),
            "intervals_match": _intervals(expected) == _intervals(produced),
        })
    return {
        "mode": "legacy_replay",
        "status": report["status"],
        "deliverable": report["deliverable"],
        "rule": ("legacy round-inclusive seconds->frame plus nearest-old-box anywhere in the "
                 "video (historical round-5 rule)"),
        "videos_total": len(report["videos"]),
        "videos_identical_including_boxes": identical,
        "videos_mismatched": len(report["videos"]) - identical,
        "packaged_frame_count": total_frames,
        "frame_count_mismatches": total_missing + total_extra,
        "box_mismatch_count": total_box_mismatch,
        "legacy_fallbacks_used": report["totals"].get("invalid_windows", 0),
        "invalid_windows": report["totals"]["invalid_windows"],
        "empty_windows": report["totals"]["empty_windows"],
        "needs_spatial_inference": report["totals"]["needs_spatial_inference"],
        "per_video": videos,
    }


def parse_consistency(
    *,
    requests: Sequence[WindowRequest],
    recorded: Mapping[str, Sequence[Mapping]],
    constraint: SegmentConstraint,
) -> dict:
    """Re-parse recorded window text and compare with the recorded parse result."""
    per_window: list[dict] = []
    states = Counter()
    matched = 0
    for request in requests:
        key = f"{request.video_id}#{request.index}"
        outcome = parse_response(request.raw_output, duration_sec=request.duration_sec,
                                 constraint=constraint)
        states[outcome.state.value] += 1
        reference = recorded.get(key)
        if reference is None:
            per_window.append({"window": key, "state": outcome.state.value,
                               "recorded": None, "match": None,
                               "note": "no recorded parse for this window key"})
            continue
        recorded_valid = bool(reference.get("output_valid"))
        recorded_segments = reference.get("parsed_segments")
        new_segments = [list(s) for s in outcome.segments]
        same_state = (outcome.state.value == "VALID_NONEMPTY") == recorded_valid
        if recorded_valid and recorded_segments is not None:
            same_segments = (len(recorded_segments) == len(new_segments)
                             and all(abs(a - c) < 1e-6 and abs(b - d) < 1e-6
                                     for (a, b), (c, d) in zip(recorded_segments, new_segments)))
        else:
            same_segments = recorded_segments is None
        ok = bool(same_state and same_segments)
        matched += int(ok)
        per_window.append({
            "window": key, "state": outcome.state.value,
            "recorded_output_valid": recorded_valid,
            "recorded_segments": recorded_segments, "new_segments": new_segments,
            "same_validity": same_state, "same_segments": same_segments, "match": ok,
            "decode_path": outcome.decode_path,
        })
    return {
        "windows": len(requests),
        "windows_matching_recorded_parse": matched,
        "state_counts": dict(states),
        "rules": "same duration bound, same 1e-3 tolerance, same 4-decimal quantisation, "
                 "same overlap warning semantics, empty list is now VALID_EMPTY not a failure",
        "per_window": per_window,
    }


def convention_diff(
    *,
    requests: Sequence[WindowRequest],
    fps_by_video: Mapping[str, float],
    n_frames_by_video: Mapping[str, int],
    constraint: SegmentConstraint,
    legacy_convention: str = TimeConvention.LEGACY_ROUND_INCLUSIVE.value,
) -> dict:
    """Frame-set difference between the new policy and one legacy policy."""
    per_video: dict[str, dict] = {}
    origin_offsets: list[float] = []
    for request in requests:
        vid = request.video_id
        fps = float(fps_by_video[vid])
        n_frames = int(n_frames_by_video[vid])
        timeline = CfrTimeline(fps=fps, n_frames=n_frames)
        outcome = parse_response(request.raw_output, duration_sec=request.duration_sec,
                                 constraint=constraint)
        if outcome.state.value != "VALID_NONEMPTY":
            continue
        slot = per_video.setdefault(vid, {"video_id": vid, "new": set(), "legacy": set()})
        for a_local, b_local in outcome.segments:
            _a_abs, _b_abs, origin = local_interval_to_absolute(
                a_local_sec=a_local, b_local_sec=b_local, window_start_sec=request.start_sec,
                fps=fps, n_frames=n_frames, use_sampling_origin=True)
            origin_offsets.append(origin / fps - request.start_sec)
            new_selection = select_frames_timestamp_halfopen(
                a_sec=a_local, b_sec=b_local, timeline=timeline, origin_frame=origin)
            if legacy_convention == TimeConvention.LEGACY_ROUND_INCLUSIVE.value:
                legacy_selection = select_frames_legacy_round_inclusive(
                    a_sec=request.start_sec + a_local, b_sec=request.start_sec + b_local,
                    fps=fps, n_frames=n_frames)
            elif legacy_convention == TimeConvention.LEGACY_CEIL_HALFOPEN.value:
                legacy_selection = select_frames_legacy_ceil_halfopen(
                    a_sec=request.start_sec + a_local, b_sec=request.start_sec + b_local,
                    fps=fps, n_frames=n_frames)
            else:
                raise ValueError(f"unsupported legacy convention {legacy_convention!r}")
            slot["new"].update(new_selection.frames)
            slot["legacy"].update(legacy_selection.frames)

    rows = []
    added_total = removed_total = 0
    for vid, slot in sorted(per_video.items(), key=lambda kv: (not kv[0].isdigit(), kv[0])):
        added = sorted(slot["new"] - slot["legacy"])
        removed = sorted(slot["legacy"] - slot["new"])
        added_total += len(added)
        removed_total += len(removed)
        rows.append({
            "video_id": vid,
            "new_policy_frames": len(slot["new"]), "legacy_policy_frames": len(slot["legacy"]),
            "frames_added_by_new_policy": len(added), "frames_removed_by_new_policy": len(removed),
            "first_added_examples": added[:5], "first_removed_examples": removed[:5],
        })
    return {
        "comparison": f"TIMESTAMP_HALFOPEN (new, sampling-frame origin) vs {legacy_convention}",
        "videos_compared": len(rows),
        "frames_new_policy": sum(r["new_policy_frames"] for r in rows),
        "frames_legacy_policy": sum(r["legacy_policy_frames"] for r in rows),
        "frames_added_total": added_total,
        "frames_removed_total": removed_total,
        "videos_with_identical_frame_sets": sum(
            1 for r in rows if r["frames_added_by_new_policy"] == 0
            and r["frames_removed_by_new_policy"] == 0),
        "origin_offset_sec": {
            "n_intervals": len(origin_offsets),
            "min": round(min(origin_offsets), 6) if origin_offsets else None,
            "max": round(max(origin_offsets), 6) if origin_offsets else None,
            "n_nonzero": sum(1 for x in origin_offsets if abs(x) > 1e-9),
            "p50": round(_percentile(origin_offsets, 0.5), 6) if origin_offsets else None,
            "p90": round(_percentile(origin_offsets, 0.9), 6) if origin_offsets else None,
        },
        "rule_note": ("the new policy measures the interval from the frame the model actually "
                      "saw at local time zero (ceil(window_start*fps)/fps), the legacy policy "
                      "measured it from the nominal window start"),
        "per_video": rows,
    }


def spatial_gap_audit(
    *,
    requests: Sequence[WindowRequest],
    spatial_source: Mapping[str, Mapping[int, Sequence[int]]],
    fps_by_video: Mapping[str, float],
    n_frames_by_video: Mapping[str, int],
    constraint: SegmentConstraint,
    shot_map: Optional[ShotMap] = None,
    max_shot_nearest_gap_frames: Optional[int] = None,
) -> dict:
    """Count frames the traceable mode refuses to auto-fill, with distance context."""
    traceable = compose(requests=requests, spatial_source=spatial_source,
                        fps_by_video=fps_by_video, n_frames_by_video=n_frames_by_video,
                        constraint=constraint, mode=CompositionMode.TRACEABLE,
                        shot_map=shot_map, allow_within_shot_nearest=shot_map is not None,
                        max_shot_nearest_gap_frames=max_shot_nearest_gap_frames)
    legacy = compose(requests=requests, spatial_source=spatial_source,
                     fps_by_video=fps_by_video, n_frames_by_video=n_frames_by_video,
                     constraint=constraint, mode=CompositionMode.LEGACY_REPLAY,
                     shot_map=None)

    gaps = []
    legacy_distances = []
    for entry in traceable["videos"]:
        vid = entry["video_id"]
        fps = float(fps_by_video[vid])
        for frame in entry["frames"]:
            if frame["provenance"] == "NEEDS_SPATIAL_INFERENCE":
                gaps.append({"video_id": vid, "frame": frame["frame"],
                             "reason": frame["detail"].get("reason")})
    for entry in legacy["videos"]:
        for frame in entry["frames"]:
            if frame["provenance"] == "SOURCE_LEGACY_NEAREST":
                legacy_distances.append(frame["detail"]["distance"])

    per_video_gap = Counter(g["video_id"] for g in gaps)
    return {
        "traceable_mode": {
            "status": traceable["status"],
            "deliverable": traceable["deliverable"],
            "status_reason": traceable["status_reason"],
            "shot_map_provided": shot_map is not None,
            "declared_max_shot_nearest_gap_frames": max_shot_nearest_gap_frames,
            "notes": ("without a declared shot map the new mode never invents a box for a frame "
                      "the spatial source never saw"),
            "frames_selected": traceable["totals"]["frames_selected"],
            "resolved_frames": traceable["totals"]["resolved_frames"],
            "same_frame": traceable["totals"]["same_frame"],
            "shot_nearest": traceable["totals"]["shot_nearest"],
            "needs_spatial_inference": traceable["totals"]["needs_spatial_inference"],
            "videos_with_gaps": len(per_video_gap),
            "worst_videos": [{"video_id": v, "gap_frames": n}
                             for v, n in per_video_gap.most_common(10)],
        },
        "legacy_mode_for_contrast": {
            "status": legacy["status"],
            "deliverable": legacy["deliverable"],
            "frames_selected": legacy["totals"]["frames_selected"],
            "legacy_nearest_copies": legacy["totals"]["legacy_nearest"],
            "copy_distance_frames": {
                "min": min(legacy_distances) if legacy_distances else None,
                "p50": _percentile(legacy_distances, 0.5),
                "p90": _percentile(legacy_distances, 0.9),
                "max": max(legacy_distances) if legacy_distances else None,
                "n_gt_30_frames": sum(1 for d in legacy_distances if d > 30),
            },
            "note": "the historical rule fills these frames anyway; the new mode reports them",
        },
        "no_quality_score": True,
    }
