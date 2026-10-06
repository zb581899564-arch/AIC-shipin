"""Source-frame replay and coverage mask. No teacher semantics are inferred here."""
from __future__ import annotations

import math
import torch

UNKNOWN, TEACHER_NEGATIVE, WEAK_POSITIVE = -1, 0, 1


def grid_targets_from_source_frames(frame_ids: list[int], starts: list[float],
                                    ends: list[float], states: list[int],
                                    cells: list[tuple[float, float]],
                                    observed_intervals: list[tuple[float, float]]) -> dict:
    """Known cell target = mean binary label over its source-frame starts.

    Caller must supply *all contiguous source frames*, audited binary frame states,
    and explicit teacher-observation intervals in the same source PTS coordinate.
    A partial observation, UNKNOWN frame, padded cell, or cell without source-frame
    starts is masked. Observation itself does not turn an UNKNOWN frame negative.
    """
    if not frame_ids or not (len(frame_ids) == len(starts) == len(ends) == len(states)):
        raise ValueError("source-frame vectors are empty or have different lengths")
    if frame_ids != list(range(frame_ids[0], frame_ids[0] + len(frame_ids))):
        raise ValueError("source frames must be contiguous; sampled positives are not coverage")
    if any(not math.isfinite(x) for x in starts + ends):
        raise ValueError("nonfinite source PTS")
    if any(a >= b for a, b in zip(starts, ends)) or any(a >= b for a, b in zip(starts, starts[1:])):
        raise ValueError("nonpositive frame duration/nonmonotone source PTS")
    if any(abs(a - b) > 1e-7 for a, b in zip(ends[:-1], starts[1:])):
        raise ValueError("source PTS durations do not tile the contiguous frame span")
    if any(x not in (UNKNOWN, TEACHER_NEGATIVE, WEAK_POSITIVE) for x in states):
        raise ValueError("unrecognized frame-state semantics")
    merged = []
    for a, b in sorted(observed_intervals):
        if not math.isfinite(a) or not math.isfinite(b) or a >= b:
            raise ValueError("invalid observation interval")
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    targets, known, replay = [], [], []
    previous_end = None
    for a, b in cells:
        if not math.isfinite(a) or not math.isfinite(b) or a >= b or (previous_end is not None and a < previous_end):
            raise ValueError("invalid/overlapping grid cells")
        previous_end = b
        indices = [i for i, pts in enumerate(starts) if a <= pts < b]
        inside_source = starts[0] <= a and b <= ends[-1]
        observed = any(left <= a and b <= right for left, right in merged)
        usable = bool(indices) and inside_source and observed and all(states[i] != UNKNOWN for i in indices)
        targets.append(sum(states[i] for i in indices) / len(indices) if usable else float("nan"))
        known.append(usable)
        replay.append({"start_pts": a, "end_pts_exclusive": b,
                       "source_frame_ids": [frame_ids[i] for i in indices],
                       "source_frame_pts": [starts[i] for i in indices],
                       "fully_observed": observed, "inside_source": inside_source,
                       "known": usable, "target": targets[-1] if usable else None})
    return {"targets": torch.tensor([targets], dtype=torch.float32),
            "known_mask": torch.tensor([known], dtype=torch.bool), "replay": replay,
            "semantics": "weak binary source-frame mean; UNKNOWN never inferred negative"}
