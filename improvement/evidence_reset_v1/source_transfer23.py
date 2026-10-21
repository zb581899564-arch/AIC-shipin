"""Read-only learned-policy TF transfer test. One frozen model, no generation."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback
from unittest.mock import patch


def save(p,v):
    with Path(p).open('x')as f:json.dump(v,f,indent=2,allow_nan=False)


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def checked(r,W):
    p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(W)and ref(p)==r
    return p


def readref(r,W):return json.loads(checked(r,W).read_text())


def context(root):
    N=Path(root).resolve(strict=True);R=N.parent;W=R.parent
    reg=json.loads((N/'registration23.json').read_text());assert reg['code_ref']==ref(__file__)
    p=readref(reg['protocol_ref'],W);assert p['sources']==['S02','S06','S08','S23']
    sys.path.insert(0,reg['prior_code_root'])
    from improvement.native_preference_v1 import inputs as inp
    from improvement.native_preference_v1.runtime import tensor_signature
    from improvement.content_choice_v1.runtime import permute_visual
    class FastStore(inp.NativeInputStore):
        def _source_pixels(self,sid):
            def once(path,mode='rb',*args,**kwargs):
                assert mode=='rb';return io.BytesIO(gzip.decompress(Path(path).read_bytes()))
            with patch.object(inp.gzip,'open',once):return super()._source_pixels(sid)
    coll=readref(reg['collection_ref'],W);manifest=readref(coll['asset_manifest_ref'],W)
    return N,R,W,reg,p,coll,manifest,FastStore,tensor_signature,permute_visual


def prepare(root):
    import numpy as np
    import torch
    N,R,W,reg,p,coll,m,Store,signature,permute=context(root)
    store=Store(m,'train');done=readref(reg['risk19_ref'],W)
    refs={readref(v,W)['source_id']:v for v in done['training_coefficient_refs']}
    cases={};targets=[];start=time.monotonic()
    for sid in p['sources']:
        coeff=readref(refs[sid],W);assert coeff['metrics']['hashed_process4']and not coeff['metrics']['hashed_training4']
        h=store.source_supervision(sid);n=len(h['clock']['normalized_exact_pts'])
        assert h['source_sha256']==coeff['source_sha256']and all(len(mask)==n and all(mask)for mask in h['known_masks'])
        labels=np.zeros((n,len(h['raters'])),bool)
        for j,truth in enumerate(h['raters']):labels[sorted(truth),j]=True
        target=dict(sid=sid,source_sha256=h['source_sha256'],source_ref=store.sources[sid]['supervision_ref'],
            gt=labels.sum(axis=0,dtype=np.int64).tolist(),protected_baseline_F1=coeff['metrics']['original_baseline_F1'],windows=[])
        domains=[]
        for w in coeff['windows']:
            request,values,_=store.case(w['uid']);old=readref(w['window_ref'],W)
            moved=permute(values);assert signature(torch,moved)==old['counterfactual_input_signature']
            assert signature(torch,values)==old['input_signature']==w.get('input_signature',request['input_signature'])
            slots=[old['slots'][j]for j in w['slots']];assert len({tuple(v['ids'])for v in slots})==len(slots)
            actions=[v['selected_ordinals']for v in slots];domains.append(set().union(*map(set,actions)))
            cases[w['uid']]=dict(uid=w['uid'],sid=sid,request_ref=w['original_request_ref'],window_ref=w['window_ref'],
                input_signature=old['input_signature'],counterfactual_input_signature=old['counterfactual_input_signature'],
                slots=w['slots'],suffixes=[v['ids']for v in slots],original_real=[v['real']['logprob']for v in slots],
                original_shifted=[v['permuted']['logprob']for v in slots],labels_in_input=False)
            target['windows'].append(dict(uid=w['uid'],lengths=list(map(len,actions)),overlap=[labels[a].sum(axis=0,dtype=np.int64).tolist()for a in actions]))
        assert len(set().union(*domains))==sum(map(len,domains))
        targets.append(target)
    store.close();assert len(cases)==24 and sum(len(c['slots'])for c in cases.values())==81
    save(N/'cases23.json',cases);save(N/'targets23.json',targets)
    save(N/'input_acceptance23.json',dict(status='ADOPTED24_REAL_AND_COUNTERFACTUAL_NATIVE_INPUTS_FOR_FROZEN20_TRANSFER',
        cases_ref=ref(N/'cases23.json'),targets_ref=ref(N/'targets23.json'),sources=4,windows=24,unique_suffixes=81,
        actual_max_forwards=162,new_decode=0,new_encode=0,old_input_QA_adopted=True,seconds=time.monotonic()-start))


def gpu(root):
    N,R,W,reg,p,coll,m,Store,signature,permute=context(root)
    a=json.loads((N/'gpu_admission23.json').read_text());assert a['approved']and a['code_ref']==ref(__file__)
    accepted=readref(a['input_acceptance_ref'],W);cases=readref(accepted['cases_ref'],W)
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from improvement.native_preference_v1.runtime import QwenPreferenceRuntime,canonical_frozen_hash
    import torch
    start=time.monotonic();events=N/'events23.jsonl'
    def event(kind,payload):
        with events.open('a')as f:f.write(json.dumps(dict(kind=kind,elapsed=time.monotonic()-start,**payload),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def budget(forward=False):assert time.monotonic()-start<p['max_GPU_seconds']
    runtime=QwenPreferenceRuntime(m['model_spec'],check_budget=budget,on_event=event);runtime.load()
    policy=reg['learned_policy_ref'];checked(policy,W)
    runtime.load_policy(str(Path(policy['path']).parent),policy['sha256'])
    before=runtime._adapter_state();store=Store(m,'train');rows=[];cache={};adopted=0
    for uid,c in cases.items():
        request,values,_=store.case(uid);assert request['input_signature']==c['input_signature']
        moved=permute(values);assert signature(torch,moved)==c['counterfactual_input_signature']
        row=dict(uid=uid,sid=c['sid'],slots=c['slots'],real=[],shifted=[],input_signature=c['input_signature'],counterfactual_input_signature=c['counterfactual_input_signature'])
        for arm,v in [('real',values),('shifted',moved)]:
            for j,suffix in enumerate(c['suffixes']):
                event('BEGIN_FIRST_LEARNED_POLICY_SCORE',dict(uid=uid,arm=arm,slot=c['slots'][j]))
                key=(json.dumps(signature(torch,v),sort_keys=True),tuple(suffix))
                if key in cache:
                    value=cache[key];adopted+=1
                    event('SCORE_ADOPTED_IDENTICAL_CURRENT_POLICY',dict(uid=uid,arm=arm,slot=c['slots'][j],logprob=value))
                else:
                    value=runtime.score(v,suffix);cache[key]=value
                    event('SCORE_RAW_ACCEPTED',dict(uid=uid,arm=arm,slot=c['slots'][j],logprob=value))
                row[arm].append(value)
        path=N/(uid+'_scores23.json');save(path,row);rows.append(ref(path))
    store.close();assert runtime.counts['sequence_scores_completed']==runtime.counts['top_level_forward_calls'] and runtime.counts['top_level_forward_calls']+adopted==162
    assert runtime.counts['backward_calls']==runtime.counts['optimizer_steps']==runtime.counts['generation_calls']==0
    after=runtime._adapter_state();assert all(torch.equal(before[k].view(torch.uint8),after[k].view(torch.uint8))for k in before)
    base=canonical_frozen_hash(runtime.model,torch);assert base==runtime.base_before
    checked(policy,W);runtime._original_files();runtime._inventory(False)
    save(N/'gpu_completion23.json',dict(status='ENGINEERING_COMPLETE_FROZEN_ONE_STEP_POLICY_TRANSFER_SCORES',score_refs=rows,
        cases=24,actual_forwards=runtime.counts['top_level_forward_calls'],adopted_identical_scores=adopted,logical_scores=162,new_updates=0,new_backwards=0,inherited_updates=1,policy_ref=policy,
        base_before=runtime.base_before,base_after=base,all_288_policy_bytes_frozen=True,counts=dict(runtime.counts),
        labels_read=False,seconds=time.monotonic()-start,production_admitted=False))


def native_metrics(np,target,logits):
    from source_risk19 import expected_utility,normalize
    lengths=[w['lengths']for w in target['windows']];overlap=[w['overlap']for w in target['windows']]
    q=[normalize(np,l)for l in logits];J,stats=expected_utility(np,lengths,overlap,q,target['gt'])
    choices=[int(np.argmax(v))for v in logits];P=sum(n[j]for n,j in zip(lengths,choices))
    tp=sum((np.asarray(t[j],dtype=np.int64)for t,j in zip(overlap,choices)),np.zeros(len(target['gt']),np.int64))
    den=P+np.asarray(target['gt']);f1=float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())
    return dict(J=J,MAP_F1=f1,MAP_frames=P,choices=choices,expected_frames=stats['expected_selected_frames'],empty_probability=stats['probability_source_empty'])


def review(root):
    import numpy as np
    N,R,W,reg,p,coll,m,Store,signature,permute=context(root)
    a=json.loads((N/'input_acceptance23.json').read_text());cases=readref(a['cases_ref'],W);targets=readref(a['targets_ref'],W)
    result=json.loads((N/'gpu_completion23.json').read_text());assert result['base_before']==result['base_after']and result['all_288_policy_bytes_frozen']
    scores={}
    for r in result['score_refs']:
        row=readref(r,W);c=cases[row['uid']]
        assert row['slots']==c['slots']and row['input_signature']==c['input_signature']and row['counterfactual_input_signature']==c['counterfactual_input_signature']
        assert len(row['real'])==len(row['shifted'])==len(c['suffixes'])and all(np.isfinite(row[arm]).all()for arm in ['real','shifted'])
        scores[row['uid']]=row
    assert len(scores)==24 and result['actual_forwards']+result['adopted_identical_scores']==162 and result['new_updates']==result['new_backwards']==0
    rows=[]
    for target in targets:
        metrics={}
        for arm in ['real','shifted']:
            old=[cases[w['uid']]['original_'+arm]for w in target['windows']]
            new=[scores[w['uid']][arm]for w in target['windows']]
            metrics[arm]=dict(original=native_metrics(np,target,old),updated=native_metrics(np,target,new))
            metrics[arm]['delta_J']=metrics[arm]['updated']['J']-metrics[arm]['original']['J']
            metrics[arm]['delta_MAP_F1']=metrics[arm]['updated']['MAP_F1']-metrics[arm]['original']['MAP_F1']
            metrics[arm]['changed_windows']=sum(x!=y for x,y in zip(metrics[arm]['original']['choices'],metrics[arm]['updated']['choices']))
            native=[]
            for phase in ['original','updated']:
                selected=set()
                for w,choice in zip(target['windows'],metrics[arm][phase]['choices']):
                    c=cases[w['uid']];old_window=readref(c['window_ref'],W)
                    selected.update(old_window['slots'][c['slots'][choice]]['selected_ordinals'])
                assert len(selected)==metrics[arm][phase]['MAP_frames']
                native.append(selected)
            metrics[arm].update(added=len(native[1]-native[0]),deleted=len(native[0]-native[1]),native_changed=native[0]!=native[1])
        rows.append(dict(sid=target['sid'],metrics=metrics,protected_baseline_F1=target['protected_baseline_F1']))
    macro={arm:{k:float(np.mean([v['metrics'][arm][k]for v in rows]))for k in ['delta_J','delta_MAP_F1','changed_windows']}for arm in ['real','shifted']}
    for arm in ['real','shifted']:
        macro[arm].update(changed_sources=sum(v['metrics'][arm]['native_changed']for v in rows),added=sum(v['metrics'][arm]['added']for v in rows),deleted=sum(v['metrics'][arm]['deleted']for v in rows))
    failures=[]
    if macro['real']['delta_J']<=1e-6:failures.append('NO_POSITIVE_PROCESS_SOURCE_EXPECTED_UTILITY_TRANSFER')
    if macro['real']['delta_J']<=macro['shifted']['delta_J']:failures.append('NO_REAL_OVER_SHIFTED_TRANSFER_ADVANTAGE')
    if sum(v['metrics']['real']['delta_J']>1e-6 for v in rows)<2:failures.append('FEWER_THAN_TWO_SOURCES_WITH_POSITIVE_TRANSFER')
    if macro['real']['delta_MAP_F1'] < -1e-6:failures.append('NATURAL_MAP_PROXY_DECREASES')
    status='STOP_FIRST4_SOURCE_RISK_POLICY_CONTINUATION_NO_TRANSFER' if failures else 'ELIGIBLE_FOR_SEPARATE_BROADER_TRAINING_REVIEW_ONLY'
    save(N/'review23.json',dict(status=status,stop_reasons=failures,macro=macro,rows=rows,
        first_independent_native_source_QA='PASS24_REAL_SHIFTED',new_model_calls_in_review=0,new_updates=0,
        automatic_training=False,production_admitted=False,new_ZIP=0,official_submissions=0,
        limits='Historically exposed process4 summary proxy. Stop only this fixed first4 policy continuation, not a universal impossibility result.'))


if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('--phase',choices=['prepare','gpu','review'],required=True);pa.add_argument('--run-root',required=True);args=pa.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'23.json'),dict(status='ACTUAL_FAILURE_NO_AUTOMATIC_REPEAT',traceback=traceback.format_exc()));raise
