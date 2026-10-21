"""Exact source-count-conditioned window programs, no data/model interface.

Cardinality is projected to the nearest reachable native count using no labels;
ties prefer the lower count. All windows choose one existing complete answer.
"""
import math
import numpy as np


def validate(lengths,logits):
    if not lengths or len(lengths)!=len(logits):raise ValueError('Complete windows required')
    for counts,scores in zip(lengths,logits):
        if not counts or len(counts)!=len(scores)or any(type(n)is not int or n<0 for n in counts)or not np.isfinite(scores).all():
            raise ValueError('Native nonnegative counts and finite answer logp required')


def project_budget(lengths,budget):
    if type(budget)is not int or budget<0:raise ValueError('Native count budget required')
    support={0}
    for counts in lengths:
        if not counts or any(type(n)is not int or n<0 for n in counts):raise ValueError('Native action counts')
        support={a+b for a in support for b in counts}
    return min(support,key=lambda n:(abs(n-budget),n)),len(support)


def best_program(lengths,scores,budget,baseline_overlap=None):
    """Exact fixed-count max; ties maximize baseline overlap then reverse slots."""
    validate(lengths,scores)
    if baseline_overlap is None:baseline_overlap=[[0]*len(c)for c in lengths]
    if len(baseline_overlap)!=len(lengths)or any(len(a)!=len(b)for a,b in zip(lengths,baseline_overlap)):
        raise ValueError('Complete unlabeled baseline-overlap tie data')
    v=np.full(budget+1,-np.inf);v[0]=0.;keep=np.full(budget+1,-1,dtype=np.int64);keep[0]=0;parents=[]
    for counts,row,overlaps in zip(lengths,scores,baseline_overlap):
        nv=np.full_like(v,-np.inf);nk=np.full_like(keep,-1);parent=np.full(budget+1,-1,dtype=np.int32)
        for j,(n,score,overlap)in enumerate(zip(counts,row,overlaps)):
            if n>budget:continue
            size=budget-n+1;candidate=v[:size]+score;secondary=keep[:size]+overlap
            mask=np.isfinite(v[:size])&((candidate>nv[n:])|((candidate==nv[n:])&(secondary>nk[n:])))
            nv[n:][mask]=candidate[mask];nk[n:][mask]=secondary[mask];parent[n:][mask]=j
        v,keep=nv,nk;parents.append(parent)
    if not np.isfinite(v[budget]):raise ValueError('Unreachable count, no fallback output')
    point=budget;choices=[]
    for counts,parent in reversed(list(zip(lengths,parents))):
        j=int(parent[point]);assert j>=0;choices.append(j);point-=counts[j]
    assert point==0;choices.reverse()
    return choices,float(v[budget]),int(keep[budget])


def conditional(lengths,logits,budget,target=None):
    """Stable log-count forward/backward and exact conditional-NLL derivatives."""
    validate(lengths,logits)
    def advance(prev,counts,scores):
        out=np.full(budget+1,-np.inf)
        for n,score in zip(counts,scores):
            if n<=budget:out[n:]=np.logaddexp(out[n:],prev[:budget-n+1]+score)
        return out
    init=np.full(budget+1,-np.inf);init[0]=0.;forward=[init]
    for c,l in zip(lengths,logits):forward.append(advance(forward[-1],c,l))
    z=float(forward[-1][budget])
    if not math.isfinite(z):raise ValueError('No feasible conditional programs')
    backward=[None]*(len(lengths)+1);backward[-1]=init
    for w in range(len(lengths)-1,-1,-1):backward[w]=advance(backward[w+1],lengths[w],logits[w])
    marginals=[]
    for w,(counts,scores)in enumerate(zip(lengths,logits)):
        values=[]
        for n,score in zip(counts,scores):
            if n>budget:values.append(0.);continue
            terms=forward[w][:budget-n+1]+backward[w+1][:budget-n+1][::-1]+score
            finite=terms[np.isfinite(terms)]
            if not len(finite):values.append(0.);continue
            peak=float(finite.max());mass=peak+math.log(float(np.exp(finite-peak).sum()));values.append(math.exp(mass-z))
        if abs(sum(values)-1)>1e-9:raise AssertionError('Conditional window marginal mass')
        marginals.append(np.asarray(values))
    result=dict(log_partition=z,marginals=[v.tolist()for v in marginals])
    if target is not None:
        if len(target)!=len(lengths)or sum(c[j]for c,j in zip(lengths,target))!=budget:raise ValueError('Feasible complete target')
        loss=z-sum(l[j]for l,j in zip(logits,target))
        if loss < -1e-9:raise AssertionError('Nonnegative conditional NLL')
        gradient=[q-np.eye(len(q))[j]for q,j in zip(marginals,target)]
        result.update(NLL=max(0.,float(loss)),gradient=[v.tolist()for v in gradient],gradient_L1=float(sum(np.abs(v).sum()for v in gradient)))
    return result
