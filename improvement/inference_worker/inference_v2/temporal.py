"""Pure-CPU temporal parsing, prompting, and timeline utilities.

All intervals in this module are half-open: ``[start, end)``.  Frame
intervals are expressed on the original media timeline as
``[start_frame, end_frame_exclusive)``.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


Segment = Tuple[float, float]
FrameSegment = Tuple[int, int]


_SINGLE_GENERIC_PROMPT = (
    "This is a short video. Find the single most highlight-worthy clip "
    "that is worth keeping and re-framing, and give its time interval "
    "in seconds counted from the start of the video.\n"
    "Output ONLY JSON, no extra text, strictly: "
    '{"segments": [[start_sec, end_sec]]}'
)

_GENERIC_GOAL = "the most highlight-worthy moments worth keeping and re-framing"


@dataclass(frozen=True)
class ParseResult:
    """Result of strict model-output validation.

    ``valid_empty`` is a successful prediction.  ``invalid`` means the model
    did not satisfy the JSON/interval contract and must never be conflated
    with a deliberate empty list.
    """

    status: str
    segments: Tuple[Segment, ...] = ()
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {"valid", "valid_empty"}


def build_temporal_prompt(
    query: Optional[str], policy: str = "multi", duration_sec: Optional[float] = None
) -> str:
    """Build the exported stage-1 prompt used by inference and training.

    A generic ``single`` call is byte-for-byte compatible with the original
    baseline prompt.  Query-aware comparisons share the same goal/query
    template across policies; only the allowed number of returned clips
    changes.
    """
    if policy not in {"single", "multi", "windowed"}:
        raise ValueError(f"unknown temporal policy: {policy}")
    cleaned_query = " ".join(str(query).split()) if query is not None else ""
    if not cleaned_query and policy == "single":
        return _SINGLE_GENERIC_PROMPT
    goal = cleaned_query or _GENERIC_GOAL
    cardinality = "zero or one" if policy == "single" else "zero to four"
    context = (
        "Times must be local to this supplied video window. "
        if policy == "windowed" else
        "Times are counted from the start of the supplied video. "
    )
    if duration_sec is not None:
        if not math.isfinite(duration_sec) or duration_sec <= 0:
            raise ValueError("duration_sec must be positive and finite")
        time_limit = (
            f"Every clip must satisfy 0 <= start_sec < end_sec <= {duration_sec:.6f}. "
        )
    else:
        time_limit = "Every clip must satisfy 0 <= start_sec < end_sec. "
    if duration_sec is None or duration_sec >= 27.0:
        example = "{\"segments\":[[12.5,27.0]]}"
    else:
        example_end = max(0.002, float(duration_sec) * 0.8)
        example_start = max(0.001, min(example_end * 0.5, example_end - 0.001))
        example = json.dumps(
            {"segments": [[round(example_start, 3), round(example_end, 3)]]},
            separators=(",", ":"),
        )
    return (
        f"Selection goal: {goal}\n"
        "Find the non-overlapping, coherent video clips that best satisfy the "
        f"selection goal. Return {cardinality} clips in chronological order. "
        f"{context}{time_limit}Use half-open intervals [start_sec, end_sec).\n"
        "Each endpoint must be a JSON number in seconds, such as 12.5. Never "
        "use a string, timestamp text, or mm:ss. Output ONLY a JSON object "
        "with exactly the key segments and no extra text. Valid non-empty "
        f"example: {example}\nValid empty example: "
        '{"segments":[]}'
    )


def prompt_hashes() -> Dict[str, str]:
    """Return stable SHA-256 fingerprints for prompt comparison."""
    prompts = {
        "single_generic": build_temporal_prompt(None, "single"),
        "multi_generic": build_temporal_prompt(None, "multi"),
        "windowed_generic": build_temporal_prompt(None, "windowed"),
        "single_query_template": build_temporal_prompt("{query}", "single"),
        "multi_query_template": build_temporal_prompt("{query}", "multi"),
        "windowed_query_template": build_temporal_prompt("{query}", "windowed"),
        "multi_query_150s": build_temporal_prompt("{query}", "multi", 150.0),
        "windowed_query_30s": build_temporal_prompt("{query}", "windowed", 30.0),
    }
    return {
        key: hashlib.sha256(value.encode("utf-8")).hexdigest()
        for key, value in prompts.items()
    }


def temporal_json_schema(policy: str = "multi") -> Dict[str, Any]:
    """Public JSON schema; numeric semantics remain post-parse checks."""
    if policy not in {"single", "multi", "windowed"}:
        raise ValueError(f"unknown temporal policy: {policy}")
    return {
        "type": "object",
        "properties": {
            "segments": {
                "type": "array",
                "maxItems": 1 if policy == "single" else 4,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {"type": "number"},
                },
            },
        },
        "required": ["segments"],
        "additionalProperties": False,
    }


def temporal_json_regex(policy: str = "multi") -> str:
    """Compact JSON grammar used by lm-format-enforcer 0.11.3.

    Its JsonSchemaParser has an off-by-one bug for nested fixed-size arrays:
    ``maxItems: 4`` permits only three pairs. RegexParser preserves the exact
    requested 0..1/0..4 cardinality without mutating the dependency or lying
    in the public schema. Strict post-parse checks still own bounds and order.
    """
    if policy not in {"single", "multi", "windowed"}:
        raise ValueError(f"unknown temporal policy: {policy}")
    max_items = 1 if policy == "single" else 4
    number = r"(?:0|[1-9][0-9]{0,5})(?:\.[0-9]{1,6})?"
    pair = rf"\[{number},{number}\]"
    if max_items == 1:
        items = rf"(?:{pair})?"
    else:
        items = rf"(?:{pair}(?:,{pair}){{0,{max_items - 1}}})?"
    return rf'\{{"segments":\[{items}\]\}}'
def _strip_json_fence(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("```") and value.endswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            first = lines[0].strip().lower()
            if first in {"```", "```json"}:
                value = "\n".join(lines[1:-1]).strip()
    return value


def parse_segments_response(text: str, policy: str = "multi") -> ParseResult:
    """Parse and strictly validate a temporal model response.

    Booleans, strings, NaN/Infinity, zero/reversed intervals, overlapping
    intervals, unordered intervals, and policy cardinality violations are
    invalid.  Bound clipping is a separate media-aware operation.
    """
    if policy not in {"single", "multi", "windowed"}:
        return ParseResult("invalid", reason="unknown_policy")
    try:
        obj = json.loads(_strip_json_fence(text))
    except (json.JSONDecodeError, TypeError):
        return ParseResult("invalid", reason="invalid_json")
    if not isinstance(obj, dict) or set(obj) != {"segments"}:
        return ParseResult("invalid", reason="invalid_root_structure")
    values = obj["segments"]
    if not isinstance(values, list):
        return ParseResult("invalid", reason="segments_not_list")
    max_segments = 1 if policy == "single" else 4
    if len(values) > max_segments:
        return ParseResult("invalid", reason="too_many_segments")
    if not values:
        return ParseResult("valid_empty")

    segments: List[Segment] = []
    for value in values:
        if not isinstance(value, list) or len(value) != 2:
            return ParseResult("invalid", reason="invalid_segment_structure")
        start, end = value
        if (
            isinstance(start, bool) or isinstance(end, bool)
            or not isinstance(start, (int, float))
            or not isinstance(end, (int, float))
        ):
            return ParseResult("invalid", reason="segment_not_numeric")
        start_f, end_f = float(start), float(end)
        if not math.isfinite(start_f) or not math.isfinite(end_f):
            return ParseResult("invalid", reason="segment_nonfinite")
        if end_f <= start_f:
            return ParseResult("invalid", reason="segment_not_forward")
        if segments and start_f < segments[-1][1]:
            return ParseResult("invalid", reason="segments_unordered_or_overlapping")
        segments.append((start_f, end_f))
    return ParseResult("valid", tuple(segments))


def clip_segments(segments: Sequence[Segment], duration_sec: float) -> List[Segment]:
    """Clamp valid segments to media bounds and discard empty intersections."""
    if not math.isfinite(duration_sec) or duration_sec <= 0:
        return []
    out: List[Segment] = []
    for start, end in segments:
        a = max(0.0, min(float(start), duration_sec))
        b = max(0.0, min(float(end), duration_sec))
        if b > a:
            out.append((a, b))
    return out


def seconds_to_frame_segments(
    segments: Sequence[Segment], fps: float, n_frames: int
) -> List[FrameSegment]:
    """Map seconds to original-frame timestamp membership.

    A frame ``f`` is selected exactly when its timestamp ``f / fps`` belongs
    to the half-open seconds interval.  Returned end frames are exclusive.
    """
    if not math.isfinite(fps) or fps <= 0 or n_frames <= 0:
        return []
    out: List[FrameSegment] = []
    epsilon = 1e-9
    for start, end in segments:
        f0 = int(math.ceil(start * fps - epsilon))
        f1 = int(math.ceil(end * fps - epsilon))
        f0 = max(0, min(f0, n_frames))
        f1 = max(0, min(f1, n_frames))
        if f1 > f0:
            out.append((f0, f1))
    return out


def merge_overlapping_frame_segments(
    segments: Iterable[FrameSegment], n_frames: int
) -> List[FrameSegment]:
    """Dedupe true frame overlap without joining merely adjacent clips."""
    clean: List[FrameSegment] = []
    for start, end in segments:
        a = max(0, min(int(start), n_frames))
        b = max(0, min(int(end), n_frames))
        if b > a:
            clean.append((a, b))
    clean.sort()
    merged: List[List[int]] = []
    for start, end in clean:
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        elif merged and start == merged[-1][0] and end == merged[-1][1]:
            continue
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def canonicalize_segments(
    segments: Sequence[Segment], fps: float, n_frames: int,
    duration_sec: Optional[float] = None,
) -> Tuple[List[Segment], List[FrameSegment]]:
    """Bound, project, and deduplicate intervals on the original timeline."""
    if duration_sec is None:
        duration_sec = n_frames / fps if fps > 0 else 0.0
    bounded = clip_segments(segments, float(duration_sec))
    frames = merge_overlapping_frame_segments(
        seconds_to_frame_segments(bounded, fps, n_frames), n_frames
    )
    seconds = [
        (start / fps, min(float(duration_sec), end / fps))
        for start, end in frames
        if min(float(duration_sec), end / fps) > start / fps
    ]
    return seconds, frames


def plan_windows(
    duration_sec: float, window_sec: float = 30.0, step_sec: float = 25.0
) -> List[Segment]:
    """Plan overlapping reader windows, including the final partial window."""
    if (
        not math.isfinite(duration_sec) or duration_sec <= 0
        or not math.isfinite(window_sec) or window_sec <= 0
        or not math.isfinite(step_sec) or step_sec <= 0
    ):
        return []
    windows: List[Segment] = []
    start = 0.0
    while start < duration_sec:
        windows.append((start, min(duration_sec, start + window_sec)))
        if windows[-1][1] >= duration_sec:
            break
        start += step_sec
    return windows


def offset_window_segments(
    segments: Sequence[Segment], window_start: float, window_end: float
) -> List[Segment]:
    """Map local window intervals to global seconds after local clipping."""
    duration = max(0.0, window_end - window_start)
    return [
        (window_start + start, window_start + end)
        for start, end in clip_segments(segments, duration)
    ]
