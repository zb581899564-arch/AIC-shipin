"""Temporal proxy losses only. No spatial IoU or official joint-score claim."""
from dataclasses import dataclass
from math import fsum, isfinite
from typing import Optional, Sequence
import torch
from torch.nn import functional as F

try:
    from .contracts import NativeContract
except ImportError:
    from contracts import NativeContract


@dataclass(frozen=True)
class VideoLoss:
    bce: Optional[torch.Tensor]
    score_loss: Optional[torch.Tensor]
    soft_f1: Optional[torch.Tensor]
    scope: str
    reference_kind: str


def video_losses(logits: torch.Tensor, contract: NativeContract) -> VideoLoss:
    """Known-frame weighting is identical in BCE and soft-F1 numerator/denominator.

    An empty KNOWN region has a mean-selection penalty, never epsilon-generated
    perfect F1. With partial labels this remains a masked proxy, not a complete
    empty-video claim. An all-UNKNOWN video contributes to neither objective.
    """
    contract.validate()
    if logits.device.type != "cpu" or logits.ndim != 1 or logits.numel() != len(contract.n) or not logits.is_floating_point() or not torch.isfinite(logits).all():
        raise ValueError("Expected finite CPU logits per native unit")
    known = torch.tensor(contract.known_n, dtype=logits.dtype)
    c = torch.tensor(contract.c, dtype=logits.dtype)
    if not sum(contract.known_n):
        return VideoLoss(None, None, None, contract.reference_scope, "UNKNOWN")
    active = known > 0
    known_active, c_active, z = known[active], c[active], logits[active]
    target = c_active / known_active
    bce = (F.binary_cross_entropy_with_logits(z, target, reduction="none") * known_active).sum() / known_active.sum()
    p = z.sigmoid()
    selected_mass = (p * known_active).sum()
    reference_mass = c_active.sum()
    if fsum(contract.c) == 0:
        return VideoLoss(bce, selected_mass / known_active.sum(), None, contract.reference_scope,
                         "COMPLETE_EMPTY" if contract.complete_empty_reference else "MASKED_EMPTY_REGION")
    soft_f1 = 2 * (p * c_active).sum() / (selected_mass + reference_mass)
    return VideoLoss(bce, 1-soft_f1, soft_f1, contract.reference_scope, "NONEMPTY")


def macro_objective(videos: Sequence[VideoLoss], arm: str, score_weight: float = 1.0) -> torch.Tensor:
    """Each known video has equal weight, independently of native duration/FPS."""
    if arm not in ("BCE", "SCORE") or not isfinite(score_weight) or score_weight < 0:
        raise ValueError("Unregistered objective or invalid score weight")
    terms = []
    for video in videos:
        if video.bce is not None:
            terms.append(video.bce if arm == "BCE" else video.bce + score_weight * video.score_loss)
    if not terms:
        raise ValueError("No known reference: no training update is permitted")
    return torch.stack(terms).mean()


def hard_temporal_metrics(prediction: Sequence[bool], reference: Sequence[Optional[float]]) -> dict:
    """Hard-reference native-frame proxy; empty-reference status is explicit."""
    pred, ref = tuple(prediction), tuple(reference)
    if not pred or len(pred) != len(ref) or any(type(p) is not bool for p in pred):
        raise ValueError("Complete boolean native prediction required")
    if any(x is not None and (type(x) is bool or x not in (0, 1)) for x in ref):
        raise ValueError("Hard metrics require binary reference; soft labels stay soft")
    known = [(p, r) for p, r in zip(pred, ref) if r is not None]
    scope = "UNKNOWN" if not known else ("FULL" if len(known) == len(ref) else "MASKED")
    tp = sum(p and r == 1 for p, r in known)
    fp = sum(p and r == 0 for p, r in known)
    fn = sum(not p and r == 1 for p, r in known)
    has_positive = tp + fn > 0
    return dict(scope=scope, known_frames=len(known), tp=tp, fp=fp, fn=fn,
                temporal_f1=2*tp/(2*tp+fp+fn) if has_positive else None,
                empty_reference=(not has_positive) if known else None,
                empty_match=(fp == 0) if known and not has_positive else None,
                metric_scope="TEMPORAL_PROXY_ONLY_NO_SPATIAL_IOU")
