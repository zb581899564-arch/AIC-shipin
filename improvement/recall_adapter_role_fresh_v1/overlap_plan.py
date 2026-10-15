"""Pure exact-PTS 15s / 7.5s candidate planning; no media or model admission.

Input is RECALL_SOURCE_CLOCKS_V1 with a nonempty ``sources`` list. Each source
has video_id, source_sha256, width, height, n_frames, targetRatioWH,
normalized_exact_pts and physical_end_exact. Exact seconds are JSON strings or
integers, never floats. Existing accepted full clocks are supplied by the caller.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

SOURCE_SCHEMA = "RECALL_SOURCE_CLOCKS_V1"
PLAN_SCHEMA = "RECALL_OVERLAP_PLAN_V1"
BASELINE_PLAN_SCHEMA = "RECALL_BASELINE_EQUAL_PLAN_V1"
WINDOW_SECONDS = Fraction(15)
STRIDE_SECONDS = Fraction(15, 2)
NATIVE_FRAMES = 64
TARGET_RATIOS = ((16, 9), (9, 16))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value):
    require(type(value) in (str, int), "Exact seconds must be a string or non-bool integer")
    if isinstance(value, str):
        require(bool(value) and value.strip() == value, "Exact seconds cannot contain surrounding whitespace")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError("Invalid finite exact seconds") from error


def stable_id(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value)
            and ".." not in value, "A safe explicit string identifier is required")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Nonfinite JSON constant: " + value)


def read_json_document(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def write_json_document(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def validate_sources(document):
    """Validate the caller's complete source set without measuring/repairing it."""
    require(isinstance(document, dict) and document.get("schema") == SOURCE_SCHEMA,
            "RECALL_SOURCE_CLOCKS_V1 is required")
    rows = document.get("sources")
    require(isinstance(rows, list) and bool(rows), "The source collection must be a nonempty list")
    result = {}
    for source in rows:
        require(isinstance(source, dict), "Every source must be an object")
        video_id = stable_id(source.get("video_id"))
        require(video_id not in result, "Duplicate source video_id: " + video_id)
        digest = source.get("source_sha256")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
                "An explicit source SHA256 binding is required")
        for key in ("width", "height", "n_frames"):
            require(type(source.get(key)) is int and source[key] > 0, "Positive integer source " + key + " required")
        ratio = source.get("targetRatioWH")
        require(isinstance(ratio, list) and len(ratio) == 2 and all(type(v) is int for v in ratio)
                and tuple(ratio) in TARGET_RATIOS, "Only explicit 16:9 or 9:16 source ratios are supported")
        raw_points = source.get("normalized_exact_pts")
        require(isinstance(raw_points, list) and len(raw_points) == source["n_frames"],
                "Complete native source PTS/count identity is required")
        points = list(map(exact, raw_points))
        end = exact(source.get("physical_end_exact"))
        require(points[0] == 0 and all(a < b for a, b in zip(points, points[1:]))
                and end > points[-1], "Source PTS must start at zero, increase strictly and end after the last frame")
        result[video_id] = dict(source=source, points=points, end=end)
    return result


def fixed_windows(physical_end):
    """Uniform starts plus one right-aligned tail, deduplicated before sampling."""
    end = exact(physical_end) if not isinstance(physical_end, Fraction) else physical_end
    require(end > 0, "A positive physical source domain is required")
    if end <= WINDOW_SECONDS:
        return [(Fraction(0), end)]
    starts, cursor = set(), Fraction(0)
    while cursor + WINDOW_SECONDS <= end:
        starts.add(cursor)
        cursor += STRIDE_SECONDS
    starts.add(end - WINDOW_SECONDS)
    return [(start, start + WINDOW_SECONDS) for start in sorted(starts)]


def baseline_windows(physical_end):
    """Unchanged B0 equal nonoverlap views with ceil(T/30) source windows."""
    end = exact(physical_end) if not isinstance(physical_end, Fraction) else physical_end
    require(end > 0, "A positive physical source domain is required")
    count = (end.numerator + 30 * end.denominator - 1) // (30 * end.denominator)
    return [(end * index / count, end * (index + 1) / count) for index in range(count)]


def input_view_key(source, start, stop, ordinals, samples):
    """Prospective view identity only; does not attest actual encoded tensors."""
    value = dict(source_sha256=source["source_sha256"], video_id=source["video_id"],
                 window_start_exact=str(start), window_end_exact=str(stop),
                 source_frame_ordinals=ordinals, sample_exact_pts=samples)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return "view_" + hashlib.sha256(raw).hexdigest()


def _plan_sources(accepted, window_builder, mode):
    sources, total = [], 0
    for video_id, value in accepted.items():
        source, points, end = value["source"], value["points"], value["end"]
        windows = []
        for index, (start, stop) in enumerate(window_builder(end)):
            require(0 <= start < stop <= end, "Zero-length or out-of-domain candidate window")
            require(stop - start <= 30, "Every B0 native64 view must remain at most 30 seconds")
            first, limit = bisect_left(points, start), bisect_left(points, stop)
            count = limit - first
            require(count >= NATIVE_FRAMES, "Candidate window has fewer than 64 distinct native frames: " + video_id)
            ordinals = [first + sample * (count - 1) // (NATIVE_FRAMES - 1) for sample in range(NATIVE_FRAMES)]
            require(len(set(ordinals)) == NATIVE_FRAMES, "Native64 sampling must not repeat or pad frames")
            samples = [str(points[i]) for i in ordinals]
            windows.append(dict(case_id=f"{video_id}.{mode}{index:04d}", index=index,
                start_exact=str(start), end_exact=str(stop), eligible_first=first, eligible_stop=limit,
                source_frame_ordinals=ordinals, sample_exact_pts=samples,
                input_view_key=input_view_key(source, start, stop, ordinals, samples)))
        sources.append(dict(video_id=video_id, source_sha256=source["source_sha256"],
            physical_end_exact=str(end), n_frames=source["n_frames"], windows=windows))
        total += len(windows)
    return dict(schema=PLAN_SCHEMA if mode == "overlap" else BASELINE_PLAN_SCHEMA, mode=mode,
        native_frames=NATIVE_FRAMES, interval_policy="EXACT_HALF_OPEN_NO_PADDING",
        source_count=len(sources), window_count=total, sources=sources,
        hypothetical_B0_model_call_budget=total, VERIFY_model_call_budget_not_yet_known=True,
        model_calls=0, media_decodes=0, processor_encodes=0, GPU_admitted=False,
        scientific_quality_pass=False, status="PASS_PURE_" + mode.upper() + "_PLAN_NOT_INPUT_OR_GPU_ADMISSION")


def plan_baseline_sources(document):
    plan = _plan_sources(validate_sources(document), baseline_windows, "baseline")
    plan.update(window_policy="EQUAL_NONOVERLAP_CEIL_PHYSICAL_END_DIV_30", maximum_window_seconds_exact="30")
    return plan


def plan_overlapping_sources(document):
    accepted = validate_sources(document)
    plan = _plan_sources(accepted, fixed_windows, "overlap")
    baseline = _plan_sources(accepted, baseline_windows, "baseline")
    keys = lambda value: {window["input_view_key"] for source in value["sources"] for window in source["windows"]}
    overlap_keys, baseline_keys = keys(plan), keys(baseline)
    plan.update(window_seconds_exact=str(WINDOW_SECONDS), stride_seconds_exact=str(STRIDE_SECONDS),
        tail_policy="RIGHT_ALIGNED_EXACT_END_DEDUPLICATE", baseline_window_count=baseline["window_count"],
        baseline_shared_view_count=len(overlap_keys & baseline_keys),
        overlap_only_view_count=len(overlap_keys - baseline_keys),
        combined_unique_view_budget=len(overlap_keys | baseline_keys),
        overlap_B0_new_model_call_budget=len(overlap_keys - baseline_keys),
        new_candidate_VERIFY_upper_bound=5 * len(overlap_keys - baseline_keys),
        same_view_policy="ADOPT_ONE_ACTUAL_INPUT_AND_B0_ANSWER_NO_REPEAT")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("baseline", "overlap"), default="overlap")
    args = parser.parse_args()
    planner = plan_baseline_sources if args.mode == "baseline" else plan_overlapping_sources
    plan = planner(read_json_document(args.sources))
    write_json_document(args.output, plan)
    print(json.dumps({key: plan[key] for key in ("status", "source_count", "window_count", "GPU_admitted")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
