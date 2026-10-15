"""Exact native sampling domains and unchanged training prompt; no inference."""
from bisect import bisect_left
from fractions import Fraction
def grid(points,start,end):
    assert all(isinstance(p,Fraction) for p in points)
    start,end=Fraction(start),Fraction(end)
    assert 0<=start<end and all(b>a for a,b in zip(points,points[1:]))
    first,stop=bisect_left(points,start),bisect_left(points,end)
    assert 0<=first<stop<=len(points)
    cursor=first;edge=start;result=[]
    while cursor<stop:
        right=min(edge+2,end);a=cursor
        while cursor<stop and points[cursor]<right:cursor+=1
        assert cursor>a,'empty sampling bin; no silent skip'
        ordinal=(a+cursor-1)//2
        result.append({'grid_index':len(result),'first_native_ordinal':a,'end_native_ordinal_exclusive':cursor,
          'sample_native_ordinal':ordinal,'sample_seconds':float(points[ordinal]),
          'start_exact':str(edge),'end_exact':str(right)})
        edge+=2
    assert result[0]['first_native_ordinal']==first and result[-1]['end_native_ordinal_exclusive']==stop
    assert all(a['end_native_ordinal_exclusive']==b['first_native_ordinal'] for a,b in zip(result,result[1:]))
    return result
def prompt(sequence):
    assert 1<=len(sequence)<=16
    descriptors='\n'.join(f'Frame {i}: native ordinal {s["sample_native_ordinal"]}, time {s["sample_seconds"]:.6f} s.' for i,s in enumerate(sequence))
    return ('Rate the visual importance of each shown frame within this ordered video sequence. '
      'Use TVSum average importance: 1 low, 3 medium, 5 high. '
      'Encode the average multiplied by 20 as an integer 20..100, preserving 0.05-point precision. '
      'Return ONLY JSON {"scores_x20":[...]} with exactly one integer per shown frame in the same order. '
      'Divide each output by 20 to recover average importance. '
      'This is sampled-frame importance, not semantic event start/end detection.\n'+descriptors)
def selftest():
    import json,numpy as np
    from pathlib import Path
    h=Path(__file__).resolve().parent;old=h.parent/'qwen8b_annotation_20261009_v1/training_v2'
    original=[json.loads(s) for s in (old/'fixed_grid_samples.jsonl').read_text().splitlines()]
    targets=[json.loads(s) for s in (old/'data/temporal_fixed_validation.jsonl').read_text().splitlines()]
    for sid in sorted({r['source_id'] for r in targets}):
        root=old.parent/'input'/sid;m=json.loads((root/'manifest.json').read_text());tb=Fraction(*m['native_time_base'])
        pts=np.load(root/'native_pts.npz')['pts'];points=[(int(p)-int(pts[0]))*tb for p in pts]
        actual=grid(points,0,Fraction(str(m['source_duration_seconds'])))
        expected=[r for r in original if r['source_id']==sid]
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected):
            assert all(a[k]==b[k] for k in ('grid_index','first_native_ordinal','end_native_ordinal_exclusive','sample_native_ordinal','sample_seconds'))
        for t in (r for r in targets if r['source_id']==sid):
            seq=[actual[i] for i in t['grid_indices']]
            assert '<image>\n'*len(seq)+prompt(seq)==t['messages'][0]['content']
    print('PASS nine-source exact training-grid and all 89 prompt identities')
if __name__=='__main__':selftest()
