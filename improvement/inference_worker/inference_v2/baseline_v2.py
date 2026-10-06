#!/usr/bin/env python3
"""Independent AIC Qwen3-VL temporal-policy inference entry point."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inference_v2.qwen_io import infer_temporal_policy
from inference_v2.temporal import canonicalize_segments, prompt_hashes, temporal_json_regex


DEFAULT_MODEL = "/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct"
DEFAULT_MAX_PIXELS = 128 * 32 * 32
DEFAULT_MAX_VIDEO_FRAMES = 64
DEFAULT_DETECT_FPS = 2.0
DEFAULT_CROP_STRIDE = 15
DEFAULT_DETECT_TOKENS = 256
DEFAULT_CROP_TOKENS = 128


def _legacy_path() -> Path:
    return Path(__file__).resolve().parent.parent / "inference" / "baseline_qwen3vl.py"


def load_legacy() -> Any:
    """Load the frozen baseline helpers without modifying its source."""
    path = _legacy_path()
    spec = importlib.util.spec_from_file_location("aic_frozen_baseline_qwen3vl", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import frozen baseline: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def contract() -> Dict[str, Any]:
    root = Path(__file__).resolve().parent
    sources = [root / "baseline_v2.py", root / "qwen_io.py", root / "temporal.py"]
    legacy = _legacy_path()
    return {
        "interval_convention": {
            "seconds": "half-open [start_sec,end_sec)",
            "frames": "original-media [start_frame,end_frame_exclusive)",
        },
        "prompt_sha256": prompt_hashes(),
        "constraint_regex_sha256": {
            policy: hashlib.sha256(temporal_json_regex(policy).encode("utf-8")).hexdigest()
            for policy in ("single", "multi", "windowed")
        },
        "source_sha256": {str(path): _sha256(path) for path in sources if path.exists()},
        "frozen_baseline": {"path": str(legacy), "sha256": _sha256(legacy)},
    }


def infer_source_group(item: Dict[str, Any], video_id: str) -> str:
    if item.get("source_group") is not None:
        return str(item["source_group"])
    provenance = item.get("provenance")
    if isinstance(provenance, dict) and provenance.get("source_group") is not None:
        return str(provenance["source_group"])
    clip = item.get("clip")
    if isinstance(clip, dict) and clip.get("source_vid") is not None:
        source_vid = str(clip["source_vid"])
        parts = source_vid.rsplit("_", 2)
        return parts[0] if len(parts) == 3 else source_vid
    candidate = video_id[len("train_"):] if video_id.startswith("train_") else video_id
    parts = candidate.rsplit("_", 2)
    return parts[0] if len(parts) == 3 else candidate


def load_index(
    index_path: str, *, allow_missing_target: bool = False
) -> List[Dict[str, Any]]:
    """Load inference rows while preserving query and source identity."""
    with open(index_path, "r", encoding="utf-8") as stream:
        text = stream.read()
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        items = []
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL at {index_path}:{line_no}: {exc.msg}"
                ) from exc
    if isinstance(items, dict) and isinstance(items.get("records"), list):
        items = items["records"]
    if not isinstance(items, list):
        raise ValueError(f"index must be a JSON list: {index_path}")
    out: List[Dict[str, Any]] = []
    seen = set()
    for raw in items:
        if not isinstance(raw, dict) or raw.get("video_id") is None:
            raise ValueError(f"invalid index item: {raw!r}")
        video_id = str(raw["video_id"])
        if video_id in seen:
            raise ValueError(f"duplicate video_id in index: {video_id}")
        seen.add(video_id)
        target = raw.get("targetRatioWH")
        if target is None:
            if not allow_missing_target:
                raise ValueError(f"missing targetRatioWH for {video_id}")
            # Temporal-only validation never consumes crop geometry.
            target = [16, 9]
        if not isinstance(target, (list, tuple)) or len(target) < 2:
            raise ValueError(f"invalid targetRatioWH for {video_id}: {target!r}")
        tw, th = float(target[0]), float(target[1])
        if not math.isfinite(tw) or not math.isfinite(th) or tw <= 0 or th <= 0:
            raise ValueError(f"invalid targetRatioWH for {video_id}: {target!r}")
        query = raw.get("query")
        if query is not None and not isinstance(query, str):
            raise ValueError(f"query must be a string for {video_id}")
        out.append({
            "video_id": video_id,
            "source_group": infer_source_group(raw, video_id),
            "targetRatioWH": [tw, th],
            "video_path": str(raw["video_path"]) if raw.get("video_path") else None,
            "query": query,
        })
    return out


def resolve_video(item: Dict[str, Any], video_dir: Optional[str]) -> str:
    if item.get("video_path"):
        return str(item["video_path"])
    if not video_dir:
        return ""
    return os.path.join(video_dir, str(item["video_id"]) + ".mp4")


class TemporalModel:
    """Frozen base model with an optional temporal-only PEFT adapter."""

    def __init__(self, args: argparse.Namespace):
        legacy = load_legacy()
        self.legacy = legacy
        self.backend = legacy.Qwen3VL(
            args.model,
            max_pixels=args.max_pixels,
            max_video_frames=args.max_video_frames,
            device_map=args.device_map,
            attn_implementation=args.attn_implementation,
        )
        self.adapter_path: Optional[str] = None
        if args.temporal_adapter:
            try:
                from peft import PeftModel
            except ImportError as exc:
                raise RuntimeError(
                    "--temporal-adapter requires PEFT in the project environment; "
                    "install it in /home/inspur/aic_video_work/env/qwen3vl"
                ) from exc
            self.backend.model = PeftModel.from_pretrained(
                self.backend.model,
                args.temporal_adapter,
                is_trainable=False,
            )
            self.backend.model.eval()
            self.adapter_path = os.path.abspath(args.temporal_adapter)
        for parameter in self.backend.model.parameters():
            parameter.requires_grad_(False)

    @property
    def model(self) -> Any:
        return self.backend.model

    @property
    def processor(self) -> Any:
        return self.backend.processor

    def reset_peak_memory(self) -> None:
        self.backend.reset_peak_memory()

    def peak_memory_mib(self) -> float:
        return self.backend.peak_memory_mib()

    @contextlib.contextmanager
    def base_only(self):
        """Disable the temporal adapter for stage 2."""
        if self.adapter_path:
            disable = getattr(self.backend.model, "disable_adapter", None)
            if disable is None:
                raise RuntimeError("loaded PEFT model cannot disable adapter for stage 2")
            with disable():
                yield
        else:
            yield

    def predict_focus(
        self, image: Any, target: Sequence[float], max_new_tokens: int
    ) -> str:
        with self.base_only():
            return self.backend.predict_focus(image, target, max_new_tokens)


def write_line(stream: Any, obj: Dict[str, Any]) -> None:
    stream.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def load_completed(path: str) -> set[str]:
    done: set[str] = set()
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as stream:
        for line in stream:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("video_id") is not None:
                done.add(str(obj["video_id"]))
    return done


def _paths(args: argparse.Namespace) -> Tuple[str, str, Optional[str]]:
    if args.temporal_only:
        output = args.temporal_out or args.out or "temporal_predictions.jsonl"
        raw = args.raw_out or output + ".raw.jsonl"
        return os.path.abspath(output), os.path.abspath(raw), None
    output = args.out or "predictions.jsonl"
    raw = args.raw_out or output + ".raw.jsonl"
    status = args.status_out or output + ".status.jsonl"
    return os.path.abspath(output), os.path.abspath(raw), os.path.abspath(status)


def infer(args: argparse.Namespace) -> int:
    items = load_index(args.index, allow_missing_target=args.temporal_only)
    if args.num_videos > 0:
        items = items[:args.num_videos]
    if not items:
        raise ValueError("empty inference index")
    if args.max_pixels < DEFAULT_MAX_PIXELS:
        raise ValueError(f"max-pixels must be at least {DEFAULT_MAX_PIXELS}")
    output_path, raw_path, status_path = _paths(args)
    for path in [output_path, raw_path, status_path]:
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    completed = load_completed(output_path)
    print(f"To infer: {len(items)} videos; policy={args.temporal_policy}", flush=True)
    model = TemporalModel(args)
    legacy = model.legacy

    output_stream = open(output_path, "a", encoding="utf-8")
    raw_stream = open(raw_path, "a", encoding="utf-8")
    status_stream = (
        open(status_path, "a", encoding="utf-8") if status_path else None
    )
    try:
        for position, item in enumerate(items, 1):
            video_id = str(item["video_id"])
            if video_id in completed:
                print(f"  [{position}/{len(items)}] {video_id} already complete", flush=True)
                continue
            started = time.monotonic()
            video_path = resolve_video(item, args.video_dir)
            query = item.get("query") if args.query_aware else None
            status, reason = "ok", ""
            seconds: List[Tuple[float, float]] = []
            frames: List[Tuple[int, int]] = []
            sampling: List[Dict[str, Any]] = []
            predictions: List[Dict[str, Any]] = []
            stage1_sec = 0.0
            stage2_sec = 0.0
            peak_mib = 0.0
            fallback_count = 0
            failed_count = 0
            n_frames = 0
            fps = 0.0
            width = 0
            height = 0
            crop_width = 0
            implicit_crop_height = 0.0
            try:
                if not video_path or not os.path.isfile(video_path):
                    status, reason = "invalid", "video_missing"
                elif args.query_aware and not (query or "").strip():
                    status, reason = "invalid", "query_missing"
                else:
                    n_frames, fps, width, height = legacy.video_meta(video_path)
                    if n_frames <= 1 or fps <= 0 or width <= 0 or height <= 0:
                        status, reason = "invalid", "video_decode_metadata"
                    else:
                        duration_sec = n_frames / fps
                        model.reset_peak_memory()
                        t1 = time.monotonic()
                        temporal = infer_temporal_policy(
                            model.model,
                            model.processor,
                            video_path,
                            policy=args.temporal_policy,
                            query=query,
                            duration_sec=duration_sec,
                            fps_sample=args.detect_fps,
                            max_frames=args.max_video_frames,
                            max_pixels=args.max_pixels,
                            window_sec=args.window_sec,
                            step_sec=args.window_step_sec,
                            max_new_tokens=args.detect_tokens,
                            constrained_json=args.constrained_json,
                        )
                        stage1_sec = time.monotonic() - t1
                        peak_mib = model.peak_memory_mib()
                        sampling = temporal.sampling
                        for raw in temporal.raw_outputs:
                            write_line(raw_stream, {
                                "video_id": video_id,
                                "stage": "detect",
                                "policy": args.temporal_policy,
                                **raw,
                            })
                        if temporal.status == "invalid":
                            status, reason = "invalid", temporal.reason
                        else:
                            seconds, frames = canonicalize_segments(
                                temporal.segments_sec, fps, n_frames, duration_sec
                            )
                            status = "ok" if frames else "valid_empty"

                        if not args.temporal_only and status == "ok":
                            target = item["targetRatioWH"]
                            crop_width, implicit_crop_height = legacy.compute_crop_size(
                                width, height, target[0], target[1]
                            )
                            for frame_start, frame_end_exclusive in frames:
                                model.reset_peak_memory()
                                t2 = time.monotonic()
                                key_frames, key_boxes, stats = legacy.crop_keyframes(
                                    model,
                                    video_path,
                                    (frame_start, frame_end_exclusive - 1),
                                    target,
                                    args.crop_stride,
                                    width,
                                    height,
                                    crop_width,
                                    implicit_crop_height,
                                    raw_stream,
                                    video_id,
                                    args.crop_tokens,
                                )
                                stage2_sec += time.monotonic() - t2
                                peak_mib = max(peak_mib, model.peak_memory_mib())
                                fallback_count += stats["crop_parse_fallbacks"]
                                failed_count += stats["crop_failures"] + stats["decode_misses"]
                                if stats["crop_failures"] or stats["decode_misses"]:
                                    status, reason = "invalid", "crop_frame_failure"
                                elif stats["crop_parse_fallbacks"] and status == "ok":
                                    reason = reason or "crop_parse_fallback"
                                if not key_frames:
                                    status, reason = "invalid", "crop_no_decodable_keyframes"
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
                write_line(raw_stream, {
                    "video_id": video_id,
                    "stage": "error",
                    "error": repr(exc),
                })

            elapsed = time.monotonic() - started
            metadata = {
                "n_frames": n_frames,
                "fps": fps,
                "width": width,
                "height": height,
                "crop_width": crop_width,
                "implicit_crop_height": implicit_crop_height,
            }
            common = {
                "video_id": video_id,
                "source_group": item["source_group"],
                "segments_sec": [[a, b] for a, b in seconds],
                "segments_frames": [[a, b] for a, b in frames],
                "status": status,
                "reason": reason,
                "timing": {
                    "total_sec": elapsed,
                    "stage1_sec": stage1_sec,
                    "stage2_sec": stage2_sec,
                },
                "VRAM": {"peak_mib": peak_mib},
                "sampling": sampling,
                "policy": args.temporal_policy,
                "query": query,
                "adapter": model.adapter_path,
                "constrained_json": args.constrained_json,
                "constraint_backend": "regex" if args.constrained_json else None,
                "metadata": metadata,
            }
            if args.temporal_only:
                write_line(output_stream, common)
            else:
                target = item["targetRatioWH"]
                official = {
                    "video_id": video_id,
                    "targetRatioWH": [int(round(target[0])), int(round(target[1]))],
                    "predictions": predictions,
                }
                write_line(output_stream, official)
                write_line(status_stream, {
                    **common,
                    "n_predictions": len(predictions),
                    "fallback_count": fallback_count,
                    "failed_count": failed_count,
                    "raw_log": raw_path,
                })
            print(
                f"  [{position}/{len(items)}] {video_id}: {status}; "
                f"segments={len(frames)}; {elapsed:.2f}s",
                flush=True,
            )
    finally:
        output_stream.close()
        raw_stream.close()
        if status_stream is not None:
            status_stream.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index")
    parser.add_argument("--video-dir", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default=None)
    parser.add_argument("--temporal-out", default=None)
    parser.add_argument("--raw-out", default=None)
    parser.add_argument("--status-out", default=None)
    parser.add_argument(
        "--temporal-policy", choices=["single", "multi", "windowed"], default="multi"
    )
    parser.add_argument("--query-aware", action="store_true")
    parser.add_argument("--temporal-only", action="store_true")
    parser.add_argument("--temporal-adapter", default=None)
    parser.add_argument("--constrained-json", action="store_true")
    parser.add_argument("--window-sec", type=float, default=30.0)
    parser.add_argument("--window-step-sec", type=float, default=25.0)
    parser.add_argument("--detect-fps", type=float, default=DEFAULT_DETECT_FPS)
    parser.add_argument("--max-video-frames", type=int, default=DEFAULT_MAX_VIDEO_FRAMES)
    parser.add_argument("--max-pixels", type=int, default=DEFAULT_MAX_PIXELS)
    parser.add_argument("--crop-stride", type=int, default=DEFAULT_CROP_STRIDE)
    parser.add_argument("--detect-tokens", type=int, default=DEFAULT_DETECT_TOKENS)
    parser.add_argument("--crop-tokens", type=int, default=DEFAULT_CROP_TOKENS)
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--attn-implementation", choices=["sdpa", "eager"], default="sdpa")
    parser.add_argument("--num-videos", type=int, default=0)
    parser.add_argument("--print-contract", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.print_contract:
        print(json.dumps(contract(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if not args.index:
        raise SystemExit("--index is required unless --print-contract is used")
    return infer(args)


if __name__ == "__main__":
    raise SystemExit(main())
