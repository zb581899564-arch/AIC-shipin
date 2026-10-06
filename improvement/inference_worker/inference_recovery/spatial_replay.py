#!/usr/bin/env python3
"""Replay only frozen spatial cropping with sequential-from-zero frame reads."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inference_recovery.reader import extract_frames
from inference_v2 import baseline_v2


VERSION = "sequential-from-zero-spatial-replay-v1"
ROOT = Path("/home/inspur/aic_video_work").resolve()
FIXED_MODEL = (ROOT / "models/Qwen3-VL-4B-Instruct").resolve()
MAX_PIXELS = 131072
MAX_VIDEO_FRAMES = 64
CROP_STRIDE = 15
CROP_TOKENS = 128
DETECT_FPS = 2.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str:
    """Hash relative paths and bytes for every file in a model directory."""

    root = path.resolve(strict=True)
    digest = hashlib.sha256()
    files = sorted(item for item in root.rglob("*") if item.is_file())
    if not files:
        raise ValueError(f"model directory has no files: {root}")
    for item in files:
        relative = item.relative_to(root).as_posix().encode("utf-8")
        real = item.resolve(strict=True)
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(real.stat().st_size.to_bytes(8, "big"))
        with real.open("rb") as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, raw in enumerate(stream, 1):
            if not raw.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row must be an object at {path}:{line_number}")
            rows.append(value)
    return rows


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _validate_pairs(
    value: Any,
    *,
    name: str,
    integer: bool,
    maximum: float | int | None = None,
) -> List[Tuple[float, float]] | List[Tuple[int, int]]:
    if not isinstance(value, list) or len(value) > 4:
        raise ValueError(f"{name} must be an array with at most four segments")
    pairs: List[Any] = []
    previous_end: float | int | None = None
    for index, pair in enumerate(value):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"{name}[{index}] must be [start,end]")
        if integer:
            if any(isinstance(x, bool) or not isinstance(x, int) for x in pair):
                raise ValueError(f"{name}[{index}] boundaries must be integers")
            start, end = int(pair[0]), int(pair[1])
        else:
            if any(not _finite_number(x) for x in pair):
                raise ValueError(f"{name}[{index}] boundaries must be finite numbers")
            start, end = float(pair[0]), float(pair[1])
        if start < 0 or end <= start:
            raise ValueError(f"{name}[{index}] is reversed or empty: {pair!r}")
        if previous_end is not None and start < previous_end:
            raise ValueError(f"{name} is out of order or overlapping at index {index}")
        if maximum is not None and end > maximum:
            raise ValueError(f"{name}[{index}] exceeds media bound {maximum}")
        pairs.append((start, end))
        previous_end = end
    return pairs


def validate_temporal_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    video_id = str(row.get("video_id")) if row.get("video_id") is not None else ""
    if not video_id:
        raise ValueError("temporal row has no video_id")
    if row.get("status") not in ("ok", "valid_empty"):
        raise ValueError(f"temporal status is not successful for {video_id}")
    if "query" not in row or row["query"] is not None:
        raise ValueError(f"temporal query must be explicit null for {video_id}")
    if row.get("policy") != "multi":
        raise ValueError(f"temporal policy must be multi for {video_id}")
    if row.get("adapter") is not None:
        raise ValueError(f"temporal adapter must be null for {video_id}")
    if row.get("constrained_json") is not True:
        raise ValueError(f"constrained_json must be true for {video_id}")
    if row.get("constraint_backend") != "regex":
        raise ValueError(f"constraint_backend must be regex for {video_id}")
    if not isinstance(row.get("sampling"), list):
        raise ValueError(f"temporal sampling must be an array for {video_id}")
    if row.get("source_group") is None:
        raise ValueError(f"temporal source_group is missing for {video_id}")
    seconds = _validate_pairs(row.get("segments_sec"), name="segments_sec", integer=False)
    frames = _validate_pairs(row.get("segments_frames"), name="segments_frames", integer=True)
    if row["status"] == "valid_empty" and (seconds or frames):
        raise ValueError(f"valid_empty temporal row contains segments for {video_id}")
    if row["status"] == "ok" and (not seconds or not frames):
        raise ValueError(f"ok temporal row has empty segments for {video_id}")
    if len(seconds) != len(frames):
        raise ValueError(f"temporal second/frame segment count differs for {video_id}")
    timing = row.get("timing")
    if not isinstance(timing, dict) or any(
        not _finite_number(timing.get(name)) or float(timing[name]) < 0
        for name in ("total_sec", "stage1_sec", "stage2_sec")
    ):
        raise ValueError(f"temporal timing is invalid for {video_id}")
    vram = row.get("VRAM")
    if not isinstance(vram, dict) or not _finite_number(vram.get("peak_mib")) or float(vram["peak_mib"]) < 0:
        raise ValueError(f"temporal VRAM record is invalid for {video_id}")
    if not isinstance(row.get("metadata"), dict):
        raise ValueError(f"temporal metadata is missing for {video_id}")
    return dict(row)


def validate_temporal_for_media(
    row: Mapping[str, Any],
    *,
    item: Mapping[str, Any],
    n_frames: int,
    fps: float,
    width: int,
    height: int,
) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]]]:
    video_id = str(item["video_id"])
    if str(row["video_id"]) != video_id:
        raise ValueError(f"temporal video identity differs for {video_id}")
    if str(row["source_group"]) != str(item["source_group"]):
        raise ValueError(f"temporal source_group differs for {video_id}")
    duration = n_frames / fps
    seconds = _validate_pairs(
        row["segments_sec"], name="segments_sec", integer=False, maximum=duration + 1e-5
    )
    frames = _validate_pairs(
        row["segments_frames"], name="segments_frames", integer=True, maximum=n_frames
    )
    metadata = row["metadata"]
    expected = {"n_frames": n_frames, "width": width, "height": height}
    for name, value in expected.items():
        if metadata.get(name) != value:
            raise ValueError(f"temporal metadata {name} differs for {video_id}")
    if not _finite_number(metadata.get("fps")) or not math.isclose(
        float(metadata["fps"]), fps, rel_tol=1e-9, abs_tol=1e-9
    ):
        raise ValueError(f"temporal metadata fps differs for {video_id}")
    return seconds, frames


def write_line(stream: Any, value: Mapping[str, Any]) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def _model_args(model: Path) -> argparse.Namespace:
    return argparse.Namespace(
        model=str(model),
        max_pixels=MAX_PIXELS,
        max_video_frames=MAX_VIDEO_FRAMES,
        device_map="auto",
        attn_implementation="sdpa",
        temporal_adapter=None,
    )


def _recovery_contract(temporal_path: Path, model_path: Path) -> Dict[str, Any]:
    inference_contract = baseline_v2.contract()
    return {
        "version": VERSION,
        "temporal_path": str(temporal_path),
        "temporal_sha256": sha256_file(temporal_path),
        "reader_path": str(Path(extract_frames.__code__.co_filename).resolve()),
        "reader_sha256": sha256_file(Path(extract_frames.__code__.co_filename).resolve()),
        "spatial_replay_path": str(Path(__file__).resolve()),
        "spatial_replay_sha256": sha256_file(Path(__file__).resolve()),
        "model_path": str(model_path),
        "model_tree_sha256": sha256_tree(model_path),
        "inference_v2": inference_contract,
        "fixed_parameters": {
            "max_pixels": MAX_PIXELS,
            "max_video_frames": MAX_VIDEO_FRAMES,
            "detect_fps": DETECT_FPS,
            "crop_stride": CROP_STRIDE,
            "crop_tokens": CROP_TOKENS,
            "device_map": "auto",
            "attn_implementation": "sdpa",
        },
    }


def replay(args: argparse.Namespace) -> int:
    model_path = Path(args.model).resolve(strict=True)
    if model_path != FIXED_MODEL:
        raise ValueError(f"model must remain fixed at {FIXED_MODEL}")
    index_path = Path(args.index).resolve(strict=True)
    temporal_path = Path(args.temporal).resolve(strict=True)
    output_path = Path(args.out).resolve()
    status_path = Path(args.status_out).resolve()
    raw_path = Path(args.raw_out).resolve()
    if len({output_path, status_path, raw_path}) != 3:
        raise ValueError("out, status-out, and raw-out must be distinct")
    if any(path.exists() for path in (output_path, status_path, raw_path)):
        raise ValueError("replay outputs must not already exist")

    items = baseline_v2.load_index(str(index_path), allow_missing_target=False)
    temporal_rows = load_jsonl(temporal_path)
    if not items or len(items) != len(temporal_rows):
        raise ValueError("index and temporal inputs must have the same non-zero row count")
    temporal_by_id: Dict[str, Dict[str, Any]] = {}
    for raw in temporal_rows:
        row = validate_temporal_row(raw)
        video_id = str(row["video_id"])
        if video_id in temporal_by_id:
            raise ValueError(f"duplicate temporal video_id: {video_id}")
        temporal_by_id[video_id] = row
    index_ids = [str(item["video_id"]) for item in items]
    if set(index_ids) != set(temporal_by_id):
        missing = sorted(set(index_ids) - set(temporal_by_id))
        extra = sorted(set(temporal_by_id) - set(index_ids))
        raise ValueError(f"temporal coverage mismatch: missing={missing[:10]}, extra={extra[:10]}")

    contract = _recovery_contract(temporal_path, model_path)
    manifest_path = status_path.with_suffix(status_path.suffix + ".recovery.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        **contract,
        "index_path": str(index_path),
        "index_sha256": sha256_file(index_path),
        "expected_videos": len(items),
        "out": str(output_path),
        "status_out": str(status_path),
        "raw_out": str(raw_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    model = baseline_v2.TemporalModel(_model_args(model_path))
    legacy = model.legacy
    legacy.extract_frames = extract_frames
    for path in (output_path, status_path, raw_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("x", encoding="utf-8") as output_stream, \
            status_path.open("x", encoding="utf-8") as status_stream, \
            raw_path.open("x", encoding="utf-8") as raw_stream:
        for position, item in enumerate(items, 1):
            video_id = str(item["video_id"])
            temporal = temporal_by_id[video_id]
            started = time.monotonic()
            stage2_sec = 0.0
            source_stage1 = float(temporal["timing"]["stage1_sec"])
            source_peak_mib = float(temporal["VRAM"]["peak_mib"])
            peak_mib = source_peak_mib
            status, reason = temporal["status"], ""
            fallback_count = 0
            failed_count = 0
            predictions: List[Dict[str, Any]] = []
            n_frames = 0
            fps = 0.0
            width = 0
            height = 0
            crop_width = 0
            implicit_crop_height = 0.0
            seconds: List[Tuple[float, float]] = []
            frames: List[Tuple[int, int]] = []
            video_path = baseline_v2.resolve_video(item, None)
            try:
                if not video_path or not os.path.isfile(video_path):
                    status, reason, failed_count = "invalid", "video_missing", 1
                else:
                    n_frames, fps, width, height = legacy.video_meta(video_path)
                    if n_frames <= 1 or fps <= 0 or width <= 0 or height <= 0:
                        status, reason, failed_count = "invalid", "video_decode_metadata", 1
                    else:
                        seconds, frames = validate_temporal_for_media(
                            temporal,
                            item=item,
                            n_frames=n_frames,
                            fps=fps,
                            width=width,
                            height=height,
                        )
                        if status == "ok":
                            target = item["targetRatioWH"]
                            crop_width, implicit_crop_height = legacy.compute_crop_size(
                                width, height, target[0], target[1]
                            )
                            for frame_start, frame_end_exclusive in frames:
                                model.reset_peak_memory()
                                segment_started = time.monotonic()
                                key_frames, key_boxes, stats = legacy.crop_keyframes(
                                    model,
                                    video_path,
                                    (frame_start, frame_end_exclusive - 1),
                                    target,
                                    CROP_STRIDE,
                                    width,
                                    height,
                                    crop_width,
                                    implicit_crop_height,
                                    raw_stream,
                                    video_id,
                                    CROP_TOKENS,
                                )
                                stage2_sec += time.monotonic() - segment_started
                                peak_mib = max(peak_mib, model.peak_memory_mib())
                                fallback_count += stats["crop_parse_fallbacks"]
                                failed_count += stats["crop_failures"] + stats["decode_misses"]
                                if any(stats.values()):
                                    status = "invalid"
                                    reason = "spatial_replay_failure"
                                if not key_frames:
                                    status = "invalid"
                                    reason = "crop_no_decodable_keyframes"
                                    failed_count += 1
                                    continue
                                dense = legacy.densify_boxes(
                                    frame_start,
                                    frame_end_exclusive - 1,
                                    key_frames,
                                    key_boxes,
                                )
                                for frame in range(frame_start, frame_end_exclusive):
                                    box = dense.get(frame)
                                    if box is None:
                                        status, reason = "invalid", "crop_dense_frame_missing"
                                        failed_count += 1
                                        continue
                                    if not legacy.validate_box(
                                        box, width, height, target[0], target[1]
                                    ):
                                        status, reason = "invalid", "geometry_validation"
                                        failed_count += 1
                                        continue
                                    predictions.append({
                                        "frame": int(frame),
                                        "bboxes": [int(box[0]), int(box[1]), int(box[2])],
                                    })
            except Exception as exc:
                status, reason = "invalid", "unhandled_exception"
                failed_count += 1
                write_line(raw_stream, {
                    "video_id": video_id,
                    "stage": "spatial_replay_error",
                    "error": repr(exc),
                })

            replay_wall = time.monotonic() - started
            metadata = {
                **temporal["metadata"],
                "crop_width": crop_width,
                "implicit_crop_height": implicit_crop_height,
            }
            target = item["targetRatioWH"]
            official = {
                "video_id": video_id,
                "targetRatioWH": [int(round(target[0])), int(round(target[1]))],
                "predictions": predictions,
            }
            status_record = {
                "video_id": video_id,
                "source_group": temporal["source_group"],
                "segments_sec": temporal["segments_sec"],
                "segments_frames": temporal["segments_frames"],
                "status": status,
                "reason": reason,
                "timing": {
                    "total_sec": source_stage1 + replay_wall,
                    "stage1_sec": source_stage1,
                    "stage2_sec": stage2_sec,
                },
                "VRAM": {"peak_mib": peak_mib},
                "sampling": temporal["sampling"],
                "policy": temporal["policy"],
                "query": temporal["query"],
                "adapter": temporal["adapter"],
                "constrained_json": temporal["constrained_json"],
                "constraint_backend": temporal["constraint_backend"],
                "metadata": metadata,
                "n_predictions": len(predictions),
                "fallback_count": fallback_count,
                "failed_count": failed_count,
                "raw_out": str(raw_path),
                "recovery": {
                    "version": VERSION,
                    "manifest": str(manifest_path),
                    "temporal_sha256": contract["temporal_sha256"],
                    "reader_sha256": contract["reader_sha256"],
                    "spatial_replay_sha256": contract["spatial_replay_sha256"],
                    "model_tree_sha256": contract["model_tree_sha256"],
                    "replay_wall_sec": replay_wall,
                },
            }
            write_line(output_stream, official)
            write_line(status_stream, status_record)
            raw_stream.flush()
            os.fsync(raw_stream.fileno())
            print(
                f"[{position}/{len(items)}] {video_id} status={status} "
                f"predictions={len(predictions)}",
                flush=True,
            )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay frozen multi-policy temporal segments through the original spatial stage."
    )
    parser.add_argument("--index", required=True)
    parser.add_argument("--temporal", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--status-out", required=True)
    parser.add_argument("--raw-out", required=True)
    return parser


def main() -> int:
    return replay(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
