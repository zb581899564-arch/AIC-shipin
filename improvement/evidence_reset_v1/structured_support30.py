"""First baseline-inclusive native program support audit, no neural calls."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from count_interval30_math import certify
    import resource
    N=Path(__file__).resolve().parent;R=N.parent;W=R.parent;started=time.monotonic()
    reg=json.loads((N/'registration30.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(W)and ref(p)==r;return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);read(reg['original_protocol29_ref']);oldreg=read(reg['registration19_ref']);old19=read(reg['completion19_ref']);noop=read(reg['completion28_ref'])
    sys.path.insert(0,oldreg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    coll=read(oldreg['train_collection_ref']);store=NativeInputStore(read(coll['asset_manifest_ref']),'train')
    process={'S02','S06','S08','S23'};fit20={r['source_id']for r in old19['source_rows']if r['scope']=='train'and r['hashed_training4']}
    remaining=[sid for sid in store.source_ids if sid not in fit20|process];assert len(remaining)==17
    ordered=sorted(remaining,key=lambda sid:hashlib.sha256(('SOURCE_STRUCTURED_MAP29:'+coll['sources'][sid]['source_sha256']).encode()).hexdigest())
    chosen={'fit':ordered[:4],'process':sorted(process)}
    assert chosen==read(reg['partition29_ref'])['chosen'],'Original29 source identities cannot change'
    with(N/'source_partition_adopted_before_metrics30.json').open('x')as f:json.dump(dict(chosen=chosen,excluded_oldfit=sorted(fit20),replacement=False),f,indent=2)
    noops={v['sid']:(r,v)for r in noop['outputs']for v in [read(r)]if v['scope']=='train'}
    rows=[];targets={'fit':[],'process':[]}
    def utility(selected,labels):
        P=len(selected);tp=labels[sorted(selected)].sum(axis=0,dtype=np.int64);den=P+labels.sum(axis=0,dtype=np.int64)
        return float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())
    for cohort,ids in chosen.items():
        for sid in ids:
            human=store.source_supervision(sid);clock=human['clock']['normalized_exact_pts'];b=set(human['baseline']);n=len(clock)
            assert all(len(m)==n and all(m)for m in human['known_masks'])
            labels=np.zeros((n,len(human['raters'])),dtype=bool)
            for j,rater in enumerate(human['raters']):labels[sorted(rater),j]=True
            bF1=utility(b,labels);noop_ref,adopted=noops[sid];assert adopted['source_sha256']==human['source_sha256']
            if not adopted['complete_source_support']:
                rows.append(dict(sid=sid,cohort=cohort,status='FORCED_UNCHANGED_B_NO_MODEL_LOSS',baseline_F1=bF1,witness_F1=bF1,
                    witness_gain=0.,strictly_better_native_witness_found=False,native_programs=1,baseline_frames=len(b),reason='28 unsupported source, no replacement',noop_ref=noop_ref));continue
            source_windows={r['uid']:r for r in adopted['windows']};windows=[];lengths=[];tp=[];baseline_program=[];overlaps=[];domains=[];native_actions=[]
            for uid in coll['sources'][sid]['window_ids']:
                old_ref=coll['window_refs'][uid];old=read(old_ref);new=source_windows[uid];assert new['status'].startswith('PASS_')
                groups={}
                for c in old['slots']:
                    key=tuple(sorted(c['selected_ordinals']));assert len(key)==len(set(key))
                    groups.setdefault(key,[]).append(dict(kind='OLD_ACCEPTED_SUFFIX',window_ref=old_ref,slot=c['slot'],original_real_logp=c['real']['logprob'],original_shifted_logp=c['permuted']['logprob']))
                base=tuple(new['selected_ordinals'])
                if base not in groups:groups[base]=[dict(kind='NEW_EXACT_BASELINE_NOOP',source_noop_ref=noop_ref,uid=uid,model_score_unknown=True)]
                aa=list(groups);native_actions.append(aa);domains.append(set().union(*map(set,aa)));baseline_program.append(aa.index(base))
                lengths.append(list(map(len,aa)));tp.append([labels[list(a)].sum(axis=0,dtype=np.int64)for a in aa]);overlaps.append([len(set(a)&b)for a in aa])
                windows.append(dict(uid=uid,request_ref=store.request_refs[uid],groups=[dict(native_count=len(a),TP=tp[-1][j].tolist(),variants=groups[a])for j,a in enumerate(aa)],baseline_group=aa.index(base)))
            assert len(set().union(*domains))==sum(map(len,domains))
            before=N/(cohort+'_'+sid+'_inputs_before30.json')
            with before.open('x')as f:json.dump(dict(sid=sid,cohort=cohort,reference_ref=store.sources[sid]['supervision_ref'],
                gt=labels.sum(axis=0,dtype=np.int64).tolist(),lengths=lengths,TP=[[v.tolist()for v in row]for row in tp],
                baseline_program=baseline_program,overlaps=overlaps,windows=windows),f,indent=2,allow_nan=False)
            certificate=certify(lengths,tp,labels.sum(axis=0,dtype=np.int64),baseline_program,overlaps,
                deadline=started+protocol['maximum_CPU_seconds'],max_nodes=protocol['maximum_DP_nodes_per_source'])
            gold=certificate['choices'];witness=set().union(*(set(a[j])for a,j in zip(native_actions,gold)))
            actual=utility(witness,labels);assert len(witness)==certificate['witness_frames']and abs(actual-certificate['witness_F1'])<1e-12
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=protocol['maximum_RSS_bytes'],'Bounded CPU RSS'
            value=dict(sid=sid,cohort=cohort,status='SUPPORTED_NATIVE_PROGRAM_WITNESS_ONLY',baseline_F1=bF1,witness_F1=actual,
                witness_gain=actual-bF1,strictly_better_native_witness_found=actual>bF1+1e-12,native_programs=certificate['native_programs'],
                same_baseline_count_programs=certificate['same_baseline_count_programs'],baseline_frames=len(b),witness_frames=len(witness),
                witness_added=len(witness-b),witness_deleted=len(b-witness),reference_optimal_native_programs='UNKNOWN_NOT_ENUMERATED',
                certificate=certificate,first_native_witness_expansion_QA=True,input_ref=ref(before))
            path=N/(cohort+'_'+sid+'_support30.json')
            target=dict(**value,source_sha256=human['source_sha256'],reference_ref=store.sources[sid]['supervision_ref'],
                gt=labels.sum(axis=0,dtype=np.int64).tolist(),windows=windows,baseline_program=baseline_program,one_witness_program=gold,
                all_reference_optimal_programs_defined_by='This is a verified feasible witness with a declared numerical-margin upper-bound gap; all highest-model-score golds and their count remain UNKNOWN, no training target admission',
                label_data_must_not_enter_model_input=True,official_data=False)
            with path.open('x')as f:json.dump(target,f,indent=2,allow_nan=False)
            targets[cohort].append(ref(path));rows.append(value);assert time.monotonic()-started<protocol['maximum_CPU_seconds']
    store.close();summaries={};reasons=[]
    for cohort in chosen:
        source=[r for r in rows if r['cohort']==cohort];good=sum(r['witness_gain']>=.01+1e-9 for r in source);gain=float(np.mean([r['witness_gain']for r in source]))
        summaries[cohort]=dict(sources=len(source),supported=sum(r['status'].startswith('SUPPORTED_')for r in source),witness_gain=gain,
            sources_with_at_least_point01_headroom=good,native_programs=sum(r['native_programs']for r in source),rows=source)
        if good<3:reasons.append(cohort.upper()+'_FEWER_THAN3_MEANINGFUL_NATIVE_ALTERNATIVES')
        if gain<=.03+1e-9:reasons.append(cohort.upper()+'_MEAN_HEADROOM_NOT_OVER_POINT03')
    summary=dict(status='STOP_BASELINE_INCLUSIVE_PROGRAM_SUPPORT'if reasons else'ELIGIBLE_FOR_SEPARATE_BASELINE_SCORE_AND_LOSS_REVIEW_ONLY',stop_reasons=reasons,
        source_partition=chosen,summary=summaries,target_refs_by_role=targets,seconds=time.monotonic()-started,
        model_scores_of_new_B='UNKNOWN_NOT_ZERO',new_model_calls=0,new_updates=0,new_fits=0,new_ZIP=0,official_submissions=0,
        no_automatic_GPU=True,oracle_is_not_selector_ability=True,
        actual_peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,all_gold_programs='UNKNOWN_NOT_ENUMERATED')
    with(N/'completion30.json').open('x')as f:json.dump(summary,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(N/'completion30.json'),summary={k:v for k,v in summary.items()if k not in ['target_refs_by_role','summary']}|
        dict(cohorts={k:{a:b for a,b in v.items()if a!='rows'}for k,v in summaries.items()}))))


if __name__=='__main__':main()
