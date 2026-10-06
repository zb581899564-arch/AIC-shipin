from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from protected_boundary import assert_not_protected, assert_reference_payload_absent, load_registry


class SealedEvaluationError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_json_load(path: Path, code: str) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("nonfinite")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise SealedEvaluationError(code) from None


def safe_jsonl_load(path: Path, code: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                value = json.loads(
                    line,
                    parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("nonfinite")),
                )
                if not isinstance(value, dict):
                    raise ValueError("nonobject")
                rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise SealedEvaluationError(code) from None
    return rows


def finite_number(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SealedEvaluationError(code)
    result = float(value)
    if not math.isfinite(result):
        raise SealedEvaluationError(code)
    return result


def validate_ratio(value: object) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise SealedEvaluationError("INVALID_RATIO")
    width = finite_number(value[0], "INVALID_RATIO")
    height = finite_number(value[1], "INVALID_RATIO")
    if width <= 0 or height <= 0:
        raise SealedEvaluationError("INVALID_RATIO")
    return width, height


def validate_boxes(
    value: object,
    source_width: int,
    source_height: int,
    target_ratio: tuple[float, float],
    code: str,
) -> list[list[float]]:
    if not isinstance(value, list):
        raise SealedEvaluationError(code)
    boxes: list[list[float]] = []
    expected_ratio = target_ratio[0] / target_ratio[1]
    for raw_box in value:
        if not isinstance(raw_box, list) or len(raw_box) != 4:
            raise SealedEvaluationError(code)
        x, y, width, height = [finite_number(part, code) for part in raw_box]
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise SealedEvaluationError(code)
        if x + width > source_width + 1e-6 or y + height > source_height + 1e-6:
            raise SealedEvaluationError(code)
        if abs(width / height - expected_ratio) > 1e-6:
            raise SealedEvaluationError("WRONG_BOX_RATIO")
        boxes.append([x, y, width, height])
    return boxes


def iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    intersection = iw * ih
    union = aw * ah + bw * bh - intersection
    return 0.0 if union <= 0 else intersection / union


def score_frame(predictions: list[list[float]], references: list[list[float]]) -> float:
    if not predictions and not references:
        return 1.0
    if not predictions or not references:
        return 0.0
    return max(iou(prediction, reference) for prediction in predictions for reference in references)


def validate_public_commitment(commitment: dict[str, Any]) -> None:
    try:
        assert_reference_payload_absent(commitment)
    except Exception:
        raise SealedEvaluationError("COMMITMENT_EXPOSES_REFERENCE") from None
    if commitment.get("schema") != "p2r9_holdout_commitment_v1":
        raise SealedEvaluationError("COMMITMENT_SCHEMA_MISMATCH")
    if commitment.get("status") != "BOUND":
        raise SealedEvaluationError("COMMITMENT_NOT_BOUND")
    items = commitment.get("items")
    if not isinstance(items, list) or commitment.get("item_count") != len(items):
        raise SealedEvaluationError("COMMITMENT_COUNT_MISMATCH")
    forbidden = {
        "reference_boxes", "reference_box", "crop_boxes", "crop_bbox", "crop_bboxes",
        "trajectory", "trajectories", "item_iou", "per_item_score", "best_reference",
    }

    def recurse(value: object) -> None:
        if isinstance(value, dict):
            if forbidden & set(value):
                raise SealedEvaluationError("COMMITMENT_EXPOSES_REFERENCE")
            for child in value.values():
                recurse(child)
        elif isinstance(value, list):
            for child in value:
                recurse(child)

    recurse(commitment)


def _unique_by_id(rows: list[dict[str, Any]], duplicate_code: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        item_id = row.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise SealedEvaluationError("INVALID_ITEM_ID")
        if item_id in result:
            raise SealedEvaluationError(duplicate_code)
        result[item_id] = row
    return result


def evaluate(
    commitment_path: Path,
    reference_path: Path,
    prediction_path: Path,
    registry_path: Path,
    wrapper_path: Path,
    engine_path: Path,
) -> dict[str, Any]:
    commitment = safe_json_load(commitment_path, "INVALID_COMMITMENT_JSON")
    if not isinstance(commitment, dict):
        raise SealedEvaluationError("INVALID_COMMITMENT_JSON")
    validate_public_commitment(commitment)
    if commitment.get("evaluator_sha256") != sha256_file(wrapper_path):
        raise SealedEvaluationError("EVALUATOR_HASH_MISMATCH")
    if commitment.get("engine_sha256") != sha256_file(engine_path):
        raise SealedEvaluationError("ENGINE_HASH_MISMATCH")
    if commitment.get("reference_labels_sha256") != sha256_file(reference_path):
        raise SealedEvaluationError("REFERENCE_HASH_MISMATCH")
    if commitment.get("protected_registry_sha256") != sha256_file(registry_path):
        raise SealedEvaluationError("REGISTRY_HASH_MISMATCH")

    registry = load_registry(registry_path)
    reference_rows = safe_jsonl_load(reference_path, "INVALID_REFERENCE_JSON")
    prediction_rows = safe_jsonl_load(prediction_path, "INVALID_PREDICTION_JSON")
    references = _unique_by_id(reference_rows, "DUPLICATE_REFERENCE")
    predictions = _unique_by_id(prediction_rows, "DUPLICATE_PREDICTION")
    commitment_items = _unique_by_id(commitment["items"], "DUPLICATE_COMMITMENT_ITEM")
    if set(references) != set(commitment_items):
        raise SealedEvaluationError("REFERENCE_ITEM_SET_MISMATCH")
    if set(predictions) != set(references):
        if set(predictions) - set(references):
            raise SealedEvaluationError("EXTRA_PREDICTION")
        raise SealedEvaluationError("MISSING_PREDICTION")

    blocked_dev_groups = set(commitment.get("dev_source_group_sha256", []))
    per_group: dict[str, list[float]] = defaultdict(list)
    failed_items = 0
    empty_empty_items = 0
    single_empty_items = 0
    sparse_items = 0

    for item_id, reference in references.items():
        public = commitment_items[item_id]
        prediction = predictions[item_id]
        required_reference = {
            "item_id", "source_group", "media_sha256", "source_width", "source_height",
            "target_ratio_wh", "reference_boxes", "coverage",
        }
        if not required_reference <= set(reference):
            raise SealedEvaluationError("INVALID_REFERENCE_SCHEMA")
        required_prediction = {
            "item_id", "source_group", "media_sha256", "target_ratio_wh", "status", "predicted_boxes",
        }
        if set(prediction) != required_prediction:
            raise SealedEvaluationError("INVALID_PREDICTION_SCHEMA")

        source_group = reference["source_group"]
        if not isinstance(source_group, str) or not source_group:
            raise SealedEvaluationError("INVALID_SOURCE_GROUP")
        group_digest = hashlib.sha256(source_group.encode("utf-8")).hexdigest()
        if group_digest in blocked_dev_groups:
            raise SealedEvaluationError("SOURCE_SPLIT_LEAKAGE")
        if prediction["source_group"] != source_group or public.get("source_group") != source_group:
            raise SealedEvaluationError("SOURCE_GROUP_MISMATCH")
        media_sha = reference["media_sha256"]
        if not isinstance(media_sha, str) or len(media_sha) != 64:
            raise SealedEvaluationError("INVALID_MEDIA_HASH")
        if prediction["media_sha256"] != media_sha or public.get("media_sha256") != media_sha:
            raise SealedEvaluationError("MEDIA_HASH_MISMATCH")
        ratio = validate_ratio(reference["target_ratio_wh"])
        if prediction["target_ratio_wh"] != reference["target_ratio_wh"] or public.get("target_ratio_wh") != reference["target_ratio_wh"]:
            raise SealedEvaluationError("RATIO_MISMATCH")
        source_width = int(finite_number(reference["source_width"], "INVALID_SOURCE_DIMENSION"))
        source_height = int(finite_number(reference["source_height"], "INVALID_SOURCE_DIMENSION"))
        if source_width <= 0 or source_height <= 0:
            raise SealedEvaluationError("INVALID_SOURCE_DIMENSION")
        ref_boxes = validate_boxes(reference["reference_boxes"], source_width, source_height, ratio, "INVALID_REFERENCE_BOX")
        pred_boxes = validate_boxes(prediction["predicted_boxes"], source_width, source_height, ratio, "INVALID_PREDICTION_BOX")
        if reference["coverage"] not in {"single_image", "sparse_frame"}:
            raise SealedEvaluationError("INVALID_COVERAGE")
        sparse_items += int(reference["coverage"] == "sparse_frame")

        boundary_candidate = {
            "split": "process_sealed_holdout",
            "item_id": item_id,
            "source_group": source_group,
            "source_dataset_sha256": commitment.get("source_dataset_sha256"),
            "provenance_path": commitment.get("provenance_path", ""),
        }
        for identity_key in ("row_index", "video_id", "source_vid", "youtube_id"):
            if identity_key in reference:
                boundary_candidate[identity_key] = reference[identity_key]
        try:
            assert_not_protected(boundary_candidate, registry)
        except Exception:
            raise SealedEvaluationError("PROTECTED_INPUT_REJECTED") from None

        status = prediction["status"]
        if status not in {"OK", "FAILED"}:
            raise SealedEvaluationError("INVALID_PREDICTION_STATUS")
        if status == "FAILED":
            if pred_boxes:
                raise SealedEvaluationError("FAILED_PREDICTION_HAS_BOX")
            score = 0.0
            failed_items += 1
        else:
            score = score_frame(pred_boxes, ref_boxes)
            empty_empty_items += int(not pred_boxes and not ref_boxes)
            single_empty_items += int(bool(pred_boxes) != bool(ref_boxes))
        per_group[source_group].append(score)

    group_means = [sum(values) / len(values) for values in per_group.values()]
    all_scores = [score for values in per_group.values() for score in values]
    return {
        "schema": "p2r9_process_sealed_aggregate_v1",
        "status": "PASS_AGGREGATE",
        "protocol": "PROCESS_SEALED",
        "cryptographic_blind": False,
        "dataset_version": commitment["dataset_version"],
        "evaluated_items": len(all_scores),
        "source_groups": len(group_means),
        "failed_items": failed_items,
        "empty_empty_items": empty_empty_items,
        "single_empty_items": single_empty_items,
        "sparse_items": sparse_items,
        "macro_item_mean_iou": sum(all_scores) / len(all_scores) if all_scores else None,
        "macro_source_group_mean_iou": sum(group_means) / len(group_means) if group_means else None,
        "prediction_sha256": sha256_file(prediction_path),
        "commitment_sha256": sha256_file(commitment_path),
        "reference_labels_sha256": sha256_file(reference_path),
        "evaluator_sha256": sha256_file(wrapper_path),
        "engine_sha256": sha256_file(engine_path),
        "protected_registry_sha256": sha256_file(registry_path),
    }
