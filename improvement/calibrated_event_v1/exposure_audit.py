"""One fixed coverage-matched diagnostic; never a delivery threshold search."""
import sys
from pathlib import Path
sys.path.insert(0,'/home/inspur/aic_video_work/calibrated_event_20261018_v1/code_v1')
from calibrate import *


def main():
    old=read(EVENT/'semantic_event_01/adopted_evaluation.json');controls={v['sid']:v for v in old['sources']if v['group']=='check'}
    budget=sum(v['added_frames']for v in controls.values());items=[]
    for s in read(EVENT/'registration.json')['sources']:
        if s['group']!='check':continue
        d=load_source(s);out=np.load(ROOT/'development_01'/(s['sid']+'_output.npz'));gain=out['estimated_gain'];idx=None if not len(gain)or gain.max()<=0 else int(gain.argmax());action=None if idx is None else dict(sid=s['sid'],candidate_index=idx,added_frames=d['candidates'][idx]['added_frames'],predicted_gain=float(gain[idx]));items.append(dict(d=d,action=action))
    chosen=knapsack([v['action']for v in items if v['action']],budget);rows=[]
    for v in items:
        d=v['d'];mask=d['baseline'].copy()
        if d['sid']in chosen:
            c=d['candidates'][v['action']['candidate_index']];mask[c['left']:c['right']]=True
        b,n=metric(d['baseline'],d['labels']),metric(mask,d['labels']);added=mask&~d['baseline'];ctrl=controls[d['sid']];old_added=ctrl['added_frames'];old_precision=None if old_added==0 else (ctrl['candidate']['precision']*ctrl['candidate']['selected']-ctrl['baseline']['precision']*ctrl['baseline']['selected'])/old_added
        rows.append(dict(sid=d['sid'],baseline=b,candidate=n,delta=n['f1']-b['f1'],added_frames=int(added.sum()),added_precision=None if not added.any()else float(d['labels'][added].mean()),original_control_added_frames=old_added,original_control_added_precision=old_precision))
    save(ROOT/'matched_exposure_diagnostic_02.json',dict(status='ONE_MATCHED_EXPOSURE_AUDIT_NOT_A_PRODUCTION_THRESHOLD',budget_derived_from_previous_control=budget,actual_added_frames=sum(v['added_frames']for v in rows),macro_delta=float(np.mean([v['delta']for v in rows])),original_semantic_delta=old['summary']['check']['macro_delta'],original_production_budget_unchanged=True,no_model_refit=True,sources=rows,utc=utc()))
    print(json.dumps(dict(budget=budget,actual_added_frames=sum(v['added_frames']for v in rows),macro_delta=float(np.mean([v['delta']for v in rows])))),flush=True)


if __name__=='__main__':main()
