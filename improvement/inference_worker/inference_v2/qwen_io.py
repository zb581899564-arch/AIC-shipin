"""Shared Qwen3-VL video encoding and temporal-generation API.

The encoding path intentionally mirrors the verified baseline metadata flow.
It does not truncate token sequences; callers receive the complete processor
batch and a cloned copy of the prefix token ids for teacher forcing.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import threading
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .temporal import (
    ParseResult,
    build_temporal_prompt,
    parse_segments_response,
    plan_windows,
    temporal_json_regex,
)


_TOKENIZER_DATA_CACHE: Dict[int, Tuple[Any, Any]] = {}
_TOKENIZER_DATA_LOCK = threading.Lock()


@dataclass
class EncodedQwenBatch:
    inputs: Any
    prefix_input_ids: Any
    rendered_prompt: str
    sampling: List[Dict[str, Any]]


@dataclass
class GenerationResult:
    text: str
    sampling: List[Dict[str, Any]]


@dataclass
class TemporalResult:
    status: str
    segments_sec: List[Tuple[float, float]]
    reason: str
    sampling: List[Dict[str, Any]]
    raw_outputs: List[Dict[str, Any]]


def _cached_tokenizer_data(tokenizer: Any) -> Any:
    """Cache lm-format-enforcer's expensive vocabulary normalization."""
    key = id(tokenizer)
    with _TOKENIZER_DATA_LOCK:
        cached = _TOKENIZER_DATA_CACHE.get(key)
        if cached is not None and cached[0] is tokenizer:
            return cached[1]
        try:
            from lmformatenforcer.integrations.transformers import (
                build_token_enforcer_tokenizer_data,
            )
        except ImportError as exc:
            raise RuntimeError(
                "--constrained-json requires lm-format-enforcer in the project environment"
            ) from exc
        tokenizer_data = build_token_enforcer_tokenizer_data(tokenizer)
        _TOKENIZER_DATA_CACHE[key] = (tokenizer, tokenizer_data)
        return tokenizer_data


def tokenizer_data_cache_size() -> int:
    """Expose cache size for CPU contract tests and observability."""
    with _TOKENIZER_DATA_LOCK:
        return len(_TOKENIZER_DATA_CACHE)


def build_temporal_prefix_allowed_tokens_fn(tokenizer: Any, policy: str) -> Any:
    """Build the official transformers prefix callback for one generation."""
    try:
        from lmformatenforcer import RegexParser
        from lmformatenforcer.integrations.transformers import (
            build_transformers_prefix_allowed_tokens_fn,
        )
    except ImportError as exc:
        raise RuntimeError(
            "--constrained-json requires lm-format-enforcer in the project environment"
        ) from exc
    parser = RegexParser(temporal_json_regex(policy))
    return build_transformers_prefix_allowed_tokens_fn(
        _cached_tokenizer_data(tokenizer), parser
    )


def build_temporal_messages(
    video_path: str,
    prompt: str,
    *,
    fps: float = 2.0,
    max_frames: int = 64,
    max_pixels: int = 131072,
    clip_start_sec: Optional[float] = None,
    clip_end_sec: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Build one video + text request without creating derived media."""
    video: Dict[str, Any] = {
        "type": "video",
        "video": video_path,
        "fps": float(fps),
        "min_frames": 4,
        "max_frames": int(max_frames),
        "max_pixels": int(max_pixels),
    }
    if clip_start_sec is not None:
        video["video_start"] = float(clip_start_sec)
    if clip_end_sec is not None:
        end = float(clip_end_sec)
        # qwen-vl-utils readers treat ``video_end`` as inclusive.  Move by
        # one representable float toward the start so our public window stays
        # half-open and cannot include the first frame of the next window.
        toward = float(clip_start_sec) if clip_start_sec is not None else -math.inf
        video["video_end"] = math.nextafter(end, toward)
    return [{"role": "user", "content": [
        video,
        {"type": "text", "text": prompt},
    ]}]


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value)


def _sampling_record(metadata: Dict[str, Any]) -> Dict[str, Any]:
    indices = _as_list(metadata.get("frames_indices"))
    source_fps = float(metadata.get("fps") or 0.0)
    total_frames = int(metadata.get("total_num_frames") or 0)
    first_frame = int(indices[0]) if indices else None
    last_frame = int(indices[-1]) if indices else None
    return {
        "sampled_frames": len(indices),
        "source_fps": source_fps,
        "source_total_frames": total_frames,
        "first_source_frame": first_frame,
        "last_source_frame": last_frame,
        "first_source_timestamp_sec": (
            first_frame / source_fps
            if first_frame is not None and source_fps > 0 else None
        ),
        "last_source_timestamp_sec": (
            last_frame / source_fps
            if last_frame is not None and source_fps > 0 else None
        ),
        "duration_sec": total_frames / source_fps if source_fps > 0 else None,
        "video_backend": metadata.get("video_backend"),
    }


def _video_elements(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    elements: List[Dict[str, Any]] = []
    for message in messages:
        content = message.get("content", []) if isinstance(message, dict) else []
        if isinstance(content, list):
            elements.extend(
                value for value in content
                if isinstance(value, dict) and value.get("type") == "video"
            )
    return elements


def _processor_metadata(
    metadata: Dict[str, Any], video_element: Dict[str, Any]
) -> Dict[str, Any]:
    """Make clipped-video timestamps reader-local while retaining metadata.

    decord and torchcodec expose original-file frame indices after a ranged
    read, whereas torchvision exposes clip-local indices.  Qwen3-VL derives
    visible timestamps from these indices.  Normalize only the documented
    global-index backends so a local-time window prompt cannot be double
    offset when predictions are mapped back to the global timeline.
    """
    result = dict(metadata)
    clip_start = float(video_element.get("video_start") or 0.0)
    if clip_start <= 0:
        return result
    backend = str(metadata.get("video_backend") or "")
    indices = _as_list(metadata.get("frames_indices"))
    if backend in {"decord", "torchcodec"}:
        source_fps = float(metadata.get("fps") or 0.0)
        if source_fps <= 0:
            raise RuntimeError("video metadata has no valid source FPS")
        origin_frame = int(math.ceil(clip_start * source_fps))
        result["frames_indices"] = [int(value) - origin_frame for value in indices]
    elif backend == "torchvision":
        result["frames_indices"] = indices
    else:
        raise RuntimeError(
            f"cannot establish clipped-video timestamp origin for backend {backend!r}"
        )
    return result


def encode_qwen3vl_messages(
    processor: Any,
    messages: List[Dict[str, Any]],
    *,
    device: Any = None,
    image_patch_size: int = 16,
) -> EncodedQwenBatch:
    """Encode complete Qwen3-VL inputs with original-timeline metadata.

    No ``truncation`` or ``max_length`` is passed.  When qwen-vl-utils
    returns ``(video_tensor, metadata)``, the two values are separated for
    the processor and frame sampling is disabled there, preserving the exact
    sampled source-frame indices and timestamps.
    """
    try:
        rendered = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except (TypeError, ValueError):
        rendered = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    from qwen_vl_utils import process_vision_info

    image_inputs, video_inputs, video_kwargs = process_vision_info(
        messages,
        return_video_kwargs=True,
        return_video_metadata=True,
        image_patch_size=int(image_patch_size),
    )
    plain_videos: List[Any] = []
    metadata_list: List[Dict[str, Any]] = []
    sampling: List[Dict[str, Any]] = []
    video_elements = _video_elements(messages)
    if not video_inputs or len(video_inputs) != len(video_elements):
        raise RuntimeError("video metadata path is incomplete")
    for position, video_item in enumerate(video_inputs):
        if isinstance(video_item, tuple) and len(video_item) == 2:
            video, metadata = video_item
        else:
            video, metadata = video_item, None
        plain_videos.append(video)
        if not isinstance(metadata, dict):
            raise RuntimeError("qwen-vl-utils did not return video metadata")
        processor_metadata = _processor_metadata(metadata, video_elements[position])
        sample = _sampling_record(metadata)
        processor_indices = _as_list(processor_metadata.get("frames_indices"))
        source_fps = float(metadata.get("fps") or 0.0)
        processor_first = int(processor_indices[0]) if processor_indices else None
        processor_last = int(processor_indices[-1]) if processor_indices else None
        sample["processor_first_frame"] = processor_first
        sample["processor_last_frame"] = processor_last
        sample["first_timestamp_sec"] = (
            processor_first / source_fps
            if processor_first is not None and source_fps > 0 else None
        )
        sample["last_timestamp_sec"] = (
            processor_last / source_fps
            if processor_last is not None and source_fps > 0 else None
        )
        sample["clip_start_sec"] = video_elements[position].get("video_start")
        sample["clip_end_sec"] = video_elements[position].get("video_end")
        sample["processor_timestamp_mode"] = "clip_local"
        sampling.append(sample)
        metadata_list.append(processor_metadata)
    video_kwargs = dict(video_kwargs)
    video_kwargs["video_metadata"] = metadata_list
    video_kwargs["do_sample_frames"] = False
    inputs = processor(
        text=[rendered],
        images=image_inputs,
        videos=plain_videos or None,
        padding=True,
        return_tensors="pt",
        **video_kwargs,
    )
    if device is not None:
        inputs = inputs.to(device)
    return EncodedQwenBatch(
        inputs=inputs,
        prefix_input_ids=inputs.input_ids.clone(),
        rendered_prompt=rendered,
        sampling=sampling,
    )


def generate_temporal(
    model: Any,
    processor: Any,
    messages: List[Dict[str, Any]],
    *,
    max_new_tokens: int = 256,
    constrained_json: bool = False,
    temporal_policy: str = "multi",
) -> GenerationResult:
    """Greedily generate from an already loaded model and processor."""
    import torch

    device = next(model.parameters()).device
    encoded = encode_qwen3vl_messages(processor, messages, device=device)
    generation_kwargs: Dict[str, Any] = {}
    if constrained_json:
        tokenizer = getattr(processor, "tokenizer", None)
        if tokenizer is None:
            raise RuntimeError("processor has no tokenizer for constrained JSON generation")
        generation_kwargs["prefix_allowed_tokens_fn"] = (
            build_temporal_prefix_allowed_tokens_fn(tokenizer, temporal_policy)
        )
    with torch.inference_mode():
        generated = model.generate(
            **encoded.inputs,
            max_new_tokens=int(max_new_tokens),
            do_sample=False,
            num_beams=1,
            use_cache=True,
            **generation_kwargs,
        )
    trimmed = generated[:, encoded.inputs.input_ids.shape[1]:]
    text = processor.batch_decode(
        trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]
    return GenerationResult(text=text, sampling=encoded.sampling)


def _merge_seconds(segments: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Merge true temporal overlap from repeated windows; keep adjacency."""
    merged: List[List[float]] = []
    for start, end in sorted(segments):
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        elif end > start:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def infer_temporal_policy(
    model: Any,
    processor: Any,
    video_path: str,
    *,
    policy: str,
    query: Optional[str],
    duration_sec: float,
    fps_sample: float = 2.0,
    max_frames: int = 64,
    max_pixels: int = 131072,
    window_sec: float = 30.0,
    step_sec: float = 25.0,
    max_new_tokens: int = 256,
    constrained_json: bool = False,
) -> TemporalResult:
    """Run one temporal policy using caller-owned model weights.

    For ``windowed``, model outputs are local to each reader window and are
    offset back to the original video timeline before overlap deduplication.
    """
    if policy not in {"single", "multi", "windowed"}:
        raise ValueError(f"unknown temporal policy: {policy}")
    windows = (
        plan_windows(duration_sec, window_sec, step_sec)
        if policy == "windowed" else [(0.0, duration_sec)]
    )
    all_segments: List[Tuple[float, float]] = []
    all_sampling: List[Dict[str, Any]] = []
    raw_outputs: List[Dict[str, Any]] = []
    statuses: List[ParseResult] = []
    prompt_policy = "windowed" if policy == "windowed" else policy
    for window_start, window_end in windows:
        prompt = build_temporal_prompt(
            query, prompt_policy, duration_sec=window_end - window_start
        )
        messages = build_temporal_messages(
            video_path,
            prompt,
            fps=fps_sample,
            max_frames=max_frames,
            max_pixels=max_pixels,
            clip_start_sec=window_start if policy == "windowed" else None,
            clip_end_sec=window_end if policy == "windowed" else None,
        )
        generated = generate_temporal(
            model,
            processor,
            messages,
            max_new_tokens=max_new_tokens,
            constrained_json=constrained_json,
            temporal_policy=prompt_policy,
        )
        parsed = parse_segments_response(generated.text, prompt_policy)
        statuses.append(parsed)
        all_sampling.extend(generated.sampling)
        raw_outputs.append({
            "window_sec": [window_start, window_end],
            "raw": generated.text,
            "parse_status": parsed.status,
            "parse_reason": parsed.reason,
            "sampling": generated.sampling,
        })
        if parsed.ok:
            for start, end in parsed.segments:
                if policy == "windowed":
                    start += window_start
                    end += window_start
                # Reader-local predictions may exceed their supplied window;
                # clamp each before global merge.
                start = max(window_start, min(start, window_end))
                end = max(window_start, min(end, window_end))
                if end > start:
                    all_segments.append((start, end))
    invalid = [result for result in statuses if not result.ok]
    if invalid:
        return TemporalResult(
            status="invalid",
            segments_sec=[],
            reason=invalid[0].reason,
            sampling=all_sampling,
            raw_outputs=raw_outputs,
        )
    merged = _merge_seconds(all_segments)
    return TemporalResult(
        status="ok" if merged else "valid_empty",
        segments_sec=merged,
        reason="",
        sampling=all_sampling,
        raw_outputs=raw_outputs,
    )
