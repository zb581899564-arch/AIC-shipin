"""Small zero-output MLP over already frozen, detached features. CPU by design."""
import math
from dataclasses import dataclass
from typing import Sequence
import torch
from torch import nn

try:
    from .contracts import NativeContract
    from .metrics import macro_objective, video_losses
except ImportError:  # Standalone import from this directory.
    from contracts import NativeContract
    from metrics import macro_objective, video_losses

FROZEN_BACKBONE_PARAMETERS = 8_782_459_120
MAX_HEAD_PARAMETERS = 2_000_000
MAX_TOTAL_PARAMETERS = 9_000_000_000


class ResidualHead(nn.Module):
    def __init__(self, feature_dim: int, hidden_dim: int = 64):
        super().__init__()
        if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (feature_dim, hidden_dim)):
            raise ValueError("Feature/hidden dimensions must be measured positive integers")
        count = feature_dim * hidden_dim + hidden_dim + hidden_dim + 1
        if count > MAX_HEAD_PARAMETERS or FROZEN_BACKBONE_PARAMETERS + count > MAX_TOTAL_PARAMETERS:
            raise ValueError("Actual resident parameter budget exceeded")
        self.feature_dim = feature_dim
        self.network = nn.Sequential(nn.Linear(feature_dim, hidden_dim), nn.GELU(), nn.Linear(hidden_dim, 1))
        nn.init.zeros_(self.network[-1].weight)
        nn.init.zeros_(self.network[-1].bias)

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        if features.device.type != "cpu" or any(p.device.type != "cpu" for p in self.parameters()):
            raise ValueError("This bounded implementation accepts CPU only")
        if features.ndim != 2 or features.shape[1] != self.feature_dim or features.shape[0] == 0:
            raise ValueError("Expected actual frozen features [N,D]")
        if features.requires_grad or not features.is_floating_point() or not torch.isfinite(features).all():
            raise ValueError("Features must be finite, floating point and detached")
        if features.dtype != self.network[0].weight.dtype:
            raise ValueError("Feature dtype must match explicitly chosen head dtype")
        return self.network(features).squeeze(-1)


def unit_logits(residual: torch.Tensor, contract: NativeContract, margin: float = 1.0) -> torch.Tensor:
    """Baseline is a binary prior, not a calibrated probability estimate."""
    contract.validate()
    if not math.isfinite(margin) or margin <= 0:
        raise ValueError("Baseline margin must be finite and positive")
    if residual.device.type != "cpu" or residual.ndim != 1 or residual.numel() != contract.feature_count or not residual.is_floating_point() or not torch.isfinite(residual).all():
        raise ValueError("Residual must contain one finite CPU value per actual feature group")
    index = torch.tensor(contract.feature_index, dtype=torch.long)
    sign = torch.tensor(contract.baseline, dtype=residual.dtype) * 2 - 1
    logits = sign * margin + residual[index]
    if not torch.isfinite(logits).all():
        raise ValueError("Baseline prior plus residual overflowed")
    return logits


def native_prediction(residual: torch.Tensor, contract: NativeContract, margin: float = 1.0) -> tuple[bool, ...]:
    """Zero residual reproduces EVERY original frame; ties preserve its prior."""
    logits = unit_logits(residual, contract, margin).detach().tolist()
    selected = tuple(b if z == 0 else z > 0 for z, b in zip(logits, contract.baseline))
    return tuple(selected[u] for u in contract.native_unit)


@dataclass(frozen=True)
class TrainingVideo:
    source_id: str
    features: torch.Tensor
    contract: NativeContract


def train_head(videos: Sequence[TrainingVideo], arm: str, seed: int, *,
               updates: int, hidden_dim: int = 64, learning_rate: float = 1e-3,
               margin: float = 1.0, score_weight: float = 1.0):
    """Explicit bounded full-batch CPU fitting, never called at import time.

    Caller must pre-register data roles/splits, seed, dimensions and hyperparameters.
    This function does not grant scientific/production admission or inspect labels
    outside the supplied training videos. Use matching seed/settings for BCE/SCORE.
    """
    if not videos or isinstance(updates, bool) or not isinstance(updates, int) or not 1 <= updates <= 200:
        raise ValueError("Require actual training videos and 1..200 updates")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
        raise ValueError("A pre-registered nonnegative integer seed is required")
    if not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("Invalid learning rate")
    ids = [v.source_id for v in videos]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Use one complete sample per unique original source")
    for video in videos:
        video.contract.validate()
        if video.features.ndim != 2 or video.features.shape[0] != video.contract.feature_count:
            raise ValueError("Feature count differs from native contract")
    first = videos[0].features
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = ResidualHead(first.shape[1], hidden_dim).to(dtype=first.dtype)
    # Validate before any update and retain exact native baseline identity.
    for video in videos:
        residual = model(video.features)
        if native_prediction(residual, video.contract, margin) != video.contract.baseline_native:
            raise ValueError("Zero-output baseline identity failed")
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.0)
    history = []
    model.train()
    for _ in range(updates):
        optimizer.zero_grad(set_to_none=True)
        losses = [video_losses(unit_logits(model(v.features), v.contract, margin), v.contract) for v in videos]
        objective = macro_objective(losses, arm, score_weight)
        if not torch.isfinite(objective):
            raise ValueError("Nonfinite loss; no empty/fallback result permitted")
        objective.backward()
        if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):
            raise ValueError("Nonfinite gradients")
        optimizer.step()
        history.append(float(objective.detach()))
    if any(not torch.isfinite(p).all() for p in model.parameters()):
        raise ValueError("Nonfinite final head")
    model.eval()
    return model, dict(arm=arm, seed=seed, updates=updates, learning_rate=learning_rate,
                       margin=margin, score_weight=score_weight, objective_history=history,
                       original_source_ids=ids, head_parameters=model.parameter_count,
                       frozen_backbone_parameters=FROZEN_BACKBONE_PARAMETERS,
                       resident_parameters=FROZEN_BACKBONE_PARAMETERS + model.parameter_count,
                       metric_scope="TEMPORAL_PROXY_ONLY_NO_SPATIAL_IOU")
