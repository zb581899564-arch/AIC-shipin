"""Fail-closed Qwen3-VL temporal-only LoRA training entrypoint.

The entrypoint checks supervisor authorization and A's accepted data gate
before importing any GPU framework or loading model weights.  With the
current coordination state (``training_authorized: false`` and no accepted
200/50/50 source-disjoint media-aligned split) it writes a rejection report
and exits without creating an adapter.

The deferred training path is intentionally ordinary Transformers Trainer +
PEFT code so it can run inside B's independently prepared environment after
the supervisor releases the gate.  No environment installation is performed
here.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

try:  # module invocation: python -m training.train_lora
    from .gate import GateDecision, evaluate_training_gate, write_gate_report
except ImportError:  # direct invocation from training/
    from gate import GateDecision, evaluate_training_gate, write_gate_report


WORK_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TrainingConfig:
    model_name_or_path: str
    output_dir: str
    fps: float = 2.0
    max_frames: int = 32
    max_pixels_per_frame: int = 100_000
    max_seq_length: int = 8192
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.05
    max_grad_norm: float = 1.0
    seed: int = 42
    num_train_epochs: float = 3.0
    time_limit_hours: float = 8.0
    smoke_samples: int = 16
    smoke_steps: int = 20
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_targets: Tuple[str, ...] = ("q_proj", "k_proj", "v_proj", "o_proj")
    temporal_only: bool = True
    freeze_visual_connector: bool = True
    use_cache: bool = False

    def as_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["lora_targets"] = list(self.lora_targets)
        return result


def assistant_only_labels(full_ids: Sequence[int], prefix_ids: Sequence[int]) -> List[int]:
    """Mask every user/video token and retain assistant tokens only.

    The generation-prompt token is part of ``prefix_ids`` and is masked too;
    the learned target therefore begins at the assistant response text.  A
    prefix mismatch is fatal because silently shifting this boundary would
    train on the user prompt or vision placeholders.
    """

    full = list(full_ids)
    prefix = list(prefix_ids)
    if len(prefix) > len(full) or full[: len(prefix)] != prefix:
        raise ValueError("Qwen chat template prefix mismatch; refusing an imprecise assistant mask")
    return [-100] * len(prefix) + full[len(prefix) :]


def _default_model(coordination_path: Path) -> str:
    try:
        with coordination_path.open("r", encoding="utf-8") as handle:
            value = json.load(handle).get("model")
        if isinstance(value, str) and value:
            return value
    except (OSError, ValueError, AttributeError):
        pass
    return "Qwen/Qwen3-VL-4B-Instruct"


def _jsonl_rows(path: Union[str, Path]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be an object")
            rows.append(row)
    return rows


def _row_video_path(row: Mapping[str, Any]) -> str:
    for key in ("video_path", "video", "media_path"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    for key in ("videos", "video_paths", "media"):
        value = row.get(key)
        if isinstance(value, list) and value and isinstance(value[0], str):
            return value[0]
        if isinstance(value, str) and value:
            return value
    raise ValueError("training row has no video path")


def _row_prompt(row: Mapping[str, Any]) -> str:
    for key in ("prompt", "question", "instruction", "problem"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return (
        "Select the high-light frames in this video and return the required "
        "frame and crop-box JSONL format."
    )


def _row_answer(row: Mapping[str, Any]) -> str:
    for key in ("answer", "response", "target", "label", "output"):
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    raise ValueError("training row has no answer/target")


def build_temporal_messages(row: Mapping[str, Any], config: TrainingConfig) -> List[Dict[str, Any]]:
    """Build a video-only Qwen message; image inputs are rejected."""

    for image_key in ("image", "images", "image_path", "image_paths"):
        if row.get(image_key):
            raise ValueError(f"temporal-only row contains {image_key}")
    video_path = _row_video_path(row)
    if not os.path.isfile(video_path):
        raise ValueError(f"video path does not exist: {video_path}")
    video = {
        "type": "video",
        "video": video_path,
        "fps": config.fps,
        # Qwen processors that support these controls enforce the caps.  The
        # collator also passes them through as processor kwargs.
        "max_frames": config.max_frames,
        "max_pixels": config.max_pixels_per_frame,
        "total_pixels": config.max_pixels_per_frame * config.max_frames,
    }
    return [
        {
            "role": "user",
            "content": [
                video,
                {"type": "text", "text": _row_prompt(row)},
            ],
        },
        {"role": "assistant", "content": _row_answer(row)},
    ]


class JsonlVideoDataset:
    """Tiny dependency-free dataset wrapper used by Transformers Trainer."""

    def __init__(self, paths: Sequence[Union[str, Path]], max_samples: Optional[int] = None):
        self.rows: List[Dict[str, Any]] = []
        for path in paths:
            self.rows.extend(_jsonl_rows(path))
        if max_samples is not None:
            self.rows = self.rows[:max_samples]
        if not self.rows:
            raise ValueError("accepted training split is empty")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return self.rows[index]


def _language_target_modules(model: Any, wanted: Sequence[str]) -> List[str]:
    """Find exact language-model attention paths, excluding vision/connectors."""

    targets: List[str] = []
    bad_tokens = ("visual", "vision", "connector", "merger", "multimodal")
    language_tokens = ("language_model", "decoder", "transformer", ".layers.")
    for name, _module in model.named_modules():
        leaf = name.rsplit(".", 1)[-1]
        lowered = name.lower()
        if leaf in wanted and any(token in lowered for token in language_tokens) and not any(
            token in lowered for token in bad_tokens
        ):
            targets.append(name)
    # De-duplicate while preserving module traversal order.
    return list(dict.fromkeys(targets))


def _load_base_model(model_name: str, torch: Any, transformers: Any) -> Any:
    load_kwargs = {
        "torch_dtype": torch.bfloat16,
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
    }
    last_error: Optional[Exception] = None
    for class_name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq", "AutoModelForCausalLM"):
        cls = getattr(transformers, class_name, None)
        if cls is None:
            continue
        try:
            return cls.from_pretrained(model_name, **load_kwargs)
        except Exception as exc:  # try the next compatible Auto class
            last_error = exc
    raise RuntimeError(f"unable to load Qwen3-VL model {model_name}: {last_error}")


def _attach_lora(model: Any, config: TrainingConfig, torch: Any, peft: Any) -> Any:
    for _name, parameter in model.named_parameters():
        parameter.requires_grad = False
    target_modules = _language_target_modules(model, config.lora_targets)
    if not target_modules:
        raise RuntimeError("no language attention q/k/v/o modules found; refusing broad/vision LoRA")
    lora_config = peft.LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )
    model = peft.get_peft_model(model, lora_config)
    trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    if not trainable or any("lora_" not in name for name in trainable):
        raise RuntimeError("LoRA attachment exposed non-LoRA trainable parameters")
    if any(any(token in name.lower() for token in ("visual", "vision", "connector", "merger")) for name in trainable):
        raise RuntimeError("LoRA attachment touched visual/connector parameters")
    model.config.use_cache = config.use_cache
    return model


def _make_collator(processor: Any, config: TrainingConfig, process_vision_info: Any) -> Any:
    def vision_inputs(messages: List[Dict[str, Any]]) -> Tuple[List[Any], List[Any], Dict[str, Any]]:
        """Decode one video and preserve Qwen's optional video metadata."""

        try:
            image_values, video_values, kwargs = process_vision_info(
                messages,
                image_patch_size=getattr(processor.image_processor, "patch_size", 16),
                return_video_kwargs=True,
                return_video_metadata=True,
            )
        except TypeError:
            image_values, video_values, kwargs = process_vision_info(
                messages,
                image_patch_size=getattr(processor.image_processor, "patch_size", 16),
                return_video_kwargs=True,
            )
        if image_values:
            raise ValueError("temporal-only collator received image inputs")
        kwargs = dict(kwargs or {})

        # Recent qwen-vl-utils returns (video, video_metadata), either as one
        # tuple or as a list of such tuples.  Transformers expects the video
        # tensors and `video_metadata` as separate arguments.
        if isinstance(video_values, tuple) and len(video_values) == 2:
            video_values = [video_values]
        videos: List[Any] = []
        metadata: List[Any] = []
        for value in video_values or []:
            if isinstance(value, tuple) and len(value) == 2:
                videos.append(value[0])
                metadata.append(value[1])
            else:
                videos.append(value)
        if metadata:
            kwargs["video_metadata"] = metadata
        return [], videos, kwargs

    class VideoCollator:
        def __call__(self, features: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
            if len(features) != 1:
                raise ValueError("Qwen3-VL collator requires per-device batch_size=1")
            messages = build_temporal_messages(features[0], config)
            user_messages = messages[:1]
            full_text = processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
                enable_thinking=False,
            )
            user_text = processor.apply_chat_template(
                user_messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            _images, videos, video_kwargs = vision_inputs(messages)
            inputs: Dict[str, Any] = {
                "text": [full_text],
                "videos": videos,
                "padding": False,
                "return_tensors": "pt",
                "truncation": False,
            }
            inputs.update(video_kwargs)
            batch = processor(**inputs)
            # Tokenize the identical video prefix with the generation prompt.
            # This gives an exact assistant-only label boundary, including
            # Qwen's expanded video placeholder tokens.
            prefix_inputs: Dict[str, Any] = {
                "text": [user_text],
                "videos": videos,
                "padding": False,
                "return_tensors": "pt",
                "truncation": False,
            }
            prefix_inputs.update(video_kwargs)
            prefix_batch = processor(**prefix_inputs)
            full_ids = batch["input_ids"][0].tolist()
            prefix_ids = prefix_batch["input_ids"][0].tolist()
            input_length = len(full_ids)
            prefix_length = len(prefix_ids)
            if input_length > config.max_seq_length:
                raise ValueError(
                    f"sequence length {input_length} exceeds max_seq_length={config.max_seq_length}; refusing truncation"
                )
            label_values = assistant_only_labels(full_ids, prefix_ids)
            labels = batch["input_ids"].clone()
            labels[0] = labels.new_tensor(label_values)
            if "attention_mask" in batch:
                labels[batch["attention_mask"] == 0] = -100
            batch["labels"] = labels
            return batch

    return VideoCollator()


def _run_training(config: TrainingConfig, decision: GateDecision, smoke: bool) -> Dict[str, Any]:
    """Deferred GPU path; called only after the fail-closed gate passes."""

    # Deliberately deferred imports: the rejected path above cannot initialize
    # CUDA or download model code.
    import torch
    import transformers
    import peft
    from qwen_vl_utils import process_vision_info

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; refusing BF16 training")
    if hasattr(torch.cuda, "is_bf16_supported") and not torch.cuda.is_bf16_supported():
        raise RuntimeError("CUDA device does not report BF16 support")
    torch.manual_seed(config.seed)
    random.seed(config.seed)

    split_paths = [decision.split_audit[name]["path"] for name in ("train", "dev", "holdout")]
    train_dataset = JsonlVideoDataset([split_paths[0]], max_samples=config.smoke_samples if smoke else None)
    dev_dataset = JsonlVideoDataset([split_paths[1]])
    # Holdout is loaded only to verify the accepted interface and remains
    # outside Trainer's training/evaluation datasets.
    holdout_count = len(JsonlVideoDataset([split_paths[2]]))

    processor = transformers.AutoProcessor.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=True,
        padding_side="right",
    )
    model = _load_base_model(config.model_name_or_path, torch, transformers)
    model = _attach_lora(model, config, torch, peft)
    collator = _make_collator(processor, config, process_vision_info)

    class TimeLimitCallback(transformers.TrainerCallback):
        def __init__(self, hours: float):
            self.deadline = max(hours, 0.01) * 3600.0
            self.started = 0.0

        def on_train_begin(self, args, state, control, **kwargs):
            self.started = time.monotonic()
            return control

        def on_step_end(self, args, state, control, **kwargs):
            if time.monotonic() - self.started >= self.deadline:
                control.should_training_stop = True
            return control

    max_steps = config.smoke_steps if smoke else -1
    train_args_kwargs = dict(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        lr_scheduler_type=config.lr_scheduler_type,
        warmup_ratio=config.warmup_ratio,
        max_grad_norm=config.max_grad_norm,
        num_train_epochs=config.num_train_epochs,
        max_steps=max_steps,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=1,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=2,
        remove_unused_columns=False,
        report_to=[],
        seed=config.seed,
        data_seed=config.seed,
        optim="adamw_torch",
    )
    try:
        training_args = transformers.TrainingArguments(eval_strategy="epoch", **train_args_kwargs)
    except TypeError:
        training_args = transformers.TrainingArguments(evaluation_strategy="epoch", **train_args_kwargs)
    trainer = transformers.Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        data_collator=collator,
        callbacks=[TimeLimitCallback(config.time_limit_hours)],
    )
    trainer.train()
    trainer.save_model(config.output_dir)
    processor.save_pretrained(config.output_dir)

    adapter_config = Path(config.output_dir) / "adapter_config.json"
    if not adapter_config.is_file():
        raise RuntimeError("Trainer completed but adapter_config.json was not saved")
    # Reload the adapter onto a *fresh* base model. Wrapping the already-PEFT
    # model would only prove that a second adapter wrapper can be nested; it
    # would not verify the saved artifact can restore the base checkpoint.
    fresh_base = _load_base_model(config.model_name_or_path, torch, transformers)
    reloaded = peft.PeftModel.from_pretrained(fresh_base, config.output_dir, is_trainable=False)
    if any(parameter.requires_grad for parameter in reloaded.parameters()):
        raise RuntimeError("reloaded adapter unexpectedly has trainable parameters")
    return {
        "status": "COMPLETED",
        "gpu_started": True,
        "adapter_created": True,
        "adapter_reload_ok": True,
        "train_rows": len(train_dataset),
        "dev_rows": len(dev_dataset),
        "holdout_rows_checked": holdout_count,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fail-closed Qwen3-VL temporal-only LoRA trainer")
    parser.add_argument("--coordination", default=str(WORK_ROOT / "coordination.json"))
    parser.add_argument("--data-gate", default=str(WORK_ROOT / "data_audit" / "training_gate.json"))
    parser.add_argument("--report", default=str(WORK_ROOT / "reports" / "eval_training_gate.json"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--output-dir", default=str(WORK_ROOT / "runs" / "qwen3_vl_lora"))
    parser.add_argument("--train-file", default=None)
    parser.add_argument("--dev-file", default=None)
    parser.add_argument("--holdout-file", default=None)
    parser.add_argument("--smoke", action="store_true", help="after gate release: 16 samples / 20 optimizer steps")
    parser.add_argument("--dry-run", action="store_true", help="after gate release: validate gate and config without loading GPU")
    parser.add_argument("--overwrite", action="store_true", help="allow writing into a non-empty output directory after gate release")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    coordination_path = Path(args.coordination)
    gate_path = Path(args.data_gate)
    overrides = {
        name: value
        for name, value in {
            "train": args.train_file,
            "dev": args.dev_file,
            "holdout": args.holdout_file,
        }.items()
        if value
    }
    decision = evaluate_training_gate(coordination_path, gate_path, split_overrides=overrides)
    model_name = args.model or _default_model(coordination_path)
    config = TrainingConfig(model_name_or_path=model_name, output_dir=args.output_dir)
    common = {
        "config": config.as_dict(),
        "smoke_requested": args.smoke,
        "dry_run": args.dry_run,
        "source_data_policy": "raw test data is read-only and never a training source",
    }
    if not decision.ok:
        write_gate_report(
            args.report,
            decision,
            status="REJECTED",
            rejection_reasons=decision.reasons,
            **common,
        )
        print(json.dumps({"status": "REJECTED", "reasons": decision.reasons, "report": args.report}))
        return 2

    output_path = Path(args.output_dir)
    if output_path.exists() and any(output_path.iterdir()) and not args.overwrite:
        decision.ok = False
        decision.reasons.append("OUTPUT_DIR_NON_EMPTY")
        write_gate_report(args.report, decision, status="REJECTED", rejection_reasons=decision.reasons, **common)
        print(json.dumps({"status": "REJECTED", "reasons": decision.reasons, "report": args.report}))
        return 2
    if args.dry_run:
        write_gate_report(args.report, decision, status="GATE_PASS_DRY_RUN", **common)
        print(json.dumps({"status": "GATE_PASS_DRY_RUN", "report": args.report}))
        return 0

    try:
        result = _run_training(config, decision, args.smoke)
    except Exception as exc:
        write_gate_report(
            args.report,
            decision,
            status="ERROR",
            error_type=type(exc).__name__,
            error=str(exc),
            **common,
        )
        print(json.dumps({"status": "ERROR", "error": str(exc), "report": args.report}))
        return 1
    write_gate_report(args.report, decision, **result, **common)
    print(json.dumps({"status": result["status"], "report": args.report, "adapter_reload_ok": result.get("adapter_reload_ok")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
