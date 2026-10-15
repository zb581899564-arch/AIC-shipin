"""The frozen D2/D4/D8 rules, calculated once from original segment endpoints."""
from fractions import Fraction as F

THRESHOLDS={'D2':F(2),'D4':F(4),'D8':F(8)}

def spans(windows,minimum_length=None):
    result=[]
    for window in windows:
        origin,limit=F(window['start_exact']),F(window['end_exact'])
        for first,last in window['segments']:
            first,last=F(str(first)),F(str(last))
            if not 0<=first<last<=limit-origin:
                raise ValueError('Original temporal interval is outside its source window')
            post=F(1,2)
            if minimum_length is not None and last-first>=minimum_length:post+=F(1,4)
            left,right=max(origin,origin+first-F(3,4)),min(limit,origin+last+post)
            if left<right:result.append((left,right))
    return result
