"""Three-state temporal parsing and the single shared prompt/constraint source.

States
------
``VALID_NONEMPTY``  parsed, at least one interval, satisfies the constraint
``VALID_EMPTY``     parsed, explicitly zero intervals (a legal prediction)
``INVALID``         contract violation; carries reason codes, never silently
                    repaired and never converted into an empty prediction

The historical chain collapsed ``VALID_EMPTY`` into failure and then replaced
both with a centred-80% span.  Here the three states stay distinct; the legacy
fallback lives only in ``legacy_behavior`` for historical replay.

Segment counts are governed by one configurable :class:`SegmentConstraint`
shared by training and inference.  Labels that exceed it are *reported*, never
truncated or merged.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Optional, Sequence

HISTORICAL_QUANTIZE_DIGITS = 4
DURATION_TOLERANCE = 1e-3
_OBJ_RE = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*\}", re.S)


class SegmentState(str, Enum):
    VALID_NONEMPTY = "VALID_NONEMPTY"
    VALID_EMPTY = "VALID_EMPTY"
    INVALID = "INVALID"


@dataclass(frozen=True)
class SegmentConstraint:
    """One constraint object shared by prompt, parser, training and inference."""

    min_segments: int = 0
    max_segments: int = 5

    def __post_init__(self):
        if self.min_segments < 0 or self.max_segments < 0:
            raise ValueError("segment bounds must be non-negative")
        if self.min_segments > self.max_segments:
            raise ValueError("min_segments must not exceed max_segments")


@dataclass(frozen=True)
class ParseOutcome:
    state: SegmentState
    segments: tuple[tuple[float, float], ...]
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    decode_path: str
    detail: dict

    @property
    def is_usable(self) -> bool:
        """Both non-empty and explicitly-empty parses are usable predictions."""
        return self.state in (SegmentState.VALID_NONEMPTY, SegmentState.VALID_EMPTY)

    def as_dict(self) -> dict:
        return {
            "state": self.state.value,
            "segments": [list(s) for s in self.segments],
            "n_segments": len(self.segments),
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "decode_path": self.decode_path,
            "detail": self.detail,
        }


def build_prompt(*, duration_sec: float, constraint: SegmentConstraint) -> str:
    """The one prompt used by both training and inference.

    It explicitly allows the empty answer, so the model is never forced to
    invent an interval for a clip with no highlight.
    """
    if not math.isfinite(duration_sec) or duration_sec <= 0:
        raise ValueError("duration_sec must be positive and finite")
    empty_example = '{"segments":[]}'
    nonempty_example = json.dumps(
        {"segments": [[round(duration_sec * 0.2, 2), round(min(duration_sec, duration_sec * 0.6), 2)]]},
        separators=(",", ":"))
    if constraint.min_segments == 0:
        empty_rule = (f"- if nothing in this clip is worth keeping, return the empty list "
                      f"{empty_example}\n")
        empty_tail = f"\nEmpty example: {empty_example}"
    else:
        empty_rule = ""
        empty_tail = ""
    return (
        "You are shown a short video clip. Identify every time interval in the clip that is "
        "worth keeping in a short highlight edit.\n"
        "Times are seconds measured from the START of this clip, where 0 is the clip start.\n"
        'Return ONLY JSON of the form {"segments": [[start_sec, end_sec], ...]} using '
        "clip-local seconds.\n"
        "Rules:\n"
        f"- every interval must satisfy 0 <= start_sec < end_sec <= {duration_sec:.6f}\n"
        f"- return between {constraint.min_segments} and {constraint.max_segments} intervals\n"
        f"{empty_rule}"
        "- sort them by start time and do not let them overlap\n"
        "- output nothing except the JSON\n"
        f"Non-empty example: {nonempty_example}"
        f"{empty_tail}"
    )


def _strip_fence(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("```") and value.endswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            if lines[0].strip().lower() in {"```", "```json"}:
                value = "\n".join(lines[1:-1]).strip()
    return value


def _decode(text: str) -> tuple[Optional[dict], str, list[str]]:
    """Strict JSON first, then the historical object-scan as a named fallback.

    A non-object strict root (for example ``[{"segments": ...}]``) also falls
    through to the scan so that parsing stays consistent with the historical
    chain on already-recorded model text.
    """
    stripped = _strip_fence(text)
    strict_note: list[str] = []
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj, "strict_json", []
        strict_note = [f"strict root is {type(obj).__name__}, not an object"]
    except (json.JSONDecodeError, TypeError) as exc:
        strict_note = [f"strict json failed: {exc}"]
    found = None
    for candidate in _OBJ_RE.findall(text or ""):
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict) and "segments" in parsed:
            if found is not None:
                return None, "historical_object_scan", strict_note + [
                    "ambiguous: more than one JSON object with 'segments'"]
            found = parsed
    if found is None:
        return None, "historical_object_scan", strict_note + [
            "no JSON object containing 'segments'"]
    return found, "historical_object_scan", strict_note


def parse_response(
    raw: str,
    *,
    duration_sec: float,
    constraint: SegmentConstraint,
    quantize_digits: int = HISTORICAL_QUANTIZE_DIGITS,
    allow_historical_scan: bool = True,
) -> ParseOutcome:
    """Strict three-state parse of one model response."""
    detail: dict[str, Any] = {"duration_sec": duration_sec,
                              "constraint": {"min": constraint.min_segments,
                                             "max": constraint.max_segments},
                              "quantize_digits": quantize_digits}
    if not isinstance(raw, str) or not raw.strip():
        return ParseOutcome(SegmentState.INVALID, (), ("empty_model_output",), (), "none", detail)

    if allow_historical_scan:
        obj, path, decode_notes = _decode(raw)
    else:
        stripped = _strip_fence(raw)
        try:
            obj = json.loads(stripped)
            path = "strict_json"
            decode_notes = [] if isinstance(obj, dict) else [
                f"root is {type(obj).__name__}, not an object"]
            obj = obj if isinstance(obj, dict) else None
        except (json.JSONDecodeError, TypeError) as exc:
            obj, path, decode_notes = None, "strict_json", [f"strict json failed: {exc}"]

    if obj is None:
        return ParseOutcome(SegmentState.INVALID, (), tuple(decode_notes),
                            (), path, detail)
    if "segments" not in obj:
        return ParseOutcome(SegmentState.INVALID, (), ("missing_segments_key",),
                            (), path, detail)
    if len(obj) != 1:
        detail["extra_keys"] = sorted(k for k in obj if k != "segments")

    values = obj["segments"]
    if not isinstance(values, list):
        return ParseOutcome(SegmentState.INVALID, (),
                            (f"segments_not_list:{type(values).__name__}",), (), path, detail)

    n = len(values)
    detail["n_segments"] = n
    if n == 0:
        if constraint.min_segments > 0:
            return ParseOutcome(SegmentState.INVALID, (),
                                (f"empty_below_min_segments:{constraint.min_segments}",),
                                (), path, detail)
        return ParseOutcome(SegmentState.VALID_EMPTY, (), (), (), path, detail)
    if n > constraint.max_segments:
        return ParseOutcome(SegmentState.INVALID, (),
                            (f"too_many_segments:{n}>{constraint.max_segments}",), (), path, detail)

    segments: list[tuple[float, float]] = []
    reasons: list[str] = []
    warnings: list[str] = []
    for index, item in enumerate(values):
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            reasons.append(f"segment_{index}_not_two_elements")
            continue
        a, b = item
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (a, b)):
            reasons.append(f"segment_{index}_non_numeric")
            continue
        a_f, b_f = float(a), float(b)
        if not (math.isfinite(a_f) and math.isfinite(b_f)):
            reasons.append(f"segment_{index}_non_finite")
            continue
        if not 0 <= a_f < b_f:
            reasons.append(f"segment_{index}_not_0_le_start_lt_end")
            continue
        if b_f > duration_sec + DURATION_TOLERANCE:
            reasons.append(f"segment_{index}_exceeds_duration")
            continue
        segments.append((round(a_f, quantize_digits),
                         round(min(b_f, duration_sec), quantize_digits)))
    if reasons:
        return ParseOutcome(SegmentState.INVALID, (), tuple(reasons), tuple(warnings), path, detail)
    if not segments:
        return ParseOutcome(SegmentState.INVALID, (), ("no_usable_segment",), (), path, detail)

    segments.sort()
    for (a1, b1), (a2, b2) in zip(segments, segments[1:]):
        if a2 < b1 - 1e-9:
            warnings.append(f"overlapping_segments:[[{a1},{b1}],[{a2},{b2}]]")
    return ParseOutcome(SegmentState.VALID_NONEMPTY, tuple(segments), (), tuple(warnings), path, detail)


def union_length(segments: Sequence[Sequence[float]]) -> float:
    if not segments:
        return 0.0
    ordered = sorted((float(a), float(b)) for a, b in segments)
    total, cur_a, cur_b = 0.0, ordered[0][0], ordered[0][1]
    for a, b in ordered[1:]:
        if a <= cur_b + 1e-9:
            cur_b = max(cur_b, b)
        else:
            total += cur_b - cur_a
            cur_a, cur_b = a, b
    return total + (cur_b - cur_a)


def check_label_cardinality(rows: Iterable[dict], *, constraint: SegmentConstraint,
                            key: str = "segments_clip_local") -> dict:
    """Report label rows that break the shared constraint. Never edits the rows."""
    n_rows = 0
    histogram: dict[str, int] = {}
    violations = []
    for row in rows:
        n_rows += 1
        segments = row.get(key) or []
        n = len(segments)
        histogram[str(n)] = histogram.get(str(n), 0) + 1
        if n < constraint.min_segments or n > constraint.max_segments:
            violations.append({
                "sample_id": row.get("sample_id"),
                "row_index": row.get("row_index"),
                "n_segments": n,
                "action": "REPORTED_UNCHANGED",
            })
    return {
        "n_rows": n_rows,
        "histogram": dict(sorted(histogram.items(), key=lambda kv: int(kv[0]))),
        "constraint": {"min": constraint.min_segments, "max": constraint.max_segments},
        "n_violations": len(violations),
        "violations": violations,
        "note": ("violating rows are reported and left byte-identical; no truncation, "
                 "no merging, no dropping"),
    }


def legacy_behavior(raw: str, *, duration_sec: float, max_segments: int = 5) -> dict:
    """Historical round-5 behaviour, kept for replay comparison only.

    Reproduces: empty list -> parse failure, >max -> failure, any bad segment ->
    failure, and (in the composer) both failures -> centred 80% of the window.
    """
    outcome = parse_response(raw, duration_sec=duration_sec,
                             constraint=SegmentConstraint(0, max_segments))
    if outcome.state is SegmentState.VALID_NONEMPTY:
        return {"legacy_output_valid": True, "legacy_segments": [list(s) for s in outcome.segments],
                "legacy_reason": None}
    if outcome.state is SegmentState.VALID_EMPTY:
        return {"legacy_output_valid": False, "legacy_segments": None,
                "legacy_reason": "'segments' is empty"}
    return {"legacy_output_valid": False, "legacy_segments": None,
            "legacy_reason": "; ".join(outcome.reasons)}
