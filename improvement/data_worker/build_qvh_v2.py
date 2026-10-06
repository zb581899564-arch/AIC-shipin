#!/usr/bin/env python3
"""Build deterministic QVHighlights query-retrieval candidates, fail closed.

The script never reads the sealed contest test directory.  It validates only
the user-provided QVHighlights training videos and pinned official annotations.
Source provenance and media alignment are deliberately separate decisions:
aligned rows remain candidate-only until a supervisor explicitly confirms the
source package provenance.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import re
import shutil
import statistics
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


ANNOTATION_COMMIT = "b7e553ac3b0c898ee6b85e03ee507c064eab89ca"
REPOSITORY_URL = "https://github.com/jayleicn/moment_detr"
SHARE_URL = "https://pan.baidu.com/s/1MspCw2p1-Mf0Ke8MZtY8-w?pwd=pixw"
UNC_ARCHIVE_URL = "https://nlp.cs.unc.edu/data/jielei/qvh/qvhilights_videos.tar.gz"
TASK_TYPE = "query_moment_retrieval"
SEED = 42
TARGETS = {"train": 1000, "dev": 100, "holdout": 100}
MINIMUMS = {"train": 200, "dev": 50, "holdout": 50}
DEV_ONLY_GROUPS = {"wUgPzvcKK5c"}
EXPECTED_SOURCE_SHA256 = {
    "highlight_train_release.jsonl": "fd28404187468f57cf99242be2963127dc9b4aef26c7de3cb9469569801f2625",
    "highlight_val_release.jsonl": "f668a1eaea156ec5315e14718999cea043a8cf948d3cafbd8e8d655318c3cd02",
    "LICENSE": "7e46ea42ece13fd153d63c72bef744b1ec0a378dcf008b075b8a989e640825eb",
    "README.md": "86b719477ee4f068722e27190957c2a73178efd9149c405b1d0f3d912241f1b8",
    "data_README.md": "41282f76f634d0fc026fc9db6fa2083be3c81bcbff3eb897e41d9bfb1cbfa3ad",
    "data_LICENSE": "9e502ba75fd0fd30cea5497b438a4bc12f07f02bc932a7a6041fd6a18b8f46a0",
}
VIDEO_SUFFIX = re.compile(r"^(?P<group>.+)_(?P<start>-?\d+(?:\.\d+)?)_(?P<end>-?\d+(?:\.\d+)?)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_group(vid: str) -> str:
    parts = vid.rsplit("_", 2)
    return parts[0] if len(parts) == 3 else vid


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: row is not an object")
            value["_line"] = number
            rows.append(value)
    return rows


def annotation_errors(row: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    required = ("qid", "query", "duration", "vid", "relevant_clip_ids", "saliency_scores", "relevant_windows")
    errors.extend(f"MISSING_{key.upper()}" for key in required if key not in row)
    if errors:
        return errors
    if not isinstance(row["qid"], int) or isinstance(row["qid"], bool):
        errors.append("INVALID_QID")
    if not isinstance(row["query"], str) or not row["query"].strip():
        errors.append("INVALID_QUERY")
    if not isinstance(row["vid"], str) or not VIDEO_SUFFIX.fullmatch(row["vid"]):
        errors.append("INVALID_VID")
    duration = row["duration"]
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(float(duration)) or duration <= 0:
        errors.append("INVALID_DURATION")
        return errors
    windows = row["relevant_windows"]
    if not isinstance(windows, list):
        errors.append("INVALID_RELEVANT_WINDOWS")
    else:
        for window in windows:
            if (
                not isinstance(window, list)
                or len(window) != 2
                or any(not isinstance(x, (int, float)) or isinstance(x, bool) for x in window)
                or not 0 <= float(window[0]) < float(window[1]) <= float(duration)
            ):
                errors.append("RELEVANT_WINDOW_OUT_OF_BOUNDS")
                break
        if len(windows) > 4:
            errors.append("TOO_MANY_RELEVANT_WINDOWS")
        valid_windows = [
            (float(window[0]), float(window[1]))
            for window in windows
            if isinstance(window, list)
            and len(window) == 2
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in window)
        ]
        if len(valid_windows) == len(windows):
            if valid_windows != sorted(valid_windows):
                errors.append("UNORDERED_RELEVANT_WINDOWS")
            if any(current[0] < previous[1] for previous, current in zip(valid_windows, valid_windows[1:])):
                errors.append("OVERLAPPING_RELEVANT_WINDOWS")
    clips, scores = row["relevant_clip_ids"], row["saliency_scores"]
    if not isinstance(clips, list) or not isinstance(scores, list) or len(clips) != len(scores):
        errors.append("INVALID_SALIENCY_ALIGNMENT")
    return errors


def saliency_segments_2s(row: Mapping[str, Any]) -> List[List[float]]:
    """Return unmerged 2-second diagnostic intervals with median score >= 3."""

    duration = float(row["duration"])
    result: List[List[float]] = []
    for clip_id, scores in zip(row["relevant_clip_ids"], row["saliency_scores"]):
        if not isinstance(clip_id, int) or not isinstance(scores, list) or not scores:
            continue
        numeric = [float(x) for x in scores if isinstance(x, (int, float)) and not isinstance(x, bool)]
        if len(numeric) != len(scores) or statistics.median(numeric) < 3:
            continue
        start = 2.0 * clip_id
        end = min(start + 2.0, duration)
        if 0 <= start < end:
            result.append([start, end])
    return result


def clip_diagnostic_segments(segments: Sequence[Sequence[float]], media_duration: float) -> Tuple[List[List[float]], int]:
    """Intersect diagnostic intervals with decoded media time; never rescale."""

    result: List[List[float]] = []
    clipped = 0
    for start, end in segments:
        new_start = max(0.0, float(start))
        new_end = min(float(end), float(media_duration))
        if new_start != float(start) or new_end != float(end):
            clipped += 1
        if new_start < new_end:
            result.append([new_start, new_end])
    return result, clipped


def video_path_for(video_root: Path, vid: str) -> Path:
    return video_root / vid[0].lower() / f"{vid}.mp4"


def verify_media(path: Path, annotation_duration: float) -> Dict[str, Any]:
    """Hash a video and verify header, first frame, final frame, and duration."""

    result: Dict[str, Any] = {"video_path": str(path), "errors": []}
    if not path.is_file():
        result["errors"].append("MEDIA_NOT_FOUND")
        return result
    try:
        import av  # type: ignore
    except Exception as exc:  # pragma: no cover - environment-specific
        result["errors"].append(f"PYAV_UNAVAILABLE:{type(exc).__name__}")
        return result
    try:
        result["video_sha256"] = sha256_file(path)
        result["file_size_bytes"] = path.stat().st_size
        with av.open(str(path)) as container:
            if not container.streams.video:
                result["errors"].append("NO_VIDEO_STREAM")
                return result
            stream = container.streams.video[0]
            if stream.duration is None or stream.time_base is None:
                result["errors"].append("STREAM_DURATION_UNAVAILABLE")
                return result
            duration = float(stream.duration * stream.time_base)
            fps = float(stream.average_rate) if stream.average_rate else 0.0
            n_frames = int(stream.frames or 0)
            if duration <= 0 or not math.isfinite(duration):
                result["errors"].append("INVALID_MEDIA_DURATION")
            if fps <= 0 or not math.isfinite(fps):
                result["errors"].append("INVALID_FPS")
            if n_frames <= 0:
                result["errors"].append("N_FRAMES_UNAVAILABLE")
            first = next(container.decode(stream), None)
            if first is None or first.pts is None:
                result["errors"].append("FIRST_FRAME_DECODE_FAILED")
                first_sec = None
            else:
                start_pts = int(stream.start_time or 0)
                first_sec = float((first.pts - start_pts) * stream.time_base)
                if first_sec < -0.05 or first_sec > 1.0:
                    result["errors"].append("FIRST_FRAME_TIMELINE_MISMATCH")
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            stream_duration = float(stream.duration * stream.time_base)
            target = max(0.0, stream_duration - 5.0)
            container.seek(int(target / float(stream.time_base)), stream=stream, backward=True, any_frame=False)
            last = None
            for frame in container.decode(stream):
                last = frame
            if last is None or last.pts is None:
                result["errors"].append("LAST_FRAME_DECODE_FAILED")
                last_sec = None
                frame_end_sec = None
            else:
                start_pts = int(stream.start_time or 0)
                last_sec = float((last.pts - start_pts) * stream.time_base)
                frame_end_sec = last_sec + (1.0 / fps if fps > 0 else 0.0)
                if abs(frame_end_sec - stream_duration) > 1.0:
                    result["errors"].append("LAST_FRAME_TIMELINE_MISMATCH")
        result.update(
            {
                "duration_sec": duration,
                "annotation_duration_sec": float(annotation_duration),
                "duration_delta_sec": abs(duration - float(annotation_duration)),
                "fps": fps,
                "n_frames": n_frames,
                "first_frame_sec": first_sec,
                "last_frame_sec": last_sec,
                "last_frame_end_sec": frame_end_sec,
            }
        )
        if result["duration_delta_sec"] > 1.0:
            result["errors"].append("DURATION_DELTA_GT_1S")
    except Exception as exc:
        result["errors"].append(f"MEDIA_READ_ERROR:{type(exc).__name__}:{exc}")
    result["ok"] = not result["errors"]
    return result


def grouped_order(rows: Sequence[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[source_group(row["vid"])].append(row)
    rng = random.Random(seed)
    keys = sorted(groups)
    rng.shuffle(keys)
    ordered: List[Dict[str, Any]] = []
    for key in keys:
        members = sorted(groups[key], key=lambda item: (item["vid"], item["qid"]))
        rng.shuffle(members)
        ordered.extend(members)
    return ordered


def partition_val_groups(rows: Sequence[Dict[str, Any]], seed: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[source_group(row["vid"])].append(row)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    dev_keys = set(keys[::2]) | (DEV_ONLY_GROUPS & set(keys))
    dev = [row for key in keys if key in dev_keys for row in sorted(groups[key], key=lambda item: (item["vid"], item["qid"]))]
    holdout = [row for key in keys if key not in dev_keys for row in sorted(groups[key], key=lambda item: (item["vid"], item["qid"]))]
    return grouped_order(dev, seed + 1), grouped_order(holdout, seed + 2)


def select_verified(
    candidates: Sequence[Dict[str, Any]],
    count: int,
    video_root: Path,
    cache: MutableMapping[str, Dict[str, Any]],
    workers: int,
) -> Tuple[List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]]]:
    accepted: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    rejected: List[Dict[str, Any]] = []
    index = 0
    while len(accepted) < count and index < len(candidates):
        batch = list(candidates[index : index + 128])
        index += len(batch)
        pending: Dict[str, Tuple[Path, float]] = {}
        for row in batch:
            path = video_path_for(video_root, row["vid"])
            key = str(path)
            if key not in cache:
                pending[key] = (path, float(row["duration"]))
        if pending:
            keys = list(pending)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = pool.map(lambda key: verify_media(*pending[key]), keys)
                cache.update(zip(keys, results))
        for row in batch:
            if len(accepted) >= count:
                break
            media = cache[str(video_path_for(video_root, row["vid"]))]
            row_errors = annotation_errors(row)
            windows_ok = all(float(end) <= float(media.get("duration_sec", -1)) + 1e-6 for _, end in row.get("relevant_windows", []))
            if not windows_ok:
                row_errors.append("RELEVANT_WINDOW_EXCEEDS_MEDIA")
            errors = row_errors + list(media.get("errors", []))
            if errors:
                rejected.append(
                    {
                        "qid": row.get("qid"),
                        "vid": row.get("vid"),
                        "annotation_duration_sec": row.get("duration"),
                        "media_duration_sec": media.get("duration_sec"),
                        "relevant_windows": row.get("relevant_windows"),
                        "errors": sorted(set(errors)),
                    }
                )
            else:
                accepted.append((row, media))
    return accepted, rejected


def training_row(annotation: Mapping[str, Any], media: Mapping[str, Any], split: str, trusted: bool) -> Dict[str, Any]:
    windows = [[float(start), float(end)] for start, end in annotation["relevant_windows"]]
    saliency, saliency_clipped = clip_diagnostic_segments(
        saliency_segments_2s(annotation), float(media["duration_sec"])
    )
    query = annotation["query"].strip()
    result: Dict[str, Any] = {
        "video_id": f"qvh_{annotation['qid']}",
        "source_vid": annotation["vid"],
        "annotation_id": f"qvh_{annotation['qid']}",
        "source_group": source_group(annotation["vid"]),
        "video_path": media["video_path"],
        "video_sha256": media["video_sha256"],
        "alignment_verified": True,
        "trusted_identity": trusted,
        "annotation_revision": ANNOTATION_COMMIT,
        "task_type": TASK_TYPE,
        "query": query,
        "prompt": f"Locate all video moments relevant to this query: {query}",
        "answer": {"segments": windows},
        "relevant_windows": windows,
        "saliency_segments": saliency,
        "saliency_segments_clipped_count": saliency_clipped,
        "duration_sec": media["duration_sec"],
        "annotation_duration_sec": float(annotation["duration"]),
        "fps": media["fps"],
        "n_frames": media["n_frames"],
        "official_split": "train" if split == "train" else "val",
        "split": split,
    }
    if not trusted:
        result.update(
            {
                "candidate_only": True,
                "do_not_use_as_training": True,
                "source_trust_status": "PENDING_SUPERVISOR_ADJUDICATION",
            }
        )
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def count_log_matches(path: Path, pattern: str) -> int:
    if not path.is_file():
        return 0
    regex = re.compile(pattern)
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if regex.search(line))


def build_source_evidence(args: argparse.Namespace, generated_at: str) -> Dict[str, Any]:
    source_files: Dict[str, Any] = {}
    for name, expected in EXPECTED_SOURCE_SHA256.items():
        path = args.source_dir / name
        actual = sha256_file(path) if path.is_file() else None
        source_files[name] = {"path": str(path), "sha256": actual, "expected_sha256": expected, "matches_pin": actual == expected}
    return {
        "schema_version": "qvh_v2_source_evidence_v1",
        "generated_at_utc": generated_at,
        "official_annotation": {
            "repository_url": REPOSITORY_URL,
            "commit": ANNOTATION_COMMIT,
            "dataset_license_spdx": "CC-BY-NC-SA-4.0",
            "dataset_license_file": "data_LICENSE",
            "repository_code_license_spdx": "MIT",
            "repository_code_license_file": "LICENSE",
            "files": source_files,
        },
        "media_package": {
            "user_supplied_share_url": SHARE_URL,
            "baidu_download_log": {
                "path": str(args.baidu_log),
                "sha256": sha256_file(args.baidu_log) if args.baidu_log.is_file() else None,
                "zip_download_complete_lines": count_log_matches(args.baidu_log, r"下载完成.*qvhighlights-videos-[^/]+\.zip"),
                "declared_total_line_present": count_log_matches(args.baidu_log, r"下载结束.*124\.026100GB") == 1,
                "integrity_warning_present": count_log_matches(args.baidu_log, r"跳过文件有效性检验") > 0,
                "share_id_bound_in_log": count_log_matches(args.baidu_log, r"1MspCw2p1-Mf0Ke8MZtY8-w") > 0,
            },
            "unzip": {
                "script_path": str(args.unzip_script),
                "script_sha256": sha256_file(args.unzip_script) if args.unzip_script.is_file() else None,
                "log_path": str(args.unzip_log),
                "log_sha256": sha256_file(args.unzip_log) if args.unzip_log.is_file() else None,
                "zip_attempt_lines": count_log_matches(args.unzip_log, r"^解压 qvhighlights-videos-[^/]+\.zip"),
                "status_path": str(args.unzip_status),
                "status_sha256": sha256_file(args.unzip_status) if args.unzip_status.is_file() else None,
                "status": args.unzip_status.read_text(encoding="utf-8", errors="replace").strip() if args.unzip_status.is_file() else None,
                "warning": "UNZIP_ALL_DONE is emitted even when an individual unzip command fails",
            },
            "unc_alternative": {
                "url": UNC_ARCHIVE_URL,
                "content_length_observed_2026_09_10": 143734787897,
                "etag_observed_2026_09_10": "217742cf39-5f48976492b8f",
                "archive_sha256": "NOT_AVAILABLE",
                "local_parts_present": 0,
                "note": "dl_unc.sh exists, but no retained parts or assembly/extraction record binds current videos to this archive",
            },
            "current_video_inventory": {
                "root": str(args.video_root),
                "file_count": sum(1 for path in args.video_root.rglob("*.mp4") if path.is_file()),
            },
        },
        "source_identity_decision": {
            "status": "CONFIRMED" if args.source_trust == "confirmed" else "PENDING_SUPERVISOR_ADJUDICATION",
            "blocking_facts": [] if args.source_trust == "confirmed" else [
                "download log does not contain the user-provided share ID",
                "download tool skipped ZIP validity checks",
                "source ZIPs and their hashes are no longer present",
                "UNC archive parts/hash/assembly record are not present",
            ],
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--video-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--baidu-log", type=Path, required=True)
    parser.add_argument("--unzip-script", type=Path, required=True)
    parser.add_argument("--unzip-log", type=Path, required=True)
    parser.add_argument("--unzip-status", type=Path, required=True)
    parser.add_argument("--source-trust", choices=("pending", "confirmed"), default="pending")
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.workers < 1 or args.workers > 8:
        raise ValueError("--workers must be in [1, 8]")
    if any(not (args.source_dir / name).is_file() for name in EXPECTED_SOURCE_SHA256):
        raise FileNotFoundError("pinned source file missing")
    bad_pins = [name for name, digest in EXPECTED_SOURCE_SHA256.items() if sha256_file(args.source_dir / name) != digest]
    if bad_pins:
        raise ValueError(f"source hash mismatch: {bad_pins}")
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    train_all = load_jsonl(args.source_dir / "highlight_train_release.jsonl")
    val_all = load_jsonl(args.source_dir / "highlight_val_release.jsonl")
    matched_rows = {
        "train": [row for row in train_all if video_path_for(args.video_root, row["vid"]).is_file()],
        "val": [row for row in val_all if video_path_for(args.video_root, row["vid"]).is_file()],
    }
    train_groups = {source_group(row["vid"]) for row in train_all if isinstance(row.get("vid"), str)}
    val_groups = {source_group(row["vid"]) for row in val_all if isinstance(row.get("vid"), str)}
    boundary_overlap = train_groups & val_groups
    annotation_rejects: List[Dict[str, Any]] = []
    def eligible(rows: Sequence[Dict[str, Any]], official_split: str) -> List[Dict[str, Any]]:
        result = []
        for row in rows:
            errors = annotation_errors(row)
            if isinstance(row.get("vid"), str) and source_group(row["vid"]) in boundary_overlap:
                errors.append("SOURCE_GROUP_CROSSES_OFFICIAL_TRAIN_VAL")
            path = video_path_for(args.video_root, row["vid"]) if isinstance(row.get("vid"), str) and row["vid"] else None
            if path is None or not path.is_file():
                errors.append("MEDIA_NOT_FOUND")
            if errors:
                annotation_rejects.append({"official_split": official_split, "qid": row.get("qid"), "vid": row.get("vid"), "errors": sorted(set(errors))})
            else:
                result.append(row)
        return result
    train_eligible = eligible(train_all, "train")
    val_eligible = eligible(val_all, "val")
    dev_candidates, holdout_candidates = partition_val_groups(val_eligible, SEED)
    candidate_orders = {
        "train": grouped_order(train_eligible, SEED),
        "dev": dev_candidates,
        "holdout": holdout_candidates,
    }
    cache: Dict[str, Dict[str, Any]] = {}
    selected: Dict[str, List[Dict[str, Any]]] = {}
    media_rejects: List[Dict[str, Any]] = []
    trusted = args.source_trust == "confirmed"
    for split in ("train", "dev", "holdout"):
        verified, rejected = select_verified(candidate_orders[split], TARGETS[split], args.video_root, cache, args.workers)
        media_rejects.extend({"requested_split": split, **item} for item in rejected)
        selected[split] = [training_row(row, media, split, trusted) for row, media in verified]
        write_jsonl(args.output_dir / f"{split}.jsonl", selected[split])
    counts = {split: len(rows) for split, rows in selected.items()}
    group_sets = {split: {row["source_group"] for row in rows} for split, rows in selected.items()}
    overlap = {
        "train__dev": sorted(group_sets["train"] & group_sets["dev"]),
        "train__holdout": sorted(group_sets["train"] & group_sets["holdout"]),
        "dev__holdout": sorted(group_sets["dev"] & group_sets["holdout"]),
    }
    source_evidence = build_source_evidence(args, generated_at)
    write_json(args.output_dir / "evidence" / "source_evidence.json", source_evidence)
    write_jsonl(args.output_dir / "evidence" / "quarantine.jsonl", annotation_rejects + media_rejects)
    reasons: List[str] = []
    if not trusted:
        reasons.append("SOURCE_PACKAGE_PROVENANCE_PENDING_SUPERVISOR_ADJUDICATION")
    if any(counts[split] < MINIMUMS[split] for split in MINIMUMS):
        reasons.append("TRUSTED_OR_ALIGNED_COUNT_BELOW_MINIMUM")
    if any(overlap.values()):
        reasons.append("SOURCE_GROUP_OVERLAP")
    aligned = all(counts[split] >= TARGETS[split] for split in TARGETS) and not any(overlap.values())
    gate = {
        "schema_version": "qvh_v2_training_gate_v1",
        "generated_at_utc": generated_at,
        "passed": trusted and aligned and not reasons,
        "alignment_verified": aligned,
        "source_identity_status": source_evidence["source_identity_decision"]["status"],
        "annotation_revision": ANNOTATION_COMMIT,
        "task_type": TASK_TYPE,
        "seed": SEED,
        "thresholds": MINIMUMS,
        "counts": {
            split: {
                "aligned_candidate": counts[split],
                "trusted_identity": counts[split] if trusted else 0,
                "groups": len(group_sets[split]),
            }
            for split in TARGETS
        },
        "candidate_artifacts": {split: str(args.output_dir / f"{split}.jsonl") for split in TARGETS},
        "reasons": reasons,
        "cross_split_source_group_overlap": overlap,
    }
    if gate["passed"]:
        gate["accepted_splits"] = {split: {"path": str(args.output_dir / f"{split}.jsonl")} for split in TARGETS}
    write_json(args.output_dir / "gate" / "training_gate.json", gate)
    summary = {
        "schema_version": "qvh_v2_summary_v1",
        "generated_at_utc": generated_at,
        "annotation_revision": ANNOTATION_COMMIT,
        "official_rows": {"train": len(train_all), "val": len(val_all)},
        "official_unique_videos": {"train": len({r["vid"] for r in train_all}), "val": len({r["vid"] for r in val_all})},
        "matched_annotation_rows_before_contract": {split: len(rows) for split, rows in matched_rows.items()},
        "matched_unique_videos_before_contract": {split: len({row["vid"] for row in rows}) for split, rows in matched_rows.items()},
        "matched_after_boundary_exclusion": {"train": len(train_eligible), "val": len(val_eligible)},
        "official_cross_boundary_source_groups_removed": len(boundary_overlap),
        "dev_only_source_groups": sorted(DEV_ONLY_GROUPS),
        "output_rows": counts,
        "output_groups": {split: len(groups) for split, groups in group_sets.items()},
        "diagnostic_saliency_segments_clipped": sum(
            int(row["saliency_segments_clipped_count"])
            for rows in selected.values()
            for row in rows
        ),
        "verified_unique_media": sum(1 for value in cache.values() if value.get("ok")),
        "media_verification_failures": sum(1 for value in cache.values() if not value.get("ok")),
        "rejection_reason_counts": dict(
            sorted(
                Counter(
                    reason
                    for item in annotation_rejects + media_rejects
                    for reason in item.get("errors", [])
                ).items()
            )
        ),
        "quarantine_rows": len(annotation_rejects) + len(media_rejects),
        "gate_passed": gate["passed"],
        "gate_reasons": gate["reasons"],
        "target_semantics": {
            "answer.segments": "official query-conditioned relevant_windows; training target",
            "saliency_segments": "diagnostic-only 2-second intervals whose annotator-score median is >= 3; endpoint is intersected with decoded media duration when needed",
            "time_transform": "NONE; rows whose relevant-window endpoint exceeds decoded media duration are quarantined",
            "aic_generic_highlight_ground_truth": "NOT_CLAIMED",
            "bbox_ground_truth": "NOT_AVAILABLE",
        },
    }
    write_json(args.output_dir / "summary.json", summary)
    artifact_hashes = {}
    for path in sorted(args.output_dir.rglob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            artifact_hashes[str(path.relative_to(args.output_dir))] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    write_json(args.output_dir / "artifact_manifest.json", {"schema_version": "qvh_v2_artifact_manifest_v1", "files": artifact_hashes})
    report = f"""# QVHighlights v2 data gate\n\nGenerated: {generated_at}\n\n- Official annotation commit: `{ANNOTATION_COMMIT}`\n- Rows: train={counts['train']}, dev={counts['dev']}, holdout={counts['holdout']} (seed {SEED})\n- Official train/val crossing source groups removed: {len(boundary_overlap)}\n- Cross-output source-group overlap: {sum(len(v) for v in overlap.values())}\n- Media checks: SHA-256, PyAV header, first/final decode, frame timeline, duration delta <= 1 second, window bounds\n- Window endpoint beyond media duration: {summary['rejection_reason_counts'].get('RELEVANT_WINDOW_EXCEEDS_MEDIA', 0)} quarantined; timestamps are never scaled\n- Diagnostic saliency intervals intersected with media duration: {summary['diagnostic_saliency_segments_clipped']}\n- More than four windows: {summary['rejection_reason_counts'].get('TOO_MANY_RELEVANT_WINDOWS', 0)} quarantined\n- Unordered windows: {summary['rejection_reason_counts'].get('UNORDERED_RELEVANT_WINDOWS', 0)} quarantined\n- Overlapping windows: {summary['rejection_reason_counts'].get('OVERLAPPING_RELEVANT_WINDOWS', 0)} quarantined\n- Gate: **{'PASS' if gate['passed'] else 'REJECT'}**\n- Reasons: {', '.join(gate['reasons']) if gate['reasons'] else 'none'}\n\n`answer.segments` contains the official query-conditioned `relevant_windows`. `saliency_segments` is diagnostic only and is clipped, never rescaled, only at the decoded media endpoint. Neither target is claimed as generic AIC highlight ground truth, and no bounding boxes are fabricated.\n"""
    args.report_dir.mkdir(parents=True, exist_ok=True)
    with (args.report_dir / "qvh_v2_data_report.md").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    shutil.copyfile(args.output_dir / "summary.json", args.report_dir / "qvh_v2_summary.json")
    shutil.copyfile(args.output_dir / "gate" / "training_gate.json", args.report_dir / "qvh_v2_training_gate.json")
    shutil.copyfile(args.output_dir / "evidence" / "source_evidence.json", args.report_dir / "qvh_v2_source_evidence.json")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if aligned else 2


if __name__ == "__main__":
    raise SystemExit(main())
