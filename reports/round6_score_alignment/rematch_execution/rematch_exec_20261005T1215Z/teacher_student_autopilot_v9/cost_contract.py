"""Measured incremental output estimates, excluding already stored pilot bytes."""
import math
from pathlib import Path


def directory_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file())


def teacher_remaining_cost(teacher_dir, probe_ids, total_windows, accepted_ids=()):
    root = Path(teacher_dir)
    if not probe_ids or len(set(probe_ids)) != len(probe_ids) or total_windows < len(probe_ids):
        raise ValueError("unique measured probe identities and full denominator required")
    measured = [root / "windows" / i for i in probe_ids]
    if not all((p/"done.json").is_file() and (p/"http/request.json").is_file() for p in measured):
        raise ValueError("complete measured probe window evidence required")
    existing = set(accepted_ids) | {p.parent.name for p in (root/"windows").glob("*/done.json")}
    if len(existing) > total_windows:
        raise ValueError("cached label denominator exceeds registered population")
    label_unit = max(directory_bytes(p) for p in measured)
    request_unit = max((p/"http/request.json").stat().st_size for p in measured)
    remaining = total_windows - len(existing)
    # Review requests include the same original image payload and the original
    # answer. The twofold allowance covers measured payload growth/logs; no
    # already stored PNG, request, or pilot result is charged as new output.
    planned = remaining * label_unit * 2 + total_windows * request_unit * 2 + 20_000_000
    return {"planned_output_bytes":planned, "remaining_label_windows":remaining,
        "existing_label_windows":len(existing), "measured_probe_window_count":len(measured),
        "measured_probe_window_bytes":[directory_bytes(p) for p in measured],
        "maximum_measured_label_bytes":label_unit, "maximum_measured_request_bytes":request_unit,
        "full_review_windows":total_windows, "already_stored_bytes_charged_again":False}


def measured_spatial_cost(receipts):
    for path, value in receipts:
        seconds = value.get("measured_seconds_per_anchor")
        if (value.get("status") == "PASS_STRICT_SOURCE_FIELD_SPATIAL" and value.get("invalid") == 0
                and value.get("model_calls",0) > 0 and type(seconds) in (int,float)
                and math.isfinite(seconds) and seconds > 0):
            return str(path), seconds
    raise ValueError("no actual successful non-test spatial measurement; empty stages provide no model timing")
