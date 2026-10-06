"""Fail-closed data/authorization gate for the Qwen3-VL adapter run.

The gate deliberately accepts only an explicitly accepted split manifest.  A
``candidate_splits`` section is evidence for review, never an input to
training.  This module is standard-library-only so a rejected run does not
import torch, Transformers, PEFT, or touch a GPU.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union


REQUIRED_COUNTS = {"train": 200, "dev": 50, "holdout": 50}
TEST_ROOT = "/home/inspur/aic_video_data/test"
CANDIDATE_FILE_NAMES = {"candidate_splits.jsonl", "candidate_groups.jsonl", "candidate_split_leakage.json"}
SOURCE_GROUP_SUFFIX = re.compile(r"^(?P<base>.+)_(?:-?\d+(?:\.\d+)?)_(?:-?\d+(?:\.\d+)?)$")


@dataclass
class GateDecision:
    ok: bool
    reasons: list
    coordination_path: str
    data_gate_path: str
    training_authorized: bool
    split_audit: Dict[str, Any]
    candidate_splits_ignored: bool = False

    def as_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["gpu_started"] = False
        result["adapter_created"] = False
        return result


def _load_json(path: Path) -> Tuple[Optional[Any], Optional[str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except FileNotFoundError:
        return None, "FILE_NOT_FOUND"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"READ_ERROR:{exc}"


def _pass_marker(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, Mapping):
        for key in ("accepted", "passed", "pass", "ok", "value"):
            if value.get(key) is True:
                return True
        status = str(value.get("status", "")).upper()
        return status in {"PASS", "PASSED", "ACCEPTED", "OK", "TRUE"}
    return False


def _path_from_entry(entry: Any) -> Optional[str]:
    if isinstance(entry, str):
        return entry
    if not isinstance(entry, Mapping):
        return None
    for key in ("path", "file", "jsonl", "source_file"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _resolve(path_value: Optional[str], base: Path) -> Optional[Path]:
    if not path_value:
        return None
    path = Path(path_value)
    return path if path.is_absolute() else base / path


def _video_paths(row: Mapping[str, Any]) -> Sequence[str]:
    values = []
    for key in ("video_path", "video", "media_path"):
        value = row.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    for key in ("videos", "video_paths", "media"):
        value = row.get(key)
        if isinstance(value, str) and value:
            values.append(value)
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str) and item)
    return values


def _is_under(path_value: str, root: str) -> bool:
    try:
        path = os.path.realpath(path_value)
        root_path = os.path.realpath(root)
        return path == root_path or path.startswith(root_path + os.sep)
    except OSError:
        return False


def _canonical_source_group(value: str) -> str:
    """Collapse clip-level ``source_vid_start_end`` to its source group."""

    match = SOURCE_GROUP_SUFFIX.match(value.strip())
    return match.group("base") if match else value.strip()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _row_flagged(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _row_trusted(row: Mapping[str, Any]) -> bool:
    return row.get("trusted_identity") is True or row.get("trusted_for_gate") is True


def _row_alignment_verified(row: Mapping[str, Any]) -> bool:
    return row.get("alignment_verified") is True


def _row_media_hash(row: Mapping[str, Any]) -> Optional[str]:
    for key in ("media_sha256", "actual_sha256", "video_sha256", "sha256"):
        value = row.get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value):
            return value.lower()
    return None


def _resolve_media_path(value: str, split_path: Path, work_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidate = work_root / path
    if candidate.is_file():
        return candidate
    return split_path.parent / path


def _audit_split_file(path: Path, expected_count: int, split: str, work_root: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "path": str(path),
        "expected_count": expected_count,
        "actual_count": 0,
        "malformed_rows": 0,
        "missing_media_path_rows": 0,
        "missing_media_file_rows": 0,
        "missing_source_group_rows": 0,
        "missing_alignment_verified_rows": 0,
        "untrusted_rows": 0,
        "missing_media_hash_rows": 0,
        "media_hash_mismatch_rows": 0,
        "test_leakage_rows": 0,
        "candidate_flag_rows": 0,
        "candidate_file_name": path.name in CANDIDATE_FILE_NAMES,
        "source_groups": [],
        "errors": [],
    }
    if not path.is_file():
        result["errors"].append("SPLIT_FILE_NOT_FOUND")
        return result
    if result["candidate_file_name"]:
        result["errors"].append("CANDIDATE_FILE_BLOCKED")
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError as exc:
        result["errors"].append(f"SPLIT_FILE_READ_ERROR:{exc}")
        return result
    with handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            result["actual_count"] += 1
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                result["malformed_rows"] += 1
                continue
            if not isinstance(row, Mapping):
                result["malformed_rows"] += 1
                continue
            paths = _video_paths(row)
            if not paths:
                result["missing_media_path_rows"] += 1
            resolved_paths = [_resolve_media_path(item, path, work_root) for item in paths]
            if paths and any(not item.is_file() for item in resolved_paths):
                result["missing_media_file_rows"] += 1
            if any(_is_under(str(item), TEST_ROOT) for item in resolved_paths):
                result["test_leakage_rows"] += 1
            source_group = row.get("source_group")
            if not isinstance(source_group, str) or not source_group.strip():
                result["missing_source_group_rows"] += 1
            else:
                result["source_groups"].append(_canonical_source_group(source_group))
            if not _row_alignment_verified(row):
                result["missing_alignment_verified_rows"] += 1
            if not _row_trusted(row):
                result["untrusted_rows"] += 1
            media_hash = _row_media_hash(row)
            if media_hash is None:
                result["missing_media_hash_rows"] += 1
            else:
                for media_path in resolved_paths:
                    if media_path.is_file() and _hash_file(media_path) != media_hash:
                        result["media_hash_mismatch_rows"] += 1
                        break
            if _row_flagged(row.get("candidate_only")) or _row_flagged(row.get("do_not_use_as_training")):
                result["candidate_flag_rows"] += 1
    if result["actual_count"] != expected_count:
        result["errors"].append("SPLIT_COUNT_DRIFT")
    if result["malformed_rows"]:
        result["errors"].append("MALFORMED_ROW")
    if result["missing_media_path_rows"]:
        result["errors"].append("MEDIA_PATH_MISSING")
    if result["missing_media_file_rows"]:
        result["errors"].append("MEDIA_FILE_NOT_FOUND")
    if result["missing_source_group_rows"]:
        result["errors"].append("SOURCE_GROUP_MISSING")
    if result["missing_alignment_verified_rows"]:
        result["errors"].append("ROW_ALIGNMENT_NOT_VERIFIED")
    if result["untrusted_rows"]:
        result["errors"].append("ROW_NOT_TRUSTED")
    if result["missing_media_hash_rows"]:
        result["errors"].append("MEDIA_HASH_MISSING")
    if result["media_hash_mismatch_rows"]:
        result["errors"].append("MEDIA_HASH_MISMATCH")
    if result["test_leakage_rows"]:
        result["errors"].append("TEST_LEAKAGE_PATH")
    if result["candidate_flag_rows"]:
        result["errors"].append("CANDIDATE_ROW_BLOCKED")
    return result


def evaluate_training_gate(
    coordination_path: Union[str, Path],
    data_gate_path: Union[str, Path],
    *,
    split_overrides: Optional[Mapping[str, Union[str, Path]]] = None,
) -> GateDecision:
    """Evaluate authorization and accepted split evidence before imports."""

    coordination_path = Path(coordination_path)
    data_gate_path = Path(data_gate_path)
    reasons = []
    split_audit: Dict[str, Any] = {}
    coordination, coordination_error = _load_json(coordination_path)
    gate, gate_error = _load_json(data_gate_path)
    training_authorized = bool(isinstance(coordination, Mapping) and coordination.get("training_authorized") is True)
    if coordination_error:
        reasons.append("COORDINATION_" + coordination_error)
    if not training_authorized:
        reasons.append("TRAINING_NOT_AUTHORIZED")
    if gate_error:
        reasons.append("DATA_GATE_" + gate_error)

    candidate_splits_ignored = isinstance(gate, Mapping) and (
        "candidate_splits" in gate or "candidate_artifacts" in gate
    )
    if isinstance(gate, Mapping):
        # A's locked data-gate schema uses `passed`, `alignment_verified`,
        # and counts[*].trusted_identity.  Do not infer acceptance from the
        # candidate split artifacts or from a merely large label count.
        if gate.get("passed") is not True:
            reasons.append("DATA_GATE_PASSED_FALSE")
        if gate.get("alignment_verified") is not True:
            reasons.append("ALIGNMENT_NOT_VERIFIED")
        if candidate_splits_ignored and "accepted_splits" not in gate:
            reasons.append("CANDIDATE_ARTIFACTS_NOT_ACCEPTED")
        counts = gate.get("counts")
        if not isinstance(counts, Mapping):
            reasons.append("COUNTS_MISSING")
            counts = {}
        accepted_splits = gate.get("accepted_splits")
        if not isinstance(accepted_splits, Mapping):
            reasons.append("ACCEPTED_SPLITS_MISSING")
            accepted_splits = {}
        base = data_gate_path.parent.parent
        split_overrides = split_overrides or {}
        for split, minimum in REQUIRED_COUNTS.items():
            entry = accepted_splits.get(split)
            count_record = counts.get(split)
            count = count_record.get("trusted_identity") if isinstance(count_record, Mapping) else None
            if not isinstance(count, int) or isinstance(count, bool):
                reasons.append(f"{split.upper()}_TRUSTED_COUNT_MISSING")
                count = 0
            if count < minimum:
                reasons.append(f"{split.upper()}_TRUSTED_COUNT_BELOW_{minimum}")
            path_value = _path_from_entry(entry)
            if split in split_overrides:
                path_value = str(split_overrides[split])
            split_path = _resolve(path_value, base)
            if split_path is None:
                reasons.append(f"{split.upper()}_FILE_MISSING")
                split_audit[split] = {"expected_count": count, "errors": ["SPLIT_PATH_MISSING"]}
            else:
                split_audit[split] = _audit_split_file(split_path, count, split, base)
                for error in split_audit[split]["errors"]:
                    reasons.append(f"{split.upper()}_{error}")
        # Recompute source-group intersections from the files we would train
        # on. The candidate_split_leakage.json artifact is not trusted for
        # this gate because it is explicitly candidate-only.
        groups = {
            split: set(split_audit.get(split, {}).get("source_groups", []))
            for split in REQUIRED_COUNTS
        }
        for left, right in (("train", "dev"), ("train", "holdout"), ("dev", "holdout")):
            overlap = sorted(groups[left] & groups[right])
            split_audit.setdefault("cross_split", {})[f"{left}__{right}"] = overlap
            if overlap:
                reasons.append(f"SOURCE_GROUP_OVERLAP_{left.upper()}_{right.upper()}")
        split_audit.setdefault("cross_split", {})["zero_overlap"] = not any(
            split_audit["cross_split"][key]
            for key in ("train__dev", "train__holdout", "dev__holdout")
        )
    else:
        reasons.append("DATA_GATE_NOT_OBJECT")

    # Keep stable order while removing repeated reasons from nested checks.
    reasons = list(dict.fromkeys(reasons))
    return GateDecision(
        ok=not reasons,
        reasons=reasons,
        coordination_path=str(coordination_path),
        data_gate_path=str(data_gate_path),
        training_authorized=training_authorized,
        split_audit=split_audit,
        candidate_splits_ignored=candidate_splits_ignored,
    )


def write_gate_report(path: Union[str, Path], decision: GateDecision, **extra: Any) -> None:
    payload = decision.as_dict()
    payload.update(extra)
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
