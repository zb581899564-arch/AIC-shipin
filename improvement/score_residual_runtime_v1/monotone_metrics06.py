"""Full-rater temporal soft-F1; fixed original selection, learn additions only."""
import torch
from torch.nn import functional as F
from score_residual_head_v1.metrics import VideoLoss

def video_losses(logits,contract,rater_counts):
    contract.validate()
    if contract.reference_scope!='FULL':raise ValueError('This SumMe recipe requires full known original rater references; UNKNOWN is not zero')
    n=torch.tensor(contract.n,dtype=logits.dtype)
    base=torch.tensor(contract.baseline,dtype=torch.bool)
    counts=rater_counts.to(dtype=logits.dtype)
    if counts.ndim!=2 or counts.shape[0]!=len(n) or not torch.isfinite(counts).all() or bool((counts<0).any()) or bool((counts>n[:,None]).any()):raise ValueError('Original per-rater native counts')
    if not torch.allclose(counts.mean(1),torch.tensor(contract.c,dtype=logits.dtype),atol=2e-5,rtol=1e-6):raise ValueError('Per-rater and original soft target mismatch')
    free=~base
    # Never evaluate BCE at p_B=1; irreducible baseline errors are outside actions.
    zero=logits.sum()*0
    if bool(free.any()):
        target=counts[free].mean(1)/n[free]
        bce=(F.binary_cross_entropy_with_logits(logits[free],target,reduction='none')*n[free]).sum()/n[free].sum()
    else:bce=zero
    p=torch.where(base,torch.ones_like(logits),logits.sigmoid())
    selected=(p*n).sum();totals=counts.sum(0);intersection=(p[:,None]*counts).sum(0)
    nonempty=totals>0
    scores=torch.zeros_like(totals)
    scores[nonempty]=2*intersection[nonempty]/(selected+totals[nonempty])
    losses=torch.empty_like(totals)
    losses[nonempty]=1-scores[nonempty]
    # Empty raters use an explicit selection penalty, not fabricated perfect F1.
    losses[~nonempty]=selected/n.sum()
    score_loss=losses.mean()+zero
    return VideoLoss(bce,score_loss,scores[nonempty].mean() if bool(nonempty.any()) else None,'FULL','MULTIRATER_FIXED_BASELINE_ADDITIONS')
