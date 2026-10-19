"""One fixed source-balanced ridge on complete-baseline marginal utility."""
from sr_common import *
from fractions import Fraction as F
from bisect import bisect_left

def candidates(hidden,score,baseline,groups):
    import numpy as np
    n=len(baseline);cells=len(hidden);all_count=np.bincount(groups,minlength=cells)
    added_count=np.bincount(groups,weights=(~baseline).astype(np.float64),minlength=cells)
    occ=(all_count-added_count)/all_count
    x=np.column_stack([hidden.astype(np.float64),score.astype(np.float64),occ,np.full(cells,float(baseline.mean())),added_count/n])
    require(x.shape==(cells,12)and np.isfinite(x).all(),'Bounded12-dimensional incremental features')
    return x,added_count>0

def utility_targets(baseline,groups,labels,cells):
    import numpy as np
    require(labels.dtype==np.bool_ and labels.shape[0]==len(baseline) and labels.ndim==2,'Native original all-rater label domain')
    g=labels.sum(0,dtype=np.float64);b=float(baseline.sum());tp=(labels & baseline[:,None]).sum(0,dtype=np.float64)
    extra=np.bincount(groups,weights=(~baseline).astype(float),minlength=cells);counts=np.zeros((cells,labels.shape[1]),np.float64)
    np.add.at(counts,groups,labels & (~baseline)[:,None])
    require(np.all(g>0),'Original reviewers must have a selected summary')
    return (2*(tp[None,:]+counts)/(b+extra[:,None]+g[None,:])-2*tp/(b+g)).mean(1)

def metric(mask,labels):
    import numpy as np
    count=int(mask.sum());gt=labels.sum(0);tp=(labels&mask[:,None]).sum(0)
    return dict(f1=float(np.mean(2*tp/np.maximum(1,count+gt))),precision=float(np.mean(tp/max(1,count))),recall=float(np.mean(tp/np.maximum(1,gt))),selected=count)

def predict(x,eligible,model):
    import numpy as np
    value=((x-model['mean'])/model['std'])@model['coef']+float(model['bias'])
    require(np.isfinite(value).all(),'Finite new utility prediction')
    choices=np.flatnonzero(eligible)
    if not len(choices):return None,value
    best=int(choices[np.argmax(value[choices])]) # Deterministic first cell at exact tie.
    return (best if value[best]>0 else None),value

def original_labels(source,clock):
    import numpy as np
    if source['group']=='train':return np.load(bound(source['labels_ref']))>0
    row=read(bound(source['reference_ref']));require(len(row)==1 and row[0]['video_id']==source['name'],'Original reference source binding')
    raters=row[0]['annotator_intervals_exact_seconds'];require(len(raters)==10,'All original10 video summary reviewers')
    pts=list(map(F,clock['normalized_exact_pts']));end=F(clock['physical_end_exact']);labels=np.zeros((len(pts),10),bool)
    for j,segments in enumerate(raters):
        for a,b in segments:
            a,b=F(a),F(b);require(0<=a<b<=end,'No clipping/stretching original human intervals')
            labels[bisect_left(pts,a):bisect_left(pts,b),j]=True
    return labels

def external_source(source,reg,decisions):
    import numpy as np
    sid=source['sid'];folder=ROOT/'external'/sid;folder.mkdir(parents=True,exist_ok=False)
    clock=read(ROOT/'inputs'/sid/'clock.json');pts=list(map(F,clock['normalized_exact_pts']));verify=np.zeros(len(pts),bool);b0=np.zeros(len(pts),bool)
    for w in reg['windows']:
        if w['sid']!=sid:continue
        lo,hi=map(F,(w['meta']['window_start'],w['meta']['window_end']))
        for e in w['events']:
            a,b=map(F,e['original_interval_exact']);tail=F(1,2)+(F(1,4)if b-a>=8 else 0);a,b=max(lo,a-F(3,4)),min(hi,b+tail)
            left,right=bisect_left(pts,a),bisect_left(pts,b);require(left<right,'Actual D8 event contains native frames')
            b0[left:right]=True
            require(e['event_id']in decisions,'Missing VERIFY cannot become UNKNOWN')
            if decisions[e['event_id']]!='DROP':verify[left:right]=True
    if source['group']=='train':
        old=np.load(bound(source['native_ref']));groups=old['groups'];language=np.load(bound(source['language_ref']))
    else:
        groups=np.load(ROOT/'inputs'/sid/'native.npz')['groups'];language=np.load(ROOT/'features'/sid/'language.npy')
    require(len(groups)==len(pts)and groups.min()==0 and groups.max()+1==len(language),'Actual native groups cover semantic features')
    hidden,score,baseline=semantic(language,verify,groups)
    # New utility readout is conditioned on COMPLETE current selection, while
    # frozen semantic hidden/score uses its original pre-semantic VERIFY input.
    x,eligible=candidates(hidden,score,baseline,groups);labels=original_labels(source,clock)
    require(labels.shape[0]==len(pts),'Human labels must match inherited native clock exactly')
    y=utility_targets(baseline,groups,labels,len(hidden))
    np.savez(folder/'data.npz',x=x,eligible=eligible,target=y,baseline=baseline,groups=groups,labels=labels,semantic_score=score)
    info=dict(sid=sid,name=source['name'],group=source['group'],native_frames=len(pts),cells=len(hidden),candidates=int(eligible.sum()),B0_D8=metric(b0,labels),VERIFY=metric(verify,labels),complete40_47_policy=metric(baseline,labels),label_raters=labels.shape[1],historical_exposure=True)
    save(folder/'completion.json',info);return dict(x=x,eligible=eligible,target=y,baseline=baseline,groups=groups,labels=labels,info=info,semantic_score=score)

def fit_model(data):
    import numpy as np
    train=[d for d in data if d['info']['group']=='train'];require(len(train)==25,'Exactly25 public training sources')
    xs=[];ys=[];weights=[]
    for d in train:
        k=int(d['eligible'].sum())
        if not k:continue
        xs.append(d['x'][d['eligible']]);ys.append(d['target'][d['eligible']]);weights.append(np.full(k,1/k))
    require(xs,'No source with a valid incremental training candidate')
    x=np.concatenate(xs);y=np.concatenate(ys);w=np.concatenate(weights)
    mean=(x*w[:,None]).sum(0)/w.sum();std=np.sqrt(((x-mean)**2*w[:,None]).sum(0)/w.sum());std=np.where(std<1e-6,1.,std)
    z=(x-mean)/std;z=np.column_stack([z,np.ones(len(z))]);penalty=np.eye(13);penalty[-1,-1]=0.
    beta=np.linalg.solve(z.T@(w[:,None]*z)+penalty,z.T@(w*y))
    require(np.isfinite(beta).all(),'Finite unique ridge solution')
    model=dict(mean=mean,std=std,coef=beta[:12],bias=beta[12]);np.savez(ROOT/'utility_head.npz',**model)
    restored=dict(np.load(ROOT/'utility_head.npz'));require(all(np.array_equal(v,restored[k])for k,v in model.items()),'Actual learned coefficients save/reload')
    save(ROOT/'frozen_selection.json',dict(status='FROZEN_SINGLE_RIDGE_NO_THRESHOLD_SEARCH',train_source_ids=[d['info']['sid']for d in train],check_source_ids=[d['info']['sid']for d in data if d['info']['group']=='check'],ridge_alpha=1.,input_dim=12,learned_tensor_scalars=37,null_utility=0.,max_cells_per_source=1,weights_ref=ref(ROOT/'utility_head.npz'),official_data_or_scores_used=False,utc=utc()))
    return model

def main():
    cpu();import numpy as np
    import torch
    torch.set_num_threads(2)
    require(read(ROOT/'output_qa.json')['status']=='PASS_FIRST_INDEPENDENT_ALL_EXTERNAL_TOKEN_CONTEXT_REPLAY','First complete independent output QA')
    require(read(ROOT/'original_human_label_adoption.json')['status']=='PASS25_ADOPTED_ORIGINAL_AUTHOR_HUMAN_LABEL_BYTES','Adopt original author human supervision, not unknown old teacher labels')
    reg=read(ROOT/'registration.json');decisions=read(ROOT/'decisions.json');data=[]
    for s in reg['sources']:
        # Check labels are not read until AFTER this new fit is frozen.
        if s['group']=='train':data.append(external_source(s,reg,decisions))
    # Register check membership without looking at its target/metric values.
    dummy=[dict(info=dict(sid=s['sid'],group='check'))for s in reg['sources']if s['group']=='check']
    model=fit_model(data+dummy)
    for s in reg['sources']:
        if s['group']=='check':data.append(external_source(s,reg,decisions))
    results=[]
    for d in data:
        best,values=predict(d['x'],d['eligible'],model);mask=d['baseline'].copy()
        if best is not None:mask |= d['groups']==best
        b=metric(d['baseline'],d['labels']);n=metric(mask,d['labels']);extra=mask&~d['baseline'];changed=int(extra.sum())
        require(not np.any(d['baseline']&~mask),'Protected baseline retention')
        # Single frozen semantic score ordering control, not a competing fit.
        choices=np.flatnonzero(d['eligible']);control=None if not len(choices)else int(choices[np.argmax(d['semantic_score'][choices])]);controlmask=d['baseline'].copy()
        if control is not None:controlmask |= d['groups']==control
        r=dict(sid=d['info']['sid'],group=d['info']['group'],baseline=b,candidate=n,delta=n['f1']-b['f1'],chosen_cell=best,added_frames=changed,predicted_gain=None if best is None else float(values[best]),actual_added_rater_precision=None if not changed else float(d['labels'][extra].mean()),semantic_order_control_F1=metric(controlmask,d['labels'])['f1'])
        results.append(r);np.savez(ROOT/'external'/d['info']['sid']/'output.npz',selected=mask,utility=values)
    summary={}
    for group in ['train','check']:
        rows=[r for r in results if r['group']==group];summary[group]=dict(sources=len(rows),macro_delta=float(np.mean([r['delta']for r in rows])),changed_sources=sum(r['added_frames']>0 for r in rows),added_frames=sum(r['added_frames']for r in rows),worst_delta=min(r['delta']for r in rows))
    # No resurrected universal proxy-F1 gate. A bounded one-cell addition cannot
    # delete baseline content; still stop a plainly wrong implementation.
    require(all(r['candidate']['selected']>=r['baseline']['selected'] for r in results),'No hidden deletions')
    save(ROOT/'external_comparison.json',dict(status='SINGLE_FIXED_HEAD_EXTERNAL_PROXY_DIAGNOSTIC_NOT_OFFICIAL_QUALITY',summary=summary,sources=results,official_joint_score='UNKNOWN',new_fivefold=False,check_used_to_retune=False))
    event('ONE_HEAD_TRAIN_AND_EXTERNAL_DIAGNOSTIC_COMPLETE',summary=summary)

if __name__=='__main__':
    try:main()
    except BaseException as e:failure('fit',e);raise
