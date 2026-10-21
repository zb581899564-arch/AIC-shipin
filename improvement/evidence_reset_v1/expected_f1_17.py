"""Exact fixed-cardinality expected temporal F1 under a finite answer distribution.

The finite model answer distribution is a hypothesis, not human GT or a calibrated
official posterior. No targets enter the selection algorithm.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback


def logsumexp(values):
    m=max(values)
    return m+math.log(math.fsum(math.exp(x-m)for x in values))


def expected_select(actions,logweights,baseline,native_count):
    """Keep baseline outside union and exactly its original full-source count."""
    baseline=set(baseline);actions=[set(a)for a in actions]
    if (not actions or len(actions)!=len(logweights) or any(not math.isfinite(x)for x in logweights)
        or any(type(i)is not int or not 0<=i<native_count for a in [baseline,*actions]for i in a)):
        raise ValueError('Finite complete bound candidate/native domain required')
    union=set().union(*actions);outside=baseline-union;inside=len(baseline)-len(outside)
    if inside==0:return baseline,dict(original_count=len(baseline),mutable_count=0,changed=0)
    k=len(baseline);pattern={};score={}
    for j,a in enumerate(actions):
        for i in a:pattern[i]=pattern.get(i,0)|(1<<j)
    for bit in set(pattern.values()):
        score[bit]=logsumexp([logweights[j]-math.log(k+len(a))for j,a in enumerate(actions)if bit&(1<<j)])
    # Stable ties retain original frames before source ordinal; no label access.
    order=sorted(union,key=lambda i:(-score[pattern[i]],i not in baseline,i))
    selected=outside|set(order[:inside])
    if len(selected)!=k or selected-union!=outside:raise AssertionError('Exact per-source protected budget')
    z=logsumexp(logweights);q=[math.exp(x-z)for x in logweights]
    def value(s):return math.fsum(p*2*len(s&a)/(k+len(a))for p,a in zip(q,actions))
    return selected,dict(original_count=k,mutable_count=inside,fixed_outside=len(outside),
        union_frames=len(union),changed=len(selected-baseline),class_count=len(score),
        expected_model_F1=value(selected),expected_baseline_F1=value(baseline),
        probabilities=q,not_human_or_official_posterior=True)


def main(root):
    import numpy as np
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent;t=time.monotonic()
    spec=importlib.util.spec_from_file_location('old_diagnostic17',R/'diagnostic.py');api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    reg=json.loads((N/'registration17.json').read_text());protocol=api.checked_json(reg['protocol_ref'],W)
    sys.path.insert(0,reg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    collections={s:api.checked_json(reg[s+'_collection_ref'],W)for s in ['train','check']}
    metrics={};decisions={}
    for scope,source_count,window_count in [('train',25,144),('check',8,43)]:
        collection=collections[scope]
        assert collection['source_count']==source_count and collection['window_count']==window_count and collection['labels_read'] is False
        store=NativeInputStore(api.checked_json(collection['asset_manifest_ref'],W),scope)
        assert set(collection['sources'])==set(store.source_ids)
        results=[];decisions[scope]={}
        for sid in sorted(store.source_ids):
            source=collection['sources'][sid];human=store.source_supervision(sid)
            assert human['source_sha256']==source['source_sha256']
            windows=[api.checked_json(collection['window_refs'][uid],W)for uid in source['window_ids']]
            for uid,row in zip(source['window_ids'],windows):
                assert row['uid']==uid and row['status']=='ACCEPTED' and row['labels_read'] is False
                assert row['source_sha256']==human['source_sha256'] and row['input_signature']==store.requests[uid]['input_signature']
                assert all(s['status']=='ACCEPTED'for s in row['slots'])
            actions=[];real=[];shift=[];seen={};kept=[]
            for j,c in enumerate(source['candidates']):
                signature=tuple(tuple(row['slots'][j]['ids'])for row in windows)
                if signature in seen:
                    other=source['candidates'][seen[signature]]
                    assert c['selected_ordinals']==other['selected_ordinals'] and abs(c['logprob_sum']-other['logprob_sum'])<1e-9
                    continue
                seen[signature]=j;kept.append(j);actions.append(c['selected_ordinals'])
                real.append(c['logprob_sum']);shift.append(c['permuted_logprob_sum'])
            n=source['native_count'];baseline=set(human['baseline']);labels=np.zeros((n,len(human['raters'])),bool)
            assert all(len(m)==n and all(m)for m in human['known_masks'])
            for j,truth in enumerate(human['raters']):labels[sorted(truth),j]=True
            selections={};stats={}
            for arm,weights in [('real',real),('shifted',shift),('uniform',[0.]*len(actions))]:
                selected,info=expected_select(actions,weights,baseline,n)
                assert len(selected)==len(baseline)
                selections[arm]=selected;stats[arm]=info
            b=api.utility(baseline,labels)
            row=dict(source_id=sid,source_sha256=human['source_sha256'],baseline_f1=b,original_count=len(baseline),
                unique_complete_answers=len(actions),kept_slots=kept,arms={arm:dict(f1=api.utility(s,labels),
                    added=len(s-baseline),deleted=len(baseline-s),stats=stats[arm])for arm,s in selections.items()})
            results.append(row);decisions[scope][sid]={arm:sorted(s)for arm,s in selections.items()}
        summary=dict(sources=len(results),macro_baseline=sum(r['baseline_f1']for r in results)/len(results),arms={})
        for arm in ['real','shifted','uniform']:
            summary['arms'][arm]=dict(macro_f1=sum(r['arms'][arm]['f1']for r in results)/len(results),
                improved=sum(r['arms'][arm]['f1']>r['baseline_f1']for r in results),worsened=sum(r['arms'][arm]['f1']<r['baseline_f1']for r in results),
                changed_sources=sum(r['arms'][arm]['added']>0 for r in results),
                added=sum(r['arms'][arm]['added']for r in results),deleted=sum(r['arms'][arm]['deleted']for r in results),
                worst_delta=min(r['arms'][arm]['f1']-r['baseline_f1']for r in results))
        metrics[scope]=dict(summary=summary,per_source=results)
    reasons=[]
    for scope,data in metrics.items():
        s=data['summary'];a=s['arms']['real']
        if not a['macro_f1']>s['macro_baseline']:reasons.append(scope.upper()+'_NO_GAIN_OVER_PROTECTED_PROXY')
        for control in ['shifted','uniform']:
            if not a['macro_f1']>s['arms'][control]['macro_f1']:reasons.append(scope.upper()+'_NO_GAIN_OVER_'+control.upper())
        if a['changed_sources']<3:reasons.append(scope.upper()+'_INSUFFICIENT_REAL_CHANGED_SOURCES')
    assert time.monotonic()-t<protocol['max_CPU_seconds']
    result=dict(status='STOP_RESTRICTED_POSTERIOR_EXPECTED_F1'if reasons else 'ELIGIBLE_FOR_SEPARATE_COMPLETE_POLICY_REVIEW',
        stop_reasons=reasons,metrics=metrics,seconds=time.monotonic()-t,new_model_calls=0,new_fits=0,new_decode=0,
        per_source_frame_counts_preserved=True,reference_targets_in_selection=False,
        historical_exposed=True,official_joint_score='UNKNOWN',production_admitted=False,official_submissions=0)
    api.save_new(N/'decisions17.json',dict(selected=decisions,no_reference_targets_in_rule=True))
    api.save_new(N/'completion17.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='metrics'}|{'metrics':{k:v['summary']for k,v in metrics.items()}}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args()
    try:main(args.run_root)
    except BaseException:
        with (Path(args.run_root)/'failure17.json').open('x')as f:json.dump(dict(status='ACTUAL_FAILURE_NOT_EMPTY',traceback=traceback.format_exc()),f,indent=2)
        raise
