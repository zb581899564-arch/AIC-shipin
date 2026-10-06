"""Bind Qwen processor timestamp expansion to audited source PTS, not avg FPS."""
from __future__ import annotations

from contextlib import contextmanager
import math


@contextmanager
def exact_source_pts(processor, source_ids: list[int], source_pts: list[float],
                     window_start_pts: float, metadata_fps: float):
    if len(source_ids) != len(source_pts) or len(source_ids) < 2 or len(source_ids) % 2:
        raise ValueError("exact-PTS processor requires complete even temporal pairs")
    if source_ids != sorted(set(source_ids)) or any(not math.isfinite(t) for t in source_pts):
        raise ValueError("invalid source frame IDs/PTS")
    if any(a >= b for a, b in zip(source_pts, source_pts[1:])) or source_pts[0] < window_start_pts:
        raise ValueError("source PTS not monotone/inside source window")
    if not math.isfinite(metadata_fps) or metadata_fps <= 0:
        raise ValueError("processor metadata requires verified source FPS")
    local_pts = [p - window_start_pts for p in source_pts]
    original = processor._calculate_timestamps
    record = {"source_frame_ids": source_ids, "exact_source_frame_pts": source_pts,
              "window_start_pts": window_start_pts, "exact_window_local_pts": local_pts,
              "metadata_fps": metadata_fps, "timestamp_clock": "EXACT_SOURCE_PTS_OVERRIDE",
              "processor_calls": []}
    def calculate(indices, fps, merge_size=2):
        actual_ids = list(indices)
        if actual_ids != source_ids or fps != metadata_fps or merge_size != 2:
            raise ValueError("processor resampled/reidentified frames or changed temporal merge contract")
        times = [(local_pts[i] + local_pts[i + 1]) / 2 for i in range(0, len(local_pts), 2)]
        record["processor_calls"].append({"frame_ids": actual_ids, "merge_size": merge_size,
                                           "exact_temporal_patch_local_pts": times})
        return times
    processor._calculate_timestamps = calculate
    try:
        yield record
        if len(record["processor_calls"]) != 1:
            raise ValueError("processor did not expand exactly one identity-bound video")
    finally:
        processor._calculate_timestamps = original
