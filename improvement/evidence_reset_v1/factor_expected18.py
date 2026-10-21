"""Fixed-count native expected F1 over independent per-window answer choices.

This is a declared finite answer-model hypothesis, not an official/human
posterior. The decision rule never receives reference annotations.
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


def logsumexp(x):
    m=max(x);return m+math.log(math.fsum(math.exp(v-m)for v in x))


def count_distribution(np,actions,probabilities,omit):
    p=np.ones(1,dtype=float)
    for i,(a,q)in enumerate(zip(actions,probabilities)):
        if i==omit:continue
        sizes=list(map(len,a));next_p=np.zeros(len(p)+max(sizes),dtype=float)
        for size,weight in zip(sizes,q):
            if weight:next_p[size:size+len(p)]+=weight*p
        p=next_p
    if not np.isclose(p.sum(),1,atol=1e-12):raise AssertionError('Complete probability mass')
    return p


def select(actions,logweights,baseline,native_count):
    import numpy as np
    b=set(baseline);actions=[[set(a)for a in window]for window in actions]
    if (not actions or len(actions)!=len(logweights) or
        any(not a or len(a)!=len(w)or any(not math.isfinite(v)for v in w)for a,w in zip(actions,logweights))or
        any(type(i)is not int or not 0<=i<native_count for a in [b]+[a for win in actions for a in win]for i in a)):
        raise ValueError('Complete valid finite source/native candidate distribution required')
    domains=[set().union(*a)for a in actions];union=set().union(*domains)
    if len(union)!=sum(map(len,domains)):raise ValueError('Different native windows may not overlap')
    outside=b-union;inside=len(b)-len(outside);k=len(b)
    if not inside:return b,dict(original_count=k,mutable_count=0,changed=0)
    normal=[[v-logsumexp(w)for v in w]for w in logweights]
    probs=[[math.exp(v)for v in w]for w in normal]
    scores={};conditional_counts=[]
    for i,(a,lq)in enumerate(zip(actions,normal)):
        p=count_distribution(np,actions,probs,i);counts=np.arange(len(p));terms=[]
        for candidate,logp in zip(a,lq):
            expected_inverse=float(np.sum(p/(k+len(candidate)+counts)))
            if not expected_inverse>0:raise AssertionError('Positive inverse denominator')
            terms.append(logp+math.log(expected_inverse))
        membership={}
        for j,c in enumerate(a):
            for ordinal in c:membership[ordinal]=membership.get(ordinal,0)|(1<<j)
        class_score={bit:logsumexp([terms[j]for j in range(len(a))if bit&(1<<j)])for bit in set(membership.values())}
        scores.update({ordinal:class_score[bit]for ordinal,bit in membership.items()})
        conditional_counts.append(dict(window=i,possible_other_counts=len(p),positive_mass_counts=int(np.count_nonzero(p)),
                                       empty_probability=float(p[0])))
    order=sorted(union,key=lambda ordinal:(-scores[ordinal],ordinal not in b,ordinal))
    chosen=outside|set(order[:inside])
    if len(chosen)!=k or chosen-union!=outside:raise AssertionError('Original per-source budget/outside retained')
    def value(s):return 2*math.fsum(math.exp(scores[o])for o in s&union)
    return chosen,dict(original_count=k,mutable_count=inside,fixed_outside=len(outside),union_frames=len(union),
        changed=len(chosen-b),model_expected_F1=value(chosen),baseline_model_expected_F1=value(b),
        factorized_empty_probability=math.prod(math.fsum(q for c,q in zip(a,p)if not c)for a,p in zip(actions,probs)),
        expected_latent_frame_count=math.fsum(q*len(c)for a,p in zip(actions,probs)for c,q in zip(a,p)),
        window_count=len(actions),conditional_count_support=conditional_counts,
        not_human_or_official_posterior=True)


def main(root):
    import numpy as np
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent;t=time.monotonic()
    spec=importlib.util.spec_from_file_location('old_diagnostic18',R/'diagnostic.py');api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    reg=json.loads((N/'registration18.json').read_text());protocol=api.checked_json(reg['protocol_ref'],W)
    sys.path.insert(0,reg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    metrics={};decisions={}
    for scope,ns,nw in [('train',25,144),('check',8,43)]:
        collection=api.checked_json(reg[scope+'_collection_ref'],W)
        assert (collection['source_count'],collection['window_count'],collection['labels_read'])==(ns,nw,False)
        store=NativeInputStore(api.checked_json(collection['asset_manifest_ref'],W),scope);rows=[];decisions[scope]={}
        assert set(collection['sources'])==set(store.source_ids)
        for sid in sorted(store.source_ids):
            source=collection['sources'][sid];human=store.source_supervision(sid);n=len(human['clock']['normalized_exact_pts'])
            assert source['source_sha256']==human['source_sha256'] and n==source['native_count']
            actions=[];real=[];shifted=[]
            for uid in source['window_ids']:
                w=api.checked_json(collection['window_refs'][uid],W)
                assert w['status']=='ACCEPTED'and w['labels_read']is False and w['uid']==uid
                assert w['input_signature']==store.requests[uid]['input_signature'] and w['source_sha256']==human['source_sha256']
                a=[];r=[];s=[];seen={}
                for c in w['slots']:
                    assert c['status']=='ACCEPTED';key=tuple(c['ids'])
                    if key in seen:
                        prior=seen[key];assert c['selected_ordinals']==prior['selected_ordinals']and abs(c['real']['logprob']-prior['real']['logprob'])<1e-9
                        continue
                    seen[key]=c;a.append(c['selected_ordinals']);r.append(c['real']['logprob']);s.append(c['permuted']['logprob'])
                actions.append(a);real.append(r);shifted.append(s)
            assert all(len(m)==n and all(m)for m in human['known_masks'])
            labels=np.zeros((n,len(human['raters'])),bool)
            for j,truth in enumerate(human['raters']):labels[sorted(truth),j]=True
            baseline=set(human['baseline']);b=api.utility(baseline,labels);results={};decisions[scope][sid]={}
            for arm,weights in [('real',real),('shifted',shifted),('uniform',[[0.]*len(a)for a in actions])]:
                selected,stats=select(actions,weights,baseline,n)
                results[arm]=dict(f1=api.utility(selected,labels),added=len(selected-baseline),deleted=len(baseline-selected),stats=stats)
                assert results[arm]['added']==results[arm]['deleted']
                decisions[scope][sid][arm]=sorted(selected)
            rows.append(dict(source_id=sid,source_sha256=human['source_sha256'],baseline_f1=b,arms=results))
        summary=dict(sources=len(rows),macro_baseline=sum(r['baseline_f1']for r in rows)/len(rows),arms={})
        for arm in ['real','shifted','uniform']:
            summary['arms'][arm]=dict(macro_f1=sum(r['arms'][arm]['f1']for r in rows)/len(rows),
                improved=sum(r['arms'][arm]['f1']>r['baseline_f1']for r in rows),worsened=sum(r['arms'][arm]['f1']<r['baseline_f1']for r in rows),
                changed_sources=sum(r['arms'][arm]['added']>0 for r in rows),added=sum(r['arms'][arm]['added']for r in rows),
                worst_delta=min(r['arms'][arm]['f1']-r['baseline_f1']for r in rows))
        metrics[scope]=dict(summary=summary,per_source=rows)
    reasons=[]
    for scope,v in metrics.items():
        s=v['summary'];a=s['arms']['real']
        if not a['macro_f1']>s['macro_baseline']:reasons.append(scope.upper()+'_NO_GAIN_OVER_PROTECTED_PROXY')
        for arm in ['shifted','uniform']:
            if not a['macro_f1']>s['arms'][arm]['macro_f1']:reasons.append(scope.upper()+'_NO_GAIN_OVER_'+arm.upper())
        if a['changed_sources']<3:reasons.append(scope.upper()+'_INSUFFICIENT_CHANGED_SOURCES')
    assert time.monotonic()-t<protocol['max_CPU_seconds']
    result=dict(status='STOP_FACTORIZED_EXPECTED_F1_POLICY'if reasons else'ELIGIBLE_FOR_SEPARATE_FACTORIZED_POLICY_REVIEW',
        stop_reasons=reasons,metrics=metrics,seconds=time.monotonic()-t,new_model_calls=0,new_fits=0,new_decode=0,
        per_source_count_preserved=True,labels_in_rule=False,official_joint_score='UNKNOWN',historical_exposed=True,
        automatic_production=False,new_ZIP=0,official_submissions=0)
    api.save_new(N/'decisions18.json',dict(selected=decisions,no_reference_targets_in_rule=True))
    api.save_new(N/'completion18.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='metrics'}|{'metrics':{k:v['summary']for k,v in metrics.items()}}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args()
    try:main(args.run_root)
    except BaseException:
        with (Path(args.run_root)/'failure18.json').open('x')as f:json.dump(dict(status='ACTUAL_FAILURE_NOT_EMPTY',traceback=traceback.format_exc()),f,indent=2)
        raise
