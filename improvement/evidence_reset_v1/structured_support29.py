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
    from structured_program29_math import enumerate_programs
    N=Path(__file__).resolve().parent;R=N.parent;W=R.parent;started=time.monotonic()
    reg=json.loads((N/'registration29.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(W)and ref(p)==r;return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);oldreg=read(reg['registration19_ref']);old19=read(reg['completion19_ref']);noop=read(reg['completion28_ref'])
    sys.path.insert(0,oldreg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    coll=read(oldreg['train_collection_ref']);store=NativeInputStore(read(coll['asset_manifest_ref']),'train')
    process={'S02','S06','S08','S23'};fit20={r['source_id']for r in old19['source_rows']if r['scope']=='train'and r['hashed_training4']}
    remaining=[sid for sid in store.source_ids if sid not in fit20|process];assert len(remaining)==17
    ordered=sorted(remaining,key=lambda sid:hashlib.sha256(('SOURCE_STRUCTURED_MAP29:'+coll['sources'][sid]['source_sha256']).encode()).hexdigest())
    chosen={'fit':ordered[:4],'process':sorted(process)}
    with(N/'source_partition_before_metrics29.json').open('x')as f:json.dump(dict(chosen=chosen,excluded_oldfit=sorted(fit20),replacement=False),f,indent=2)
    noops={v['sid']:(r,v)for r in noop['outputs']for v in [read(r)]if v['scope']=='train'}
    rows=[];targets=[]
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
                rows.append(dict(sid=sid,cohort=cohort,status='FORCED_UNCHANGED_B_NO_MODEL_LOSS',baseline_F1=bF1,oracle_F1=bF1,
                    oracle_gain=0.,strictly_better_programs=0,native_programs=1,baseline_frames=len(b),reason='28 unsupported source, no replacement',noop_ref=noop_ref));continue
            source_windows={r['uid']:r for r in adopted['windows']};windows=[];lengths=[];tp=[];baseline_program=[];overlaps=[];domains=[]
            for uid in coll['sources'][sid]['window_ids']:
                old_ref=coll['window_refs'][uid];old=read(old_ref);new=source_windows[uid];assert new['status'].startswith('PASS_')
                groups={}
                for c in old['slots']:
                    key=tuple(c['selected_ordinals']);assert len(key)==len(set(key))
                    groups.setdefault(key,[]).append(dict(kind='OLD_ACCEPTED_SUFFIX',window_ref=old_ref,slot=c['slot'],original_real_logp=c['real']['logprob'],original_shifted_logp=c['permuted']['logprob']))
                base=tuple(new['selected_ordinals'])
                if base not in groups:groups[base]=[dict(kind='NEW_EXACT_BASELINE_NOOP',source_noop_ref=noop_ref,uid=uid,model_score_unknown=True)]
                aa=list(groups);domains.append(set().union(*map(set,aa)));baseline_program.append(aa.index(base))
                lengths.append(list(map(len,aa)));tp.append([labels[list(a)].sum(axis=0,dtype=np.int64)for a in aa]);overlaps.append([len(set(a)&b)for a in aa])
                windows.append(dict(uid=uid,request_ref=store.request_refs[uid],groups=[dict(native_count=len(a),TP=tp[-1][j].tolist(),variants=groups[a])for j,a in enumerate(aa)],baseline_group=aa.index(base)))
            assert len(set().union(*domains))==sum(map(len,domains))
            choices,P,u=enumerate_programs(lengths,tp,labels.sum(axis=0,dtype=np.int64),limit=2000000)
            Bindex=np.flatnonzero((choices==np.asarray(baseline_program)).all(axis=1));assert len(Bindex)==1 and abs(float(u[Bindex[0]])-bF1)<1e-12 and int(P[Bindex[0]])==len(b)
            keep=sum((np.asarray(v)[choices[:,w]]for w,v in enumerate(overlaps)),start=np.zeros(len(choices),dtype=np.int64))
            best=np.flatnonzero(u==u.max());index=int(best[np.argmax(keep[best])]);gold=choices[index].tolist()
            value=dict(sid=sid,cohort=cohort,status='SUPPORTED_NATIVE_PROGRAM_SPACE_ONLY',baseline_F1=bF1,oracle_F1=float(u[index]),
                oracle_gain=float(u[index]-bF1),strictly_better_programs=int(np.sum(u>bF1+1e-12)),native_programs=len(u),
                same_baseline_count_programs=int(np.sum(P==len(b))),baseline_frames=len(b),oracle_frames=int(P[index]),
                oracle_added=int(P[index]-keep[index]),oracle_deleted=int(len(b)-keep[index]),reference_optimal_native_programs=len(best))
            path=N/(cohort+'_'+sid+'_support29.json')
            target=dict(**value,source_sha256=human['source_sha256'],reference_ref=store.sources[sid]['supervision_ref'],
                gt=labels.sum(axis=0,dtype=np.int64).tolist(),windows=windows,baseline_program=baseline_program,one_oracle_program=gold,
                all_reference_optimal_programs_defined_by='Exact maximum of all-rater full-source nativeF1 over these unique native groups; future gold score maximizes over all exact optimal native programs/variants, not only one canonical text',
                label_data_must_not_enter_model_input=True,official_data=False)
            with path.open('x')as f:json.dump(target,f,indent=2,allow_nan=False)
            targets.append(ref(path));rows.append(value);assert time.monotonic()-started<protocol['maximum_CPU_seconds']
    store.close();summaries={};reasons=[]
    for cohort in chosen:
        source=[r for r in rows if r['cohort']==cohort];good=sum(r['oracle_gain']>=.01 for r in source);gain=float(np.mean([r['oracle_gain']for r in source]))
        summaries[cohort]=dict(sources=len(source),supported=sum(r['status'].startswith('SUPPORTED_')for r in source),oracle_gain=gain,
            sources_with_at_least_point01_headroom=good,native_programs=sum(r['native_programs']for r in source),rows=source)
        if good<3:reasons.append(cohort.upper()+'_FEWER_THAN3_MEANINGFUL_NATIVE_ALTERNATIVES')
        if gain<=.03:reasons.append(cohort.upper()+'_MEAN_HEADROOM_NOT_OVER_POINT03')
    summary=dict(status='STOP_BASELINE_INCLUSIVE_PROGRAM_SUPPORT'if reasons else'ELIGIBLE_FOR_SEPARATE_BASELINE_SCORE_AND_LOSS_REVIEW_ONLY',stop_reasons=reasons,
        source_partition=chosen,summary=summaries,target_refs=targets,seconds=time.monotonic()-started,
        model_scores_of_new_B='UNKNOWN_NOT_ZERO',new_model_calls=0,new_updates=0,new_fits=0,new_ZIP=0,official_submissions=0,
        no_automatic_GPU=True,oracle_is_not_selector_ability=True)
    with(N/'completion29.json').open('x')as f:json.dump(summary,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(N/'completion29.json'),summary={k:v for k,v in summary.items()if k not in ['target_refs','summary']}|
        dict(cohorts={k:{a:b for a,b in v.items()if a!='rows'}for k,v in summaries.items()}))))


if __name__=='__main__':main()
