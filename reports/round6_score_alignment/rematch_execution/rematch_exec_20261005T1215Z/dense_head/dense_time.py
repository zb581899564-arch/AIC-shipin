"""Coverage-aware post-video query head. This module performs no I/O or downloads."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import re
from typing import Any, Callable

import torch
from torch import nn
from torch.nn import functional as F

MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"
REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
EXPECTED_BASE = 8_767_123_696
EXPECTED_LORA = 15_335_424
EXPECTED_HEAD = 524_545
EXPECTED_TOTAL = 8_782_983_665
LIMIT = 9_000_000_000


@dataclass(frozen=True)
class QueryContract:
    markers: tuple[str, ...]
    positions: tuple[int, ...]
    marker_token_ids: tuple[tuple[int, ...], ...]
    last_video_position: int
    sequence_length: int
    original_vocab_size: int


def query_markers(count: int) -> tuple[str, ...]:
    if not 1 <= count <= 100:
        raise ValueError("grid query count must be 1..100")
    # Ordinary strings in the existing vocabulary; no add_tokens/resize_token_embeddings.
    # Include the trailing newline so Qwen's punctuation+newline BPE grouping
    # has exactly the same right context in isolation and in the full prompt.
    return tuple(f" [GRID_QUERY_{i:02d}]\n" for i in range(count))


def query_text(count: int, cell_seconds: float, window_seconds: float) -> str:
    if not 0 < cell_seconds <= window_seconds or count * cell_seconds < window_seconds:
        raise ValueError("grid does not cover window")
    return (f"Assess generic video highlights after observing the entire preceding video. "
            f"The window is {window_seconds:g} seconds; grid cells are {cell_seconds:g} seconds "
            "with zero-based numbering. Each marker queries its corresponding time cell.\n"
            + "".join(query_markers(count)))


def resolve_queries(encoded: dict, tokenizer: Any, count: int,
                    video_token_id: int) -> QueryContract:
    """Read indices from *processor-expanded* IDs; fail on ambiguity/truncation."""
    ids_tensor = encoded["input_ids"]
    mask_tensor = encoded["attention_mask"]
    if ids_tensor.ndim != 2 or ids_tensor.shape[0] != 1 or mask_tensor.shape != ids_tensor.shape:
        raise ValueError("first implementation requires a single processor example")
    ids = ids_tensor[0].detach().cpu().tolist()
    mask = mask_tensor[0].detach().cpu().tolist()
    video_positions = [i for i, tok in enumerate(ids) if tok == video_token_id and mask[i]]
    if not video_positions:
        raise ValueError("processor output contains no attended video tokens")
    vocab_size = len(tokenizer)
    markers = query_markers(count)
    positions, all_marker_ids = [], []
    for marker in markers:
        marker_ids = tuple(tokenizer.encode(marker, add_special_tokens=False))
        if not marker_ids or any(i < 0 or i >= vocab_size for i in marker_ids):
            raise ValueError("query marker not represented by existing vocabulary")
        hits = [i for i in range(len(ids) - len(marker_ids) + 1)
                if tuple(ids[i:i + len(marker_ids)]) == marker_ids
                and all(mask[i:i + len(marker_ids)])]
        if len(hits) != 1:
            raise ValueError(f"query marker missing/ambiguous after expansion: {marker!r}: {hits}")
        start = hits[0]
        if start <= video_positions[-1]:
            raise ValueError("query is not entirely after the complete video")
        positions.append(start + len(marker_ids) - 1)
        all_marker_ids.append(marker_ids)
    if positions != sorted(set(positions)) or len(tokenizer) != vocab_size:
        raise ValueError("query order/vocabulary changed")
    return QueryContract(markers, tuple(positions), tuple(all_marker_ids),
                         video_positions[-1], len(ids), vocab_size)


class DenseTimeHead(nn.Module):
    def __init__(self, hidden_size: int = 4096, bottleneck: int = 128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(hidden_size, bottleneck), nn.GELU(),
                                 nn.Linear(bottleneck, 1))

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        return self.net(states.float()).squeeze(-1)


def language_targets(model: nn.Module) -> list[str]:
    pattern = re.compile(r"^model\.language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$")
    targets = [name for name, module in model.named_modules()
               if pattern.fullmatch(name) and isinstance(module, nn.Linear)]
    layer_count = model.config.text_config.num_hidden_layers
    if len(targets) != layer_count * 4:
        raise RuntimeError(f"expected {layer_count * 4} language projections, got {len(targets)}")
    return targets


def unique_parameters(module: nn.Module):
    seen = set()
    for name, parameter in module.named_parameters(remove_duplicate=False):
        if id(parameter) not in seen:
            seen.add(id(parameter))
            yield name, parameter


def parameter_inventory(backbone: nn.Module, head: nn.Module,
                        enforce_expected: bool = True) -> dict:
    seen, aliases, base, lora, head_count = {}, {}, 0, 0, 0
    for prefix, module in (("backbone", backbone), ("head", head)):
        for name, p in module.named_parameters(remove_duplicate=False):
            fullname = prefix + "." + name
            key = id(p)
            if key in seen:
                aliases.setdefault(seen[key], []).append(fullname)
                continue
            seen[key] = fullname
            if prefix == "head":
                head_count += p.numel()
            elif "lora_" in name:
                lora += p.numel()
            else:
                base += p.numel()
            if prefix == "backbone" and p.requires_grad and "lora_" not in name:
                raise RuntimeError(f"unexpected trainable base parameter: {name}")
            if prefix == "backbone" and "visual" in name and p.requires_grad:
                raise RuntimeError("vision must remain frozen")
            if "modules_to_save" in name:
                raise RuntimeError("modules_to_save would introduce unapproved parameter copies")
    total = base + lora + head_count
    result = {"base": base, "lora": lora, "head": head_count, "total": total,
              "decimal_9B_remaining": LIMIT - total, "shared_parameter_aliases": aliases,
              "method": "actual numel, tensor identity de-duplication, unquantized BF16 base"}
    if total > LIMIT:
        raise RuntimeError(f"parameter budget exceeded: {result}")
    if enforce_expected and (base, lora, head_count, total) != (
            EXPECTED_BASE, EXPECTED_LORA, EXPECTED_HEAD, EXPECTED_TOTAL):
        raise RuntimeError(f"actual parameter count differs from frozen proposal: {result}")
    return result


def clear_model_cache(backbone: nn.Module, external_caches: dict | None = None) -> int:
    """No KV state is retained by this wrapper; clear Qwen's persisted RoPE state."""
    if external_caches is not None:
        external_caches.clear()
    reset = 0
    for module in backbone.modules():
        if hasattr(module, "rope_deltas"):
            module.rope_deltas = None
            reset += 1
    return reset


class DenseTimeModel(nn.Module):
    def __init__(self, peft_backbone: nn.Module, hidden_size: int = 4096):
        super().__init__()
        self.backbone = peft_backbone
        self.head = DenseTimeHead(hidden_size)
        self.head_enabled = True
        self.external_caches: dict = {}

    def forward(self, encoded: dict, positions: torch.Tensor) -> torch.Tensor:
        if not self.head_enabled:
            raise RuntimeError("time head is disabled for spatial use")
        if any(k in encoded for k in ("labels", "inputs_embeds", "past_key_values", "logits_to_keep")):
            raise ValueError("dense input contains forbidden state/LM supervision")
        if positions.ndim != 2 or positions.shape[0] != encoded["input_ids"].shape[0]:
            raise ValueError("query position batch shape mismatch")
        if positions.numel() == 0 or (positions < 0).any() or (positions >= encoded["input_ids"].shape[1]).any():
            raise ValueError("query positions outside processor sequence")
        if not encoded["attention_mask"].gather(1, positions).bool().all():
            raise ValueError("query points into padding")
        clear_model_cache(self.backbone, self.external_caches)
        base = self.backbone.get_base_model()
        # Bypass Qwen3VLForConditionalGeneration and lm_head completely. Only the
        # final BxSxH tensor is produced, never all-layer hidden_states or BxSxV logits.
        output = base.model(**encoded, use_cache=False, output_hidden_states=False,
                            output_attentions=False, return_dict=True)
        states = output.last_hidden_state
        if states.shape[:2] != encoded["input_ids"].shape or states.shape[-1] != self.head.net[0].in_features:
            raise RuntimeError("final hidden state shape differs from processor input")
        if getattr(output, "past_key_values", None) is not None:
            raise RuntimeError("dense path unexpectedly retained a KV cache")
        if getattr(output, "hidden_states", None) is not None:
            raise RuntimeError("dense path unexpectedly returned all hidden layers")
        rows = torch.arange(states.shape[0], device=states.device).unsqueeze(1)
        gathered = states[rows, positions.to(states.device)]
        logits = self.head(gathered)
        if not torch.isfinite(logits).all():
            raise RuntimeError("dense head produced nonfinite logits, including UNKNOWN cells")
        return logits

    @contextmanager
    def spatial_base(self):
        """Use the same original base, with adapters disabled and no merged weights."""
        was_training, was_enabled = self.training, self.head_enabled
        if any(bool(getattr(m, "merged", False)) for m in self.backbone.modules()):
            raise RuntimeError("merged LoRA weights cannot establish original-base restoration")
        self.head_enabled = False
        self.eval()
        clear_model_cache(self.backbone, self.external_caches)
        try:
            with self.backbone.disable_adapter():
                yield self.backbone.get_base_model()
        finally:
            clear_model_cache(self.backbone, self.external_caches)
            self.head_enabled = was_enabled
            self.train(was_training)


def masked_bce_sum(logits: torch.Tensor, targets: torch.Tensor,
                   known_mask: torch.Tensor) -> tuple[torch.Tensor | None, int]:
    if logits.shape != targets.shape or logits.shape != known_mask.shape or known_mask.dtype != torch.bool:
        raise ValueError("BCE grid shapes/boolean mask mismatch")
    count = int(known_mask.sum().item())
    if count == 0:
        return None, 0
    # Index BEFORE BCE. NaN/invalid UNKNOWN labels must never enter the loss graph.
    selected_logits, selected_targets = logits[known_mask].float(), targets[known_mask].float()
    if not torch.isfinite(selected_logits).all() or not torch.isfinite(selected_targets).all():
        raise ValueError("known logits/targets are non-finite")
    if ((selected_targets < 0) | (selected_targets > 1)).any():
        raise ValueError("known BCE targets are outside [0,1]")
    return F.binary_cross_entropy_with_logits(selected_logits, selected_targets, reduction="sum"), count


@dataclass
class UpdateCounters:
    optimizer_steps: int = 0
    skipped_unknown_accumulations: int = 0
    known_cells_seen: int = 0


def accumulation_update(model: nn.Module, microbatches: list[dict], optimizer,
                        scheduler, counters: UpdateCounters,
                        forward: Callable[[dict], torch.Tensor],
                        before_step: Callable[[], Any] | None = None,
                        clip_norm: float = 1.0) -> dict:
    if not microbatches:
        raise ValueError("empty accumulation")
    total_known = sum(int(batch["known_mask"].sum().item()) for batch in microbatches)
    optimizer.zero_grad(set_to_none=True)
    if total_known == 0:
        counters.skipped_unknown_accumulations += 1
        return {"status": "SKIP_ALL_UNKNOWN", "known_cells": 0,
                "optimizer_step": counters.optimizer_steps}
    value = 0.0
    for batch in microbatches:
        if not bool(batch["known_mask"].any()):
            continue
        loss_sum, count = masked_bce_sum(forward(batch), batch["targets"], batch["known_mask"])
        assert loss_sum is not None and count > 0
        value += float(loss_sum.detach().item()) / total_known
        (loss_sum / total_known).backward()
    trainable = [p for p in model.parameters() if p.requires_grad]
    if any(p.grad is None or not torch.isfinite(p.grad).all() for p in trainable):
        raise RuntimeError("missing or non-finite trainable gradient")
    evidence = before_step() if before_step is not None else None
    norm = torch.nn.utils.clip_grad_norm_(trainable, clip_norm, error_if_nonfinite=True)
    optimizer.step()
    if scheduler is not None:
        scheduler.step()
    counters.optimizer_steps += 1
    counters.known_cells_seen += total_known
    optimizer.zero_grad(set_to_none=True)
    return {"status": "UPDATED", "loss_known_cell_mean": value, "known_cells": total_known,
            "optimizer_step": counters.optimizer_steps, "gradient_norm": float(norm),
            "gradient_evidence": evidence}


def fingerprint_parameters(module: nn.Module, include: Callable[[str, torch.Tensor], bool]) -> dict:
    """Hash all selected bytes in bounded chunks, including frozen visual weights."""
    digest, count, tensors = hashlib.sha256(), 0, 0
    for name, parameter in unique_parameters(module):
        if not include(name, parameter):
            continue
        digest.update(name.encode("utf-8"))
        digest.update(str((tuple(parameter.shape), parameter.dtype)).encode("ascii"))
        flat = parameter.detach().reshape(-1)
        for start in range(0, flat.numel(), 1 << 20):
            data = flat[start:start + (1 << 20)].contiguous().view(torch.uint8).cpu().numpy().tobytes()
            digest.update(data)
        count += parameter.numel()
        tensors += 1
    return {"sha256": digest.hexdigest(), "numel": count, "tensors": tensors}
