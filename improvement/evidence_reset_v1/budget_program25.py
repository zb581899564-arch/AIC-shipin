"""First closed source-program budget/conditional-gradient feasibility audit."""
import hashlib
import json
from pathlib import Path
import sys
import time


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    import numpy as np
    from budget_program25_math import project_budget,best_program,conditional
    N=Path(__file__).resolve().parent;R=N.parent;W=R.parent;start=time.monotonic()
    reg=json.loads((N/'registration25.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        path=Path(r['path']).resolve(strict=True);assert path.is_relative_to(W)and ref(path)==r
        return json.loads(path.read_text())
    p=read(reg['protocol_ref']);oldreg=read(reg['registration19_ref'])
    sys.path.insert(0,oldreg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    read(oldreg['protocol_ref'])
    held={'S02','S06','S08','S23'};metrics={};training=[];programs={}
    def utility(selected,labels):
        gt=labels.sum(axis=0,dtype=np.int64);tp=labels[sorted(selected)].sum(axis=0,dtype=np.int64);den=len(selected)+gt
        return float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())
    for scope,count in [('train',25),('check',8)]:
        coll=read(oldreg[scope+'_collection_ref']);store=NativeInputStore(read(coll['asset_manifest_ref']),scope);rows=[];programs[scope]={}
        assert coll['source_count']==count and coll['labels_read']is False
        for sid in store.source_ids:
            h=store.source_supervision(sid);n=len(h['clock']['normalized_exact_pts']);b=set(h['baseline'])
            assert all(len(v)==n and all(v)for v in h['known_masks'])and h['source_sha256']==coll['sources'][sid]['source_sha256']
            labels=np.zeros((n,len(h['raters'])),bool)
            for r,truth in enumerate(h['raters']):labels[sorted(truth),r]=True
            actions=[];logits={a:[]for a in ['real','shifted','uniform']};bindings=[];lengths=[];tp=[];overlaps=[];domains=[]
            for uid in coll['sources'][sid]['window_ids']:
                w=read(coll['window_refs'][uid]);assert w['status']=='ACCEPTED'and w['labels_read']is False
                assert w['input_signature']==store.requests[uid]['input_signature']
                seen=set();candidates=[]
                for c in w['slots']:
                    key=tuple(c['ids'])
                    if key in seen:continue
                    seen.add(key);assert c['status']=='ACCEPTED';candidates.append(c)
                aa=[set(c['selected_ordinals'])for c in candidates]
                assert all(len(a)==len(c['selected_ordinals'])and all(type(i)is int and 0<=i<n for i in a)for a,c in zip(aa,candidates))
                actions.append(aa);lengths.append(list(map(len,aa)));tp.append([labels[sorted(a)].sum(axis=0,dtype=np.int64)for a in aa]);overlaps.append([len(a&b)for a in aa]);domains.append(set().union(*aa))
                for arm,key in [('real','real'),('shifted','permuted')]:logits[arm].append([c[key]['logprob']for c in candidates])
                logits['uniform'].append([0.]*len(aa));bindings.append(dict(uid=uid,window_ref=coll['window_refs'][uid],slots=[c['slot']for c in candidates]))
            union=set().union(*domains);assert len(union)==sum(map(len,domains));outside=b-union
            projected,support_size=project_budget(lengths,len(b&union));P=len(outside)+projected;gt=labels.sum(axis=0,dtype=np.int64)
            den=P+gt;gains=[[float(np.divide(2.*t,den,out=np.zeros_like(t,dtype=float),where=den!=0).mean())for t in window]for window in tp]
            target,target_score,_=best_program(lengths,gains,projected,overlaps)
            oracle=outside|set().union(*(a[j]for a,j in zip(actions,target)));oracle_F1=utility(oracle,labels)
            outside_TP=labels[sorted(outside)].sum(axis=0,dtype=np.int64)
            constant=float(np.divide(2.*outside_TP,den,out=np.ones_like(den,dtype=float),where=den!=0).mean())
            assert abs(oracle_F1-(constant+target_score))<1e-10
            arms={};programs[scope][sid]={}
            for arm in logits:
                chosen,score,retained=best_program(lengths,logits[arm],projected,overlaps)
                selected=outside|set().union(*(a[j]for a,j in zip(actions,chosen)))
                assert len(selected)==P and selected-union==outside
                arms[arm]=dict(F1=utility(selected,labels),selected_frames=P,added=len(selected-b),deleted=len(b-selected),choices=chosen,score=score)
                programs[scope][sid][arm]=dict(choices=chosen,slots=[binding['slots'][j]for binding,j in zip(bindings,chosen)],projected_inside_count=projected)
            loss=conditional(lengths,logits['real'],projected,target)
            uniform_partition=conditional(lengths,logits['uniform'],projected)
            row=dict(source_id=sid,source_sha256=h['source_sha256'],protected_F1=utility(b,labels),protected_count=len(b),
                projected_count=P,count_projection_delta=P-len(b),count_support_size=support_size,log_feasible_programs=uniform_partition['log_partition'],
                oracle_F1=oracle_F1,conditional_NLL=loss['NLL'],conditional_gradient_L1=loss['gradient_L1'],arms=arms)
            rows.append(row)
            if scope=='train'and sid not in held:
                path=N/(sid+'_target25.json')
                value=dict(source_id=sid,source_sha256=h['source_sha256'],reference_supervision_ref=store.sources[sid]['supervision_ref'],
                    source_count_budget_from_predictions=len(b),projected_inside_count=projected,immutable_outside_ordinals=sorted(outside),
                    lengths=lengths,target_program=target,original_logits=logits['real'],original_conditional=loss,windows=bindings,
                    target_definition='Original all-rater sourceF1 optimal feasible program at prediction-only projected count, not cherry-picked reviewer',
                    official_data=False,oracle_must_not_enter_formal_inference=True)
                with path.open('x')as f:json.dump(value,f,indent=2,allow_nan=False)
                training.append(ref(path))
            assert time.monotonic()-start<p['maximum_CPU_seconds']
        store.close();metrics[scope]=dict(sources=len(rows),macro_protected=float(np.mean([v['protected_F1']for v in rows])),
            macro_oracle=float(np.mean([v['oracle_F1']for v in rows])),max_absolute_count_projection=max(abs(v['count_projection_delta'])for v in rows),
            projected_count_sources=sum(v['count_projection_delta']!=0 for v in rows),arms={a:dict(macro_F1=float(np.mean([v['arms'][a]['F1']for v in rows])),
                changed_sources=sum(bool(v['arms'][a]['added']or v['arms'][a]['deleted'])for v in rows),added=sum(v['arms'][a]['added']for v in rows),deleted=sum(v['arms'][a]['deleted']for v in rows))for a in logits},rows=rows)
    reasons=[]
    for scope,v in metrics.items():
        if v['arms']['real']['macro_F1']<=v['macro_protected']:reasons.append(scope.upper()+'_NO_DECODER_GAIN_OVER_PROTECTED')
        for arm in ['shifted','uniform']:
            if v['arms']['real']['macro_F1']<=v['arms'][arm]['macro_F1']:reasons.append(scope.upper()+'_NO_GAIN_OVER_'+arm.upper())
        if v['arms']['real']['changed_sources']<3:reasons.append(scope.upper()+'_FEWER_THAN3_CHANGED_SOURCES')
    eligible=[r for r in metrics['train']['rows']if r['source_id']not in held]
    feasible=sum(r['conditional_gradient_L1']>1e-8 for r in eligible)>=3 and np.mean([r['oracle_F1']-r['protected_F1']for r in eligible])>0
    summary=dict(status='STOP_UNTRAINED_BUDGET_PROGRAM_DECODER'if reasons else'ELIGIBLE_FOR_SEPARATE_UNTRAINED_DECODER_REVIEW',stop_reasons=reasons,
        metrics=metrics,training_feasibility=dict(status='MATHEMATICALLY_FEASIBLE_NOT_GPU_ADMISSION'if feasible else'STOP_CONDITIONAL_TARGET_TRAINING_NO_SUPPORT',
            sources=len(eligible),nonzero_gradient_sources=sum(r['conditional_gradient_L1']>1e-8 for r in eligible),
            macro_oracle_minus_protected=float(np.mean([r['oracle_F1']-r['protected_F1']for r in eligible]))),target_refs=training,
        seconds=time.monotonic()-start,new_model_calls=0,new_updates=0,new_fits=0,new_ZIP=0,official_submissions=0,automatic_GPU=False)
    for name,value in [('programs25.json',programs),('completion25.json',summary)]:
        with(N/name).open('x')as f:json.dump(value,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(N/'completion25.json'),summary={k:v for k,v in summary.items()if k not in ['target_refs','metrics']}|
        dict(metrics={k:{name:value for name,value in v.items()if name!='rows'}for k,v in metrics.items()}))))


if __name__=='__main__':main()
