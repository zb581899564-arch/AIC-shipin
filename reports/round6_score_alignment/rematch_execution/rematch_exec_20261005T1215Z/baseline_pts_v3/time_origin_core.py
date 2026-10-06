"""Pure CPU source-relative frame-zero identity; no media, models or labels.

This is a local identity contract, not the official timestamp origin. Source
frame i remains decoded-order index i. Bind stream metadata and every Decord
frame before removing one constant origin. The historical
abs((PTS-firstPTS)-i/fps) <= 1/fps+1e-6 gate is unchanged.
"""
from __future__ import annotations

import math
from fractions import Fraction

PASS_STATUS = "PASS_CFR_WITH_LEGACY_ONE_FRAME_TOLERANCE"
ORIGIN_CONTRACT = "SOURCE_RELATIVE_ZERO_IS_SOURCE_FRAME_0_RAW_PTS_MINUS_FIRST_FRAME_PTS"


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def probe_indices(n):
    if type(n) is not int or n <= 0:
        return []
    return sorted({0, min(1, n-1), min(2, n-1), n//2, max(0, n-3), max(0, n-2), n-1})


def audit_origin(raw_pts, fps_num, fps_den, expected_frames, stream_start_time,
                 stream_time_base, decord_timestamps, decord_fps, decord_frames,
                 decord_numeric_epsilon=2**-23):
    """Compare all starts; retain representative probes for inspection.

    Binding tolerance covers one stream tick and float representation only.
    Raw and relative clocks get separate magnitude bounds. A bound reaching
    half a source frame cannot resolve origin identity and fails closed.
    The separate historical CFR gate retains its original one frame.
    """
    if (type(fps_num) is not int or type(fps_den) is not int or fps_num <= 0 or fps_den <= 0 or
            type(expected_frames) is not int or expected_frames <= 1):
        raise ValueError("INVALID_REGISTERED_SOURCE_TIMEBASE")
    failures = []
    fps = fps_num/fps_den
    legacy_tolerance = 1/fps+1e-6
    raw_pts = raw_pts if isinstance(raw_pts, (list, tuple)) else []
    numeric = bool(raw_pts) and all(finite(p) for p in raw_pts)
    if not numeric:
        failures.append("RAW_PTS_NONFINITE_OR_MISSING")
    if len(raw_pts) != expected_frames:
        failures.append("RAW_PTS_FRAME_COUNT_MISMATCH")
    monotonic = numeric and all(b > a for a, b in zip(raw_pts, raw_pts[1:]))
    if not monotonic:
        failures.append("RAW_PTS_NOT_STRICTLY_MONOTONIC")
    origin = raw_pts[0] if numeric else None
    relative = [p-origin for p in raw_pts] if numeric else []
    maximum = max([abs(p-i/fps) for i, p in enumerate(relative)], default=None)
    if maximum is None or maximum > legacy_tolerance:
        failures.append("NORMALIZED_CFR_ERROR_EXCEEDS_UNCHANGED_ONE_FRAME_TOLERANCE")
    try:
        tick = float(Fraction(stream_time_base))
    except (TypeError, ValueError, ZeroDivisionError):
        tick = None
    if tick is None or not math.isfinite(tick) or tick <= 0:
        failures.append("STREAM_TIME_BASE_UNCONFIRMED")
        tick = 0.0
    origin_tolerance = max(tick, 1e-6)
    start_known = finite(stream_start_time)
    if not start_known:
        failures.append("STREAM_START_METADATA_UNCONFIRMED")
    elif origin is not None and abs(stream_start_time-origin) > origin_tolerance:
        failures.append("STREAM_START_AND_FIRST_PRESENTATION_PTS_ORIGINS_DISAGREE")
    if (type(decord_frames) is not int or decord_frames != expected_frames or not finite(decord_fps) or
            abs(decord_fps-fps) > max(1e-6, fps*1e-6)):
        failures.append("DECORD_REGISTERED_COUNT_OR_FPS_MISMATCH")
    if not finite(decord_numeric_epsilon) or not 0 < decord_numeric_epsilon <= 2**-23:
        failures.append("DECORD_FLOAT_REPRESENTATION_UNCONFIRMED")
        decord_numeric_epsilon = 0.0
    timestamps = decord_timestamps if isinstance(decord_timestamps, (list, tuple)) else []
    if len(timestamps) != expected_frames:
        failures.append("DECORD_ALL_FRAME_TIMESTAMP_COUNT_MISMATCH")
    valid = bool(timestamps) and all(isinstance(v, (list, tuple)) and len(v) == 2 and
                                    all(finite(t) for t in v) and v[1] > v[0] for v in timestamps)
    if not valid:
        failures.append("DECORD_TIMESTAMPS_INVALID")
    decord_monotonic = valid and all(b[0] > a[0] for a, b in zip(timestamps, timestamps[1:]))
    if not decord_monotonic:
        failures.append("DECORD_STARTS_NOT_STRICTLY_MONOTONIC")
    duration_error = max([abs((v[1]-v[0])-1/fps) for v in timestamps], default=None) if valid else None
    ends_monotonic = valid and all(b[1] > a[1] for a, b in zip(timestamps, timestamps[1:]))
    if not ends_monotonic or duration_error is None or duration_error > legacy_tolerance:
        failures.append("DECORD_INTERVAL_END_OR_DURATION_INVALID")
    raw_magnitude = max([1.0]+[abs(p) for p in raw_pts if finite(p)])
    relative_magnitude = max([1.0]+[abs(p) for p in relative])
    raw_tolerance = max(tick, 1e-6, 2*decord_numeric_epsilon*raw_magnitude)
    relative_tolerance = max(tick, 1e-6, 2*decord_numeric_epsilon*relative_magnitude)
    raw_resolvable = raw_tolerance < 0.5/fps
    relative_resolvable = relative_tolerance < 0.5/fps
    raw_errors, relative_errors = [], []
    if valid and numeric and len(raw_pts) == len(timestamps) == expected_frames:
        raw_errors = [abs(v[0]-p) for v, p in zip(timestamps, raw_pts)]
        relative_errors = [abs(v[0]-p) for v, p in zip(timestamps, relative)]
    raw_match = bool(raw_errors) and raw_resolvable and max(raw_errors) <= raw_tolerance
    relative_match = bool(relative_errors) and relative_resolvable and max(relative_errors) <= relative_tolerance
    mode = ("RAW_AND_RELATIVE_EQUIVALENT_ZERO_ORIGIN" if raw_match and relative_match and origin == 0 else
            "AMBIGUOUS_NONZERO_ORIGIN" if raw_match and relative_match else
            "RAW_CONTAINER_PTS" if raw_match else "SOURCE_RELATIVE_PTS" if relative_match else "UNCONFIRMED")
    if mode in {"UNCONFIRMED", "AMBIGUOUS_NONZERO_ORIGIN"}:
        failures.append("DECORD_RAW_OR_SOURCE_RELATIVE_ORIGIN_BINDING_FAILED")
    if not raw_resolvable and not relative_resolvable:
        failures.append("DECORD_TIMESTAMP_PRECISION_CANNOT_RESOLVE_FRAME_IDENTITY")
    normalized_decord = ([v[0]-(origin if mode == "RAW_CONTAINER_PTS" else 0) for v in timestamps]
                         if valid and mode not in {"UNCONFIRMED", "AMBIGUOUS_NONZERO_ORIGIN"} else [])
    decord_cfr_error = max([abs(p-i/fps) for i, p in enumerate(normalized_decord)], default=None)
    if decord_cfr_error is None or decord_cfr_error > legacy_tolerance:
        failures.append("DECORD_NORMALIZED_CFR_ERROR_EXCEEDS_UNCHANGED_ONE_FRAME_TOLERANCE")
    representatives = {i: timestamps[i] for i in probe_indices(expected_frames) if i < len(timestamps)}
    return {"pass": not failures, "failures": failures, "origin_contract": ORIGIN_CONTRACT,
            "contract_authority": "LOCAL_SOURCE_FRAME_IDENTITY_NOT_OFFICIAL_TIMESTAMP_ORIGIN_REQUIREMENT",
            "raw_first_pts_sec": origin, "source_relative_first_pts_sec": relative[0] if relative else None,
            "raw_pts_count": len(raw_pts), "raw_pts_numeric": numeric, "raw_pts_strictly_monotonic": monotonic,
            "max_normalized_cfr_error_sec": maximum, "one_frame_tolerance_sec": legacy_tolerance,
            "stream_start_time_sec": stream_start_time, "stream_start_metadata_known": start_known,
            "stream_time_base": stream_time_base, "stream_origin_binding_tolerance_sec": origin_tolerance,
            "decord_clock_mode": mode, "decord_all_frame_timestamp_count": len(timestamps),
            "decord_all_frame_binding_checked": len(raw_errors) == expected_frames,
            "decord_starts_strictly_monotonic": decord_monotonic,
            "decord_ends_strictly_monotonic": ends_monotonic,
            "decord_max_frame_duration_error_sec": duration_error,
            "decord_raw_binding_tolerance_sec": raw_tolerance,
            "decord_relative_binding_tolerance_sec": relative_tolerance,
            "decord_raw_clock_frame_precision_resolvable": raw_resolvable,
            "decord_relative_clock_frame_precision_resolvable": relative_resolvable,
            "decord_max_raw_binding_error_sec": max(raw_errors) if raw_errors else None,
            "decord_max_relative_binding_error_sec": max(relative_errors) if relative_errors else None,
            "decord_max_normalized_cfr_error_sec": decord_cfr_error,
            "decord_probe_indices": probe_indices(expected_frames), "decord_probes": representatives,
            "source_frame_to_raw_pts": "raw_pts = raw_first_pts + source_relative_pts",
            "source_frame_to_legacy_relative_time": "source_relative_time = frame_index / registered_fps",
            "cfr_tolerance_changed": False, "media_rewritten": False}
