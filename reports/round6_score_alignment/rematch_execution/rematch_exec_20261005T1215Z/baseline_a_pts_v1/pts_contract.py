"""CPU clock contracts for A_NATIVE_PTS_COMPAT_V1; no models or media IO."""
from __future__ import annotations

from bisect import bisect_left
import copy
import json
import math
from fractions import Fraction
from pathlib import Path

import a_contract as legacy

VARIANT = "A_NATIVE_PTS_COMPAT_V1"
CLOCK_SCHEMA = "aic_source_clock_registry_v4"
BRANCH_CFR = "CFR_LEGACY"
BRANCH_NATIVE = "NATIVE_PTS"
CLOCK_KEYS = {"clock_branch", "clock_record_id"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def legacy_manifest(manifest):
    """Explicit metadata projection for unchanged spatial/legacy contracts.

    Native time scope is validated independently against native packet-end
    evidence. The old spatial validator only receives its historical n/fps
    scope; this projection never controls native windows or segment mapping.
    """
    projected = copy.deepcopy(manifest)
    projected["schema"] = "aic_rematch_A_input_v1"
    for key in ("clock_registry", "input_manifest_sha256"):
        projected.pop(key, None)
    for row in projected["records"]:
        branch = row.pop("clock_branch", None)
        row.pop("clock_record_id", None)
        if branch == BRANCH_NATIVE:
            row["scope_start_sec"] = 0
            row["scope_end_sec"] = row["n_frames"]*row["fps_den"]/row["fps_num"]
    legacy.validate_manifest(projected)
    return projected


def load_clocks(manifest, registry_path, expected_registry_sha256):
    require(manifest.get("schema") == "aic_rematch_A_input_v2", "V2_NATIVE_CLOCK_MANIFEST_REQUIRED")
    require(manifest.get("clock_registry") == {"path": str(registry_path), "sha256": expected_registry_sha256},
            "MANIFEST_CLOCK_REGISTRY_BINDING_MISMATCH")
    require(legacy.sha(registry_path) == expected_registry_sha256, "CLOCK_REGISTRY_SHA_MISMATCH")
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    kind = manifest.get("kind")
    count = 8 if kind == "NONTEST_FROZEN8" else 426 if kind == "REMATCH426" else None
    require(count is not None and registry.get("schema") == CLOCK_SCHEMA and registry.get("kind") == kind and
            registry.get("expected_count") == count and registry.get("all_identity_pass") is True and
            registry.get("all_sources_usable") is True and registry.get("inference_allowed") is False and
            registry.get("failed_video_ids") == [] and
            registry.get("input_manifest_sha256") == manifest.get("input_manifest_sha256"),
            "ALL_SOURCE_CLOCK_IDENTITY_NOT_ADMITTED")
    rows = manifest.get("records", [])
    require(isinstance(rows, list) and len(rows) == count, "V2_SOURCE_DENOMINATOR_MISMATCH")
    for row in rows:
        require(set(row) == legacy.RECORD_KEYS | CLOCK_KEYS, "V2_SOURCE_FIELD_WHITELIST_MISMATCH")
    legacy_manifest(manifest)
    records = registry.get("records", [])
    require(isinstance(records, list) and len(records) == count, "CLOCK_REGISTRY_DENOMINATOR_MISMATCH")
    by_id = {r.get("video_id"): r for r in records}
    require(len(by_id) == count and set(by_id) == {r["video_id"] for r in rows},
            "CLOCK_REGISTRY_SOURCE_SET_MISMATCH")
    clocks = {}
    evidence_root = Path(registry_path).resolve().parent
    for row in rows:
        vid, c = row["video_id"], by_id[row["video_id"]]
        require(row["clock_record_id"] == vid and c.get("identity_pass") is True and
                all(c.get(k) == row[k] for k in ("source_sha256", "n_frames", "fps_num", "fps_den")) and
                type(c.get("cfr_eligible")) is bool and c.get("failures") == [],
                "SOURCE_CLOCK_RECORD_IDENTITY_MISMATCH")
        branch = BRANCH_CFR if c["cfr_eligible"] else BRANCH_NATIVE
        require(row["clock_branch"] == branch, "BRANCH_MUST_FOLLOW_CLOCK_FORMAT_ONLY")
        binding = c.get("decord_binding", {})
        require(binding.get("start_pass") is True, "DECODER_CLOCK_START_BINDING_UNCONFIRMED")
        if branch == BRANCH_NATIVE:
            require(binding.get("end_pass") is True, "NATIVE_PACKET_END_BINDING_UNCONFIRMED")
        else:
            require(binding.get("legacy_interval_pass") is True,
                    "LEGACY_CFR_INTERVAL_CHECK_UNCONFIRMED")
        arrays_ref = c.get("clock_arrays", {})
        require(set(arrays_ref) == {"path", "sha256"}, "CLOCK_ARRAY_EVIDENCE_MISSING")
        arrays_path = Path(arrays_ref["path"]).resolve(strict=True)
        require(evidence_root in arrays_path.parents, "CLOCK_ARRAY_PATH_OUTSIDE_REGISTRY_EVIDENCE")
        require(legacy.sha(arrays_path) == arrays_ref["sha256"], "CLOCK_ARRAY_SHA_MISMATCH")
        arrays = json.loads(arrays_path.read_text(encoding="utf-8"))
        require(arrays.get("schema") == "aic_source_clock_arrays_v1" and
                all(arrays.get(k) == row[k] for k in ("video_id", "source_sha256", "n_frames")) and
                arrays.get("raw_time_base") == c.get("raw_time_base") and
                arrays.get("raw_first_pts_ticks") == c.get("raw_first_pts_ticks"),
                "CLOCK_ARRAY_SOURCE_IDENTITY_MISMATCH")
        tick = Fraction(arrays["raw_time_base"])
        ticks = arrays.get("native_pts_ticks", [])
        origin = arrays.get("raw_first_pts_ticks")
        require(tick > 0 and type(origin) is int and len(ticks) == row["n_frames"] and
                all(type(t) is int for t in ticks) and ticks[0] == origin and
                all(b > a for a, b in zip(ticks, ticks[1:])), "NATIVE_INTEGER_PTS_INVALID")
        relative = [(t-origin)*tick for t in ticks]
        require(arrays.get("source_relative_pts_rational") == [str(t) for t in relative] and
                arrays.get("source_relative_pts") == [float(t) for t in relative],
                "NATIVE_PTS_RATIONAL_OR_FLOAT_ARRAY_MISMATCH")
        duration = c.get("duration_seconds")
        if branch == BRANCH_NATIVE:
            require(c.get("native_clock_usable") is True and
                    c.get("terminal_evidence", {}).get("kind") == "NATIVE_LAST_FRAME_PACKET_DURATION",
                    "VERIFIED_NATIVE_PACKET_ENDPOINT_REQUIRED")
            ends = arrays.get("native_frame_end_pts_ticks")
            require(isinstance(ends, list) and len(ends) == len(ticks) and
                    all(type(t) is int and t > p for p, t in zip(ticks, ends)),
                    "NATIVE_PACKET_DURATION_ARRAY_INVALID")
            terminal = (ends[-1]-origin)*tick
            require(finite(c.get("native_end_sec")) and finite(duration) and
                    c["native_end_sec"] == float(terminal) and duration == float(terminal) and terminal > relative[-1],
                    "NATIVE_TERMINAL_DURATION_MISMATCH")
        else:
            terminal = Fraction(row["n_frames"]*row["fps_den"], row["fps_num"])
            require(c.get("terminal_evidence", {}).get("kind") == "LEGACY_CFR_N_DIV_FPS" and
                    finite(duration) and duration == float(terminal), "LEGACY_CFR_DURATION_CHANGED")
        start, end = row["scope_start_sec"], row["scope_end_sec"]
        require(finite(start) and finite(end) and 0 <= start < end <= float(terminal)+1e-9,
                "SOURCE_SCOPE_OUTSIDE_REGISTERED_CLOCK")
        if kind == "REMATCH426":
            require(start == 0 and abs(end-float(terminal)) <= 1e-9, "FULL_SOURCE_NATIVE_SCOPE_REQUIRED")
        clocks[vid] = {**c, "branch": branch, "pts": relative, "duration": terminal,
                       "arrays": arrays, "clock_record_sha256": arrays_ref["sha256"]}
    return clocks


def window_schedule(record, kind, clock):
    if clock["branch"] == BRANCH_CFR:
        return legacy.window_schedule(record, kind)
    start, end = record["scope_start_sec"], record["scope_end_sec"]
    require(0 <= start < end <= float(clock["duration"])+1e-9, "NATIVE_SCOPE_INVALID")
    if kind == "NONTEST_FROZEN8":
        return [(float(start), float(end))]
    result = []
    while start < end-1e-6:
        stop = min(start+30.0, end)
        if stop-start >= 0.2:
            result.append((float(start), float(stop)))
        start = stop
    require(bool(result), "NO_ELIGIBLE_NATIVE_WINDOW_EMPTY_UNSUPPORTED")
    return result


def native_clip_plan(clock, start, end, max_frames=64):
    require(clock["branch"] == BRANCH_NATIVE and finite(start) and finite(end) and
            0 <= start < end <= float(clock["duration"])+1e-9 and max_frames == 64,
            "NATIVE_CLIP_CONTRACT_INVALID")
    starts = [float(t) for t in clock["pts"]]
    lo, hi = bisect_left(starts, start), bisect_left(starts, end)
    require(0 <= lo < hi <= len(clock["pts"]), "NATIVE_WINDOW_HAS_NO_SOURCE_FRAMES")
    n_clip = hi-lo
    k = min(max_frames, n_clip)
    local = [0] if k == 1 else [int(round(i*((n_clip-1)/(k-1)))) for i in range(k)]
    if k > 1:
        local[-1] = n_clip-1
    ids = [lo+i for i in local]
    require(ids == sorted(set(ids)), "NATIVE_UNIFORM_SAMPLE_IDENTITY_INVALID")
    pts = [float(clock["pts"][i]) for i in ids]
    return {"source_frame_ids": ids, "source_relative_pts": pts, "window_start": float(start),
            "window_end": float(end), "source_context_first": lo, "source_context_end_exclusive": hi,
            "n_frames_in_clip": n_clip, "n_sampled": k,
            "exact_window_local_pts": [p-start for p in pts], "branch": BRANCH_NATIVE}


def parse_native_segments(raw, clip_duration):
    """Keep legacy parsing, restore only round4 overshoot at its true endpoint.

    The legacy 1e-3 input allowance, segment count and empty policy remain.
    This representation event cannot accept an input the legacy parser rejects.
    """
    from vendor.temporal_common import parse_segments
    require(finite(clip_duration) and clip_duration > 0, "NATIVE_CLIP_DURATION_INVALID")
    parsed, errors, warnings = parse_segments(raw, clip_duration)
    events = []
    if parsed is None:
        return parsed, errors, warnings, events
    normalized = [list(segment) for segment in parsed]
    for index, segment in enumerate(normalized):
        if segment[1] > clip_duration and segment[1] == round(clip_duration, 4):
            events.append({"event": "LEGACY_ROUND4_NATIVE_ENDPOINT_RESTORED",
                           "parsed_segment_index": index, "legacy_parsed_end": segment[1],
                           "verified_clip_duration": clip_duration})
            segment[1] = clip_duration
        if not 0 <= segment[0] < segment[1] <= clip_duration:
            return None, errors+["invalid native segment after legacy endpoint representation"], warnings, events
    return normalized, errors, warnings, events


def native_segment_frames(clock, start, end, segments):
    require(clock["branch"] == BRANCH_NATIVE, "NATIVE_SELECTION_BRANCH_REQUIRED")
    require(isinstance(segments, list) and 1 <= len(segments) <= 5, "LEGACY_SEGMENT_COUNT_CHANGED")
    result = set()
    for segment in segments:
        require(isinstance(segment, list) and len(segment) == 2 and all(finite(x) for x in segment) and
                0 <= segment[0] < segment[1] <= end-start+1e-6, "INVALID_NATIVE_PARSED_SEGMENT")
        # Convert exact native starts to their bound float64 representation
        # once. No epsilon/quality threshold: equal represented boundaries
        # remain half-open, including fractional native time bases.
        a = float(Fraction(str(start))+Fraction(str(segment[0])))
        b = float(Fraction(str(start))+Fraction(str(segment[1])))
        starts = [float(t) for t in clock["pts"]]
        first, last = bisect_left(starts, a), bisect_left(starts, b)
        require(last > first and 0 <= first < last <= len(clock["pts"]), "SEGMENT_HAS_NO_NATIVE_SOURCE_FRAMES")
        result.update(range(first, last))
    return sorted(result)


def validate_frame_request(request, metadata):
    vid = request.get("video_id")
    require(vid in metadata, "UNREGISTERED_FRAME_SOURCE")
    row = metadata[vid]
    require(request.get("source_path") == row["source_path"] and
            request.get("source_width") == row["width"] and request.get("source_height") == row["height"] and
            request.get("source_n_frames") == row["n_frames"] and
            request.get("target_ratio_wh") == row["targetRatioWH"] and finite(request.get("fps")) and
            abs(request["fps"]-row["fps_num"]/row["fps_den"]) <= 1e-6 and
            type(request.get("source_frame")) is int and 0 <= request["source_frame"] < row["n_frames"],
            "FRAME_REQUEST_SOURCE_IDENTITY_MISMATCH")
    return row


def select_frames(manifest, temporal, clocks):
    projected = legacy_manifest(manifest)
    if all(c["branch"] == BRANCH_CFR for c in clocks.values()):
        return legacy.select_frames(projected, temporal)
    metadata = {r["video_id"]: r for r in manifest["records"]}
    by_id = {r.get("video_id"): r for r in temporal}
    require(len(by_id) == len(temporal) and set(by_id) == set(metadata), "TEMPORAL_SOURCE_SET_MISMATCH")
    selected = []
    for vid in sorted(metadata):
        m, row, clock = metadata[vid], by_id[vid], clocks[vid]
        fps = m["fps_num"]/m["fps_den"]
        require(row.get("n_frames") == m["n_frames"] and row.get("targetRatioWH") == m["targetRatioWH"] and
                row.get("video_path") == m["source_path"] and finite(row.get("fps")) and
                abs(row["fps"]-fps) <= max(1e-6, fps*1e-6), "TEMPORAL_SOURCE_IDENTITY_MISMATCH")
        expected = window_schedule(m, manifest["kind"], clock)
        require(len(row.get("windows", [])) == len(expected), "TEMPORAL_WINDOW_SET_MISMATCH")
        chosen = set()
        for window, (start, end) in zip(row["windows"], expected):
            require(window.get("status") == "MODEL_OK" and window.get("output_valid") is True and
                    not window.get("parse_errors") and window.get("parsed_segments") is not None,
                    "TEMPORAL_FAILURE_BLOCKS_CANDIDATE")
            require(abs(window.get("start_sec", -1)-start) <= 1e-6 and
                    abs(window.get("end_sec", -1)-end) <= 1e-6, "TEMPORAL_WINDOW_SCHEDULE_CHANGED")
            segments = window["parsed_segments"]
            if clock["branch"] == BRANCH_NATIVE:
                require(window.get("clock_record_sha256") == clock["clock_record_sha256"],
                        "TEMPORAL_NATIVE_CLOCK_EVIDENCE_CHANGED")
                chosen.update(native_segment_frames(clock, start, end, segments))
            else:
                # Identical arithmetic and checks to frozen A, with no PTS remapping.
                require(isinstance(segments, list) and 1 <= len(segments) <= 5, "LEGACY_SEGMENT_COUNT_CHANGED")
                for s in segments:
                    require(isinstance(s, list) and len(s) == 2 and all(finite(x) for x in s) and
                            0 <= s[0] < s[1] <= end-start+1e-6, "INVALID_CFR_PARSED_SEGMENT")
                    if manifest["kind"] == "NONTEST_FROZEN8":
                        first = math.ceil(start*fps)+math.ceil(s[0]*fps)
                        last = min(math.ceil(start*fps)+math.ceil(s[1]*fps), math.ceil(end*fps))
                    else:
                        first, last = math.ceil((start+s[0])*fps), math.ceil((start+s[1])*fps)
                    first, last = max(0, first), min(m["n_frames"], last)
                    require(last > first, "SEGMENT_HAS_NO_CFR_SOURCE_FRAMES")
                    chosen.update(range(first, last))
        require(bool(chosen), "LEGACY_EMPTY_SELECTION_UNSUPPORTED")
        for frame in sorted(chosen):
            selected.append({"video_id": vid, "source_frame": frame, "source_path": m["source_path"],
                             "source_width": m["width"], "source_height": m["height"],
                             "source_n_frames": m["n_frames"], "fps": fps,
                             "target_ratio_wh": m["targetRatioWH"]})
    return selected
