"""Stdlib native-start identity, unchanged CFR eligibility, and proven native ends.

No media/decoder import or invocation. v3 starts are explicitly reconstructed
from its frozen integer*Fraction -> float64 parser, never called retained ints.
"""
from __future__ import annotations

from fractions import Fraction
import math
import struct

ORIGIN = "SOURCE_RELATIVE_ZERO_IS_SOURCE_FRAME_0_RAW_PTS_MINUS_FIRST_FRAME_PTS"
TEXT_TOL = 1e-6 + 1e-12


def need(ok, code):
    if not ok:
        raise ValueError(code)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def f32(value):
    return struct.unpack("!f", struct.pack("!f", float(value)))[0]


def nearest_integer(value: Fraction):
    lower = value.numerator // value.denominator
    rest = value - lower
    need(rest != Fraction(1, 2), "INTEGER_TICK_HALF_WAY_AMBIGUOUS")
    return lower if rest < Fraction(1, 2) else lower + 1


def reconstruct_integer_ticks(values, tick):
    """Invert exactly the frozen float(integer * Fraction(time_base)) parser."""
    result = []
    for value in values:
        need(type(value) is float and math.isfinite(value), "V3_RAW_FLOAT64_MISSING_OR_NONFINITE")
        k = nearest_integer(Fraction.from_float(value) / tick)
        need(float(k * tick) == value, "V3_RAW_FLOAT64_NOT_EXACT_FROZEN_PARSER_REPLAY")
        need(float((k - 1) * tick) != value and float((k + 1) * tick) != value,
             "V3_FLOAT64_CANNOT_UNIQUELY_RECOVER_INTEGER_TICK")
        result.append(k)
    return result


def bind_float32(observed, expected, tick):
    """Exact representation and unique frame identity, no whole-tick tolerance."""
    need(len(observed) == len(expected) > 1, "DECORD_ALL_FRAME_COUNT_MISMATCH")
    need(all(type(x) is float and math.isfinite(x) and f32(x) == x for x in observed),
         "DECORD_STORED_VALUES_NOT_KNOWN_FLOAT32")
    need(all(b > a for a, b in zip(expected, expected[1:])), "NATIVE_CLOCK_NOT_STRICTLY_MONOTONIC")
    quantized = [f32(x) for x in expected]
    need(all(b > a for a, b in zip(quantized, quantized[1:])), "ADJACENT_NATIVE_FRAMES_ALIAS_IN_FLOAT32")
    need(observed == quantized, "DECORD_NOT_EXACT_FLOAT32_OF_NATIVE_CLOCK")
    minimum_gap = min(b - a for a, b in zip(expected, expected[1:]))
    errors = [abs(Fraction.from_float(a) - b) for a, b in zip(observed, expected)]
    need(all(error < minimum_gap / 2 for error in errors), "FLOAT32_ERROR_CANNOT_RESOLVE_HALF_FRAME")
    direct_round = []
    for value, exact in zip(observed, expected):
        try:
            direct_round.append(nearest_integer(Fraction.from_float(value) / tick) == exact / tick)
        except ValueError:
            direct_round.append(False)
    return {"pass": True, "method": "EXACT_FLOAT32_NATIVE_VALUE_AND_UNIQUE_ADJACENT_FRAME",
        "float_dtype": "float32", "whole_tick_used_as_float_error": False,
        "max_representation_error_sec": float(max(errors)), "minimum_source_gap_sec": float(minimum_gap),
        "half_minimum_source_gap_sec": float(minimum_gap / 2),
        "direct_integer_tick_roundtrip_exact_count": sum(direct_round),
        "direct_integer_tick_roundtrip_total": len(direct_round),
        "direct_integer_tick_roundtrip_is_diagnostic_only": True}


def classify_cfr(raw_values, timestamps, fps_num, fps_den, mode):
    """Same numeric 1/fps+1e-6 gate as v3; no VFR-to-CFR relabeling."""
    fps = fps_num / fps_den
    tolerance = 1 / fps + 1e-6
    origin = raw_values[0]
    raw_error = max(abs((p - origin) - i / fps) for i, p in enumerate(raw_values))
    normalized = [p[0] - (origin if mode == "RAW_CONTAINER_PTS" else 0.0) for p in timestamps]
    decord_error = max(abs(p - i / fps) for i, p in enumerate(normalized))
    duration_error = max(abs((end - start) - 1 / fps) for start, end in timestamps)
    monotonic_ends = all(b[1] > a[1] for a, b in zip(timestamps, timestamps[1:]))
    failures = []
    if raw_error > tolerance:
        failures.append("NORMALIZED_CFR_ERROR_EXCEEDS_UNCHANGED_ONE_FRAME_TOLERANCE")
    if decord_error > tolerance:
        failures.append("DECORD_NORMALIZED_CFR_ERROR_EXCEEDS_UNCHANGED_ONE_FRAME_TOLERANCE")
    if not monotonic_ends or duration_error > tolerance:
        failures.append("DECORD_INTERVAL_END_OR_DURATION_INVALID")
    return {"eligible": not failures, "failures": failures, "one_frame_tolerance_sec": tolerance,
        "max_normalized_cfr_error_sec": raw_error, "decord_max_normalized_cfr_error_sec": decord_error,
        "decord_max_frame_duration_error_sec": duration_error, "tolerance_changed": False}


def validate_base(row, numeric, prior):
    need(prior.get("source_sha256") == row["source_sha256"]
         and prior.get("source_hash_verified_before_and_after") is True
         and prior.get("media_rewritten") is False, "V3_SOURCE_BYTE_IDENTITY_UNCONFIRMED")
    n = row["n_frames"]
    need(type(n) is int and n > 1, "INVALID_SOURCE_FRAME_COUNT")
    need((numeric.get("width"), numeric.get("height")) == (row["width"], row["height"]), "SOURCE_GEOMETRY_MISMATCH")
    need(numeric.get("raw_integer_pts_count") == n and numeric.get("raw_textual_pts_count") == n
         and numeric.get("decord_frames") == n, "ALL_NATIVE_AND_DECORD_FRAME_COUNTS_REQUIRED")
    need(numeric.get("ffprobe_fps_num") * row["fps_den"] == row["fps_num"] * numeric.get("ffprobe_fps_den"),
         "REGISTERED_AVERAGE_FPS_METADATA_MISMATCH")
    need(finite(numeric.get("max_integer_text_pts_error_sec"))
         and 0 <= numeric["max_integer_text_pts_error_sec"] <= TEXT_TOL, "FFPROBE_INTEGER_TEXTUAL_PTS_UNCONFIRMED")
    need(numeric.get("decord_timestamp_dtype") == "float32" and numeric.get("decord_numeric_epsilon") == 2**-23,
         "DECORD_KNOWN_FLOAT32_DTYPE_EPSILON_REQUIRED")
    need(numeric.get("automatic_all_frame_metadata_scan") is True
         and numeric.get("images_exported_or_displayed") is False, "V3_NUMERIC_METADATA_SCOPE_UNCONFIRMED")
    tick = Fraction(numeric["stream_time_base"])
    need(tick > 0, "INVALID_NATIVE_TIME_BASE")
    raw = numeric.get("raw_pts_sec")
    need(isinstance(raw, list) and len(raw) == n, "RAW_ALL_FRAME_COUNT_MISMATCH")
    ticks = reconstruct_integer_ticks(raw, tick)
    need(all(b > a for a, b in zip(ticks, ticks[1:])), "NATIVE_STARTS_NOT_STRICTLY_MONOTONIC")
    need(type(numeric.get("stream_start_pts")) is int and numeric["stream_start_pts"] == ticks[0],
         "STREAM_INTEGER_START_AND_FIRST_NATIVE_PTS_DISAGREE")
    stream_start = numeric.get("stream_start_time")
    need(finite(stream_start) and abs(float(ticks[0] * tick) - stream_start) <= TEXT_TOL
         and numeric.get("stream_start_pts_sec") == float(ticks[0] * tick), "STREAM_TEXTUAL_START_UNCONFIRMED")
    timestamps = numeric.get("decord_timestamps")
    need(isinstance(timestamps, list) and len(timestamps) == n
         and all(isinstance(v, list) and len(v) == 2 and all(finite(x) for x in v)
                 and v[1] > v[0] for v in timestamps), "DECORD_INTERVAL_VALUES_INVALID")
    need(all(b[1] > a[1] for a, b in zip(timestamps, timestamps[1:])), "DECORD_ENDS_NOT_STRICTLY_MONOTONIC")
    need(finite(numeric.get("decord_fps")) and abs(numeric["decord_fps"] - row["fps_num"] / row["fps_den"])
         <= max(1e-6, row["fps_num"] / row["fps_den"] * 1e-6), "DECORD_AVERAGE_FPS_METADATA_MISMATCH")
    return tick, ticks, timestamps


def bind_starts(tick, ticks, timestamps):
    raw = [k * tick for k in ticks]
    relative = [(k - ticks[0]) * tick for k in ticks]
    observed = [v[0] for v in timestamps]
    matches = {}
    failures = {}
    for name, expected in (("RAW_CONTAINER_PTS", raw), ("SOURCE_RELATIVE_PTS", relative)):
        try:
            matches[name] = bind_float32(observed, expected, tick)
        except ValueError as exc:
            failures[name] = str(exc)
    need(matches, "DECORD_NATIVE_START_BINDING_FAILED:" + str(failures))
    if len(matches) == 2:
        need(ticks[0] == 0, "NONZERO_RAW_AND_RELATIVE_DECORD_ORIGINS_AMBIGUOUS")
        mode = "RAW_AND_RELATIVE_EQUIVALENT_ZERO_ORIGIN"
        evidence = matches["RAW_CONTAINER_PTS"]
    else:
        mode = next(iter(matches))
        evidence = matches[mode]
    return mode, evidence


def native_endpoint(row, numeric, tick, ticks, mode, addendum_record, ffprobe):
    """Join new raw integer/packet evidence to the SAME bound v3 numeric source."""
    need(isinstance(addendum_record, dict) and isinstance(ffprobe, dict), "NONCFR_NATIVE_ENDPOINT_ADDENDUM_REQUIRED")
    digest = row["source_sha256"]
    need(addendum_record.get("source_sha256") == digest
         and addendum_record.get("source_sha256_before") == digest
         and addendum_record.get("source_sha256_after") == digest
         and addendum_record.get("source_hash_verified_before_and_after") is True,
         "ADDENDUM_SOURCE_BEFORE_AFTER_BYTE_IDENTITY_UNCONFIRMED")
    streams = ffprobe.get("streams", [])
    need(len(streams) == 1, "ADDENDUM_STREAM_COUNT_MISMATCH")
    stream = streams[0]
    need((stream.get("width"), stream.get("height")) == (row["width"], row["height"])
         and Fraction(stream["time_base"]) == tick, "ADDENDUM_GEOMETRY_OR_NATIVE_TIME_BASE_MISMATCH")
    need(Fraction(stream["avg_frame_rate"]) == Fraction(row["fps_num"], row["fps_den"]), "ADDENDUM_AVERAGE_FPS_METADATA_MISMATCH")
    need(type(stream.get("start_pts")) is int and stream["start_pts"] == ticks[0]
         and abs(float(Fraction(str(stream["start_time"])) - ticks[0] * tick)) <= TEXT_TOL,
         "ADDENDUM_STREAM_ORIGIN_MISMATCH")
    frames = ffprobe.get("frames", [])
    need(len(frames) == row["n_frames"], "ADDENDUM_ALL_NATIVE_FRAME_COUNT_MISMATCH")
    actual_ticks, durations, pair_errors = [], [], []
    for frame in frames:
        pts, duration = frame.get("best_effort_timestamp"), frame.get("pkt_duration")
        need(type(pts) is int and type(duration) is int and duration > 0,
             "NATIVE_INTEGER_PTS_OR_PACKET_DURATION_MISSING")
        textual = Fraction(str(frame["best_effort_timestamp_time"]))
        need(abs(float(textual - pts * tick)) <= TEXT_TOL, "ADDENDUM_INTEGER_TEXTUAL_PTS_MISMATCH")
        if "pkt_duration_time" in frame:
            need(abs(float(Fraction(str(frame["pkt_duration_time"])) - duration * tick)) <= TEXT_TOL,
                 "ADDENDUM_INTEGER_TEXTUAL_PACKET_DURATION_MISMATCH")
        actual_ticks.append(pts)
        durations.append(duration)
        pair_errors.append(abs(float(textual - pts * tick)))
    need(actual_ticks == ticks, "ADDENDUM_ORIGINAL_NATIVE_INTEGERS_DIFFER_FROM_V3_UNIQUE_RECONSTRUCTION")
    end_ticks = [pts + duration for pts, duration in zip(actual_ticks, durations)]
    need(all(b > a for a, b in zip(end_ticks, end_ticks[1:])), "NATIVE_PACKET_ENDS_NOT_STRICTLY_MONOTONIC")
    end_expected = [(end - (ticks[0] if mode != "RAW_CONTAINER_PTS" else 0)) * tick for end in end_ticks]
    end_binding = bind_float32([v[1] for v in numeric["decord_timestamps"]], end_expected, tick)
    terminal = (end_ticks[-1] - ticks[0]) * tick
    need(terminal > 0, "INVALID_NATIVE_TERMINAL_DURATION")
    duration_ts = stream.get("duration_ts")
    duration_text = stream.get("duration")
    # Container/header duration need not include the presentation duration of
    # the final decoded frame. The native packet + same-frame decoder endpoint
    # is authoritative for this branch; keep header discrepancies as evidence.
    header_integer = duration_ts * tick if type(duration_ts) is int else None
    header_textual = Fraction(str(duration_text)) if duration_text is not None else None
    evidence = {"status": "PASS_NATIVE_PACKET_AND_DECORD_END_BINDING", "kind": "NATIVE_LAST_FRAME_PACKET_DURATION",
        "last_frame_pts_ticks": ticks[-1], "last_packet_duration_ticks": durations[-1],
        "last_frame_end_pts_ticks": end_ticks[-1], "raw_time_base": str(tick),
        "relative_terminal_rational": str(terminal), "stream_duration_ts": duration_ts,
        "stream_duration_text": duration_text, "all_packet_durations_positive": True,
        "endpoint_authority": "NATIVE_LAST_FRAME_PACKET_AND_DECORD_END",
        "stream_header_duration_used_as_endpoint": False,
        "stream_header_integer_duration_rational": str(header_integer) if header_integer is not None else None,
        "stream_header_textual_duration_rational": str(header_textual) if header_textual is not None else None,
        "stream_header_integer_minus_packet_terminal_sec": float(header_integer - terminal) if header_integer is not None else None,
        "stream_header_textual_minus_packet_terminal_sec": float(header_textual - terminal) if header_textual is not None else None,
        "stream_header_matches_packet_terminal": (header_integer == terminal if header_integer is not None
            else abs(float(header_textual - terminal)) <= TEXT_TOL if header_textual is not None else None),
        "all_native_integers_match_v3_reconstruction": True, "all_decord_ends_bound": True,
        "ffprobe_max_integer_text_pts_error_sec": max(pair_errors),
        "packet_gap_count": sum(a < b for a, b in zip(end_ticks[:-1], ticks[1:])),
        "packet_overlap_count": sum(a > b for a, b in zip(end_ticks[:-1], ticks[1:]))}
    return float(terminal), end_ticks, evidence, end_binding


def audit_record(row, numeric, prior, addendum_record=None, ffprobe=None):
    result = {"video_id": row["video_id"], "source_sha256": row["source_sha256"], "n_frames": row["n_frames"],
        "fps_num": row["fps_num"], "fps_den": row["fps_den"], "identity_pass": False,
        "native_clock_usable": False, "cfr_eligible": False, "native_end_sec": None, "duration_seconds": None,
        "legacy_a_admission_granted": False, "inference_allowed": False, "failures": [],
        "v3_pass": prior.get("pass"), "v3_failures": prior.get("failures", [])}
    arrays = None
    try:
        tick, ticks, timestamps = validate_base(row, numeric, prior)
        mode, starts = bind_starts(tick, ticks, timestamps)
        result.update(identity_pass=True, raw_time_base=str(tick), raw_first_pts_ticks=ticks[0], decord_clock_mode=mode,
            integer_evidence_kind="UNIQUE_RECONSTRUCTION_FROM_BOUND_V3_FROZEN_FLOAT64_PARSER",
            decord_binding={"start_pass": True, "end_pass": False, **starts})
        relative = [(k - ticks[0]) * tick for k in ticks]
        arrays = {"schema": "aic_source_clock_arrays_v1", "video_id": row["video_id"], "source_sha256": row["source_sha256"],
            "n_frames": row["n_frames"], "raw_time_base": str(tick), "raw_first_pts_ticks": ticks[0],
            "native_pts_ticks": ticks, "source_relative_pts": [float(p) for p in relative],
            "source_relative_pts_rational": [str(p) for p in relative], "native_frame_end_pts_ticks": None,
            "integer_evidence_kind": result["integer_evidence_kind"]}
        cfr = classify_cfr(numeric["raw_pts_sec"], timestamps, row["fps_num"], row["fps_den"], mode)
        result.update(cfr_eligible=cfr["eligible"], cfr_evidence=cfr)
        if cfr["eligible"]:
            result["decord_binding"].update(legacy_interval_pass=True,
                end_evidence={"method": "LEGACY_CFR_INTERVAL_CHECK", "finite_positive_intervals": True,
                    "ends_strictly_monotonic": True, "max_frame_duration_error_sec": cfr["decord_max_frame_duration_error_sec"],
                    "one_frame_tolerance_sec": cfr["one_frame_tolerance_sec"], "native_packet_endpoint_proven": False})
            duration = row["n_frames"] * row["fps_den"] / row["fps_num"]
            result.update(duration_seconds=duration, clock_branch="CFR_LEGACY",
                terminal_evidence={"status": "LEGACY_CFR_ENDPOINT_ONLY", "kind": "LEGACY_CFR_N_DIV_FPS",
                    "duration_seconds": duration, "native_packet_endpoint_proven": False,
                    "claim": "unchanged historical CFR branch endpoint; not native packet duration"})
        else:
            duration, ends, terminal, end_binding = native_endpoint(row, numeric, tick, ticks, mode, addendum_record, ffprobe)
            result.update(native_clock_usable=True, native_end_sec=duration, duration_seconds=duration,
                          clock_branch="NATIVE_PTS", terminal_evidence=terminal)
            result["decord_binding"].update(end_pass=True, end_evidence=end_binding)
            result["integer_evidence_kind"] = "NEW_RAW_NATIVE_INTEGER_ARRAY_MATCHES_V3_UNIQUE_RECONSTRUCTION"
            arrays["integer_evidence_kind"] = result["integer_evidence_kind"]
            arrays["native_frame_end_pts_ticks"] = ends
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        result["failures"].append(str(exc))
        result.setdefault("terminal_evidence", {"status": "STOP_MISSING_OR_INVALID_NATIVE_ENDPOINT", "kind": "UNPROVEN"})
    result["usable"] = result["identity_pass"] and (result["cfr_eligible"] or result["native_clock_usable"]) and not result["failures"]
    result["status"] = ("PASS_CFR_LEGACY_BRANCH_IDENTITY" if result["usable"] and result["cfr_eligible"] else
        "PASS_NATIVE_PTS_BRANCH_IDENTITY_NON_CFR" if result["usable"] else "STOP_SOURCE_CLOCK_EVIDENCE")
    return result, arrays
