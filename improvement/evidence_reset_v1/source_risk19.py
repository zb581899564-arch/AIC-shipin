"""Exact all-rater full-source temporal F1 expectation and action-logit gradient.

CPU feasibility only. Fixed cached model answers and TF scores; no policy
update, new forward, rollout or formal-data access.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback


def normalize(np,logits):
    a=np.asarray(logits,dtype=float)
    if a.ndim!=1 or not len(a)or not np.isfinite(a).all():raise ValueError('Finite nonempty action logits')
    v=np.exp(a-a.max());return v/v.sum()


def expected_utility(np,lengths,overlap,probabilities,gt):
    gt=np.asarray(gt,dtype=np.int64);raters=len(gt);p=np.ones(1);moment=np.zeros((1,raters))
    if not raters or (gt<0).any():raise ValueError('Actual all-reviewer complete source counts required')
    for counts,tp,q in zip(lengths,overlap,probabilities):
        if len(counts)!=len(tp)or len(counts)!=len(q)or not np.isclose(sum(q),1,atol=1e-12):raise ValueError('Action probability/count/TP mismatch')
        newp=np.zeros(len(p)+max(counts));newm=np.zeros((len(newp),raters))
        for n,t,weight in zip(counts,tp,q):
            t=np.asarray(t)
            if n<0 or t.shape!=(raters,)or (t<0).any()or(t>n).any()or(t>gt).any():raise ValueError('Native true-positive count domain')
            if weight:
                newp[n:n+len(p)]+=weight*p
                newm[n:n+len(p)]+=weight*(moment+p[:,None]*t[None,:])
        p,moment=newp,newm
    den=np.arange(len(p))[:,None]+gt[None,:]
    values=np.divide(2*moment,den,out=np.zeros_like(moment),where=den!=0).sum(axis=0)
    values+=np.where(gt==0,p[0],0.)
    if not np.isclose(p.sum(),1,atol=1e-11)or not ((values>=-1e-11)&(values<=1+1e-11)).all():raise AssertionError('Bounded complete expected F1')
    return float(values.mean()),dict(expected_selected_frames=float(np.arange(len(p))@p),probability_source_empty=float(p[0]),per_reviewer_F1=values.tolist())


def action_gradient(np,lengths,overlap,probabilities,gt):
    value,stats=expected_utility(np,lengths,overlap,probabilities,gt);gradient=[];conditional=[]
    for i,q in enumerate(probabilities):
        u=[]
        for j in range(len(q)):
            p=list(probabilities);p[i]=np.eye(len(q))[j]
            one,_=expected_utility(np,lengths,overlap,p,gt);u.append(one)
        if abs(float(np.asarray(q)@u)-value)>1e-10:raise AssertionError('Independent conditional-utility identity')
        g=np.asarray(q)*(np.asarray(u)-value)
        if abs(float(g.sum()))>1e-11:raise AssertionError('Logit gradient invariant to common shift')
        gradient.append(g);conditional.append(u)
    return value,stats,gradient,conditional


def main(root):
    import numpy as np
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent;t=time.monotonic()
    spec=importlib.util.spec_from_file_location('source_risk_api19',R/'diagnostic.py');api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    reg=json.loads((N/'registration19.json').read_text());protocol=api.checked_json(reg['protocol_ref'],W)
    sys.path.insert(0,reg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    summaries={};training=[];all_rows=[]
    for scope,ns,nw in [('train',25,144),('check',8,43)]:
        collection=api.checked_json(reg[scope+'_collection_ref'],W)
        assert (collection['source_count'],collection['window_count'],collection['labels_read'])==(ns,nw,False)
        store=NativeInputStore(api.checked_json(collection['asset_manifest_ref'],W),scope);rows=[]
        ordered=sorted(store.source_ids,key=lambda sid:hashlib.sha256(('EXACT_SOURCE_RISK19:'+store.sources[sid]['source_sha256']).encode()).hexdigest())
        first4=set(ordered[:4])if scope=='train'else set();next4=set(ordered[4:8])if scope=='train'else set()
        for sid in ordered:
            human=store.source_supervision(sid);n=len(human['clock']['normalized_exact_pts']);source=collection['sources'][sid]
            assert human['source_sha256']==source['source_sha256']and all(len(m)==n and all(m)for m in human['known_masks'])
            labels=np.zeros((n,len(human['raters'])),bool)
            for j,truth in enumerate(human['raters']):labels[sorted(truth),j]=True
            lengths=[];overlap=[];prob={k:[]for k in ['real','shifted','uniform']};bindings=[];domains=[]
            for uid in source['window_ids']:
                window=api.checked_json(collection['window_refs'][uid],W);assert window['status']=='ACCEPTED'and window['labels_read']is False
                assert window['input_signature']==store.requests[uid]['input_signature']and window['source_sha256']==human['source_sha256']
                seen=set();slots=[];actions=[];real=[];shifted=[]
                for c in window['slots']:
                    assert c['status']=='ACCEPTED';key=tuple(c['ids'])
                    if key in seen:continue
                    seen.add(key);slots.append(c['slot']);actions.append(c['selected_ordinals']);real.append(c['real']['logprob']);shifted.append(c['permuted']['logprob'])
                domains.append(set().union(*map(set,actions)));lengths.append(list(map(len,actions)))
                overlap.append([labels[a].sum(axis=0,dtype=np.int64)for a in actions])
                prob['real'].append(normalize(np,real));prob['shifted'].append(normalize(np,shifted));prob['uniform'].append(np.ones(len(actions))/len(actions))
                bindings.append(dict(uid=uid,window_ref=collection['window_refs'][uid],slots=slots,original_logits=real,original_request_ref=store.request_refs[uid]))
            assert len(set().union(*domains))==sum(map(len,domains)),'Native windows disjoint'
            gt=labels.sum(axis=0,dtype=np.int64);metrics={}
            for arm in prob:
                value,stats=expected_utility(np,lengths,overlap,prob[arm],gt);metrics[arm]=dict(expected_native_F1=value,**stats)
            record=dict(scope=scope,source_id=sid,source_sha256=human['source_sha256'],metrics=metrics,
                original_baseline_F1=api.utility(human['baseline'],labels),original_baseline_frames=len(human['baseline']),
                hashed_training4=sid in first4,hashed_process4=sid in next4)
            if scope=='train':
                value,stats,g,u=action_gradient(np,lengths,overlap,prob['real'],gt)
                record.update(logit_gradient_L1=float(sum(np.abs(v).sum()for v in g)),
                    logit_gradient_L2=float(np.sqrt(sum(v@v for v in g))),
                    informative_windows=sum(max(v)-min(v)>1e-8 for v in u),windows=len(u))
                coeff=dict(source_id=sid,source_sha256=human['source_sha256'],native_frames=n,original_reviewers=len(gt),
                    source_supervision_ref=store.sources[sid]['supervision_ref'],metrics=record,
                    windows=[dict(**b,conditional_utilities=utilities,logit_gradient=gradient.tolist(),native_action_lengths=c,
                                  original_action_probabilities=q.tolist())for b,utilities,gradient,c,q in zip(bindings,u,g,lengths,prob['real'])],
                    exact_full_source_objective='mean_rater E[2TP/(P+G)], factorized independent window actions',
                    no_new_neural_forward=True,no_reference_labels_from_official=True)
                rp=N/(sid+'_training_coefficients19.json');api.save_new(rp,coeff);training.append(api.reference(rp))
            rows.append(record);assert time.monotonic()-t<protocol['max_CPU_seconds']
        summaries[scope]=dict(sources=len(rows),windows=nw,
            macro_protected_F1=float(np.mean([r['original_baseline_F1']for r in rows])),
            expected_metrics={arm:dict(macro_expected_F1=float(np.mean([r['metrics'][arm]['expected_native_F1']for r in rows])),
                mean_source_empty_probability=float(np.mean([r['metrics'][arm]['probability_source_empty']for r in rows])))for arm in prob},
            frozen_first4=sorted(first4),frozen_next4=sorted(next4))
        if scope=='train':summaries[scope].update(median_logit_gradient_L1=float(np.median([r['logit_gradient_L1']for r in rows])),
            total_informative_windows=sum(r['informative_windows']for r in rows),
            hashed_first4_gradient_L1=[dict(source_id=r['source_id'],gradient=r['logit_gradient_L1'],windows=r['windows'])for r in rows if r['hashed_training4']])
        all_rows+=rows
    result=dict(status='EXACT_SOURCE_RISK_CPU_FEASIBILITY_ONLY_NOT_TRAINING_ADMISSION',summaries=summaries,
        source_rows=all_rows,training_coefficient_refs=training,seconds=time.monotonic()-t,
        new_model_calls=0,new_training_updates=0,new_decode=0,new_ZIP=0,official_submissions=0,automatic_model=False,
        reference_task_scope='Historical exposed external summary proxy only, not official joint score')
    api.save_new(N/'completion19.json',result)
    print(json.dumps({k:v for k,v in result.items()if k not in ['source_rows','training_coefficient_refs']}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args()
    try:main(args.run_root)
    except BaseException:
        with (Path(args.run_root)/'failure19.json').open('x')as f:json.dump(dict(status='ACTUAL_FAILURE_NOT_EMPTY',traceback=traceback.format_exc()),f,indent=2)
        raise
