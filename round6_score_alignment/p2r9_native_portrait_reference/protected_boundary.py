from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ProtectedInputError(ValueError):
    """Raised when an exposed or previously used input is presented as sealed."""


def canonical_identity(kind: str, fields: dict[str, Any]) -> str:
    payload = {"kind": kind, **fields}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def identity_digest(kind: str, fields: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_identity(kind, fields).encode("utf-8")).hexdigest()


def load_registry(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "p2r9_protected_input_registry_v1":
        raise ProtectedInputError("protected registry schema mismatch")
    return value


def assert_not_protected(candidate: dict[str, Any], registry: dict[str, Any]) -> None:
    split = candidate.get("split")
    if split != "process_sealed_holdout":
        return

    dataset_sha = candidate.get("source_dataset_sha256")
    blocked_dataset_hashes = set(registry["blocked_dataset_sha256"])
    if dataset_sha in blocked_dataset_hashes:
        raise ProtectedInputError("protected dataset cannot be assigned to process_sealed_holdout")

    provenance = str(candidate.get("provenance_path", "")).replace("\\", "/").lower()
    for marker in registry["blocked_provenance_markers"]:
        if marker.lower() in provenance:
            raise ProtectedInputError("protected provenance cannot be assigned to process_sealed_holdout")

    checks: list[tuple[str, dict[str, Any]]] = []
    if {"row_index", "video_id", "source_vid", "youtube_id"} <= candidate.keys():
        checks.append(("round6_weak_holdout", {
            "row_index": candidate["row_index"],
            "video_id": candidate["video_id"],
            "source_vid": candidate["source_vid"],
            "youtube_id": candidate["youtube_id"],
        }))
    if "item_id" in candidate:
        checks.append(("p2r_gnmc_exposed_sealed", {"item_id": candidate["item_id"]}))

    blocked = set(registry["blocked_identity_sha256"])
    if any(identity_digest(kind, fields) in blocked for kind, fields in checks):
        raise ProtectedInputError("protected identity cannot be assigned to process_sealed_holdout")

    blocked_components = set(registry.get("blocked_component_sha256", []))
    for key in ("row_index", "video_id", "source_vid", "youtube_id", "item_id", "source_group"):
        if key not in candidate:
            continue
        component = hashlib.sha256(f"{key}:{candidate[key]}".encode("utf-8")).hexdigest()
        if component in blocked_components:
            raise ProtectedInputError("protected identity component cannot be assigned to process_sealed_holdout")


def assert_reference_payload_absent(candidate: dict[str, Any]) -> None:
    forbidden = {
        "reference_boxes", "reference_box", "crop_boxes", "crop_bbox", "crop_bboxes",
        "trajectory", "trajectories", "item_iou", "per_item_score", "best_reference",
    }
    hit = sorted(forbidden & set(candidate))
    if hit:
        raise ProtectedInputError("process-sealed public record contains forbidden reference payload")
