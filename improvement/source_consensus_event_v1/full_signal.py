"""Bounded full-feature signal diagnosis and one conditional fixed linear fit."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import datetime as dt
import importlib.util
import sys
import json
import numpy as np

W=Path('/home/inspur/aic_video_work')
ROOT=W/'full_signal_event_20261018_v1'
PRIOR=W/'source_consensus_event_20261018_v1'
spec=importlib.util.spec_from_file_location('_full_signal_existing_contract',PRIOR/'code_v1/source_consensus.py')
old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
read,save,ref,bound,require=old.read,old.save,old.ref,old.bound,old.require
critic,helper=old.critic,old.helper
from event_features import normalize_language
from multiple_choice import multiple_choice_knapsack


def deadline(fit=False):
    scope=read(ROOT/'scope_before_diagnosis_01.json')
    limit=scope['fit_cutoff_utc'] if fit else scope['deadline_utc']
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(limit.replace('Z','+00:00')),'Explicit bounded work deadline')


def write_npz(path,**arrays):
    with Path(path).open('xb') as f:np.savez(f,**arrays)


def full_difference(language,groups,baseline,candidates):
    normalized=normalize_language(language)
    require(baseline.any(),'Original selected anchor defined')
    counts=np.bincount(groups[baseline],minlength=len(normalized))
    anchor=counts@normalized/int(baseline.sum())
    values=[]
    for candidate in candidates:
        left,right=candidate['left'],candidate['right']
        newgroups=groups[left:right][~baseline[left:right]]
        require(len(newgroups)==candidate['added_frames']>0,'Exact new native frame denominator')
        newcounts=np.bincount(newgroups,minlength=len(normalized))
        values.append(newcounts@normalized/len(newgroups)-anchor)
    values=np.asarray(values,np.float64).reshape(-1,4096)
    require(np.isfinite(values).all(),'Finite full4096 difference')
    if candidates:
        for index in sorted({0,len(candidates)//2,len(candidates)-1}):
            c=candidates[index];indices=np.flatnonzero(~baseline[c['left']:c['right']])+c['left']
            direct=normalized[groups[indices]].mean(0)-normalized[groups[baseline]].mean(0)
            require(np.allclose(values[index],direct,atol=2e-11,rtol=2e-9),'First new fullfeature weighted aggregation versus direct native-index mean')
    return values


def diagnose():
    deadline();out=ROOT/'cache_01';out.mkdir()
    adopted=read(PRIOR/'diagnosis_01/inputs.json')
    pca=dict(np.load(bound(adopted['pca_ref']),allow_pickle=False))
    rows=[];gradient=np.zeros(4096);energy=0.;target_energy=0.
    for role,items in [('train',adopted['training']),('external',adopted['external'])]:
        for row in items:
            deadline()
            source=row['original_source'] if role=='train' else row['source']
            native=np.load(bound(source['data_ref']),allow_pickle=False)
            language=np.load(bound(source['language_ref']),allow_pickle=False)
            clock=read(bound(source['clock_ref']))
            candidates=critic.proposals(clock,native['baseline']) if role=='train' else row['candidates']
            full=full_difference(language,native['groups'],native['baseline'],candidates)
            prior=np.load(bound(row['cache_ref'] if role=='train' else row['input_ref']),allow_pickle=False)
            require(np.allclose(full@pca['pca_components'].T,prior['difference32'],atol=2e-10,rtol=2e-8),'Every new4096 row maps exactly to adopted original32 row; source/time identity unchanged')
            path=out/(row['sid']+'_'+role+'.npz');write_npz(path,difference4096=full)
            rows.append(dict(sid=row['sid'],role=role,full_ref=ref(path),old_row=row,candidates=len(candidates),all_PCA_projection_relation_pass=True))
            if role=='train':
                target=prior['target_precision_difference'];gradient+=full.T@target/len(full)
                energy+=float(np.mean(np.sum(full*full,axis=1)));target_energy+=float(np.mean(target*target))
    inside=pca['pca_components']@gradient
    gram=pca['pca_components']@pca['pca_components'].T
    require(np.allclose(gram,np.eye(32),atol=2e-6),'Adopted PCA orthonormal subspace')
    residual=gradient-pca['pca_components'].T@inside
    result=dict(status='COMPLETED_NEW_FULL4096_TRAINING_SIGNAL_DIAGNOSIS',training_sources=25,external_sources=19,training_target_cross_covariance_energy=float(gradient@gradient),fraction_cross_covariance_outside_PCA32=float((residual@residual)/max(1e-30,gradient@gradient)),warning='Training linear target signal only; not validation accuracy or official quality. Full capacity can overfit.',new_8B=0,new_media=0,formal_data_read=False,utc=helper.utc())
    save(out/'manifest.json',dict(sources=rows,old_manifest_ref=ref(PRIOR/'diagnosis_01/inputs.json'),pca_ref=adopted['pca_ref']))
    save(ROOT/'signal_diagnosis_01.json',result);print(json.dumps(result),flush=True)


def predict(full,candidates,baseline,model):
    raw=(full/model['scale'])@model['coef']
    sizes=np.asarray([c['added_frames'] for c in candidates],float)
    gain=sizes/(int(baseline.sum())+sizes)*np.clip(raw,-1,1)
    return raw,gain


def fit_evaluate():
    deadline(True)
    require(read(ROOT/'single_fit_admission_02.json')['allow_one_fixed_full4096_fit'] is True,'Explicit post-signal diagnostic admission')
    manifest=read(ROOT/'cache_01/manifest.json')
    train=[r for r in manifest['sources'] if r['role']=='train']
    require(len(train)==25,'Fixed25 original-human training set')
    xs=[];ys=[];ws=[]
    for row in train:
        full=np.load(bound(row['full_ref']),allow_pickle=False)['difference4096']
        target=np.load(bound(row['old_row']['cache_ref']),allow_pickle=False)['target_precision_difference']
        xs.append(full);ys.append(target);ws.append(np.full(len(full),1/len(full)))
    x,y,w=np.concatenate(xs),np.concatenate(ys),np.concatenate(ws)
    scale=np.maximum(np.sqrt(np.sum(w[:,None]*x*x,axis=0)/w.sum()),1e-6)
    z=x/scale;h=z.T@(w[:,None]*z)+np.eye(4096);rhs=z.T@(w*y)
    coef=np.linalg.solve(h,rhs)
    require(np.isfinite(coef).all(),'Finite one-final full4096 coefficients')
    residual=z.T@(w*(z@coef-y))+coef
    require(np.linalg.norm(residual)<=1e-7*max(1.,np.linalg.norm(rhs)),'Actual ridge first-order stationarity')
    model=dict(coef=coef,scale=scale);write_npz(ROOT/'model.npz',**model)
    restored=dict(np.load(ROOT/'model.npz',allow_pickle=False))
    require(all(np.array_equal(v,restored[k]) for k,v in model.items()),'One final checkpoint save/reload bit identity')
    save(ROOT/'fit_completion.json',dict(status='COMPLETED_ONE_FULL4096_SOURCE_EQUAL_RIDGE',weights_ref=ref(ROOT/'model.npz'),sources=25,rows=len(x),alpha=1.,bias=False,new_scalars=8192,train_mse=float(np.sum(w*(z@coef-y)**2)/w.sum()),signal_diagnosis_ref=ref(ROOT/'signal_diagnosis_01.json'),utc=helper.utc()))
    del x,y,w,z,h,rhs,xs,ys,ws
    evaluate(model,manifest)


def evaluate(model,manifest):
    out=ROOT/'evaluation_01';out.mkdir();items=[]
    for row in manifest['sources']:
        if row['role']!='external':continue
        source=row['old_row'];data=np.load(bound(source['input_ref']),allow_pickle=False)
        full=np.load(bound(row['full_ref']),allow_pickle=False)['difference4096']
        raw,gain=predict(full,source['candidates'],data['baseline'],model)
        require(np.allclose(raw,np.sum(full/model['scale']*model['coef'],axis=1),atol=2e-11,rtol=2e-9),'First new full4096 prediction independent elementwise dot')
        path=out/(row['sid']+'_scores.npz');write_npz(path,raw_precision_difference=raw,gain=gain)
        items.append(dict(row=source,data=data,raw=raw,gain=gain,score_ref=ref(path)))
    selections={}
    for cohort in sorted({v['row']['cohort'] for v in items}):
        group=[v for v in items if v['row']['cohort']==cohort]
        choices={v['row']['sid']:[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(v['gain'][i])) for i,c in enumerate(v['row']['candidates']) if v['gain'][i]>0] for v in group}
        selections[cohort]=multiple_choice_knapsack(choices,sum(int(v['data']['baseline'].sum()) for v in group)//10)
    frozen=[]
    for v in items:
        row=v['row'];sid=row['sid'];index=selections[row['cohort']]['chosen'].get(sid);mask=v['data']['baseline'].copy();choice=None if index is None else row['candidates'][index]
        if choice is not None:mask[choice['left']:choice['right']]=True
        path=out/(sid+'_mask.npy')
        with path.open('xb') as f:np.save(f,mask)
        frozen.append(dict(sid=sid,cohort=row['cohort'],mask_ref=ref(path),score_ref=v['score_ref'],choice=choice,successful_null=not np.any(v['gain']>0)))
    save(out/'frozen_before_metrics.json',dict(status='ALL19_NEW_FULL_OUTPUTS_FROZEN_BEFORE_CURRENT_METRICS',sources=frozen,selections=selections,weights_ref=ref(ROOT/'model.npz'),all19_previously_exposed=True,utc=helper.utc()))
    rows=[]
    for v,f in zip(items,frozen):
        row=v['row'];sid=row['sid'];labels=np.load(PRIOR/'diagnosis_01'/(sid+'_human_targets.npz'),allow_pickle=False)['labels']
        mask=np.load(bound(f['mask_ref']),allow_pickle=False);before=critic.metric(v['data']['baseline'],labels);oldmetric=critic.metric(v['data']['original_selected'],labels);after=critic.metric(mask,labels);added=mask&~v['data']['baseline']
        target=critic.target_differences(v['data']['baseline'],labels,row['candidates']);positive=v['raw']>0
        rows.append(dict(sid=sid,cohort=row['cohort'],delta={k:after[k]-before[k] for k in ['precision','recall','f1']},minus_old={k:after[k]-oldmetric[k] for k in ['precision','recall','f1']},added_frames=int(added.sum()),successful_null=f['successful_null'],positive_candidates=int(positive.sum()),positive_wrong_sign=int(np.sum(positive&(target<=0))),newframe_precision=None if not added.any() else float(labels[added].mean())))
    def summary(group):
        return dict(sources=len(group),macro_delta={k:float(np.mean([r['delta'][k] for r in group])) for k in ['precision','recall','f1']},macro_minus_old={k:float(np.mean([r['minus_old'][k] for r in group])) for k in ['precision','recall','f1']},precision_up=sum(r['delta']['precision']>0 for r in group),precision_down=sum(r['delta']['precision']<0 for r in group),f1_up=sum(r['delta']['f1']>0 for r in group),f1_down=sum(r['delta']['f1']<0 for r in group),changed=sum(r['added_frames']>0 for r in group),added_frames=sum(r['added_frames'] for r in group),successful_nulls=sum(r['successful_null'] for r in group),worst_f1=min(r['delta']['f1'] for r in group),positive_candidates=sum(r['positive_candidates'] for r in group),positive_wrong_sign=sum(r['positive_wrong_sign'] for r in group))
    result=dict(status='COMPLETED_ONE_FULL4096_REPAIR_REVIEW_REQUIRED',summary={**{c:summary([r for r in rows if r['cohort']==c]) for c in selections},'all19':summary(rows)},sources=rows,all19_previously_exposed=True,new_blind_confirmation=False,automatic_production=False,official_joint_score=None,new_8B=0,formal_data_read=False,utc=helper.utc())
    save(out/'result.json',result);print(json.dumps(result['summary']),flush=True)


if __name__=='__main__':
    try:
        require(os.name=='posix','Linux resident execution only')
        {'diagnose':diagnose,'fit':fit_evaluate}[sys.argv[1]]()
    except BaseException as error:
        import traceback,uuid
        save(ROOT/('failure_'+uuid.uuid4().hex+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),original_successes_preserved=True,no_automatic_retry=True))
        raise
