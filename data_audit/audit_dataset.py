#!/usr/bin/env python3
"""Reproducible, content-free audit for the AIC video-label package.

The audit reads JSON/MP4 headers and file bytes for SHA-256 only.  It never
decodes or exports video frames and deliberately omits teacher summaries from
all generated artifacts.  The input tree is treated as read-only; callers
should place output under a separate work directory.

Example (on the data host)::

    python3 audit_dataset.py \
        --data-root /home/inspur/aic_video_data \
        --out-dir /home/inspur/aic_video_work/data_audit \
        --seed 42

``candidate_*`` outputs are planning artifacts.  They are explicitly marked
as candidate and are not training manifests.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable


SCRIPT_VERSION = "2026-09-09.data-audit.v1"
GROUP_SUFFIX_RE = re.compile(
    r"_(?P<start>[0-9]+(?:\.[0-9]+)?)_(?P<end>[0-9]+(?:\.[0-9]+)?)$"
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def json_dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def jsonl_dump(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def clean_source_value(value: Any) -> str:
    if isinstance(value, str):
        value = value.strip().replace("\\", "/")
        value = value.rsplit("/", 1)[-1]
        if value.lower().endswith(".mp4"):
            value = value[:-4]
        return value
    if value is None:
        return ""
    return str(value).strip()


def source_group(source_vid: Any, video_id: str) -> tuple[str, str]:
    """Return (raw clip identity, normalized original-source grouping key).

    The only normalization is removal of the final numeric ``_start_end``
    suffix observed in the supplied package.  Missing values are isolated per
    label instead of being merged into one guessed source.
    """

    raw = clean_source_value(source_vid)
    if not raw:
        return "", f"__MISSING_SOURCE__:{video_id}"
    match = GROUP_SUFFIX_RE.search(raw)
    return raw, (raw[: match.start()] if match else raw)


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def number(value: Any) -> float | None:
    return float(value) if finite_number(value) else None


def interval_from_clip(clip: dict[str, Any]) -> tuple[float | None, float | None]:
    start = number(clip.get("start_sec"))
    end = number(clip.get("end_sec"))
    return start, end


def metadata_from_av(path: Path) -> dict[str, Any]:
    """Read container/stream headers only; do not decode frames."""

    try:
        import av  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on host runtime
        return {"metadata_status": "pyav_unavailable", "metadata_error": str(exc)}

    try:
        with av.open(str(path), mode="r") as container:
            streams = [stream for stream in container.streams if stream.type == "video"]
            if not streams:
                return {"metadata_status": "no_video_stream"}
            stream = streams[0]

            duration_s: float | None = None
            if stream.duration is not None and stream.time_base is not None:
                duration_s = float(stream.duration * stream.time_base)
            elif container.duration is not None:
                duration_s = float(container.duration) / 1_000_000.0

            rate = stream.average_rate or stream.base_rate
            fps_num: int | None = None
            fps_den: int | None = None
            fps: float | None = None
            if rate is not None:
                fps_num = int(rate.numerator)
                fps_den = int(rate.denominator)
                if fps_den:
                    fps = fps_num / fps_den

            return {
                "metadata_status": "ok",
                "width": int(stream.width or 0),
                "height": int(stream.height or 0),
                "duration_s": duration_s,
                "frames": int(stream.frames or 0),
                "fps": fps,
                "fps_num": fps_num,
                "fps_den": fps_den,
                "codec": getattr(getattr(stream, "codec_context", None), "name", None),
                "time_base": str(stream.time_base) if stream.time_base is not None else None,
            }
    except Exception as exc:  # malformed/truncated containers stay isolated
        return {"metadata_status": "error", "metadata_error": str(exc)}


def discover_videos(video_root: Path) -> tuple[list[Path], dict[str, list[Path]]]:
    paths = sorted(
        (path for path in video_root.rglob("*") if path.is_file() and path.suffix.lower() == ".mp4"),
        key=lambda path: path.as_posix(),
    )
    by_stem: dict[str, list[Path]] = collections.defaultdict(list)
    for path in paths:
        by_stem[path.stem].append(path)
    return paths, dict(by_stem)


def label_record_ok(record: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    required = {
        "annotation_mode",
        "clip",
        "cropRois",
        "crop_keyframes",
        "dataset_split",
        "provenance",
        "quality",
        "schema_version",
        "segments",
        "targetRatioWH",
        "video_id",
        "video_path",
    }
    missing = sorted(required.difference(record))
    if missing:
        reasons.append("missing_keys:" + ",".join(missing))

    if not isinstance(record.get("video_id"), str) or not record.get("video_id"):
        reasons.append("invalid_video_id")
    if record.get("video_path") not in ("", None):
        # A non-empty path is not a failure by itself, but it must remain a
        # separately auditable value and is never trusted without resolution.
        reasons.append("video_path_nonempty")

    ratio = record.get("targetRatioWH")
    if not (
        isinstance(ratio, list)
        and len(ratio) == 2
        and all(finite_number(x) and float(x) > 0 for x in ratio)
    ):
        reasons.append("invalid_target_ratio")

    # Python's json parser accepts NaN/Infinity by default.  Reject any such
    # values in temporal/spatial/provenance fields before they can enter a
    # training manifest.  This is a structural check and never prints the
    # teacher summary or trajectory payload.
    def walk_numeric(value: Any, path: str) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            reasons.append("nonfinite_numeric:" + path)
        elif isinstance(value, dict):
            for key, child in value.items():
                if key == "summary":
                    continue
                walk_numeric(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk_numeric(child, f"{path}[{index}]")

    for field in ("clip", "cropRois", "crop_keyframes", "segments", "provenance", "quality"):
        walk_numeric(record.get(field), field)

    clip = record.get("clip")
    if not isinstance(clip, dict):
        reasons.append("invalid_clip_object")
    else:
        start, end = interval_from_clip(clip)
        if start is None or end is None or start < 0 or end <= start:
            reasons.append("invalid_clip_interval")
        qvh_window = clip.get("qvh_window")
        if isinstance(qvh_window, list) and len(qvh_window) == 2:
            qvh_start = number(qvh_window[0])
            qvh_end = number(qvh_window[1])
            if (
                qvh_start is None
                or qvh_end is None
                or qvh_start < 0
                or qvh_end <= qvh_start
            ):
                reasons.append("invalid_qvh_window")
        elif qvh_window is not None:
            reasons.append("invalid_qvh_window")

    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        reasons.append("invalid_provenance_object")
    else:
        expected = provenance.get("video_sha256")
        if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            reasons.append("invalid_expected_sha256")

    segments = record.get("segments")
    if not isinstance(segments, list):
        reasons.append("invalid_segments_list")
    else:
        for segment in segments:
            if not isinstance(segment, dict):
                reasons.append("invalid_segment_object")
                break
            start = number(segment.get("source_start_sec"))
            end = number(segment.get("source_end_sec"))
            start_frame = number(segment.get("start_frame"))
            end_frame = number(segment.get("end_frame"))
            if (
                start is None
                or end is None
                or start < 0
                or end < start
                or start_frame is None
                or end_frame is None
                or start_frame < 0
                or end_frame < start_frame
            ):
                reasons.append("invalid_segment_interval")
                break

    return not reasons, reasons


def stable_group_order(groups: list[str], seed: int) -> list[str]:
    ordered = sorted(groups)
    rng = random.Random(seed)
    rng.shuffle(ordered)
    return ordered


def candidate_split(groups: dict[str, list[int]], seed: int, n_rows: int) -> dict[str, str]:
    """Assign whole source groups to train/dev/holdout deterministically.

    The seeded order is part of the reproducibility contract.  At each step,
    the group goes to the split with the largest relative deficit to its
    target; the tie order is fixed.  Since assignments are by group, no row
    can leak across candidate splits even when one source has many clips.
    """

    targets = {"train": 0.80 * n_rows, "dev": 0.10 * n_rows, "holdout": 0.10 * n_rows}
    counts = {name: 0 for name in targets}
    assignment: dict[str, str] = {}
    for group in stable_group_order(list(groups), seed):
        size = len(groups[group])
        deficits = {
            split: (targets[split] - counts[split]) / max(targets[split], 1.0)
            for split in targets
        }
        # Tie priority is train, dev, holdout and is deterministic.
        split = max(("train", "dev", "holdout"), key=lambda name: deficits[name])
        assignment[group] = split
        counts[split] += size
    return assignment


def tsv_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def write_tsv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\t".join(columns) + "\n")
        for row in rows:
            handle.write("\t".join(tsv_value(row.get(column)) for column in columns) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--no-hash-related",
        action="store_true",
        help="skip SHA-256 for label-related MP4s (default hashes each unique related file)",
    )
    args = parser.parse_args(argv)

    data_root = args.data_root.resolve()
    out_dir = args.out_dir.resolve()
    labels_path = data_root / "labels" / "train.jsonl"
    videos_root = data_root / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    with labels_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                parse_errors.append({"line_no": line_no, "category": "blank_label_line"})
                continue
            try:
                record = json.loads(line)
            except Exception as exc:
                parse_errors.append(
                    {"line_no": line_no, "category": "json_parse_error", "error": str(exc)}
                )
                continue
            if not isinstance(record, dict):
                parse_errors.append({"line_no": line_no, "category": "label_not_object"})
                continue
            record["_line_no"] = line_no
            records.append(record)

    video_paths, video_by_stem = discover_videos(videos_root)
    related_stems = {
        clean_source_value(record.get("clip", {}).get("source_vid"))
        for record in records
        if isinstance(record.get("clip"), dict)
    }

    # Metadata is intentionally collected for every MP4; hashes are collected
    # only for files named by the 987 label rows.
    video_rows: list[dict[str, Any]] = []
    metadata_cache: dict[str, dict[str, Any]] = {}
    hash_cache: dict[str, str] = {}
    for index, path in enumerate(video_paths, 1):
        rel = path.relative_to(data_root).as_posix()
        related = path.stem in related_stems
        metadata = metadata_from_av(path)
        metadata_cache[str(path)] = metadata
        actual_hash: str | None = None
        if related and not args.no_hash_related:
            actual_hash = sha256_file(path)
            hash_cache[str(path)] = actual_hash
        video_rows.append(
            {
                "relpath": rel,
                "basename": path.name,
                "stem": path.stem,
                "size_bytes": path.stat().st_size,
                "label_related": related,
                "sha256": actual_hash,
                **metadata,
            }
        )

    groups: dict[str, list[int]] = collections.defaultdict(list)
    label_rows: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = list(parse_errors)
    raw_source_to_splits: dict[str, set[str]] = collections.defaultdict(set)

    for row_index, record in enumerate(records):
        clip = record.get("clip") if isinstance(record.get("clip"), dict) else {}
        provenance = record.get("provenance") if isinstance(record.get("provenance"), dict) else {}
        video_id = str(record.get("video_id", ""))
        raw_source, group = source_group(clip.get("source_vid"), video_id)
        groups[group].append(row_index)
        original_split = str(record.get("dataset_split", ""))
        raw_source_to_splits[group].add(original_split)

        matched = video_by_stem.get(raw_source, []) if raw_source else []
        match_path = matched[0] if len(matched) == 1 else None
        expected_hash = provenance.get("video_sha256")
        actual_hash = hash_cache.get(str(match_path)) if match_path else None
        if not matched:
            hash_status = "missing_source"
        elif len(matched) > 1:
            hash_status = "ambiguous_basename"
        elif args.no_hash_related:
            hash_status = "not_checked"
        elif actual_hash is None:
            hash_status = "hash_unavailable"
        elif isinstance(expected_hash, str) and actual_hash.lower() == expected_hash.lower():
            hash_status = "match"
        else:
            hash_status = "mismatch"

        metadata = metadata_cache.get(str(match_path), {}) if match_path else {}
        schema_ok, schema_reasons = label_record_ok(record)
        trusted = bool(
            schema_ok
            and match_path is not None
            and hash_status == "match"
            and metadata.get("metadata_status") == "ok"
        )
        isolation_reasons = list(schema_reasons)
        if not matched:
            isolation_reasons.append("source_file_missing")
        elif len(matched) > 1:
            isolation_reasons.append("source_basename_ambiguous")
        elif hash_status == "mismatch":
            isolation_reasons.append("provenance_hash_mismatch")
        elif hash_status in {"not_checked", "hash_unavailable"}:
            isolation_reasons.append("source_hash_not_verified")
        if match_path is not None and metadata.get("metadata_status") != "ok":
            isolation_reasons.append("video_metadata_not_verified")
        if record.get("video_path") in ("", None):
            anomalies.append(
                {
                    "line_no": record.get("_line_no"),
                    "video_id": video_id,
                    "category": "empty_video_path",
                    "severity": "warning",
                    "detail": "video_path is empty; source identity relies on clip.source_vid plus file/hash evidence",
                }
            )
        if not matched:
            anomalies.append(
                {
                    "line_no": record.get("_line_no"),
                    "video_id": video_id,
                    "source_vid": raw_source,
                    "source_group": group,
                    "category": "missing_source_file",
                    "severity": "error",
                }
            )
        elif hash_status == "mismatch":
            anomalies.append(
                {
                    "line_no": record.get("_line_no"),
                    "video_id": video_id,
                    "source_vid": raw_source,
                    "source_group": group,
                    "category": "provenance_hash_mismatch",
                    "severity": "error",
                    "expected_sha256": expected_hash,
                    "actual_sha256": actual_hash,
                }
            )
        elif metadata.get("metadata_status") != "ok":
            anomalies.append(
                {
                    "line_no": record.get("_line_no"),
                    "video_id": video_id,
                    "source_vid": raw_source,
                    "category": "video_metadata_error",
                    "severity": "error",
                    "metadata_status": metadata.get("metadata_status"),
                }
            )

        label_rows.append(
            {
                "line_no": record.get("_line_no"),
                "video_id": video_id,
                "dataset_split": original_split,
                "schema_version": record.get("schema_version"),
                "annotation_mode": record.get("annotation_mode"),
                "targetRatioWH": record.get("targetRatioWH"),
                "source_vid": raw_source,
                "source_group": group,
                "source_file": match_path.relative_to(data_root).as_posix() if match_path else None,
                "source_exists": bool(match_path),
                "source_match_count": len(matched),
                "source_size_bytes": match_path.stat().st_size if match_path else None,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "hash_status": hash_status,
                "metadata_status": metadata.get("metadata_status"),
                "width": metadata.get("width"),
                "height": metadata.get("height"),
                "duration_s": metadata.get("duration_s"),
                "frames": metadata.get("frames"),
                "fps": metadata.get("fps"),
                "fps_num": metadata.get("fps_num"),
                "fps_den": metadata.get("fps_den"),
                "codec": metadata.get("codec"),
                "clip_start_sec": number(clip.get("start_sec")),
                "clip_end_sec": number(clip.get("end_sec")),
                "qvh_window": clip.get("qvh_window"),
                "segment_count": len(record.get("segments", [])) if isinstance(record.get("segments"), list) else None,
                "video_path_empty": record.get("video_path") in ("", None),
                "schema_valid": schema_ok,
                "alignment_class": "verified_clip_identity" if trusted else "isolated",
                "trusted_for_gate": trusted,
                "isolation_reasons": isolation_reasons,
            }
        )

    assignment = candidate_split(groups, args.seed, len(label_rows))
    for row in label_rows:
        row["candidate_split"] = assignment[row["source_group"]]
        row["candidate_only"] = True
        row["do_not_use_as_training"] = True

    # The original package split is independently checked for source leakage.
    original_split_groups: dict[str, set[str]] = collections.defaultdict(set)
    for row in label_rows:
        original_split_groups[row["dataset_split"]].add(row["source_group"])
    original_overlap = sorted(
        original_split_groups.get("train", set()) & original_split_groups.get("val", set())
    )
    if original_overlap:
        anomalies.append(
            {
                "category": "original_train_val_source_group_overlap",
                "severity": "error",
                "count": len(original_overlap),
                "source_groups": original_overlap,
                "detail": "original dataset_split is not source-group disjoint; candidate split repairs this only for planning",
            }
        )

    candidate_group_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for group in sorted(groups):
        indices = groups[group]
        group_rows = [label_rows[i] for i in indices]
        split = assignment[group]
        trusted_count = sum(bool(row["trusted_for_gate"]) for row in group_rows)
        candidate_group_rows.append(
            {
                "source_group": group,
                "candidate_split": split,
                "candidate_only": True,
                "do_not_use_as_training": True,
                "label_count": len(group_rows),
                "trusted_identity_count": trusted_count,
                "original_splits": sorted({row["dataset_split"] for row in group_rows}),
                "missing_source_count": sum(not row["source_exists"] for row in group_rows),
                "hash_mismatch_count": sum(row["hash_status"] == "mismatch" for row in group_rows),
            }
        )
        for row in group_rows:
            candidate_rows.append(
                {
                    "line_no": row["line_no"],
                    "video_id": row["video_id"],
                    "source_vid": row["source_vid"],
                    "source_group": group,
                    "candidate_split": split,
                    "trusted_identity": row["trusted_for_gate"],
                    "candidate_only": True,
                    "do_not_use_as_training": True,
                }
            )

    candidate_split_groups = {
        split: {group for group, assigned in assignment.items() if assigned == split}
        for split in ("train", "dev", "holdout")
    }
    leakage_pairs: dict[str, list[str]] = {}
    split_names = ("train", "dev", "holdout")
    for left_index, left in enumerate(split_names):
        for right in split_names[left_index + 1 :]:
            leakage_pairs[f"{left}__{right}"] = sorted(
                candidate_split_groups[left] & candidate_split_groups[right]
            )
    zero_group_leakage = all(not values for values in leakage_pairs.values())

    split_counts: dict[str, dict[str, Any]] = {}
    for split in split_names:
        split_rows = [row for row in label_rows if row["candidate_split"] == split]
        split_counts[split] = {
            "labels": len(split_rows),
            "groups": len(candidate_split_groups[split]),
            "trusted_identity": sum(bool(row["trusted_for_gate"]) for row in split_rows),
            "isolated": sum(not row["trusted_for_gate"] for row in split_rows),
        }

    missing_count = sum(row["hash_status"] == "missing_source" for row in label_rows)
    mismatch_count = sum(row["hash_status"] == "mismatch" for row in label_rows)
    metadata_error_count = sum(
        row["source_exists"] and row["metadata_status"] != "ok" for row in label_rows
    )
    source_groups_count = len(groups)
    trusted_total = sum(bool(row["trusted_for_gate"]) for row in label_rows)

    # Global alignment is deliberately stricter than a row-level file/hash
    # match: without the exact clip-generation/alignment manifest we cannot
    # prove a temporal transform from processed clips back to the original
    # source videos.  The matched subset is therefore evidence for review,
    # never an accepted training manifest.
    alignment_verified = bool(
        not parse_errors
        and not missing_count
        and not mismatch_count
        and not metadata_error_count
        and all(row["video_path_empty"] is False for row in label_rows)
    )
    reasons = [
        "formal gate requires an explicit clip-generation/alignment manifest; none was found in the read-only data package",
        f"{missing_count} label rows have no exact clip.source_vid basename under videos/",
        f"{mismatch_count} label rows have provenance.video_sha256 mismatches",
        f"{metadata_error_count} matched rows lack valid PyAV video metadata",
        f"video_path is empty in {sum(row['video_path_empty'] for row in label_rows)} label rows, so no alternate path evidence exists",
        "candidate source-group splits are planning artifacts and are explicitly blocked from training entrypoints",
    ]
    passed = bool(
        alignment_verified
        and zero_group_leakage
        and split_counts["train"]["trusted_identity"] >= 200
        and split_counts["dev"]["trusted_identity"] >= 50
        and split_counts["holdout"]["trusted_identity"] >= 50
    )
    if zero_group_leakage:
        pass
    else:
        reasons.append("candidate source-group split failed zero-leakage check")

    gate = {
        "schema_version": "aic_data_training_gate_v1",
        "audit_script_version": SCRIPT_VERSION,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data_root": str(data_root),
        "labels_path": str(labels_path),
        "seed": args.seed,
        "passed": passed,
        "alignment_verified": alignment_verified,
        "alignment_basis": "exact clip.source_vid basename + provenance SHA-256 + PyAV headers for row evidence; formal source-to-processed temporal transform is unproven",
        "counts": split_counts,
        "thresholds": {"trusted_train_min": 200, "trusted_dev_min": 50, "trusted_holdout_min": 50},
        "reasons": reasons,
        "checks": {
            "candidate_zero_group_leakage": zero_group_leakage,
            "candidate_split_group_counts": {
                name: len(candidate_split_groups[name]) for name in split_names
            },
            "candidate_split_label_counts": {
                name: split_counts[name]["labels"] for name in split_names
            },
            "original_train_val_overlap_groups": len(original_overlap),
            "exact_source_file_rows": sum(row["source_exists"] for row in label_rows),
            "exact_source_metadata_ok_rows": sum(
                row["source_exists"] and row["metadata_status"] == "ok" for row in label_rows
            ),
        },
        "global_counts": {
            "label_rows": len(label_rows),
            "source_groups": source_groups_count,
            "video_files": len(video_paths),
            "trusted_identity_rows": trusted_total,
            "missing_source_rows": missing_count,
            "hash_mismatch_rows": mismatch_count,
            "metadata_error_rows": metadata_error_count,
            "original_train_val_overlap_groups": len(original_overlap),
            "candidate_zero_group_leakage": zero_group_leakage,
        },
        "candidate_artifacts": {
            "groups": "candidate_groups.jsonl",
            "rows": "candidate_splits.jsonl",
            "warning": "candidate-only planning artifacts; do_not_use_as_training=true",
        },
    }

    label_columns = [
        "line_no",
        "video_id",
        "dataset_split",
        "schema_version",
        "annotation_mode",
        "targetRatioWH",
        "source_vid",
        "source_group",
        "source_file",
        "source_exists",
        "source_match_count",
        "source_size_bytes",
        "expected_sha256",
        "actual_sha256",
        "hash_status",
        "metadata_status",
        "width",
        "height",
        "duration_s",
        "frames",
        "fps",
        "fps_num",
        "fps_den",
        "codec",
        "clip_start_sec",
        "clip_end_sec",
        "qvh_window",
        "segment_count",
        "video_path_empty",
        "schema_valid",
        "alignment_class",
        "trusted_for_gate",
        "candidate_split",
        "candidate_only",
        "do_not_use_as_training",
        "isolation_reasons",
    ]
    video_columns = [
        "relpath",
        "basename",
        "stem",
        "size_bytes",
        "label_related",
        "sha256",
        "metadata_status",
        "metadata_error",
        "width",
        "height",
        "duration_s",
        "frames",
        "fps",
        "fps_num",
        "fps_den",
        "codec",
        "time_base",
    ]

    json_dump(out_dir / "training_gate.json", gate)
    jsonl_dump(out_dir / "labels_inventory.jsonl", label_rows)
    jsonl_dump(out_dir / "candidate_groups.jsonl", candidate_group_rows)
    jsonl_dump(out_dir / "candidate_splits.jsonl", candidate_rows)
    jsonl_dump(out_dir / "anomalies.jsonl", anomalies)
    write_tsv(out_dir / "video_inventory.tsv", video_rows, video_columns)
    json_dump(
        out_dir / "candidate_split_leakage.json",
        {
            "candidate_only": True,
            "seed": args.seed,
            "group_key": "clip.source_vid with final numeric _start_end removed",
            "split_group_counts": {name: len(candidate_split_groups[name]) for name in split_names},
            "split_label_counts": {name: split_counts[name]["labels"] for name in split_names},
            "overlap_groups": leakage_pairs,
            "zero_group_leakage": zero_group_leakage,
        },
    )
    json_dump(
        out_dir / "audit_summary.json",
        {
            "audit_script_version": SCRIPT_VERSION,
            "generated_at_utc": gate["generated_at_utc"],
            "elapsed_seconds": round(time.time() - started, 3),
            "data_root": str(data_root),
            "labels_file": {"path": str(labels_path), "rows": len(label_rows), "parse_errors": len(parse_errors)},
            "video_files": len(video_paths),
            "label_related_video_stems": len(related_stems),
            "hash_policy": "label-related MP4s only" if not args.no_hash_related else "disabled",
            "source_groups": source_groups_count,
            "original_split_rows": collections.Counter(row["dataset_split"] for row in label_rows),
            "original_train_val_overlap_groups": original_overlap,
            "candidate_split_counts": split_counts,
            "candidate_zero_group_leakage": zero_group_leakage,
            "training_gate": "training_gate.json",
            "teacher_signals_policy": "teacher_signals omitted from all artifacts",
        },
    )

    print(json.dumps({
        "status": "ok",
        "out_dir": str(out_dir),
        "labels": len(label_rows),
        "videos": len(video_paths),
        "source_groups": source_groups_count,
        "trusted_identity": trusted_total,
        "missing_source": missing_count,
        "hash_mismatch": mismatch_count,
        "metadata_errors": metadata_error_count,
        "original_train_val_overlap_groups": len(original_overlap),
        "candidate_split_counts": split_counts,
        "candidate_zero_group_leakage": zero_group_leakage,
        "training_gate_passed": passed,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
