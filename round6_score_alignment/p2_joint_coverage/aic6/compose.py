"""Composition of selected frames with *traceable* spatial provenance.

New mode (``traceable``)
    Every selected frame gets an explicit provenance:

    ``SOURCE_SAME_FRAME``          the spatial source has a box at exactly that frame
    ``SOURCE_SHOT_NEAREST``        the frame lies inside a *declared* shot that
                                   contains spatial source frames; the box is
                                   COPIED from the nearest source frame within
                                   that same shot (nearest-box copy, explicitly
                                   NOT linear interpolation) and the distance is
                                   recorded
    ``NEEDS_SPATIAL_INFERENCE``    no same-frame and no declared within-shot source.
                                   The frame is reported with ``box: null``; it is
                                   never silently dropped, never copied across a
                                   shot boundary, never copied at unbounded
                                   distance and never taken from ground truth.

    Any numeric distance limit must be declared by the caller as a finite
    positive integer.  Nothing here is fitted from test statistics, and no new
    interpolation algorithm is implemented.

Legacy mode (``legacy_replay``)
    Reproduces the historical "nearest old box anywhere in the video" rule and is
    used *only* to replay recorded history.  It is never a delivery path.

No submission-format file is produced by this module.
"""
from __future__ import annotations

import bisect
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .segments import SegmentState, parse_response, SegmentConstraint, build_prompt
from .timebase import (
    CfrTimeline,
    FrameSelection,
    TimeConvention,
    local_interval_to_absolute,
    select_frames_legacy_round_inclusive,
    select_frames_timestamp_halfopen,
)


class SpatialProvenance(str, Enum):
    SOURCE_SAME_FRAME = "SOURCE_SAME_FRAME"
    SOURCE_SHOT_NEAREST = "SOURCE_SHOT_NEAREST"
    NEEDS_SPATIAL_INFERENCE = "NEEDS_SPATIAL_INFERENCE"
    SOURCE_LEGACY_NEAREST = "SOURCE_LEGACY_NEAREST"


class CompositionMode(str, Enum):
    TRACEABLE = "traceable"
    LEGACY_REPLAY = "legacy_replay"


class CompositionStatus(str, Enum):
    """Top-level outcome of one composition run."""

    OK_DELIVERABLE = "OK_DELIVERABLE"
    NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE = "NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE"
    FAILED_INVALID_WINDOWS = "FAILED_INVALID_WINDOWS"
    LEGACY_REPLAY_COMPLETED = "LEGACY_REPLAY_COMPLETED"


#: exit codes for callers (CLI / runner); 0 means "succeeded and deliverable"
COMPOSITION_EXIT_CODES = {
    CompositionStatus.OK_DELIVERABLE.value: 0,
    CompositionStatus.FAILED_INVALID_WINDOWS.value: 2,
    CompositionStatus.NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE.value: 4,
    CompositionStatus.LEGACY_REPLAY_COMPLETED.value: 0,
}


class CompositionError(RuntimeError):
    pass


def validate_shot_nearest_gap(value: Any) -> Optional[int]:
    """A declared within-shot copy limit must be a finite positive integer.

    Floats (including NaN/Infinity), bools and strings are refused: a NaN limit
    would silently disable the bound, because every comparison against NaN is
    False.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise CompositionError(
            f"max_shot_nearest_gap_frames must be a non-bool positive integer, got {value!r}")
    if value <= 0:
        raise CompositionError(
            f"max_shot_nearest_gap_frames must be positive, got {value!r}")
    return int(value)


@dataclass(frozen=True)
class ShotMap:
    """Declared shot boundaries ``[start_frame, end_frame)``, per video.

    Shots are *input*, not detected here: this module implements no shot
    detection model.
    """

    shots_by_video: Mapping[str, tuple[tuple[int, int], ...]]

    def __post_init__(self):
        for video_id, shots in self.shots_by_video.items():
            previous_end = None
            for start, end in shots:
                if start < 0 or end <= start:
                    raise CompositionError(f"{video_id}: invalid shot [{start},{end})")
                if previous_end is not None and start < previous_end:
                    raise CompositionError(f"{video_id}: shots overlap at [{start},{end})")
                previous_end = end

    def shots_for(self, video_id: str) -> tuple[tuple[int, int], ...]:
        return tuple(self.shots_by_video.get(video_id, ()))

    def shot_of(self, video_id: str, frame: int) -> Optional[tuple[int, int]]:
        for shot in self.shots_for(video_id):
            if shot[0] <= frame < shot[1]:
                return shot
        return None


@dataclass(frozen=True)
class WindowRequest:
    """One recorded window to be composed."""

    video_id: str
    index: int
    start_sec: float
    end_sec: float
    raw_output: str

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


def _nearest(candidates: Sequence[int], frame: int) -> int:
    i = bisect.bisect_left(candidates, frame)
    options = list(candidates[max(0, i - 1):min(len(candidates), i + 1)])
    if not options:
        raise CompositionError(f"no candidate frames near {frame}")
    return min(options, key=lambda x: (abs(x - frame), x))


def compose(
    *,
    requests: Sequence[WindowRequest],
    spatial_source: Mapping[str, Mapping[int, Sequence[int]]],
    fps_by_video: Mapping[str, float],
    n_frames_by_video: Mapping[str, int],
    constraint: SegmentConstraint,
    mode: CompositionMode,
    shot_map: Optional[ShotMap] = None,
    allow_within_shot_nearest: bool = True,
    max_shot_nearest_gap_frames: Optional[int] = None,
    legacy_invalid_fallback: bool = True,
) -> dict:
    """Compose selected frames; returns a provenance report (never a submission)."""
    within_shot = mode is CompositionMode.TRACEABLE and shot_map is not None \
        and allow_within_shot_nearest
    gap_limit = validate_shot_nearest_gap(max_shot_nearest_gap_frames)
    if within_shot and gap_limit is None:
        raise CompositionError(
            "within-shot nearest-box copying requires an explicitly declared "
            "max_shot_nearest_gap_frames; an implicit unbounded copy is not allowed")

    per_video: dict[str, dict] = {}
    for request in requests:
        vid = request.video_id
        fps = float(fps_by_video[vid])
        n_frames = int(n_frames_by_video[vid])
        timeline = CfrTimeline(fps=fps, n_frames=n_frames)
        base = spatial_source.get(vid) or {}
        base_frames = sorted(int(f) for f in base)

        outcome = parse_response(request.raw_output, duration_sec=request.duration_sec,
                                 constraint=constraint)
        entry = per_video.setdefault(vid, {
            "video_id": vid, "fps": fps, "n_frames": n_frames,
            "frames": {}, "windows": [], "state_counts": {},
            "resolved_frames": 0, "needs_spatial_inference": 0,
            "same_frame": 0, "shot_nearest": 0, "legacy_nearest": 0,
            "invalid_windows": 0, "empty_windows": 0,
        })
        entry["state_counts"][outcome.state.value] = entry["state_counts"].get(outcome.state.value, 0) + 1

        segments = [list(s) for s in outcome.segments]
        used_fallback = False
        legacy = mode is CompositionMode.LEGACY_REPLAY
        # The historical chain had no "legal empty": an empty parse was an error and
        # both were replaced by the centred-80% span.  Only the new mode keeps the
        # three states distinct.
        usable = (outcome.state is SegmentState.VALID_NONEMPTY) if legacy else outcome.is_usable
        if not usable:
            if outcome.state is SegmentState.VALID_EMPTY:
                entry["empty_windows"] += 1
            else:
                entry["invalid_windows"] += 1
            if legacy and legacy_invalid_fallback:
                segments = [[request.duration_sec * 0.1, request.duration_sec * 0.9]]
                used_fallback = True
                entry["legacy_fallbacks"] = entry.get("legacy_fallbacks", 0) + 1
            else:
                entry["windows"].append({
                    "index": request.index, "state": outcome.state.value,
                    "reasons": list(outcome.reasons), "frames_added": 0,
                    "mode": mode.value,
                    "note": ("legal empty preserved as empty; no fallback span invented"
                             if outcome.state is SegmentState.VALID_EMPTY else
                             "invalid output stays invalid; no fallback span invented"),
                })
                continue
        elif outcome.state is SegmentState.VALID_EMPTY:
            entry["empty_windows"] += 1
            entry["windows"].append({
                "index": request.index, "state": outcome.state.value,
                "reasons": [], "frames_added": 0, "mode": mode.value,
                "note": "legal empty prediction preserved as empty",
            })
            continue

        window_frames: set[int] = set()
        for a_local, b_local in segments:
            if mode is CompositionMode.TRACEABLE:
                a_abs, b_abs, origin = local_interval_to_absolute(
                    a_local_sec=a_local, b_local_sec=b_local,
                    window_start_sec=request.start_sec, fps=fps, n_frames=n_frames,
                    use_sampling_origin=True)
                selection = select_frames_timestamp_halfopen(
                    a_sec=a_local, b_sec=b_local, timeline=timeline, origin_frame=origin)
            else:
                selection = select_frames_legacy_round_inclusive(
                    a_sec=request.start_sec + a_local, b_sec=request.start_sec + b_local,
                    fps=fps, n_frames=n_frames)
                origin = None
            window_frames.update(selection.frames)
            entry["windows"].append({
                "index": request.index, "state": outcome.state.value, "reasons": [],
                "mode": mode.value, "interval_local": [a_local, b_local],
                "selection": selection.as_dict(), "frames_added": len(selection.frames),
                "used_invalid_fallback": used_fallback,
            })

        for frame in sorted(window_frames):
            if frame in entry["frames"]:
                continue
            provenance, box, detail = _resolve_frame(
                video_id=vid, frame=frame, base=base, base_frames=base_frames, shot_map=shot_map,
                mode=mode, allow_within_shot_nearest=allow_within_shot_nearest,
                max_shot_nearest_gap_frames=gap_limit)
            entry["frames"][frame] = {"frame": frame, "box": list(box) if box else None,
                                      "provenance": provenance.value, "detail": detail}
            if provenance is SpatialProvenance.NEEDS_SPATIAL_INFERENCE:
                entry["needs_spatial_inference"] += 1
            else:
                entry["resolved_frames"] += 1
            if provenance is SpatialProvenance.SOURCE_SAME_FRAME:
                entry["same_frame"] += 1
            elif provenance is SpatialProvenance.SOURCE_SHOT_NEAREST:
                entry["shot_nearest"] += 1
            elif provenance is SpatialProvenance.SOURCE_LEGACY_NEAREST:
                entry["legacy_nearest"] += 1

    videos = []
    for vid, entry in sorted(per_video.items(), key=lambda kv: (not kv[0].isdigit(), kv[0])):
        entry["frames"] = [entry["frames"][f] for f in sorted(entry["frames"])]
        entry["n_frames_selected"] = len(entry["frames"])
        videos.append(entry)

    totals = {
        "videos": len(videos),
        "frames_selected": sum(v["n_frames_selected"] for v in videos),
        "resolved_frames": sum(v["resolved_frames"] for v in videos),
        "needs_spatial_inference": sum(v["needs_spatial_inference"] for v in videos),
        "same_frame": sum(v["same_frame"] for v in videos),
        "shot_nearest": sum(v["shot_nearest"] for v in videos),
        "legacy_nearest": sum(v["legacy_nearest"] for v in videos),
        "empty_windows": sum(v["empty_windows"] for v in videos),
        "invalid_windows": sum(v["invalid_windows"] for v in videos),
        "empty_videos": sum(1 for v in videos if v["n_frames_selected"] == 0),
        "videos_with_gaps": sum(1 for v in videos if v["needs_spatial_inference"] > 0),
    }
    status, reason = _compose_status(mode=mode, totals=totals)

    return {
        "schema": "aic6_composition_report_v1",
        "mode": mode.value,
        "status": status.value,
        "status_reason": reason,
        "deliverable": status is CompositionStatus.OK_DELIVERABLE,
        "exit_code": COMPOSITION_EXIT_CODES[status.value],
        "shot_map_provided": shot_map is not None,
        "allow_within_shot_nearest": allow_within_shot_nearest,
        "max_shot_nearest_gap_frames": gap_limit,
        "legacy_invalid_fallback": bool(mode is CompositionMode.LEGACY_REPLAY and legacy_invalid_fallback),
        "totals": totals,
        "videos": videos,
    }


def _compose_status(*, mode: CompositionMode, totals: Mapping[str, int]) -> tuple[CompositionStatus, str]:
    """Single top-level verdict; never disguise a partial result as success.

    A legal empty prediction is a success.  An invalid window is a failure of the
    whole run.  Missing spatial boxes make the result undeliverable even though
    parsing succeeded.  Legacy replay is history reproduction, never a delivery
    path, so it reports ``deliverable: false`` by construction.
    """
    if mode is CompositionMode.LEGACY_REPLAY:
        return (CompositionStatus.LEGACY_REPLAY_COMPLETED,
                "historical rule reproduction only; legacy mode is not a delivery path")
    if totals["invalid_windows"] > 0:
        return (CompositionStatus.FAILED_INVALID_WINDOWS,
                f"{totals['invalid_windows']} window(s) failed strict parsing; the run is not "
                f"a success and no fallback span is invented")
    if totals["needs_spatial_inference"] > 0:
        return (CompositionStatus.NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE,
                f"{totals['needs_spatial_inference']} selected frame(s) have no same-frame and "
                f"no declared-shot spatial source; spatial inference is required")
    return (CompositionStatus.OK_DELIVERABLE,
            "every selected frame has a traceable spatial source")


def _resolve_frame(*, video_id: str, frame: int, base: Mapping[int, Sequence[int]],
                   base_frames: Sequence[int], shot_map: Optional[ShotMap],
                   mode: CompositionMode, allow_within_shot_nearest: bool,
                   max_shot_nearest_gap_frames: Optional[int]) -> tuple[SpatialProvenance, Optional[Sequence[int]], dict]:
    if frame in base:
        return SpatialProvenance.SOURCE_SAME_FRAME, base[frame], {"source_frame": frame, "distance": 0}

    if mode is CompositionMode.LEGACY_REPLAY:
        anchor = _nearest(base_frames, frame)
        return (SpatialProvenance.SOURCE_LEGACY_NEAREST, base[anchor],
                {"source_frame": anchor, "distance": abs(anchor - frame),
                 "rule": "nearest box anywhere in the video (historical rule)"})

    shot = shot_map.shot_of(video_id, frame) if shot_map is not None else None
    if allow_within_shot_nearest and shot is not None:
        if max_shot_nearest_gap_frames is None:      # fail closed; never copy unbounded
            raise CompositionError("internal: within-shot copy without a declared gap limit")
        in_shot = [f for f in base_frames if shot[0] <= f < shot[1]]
        if in_shot:
            anchor = _nearest(in_shot, frame)
            distance = abs(anchor - frame)
            if distance <= max_shot_nearest_gap_frames:
                return (SpatialProvenance.SOURCE_SHOT_NEAREST, base[anchor],
                        {"source_frame": anchor, "distance": distance, "shot": list(shot),
                         "rule": "nearest declared-shot source frame, same shot only"})
            return (SpatialProvenance.NEEDS_SPATIAL_INFERENCE, None,
                    {"reason": "within-shot source exists but exceeds the declared "
                               "max_shot_nearest_gap_frames",
                     "source_frame": anchor, "distance": distance, "shot": list(shot)})
    return (SpatialProvenance.NEEDS_SPATIAL_INFERENCE, None,
            {"reason": ("frame is not inside any declared shot" if shot_map is not None and shot is None
                        else "no same-frame source and no declared-shot source"),
             "shot": list(shot) if shot else None})


def load_spatial_source(path: Path | str) -> dict:
    """Read an existing prediction file as a *spatial source* (not ground truth)."""
    out: dict[str, dict[int, list]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        vid = str(record["video_id"])
        boxes = {}
        for prediction in record.get("predictions") or []:
            frame = int(prediction["frame"])
            boxes[frame] = [int(v) for v in prediction["bboxes"]]
        out[vid] = boxes
    return out


def load_windows(path: Path | str) -> tuple[list[WindowRequest], dict, dict]:
    """Read a recorded temporal inference file into window requests."""
    requests: list[WindowRequest] = []
    fps_by_video: dict[str, float] = {}
    n_frames_by_video: dict[str, int] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        vid = str(record["video_id"])
        fps_by_video[vid] = float(record["fps"])
        n_frames_by_video[vid] = int(record["n_frames"])
        for window in record["windows"]:
            requests.append(WindowRequest(video_id=vid, index=int(window["index"]),
                                          start_sec=float(window["start_sec"]),
                                          end_sec=float(window["end_sec"]),
                                          raw_output=window.get("raw_output") or ""))
    return requests, fps_by_video, n_frames_by_video
