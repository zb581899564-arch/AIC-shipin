"""Frame-level spatial coverage audit and the bounded-reuse gate.

The audit answers, for every frame a temporal policy selects, exactly one of
four states (``SAME_FRAME``, ``SHOT_NEAREST``, ``NEEDS_INFERENCE``,
``UNRESOLVABLE``) plus the distance and shot-crossing profile of every reused
box.  It never invents a box and never rewrites a prediction.

Three entry points:

``audit_frames``
    The four-state frame audit for one selection.  This is the single
    classification used everywhere in P2; ``legacy_replay``-style unbounded
    copying is quantified only as a *contrast* (``legacy_copy_profile``).

``legacy_copy_profile``
    What the historical round-5 rule would have done on the same selection:
    the nearest-box copy distance distribution and how many copies cross a
    declared shot boundary.  Read-only history contrast, never a delivery path.

``CoverageGate``
    The delivery gate: a composition is deliverable only when no selected frame
    is left without a same-frame or bounded within-shot source.  A gate result
    is a value; the caller decides what to do with ``NEEDS_INFERENCE`` frames
    (in P2 they are sent to real spatial inference, never auto-filled).

All counts are structural; none is a quality metric, and none is an official
score.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Optional, Sequence


class CoverageState(str, Enum):
    SAME_FRAME = "SAME_FRAME"                # a box exists at exactly this frame
    SHOT_NEAREST = "SHOT_NEAREST"            # nearest box inside the same declared shot, <= limit
    NEEDS_INFERENCE = "NEEDS_INFERENCE"      # no legal reuse; spatial inference required
    UNRESOLVABLE = "UNRESOLVABLE"            # caller declared no source at all for the video


class CoverageError(ValueError):
    pass


def validate_max_reuse_gap(value) -> Optional[int]:
    """A declared reuse limit must be a non-bool positive integer (NaN floats etc. refused)."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise CoverageError(
            f"max_reuse_gap_frames must be a non-bool positive integer or None, got {value!r}")
    if value <= 0:
        raise CoverageError(f"max_reuse_gap_frames must be positive, got {value!r}")
    return int(value)


@dataclass(frozen=True)
class ShotIntervals:
    """Declared shot boundaries ``[start, end)`` per video (input, not detected)."""

    shots_by_video: Mapping[str, tuple[tuple[int, int], ...]]

    def __post_init__(self):
        for video_id, shots in self.shots_by_video.items():
            previous_end = None
            for start, end in shots:
                if isinstance(start, bool) or isinstance(end, bool):
                    raise CoverageError(f"{video_id}: shot bounds must be integers")
                if start < 0 or end <= start:
                    raise CoverageError(f"{video_id}: invalid shot [{start},{end})")
                if previous_end is not None and start < previous_end:
                    raise CoverageError(f"{video_id}: shots overlap at [{start},{end})")
                previous_end = end

    def shot_of(self, video_id: str, frame: int) -> Optional[tuple[int, int]]:
        for shot in self.shots_by_video.get(video_id, ()):
            if shot[0] <= frame < shot[1]:
                return shot
        return None


@dataclass
class FrameAuditRow:
    frame: int
    state: str
    box: Optional[Sequence[int]]
    source_frame: Optional[int]
    distance: int
    shot: Optional[tuple[int, int]]
    crosses_shot_boundary: bool
    note: str

    def as_dict(self) -> dict:
        return {
            "frame": self.frame, "state": self.state,
            "box": list(self.box) if self.box is not None else None,
            "source_frame": self.source_frame, "distance": self.distance,
            "shot": list(self.shot) if self.shot else None,
            "crosses_shot_boundary": self.crosses_shot_boundary,
            "note": self.note,
        }


@dataclass
class AuditResult:
    video_id: str
    rows: list[FrameAuditRow] = field(default_factory=list)
    n_frames: int = 0                          # legal frame ceiling of the video

    @property
    def counts(self) -> dict:
        out = {state.value: 0 for state in CoverageState}
        for row in self.rows:
            out[row.state] += 1
        return out

    def as_dict(self, *, include_rows: bool = True) -> dict:
        payload = {
            "video_id": self.video_id,
            "counts": self.counts,
            "n_rows": len(self.rows),
        }
        if include_rows:
            payload["rows"] = [row.as_dict() for row in self.rows]
        return payload


def audit_frames(
    *,
    selected_frames: Iterable[int],
    source_boxes: Mapping[int, Sequence[int]],
    n_frames: int,
    shots: Optional[Sequence[tuple[int, int]]] = None,
    max_reuse_gap_frames: Optional[int] = None,
) -> AuditResult:
    """Classify every selected frame into the four coverage states.

    ``source_boxes`` maps a frame index to that frame's box (a *box source*,
    never ground truth).  ``shots`` is the declared shot list for the video;
    ``None`` means "no shot information was declared", in which case
    within-shot reuse is refused outright (fail closed).
    """
    gap_limit = validate_max_reuse_gap(max_reuse_gap_frames)
    source_frames = sorted(int(f) for f in source_boxes)
    result = AuditResult(video_id="", n_frames=int(n_frames))
    for frame in sorted({int(f) for f in selected_frames}):
        if not 0 <= frame < n_frames:
            raise CoverageError(
                f"selected frame {frame} outside legal range 0..{n_frames - 1}")
        if frame in source_boxes:
            result.rows.append(FrameAuditRow(
                frame=frame, state=CoverageState.SAME_FRAME.value,
                box=source_boxes[frame], source_frame=frame, distance=0,
                shot=None, crosses_shot_boundary=False, note="box exists at this frame"))
            continue
        if not source_frames:
            result.rows.append(FrameAuditRow(
                frame=frame, state=CoverageState.UNRESOLVABLE.value,
                box=None, source_frame=None, distance=0,
                shot=None, crosses_shot_boundary=False,
                note="no box source declared for this video"))
            continue
        shot = None
        if shots:
            for start, end in shots:
                if start <= frame < end:
                    shot = (start, end)
                    break
        # Within-shot reuse requires BOTH a declared shot containing a source and
        # a declared positive gap limit; without the limit this is unbounded
        # copying and is refused outright (fail closed).
        reused = None
        if shot is not None and gap_limit is not None:
            in_shot = [f for f in source_frames if shot[0] <= f < shot[1]]
            if in_shot:
                position = bisect.bisect_left(in_shot, frame)
                candidates = in_shot[max(0, position - 1):position + 1]
                nearest = min(candidates, key=lambda f: (abs(f - frame), f))
                if abs(nearest - frame) <= gap_limit:
                    reused = nearest
        if reused is not None and shot is not None:
            result.rows.append(FrameAuditRow(
                frame=frame, state=CoverageState.SHOT_NEAREST.value,
                box=source_boxes[reused], source_frame=reused, distance=abs(reused - frame),
                shot=shot, crosses_shot_boundary=False,
                note="nearest box within the declared shot and the declared gap limit"))
            continue
        if reused is not None and shot is None:
            # unreachable with the current policy (reuse requires a declared shot);
            # kept defensive so a box is never emitted without provenance
            raise CoverageError("internal: reuse without a declared shot")
        if shot is not None and gap_limit is None:
            reason = ("a shot is declared but no positive max_reuse_gap_frames was "
                      "declared; unbounded within-shot copying is refused")
        else:
            reason = ("within-shot source exists but exceeds the declared gap limit"
                      if (shot is not None and any(shot[0] <= f < shot[1] for f in source_frames))
                      else ("inside a declared shot that contains no source frame" if shots
                            else "no shot declared; unbounded copying refused"))
        result.rows.append(FrameAuditRow(
            frame=frame, state=CoverageState.NEEDS_INFERENCE.value,
            box=None, source_frame=None, distance=0,
            shot=shot, crosses_shot_boundary=False, note=reason))
    return result


def legacy_copy_profile(
    *,
    selected_frames: Iterable[int],
    source_boxes: Mapping[int, Sequence[int]],
    n_frames: int,
    shots: Optional[Sequence[tuple[int, int]]] = None,
) -> dict:
    """Contrast only: what the historical nearest-anywhere rule would copy.

    Reports the copy distance distribution and how many copies would cross a
    declared shot boundary.  Produces no boxes for delivery and no score.
    """
    source_frames = sorted(int(f) for f in source_boxes)
    if not source_frames:
        return {"n_selected": len(set(int(f) for f in selected_frames)),
                "n_copied": 0, "distances": [], "crossing": 0}
    distances: list[int] = []
    crossing = 0
    for frame in sorted({int(f) for f in selected_frames}):
        if not 0 <= frame < n_frames:
            raise CoverageError(f"selected frame {frame} outside legal range 0..{n_frames - 1}")
        if frame in source_boxes:
            continue
        position = bisect.bisect_left(source_frames, frame)
        candidates = source_frames[max(0, position - 1):position + 1]
        anchor = min(candidates, key=lambda f: (abs(f - frame), f))
        distances.append(abs(anchor - frame))
        if shots:
            for start, end in shots:
                # a copy crosses a boundary when anchor and frame sit in different shots
                if (start <= frame < end) != (start <= anchor < end) and not (
                        frame < start and anchor < start) and not (
                        frame >= end and anchor >= end):
                    crossing += 1
                    break
                if (frame < start <= anchor) or (anchor < start <= frame):
                    crossing += 1
                    break
    ordered = sorted(distances)
    return {
        "n_selected": len({int(f) for f in selected_frames}),
        "n_same_frame": len({int(f) for f in selected_frames} & set(source_frames)),
        "n_copied": len(distances),
        "distance_min": ordered[0] if ordered else None,
        "distance_p50": ordered[len(ordered) // 2] if ordered else None,
        "distance_p90": ordered[min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1))))] if ordered else None,
        "distance_max": ordered[-1] if ordered else None,
        "n_over_30_frames": sum(1 for d in ordered if d > 30),
        "n_over_300_frames": sum(1 for d in ordered if d > 300),
        "n_crossing_declared_shot_boundary": crossing,
        "note": "historical contrast profile; never a delivery path",
    }


class CoverageGate:
    """Delivery gate over an audit: bounded reuse or explicit inference demand."""

    def __init__(self, *, allow_bounded_within_shot: bool = True,
                 max_reuse_gap_frames: Optional[int] = None):
        self.allow_bounded_within_shot = bool(allow_bounded_within_shot)
        self.max_reuse_gap_frames = validate_max_reuse_gap(max_reuse_gap_frames)
        if self.allow_bounded_within_shot and self.max_reuse_gap_frames is None:
            raise CoverageError(
                "allow_bounded_within_shot requires an explicit max_reuse_gap_frames; "
                "an implicit unbounded copy is not allowed")

    def judge(self, audit: AuditResult) -> dict:
        counts = audit.counts
        n_rows = len(audit.rows)
        # Recompute provenance from the row fields.  A state label or a reported
        # distance alone is never evidence that a usable box exists at a legal
        # source frame under this gate's policy.
        policy_violations: list[dict] = []
        resolved_rows = 0

        def valid_frame(value: object) -> bool:
            return (isinstance(value, int) and not isinstance(value, bool)
                    and 0 <= value < audit.n_frames)

        def has_box(value: object) -> bool:
            return (isinstance(value, Sequence)
                    and not isinstance(value, (str, bytes)) and len(value) == 3)

        for row in audit.rows:
            if row.state == CoverageState.SAME_FRAME.value:
                allowed = (valid_frame(row.frame) and has_box(row.box)
                           and row.source_frame == row.frame
                           and isinstance(row.distance, int)
                           and not isinstance(row.distance, bool)
                           and row.distance == 0 and row.shot is None
                           and row.crosses_shot_boundary is False)
                if allowed:
                    resolved_rows += 1
                else:
                    policy_violations.append({"frame": row.frame, "state": row.state,
                                              "distance": row.distance,
                                              "reason": "same-frame box or source provenance is invalid"})
                continue
            if row.state == CoverageState.SHOT_NEAREST.value:
                shot = row.shot
                valid_shot = (isinstance(shot, (tuple, list)) and len(shot) == 2
                              and all(isinstance(v, int) and not isinstance(v, bool)
                                      for v in shot)
                              and 0 <= shot[0] < shot[1] <= audit.n_frames)
                allowed = (self.allow_bounded_within_shot
                           and self.max_reuse_gap_frames is not None
                           and valid_frame(row.frame)
                           and valid_frame(row.source_frame)
                           and has_box(row.box)
                           and isinstance(row.distance, int)
                           and not isinstance(row.distance, bool)
                           and 0 < row.distance <= self.max_reuse_gap_frames
                           and row.distance == abs(row.frame - row.source_frame)
                           and valid_shot
                           and shot[0] <= row.frame < shot[1]
                           and shot[0] <= row.source_frame < shot[1]
                           and row.crosses_shot_boundary is False)
                if allowed:
                    resolved_rows += 1
                else:
                    policy_violations.append({"frame": row.frame, "state": row.state,
                                              "distance": row.distance,
                                              "reason": "reused box provenance or distance "
                                                        "violates this gate's policy"})
            # NEEDS_INFERENCE / UNRESOLVABLE rows are unresolved by definition
        needs = n_rows - resolved_rows
        if n_rows == 0:
            verdict, reason = "EMPTY_SELECTION", "no frames selected"
        elif policy_violations:
            verdict = "NEEDS_SPATIAL_INFERENCE"
            reason = (f"{len(policy_violations)} row(s) reuse a box outside this gate's "
                      f"declared policy; the audit verdict is not trusted")
        elif needs == 0:
            verdict = "DELIVERABLE"
            reason = ("every selected frame has a same-frame or bounded within-shot box source"
                      if counts[CoverageState.SHOT_NEAREST.value] else
                      "every selected frame has a same-frame box source")
        elif self.allow_bounded_within_shot:
            verdict = "NEEDS_SPATIAL_INFERENCE"
            reason = (f"{needs} frame(s) cannot reuse a box under the declared limit; "
                      f"spatial inference is required before delivery")
        else:
            verdict = "NEEDS_SPATIAL_INFERENCE"
            reason = f"{needs} frame(s) have no same-frame source; spatial inference is required"
        return {
            "verdict": verdict,
            "reason": reason,
            "counts": counts,
            "n_rows": n_rows,
            "allow_bounded_within_shot": self.allow_bounded_within_shot,
            "max_reuse_gap_frames": self.max_reuse_gap_frames,
            "policy_violations": policy_violations,
            "deliverable": verdict == "DELIVERABLE",
        }
