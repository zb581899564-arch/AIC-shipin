#!/usr/bin/env python3
"""Isolated CPU numeric source read; no image exports, models or labels."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
from a_contract import write_json


def parse_ffprobe(data):
    streams = data.get("streams", [])
    if len(streams) != 1:
        raise ValueError("SOURCE_VIDEO_STREAM_COUNT")
    stream = streams[0]
    tick = Fraction(stream["time_base"])
    if tick <= 0:
        raise ValueError("STREAM_TIME_BASE_UNCONFIRMED")
    raw_pts, pair_errors = [], []
    integer_count = textual_count = 0
    for frame in data.get("frames", []):
        integer, textual = frame.get("best_effort_timestamp"), frame.get("best_effort_timestamp_time")
        value = float(integer*tick) if type(integer) is int else None
        if value is not None and math.isfinite(value):
            integer_count += 1
        raw_pts.append(value if value is not None and math.isfinite(value) else None)
        try:
            textual_value = float(textual)
            if not math.isfinite(textual_value):
                raise ValueError("nonfinite textual PTS")
            textual_count += 1
            pair_errors.append(abs(value-textual_value) if value is not None else None)
        except (TypeError, ValueError):
            pair_errors.append(None)
    try:
        start = float(stream.get("start_time"))
        start = start if math.isfinite(start) else None
    except (TypeError, ValueError):
        start = None
    start_pts = stream.get("start_pts")
    start_from_tick = float(start_pts*tick) if type(start_pts) is int else None
    if start_from_tick is not None and not math.isfinite(start_from_tick):
        start_from_tick = None
    avg = Fraction(stream["avg_frame_rate"])
    return {"width": stream.get("width"), "height": stream.get("height"),
            "ffprobe_fps_num": avg.numerator, "ffprobe_fps_den": avg.denominator,
            "stream_time_base": str(tick), "stream_start_time": start,
            "stream_start_pts": start_pts if type(start_pts) is int else None,
            "stream_start_pts_sec": start_from_tick,
            "stream_nominal_frame_rate": stream.get("r_frame_rate"),
            "raw_pts_sec": raw_pts, "raw_integer_pts_count": integer_count,
            "raw_textual_pts_count": textual_count,
            "max_integer_text_pts_error_sec":
                max(pair_errors) if pair_errors and all(x is not None for x in pair_errors) else None}


def read_numeric_source(source, ffprobe, decord_num_threads=0):
    process = subprocess.run([str(ffprobe), "-v", "error", "-select_streams", "v:0", "-show_frames",
                              "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,time_base,start_pts,start_time,nb_frames,duration:frame=best_effort_timestamp,best_effort_timestamp_time",
                              "-of", "json", str(source)], check=True, capture_output=True, text=True, timeout=600)
    numeric = parse_ffprobe(json.loads(process.stdout))
    import decord
    import numpy as np
    reader = decord.VideoReader(str(source), ctx=decord.cpu(0), num_threads=decord_num_threads)
    count = len(reader)
    timestamps, dtype, epsilon = [], None, None
    for first in range(0, count, 16384):
        batch = reader.get_frame_timestamp(list(range(first, min(count, first+16384))))
        values = np.asarray(batch.asnumpy() if hasattr(batch, "asnumpy") else batch)
        if values.shape != (min(count, first+16384)-first, 2):
            raise ValueError("DECORD_TIMESTAMP_ARRAY_SHAPE")
        if not np.issubdtype(values.dtype, np.floating):
            raise ValueError("DECORD_TIMESTAMP_FLOAT_DTYPE_REQUIRED")
        current_epsilon = float(np.finfo(values.dtype).eps)
        if dtype is not None and dtype != str(values.dtype):
            raise ValueError("DECORD_TIMESTAMP_DTYPE_CHANGED")
        dtype, epsilon = str(values.dtype), current_epsilon
        timestamps.extend([[float(x) if math.isfinite(float(x)) else None for x in row]
                           for row in values.tolist()])
    numeric.update(decord_frames=count, decord_fps=float(reader.get_avg_fps()),
                   decord_numeric_epsilon=epsilon, decord_timestamp_dtype=dtype,
                   decord_timestamps=timestamps, decord_version=getattr(decord, "__version__", "UNKNOWN"),
                   python_version=sys.version, decord_num_threads=decord_num_threads,
                   images_exported_or_displayed=False, automatic_all_frame_metadata_scan=True,
                   pixels_may_be_decoded_internally=True)
    return numeric


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--ffprobe", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--decord-num-threads", type=int, default=0)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior numeric evidence")
    if args.decord_num_threads < 0:
        raise ValueError("invalid Decord metadata worker count")
    write_json(args.output, read_numeric_source(args.source, args.ffprobe, args.decord_num_threads))


if __name__ == "__main__":
    main()
