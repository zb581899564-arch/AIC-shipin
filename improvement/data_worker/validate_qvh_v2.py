#!/usr/bin/env python3
"""Independent stdlib validation for generated QVHighlights v2 JSONL files."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set


EXPECTED_COUNTS = {"train": 1000, "dev": 100, "holdout": 100}
REVISION = "b7e553ac3b0c898ee6b85e03ee507c064eab89ca"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_rows(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise AssertionError(f"{path}:{number}: non-object")
            rows.append(value)
    return rows


def validate_row(row: Mapping[str, Any], split: str) -> List[str]:
    errors: List[str] = []
    required = {
        "video_id", "source_vid", "source_group", "video_path", "video_sha256",
        "alignment_verified", "trusted_identity", "annotation_revision", "task_type",
        "query", "prompt", "answer", "relevant_windows", "saliency_segments",
        "saliency_segments_clipped_count", "duration_sec", "fps", "n_frames",
    }
    if not required <= set(row):
        errors.append("MISSING_FIELDS")
        return errors
    if row["video_id"] != row.get("annotation_id") or not re.fullmatch(r"qvh_\d+", str(row["video_id"])):
        errors.append("VIDEO_ID_NOT_UNIQUE_QID")
    if row["source_group"] != str(row["source_vid"]).rsplit("_", 2)[0]:
        errors.append("SOURCE_GROUP_MISMATCH")
    if row["split"] != split or row["official_split"] != ("train" if split == "train" else "val"):
        errors.append("SPLIT_MISMATCH")
    if row["annotation_revision"] != REVISION or row["task_type"] != "query_moment_retrieval":
        errors.append("PROVENANCE_FIELD_MISMATCH")
    if row["alignment_verified"] is not True:
        errors.append("ALIGNMENT_NOT_VERIFIED")
    if row["trusted_identity"] is not False or row.get("candidate_only") is not True or row.get("do_not_use_as_training") is not True:
        errors.append("FAIL_CLOSED_FLAGS_MISSING")
    windows = row["relevant_windows"]
    if row["answer"] != {"segments": windows}:
        errors.append("ANSWER_MISMATCH")
    if not isinstance(windows, list) or len(windows) > 4 or windows != sorted(windows):
        errors.append("WINDOW_CONTRACT")
    elif any(b[0] < a[1] for a, b in zip(windows, windows[1:])):
        errors.append("WINDOW_OVERLAP")
    elif any(not 0 <= float(a) < float(b) <= float(row["duration_sec"]) for a, b in windows):
        errors.append("WINDOW_BOUNDS")
    saliency = row["saliency_segments"]
    if not isinstance(saliency, list) or any(
        not isinstance(segment, list)
        or len(segment) != 2
        or not 0 <= float(segment[0]) < float(segment[1]) <= float(row["duration_sec"])
        for segment in saliency
    ):
        errors.append("SALIENCY_DIAGNOSTIC_BOUNDS")
    if not SHA256.fullmatch(str(row["video_sha256"])):
        errors.append("INVALID_SHA256")
    path = Path(str(row["video_path"]))
    if not path.is_file():
        errors.append("MEDIA_MISSING")
    if "/home/inspur/aic_video_data/test" in str(path):
        errors.append("TEST_PATH_LEAKAGE")
    return errors


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    all_rows: Dict[str, List[Dict[str, Any]]] = {}
    errors: List[Dict[str, Any]] = []
    groups: Dict[str, Set[str]] = {}
    ids: Set[str] = set()
    for split, expected in EXPECTED_COUNTS.items():
        rows = load_rows(args.data_dir / f"{split}.jsonl")
        all_rows[split] = rows
        if len(rows) != expected:
            errors.append({"split": split, "error": "COUNT_MISMATCH", "actual": len(rows), "expected": expected})
        groups[split] = {str(row.get("source_group")) for row in rows}
        for number, row in enumerate(rows, 1):
            row_errors = validate_row(row, split)
            if row["video_id"] in ids:
                row_errors.append("DUPLICATE_VIDEO_ID")
            ids.add(row["video_id"])
            if row_errors:
                errors.append({"split": split, "line": number, "video_id": row.get("video_id"), "errors": row_errors})
    overlaps = {
        "train__dev": sorted(groups["train"] & groups["dev"]),
        "train__holdout": sorted(groups["train"] & groups["holdout"]),
        "dev__holdout": sorted(groups["dev"] & groups["holdout"]),
    }
    if any(overlaps.values()):
        errors.append({"error": "CROSS_SPLIT_SOURCE_GROUP_OVERLAP", "overlap": overlaps})
    paths: Dict[str, str] = {}
    for rows in all_rows.values():
        for row in rows:
            paths.setdefault(row["video_path"], row["video_sha256"])
    keys = sorted(paths)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        actuals = list(pool.map(lambda value: hash_file(Path(value)), keys))
    mismatches = [path for path, actual in zip(keys, actuals) if actual != paths[path]]
    if mismatches:
        errors.append({"error": "MEDIA_SHA256_MISMATCH", "count": len(mismatches), "paths": mismatches[:10]})
    report = {
        "schema_version": "qvh_v2_validation_v1",
        "ok": not errors,
        "counts": {split: len(rows) for split, rows in all_rows.items()},
        "unique_video_ids": len(ids),
        "unique_media": len(paths),
        "cross_split_source_group_overlap": overlaps,
        "media_hash_mismatches": len(mismatches),
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
