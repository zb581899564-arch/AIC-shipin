"""Exact finite-program task-loss inference; external reference data only."""
import itertools
import math
import numpy as np


def enumerate_programs(lengths,tp,gt,limit=2000000):
    counts=[len(r)for r in lengths];size=math.prod(counts)
    if not counts or any(n==0 for n in counts)or size>limit:raise ValueError('Exact native program enumeration exceeds frozen scope')
    choices=np.asarray(list(itertools.product(*(range(n)for n in counts))),dtype=np.int16)
    P=sum((np.asarray(row,dtype=np.int64)[choices[:,w]]for w,row in enumerate(lengths)),start=np.zeros(size,dtype=np.int64))
    TP=sum((np.asarray(row,dtype=np.int64)[choices[:,w]]for w,row in enumerate(tp)),start=np.zeros((size,len(gt)),dtype=np.int64))
    gt=np.asarray(gt,dtype=np.int64);den=P[:,None]+gt
    utility=np.divide(2.*TP,den,out=np.ones_like(TP,dtype=float),where=den!=0).mean(axis=1)
    if not np.isfinite(utility).all()or(utility<0).any()or(utility>1).any():raise ValueError('Bounded all-reviewer source utility')
    return choices,P,utility


def structured_loss(choices,utility,logits,retained=None):
    """Latent reference-optimal max-margin loss, unit F1 task cost.

    L=max_a(s(a)+U*-U(a))-max_{a:U(a)=U*}s(a).
    Maxima share exactly the deployment program space. Native-equivalent text
    variants may be included; equal utility does not impose lexical preference.
    This is piecewise differentiable, not claimed globally convex.
    """
    utility=np.asarray(utility,dtype=float);choices=np.asarray(choices,dtype=np.int64)
    assert choices.ndim==2 and len(choices)==len(utility)and len(logits)==choices.shape[1]
    scores=sum((np.asarray(row,dtype=float)[choices[:,w]]for w,row in enumerate(logits)),start=np.zeros(len(choices)))
    assert np.isfinite(scores).all()and np.isfinite(utility).all()
    overlap=np.zeros(len(scores),dtype=np.int64)if retained is None else np.asarray(retained,dtype=np.int64)
    def winner(values,allowed=None):
        possible=np.arange(len(scores))if allowed is None else np.flatnonzero(allowed)
        best=float(values[possible].max());possible=possible[values[possible]==best]
        return int(possible[np.argmax(overlap[possible])])
    U=float(utility.max());gold=winner(scores,utility==U);cost=U-utility;violator=winner(scores+cost);prediction=winner(scores)
    loss=float(scores[violator]+cost[violator]-scores[gold]);assert loss>=-1e-12
    gradient=[np.zeros(len(row),dtype=float)for row in logits]
    for w in range(choices.shape[1]):gradient[w][choices[violator,w]]+=1;gradient[w][choices[gold,w]]-=1
    return dict(loss=max(0.,loss),oracle_utility=U,gold_index=gold,violator_index=violator,prediction_index=prediction,
        prediction_utility=float(utility[prediction]),gradient=[g.tolist()for g in gradient])
