"""Exhaustive small-domain equivalence, not a model/real-source experiment."""
from itertools import product
import importlib.util
from pathlib import Path

p=Path(__file__).resolve().parents[2]/'improvement/recall_consensus_production_v1/native_no_effect.py'
s=importlib.util.spec_from_file_location('native_no_effect_checked',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

points=[0,5,10,15,19]
views=[dict(view_id='left',start_exact='0',end_exact='15'),dict(view_id='right',start_exact='5',end_exact='20')]
positions=[(v['view_id'],i) for v in views for i,t in enumerate(points) if int(v['start_exact'])<=t<int(v['end_exact'])]
checked=0
for bmask in range(1<<len(points)):
    base={i for i in range(len(points)) if bmask>>i&1}
    plan=m.plan_native_effect(points,20,sorted(base),views);required=set(plan['required_view_ids'])
    for votes in product((False,True),repeat=len(positions)):
        full=dict.fromkeys(range(len(points)),0);retained=full.copy()
        for (view_id,i),keep in zip(positions,votes):
            if keep:
                full[i]+=1
                if view_id in required:retained[i]+=1
        assert base|{i for i,c in full.items() if c>=2}==base|{i for i,c in retained.items() if c>=2}
        checked+=1
assert checked==4096
short=m.plan_native_effect([0,1,2],3,[],[dict(view_id='single',start_exact=0,end_exact=3)])
assert not short['required_view_ids'] and len(short['omitted'])==1
protected=m.plan_native_effect(points,20,[1,2],views)
assert not protected['required_view_ids'] and len(protected['omitted'])==2
tail=[dict(view_id=str(i),start_exact=str(a),end_exact=str(b)) for i,(a,b) in enumerate(sorted(m.full_grid('151/5')))]
triple=m.plan_native_effect([0,8,16,20,25,30],'151/5',[],tail)
assert max(triple['complete_full_grid_coverage'])==3
assert len(set(triple['required_view_ids']))==4
for bad in [views[:1],views+[dict(view_id='alias',start_exact='0/1',end_exact=15)]]:
    try:m.plan_native_effect(points,20,[],bad)
    except ValueError:pass
    else:raise AssertionError('Missing grid/duplicate geometry was accepted')
try:m.plan_native_effect(points,20,[True],views)
except ValueError:pass
else:raise AssertionError('Bool baseline ordinal was accepted')
print('PASS:4096 exhaustive native-output assignments; single-view/protected-overlap/triple-tail; missing/aliased/bool rejection. Real data, model and production calls:0.')
