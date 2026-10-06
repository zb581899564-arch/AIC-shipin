"""Internal diagnostic implementation of the AIC per-video F score.

This is deliberately named and reported as an internal diagnostic metric.  It
must not be presented as the official evaluator: the AIC task page documents
the formula and says that a basic evaluator exists, but neither that page nor
the pinned TempSamp-R1 repository exposes the evaluator source or test labels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
import math
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .schema import (
    BBox,
    ValidatedPrediction,
    VideoMeta,
    load_jsonl_records,
    load_media_metadata,
    validate_submission_records,
)


@dataclass(frozen=True)
class VideoMetric:
    video_id: str
    s_iou: float
    n_pred: int
    n_gt: int
    precision: float
    recall: float
    f1: float
    duplicate_predictions: int
    unmatched_predictions: int
    missed_ground_truth: int

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def spatial_iou(left: BBox, right: BBox) -> float:
    """Axis-aligned IoU for source-pixel [x, y, w, h] boxes."""

    left_x2 = left.x + left.w
    left_y2 = left.y + left.h
    right_x2 = right.x + right.w
    right_y2 = right.y + right.h
    ix1 = max(left.x, right.x)
    iy1 = max(left.y, right.y)
    ix2 = min(left_x2, right_x2)
    iy2 = min(left_y2, right_y2)
    intersection = max(ix2 - ix1, 0.0) * max(iy2 - iy1, 0.0)
    union = left.w * left.h + right.w * right.h - intersection
    return intersection / union if union > 0 else 0.0


def _bbox_from_value(value: Any, meta: VideoMeta, location: str) -> BBox:
    if isinstance(value, Mapping):
        value = value.get("bboxes", value.get("bbox"))
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{location}: ground truth box must be [x, y, w]")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise ValueError(f"{location}: ground truth box values must be numeric")
    x, y, w = (float(item) for item in value)
    if not all(math.isfinite(item) for item in (x, y, w)) or x < 0 or y < 0 or w <= 0:
        raise ValueError(f"{location}: invalid ground truth box values")
    tw, th = meta.target_ratio_wh
    h = w * th / tw
    if x + w > meta.width + 1e-9 or y + h > meta.height + 1e-9:
        raise ValueError(f"{location}: ground truth box is outside media bounds")
    return BBox(x, y, w, h)


def _gt_records(payload: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping) and isinstance(payload.get("records"), list):
        return payload["records"]
    if isinstance(payload, Mapping) and payload and all(isinstance(value, (Mapping, list)) for value in payload.values()):
        records = []
        for video_id, value in payload.items():
            records.append(value if isinstance(value, Mapping) else {"frames": value, "video_id": video_id})
            if isinstance(value, Mapping) and "video_id" not in value:
                records[-1] = dict(value, video_id=video_id)
        return records
    raise ValueError("ground truth must be a list, {records: [...]}, or an id mapping")


def _strict_frame(value: Any, location: str) -> int:
    """Accept integer frame indices only; never truncate float/bool labels."""

    if isinstance(value, bool):
        raise ValueError(f"{location}: frame must be an integer, not bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value.strip()):
        return int(value)
    raise ValueError(f"{location}: frame must be an integer")


def _frame_rows(record: Mapping[str, Any]) -> Iterable[Tuple[int, Any]]:
    frames = record.get("frames", record.get("annotations", record.get("ground_truth")))
    if frames is None and isinstance(record.get("gt"), Mapping):
        frames = record["gt"].get("frames", record["gt"].get("annotations"))
    if isinstance(frames, Mapping):
        for frame, value in frames.items():
            yield _strict_frame(frame, "ground truth frame key"), value
        return
    if not isinstance(frames, list):
        raise ValueError("ground truth record must contain frames/annotations")
    for index, value in enumerate(frames):
        if not isinstance(value, Mapping) or "frame" not in value:
            raise ValueError(f"ground truth frame item {index} must contain frame")
        yield _strict_frame(value["frame"], f"ground truth frame item {index}"), value.get("bboxes", value.get("bbox"))


def parse_ground_truth(
    payload: Any,
    metadata: Mapping[str, VideoMeta],
) -> Dict[str, Dict[int, BBox]]:
    """Parse a small, explicit diagnostic-GT format.

    Accepted forms are ``{"records": [{"video_id": ..., "frames":
    [{"frame": 1, "bboxes": [x,y,w]}]}]}`` and equivalent id mappings.
    This parser is for synthetic/dev labels only; the contest test labels are
    not available to the team.
    """

    result: Dict[str, Dict[int, BBox]] = {}
    for record_index, record in enumerate(_gt_records(payload)):
        if not isinstance(record, Mapping) or record.get("video_id") is None:
            raise ValueError(f"ground truth record {record_index} has no video_id")
        video_id = str(record["video_id"])
        if video_id not in metadata:
            raise ValueError(f"ground truth contains unknown video_id {video_id!r}")
        if video_id in result:
            raise ValueError(f"duplicate ground truth video_id {video_id!r}")
        by_frame: Dict[int, BBox] = {}
        meta = metadata[video_id]
        for frame, value in _frame_rows(record):
            if frame < 0 or frame >= meta.n_frames:
                raise ValueError(f"ground truth {video_id!r} frame {frame} is out of range")
            if frame in by_frame:
                raise ValueError(f"duplicate ground truth frame {video_id!r}:{frame}")
            by_frame[frame] = _bbox_from_value(value, meta, f"ground truth {video_id!r}:{frame}")
        result[video_id] = by_frame
    return result


def _zero_case(n_pred: int, n_gt: int, s_iou: float) -> Tuple[float, float, float]:
    if n_pred == 0 and n_gt == 0:
        return 1.0, 1.0, 1.0
    if n_pred == 0 or n_gt == 0:
        return 0.0, 0.0, 0.0
    return s_iou / n_pred, s_iou / n_gt, 2.0 * s_iou / (n_pred + n_gt)


def score_predictions(
    predictions: Sequence[ValidatedPrediction],
    ground_truth: Mapping[str, Mapping[int, BBox]],
    metadata: Mapping[str, VideoMeta],
    *,
    require_complete_gt: bool = True,
) -> Dict[str, Any]:
    """Score schema-valid predictions with an explicitly diagnostic policy.

    For each video, ``n_pred`` includes every schema-valid prediction,
    including valid wrong-frame predictions and duplicate frames.  Only the
    first valid prediction for a frame contributes to ``S``; later valid
    duplicates remain in ``n_pred`` and therefore lower F.  Invalid rows are
    excluded before this function and are reported by the validator.
    """

    metadata_ids = set(metadata)
    gt_ids = set(ground_truth)
    unknown_gt = sorted(gt_ids - metadata_ids)
    if unknown_gt:
        raise ValueError(f"ground truth contains unknown IDs: {unknown_gt}")
    missing_gt = sorted(metadata_ids - gt_ids)
    if require_complete_gt and missing_gt:
        raise ValueError(f"ground truth is missing indexed IDs: {missing_gt[:10]}")

    grouped: Dict[str, List[ValidatedPrediction]] = {video_id: [] for video_id in metadata}
    for prediction in predictions:
        if prediction.video_id not in metadata:
            raise ValueError(f"prediction contains unknown video_id {prediction.video_id!r}")
        grouped[prediction.video_id].append(prediction)

    per_video: List[VideoMetric] = []
    for video_id, meta in metadata.items():
        rows = grouped[video_id]
        gt_frames = dict(ground_truth.get(video_id, {}))
        n_pred = len(rows)
        n_gt = len(gt_frames)
        seen_frames: set[int] = set()
        s_iou = 0.0
        duplicate_count = 0
        unmatched_count = 0
        matched_frames: set[int] = set()
        for row in rows:
            if row.frame in seen_frames:
                duplicate_count += 1
                continue
            seen_frames.add(row.frame)
            gt_box = gt_frames.get(row.frame)
            if gt_box is None:
                unmatched_count += 1
                continue
            s_iou += spatial_iou(row.bbox, gt_box)
            matched_frames.add(row.frame)
        precision, recall, f1 = _zero_case(n_pred, n_gt, s_iou)
        per_video.append(
            VideoMetric(
                video_id=video_id,
                s_iou=s_iou,
                n_pred=n_pred,
                n_gt=n_gt,
                precision=precision,
                recall=recall,
                f1=f1,
                duplicate_predictions=duplicate_count,
                unmatched_predictions=unmatched_count,
                missed_ground_truth=n_gt - len(matched_frames),
            )
        )

    mean_f1 = sum(item.f1 for item in per_video) / len(per_video) if per_video else 0.0
    return {
        "metric_name": "aic_internal_diagnostic_video_equal_f1",
        "official_status": "internal_diagnostic",
        "official_evaluator_source_found": False,
        "formula": {
            "s": "sum IoU over first schema-valid prediction at each same-video/same-frame pair",
            "precision": "S / Npred",
            "recall": "S / Ngt",
            "f1": "2*S / (Npred + Ngt)",
            "aggregation": "equal mean of per-video F1 multiplied by 100",
            "both_empty": 1.0,
            "one_empty": 0.0,
        },
        "diagnostic_policy": {
            "duplicate": "first valid prediction contributes; later valid duplicates remain Npred false positives",
            "invalid_rows": "excluded from Npred and reported by schema validator",
            "unknown_video_id": "excluded from scoring and reported as an error",
            "frame_bound": "0 <= frame < n_frames",
        },
        "videos": [item.as_dict() for item in per_video],
        "video_count": len(per_video),
        "mean_f1": mean_f1,
        "score_percent": mean_f1 * 100.0,
    }


def _load_ground_truth(path: Union[str, Path], metadata: Mapping[str, VideoMeta]) -> Dict[str, Dict[int, BBox]]:
    with open(path, "r", encoding="utf-8") as handle:
        return parse_ground_truth(json.load(handle), metadata)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AIC internal diagnostic scorer; not the official evaluator")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    metadata = load_media_metadata(args.metadata)
    records, parse_issues = load_jsonl_records(args.predictions)
    validation = validate_submission_records(records, metadata)
    result: Dict[str, Any] = {
        "official_status": "internal_diagnostic",
        "validation": validation.as_dict(include_predictions=False),
        "parse_issues": parse_issues,
    }
    if validation.ok and not parse_issues:
        ground_truth = _load_ground_truth(args.ground_truth, metadata)
        result["metric"] = score_predictions(validation.valid_predictions, ground_truth, metadata)
        exit_code = 0
    else:
        result["metric"] = None
        exit_code = 2
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": exit_code == 0, "out": str(args.out), "official_status": "internal_diagnostic"}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
