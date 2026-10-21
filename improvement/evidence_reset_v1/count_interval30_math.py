"""Count-interval certificates over unchanged full native program space."""
import heapq
import math
import time
import numpy as np


def reachable_counts(lengths):
    ways={0:1}
    for row in lengths:
        nxt={}
        for P,count in ways.items():
            for n in row:nxt[P+n]=nxt.get(P+n,0)+count
        ways=nxt
    return ways


def range_program(lengths,weights,lower,upper,overlaps):
    """Exact additive multiple-choice DP for any final count in[L,U]."""
    v=np.full(upper+1,-np.inf);v[0]=0.;keep=np.full(upper+1,-1,dtype=np.int64);keep[0]=0;parents=[]
    for counts,scores,retained in zip(lengths,weights,overlaps):
        nv=np.full_like(v,-np.inf);nk=np.full_like(keep,-1);parent=np.full(upper+1,-1,dtype=np.int16)
        for j,(n,score,overlap)in enumerate(zip(counts,scores,retained)):
            if n>upper:continue
            q=upper-n+1;candidate=v[:q]+score;secondary=keep[:q]+overlap
            mask=np.isfinite(v[:q])&((candidate>nv[n:])|((candidate==nv[n:])&(secondary>nk[n:])))
            nv[n:][mask]=candidate[mask];nk[n:][mask]=secondary[mask];parent[n:][mask]=j
        v,keep=nv,nk;parents.append(parent)
    points=np.flatnonzero(np.isfinite(v[lower:]))+lower
    if not len(points):raise ValueError('No native program in requested count interval')
    maximum=float(v[points].max());points=points[v[points]==maximum];best=int(points[np.argmax(keep[points])]);point=best;choices=[]
    for row,parent in reversed(list(zip(lengths,parents))):
        j=int(parent[point]);assert j>=0;choices.append(j);point-=row[j]
    assert point==0;choices.reverse()
    return choices,maximum,int(keep[best])


def source_utility(lengths,tp,gt,choice):
    gt=np.asarray(gt,dtype=np.int64);P=sum(lengths[w][j]for w,j in enumerate(choice))
    TP=sum((np.asarray(tp[w][j],dtype=np.int64)for w,j in enumerate(choice)),start=np.zeros(len(gt),dtype=np.int64));den=P+gt
    value=float(np.divide(2.*TP,den,out=np.ones_like(TP,dtype=float),where=den!=0).mean())
    return value,P


def certify(lengths,tp,gt,baseline,overlaps,deadline=None,tolerance=1e-10,max_nodes=25000):
    """Return a feasible witness and count-interval upper-bound certificate.

    For P in[L,U], every nonempty-rater denominator is >=L+G.
    Thus additive gains using L upper-bound that entire interval. P=0 is
    evaluated separately before positive-count nodes. No program/count is
    dropped; the declared finite precision margin is not a formal interval proof.
    """
    gt=np.asarray(gt,dtype=np.int64);assert len(gt)>0 and(gt>=0).all()
    assert len(lengths)==len(tp)==len(overlaps)==len(baseline)and len(lengths)<=32 and len(gt)<=100
    for counts,tps,kk in zip(lengths,tp,overlaps):
        assert len(counts)==len(tps)==len(kk)and len(counts)>0
        for n,t in zip(counts,tps):
            t=np.asarray(t);assert type(n)is int and n>=0 and t.shape==gt.shape and(t>=0).all()and(t<=gt).all()and(t<=n).all()
    positives=sum((np.asarray(row,dtype=np.int64).max(axis=0)for row in tp),start=np.zeros_like(gt))
    assert(positives<=gt).all(),'Disjoint source windows cannot contain more positives than complete-source GT'
    assert sum(max(row)for row in lengths)<2**53 and int(gt.max())<2**53
    ways=reachable_counts(lengths);support=sorted(ways);best=list(baseline);best_value,best_count=source_utility(lengths,tp,gt,best)
    best_keep=sum(row[j]for row,j in zip(overlaps,best));queue=[];serial=0;nodes=0;largest_pruned=-math.inf
    padding=1e-10;tp_arrays=[np.asarray(row,dtype=float)for row in tp]
    # Conservative operation-count check for the stated small finite domain.
    unit=np.finfo(float).eps/2;operations=8*(len(gt)+len(lengths)+1)
    error_estimate=operations*unit/(1-operations*unit)*(2*len(lengths)+1)
    assert error_estimate<padding
    def bound(left,right):
        nonlocal best,best_value,best_count,best_keep,serial,nodes,largest_pruned
        if deadline is not None and time.monotonic()>deadline:raise TimeoutError('Frozen CPU budget, no approximate fallback')
        if nodes>=max_nodes:raise RuntimeError('Frozen node budget, support remains undecided')
        lo,hi=support[left],support[right];den=lo+gt
        weights=[np.divide(2*t,den[None,:],out=np.zeros_like(t),where=den[None,:]!=0).mean(axis=1)for t in tp_arrays]
        choice,value,retained=range_program(lengths,weights,lo,hi,overlaps);nodes+=1
        actual,P=source_utility(lengths,tp,gt,choice)
        if actual>best_value or(actual==best_value and retained>best_keep):best,best_value,best_count,best_keep=choice,actual,P,retained
        upper=min(1.,value+padding)
        if left==right:
            # At a singleton the DP denominator is exact; preserve roundoff bound.
            upper=min(upper,actual+padding)
        assert upper+padding>=actual
        if upper<=best_value+tolerance or left==right:largest_pruned=max(largest_pruned,upper)
        else:serial+=1;heapq.heappush(queue,(-upper,serial,left,right))
    first=0
    if support[0]==0:
        empty_choice=[row.index(0)for row in lengths];empty_value,unused=source_utility(lengths,tp,gt,empty_choice)
        if empty_value>best_value:best,best_value,best_count,best_keep=empty_choice,empty_value,0,0
        first=1
    if first<len(support):bound(first,len(support)-1)
    while queue:
        negative,unused,left,right=heapq.heappop(queue);upper=-negative
        if upper<=best_value+tolerance:largest_pruned=max(largest_pruned,upper);continue
        middle=(left+right)//2;bound(left,middle);bound(middle+1,right)
    upper=max(best_value,largest_pruned);gap=max(0.,upper-best_value)
    assert gap<=tolerance+1e-12
    return dict(choices=best,witness_F1=best_value,witness_frames=best_count,retained_baseline_frames=best_keep,
        upper_bound=upper,certified_gap=gap,absolute_roundoff_padding=padding,count_interval_DP_nodes=nodes,
        finite_domain_roundoff_estimate=error_estimate,certificate_kind='DECLARED_NUMERICAL_MARGIN_NOT_FORMAL_INTERVAL_ARITHMETIC',
        reachable_count_values=len(support),native_programs=sum(ways.values()),same_baseline_count_programs=ways[sum(row[j]for row,j in zip(lengths,baseline))],
        all_optimal_native_programs_enumerated=False)
