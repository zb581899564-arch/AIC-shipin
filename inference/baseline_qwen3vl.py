#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qwen3-VL two-stage AIC highlight baseline.

This is an adaptation of the pinned TempSamp-R1 ``baseline_qwen.py``.  The
original file under ``vendor/TempSamp-R1`` is intentionally left unchanged.

The production defaults are bounded for the single RTX 6000 Ada allocation:
2 FPS, at most 64 video frames, about 100k pixels per video frame, BF16,
greedy decoding, 256 output tokens for highlight localization and 128 output
tokens for each subject query.  Official JSONL output is kept separate from
the server-only raw-answer log and from a status sidecar.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
from PIL import Image


# Qwen3-VL uses a 16px patch and 2x2 spatial merge, hence a 32px visual
# factor.  128 visual tokens are 131,072 pixels, which is the model's minimum
# video-frame budget and is still the requested approximately 100k pixels.
DEFAULT_MAX_PIXELS = 128 * 32 * 32
DEFAULT_DETECT_FPS = 2.0
DEFAULT_MAX_VIDEO_FRAMES = 64
DEFAULT_CROP_STRIDE = 15
DEFAULT_DETECT_TOKENS = 256
DEFAULT_CROP_TOKENS = 128


_NUM = re.compile(r"-?\d+\.?\d*")


def load_index(index_path: str) -> List[Dict[str, Any]]:
    """Load an index list and validate the fields used by inference."""
    with open(index_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    if isinstance(items, dict) and isinstance(items.get("records"), list):
        items = items["records"]
    if not isinstance(items, list):
        raise ValueError(f"index must be a JSON list: {index_path}")
    out: List[Dict[str, Any]] = []
    seen = set()
    for it in items:
        if not isinstance(it, dict) or "video_id" not in it:
            raise ValueError(f"invalid index item: {it!r}")
        vid = str(it["video_id"])
        if vid in seen:
            raise ValueError(f"duplicate video_id in index: {vid}")
        seen.add(vid)
        tr = it.get("targetRatioWH", [16, 9])
        if not isinstance(tr, (list, tuple)) or len(tr) < 2:
            raise ValueError(f"invalid targetRatioWH for {vid}: {tr!r}")
        tw, th = float(tr[0]), float(tr[1])
        if not math.isfinite(tw) or not math.isfinite(th) or tw <= 0 or th <= 0:
            raise ValueError(f"invalid target ratio for {vid}: {tr!r}")
        out.append({
            "video_id": vid,
            "targetRatioWH": [tw, th],
            "video_path": str(it["video_path"]) if it.get("video_path") else None,
        })
    return out


def video_meta(video_path: str) -> Tuple[int, float, int, int]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        return 0, 0.0, 0, 0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return n, fps, width, height


def extract_frames(video_path: str, frame_ids: Iterable[int]) -> Dict[int, Any]:
    """Read sorted frame ids sequentially to avoid repeated random seeks."""
    ids = sorted(set(int(f) for f in frame_ids))
    if not ids:
        return {}
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        return {}
    out: Dict[int, Any] = {}
    cap.set(cv2.CAP_PROP_POS_FRAMES, ids[0])
    wanted = set(ids)
    idx = ids[0]
    while idx <= ids[-1]:
        ok, frame = cap.read()
        if not ok:
            break
        if idx in wanted:
            out[idx] = frame
        idx += 1
    cap.release()
    return out


def compute_crop_size(W: int, H: int, tw: float, th: float) -> Tuple[int, float]:
    """Return a legal integer width and the evaluator-derived float height.

    The official evaluator derives ``h = w * target_h / target_w`` from the
    submitted triplet.  ``round`` can produce a width whose implicit height
    is larger than the source (e.g. width 169 for a 300px-high 9:16 frame),
    so the free dimension is floored and checked with exact cross-products.
    """
    if W <= 0 or H <= 0 or tw <= 0 or th <= 0:
        return max(1, W), float(max(1, H))
    target = tw / th
    if W / float(H) >= target:
        # Full source height is the largest fit in real-valued geometry, but
        # the submitted width must be an integer whose derived h is <= H.
        cw = min(W, max(1, int(math.floor((H * tw) / th + 1e-12))))
    else:
        # Full source width already fits by this branch.  Keep a final guard
        # for floating-point boundaries and unusual metadata.
        cw = W
    while cw > 1 and cw * th > H * tw:
        cw -= 1
    h_float = cw * th / tw
    if h_float > H + 1e-9:
        raise AssertionError(f"illegal crop geometry W={W} H={H} cw={cw} h={h_float}")
    return max(1, cw), h_float


def center_to_box(cx: float, cy: float, W: int, H: int, cw: int,
                  h_float: float) -> List[int]:
    """Place a crop around a normalized center and clamp to legal integers."""
    px = cx * W - cw / 2.0
    py = cy * H - h_float / 2.0
    max_x = max(0, W - cw)
    # y is integer while h is evaluator-derived float, therefore floor the
    # maximum y instead of rounding it upward at a fractional boundary.
    max_y = max(0, int(math.floor(H - h_float + 1e-9)))
    x = int(round(max(0.0, min(px, float(max_x)))))
    y = int(round(max(0.0, min(py, float(max_y)))))
    if x > max_x:
        x = max_x
    if y > max_y:
        y = max_y
    return [x, y, int(cw)]


def validate_box(box: Sequence[int], W: int, H: int, tw: float, th: float) -> bool:
    if len(box) != 3 or any(not isinstance(v, int) for v in box):
        return False
    x, y, w = box
    if w <= 0 or x < 0 or y < 0 or x + w > W:
        return False
    h = w * th / tw
    return h > 0 and y + h <= H + 1e-7


def parse_focus_norm(text: str, W: Optional[int] = None,
                     H: Optional[int] = None) -> Optional[List[float]]:
    """Parse the last valid center in normalized, 0..1000, or pixel space."""
    candidate: Optional[List[float]] = None
    for match in re.finditer(r"\{[^{}]*\}", text or "", re.S):
        try:
            obj = json.loads(match.group(0))
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        for key in ("center", "subject_center", "focus", "point", "cxcy"):
            value = obj.get(key)
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                try:
                    candidate = [float(value[0]), float(value[1])]
                except (TypeError, ValueError):
                    pass
    if candidate is None:
        nums = _NUM.findall(text or "")
        if len(nums) >= 2:
            candidate = [float(nums[-2]), float(nums[-1])]
    if candidate is None:
        return None
    cx, cy = candidate

    def normalize(value: float, size: Optional[int]) -> float:
        if value <= 1.5:
            norm = value
        elif value <= 1000.0:
            norm = value / 1000.0
        elif size:
            norm = value / float(size)
        else:
            norm = value / 1000.0
        return max(0.0, min(1.0, norm))

    return [normalize(cx, W), normalize(cy, H)]


def parse_segments_sec(text: str) -> List[Tuple[float, float]]:
    """Parse ``{"segments": [[start, end], ...]}`` from model text."""
    for match in re.finditer(r"\{(?:[^{}]|\{[^{}]*\})*\}", text or "", re.S):
        try:
            obj = json.loads(match.group(0))
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        segs = obj.get("segments")
        if isinstance(segs, list):
            out: List[Tuple[float, float]] = []
            for seg in segs:
                if isinstance(seg, (list, tuple)) and len(seg) >= 2:
                    try:
                        out.append((float(seg[0]), float(seg[1])))
                    except (TypeError, ValueError):
                        continue
            if out:
                return out
    tail = (text or "")[max(0, (text or "").find("segments")):]
    pairs = re.findall(r"\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]", tail)
    return [(float(a), float(b)) for a, b in pairs]


def sec_segments_to_frames(segs_sec: Sequence[Tuple[float, float]], fps: float,
                           n_frames: int) -> List[Tuple[int, int]]:
    if fps <= 0 or n_frames <= 0:
        return []
    out = []
    for start, end in segs_sec:
        if not math.isfinite(start) or not math.isfinite(end):
            continue
        f0 = int(round(min(start, end) * fps))
        f1 = int(round(max(start, end) * fps))
        f0 = max(0, min(f0, n_frames - 1))
        f1 = max(0, min(f1, n_frames - 1))
        if f1 > f0:
            out.append((f0, f1))
    return out


def merge_segments(segs_frame: Sequence[Tuple[int, int]], n_frames: int) -> List[Tuple[int, int]]:
    if n_frames <= 0 or not segs_frame:
        return []
    segs = []
    for start, end in segs_frame:
        a, b = sorted((int(start), int(end)))
        segs.append([max(0, min(a, n_frames - 1)), max(0, min(b, n_frames - 1))])
    segs.sort()
    merged = [segs[0]]
    for start, end in segs[1:]:
        if start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged if b > a]


def densify_boxes(seg_start: int, seg_end: int, key_frames: Sequence[int],
                  key_boxes: Sequence[Sequence[int]]) -> Dict[int, List[int]]:
    if not key_frames:
        return {}
    points = sorted(zip(key_frames, key_boxes), key=lambda p: p[0])
    frames = [int(p[0]) for p in points]
    boxes = [list(map(int, p[1])) for p in points]
    out: Dict[int, List[int]] = {}
    for frame in range(seg_start, seg_end + 1):
        if frame <= frames[0]:
            out[frame] = boxes[0]
        elif frame >= frames[-1]:
            out[frame] = boxes[-1]
        else:
            j = 0
            while j + 1 < len(frames) and frames[j + 1] < frame:
                j += 1
            f0, f1 = frames[j], frames[j + 1]
            t = (frame - f0) / float(f1 - f0) if f1 > f0 else 0.0
            out[frame] = [int(round(boxes[j][i] + (boxes[j + 1][i] - boxes[j][i]) * t))
                          for i in range(3)]
    return out


class Qwen3VL:
    """Small wrapper that keeps Qwen3-VL video kwargs explicit."""

    def __init__(self, model_path: str, max_pixels: int = DEFAULT_MAX_PIXELS,
                 max_video_frames: int = DEFAULT_MAX_VIDEO_FRAMES,
                 device_map: str = "auto", attn_implementation: str = "sdpa"):
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for the allocated inference run")
        self.torch = torch
        self.max_pixels = int(max_pixels)
        self.max_video_frames = int(max_video_frames)
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map=device_map,
            low_cpu_mem_usage=True,
            attn_implementation=attn_implementation,
        )
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(
            model_path,
            min_pixels=self.max_pixels,
            max_pixels=self.max_pixels,
        )
        self.device = next(self.model.parameters()).device
        self.last_video_sampling: List[Dict[str, Any]] = []

    def _generate(self, messages: List[Dict[str, Any]], max_new_tokens: int) -> str:
        try:
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
                enable_thinking=False,
            )
        except (TypeError, ValueError):
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
            )
        from qwen_vl_utils import process_vision_info

        # Qwen3-VL inserts per-frame timestamps in its chat template.  Keep
        # the original-frame indices and source FPS returned by qwen-vl-utils
        # so a max-64-frame sample of a 150-second clip is still labelled on
        # the original timeline rather than being interpreted as a 2.6-second
        # pre-sampled video.
        image_inputs, video_inputs, video_kwargs = process_vision_info(
            messages, return_video_kwargs=True, return_video_metadata=True,
            image_patch_size=16,
        )
        # qwen-vl-utils returns (tensor, metadata) for Qwen3-VL when metadata
        # is requested.  The processor needs these as separate arguments.  In
        # particular, frames_indices + source fps preserve timestamps when a
        # long clip is reduced to <=64 model frames.
        plain_videos = []
        metadata_list = []
        self.last_video_sampling = []
        for video_item in video_inputs or []:
            if isinstance(video_item, tuple) and len(video_item) == 2:
                video, metadata = video_item
            else:
                video, metadata = video_item, None
            plain_videos.append(video)
            if isinstance(metadata, dict):
                metadata_list.append(metadata)
                indices = metadata.get("frames_indices") or []
                source_fps = float(metadata.get("fps") or 0.0)
                total_frames = int(metadata.get("total_num_frames") or 0)
                first_frame = int(indices[0]) if indices else None
                last_frame = int(indices[-1]) if indices else None
                self.last_video_sampling.append({
                    "sampled_frames": len(indices),
                    "source_fps": source_fps,
                    "source_total_frames": total_frames,
                    "first_source_frame": first_frame,
                    "last_source_frame": last_frame,
                    "first_timestamp_sec": (first_frame / source_fps)
                    if first_frame is not None and source_fps > 0 else None,
                    "last_timestamp_sec": (last_frame / source_fps)
                    if last_frame is not None and source_fps > 0 else None,
                    "duration_sec": (total_frames / source_fps)
                    if source_fps > 0 else None,
                    "video_backend": metadata.get("video_backend"),
                })
        if metadata_list:
            video_kwargs = dict(video_kwargs)
            video_kwargs["video_metadata"] = metadata_list
            video_kwargs["do_sample_frames"] = False
        inputs = self.processor(
            text=[text], images=image_inputs, videos=plain_videos or None,
            padding=True, return_tensors="pt", **video_kwargs,
        )
        inputs = inputs.to(self.device)
        with self.torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=int(max_new_tokens),
                do_sample=False,
                num_beams=1,
                use_cache=True,
            )
        trimmed = generated[:, inputs.input_ids.shape[1]:]
        return self.processor.batch_decode(
            trimmed, skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

    def detect_highlights(self, video_path: str, fps_sample: float,
                          max_new_tokens: int) -> str:
        prompt = (
            "This is a short video. Find the single most highlight-worthy clip "
            "that is worth keeping and re-framing, and give its time interval "
            "in seconds counted from the start of the video.\n"
            "Output ONLY JSON, no extra text, strictly: "
            "{\"segments\": [[start_sec, end_sec]]}"
        )
        messages = [{"role": "user", "content": [
            {"type": "video", "video": video_path, "fps": float(fps_sample),
             "min_frames": 4, "max_frames": self.max_video_frames,
             "max_pixels": self.max_pixels},
            {"type": "text", "text": prompt},
        ]}]
        return self._generate(messages, max_new_tokens)

    def predict_focus(self, pil_img: Image.Image, target_ratio: Sequence[float],
                      max_new_tokens: int) -> str:
        tw, th = target_ratio
        prompt = (
            "Below is a video frame to be re-framed (cropped) to %d:%d.\n"
            "Point out the center of the most important subject or region to "
            "keep. Use normalized integer coordinates in range 0~1000: x is "
            "horizontal (0=left, 1000=right), y is vertical (0=top, "
            "1000=bottom).\n"
            "Output ONLY JSON (no other text): {\"center\": [x, y]}"
            % (int(tw), int(th))
        )
        messages = [{"role": "user", "content": [
            {"type": "image", "image": pil_img, "max_pixels": self.max_pixels},
            {"type": "text", "text": prompt},
        ]}]
        return self._generate(messages, max_new_tokens)

    def reset_peak_memory(self) -> None:
        if self.torch.cuda.is_available():
            self.torch.cuda.reset_peak_memory_stats()

    def peak_memory_mib(self) -> float:
        if not self.torch.cuda.is_available():
            return 0.0
        self.torch.cuda.synchronize()
        return float(self.torch.cuda.max_memory_allocated() / (1024 ** 2))


def crop_keyframes(model: Qwen3VL, video_path: str, seg: Tuple[int, int],
                   target: Sequence[float], stride: int, W: int, H: int,
                   cw: int, h_float: float, raw_log: Any, vid: str,
                   max_new_tokens: int) -> Tuple[List[int], List[List[int]], Dict[str, int]]:
    start, end = seg
    key_frames = list(range(start, end + 1, max(1, int(stride))))
    if key_frames[-1] != end:
        key_frames.append(end)
    frame_map = extract_frames(video_path, key_frames)
    valid_frames: List[int] = []
    valid_boxes: List[List[int]] = []
    stats = {"crop_parse_fallbacks": 0, "crop_failures": 0, "decode_misses": 0}
    for frame in key_frames:
        image = frame_map.get(frame)
        if image is None:
            stats["decode_misses"] += 1
            continue
        pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        try:
            raw = model.predict_focus(pil, target, max_new_tokens=max_new_tokens)
            raw_log.write(json.dumps({"video_id": vid, "frame": frame,
                                      "stage": "crop", "raw": raw},
                                     ensure_ascii=False) + "\n")
            center = parse_focus_norm(raw, W, H)
            if center is None:
                stats["crop_parse_fallbacks"] += 1
                box = center_to_box(0.5, 0.5, W, H, cw, h_float)
            else:
                box = center_to_box(center[0], center[1], W, H, cw, h_float)
        except Exception as exc:
            stats["crop_failures"] += 1
            raw_log.write(json.dumps({"video_id": vid, "frame": frame,
                                      "stage": "crop_error", "error": repr(exc)},
                                     ensure_ascii=False) + "\n")
            box = center_to_box(0.5, 0.5, W, H, cw, h_float)
        valid_frames.append(frame)
        valid_boxes.append(box)
    return valid_frames, valid_boxes, stats


def load_completed(path: str) -> set[str]:
    done: set[str] = set()
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and obj.get("video_id") is not None:
                    done.add(str(obj["video_id"]))
            except json.JSONDecodeError:
                continue
    return done


def write_line(f: Any, obj: Dict[str, Any]) -> None:
    f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    f.flush()
    os.fsync(f.fileno())


def resolve_video(item: Dict[str, Any], video_dir: Optional[str]) -> str:
    if item.get("video_path"):
        return str(item["video_path"])
    if not video_dir:
        return ""
    return os.path.join(video_dir, str(item["video_id"]) + ".mp4")


def infer(args: argparse.Namespace) -> int:
    index = load_index(args.index)
    if args.num_videos > 0:
        index = index[:args.num_videos]
    if not index:
        raise ValueError("empty inference index")
    if args.max_pixels < 131072:
        raise ValueError("max-pixels must be at least 131072 for Qwen3-VL video processing")
    print(f"To infer: {len(index)} videos", flush=True)

    model = Qwen3VL(
        args.model,
        max_pixels=args.max_pixels,
        max_video_frames=args.max_video_frames,
        device_map=args.device_map,
        attn_implementation=args.attn_implementation,
    )
    output_path = os.path.abspath(args.out)
    raw_path = os.path.abspath(args.raw_out or (args.out + ".raw.jsonl"))
    status_path = os.path.abspath(args.status_out or (args.out + ".status.jsonl"))
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(raw_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(status_path) or ".", exist_ok=True)
    completed = load_completed(output_path)
    processed = 0
    predictions_total = 0
    with open(output_path, "a", encoding="utf-8") as fout, \
            open(raw_path, "a", encoding="utf-8") as raw_log, \
            open(status_path, "a", encoding="utf-8") as status_log:
        for position, item in enumerate(index, 1):
            vid = str(item["video_id"])
            if vid in completed:
                print(f"  [{position}/{len(index)}] {vid} already complete", flush=True)
                continue
            target = item["targetRatioWH"]
            video_path = resolve_video(item, args.video_dir)
            started = time.monotonic()
            status = "ok"
            reason = ""
            stage1_seconds = 0.0
            stage2_seconds = 0.0
            peak_mib = 0.0
            fallback_count = 0
            failed_count = 0
            predictions: List[Dict[str, Any]] = []
            segments: List[Tuple[int, int]] = []
            sampling: List[Dict[str, Any]] = []
            metadata = {"n_frames": 0, "fps": 0.0, "width": 0, "height": 0,
                        "crop_width": 0, "implicit_crop_height": 0.0}
            try:
                if not video_path or not os.path.isfile(video_path):
                    status, reason = "failed", "video_missing"
                    failed_count += 1
                else:
                    n_frames, fps, W, H = video_meta(video_path)
                    metadata.update({"n_frames": n_frames, "fps": fps,
                                     "width": W, "height": H})
                    if n_frames <= 1 or fps <= 0 or W <= 0 or H <= 0:
                        status, reason = "failed", "video_decode_metadata"
                        failed_count += 1
                    else:
                        cw, h_float = compute_crop_size(W, H, target[0], target[1])
                        metadata.update({"crop_width": cw,
                                         "implicit_crop_height": h_float})
                        model.reset_peak_memory()
                        t1 = time.monotonic()
                        try:
                            raw = model.detect_highlights(
                                video_path, args.detect_fps, args.detect_tokens)
                            sampling = list(model.last_video_sampling)
                            write_line(raw_log, {"video_id": vid, "stage": "detect", "raw": raw,
                                                 "sampling": model.last_video_sampling})
                            segs_sec = parse_segments_sec(raw)
                            segments = merge_segments(
                                sec_segments_to_frames(segs_sec, fps, n_frames), n_frames)
                        except Exception as exc:
                            write_line(raw_log, {"video_id": vid, "stage": "detect_error",
                                                 "error": repr(exc)})
                            status, reason = "failed", "highlight_generation"
                            failed_count += 1
                        stage1_seconds = time.monotonic() - t1
                        peak_mib = max(peak_mib, model.peak_memory_mib())
                        if status != "failed" and not segments:
                            status, reason = "fallback", "highlight_parse_empty"
                            fallback_count += 1
                        elif status != "failed":
                            for seg in segments:
                                model.reset_peak_memory()
                                t2 = time.monotonic()
                                kfs, kbs, cstats = crop_keyframes(
                                    model, video_path, seg, target, args.crop_stride,
                                    W, H, cw, h_float, raw_log, vid, args.crop_tokens)
                                stage2_seconds += time.monotonic() - t2
                                peak_mib = max(peak_mib, model.peak_memory_mib())
                                fallback_count += cstats["crop_parse_fallbacks"]
                                failed_count += cstats["crop_failures"] + cstats["decode_misses"]
                                if cstats["crop_parse_fallbacks"]:
                                    status = "fallback"
                                    reason = reason or "crop_parse_fallback"
                                if cstats["crop_failures"] or cstats["decode_misses"]:
                                    status, reason = "failed", "crop_frame_failure"
                                if not kfs:
                                    status, reason = "failed", "crop_no_decodable_keyframes"
                                    continue
                                dense = densify_boxes(seg[0], seg[1], kfs, kbs)
                                for frame in range(seg[0], seg[1] + 1):
                                    box = dense.get(frame)
                                    if box is None:
                                        continue
                                    if not validate_box(box, W, H, target[0], target[1]):
                                        status, reason = "failed", "geometry_validation"
                                        failed_count += 1
                                        continue
                                    predictions.append({"frame": int(frame),
                                                        "bboxes": [int(box[0]), int(box[1]), int(box[2])]})
            except Exception as exc:
                status, reason = "failed", "video_unhandled_exception"
                failed_count += 1
                write_line(raw_log, {"video_id": vid, "stage": "video_error",
                                     "error": repr(exc)})
            official = {"video_id": vid,
                        "targetRatioWH": [int(round(target[0])), int(round(target[1]))],
                        "predictions": predictions}
            write_line(fout, official)
            elapsed = time.monotonic() - started
            write_line(status_log, {
                "video_id": vid, "status": status, "reason": reason,
                "segments": [[int(a), int(b)] for a, b in segments],
                "sampling": sampling,
                "n_predictions": len(predictions),
                "fallback_count": fallback_count, "failed_count": failed_count,
                "elapsed_sec": elapsed, "stage1_sec": stage1_seconds,
                "stage2_sec": stage2_seconds, "peak_vram_mib": peak_mib,
                "metadata": metadata, "raw_log": raw_path,
            })
            completed.add(vid)
            processed += 1
            predictions_total += len(predictions)
            print(f"  [{position}/{len(index)}] {vid} status={status} "
                  f"pred={len(predictions)} elapsed={elapsed:.1f}s "
                  f"peak={peak_mib:.0f}MiB", flush=True)
    print(f"Done: processed={processed} predictions={predictions_total} output={output_path}", flush=True)
    print(f"Raw answers (server only): {raw_path}", flush=True)
    print(f"Status sidecar: {status_path}", flush=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--video-dir", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw-out", default=None)
    ap.add_argument("--status-out", default=None)
    ap.add_argument("--num-videos", type=int, default=0)
    ap.add_argument("--crop-stride", type=int, default=DEFAULT_CROP_STRIDE)
    ap.add_argument("--detect-fps", type=float, default=DEFAULT_DETECT_FPS)
    ap.add_argument("--max-video-frames", type=int, default=DEFAULT_MAX_VIDEO_FRAMES)
    ap.add_argument("--max-pixels", type=int, default=DEFAULT_MAX_PIXELS)
    ap.add_argument("--detect-tokens", type=int, default=DEFAULT_DETECT_TOKENS)
    ap.add_argument("--crop-tokens", type=int, default=DEFAULT_CROP_TOKENS)
    ap.add_argument("--device-map", default="auto")
    ap.add_argument("--attn-implementation", default="sdpa", choices=["sdpa", "eager"])
    return ap


if __name__ == "__main__":
    parser = build_parser()
    sys.exit(infer(parser.parse_args()))
