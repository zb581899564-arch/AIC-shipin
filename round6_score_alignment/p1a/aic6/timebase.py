"""The single seconds -> frame conversion module for round 6.

Three independent, named conventions live here:

``TIMESTAMP_HALFOPEN`` (new internal policy)
    A frame ``f`` is selected iff its timestamp ``t = f / fps`` satisfies
    ``a <= t < b``.  For a windowed model output the local interval is first
    shifted to the timeline of the *real* sampling origin frame
    (``origin_frame = ceil(window_start_sec * fps)``), not to the nominal
    window start.  Legal frames are ``0 .. n_frames-1``.

``LEGACY_CEIL_HALFOPEN`` (the convention validated for the 43.48 package)
    ``f0 = ceil(a*fps - eps)``, ``f1 = ceil(b*fps - eps)``, frames
    ``f0 .. f1-1``.  Seconds are optionally clipped to ``[0, duration]`` first.

``LEGACY_ROUND_INCLUSIVE`` (the convention used by the round-5 composer)
    ``fa = round(a*fps)``, ``fb = round(b*fps)``, frames ``fa .. fb`` inclusive.

The legacy modes exist only for historical replay.  Nothing in this module
mutates a package, and no mode is selected from unknown ground truth.

VFR is not claimed without explicit presentation timestamps.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

EPS = 1e-9


class TimeConvention(str, Enum):
    TIMESTAMP_HALFOPEN = "timestamp_halfopen"
    LEGACY_CEIL_HALFOPEN = "legacy_ceil_halfopen"
    LEGACY_ROUND_INCLUSIVE = "legacy_round_inclusive"


class TimebaseError(ValueError):
    """Invalid input for a conversion (never silently repaired)."""


class VfrRequiresPts(TimebaseError):
    """VFR conversion requested without explicit PTS."""


@dataclass(frozen=True)
class CfrTimeline:
    """Constant-frame-rate timeline: frame ``f`` has timestamp ``f / fps``."""

    fps: float
    n_frames: int

    def __post_init__(self):
        if not math.isfinite(self.fps) or self.fps <= 0:
            raise TimebaseError(f"fps must be finite and positive, got {self.fps!r}")
        if self.n_frames <= 0:
            raise TimebaseError(f"n_frames must be positive, got {self.n_frames!r}")

    def timestamp(self, frame: int) -> float:
        self.check_frame(frame)
        return frame / self.fps

    def check_frame(self, frame: int) -> int:
        if isinstance(frame, bool) or not isinstance(frame, int):
            raise TimebaseError(f"frame must be a non-bool integer, got {frame!r}")
        if not 0 <= frame < self.n_frames:
            raise TimebaseError(f"frame {frame} outside legal range 0..{self.n_frames - 1}")
        return frame

    def sampling_origin_frame(self, window_start_sec: float) -> int:
        """First frame the model can see for a window starting at ``window_start_sec``.

        Mirrors the historical virtual-clip rule ``sf = ceil(start * fps)`` while
        making the origin explicit instead of implicit.
        """
        if not math.isfinite(window_start_sec):
            raise TimebaseError("window_start_sec must be finite")
        return max(0, min(int(math.ceil(window_start_sec * self.fps - EPS)), self.n_frames - 1))


@dataclass(frozen=True)
class VfrTimeline:
    """Variable-frame-rate timeline defined by explicit decoded PTS (seconds)."""

    pts_sec: Sequence[float]

    def __post_init__(self):
        if self.pts_sec is None:
            raise VfrRequiresPts("VFR timeline requires explicit PTS")
        pts = tuple(float(x) for x in self.pts_sec)
        if not pts:
            raise TimebaseError("VFR PTS list is empty")
        if any(not math.isfinite(x) for x in pts):
            raise TimebaseError("VFR PTS contains a non-finite value")
        if any(b < a for a, b in zip(pts, pts[1:])):
            raise TimebaseError("VFR PTS must be non-decreasing")
        object.__setattr__(self, "pts_sec", pts)

    @property
    def n_frames(self) -> int:
        return len(self.pts_sec)

    def check_frame(self, frame: int) -> int:
        if isinstance(frame, bool) or not isinstance(frame, int):
            raise TimebaseError(f"frame must be a non-bool integer, got {frame!r}")
        if not 0 <= frame < self.n_frames:
            raise TimebaseError(f"frame {frame} outside legal range 0..{self.n_frames - 1}")
        return frame


@dataclass(frozen=True)
class FrameSelection:
    """Result of one interval -> frame conversion."""

    frames: tuple[int, ...]
    convention: str
    first_frame: Optional[int]
    last_frame: Optional[int]
    empty: bool
    detail: dict

    def as_dict(self) -> dict:
        return {
            "convention": self.convention,
            "n_frames": len(self.frames),
            "first_frame": self.first_frame,
            "last_frame": self.last_frame,
            "empty": self.empty,
            "detail": self.detail,
        }


def _frames_from_bounds(lo: int, hi_exclusive: int, n_frames: int) -> tuple[int, ...]:
    lo = max(0, min(int(lo), n_frames))
    hi = max(0, min(int(hi_exclusive), n_frames))
    if hi <= lo:
        return ()
    return tuple(range(lo, hi))


def select_frames_timestamp_halfopen(
    *,
    a_sec: float,
    b_sec: float,
    timeline: CfrTimeline | VfrTimeline,
    origin_frame: int = 0,
) -> FrameSelection:
    """New policy: frame timestamps ``t`` with ``a <= t < b``.

    ``origin_frame`` is the timeline position that ``a_sec``/``b_sec`` are
    measured from, so a window-local ``[0, d)`` with origin 900 converts to the
    absolute interval ``[900/fps, 900/fps + d)``.
    """
    if not (math.isfinite(a_sec) and math.isfinite(b_sec)):
        raise TimebaseError("interval bounds must be finite")
    if not a_sec < b_sec:
        raise TimebaseError(f"interval must satisfy a < b, got [{a_sec}, {b_sec}]")
    if isinstance(origin_frame, bool) or not isinstance(origin_frame, int) or origin_frame < 0:
        raise TimebaseError(f"origin_frame must be a non-negative integer, got {origin_frame!r}")

    if isinstance(timeline, CfrTimeline):
        timeline.check_frame(origin_frame)  # origin must be a legal frame index
        offset = origin_frame / timeline.fps
        a_abs, b_abs = offset + a_sec, offset + b_sec
        lo = int(math.ceil(a_abs * timeline.fps - EPS))
        hi = int(math.ceil(b_abs * timeline.fps - EPS))
        frames = _frames_from_bounds(lo, hi, timeline.n_frames)
        return FrameSelection(
            frames=frames, convention=TimeConvention.TIMESTAMP_HALFOPEN.value,
            first_frame=frames[0] if frames else None,
            last_frame=frames[-1] if frames else None, empty=not frames,
            detail={"a_abs_sec": a_abs, "b_abs_sec": b_abs, "origin_frame": origin_frame,
                    "fps": timeline.fps, "n_frames": timeline.n_frames,
                    "rule": "a <= f/fps < b", "raw_lo": lo, "raw_hi_exclusive": hi},
        )

    if isinstance(timeline, VfrTimeline):
        pts = timeline.pts_sec
        if origin_frame >= len(pts):
            raise TimebaseError(f"origin_frame {origin_frame} outside PTS length {len(pts)}")
        offset = pts[origin_frame]
        a_abs, b_abs = offset + a_sec, offset + b_sec
        frames = tuple(i for i, t in enumerate(pts) if a_abs <= t < b_abs)
        return FrameSelection(
            frames=frames, convention=TimeConvention.TIMESTAMP_HALFOPEN.value,
            first_frame=frames[0] if frames else None,
            last_frame=frames[-1] if frames else None, empty=not frames,
            detail={"a_abs_sec": a_abs, "b_abs_sec": b_abs, "origin_frame": origin_frame,
                    "timeline": "vfr_pts", "n_frames": len(pts)},
        )
    raise TimebaseError(f"unsupported timeline type {type(timeline).__name__}")


def select_frames_legacy_ceil_halfopen(
    *,
    a_sec: float,
    b_sec: float,
    fps: float,
    n_frames: int,
    duration_sec: Optional[float] = None,
) -> FrameSelection:
    """Historical 43.48 convention, reproduced for replay only."""
    if not (math.isfinite(a_sec) and math.isfinite(b_sec)):
        raise TimebaseError("interval bounds must be finite")
    if duration_sec is not None:
        a_sec = max(0.0, min(a_sec, duration_sec))
        b_sec = max(0.0, min(b_sec, duration_sec))
    if not a_sec < b_sec:
        return FrameSelection((), TimeConvention.LEGACY_CEIL_HALFOPEN.value, None, None, True,
                              {"reason": "empty after clipping", "fps": fps, "n_frames": n_frames})
    f0 = int(math.ceil(a_sec * fps - EPS))
    f1 = int(math.ceil(b_sec * fps - EPS))
    frames = _frames_from_bounds(f0, f1, n_frames)
    return FrameSelection(
        frames=frames, convention=TimeConvention.LEGACY_CEIL_HALFOPEN.value,
        first_frame=frames[0] if frames else None,
        last_frame=frames[-1] if frames else None, empty=not frames,
        detail={"fps": fps, "n_frames": n_frames, "raw_f0": f0, "raw_f1_exclusive": f1,
                "duration_sec": duration_sec, "rule": "ceil(a*fps-eps) .. ceil(b*fps-eps)-1"},
    )


def select_frames_legacy_round_inclusive(
    *,
    a_sec: float,
    b_sec: float,
    fps: float,
    n_frames: int,
) -> FrameSelection:
    """Round-5 composer convention, reproduced for replay only (inclusive end)."""
    if not (math.isfinite(a_sec) and math.isfinite(b_sec)):
        raise TimebaseError("interval bounds must be finite")
    if not a_sec < b_sec:
        raise TimebaseError(f"interval must satisfy a < b, got [{a_sec}, {b_sec}]")
    fa = max(0, min(n_frames - 1, round(a_sec * fps)))
    fb = max(0, min(n_frames - 1, round(b_sec * fps)))
    if fb <= fa:
        fb = min(n_frames - 1, fa + 1)
    frames = tuple(range(fa, fb + 1))
    return FrameSelection(
        frames=frames, convention=TimeConvention.LEGACY_ROUND_INCLUSIVE.value,
        first_frame=frames[0] if frames else None,
        last_frame=frames[-1] if frames else None, empty=not frames,
        detail={"fps": fps, "n_frames": n_frames, "fa": fa, "fb": fb,
                "rule": "round(a*fps) .. round(b*fps) inclusive"},
    )


def merge_frames(*frame_tuples: Sequence[int]) -> tuple[int, ...]:
    """Union of frame selections (dedupe, ascending)."""
    out: set[int] = set()
    for chunk in frame_tuples:
        out.update(int(f) for f in chunk)
    return tuple(sorted(out))


def frames_to_intervals(frames: Sequence[int]) -> tuple[tuple[int, int], ...]:
    """Contiguous runs of frames as ``[start, end]`` inclusive pairs."""
    runs: list[list[int]] = []
    for frame in sorted(int(f) for f in frames):
        if runs and frame == runs[-1][1] + 1:
            runs[-1][1] = frame
        else:
            runs.append([frame, frame])
    return tuple((a, b) for a, b in runs)


def local_interval_to_absolute(
    *,
    a_local_sec: float,
    b_local_sec: float,
    window_start_sec: float,
    fps: float,
    n_frames: int,
    use_sampling_origin: bool = True,
) -> tuple[float, float, int]:
    """Map window-local seconds onto the source timeline.

    ``use_sampling_origin=True`` (new policy) uses the real first sampled frame
    ``ceil(window_start_sec*fps)`` as local time zero.  ``False`` reproduces the
    historical assumption that local zero is exactly ``window_start_sec``.
    """
    if use_sampling_origin:
        origin = CfrTimeline(fps=fps, n_frames=n_frames).sampling_origin_frame(window_start_sec)
        offset = origin / fps
    else:
        origin = int(math.floor(window_start_sec * fps))
        offset = float(window_start_sec)
    return offset + a_local_sec, offset + b_local_sec, origin


def compare_conventions(
    *,
    a_sec: float,
    b_sec: float,
    fps: float,
    n_frames: int,
) -> dict:
    """Utility for tests/reports: same interval under all three conventions."""
    half = select_frames_timestamp_halfopen(
        a_sec=a_sec, b_sec=b_sec, timeline=CfrTimeline(fps=fps, n_frames=n_frames))
    ceil_legacy = select_frames_legacy_ceil_halfopen(a_sec=a_sec, b_sec=b_sec, fps=fps, n_frames=n_frames)
    round_legacy = select_frames_legacy_round_inclusive(a_sec=a_sec, b_sec=b_sec, fps=fps, n_frames=n_frames)
    return {
        "interval": [a_sec, b_sec], "fps": fps, "n_frames": n_frames,
        "timestamp_halfopen": half.as_dict(),
        "legacy_ceil_halfopen": ceil_legacy.as_dict(),
        "legacy_round_inclusive": round_legacy.as_dict(),
    }
