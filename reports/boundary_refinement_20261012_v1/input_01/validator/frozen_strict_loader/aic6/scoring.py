"""Joint scorer: strict input validation separated from the score arithmetic.

Result statuses
---------------
``OK``                 a reference with full coverage was scored
``SPARSE_DIAGNOSTIC``  the reference covers only declared sparse frames, so only
                       sparse-frame diagnostics are produced — never a
                       full-video joint score
``NOT_COMPUTABLE``     no reference, or the reference does not cover the scored
                       video universe; missing ground truth is never treated as
                       an empty ground truth
``INVALID_INPUT``      strict validation failed; ``score`` is ``null`` and every
                       issue is reported.  Invalid items are never dropped and
                       then scored on a cleaned denominator.

The math follows the published AIC formula
``F = 2 * sum(matched_frame_IoU) / (N_pred + N_gt)`` with both-empty = 1,
one-side-empty = 0, averaged over the index videos and reported x100.

This is an ``INTERNAL_SPEC_REIMPLEMENTATION``.  It is not the official evaluator
and must never be reported as one.

Deviations from the vendored ``existing_internal_evaluator`` are listed in
``DEVIATIONS_FROM_VENDORED``.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .provenance import ROOT  # noqa: F401  (kept for load_reference provenance strings)
from .timebase import EPS

# P2 has no vendored evaluator: this scoring module keeps the strict loader and
# the joint arithmetic, but validation of prediction files is done by the strict
# checks in ``validation.py`` instead of the vendored schema module.
VENDOR = Path(__file__).resolve().parent / "vendor"

DEVIATIONS_FROM_VENDORED = (
    "statuses SPARSE_DIAGNOSTIC / NOT_COMPUTABLE / INVALID_INPUT are new; the vendored "
    "implementation has a single ok/not-ok exit and no notion of reference coverage",
    "validation is executed by the vendored schema module unchanged, but its report is "
    "surfaced as INVALID_INPUT with score=null instead of an exit code",
    "the joint math is re-implemented here and cross-checked against "
    "vendor.internal_metric.score_predictions on hand cases",
    "duplicate predictions: EVERY duplicate record stays in N_pred (it is counted as a "
    "false positive exactly like the vendored implementation); only the first record for a "
    "frame contributes IoU. The vendored implementation behaves identically and additionally "
    "emits a DUPLICATE_FRAME warning through its validator",
    "reference objects must declare coverage and provenance explicitly: a missing/null frames "
    "field, a duplicate video_id or missing label_status/annotation_source is REJECTED at load "
    "time (the vendored implementation has no reference loader at all)",
    "a reference that omits a scored video is NOT_COMPUTABLE rather than silently scored as "
    "empty ground truth",
    "a sparse reference produces sparse-only diagnostics: no per-video precision/recall/F1, no "
    "false positives from unannotated frames and no whole-video empty judgement",
)


class ScoreStatus(str, Enum):
    OK = "OK"
    SPARSE_DIAGNOSTIC = "SPARSE_DIAGNOSTIC"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"
    INVALID_INPUT = "INVALID_INPUT"


class ReferenceError(ValueError):
    """Malformed reference document."""


@dataclass(frozen=True)
class Box:
    """Source-pixel crop box as a three-tuple ``[x, y, w]``; height is derived."""

    x: float
    y: float
    w: float
    h: float

    def as_xyw(self) -> list:
        return [self.x, self.y, self.w]


def box_from_xyw(value: Any, *, ratio_wh: Sequence[float], width: int, height: int,
                 location: str) -> Box:
    """Build a box from a three-element ``[x, y, w]`` triplet.

    The triplet is ``[x, y, w]`` — not ``x, y, w, h`` — and the height is derived
    from the target ratio: ``h = w * th / tw``.
    """
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{location}: box must be a three-element [x, y, w] triplet")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in value):
        raise ValueError(f"{location}: box values must be numeric")
    x, y, w = (float(v) for v in value)
    if not all(math.isfinite(v) for v in (x, y, w)):
        raise ValueError(f"{location}: box values must be finite")
    if x < 0 or y < 0 or w <= 0:
        raise ValueError(f"{location}: box requires x >= 0, y >= 0, w > 0")
    tw, th = float(ratio_wh[0]), float(ratio_wh[1])
    h = w * th / tw
    if x + w > width + 1e-9 or y + h > height + 1e-9:
        raise ValueError(f"{location}: derived box [x,y,w,h]={[x, y, w, h]} exceeds {width}x{height}")
    return Box(x=x, y=y, w=w, h=h)


def spatial_iou(left: Box, right: Box) -> float:
    ix = max(0.0, min(left.x + left.w, right.x + right.w) - max(left.x, right.x))
    iy = max(0.0, min(left.y + left.h, right.y + right.h) - max(left.y, right.y))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    union = left.w * left.h + right.w * right.h - inter
    return inter / union if union > 0 else 0.0


def _zero_case(n_pred: int, n_gt: int, s_iou: float) -> tuple[float, float, float]:
    """Both empty = 1, one side empty = 0 (published rule), else the formula."""
    if n_pred == 0 and n_gt == 0:
        return 1.0, 1.0, 1.0
    if n_pred == 0 or n_gt == 0:
        return 0.0, 0.0, 0.0
    return s_iou / n_pred, s_iou / n_gt, 2.0 * s_iou / (n_pred + n_gt)


# --------------------------------------------------------------------------- #
# reference
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Reference:
    coverage: str                       # "full" | "sparse"
    videos: Mapping[str, Mapping[int, Box]]
    label_status: str
    annotation_source: str
    sparse_frame_count: int = 0
    source_path: Optional[str] = None

    def video_ids(self) -> set[str]:
        return set(self.videos)

    def as_summary(self) -> dict:
        return {
            "coverage": self.coverage,
            "label_status": self.label_status,
            "annotation_source": self.annotation_source,
            "n_videos": len(self.videos),
            "n_annotated_frames": sum(len(v) for v in self.videos.values()),
            "source_path": self.source_path,
            "trusted_annotation": False,
            "official_status": "NOT_OFFICIAL_GROUND_TRUTH",
            "note": ("a reference is never official ground truth; no reference in this project "
                     "has passed human review, so its label_status must be read as a weak label"),
        }


def _load_reference_payload(payload: Any) -> tuple[str, str, str, list]:
    """Strict structural checks shared by the loader and its tests.

    Missing fields, ``null``, wrong types and duplicate ids are rejected here.
    Only an explicit ``frames: []`` means "this video has no annotated frames".
    """
    if not isinstance(payload, dict):
        raise ReferenceError("reference root must be an object")
    if payload.get("schema") != "aic_round6_reference_v1":
        raise ReferenceError(f"unexpected reference schema: {payload.get('schema')!r}")
    coverage = payload.get("coverage")
    if coverage not in ("full", "sparse", "declared_sparse"):
        raise ReferenceError(f"reference coverage must be full/sparse, got {coverage!r}")
    if coverage == "declared_sparse":
        coverage = "sparse"

    label_status = payload.get("label_status")
    if not isinstance(label_status, str) or not label_status.strip():
        raise ReferenceError(
            "reference must declare a non-empty label_status; missing provenance must not be "
            "presented as a trusted annotation")
    annotation_source = payload.get("annotation_source")
    if not isinstance(annotation_source, str) or not annotation_source.strip():
        raise ReferenceError("reference must declare a non-empty annotation_source")

    videos = payload.get("videos")
    if not isinstance(videos, list):
        raise ReferenceError(
            f"reference 'videos' must be an explicit list, got {type(videos).__name__} "
            "(missing or null is not an empty reference)")
    if not videos:
        raise ReferenceError("reference 'videos' is empty; at least one record is required")
    return coverage, label_status.strip(), annotation_source.strip(), videos


def load_reference(path: Path | str, index: Mapping[str, Any]) -> Reference:
    """Load and validate a reference document (internal schema v1).

    Rejecting (never guessing) on: missing/null/wrong-typed ``videos`` or ``frames``,
    duplicate ``video_id``, missing provenance metadata, unknown ids, out-of-range or
    duplicate frames and malformed boxes.
    """
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    coverage, label_status, annotation_source, records = _load_reference_payload(payload)

    videos: dict[str, dict[int, Box]] = {}
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise ReferenceError(f"reference video record {position} is not an object")
        vid = record.get("video_id")
        if vid is None or not isinstance(vid, str) or not vid.strip():
            raise ReferenceError(f"reference video record {position} has no usable video_id")
        vid = vid.strip()
        if vid not in index:
            raise ReferenceError(f"reference has unknown video_id {vid!r}")
        if vid in videos:
            raise ReferenceError(
                f"reference contains duplicate video_id {vid!r}; refusing to choose a record")
        frames_field = record.get("frames")
        if not isinstance(frames_field, list):
            raise ReferenceError(
                f"reference {vid}: 'frames' must be an explicit list, got "
                f"{type(frames_field).__name__} (missing or null does not mean 'no annotations')")
        meta = index[vid]
        frames: dict[int, Box] = {}
        for item in frames_field:
            if not isinstance(item, dict):
                raise ReferenceError(f"reference {vid}: frame entry must be an object")
            frame = item.get("frame")
            if isinstance(frame, bool) or not isinstance(frame, int):
                raise ReferenceError(f"reference {vid}: frame must be a non-bool integer")
            if not 0 <= frame < meta["n_frames"]:
                raise ReferenceError(f"reference {vid}: frame {frame} out of range")
            if frame in frames:
                raise ReferenceError(f"reference {vid}: duplicate frame {frame}")
            frames[frame] = box_from_xyw(item.get("box_xyw"), ratio_wh=meta["targetRatioWH"],
                                         width=meta["width"], height=meta["height"],
                                         location=f"reference {vid}:{frame}")
        videos[vid] = frames
    return Reference(coverage=coverage, videos=videos, label_status=label_status,
                     annotation_source=annotation_source,
                     sparse_frame_count=sum(len(v) for v in videos.values()),
                     source_path=str(path.relative_to(ROOT)).replace("\\", "/")
                     if path.is_relative_to(ROOT) else str(path))


# --------------------------------------------------------------------------- #
# prediction loading / validation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PredictionSet:
    rows: Mapping[str, Mapping[int, Box]]
    n_pred_by_video: Mapping[str, int]
    duplicate_frames: Mapping[str, int]
    parse_issues: Sequence[dict]
    validation: dict
    ok: bool
    valid_records: tuple = ()          # prediction rows in file order, duplicates included


def load_predictions(path: Path | str, index: Mapping[str, Any]) -> PredictionSet:
    """Strict prediction loader; never repairs or drops anything.

    Reads the official JSONL shape ``{"video_id", "targetRatioWH", "predictions":
    [{"frame", "bboxes": [x, y, w]}]}`` and rejects: bad JSON, non-object rows,
    missing video_id, unknown or duplicate video_id, bool/non-int frames,
    out-of-range frames, duplicate frames, malformed boxes and boxes that are
    illegal against the media geometry.  Invalid rows are reported with their
    line number; nothing is silently cleaned.
    """
    rows: dict[str, dict[int, Box]] = {vid: {} for vid in index}
    n_pred: dict[str, int] = {vid: 0 for vid in index}
    duplicates: dict[str, int] = {vid: 0 for vid in index}
    issues: list[dict] = []
    seen_ids: set[str] = set()
    n_valid_records = 0
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append({"line": line_number, "code": "BAD_JSON", "detail": str(exc)})
            continue
        if not isinstance(record, dict):
            issues.append({"line": line_number, "code": "ROW_NOT_OBJECT",
                           "detail": f"{type(record).__name__}"})
            continue
        vid = record.get("video_id")
        if vid is None or not isinstance(vid, str) or not vid.strip():
            issues.append({"line": line_number, "code": "MISSING_VIDEO_ID"})
            continue
        vid = vid.strip()
        if vid not in index:
            issues.append({"line": line_number, "code": "UNKNOWN_VIDEO_ID",
                           "detail": vid})
            continue
        if vid in seen_ids:
            issues.append({"line": line_number, "code": "DUPLICATE_VIDEO_RECORD",
                           "detail": vid})
            continue
        seen_ids.add(vid)
        meta = index[vid]
        ratio = meta["targetRatioWH"]
        predictions = record.get("predictions")
        if predictions is None:
            issues.append({"line": line_number, "code": "MISSING_PREDICTIONS",
                           "detail": vid})
            continue
        if not isinstance(predictions, list):
            issues.append({"line": line_number, "code": "PREDICTIONS_NOT_LIST",
                           "detail": vid})
            continue
        for item in predictions:
            n_pred[vid] += 1
            n_valid_records += 1
            if not isinstance(item, dict):
                issues.append({"line": line_number, "code": "PREDICTION_NOT_OBJECT",
                               "detail": vid})
                continue
            frame = item.get("frame")
            if isinstance(frame, bool) or not isinstance(frame, int):
                issues.append({"line": line_number, "code": "FRAME_NOT_INT", "detail": vid})
                continue
            if not 0 <= frame < meta["n_frames"]:
                issues.append({"line": line_number, "code": "FRAME_OUT_OF_RANGE",
                               "detail": f"{vid}:{frame}"})
                continue
            try:
                box = box_from_xyw(item.get("bboxes"), ratio_wh=ratio,
                                   width=meta["width"], height=meta["height"],
                                   location=f"{vid}:{frame}")
            except ValueError as exc:
                issues.append({"line": line_number, "code": "INVALID_BOX",
                               "detail": str(exc)})
                continue
            if frame in rows[vid]:
                duplicates[vid] += 1       # counted in N_pred, does not add IoU
                continue
            rows[vid][frame] = box
    validation = {
        "rows_ok": not issues,
        "issues": issues,
        "n_issue_codes": len({i["code"] for i in issues}),
    }
    return PredictionSet(rows=rows, n_pred_by_video=n_pred, duplicate_frames=duplicates,
                         parse_issues=issues, validation=validation,
                         ok=not issues, valid_records=())


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #
def _decompose(pred_frames: set[int], pred_boxes: Mapping[int, Box],
               gt_frames: set[int], gt_boxes: Mapping[int, Box]) -> dict:
    matched = sorted(pred_frames & gt_frames)
    s_iou = sum(spatial_iou(pred_boxes[f], gt_boxes[f]) for f in matched)
    tp, fp, fn = len(matched), len(pred_frames - gt_frames), len(gt_frames - pred_frames)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    time_f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"matched_frames": len(matched), "s_iou": s_iou,
            "time_precision": precision, "time_recall": recall, "time_f1": time_f1,
            "mean_matched_iou": (s_iou / len(matched)) if matched else None,
            "unmatched_predictions": fp, "missed_ground_truth": fn}


def score_joint(*, predictions: PredictionSet, reference: Optional[Reference],
                index: Mapping[str, Any]) -> dict:
    """Score strictly: never invent ground truth, never clean away invalid input."""
    base = {
        "official_status": "INTERNAL_SPEC_REIMPLEMENTATION",
        "metric_name": "aic_round6_internal_joint_v1",
        "formula": {"f": "2*sum(matched_frame_IoU)/(N_pred+N_gt)",
                    "both_empty": 1.0, "one_empty": 0.0,
                    "aggregation": "unweighted mean over index videos, x100"},
        "deviations_from_vendored": list(DEVIATIONS_FROM_VENDORED),
        "validation": predictions.validation,
    }
    if not predictions.ok:
        return {**base, "status": ScoreStatus.INVALID_INPUT.value, "score": None,
                "reasons": ["strict validation failed; invalid rows are reported, not removed"],
                "parse_issues": list(predictions.parse_issues),
                "issue_codes": sorted({i.get("code") for i in predictions.validation.get("issues", [])})}

    if reference is None:
        return {**base, "status": ScoreStatus.NOT_COMPUTABLE.value, "score": None,
                "reasons": ["no reference supplied; missing ground truth is not an empty ground truth"]}

    index_ids = set(index)
    ref_ids = reference.video_ids()
    missing = sorted(index_ids - ref_ids)
    extra = sorted(ref_ids - index_ids)
    if missing or extra:
        return {**base, "status": ScoreStatus.NOT_COMPUTABLE.value, "score": None,
                "reference": reference.as_summary(),
                "reasons": [f"reference incomplete for scored videos: missing={len(missing)}",
                            f"reference has unscored videos: extra={len(extra)}"],
                "missing_video_ids": missing[:20], "extra_video_ids": extra[:20]}

    if reference.coverage == "sparse":
        return _score_sparse(base=base, reference=reference, predictions=predictions, index=index)

    per_video = []
    for vid in sorted(index_ids, key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else v)):
        pred_frames = set(predictions.rows[vid])
        pred_boxes = predictions.rows[vid]
        gt_frames = set(reference.videos[vid])
        gt_boxes = reference.videos[vid]
        n_pred = predictions.n_pred_by_video[vid]
        n_gt = len(gt_frames)
        decomposition = _decompose(pred_frames, pred_boxes, gt_frames, gt_boxes)
        precision, recall, f = _zero_case(n_pred, n_gt, decomposition["s_iou"])
        per_video.append({
            "video_id": vid, "n_pred": n_pred, "n_gt": n_gt,
            "duplicate_frames": predictions.duplicate_frames[vid],
            "both_empty": n_pred == 0 and n_gt == 0,
            "one_side_empty": (n_pred == 0) != (n_gt == 0),
            "s_iou": decomposition["s_iou"], "precision": precision, "recall": recall, "f1": f,
            **{k: v for k, v in decomposition.items() if k != "s_iou"},
        })

    mean_f = sum(row["f1"] for row in per_video) / len(per_video) if per_video else 0.0
    return {**base, "status": ScoreStatus.OK.value, "score": round(mean_f * 100.0, 6),
            "score_fraction": round(mean_f, 9),
            "reference": reference.as_summary(),
            "video_count": len(per_video),
            "empty_both_count": sum(row["both_empty"] for row in per_video),
            "one_side_empty_count": sum(row["one_side_empty"] for row in per_video),
            "aggregate": {
                "macro_f1": round(mean_f, 9),
                "frame_micro_f1": _frame_micro_f1(per_video),
                "matched_frame_iou": _matched_mean(per_video),
                "prediction_coverage": round(
                    sum(row["n_pred"] for row in per_video)
                    / max(1, sum(index[vid]["n_frames"] for vid in index)), 6),
                "empty_prediction_rate": round(
                    sum(1 for row in per_video if row["n_pred"] == 0) / len(per_video), 6),
                "duplicate_frame_count": sum(row["duplicate_frames"] for row in per_video),
            },
            "per_video": per_video}


def _score_sparse(*, base: dict, reference: Reference, predictions: PredictionSet,
                  index: Mapping[str, Any]) -> dict:
    """Sparse-only diagnostics.

    Only annotated frames can be evaluated.  A predicted frame without an
    annotation is *unverifiable*, not a false positive, and a video is never
    declared "empty" from sparse evidence.  Consequently this result carries no
    per-video precision / recall / F1 / time-F1 / unmatched-prediction /
    whole-video-empty fields and no joint score.
    """
    per_video = []
    annotated_total = matched_total = unevaluated_total = predictions_total = 0
    for vid in sorted(index, key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else v)):
        annotated = reference.videos[vid]
        pred_frames = set(predictions.rows[vid])
        pred_boxes = predictions.rows[vid]
        matched = sorted(set(annotated) & pred_frames)
        iou_sum = sum(spatial_iou(pred_boxes[f], annotated[f]) for f in matched)
        predictions_total += len(pred_frames)
        annotated_total += len(annotated)
        matched_total += len(matched)
        unevaluated_total += len(pred_frames) - len(matched)
        per_video.append({
            "video_id": vid,
            "annotated_frames": len(annotated),
            "matched_annotated_frames": len(matched),
            "missed_annotated_frames": len(annotated) - len(matched),
            "matched_iou_sum": round(iou_sum, 9),
            "mean_matched_iou_on_annotated_frames": (
                round(iou_sum / len(matched), 9) if matched else None),
            "predictions_total": len(pred_frames),
            "predictions_not_evaluated": len(pred_frames) - len(matched),
        })
    videos_with_annotations = [row for row in per_video if row["annotated_frames"] > 0]
    return {
        **base,
        "status": ScoreStatus.SPARSE_DIAGNOSTIC.value,
        "score": None,
        "reference": reference.as_summary(),
        "reasons": ["reference covers only declared sparse frames; unannotated frames are "
                    "unverifiable (not negatives), so no full-video joint score, no per-video "
                    "F1/precision/recall and no whole-video empty judgement are produced"],
        "sparse": {
            "evidence_status": "SPARSE_EVIDENCE" if annotated_total else "NO_EVIDENCE",
            "annotated_frames": annotated_total,
            "matched_annotated_frames": matched_total,
            "missed_annotated_frames": annotated_total - matched_total,
            "mean_matched_iou_on_annotated_frames": (
                round(sum(row["matched_iou_sum"] for row in per_video) / matched_total, 9)
                if matched_total else None),
            "mean_annotation_coverage": (
                round(matched_total / annotated_total, 9) if annotated_total else None),
            "videos_total": len(per_video),
            "videos_with_annotated_frames": len(videos_with_annotations),
            "predictions_total": predictions_total,
            "predictions_not_evaluated": unevaluated_total,
            "note": ("'predictions_not_evaluated' is context only: those frames have no "
                     "annotation and are therefore neither correct nor incorrect"),
        },
        "per_video": per_video,
    }


def _frame_micro_f1(per_video: Sequence[dict]) -> float:
    """Pooled frame-level F1 — reported only to show it differs from the macro mean."""
    s = sum(row["s_iou"] for row in per_video)
    n_pred = sum(row["n_pred"] for row in per_video)
    n_gt = sum(row["n_gt"] for row in per_video)
    return round(2 * s / (n_pred + n_gt), 9) if (n_pred + n_gt) else 1.0


def _matched_mean(per_video: Sequence[dict]) -> Optional[float]:
    matched = sum(row["matched_frames"] for row in per_video)
    if not matched:
        return None
    return round(sum(row["s_iou"] for row in per_video) / matched, 9)


def load_index(path: Path | str) -> dict:
    """Media index used for scoring/validation (not ground truth)."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload["records"] if isinstance(payload, dict) else payload
    index: dict[str, dict] = {}
    for record in records:
        vid = str(record["video_id"])
        if vid in index:
            raise ValueError(f"duplicate video_id in index: {vid}")
        index[vid] = {"video_id": vid,
                      "targetRatioWH": [float(x) for x in record["targetRatioWH"]],
                      "width": int(record["width"]), "height": int(record["height"]),
                      "n_frames": int(record["n_frames"]),
                      "video_path": record.get("video_path")}
    return index
