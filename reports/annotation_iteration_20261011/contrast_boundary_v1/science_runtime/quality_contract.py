"""Exact time-set metrics and fixed source-balanced update objective."""
from fractions import Fraction as F
from math import ceil

def normalize(intervals):
    rows=sorted((F(str(a)),F(str(b))) for a,b in intervals)
    if any(a>=b for a,b in rows):raise ValueError('nonpositive interval')
    out=[]
    for a,b in rows:
        if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
        else:out.append((a,b))
    return out
def duration(intervals):return sum((b-a for a,b in normalize(intervals)),F(0))
def intersection(a,b):
    x,y=normalize(a),normalize(b);out=[];i=j=0
    while i<len(x) and j<len(y):
        lo,hi=max(x[i][0],y[j][0]),min(x[i][1],y[j][1])
        if lo<hi:out.append((lo,hi))
        if x[i][1]<y[j][1]:i+=1
        else:j+=1
    return out
def measure(a,b):return duration(intersection(a,b))
def reference(domain,keep,no,unknown):
    d,k,n,u=map(normalize,(domain,keep,no,unknown))
    if any(measure(a,b)>0 for a,b in ((k,n),(k,u),(n,u))):raise ValueError('reference overlaps')
    if normalize(k+n+u)!=d:raise ValueError('reference does not cover complete declared domain')
    return d,k,n,u
def metrics(domain,keep,no,unknown,prediction):
    d,k,n,u=reference(domain,keep,no,unknown);p=normalize(prediction)
    if intersection(p,d)!=p:raise ValueError('prediction outside declared scope')
    tp,fp,fn=measure(p,k),measure(p,n),duration(k)-measure(p,k)
    kd,ud,pd,pu=duration(k),duration(u),duration(p),measure(p,u)
    positive=kd>0
    f1=2*tp/(2*tp+fp+fn) if positive else None
    low=2*tp/(pd+kd+ud-pu) if positive else None
    high=2*(tp+pu)/(pd+kd+pu) if positive else None
    return dict(tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else F(0) if positive else None,
        recall=tp/kd if positive else None,f1=f1,f1_lower=low,f1_upper=high,
        known_positive_duration=kd,known_no_duration=duration(n),unknown_duration=ud,
        selected_unknown_duration=pu,prediction_duration=pd,
        known_no_false_positive_duration=fp,known_no_false_positive_rate=fp/duration(n) if duration(n)>0 else None)
def conservative_gain(reference_args,p0,p1):
    b=metrics(*reference_args,p0);c=metrics(*reference_args,p1)
    if b['f1'] is None:return None
    if normalize(p0)==normalize(p1):return F(0)
    return c['f1_lower']-b['f1_upper']
def schedule(groups,epochs=2,seed=20261011):
    import random
    n=len(groups);g=len(set(groups))
    if n!=64 or g!=16 or any(groups.count(v)!=4 for v in set(groups)) or epochs!=2 or seed!=20261011:raise ValueError('fixed sample admission differs')
    rng=random.Random(seed);batches=[]
    for epoch in range(epochs):
        order=list(range(n));rng.shuffle(order)
        batches.extend(dict(epoch=epoch,indices=order[start:start+4]) for start in range(0,n,4))
    assert len(batches)==2*ceil(n/4)
    weights=[F(n,g*groups.count(s)) for s in groups]
    return dict(batches=batches,source_weights=weights,window_ce_coefficient=F(ceil(n/4),n),updates=len(batches))
def batch_loss_mean_ce(schedule_record,indices,losses):
    return schedule_record['window_ce_coefficient']*sum(schedule_record['source_weights'][i]*losses[i] for i in indices)

