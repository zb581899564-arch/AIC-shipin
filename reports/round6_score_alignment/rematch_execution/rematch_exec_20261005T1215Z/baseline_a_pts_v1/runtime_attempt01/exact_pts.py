"""Instance-local Qwen native PTS override, including implicit final-frame pad."""
from __future__ import annotations

from contextlib import contextmanager
import math
import re

from pts_contract import require


@contextmanager
def exact_native_pts(processor, plan, metadata_fps):
    ids, source_pts = list(plan["source_frame_ids"]), list(plan["source_relative_pts"])
    start = plan["window_start"]
    require(ids and len(ids) == len(source_pts) and ids == sorted(set(ids)) and
            all(type(i) is int for i in ids) and all(math.isfinite(t) for t in source_pts) and
            all(a < b for a, b in zip(source_pts, source_pts[1:])) and source_pts[0] >= start and
            math.isfinite(metadata_fps) and metadata_fps > 0, "NATIVE_PROCESSOR_INPUT_IDENTITY_INVALID")
    local = [p-start for p in source_pts]
    padded_ids, padded_pts = list(ids), list(local)
    if len(padded_ids) % 2:
        padded_ids.append(padded_ids[-1])
        padded_pts.append(padded_pts[-1])
    expected = [(padded_pts[i]+padded_pts[i+1])/2 for i in range(0, len(padded_pts), 2)]
    original = processor._calculate_timestamps
    had_local = "_calculate_timestamps" in getattr(processor, "__dict__", {})
    record = {"source_frame_ids": ids, "source_relative_pts": source_pts, "window_start": start,
              "exact_window_local_pts": local, "padded_source_frame_ids": padded_ids,
              "padded_window_local_pts": padded_pts, "exact_temporal_patch_local_pts": expected,
              "last_frame_padding_copies": len(padded_ids)-len(ids), "processor_calls": [],
              "timestamp_clock": "NATIVE_SOURCE_RELATIVE_PTS_MINUS_WINDOW_START",
              "metadata_fps": metadata_fps}
    def calculate(indices, fps, merge_size=2):
        require(list(indices) == ids and fps == metadata_fps and merge_size == 2,
                "PROCESSOR_RESAMPLED_OR_CHANGED_NATIVE_IDENTITY")
        record["processor_calls"].append({"frame_ids": list(indices), "merge_size": merge_size,
                                          "exact_temporal_patch_local_pts": list(expected)})
        return list(expected)
    processor._calculate_timestamps = calculate
    try:
        yield record
        require(len(record["processor_calls"]) == 1, "PROCESSOR_NATIVE_TIMESTAMP_CALL_COUNT_CHANGED")
    finally:
        if had_local:
            processor._calculate_timestamps = original
        else:
            delattr(processor, "_calculate_timestamps")


def verify_native_encoding(processor, encoded, identity):
    require(len(identity["processor_calls"]) == 1, "PROCESSOR_NATIVE_TIMESTAMPS_NOT_USED")
    grid = encoded["video_grid_thw"]
    rows = grid.tolist() if hasattr(grid, "tolist") else grid
    expected = identity["exact_temporal_patch_local_pts"]
    require(len(rows) == 1 and int(rows[0][0]) == len(expected),
            "NATIVE_PROCESSOR_TEMPORAL_PATCH_COUNT_CHANGED")
    input_ids = encoded["input_ids"][0]
    decoded = processor.tokenizer.decode(input_ids, skip_special_tokens=False)
    values = [float(s) for s in re.findall(r"<([0-9]+(?:\.[0-9]+)?) seconds>", decoded)]
    require(len(values) == len(expected) and all(abs(a-b) <= 0.05000001 for a, b in zip(values, expected)),
            "NATIVE_PROCESSOR_TIMESTAMP_TEXT_MISMATCH")
    identity["processor_temporal_grid"] = rows[0]
    identity["processor_timestamp_text_values"] = values
    identity["timestamp_text_rounding_max_error"] = max(abs(a-b) for a, b in zip(values, expected))
    return identity
