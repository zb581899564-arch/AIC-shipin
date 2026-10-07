"""Stdlib-only next-round prediction contracts; no output repair or inference.

Empty segments are a valid prediction when enabled. This module does not
establish complete-observation supervision and cannot turn UNKNOWN into [].
"""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import json
import math


MODEL_OK = "MODEL_OK"
LEGAL_EMPTY = "LEGAL_EMPTY"
PARSE_FAILURE = "PARSE_FAILURE"
INFERENCE_FAILURE = "INFERENCE_FAILURE"

EMPTY_PROMPT = (
    "You are shown a short video clip. Identify every time interval in the clip that is "
    "worth keeping in a short highlight edit.\n"
    "Times are seconds measured from the START of this clip, where 0 is the clip start.\n"
    'Return ONLY JSON of the form {"segments": [[start_sec, end_sec], ...]} using '
    "clip-local seconds.\n"
    "Rules:\n"
    "- every interval must satisfy 0 <= start_sec < end_sec <= clip duration\n"
    "- return between 0 and 5 intervals\n"
    "- sort them by start time and do not let them overlap\n"
    '- when the clip has no worthwhile highlight, return {"segments": []}\n'
    "- uncertainty or insufficient observation is not evidence of no highlight; "
    "do not use an empty list to represent uncertainty\n"
    "- output nothing except the JSON"
)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def _strict_json(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("empty or non-string model output")
    # Decode the entire document. Fences, prose, multiple objects, duplicate
    # keys and JavaScript NaN/Infinity never become a prediction.
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_float=Decimal, parse_constant=_reject_constant)


def parse_focus_norm(text, W=None, H=None):
    """Return the center in [0,1], or None for a strict-contract failure.

    W/H only preserve the old call signature. The declared coordinate unit is
    always an integer in 0..1000 for both axes, independently of image size.
    """
    del W, H
    try:
        obj = _strict_json(text)
    except (TypeError, ValueError, RecursionError):
        return None
    if not isinstance(obj, dict) or set(obj) != {"center"}:
        return None
    center = obj["center"]
    if (not isinstance(center, list) or len(center) != 2 or
            any(type(value) is not int or not 0 <= value <= 1000 for value in center)):
        return None
    return [value / 1000.0 for value in center]


def _duration_fraction(duration):
    if type(duration) is int:
        value = Fraction(duration)
    elif type(duration) is float and math.isfinite(duration):
        value = Fraction(str(duration))
    elif isinstance(duration, Fraction):
        value = duration
    else:
        raise ValueError("duration must be a finite positive number")
    if value <= 0:
        raise ValueError("duration must be a finite positive number")
    return value


def _options(duration, max_segments, allow_empty):
    value = _duration_fraction(duration)
    if type(max_segments) is not int or not 1 <= max_segments <= 5:
        raise ValueError("max_segments must be an integer in 1..5")
    if type(allow_empty) is not bool:
        raise ValueError("allow_empty must be a bool")
    return value


def validate_segments(segments, duration, max_segments=5, allow_empty=True):
    """Validate and return the original list; reject instead of repairing.

    This is only geometry/format validation. An empty *training* target still
    requires separately verified complete-observation, no-highlight evidence.
    """
    end = _options(duration, max_segments, allow_empty)
    if not isinstance(segments, list):
        raise ValueError("segments must be a list")
    if not segments and not allow_empty:
        raise ValueError("empty segments are disabled by this protocol")
    if len(segments) > max_segments:
        raise ValueError("segment count exceeds the protocol maximum")
    previous_end = Fraction(0)
    for index, segment in enumerate(segments):
        if not isinstance(segment, list) or len(segment) != 2:
            raise ValueError(f"segment {index} must be a two-element list")
        if any(type(value) not in (int, float) or
               (type(value) is float and not math.isfinite(value)) for value in segment):
            raise ValueError(f"segment {index} bounds must be finite numbers, not bools")
        start, stop = (Fraction(str(value)) for value in segment)
        if not 0 <= start < stop <= end:
            raise ValueError(f"segment {index} violates 0 <= start < end <= duration")
        if start < previous_end:
            raise ValueError(f"segment {index} is unsorted or overlaps its predecessor")
        previous_end = stop
    return segments


# Old callers used this name for target validation.
segments_valid = validate_segments


def _json_number(value):
    if type(value) is int:
        return value
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("bounds must be JSON numbers, not bools or strings")
    numeric = float(value)
    if not math.isfinite(numeric) or Fraction(str(numeric)) != Fraction(value):
        raise ValueError("JSON bound cannot be represented without numeric precision loss")
    return numeric


def parse_segments(raw, duration, max_segments=5, allow_empty=True):
    """Return (segments|None, errors, warnings) with no repairs or fallback.

    A valid empty result is ([], [], []), whereas a failure is (None, [...], []).
    Original order and endpoints remain binding; excess, invalid, overlapping
    or unsorted segments fail the whole prediction.
    """
    try:
        _options(duration, max_segments, allow_empty)
        obj = _strict_json(raw)
        if not isinstance(obj, dict) or set(obj) != {"segments"}:
            raise ValueError("expected only a JSON object with the key 'segments'")
        if not isinstance(obj["segments"], list):
            raise ValueError("segments must be a list")
        segments = []
        for index, segment in enumerate(obj["segments"]):
            if not isinstance(segment, list) or len(segment) != 2:
                raise ValueError(f"segment {index} must be a two-element list")
            segments.append([_json_number(value) for value in segment])
        validate_segments(segments, duration, max_segments, allow_empty)
        return segments, [], []
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        return None, [str(exc)], []


def _canonical_number(value):
    units = Fraction(str(value)) * 10_000
    if units.denominator != 1:
        raise ValueError("target endpoint is not representable at four-decimal precision")
    integer, fractional = divmod(units.numerator, 10_000)
    return str(integer) + ("." + f"{fractional:04d}".rstrip("0") if fractional else "")


def answer_string(segments, duration, max_segments=5, allow_empty=True):
    """Serialize a valid target into the generation grammar without rounding."""
    validate_segments(segments, duration, max_segments, allow_empty)
    intervals = ["[" + ",".join(_canonical_number(value) for value in segment) + "]"
                 for segment in segments]
    return '{"segments":[' + ",".join(intervals) + "]}"


def classify_temporal_result(raw, duration, max_segments=5, allow_empty=True,
                             inference_error=None):
    """Keep legal empty, parse failure and failed execution distinct."""
    if inference_error is not None:
        return {"status": INFERENCE_FAILURE, "output_valid": False,
                "parsed_segments": None, "parse_errors": [], "parse_warnings": [],
                "inference_error": str(inference_error)}
    segments, errors, warnings = parse_segments(raw, duration, max_segments, allow_empty)
    status = PARSE_FAILURE if segments is None else LEGAL_EMPTY if not segments else MODEL_OK
    return {"status": status, "output_valid": segments is not None,
            "parsed_segments": segments, "parse_errors": errors, "parse_warnings": warnings,
            "inference_error": None}
