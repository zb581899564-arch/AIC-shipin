"""Independent validation for the AIC highlight re-framing JSONL format.

The official page describes the shape of a submission, but the official
evaluator source was not published at the time this module was written.  This
module therefore exposes a deterministic *diagnostic* validator.  It keeps
schema-valid duplicate and wrong-frame predictions so that the companion
diagnostic metric can account for their false-positive cost.

Only the Python standard library is required.  Media metadata is supplied by
the inference worker (currently ``reports/supervisor_test_metadata.json``),
and is treated as an index, never as ground truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union


@dataclass(frozen=True)
class BBox:
    """A source-pixel box after deriving height from the target ratio."""

    x: float
    y: float
    w: float
    h: float

    def as_list(self) -> List[float]:
        return [self.x, self.y, self.w, self.h]


@dataclass(frozen=True)
class VideoMeta:
    video_id: str
    target_ratio_wh: Tuple[float, float]
    width: int
    height: int
    n_frames: int
    video_path: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["target_ratio_wh"] = list(self.target_ratio_wh)
        return result


@dataclass(frozen=True)
class ValidatedPrediction:
    video_id: str
    frame: int
    bbox: BBox
    line_number: int
    prediction_index: int
    duplicate_frame: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "frame": self.frame,
            "bbox": self.bbox.as_list(),
            "line_number": self.line_number,
            "prediction_index": self.prediction_index,
            "duplicate_frame": self.duplicate_frame,
        }


@dataclass
class ValidationReport:
    """Structured result; ``valid_predictions`` is intentionally separate."""

    ok: bool
    line_count: int
    video_count: int
    valid_prediction_count: int
    issues: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    valid_predictions: List[ValidatedPrediction]

    def as_dict(self, include_predictions: bool = False) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ok": self.ok,
            "line_count": self.line_count,
            "video_count": self.video_count,
            "valid_prediction_count": self.valid_prediction_count,
            "error_count": sum(1 for issue in self.issues if issue["severity"] == "error"),
            "warning_count": sum(1 for issue in self.issues if issue["severity"] == "warning"),
            "issues": self.issues,
            "rows": self.rows,
        }
        if include_predictions:
            result["valid_predictions"] = [item.as_dict() for item in self.valid_predictions]
        return result


class MetadataError(ValueError):
    """Raised when the fixed index/media metadata cannot be trusted."""


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _positive_int(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def _ratio(value: Any) -> Optional[Tuple[float, float]]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    if not all(_finite_number(item) for item in value):
        return None
    tw, th = float(value[0]), float(value[1])
    if tw <= 0 or th <= 0:
        return None
    return tw, th


def _field(record: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in record:
            return record[name]
    return None


def _issue(
    issues: List[Dict[str, Any]],
    location: str,
    code: str,
    message: str,
    severity: str = "error",
) -> None:
    issues.append({
        "location": location,
        "code": code,
        "message": message,
        "severity": severity,
    })


def _metadata_records(payload: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    # A compact id -> metadata mapping is convenient for synthetic tests.
    if isinstance(payload, dict) and payload and all(isinstance(value, dict) for value in payload.values()):
        return [dict(value, video_id=key) for key, value in payload.items()]
    raise MetadataError("metadata must be a list, {records: [...]}, or an id mapping")


def parse_media_metadata(payload: Any) -> Dict[str, VideoMeta]:
    """Parse B's fixed media index without reading video bytes."""

    result: Dict[str, VideoMeta] = {}
    for index, record in enumerate(_metadata_records(payload)):
        if not isinstance(record, Mapping):
            raise MetadataError(f"metadata record {index} is not an object")
        raw_id = record.get("video_id")
        if raw_id is None:
            raise MetadataError(f"metadata record {index} has no video_id")
        video_id = str(raw_id)
        if video_id in result:
            raise MetadataError(f"duplicate metadata video_id: {video_id}")

        ratio = _ratio(record.get("targetRatioWH"))
        width = record.get("width")
        height = record.get("height")
        n_frames = _field(record, "n_frames", "frame_count", "num_frames")
        if ratio is None:
            raise MetadataError(f"metadata record {video_id} has invalid targetRatioWH")
        if not _positive_int(width) or not _positive_int(height) or not _positive_int(n_frames):
            raise MetadataError(f"metadata record {video_id} has invalid dimensions/frame count")
        result[video_id] = VideoMeta(
            video_id=video_id,
            target_ratio_wh=ratio,
            width=width,
            height=height,
            n_frames=n_frames,
            video_path=(str(record["video_path"]) if record.get("video_path") is not None else None),
        )
    if not result:
        raise MetadataError("metadata has no records")
    return result


def load_media_metadata(path: Union[str, Path]) -> Dict[str, VideoMeta]:
    with open(path, "r", encoding="utf-8") as handle:
        return parse_media_metadata(json.load(handle))


def _same_ratio(left: Tuple[float, float], right: Tuple[float, float]) -> bool:
    # Ratios come from a small fixed index.  Tolerance only protects JSON
    # decimal encodings; it does not allow a different requested orientation.
    return math.isclose(left[0], right[0], rel_tol=1e-9, abs_tol=1e-12) and math.isclose(
        left[1], right[1], rel_tol=1e-9, abs_tol=1e-12
    )


def _parse_bbox(
    value: Any,
    meta: VideoMeta,
    location: str,
    issues: List[Dict[str, Any]],
) -> Optional[BBox]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        _issue(issues, location, "BBOX_SHAPE", "bboxes must be a single [x, y, w] triplet")
        return None
    if not all(_finite_number(item) for item in value):
        _issue(issues, location, "NON_FINITE", "bboxes values must be finite numbers")
        return None
    x, y, w = (float(item) for item in value)
    if x < 0 or y < 0 or w <= 0:
        _issue(issues, location, "BBOX_SIGN", "require x >= 0, y >= 0, and w > 0")
        return None
    tw, th = meta.target_ratio_wh
    h = w * th / tw
    if x + w > meta.width + 1e-9 or y + h > meta.height + 1e-9:
        _issue(
            issues,
            location,
            "BOX_OUT_OF_BOUNDS",
            f"derived box [x,y,w,h] exceeds source {meta.width}x{meta.height}",
        )
        return None
    return BBox(x=x, y=y, w=w, h=h)


def validate_submission_records(
    records: Iterable[Any],
    metadata: Mapping[str, VideoMeta],
    *,
    require_complete: bool = True,
) -> ValidationReport:
    """Validate decoded JSONL records and return schema-valid predictions.

    A duplicate frame is a warning, not a schema rejection: the metric needs
    to see every valid occurrence to apply the documented first-valid-wins /
    remaining-false-positive convention.  Invalid bboxes are omitted from the
    metric input and retained in ``issues``.
    """

    issues: List[Dict[str, Any]] = []
    rows: List[Dict[str, Any]] = []
    valid_predictions: List[ValidatedPrediction] = []
    seen_video_lines: Dict[str, int] = {}
    seen_video_ids: set[str] = set()
    line_count = 0

    for line_number, record in enumerate(records, start=1):
        line_count += 1
        location = f"line[{line_number}]"
        row_result: Dict[str, Any] = {"line_number": line_number, "valid": False}
        rows.append(row_result)
        if not isinstance(record, Mapping):
            _issue(issues, location, "ROW_SHAPE", "each JSONL line must be an object")
            continue
        if "video_id" not in record:
            _issue(issues, location, "MISSING_VIDEO_ID", "video_id is required")
            continue
        video_id = str(record["video_id"])
        row_result["video_id"] = video_id
        if video_id not in metadata:
            _issue(issues, location, "UNKNOWN_VIDEO_ID", f"video_id {video_id!r} is absent from the fixed index")
            continue
        if video_id in seen_video_lines:
            _issue(
                issues,
                location,
                "DUPLICATE_VIDEO_ID",
                f"video_id already appeared on line {seen_video_lines[video_id]}",
            )
        else:
            seen_video_lines[video_id] = line_number
        seen_video_ids.add(video_id)
        meta = metadata[video_id]

        target = _ratio(record.get("targetRatioWH"))
        if target is None:
            _issue(issues, location, "TARGET_RATIO_SHAPE", "targetRatioWH must be two positive finite numbers")
            continue
        if not _same_ratio(target, meta.target_ratio_wh):
            _issue(
                issues,
                location,
                "TARGET_RATIO_MISMATCH",
                f"targetRatioWH {list(target)} does not match fixed index {list(meta.target_ratio_wh)}",
            )
            continue
        predictions = record.get("predictions")
        if not isinstance(predictions, list):
            _issue(issues, location, "PREDICTIONS_SHAPE", "predictions must be an array")
            continue

        row_result["valid"] = True
        row_result["prediction_count"] = len(predictions)
        seen_frames: set[int] = set()
        valid_row_count = 0
        for prediction_index, prediction in enumerate(predictions):
            pred_location = f"{location}.predictions[{prediction_index}]"
            if not isinstance(prediction, Mapping):
                _issue(issues, pred_location, "PREDICTION_SHAPE", "prediction must be an object")
                continue
            frame = prediction.get("frame")
            if not isinstance(frame, int) or isinstance(frame, bool):
                _issue(issues, pred_location, "FRAME_TYPE", "frame must be an integer")
                continue
            if frame < 0 or frame >= meta.n_frames:
                _issue(
                    issues,
                    pred_location,
                    "FRAME_OUT_OF_RANGE",
                    f"frame must satisfy 0 <= frame < {meta.n_frames}",
                )
                continue
            bbox = _parse_bbox(prediction.get("bboxes"), meta, pred_location, issues)
            if bbox is None:
                continue
            duplicate = frame in seen_frames
            if duplicate:
                _issue(
                    issues,
                    pred_location,
                    "DUPLICATE_FRAME",
                    "duplicate frame retained as a false-positive candidate by the diagnostic metric",
                    severity="warning",
                )
            seen_frames.add(frame)
            valid_predictions.append(
                ValidatedPrediction(
                    video_id=video_id,
                    frame=frame,
                    bbox=bbox,
                    line_number=line_number,
                    prediction_index=prediction_index,
                    duplicate_frame=duplicate,
                )
            )
            valid_row_count += 1
        row_result["valid_prediction_count"] = valid_row_count

    if require_complete:
        missing = sorted(set(metadata) - seen_video_ids)
        for video_id in missing:
            _issue(issues, "submission", "MISSING_VIDEO_ID", f"no output line for indexed video_id {video_id!r}")

    ok = not any(issue["severity"] == "error" for issue in issues)
    return ValidationReport(
        ok=ok,
        line_count=line_count,
        video_count=len(seen_video_ids),
        valid_prediction_count=len(valid_predictions),
        issues=issues,
        rows=rows,
        valid_predictions=valid_predictions,
    )


def load_jsonl_records(path: Union[str, Path]) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """Load JSONL while retaining parse errors as line-scoped issues."""

    records: List[Any] = []
    parse_issues: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                parse_issues.append({
                    "location": f"line[{line_number}]",
                    "code": "BLANK_LINE",
                    "message": "blank JSONL lines are not submission records",
                    "severity": "error",
                })
                continue
            try:
                records.append(json.loads(raw_line))
            except json.JSONDecodeError as exc:
                parse_issues.append({
                    "location": f"line[{line_number}]",
                    "code": "JSON_PARSE",
                    "message": str(exc),
                    "severity": "error",
                })
    return records, parse_issues
