"""CPU temporal selectors over frozen features, with unique-native-frame losses.

Reference values mean selection in a public human summary. An unselected frame
is not an ``ordinary`` label. Unknown annotations must use ``known_mask`` and
are never filled with negative labels. Nothing in this module reads Test data,
updates a backbone, chooses a checkpoint, or grants production admission.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F


DEFAULT_FROZEN_PARAMETERS = 8_782_557_449
MAX_HEAD_PARAMETERS = 2_000_000
MAX_TOTAL_PARAMETERS = 9_000_000_000
DEFAULT_SEED = 105
DEFAULT_UPDATES = 200


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _features(features: torch.Tensor, feature_dim: int | None = None) -> None:
    if not isinstance(features, torch.Tensor):
        raise TypeError("features must be a detached CPU tensor")
    if features.device.type != "cpu" or features.ndim != 2 or min(features.shape) < 1:
        raise ValueError("features must have nonempty CPU shape [groups, dimensions]")
    if feature_dim is not None and features.shape[1] != feature_dim:
        raise ValueError("feature dimension differs from the measured head input")
    if features.requires_grad or features.grad_fn is not None:
        raise ValueError("features must be detached; backbone gradients are forbidden")
    if features.dtype not in (torch.float32, torch.float64) or not torch.isfinite(features).all():
        raise ValueError("features must be finite float32 or float64")


class TemporalHead(nn.Module):
    """Linear/GELU, two kernel-3 temporal convolutions, then one group logit."""

    def __init__(self, feature_dim: int, hidden: int = 128):
        super().__init__()
        self.feature_dim = _positive_int(feature_dim, "feature_dim")
        self.hidden = _positive_int(hidden, "hidden")
        # Check before allocating, then verify against actual resident parameters.
        expected = feature_dim * hidden + hidden + 2 * (3 * hidden * hidden + hidden) + hidden + 1
        if expected > MAX_HEAD_PARAMETERS:
            raise ValueError("head exceeds the 2M parameter budget")
        self.input = nn.Linear(feature_dim, hidden)
        self.conv1 = nn.Conv1d(hidden, hidden, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(hidden, hidden, kernel_size=3, padding=1)
        self.output = nn.Linear(hidden, 1)
        if self.parameter_count != expected:
            raise RuntimeError("actual head parameters differ from the architecture count")

    @property
    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        _features(features, self.feature_dim)
        if any(p.device.type != "cpu" for p in self.parameters()):
            raise ValueError("this bounded implementation accepts a CPU head only")
        if features.dtype != self.input.weight.dtype:
            raise ValueError("features must match the explicitly chosen head dtype")
        x = F.gelu(self.input(features))
        x = x.transpose(0, 1).unsqueeze(0)
        x = F.gelu(self.conv1(x))
        x = F.gelu(self.conv2(x))
        logits = self.output(x.squeeze(0).transpose(0, 1)).squeeze(-1)
        if not torch.isfinite(logits).all():
            raise ValueError("nonfinite temporal head output")
        return logits


@dataclass(frozen=True)
class TrainingVideo:
    """One complete source, never overlapping windows as separate samples.

    ``native_group[f]`` is the ONE group owning unique native frame row ``f``.
    Repeated group indices are expected: they give each group its actual frame
    duration. The caller must construct a canonical frame axis before this API;
    this representation cannot encode multiple owners for the same frame.
    ``reference`` is bool [frames, raters]. ``known_mask`` may have that shape or
    [frames], where False means unobserved, not unselected.
    """

    source_id: str
    features: torch.Tensor
    native_group: torch.Tensor
    reference: torch.Tensor
    known_mask: torch.Tensor | None = None

    def validate(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("one nonempty original source_id is required")
        _features(self.features)
        group = self.native_group
        if not isinstance(group, torch.Tensor) or group.device.type != "cpu":
            raise ValueError("native_group must be a CPU tensor")
        if group.ndim != 1 or group.numel() == 0 or group.dtype != torch.int64:
            raise ValueError("native_group must be int64 [unique native frames], one owner each")
        if group.min().item() < 0 or group.max().item() >= self.features.shape[0]:
            raise ValueError("native_group references an absent temporal feature group")
        reference = self.reference
        if not isinstance(reference, torch.Tensor) or reference.device.type != "cpu":
            raise ValueError("reference must be a CPU tensor")
        if reference.dtype != torch.bool or reference.ndim != 2 or reference.shape[0] != group.numel() or reference.shape[1] == 0:
            raise ValueError("reference must be bool [unique native frames, all raters]")
        if self.known_mask is not None:
            known = self.known_mask
            if not isinstance(known, torch.Tensor) or known.device.type != "cpu" or known.dtype != torch.bool:
                raise ValueError("known_mask must be a CPU bool tensor; UNKNOWN is not zero")
            if known.shape != reference.shape and known.shape != (group.numel(),):
                raise ValueError("known_mask must be [frames] or [frames, raters]")
            if not known.any():
                raise ValueError("a source with no known annotations cannot supply a loss")

    def known(self) -> torch.Tensor:
        if self.known_mask is None:
            return torch.ones_like(self.reference)
        if self.known_mask.ndim == 1:
            return self.known_mask[:, None].expand_as(self.reference)
        return self.known_mask


def _video(value: TrainingVideo | Mapping) -> TrainingVideo:
    if isinstance(value, TrainingVideo):
        return value
    if isinstance(value, Mapping):
        return TrainingVideo(**value)
    raise TypeError("videos must contain TrainingVideo instances or equivalent mappings")


def _arm(arm: str) -> str:
    if not isinstance(arm, str) or arm.upper() not in ("BCE", "SET"):
        raise ValueError("arm must be BCE or SET")
    return arm.upper()


def source_losses(group_logits: torch.Tensor, video: TrainingVideo | Mapping) -> dict[str, torch.Tensor]:
    """Return per-source BCE and mean per-rater set loss, both native weighted.

    BCE targets are each frame's known-rater selection probability. Every
    annotated native frame receives equal weight, regardless of group duration
    or number of known raters. SET adds mean(1-softF1) over raters with known
    frames. A fully negative rater instead contributes mean(p_selected), an
    explicit selection penalty with useful gradients. A wholly unknown rater
    is excluded; no labels are invented.
    """
    video = _video(video)
    video.validate()
    if not isinstance(group_logits, torch.Tensor) or group_logits.device.type != "cpu":
        raise ValueError("group_logits must be a CPU tensor")
    if group_logits.ndim != 1 or group_logits.numel() != video.features.shape[0] or not group_logits.is_floating_point():
        raise ValueError("group_logits must contain one floating value per temporal group")
    if not torch.isfinite(group_logits).all():
        raise ValueError("group_logits must be finite")
    logits = group_logits[video.native_group]
    known = video.known()
    known_count = known.sum(dim=1)
    annotated = known_count > 0
    selected = (video.reference & known).sum(dim=1).to(logits.dtype)
    soft_target = selected[annotated] / known_count[annotated].to(logits.dtype)
    bce = F.binary_cross_entropy_with_logits(logits[annotated], soft_target)
    probabilities = logits.sigmoid()
    rater_losses = []
    for rater in range(video.reference.shape[1]):
        mask = known[:, rater]
        if not mask.any():
            continue
        p = probabilities[mask]
        y = video.reference[mask, rater].to(p.dtype)
        positives = y.sum()
        if positives.item() == 0:
            rater_losses.append(p.mean())
        else:
            # Positive references guarantee a strictly positive denominator;
            # no artificial epsilon targets or smoothed empty labels needed.
            rater_losses.append(1 - 2 * (p * y).sum() / (p.sum() + positives))
    set_loss = torch.stack(rater_losses).mean()
    return {"bce": bce, "set_loss": set_loss, "set": bce + set_loss}


def source_loss(group_logits: torch.Tensor, video: TrainingVideo | Mapping, arm: str) -> torch.Tensor:
    arm = _arm(arm)
    losses = source_losses(group_logits, video)
    return losses["bce" if arm == "BCE" else "set"]


def initialize_head(feature_dim: int, hidden: int = 128, *, seed: int = DEFAULT_SEED,
                    dtype: torch.dtype = torch.float32) -> TemporalHead:
    """Create the same initialization for either arm without changing caller RNG."""
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
        raise ValueError("seed must be a nonnegative int below 2**63")
    if dtype not in (torch.float32, torch.float64):
        raise ValueError("head dtype must be float32 or float64")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return TemporalHead(feature_dim, hidden).to(dtype=dtype)


def parameter_budget(model: TemporalHead, frozen_parameters: int = DEFAULT_FROZEN_PARAMETERS) -> dict[str, int]:
    """Count the actual head and caller's measured resident frozen components."""
    _positive_int(frozen_parameters, "frozen_parameters")
    count = model.parameter_count
    total = frozen_parameters + count
    if count > MAX_HEAD_PARAMETERS or total > MAX_TOTAL_PARAMETERS:
        raise ValueError("actual resident parameters exceed the head or total budget")
    return {"head_parameters": count, "frozen_parameters": frozen_parameters, "resident_parameters": total}


def fit(videos: Sequence[TrainingVideo | Mapping], arm: str, *, seed: int = DEFAULT_SEED,
        updates: int = DEFAULT_UPDATES, hidden: int = 128, learning_rate: float = 1e-3,
        weight_decay: float = 0.01, grad_clip: float = 1.0,
        frozen_parameters: int = DEFAULT_FROZEN_PARAMETERS) -> tuple[TemporalHead, dict]:
    """Full-batch, source-equal CPU AdamW; return ONLY the final checkpoint.

    The registered default is seed105/200 updates/lr1e-3/wd.01/clip1. Smaller
    explicit update counts support engineering tests, never checkpoint search.
    Each complete source is forwarded once per update. Backpropagating its
    loss divided by source count preserves equal source weight without keeping
    every source's graph resident. Only this new head enters the optimizer.
    """
    arm = _arm(arm)
    if isinstance(updates, bool) or not isinstance(updates, int) or not 1 <= updates <= DEFAULT_UPDATES:
        raise ValueError("updates must be an explicit integer in 1..200")
    for value, name, allow_zero in ((learning_rate, "learning_rate", False), (weight_decay, "weight_decay", True), (grad_clip, "grad_clip", False)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
            raise ValueError(f"invalid {name}")
    videos = [_video(video) for video in videos]
    if not videos:
        raise ValueError("at least one complete training source is required")
    for video in videos:
        video.validate()
    ids = [video.source_id for video in videos]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate source_id would overweight an overlapping source")
    first = videos[0].features
    if any(v.features.shape[1] != first.shape[1] or v.features.dtype != first.dtype for v in videos):
        raise ValueError("all frozen features must share dimension and dtype")
    model = initialize_head(first.shape[1], hidden, seed=seed, dtype=first.dtype)
    budget = parameter_budget(model, frozen_parameters)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    history = []
    model.train()
    for _ in range(updates):
        optimizer.zero_grad(set_to_none=True)
        source_values = []
        for video in videos:
            loss = source_loss(model(video.features), video, arm)
            if not torch.isfinite(loss):
                raise ValueError("nonfinite source loss; no fallback permitted")
            (loss / len(videos)).backward()
            source_values.append(float(loss.detach()))
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip, error_if_nonfinite=True)
        if not torch.isfinite(norm):
            raise ValueError("nonfinite gradient norm")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("nonfinite head parameters after update")
        history.append(sum(source_values) / len(source_values))
    model.eval()
    report = dict(arm=arm, seed=seed, updates=updates, learning_rate=learning_rate,
                  weight_decay=weight_decay, grad_clip=grad_clip, hidden=hidden,
                  feature_dim=first.shape[1], source_ids=ids, source_weighting="equal_complete_sources",
                  bce_weighting="equal_known_unique_native_frames",
                  label_meaning="known_rater_summary_selection_probability",
                  empty_reference_penalty="mean_selection_probability",
                  checkpoint_selection="final_update_only", objective_history=history,
                  backbone_updates=0, metric_scope="EXTERNAL_TEMPORAL_PROXY_NO_OFFICIAL_SPATIAL_SCORE",
                  **budget)
    return model, report


@torch.no_grad()
def predict(model: TemporalHead, features: torch.Tensor) -> torch.Tensor:
    """Return one detached CPU selection probability per temporal group."""
    return model(features).sigmoid().detach()


@torch.no_grad()
def predict_native(model: TemporalHead, features: torch.Tensor, native_group: torch.Tensor) -> torch.Tensor:
    """Expand group probabilities to the caller's unique native frame axis."""
    probability = predict(model, features)
    if not isinstance(native_group, torch.Tensor) or native_group.device.type != "cpu" or native_group.dtype != torch.int64 or native_group.ndim != 1 or native_group.numel() == 0:
        raise ValueError("native_group must be a nonempty CPU int64 vector")
    if native_group.min().item() < 0 or native_group.max().item() >= probability.numel():
        raise ValueError("native_group references an absent temporal group")
    return probability[native_group]
