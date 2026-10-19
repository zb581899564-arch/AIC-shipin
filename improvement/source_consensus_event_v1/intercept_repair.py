"""One train-only unpenalized intercept repair; no score-tuned constants."""
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
ROOT=W/'anchored_intercept_event_20261018_v1'
PRIOR=W/'source_consensus_event_20261018_v1'
spec=importlib.util.spec_from_file_location('_intercept_adopted_contracts',PRIOR/'code_v1/source_consensus.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
read,save,ref,bound,require=m.read,m.save,m.ref,m.bound,m.require
critic,helper=m.critic,m.helper
from multiple_choice import multiple_choice_knapsack


def deadline(fit=False):
    scope=read(ROOT/'scope_before_fit_01.json');limit=scope['fit_cutoff_utc'] if fit else scope['deadline_utc']
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(limit.replace('Z','+00:00')),'Registered deadline')


def write_npz(p,**values):
    with Path(p).open('xb') as f:np.savez(f,**values)


def solve(z,y,w):
    mean_z=np.sum(w[:,None]*z,axis=0)/w.sum();mean_y=float(w@y/w.sum())
    center=z-mean_z
    coef=np.linalg.solve(center.T@(w[:,None]*center)+np.eye(z.shape[1]),center.T@(w*(y-mean_y)))
    intercept=mean_y-mean_z@coef
    return coef,np.asarray(intercept)


def predict(x,candidates,baseline,model,anchor_present=True):
    raw=(x/model['scale'])@model['coef']+model['intercept']
    sizes=np.asarray([v['added_frames'] for v in candidates],float)
    gain=sizes/(int(baseline.sum())+sizes)*np.clip(raw,-1,1)
    if not anchor_present:gain[:]=0
    return raw,gain


def main():
    deadline(True)
    manifest=read(PRIOR/'diagnosis_01/inputs.json')
    old=dict(np.load(bound(manifest['old_model_ref']),allow_pickle=False))
    train=manifest['training'];require(len(train)==25,'Fixed original25 sources')
    xs=[];ys=[];ws=[]
    for row in train:
        data=np.load(bound(row['cache_ref']),allow_pickle=False)
        xs.append(data['difference32']);ys.append(data['target_precision_difference']);ws.append(np.full(len(xs[-1]),1/len(xs[-1])))
    x,y,w=np.concatenate(xs),np.concatenate(ys),np.concatenate(ws);z=x/old['scale']
    # A negative conditional mean with zero feature has a learned negative
    # default, while the old model was structurally forced to return zero.
    testcoef,testbias=solve(np.zeros((3,32)),np.full(3,-.3),np.ones(3))
    require(np.array_equal(testcoef,np.zeros(32)) and abs(float(testbias)+.3)<1e-14,'Constant negative target with zero feature is represented')
    coef,intercept=solve(z,y,w)
    augmented=np.c_[z,np.ones(len(z))];penalty=np.diag(np.r_[np.ones(32),0.])
    direct=np.linalg.solve(augmented.T@(w[:,None]*augmented)+penalty,augmented.T@(w*y))
    require(np.allclose(direct,np.r_[coef,intercept],atol=1e-12,rtol=1e-10),'Centered solution equals independent33-dimensional regularized normal equations')
    residual=z@coef+intercept-y
    require(abs(float(w@residual))<1e-10 and np.linalg.norm(z.T@(w*residual)+coef)<1e-8,'Actual intercept and slope normal equations')
    model=dict(coef=coef,scale=old['scale'],intercept=intercept)
    write_npz(ROOT/'model.npz',**model);restored=dict(np.load(ROOT/'model.npz',allow_pickle=False))
    require(all(np.array_equal(v,restored[k]) for k,v in model.items()),'Final checkpoint save/reload exact')
    save(ROOT/'fit_completion.json',dict(status='COMPLETED_ONE_TRAIN_ONLY_UNPENALIZED_INTERCEPT_REPAIR',weights_ref=ref(ROOT/'model.npz'),original_scale_ref=manifest['old_model_ref'],new_scalars=65,alpha=1.,intercept_penalty=0.,training_sources=25,training_rows=len(z),training_mean_residual=float(w@residual/w.sum()),training_mse=float(w@(residual*residual)/w.sum()),learned_intercept=float(intercept),independent_normal_equations_and_reload=True,official_data_read=False,utc=helper.utc()))
    out=ROOT/'evaluation_01';out.mkdir();items=[]
    for row in manifest['external']:
        data=np.load(bound(row['input_ref']),allow_pickle=False)
        raw,gain=predict(data['difference32'],row['candidates'],data['baseline'],model,row['anchor']['anchor_present'])
        direct_raw=np.sum(data['difference32']/model['scale']*model['coef'],axis=1)+model['intercept']
        require(np.allclose(raw,direct_raw,atol=2e-12,rtol=1e-10),'First new output independent dot plus intercept')
        path=out/(row['sid']+'_scores.npz');write_npz(path,raw_precision_difference=raw,gain=gain)
        items.append(dict(row=row,data=data,raw=raw,gain=gain,score_ref=ref(path)))
    selections={}
    for cohort in sorted({v['row']['cohort'] for v in items}):
        group=[v for v in items if v['row']['cohort']==cohort]
        options={v['row']['sid']:[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(v['gain'][i])) for i,c in enumerate(v['row']['candidates']) if v['gain'][i]>0] for v in group}
        selections[cohort]=multiple_choice_knapsack(options,sum(int(v['data']['baseline'].sum()) for v in group)//10)
    frozen=[]
    for v in items:
        row=v['row'];sid=row['sid'];index=selections[row['cohort']]['chosen'].get(sid);mask=v['data']['baseline'].copy();choice=None if index is None else row['candidates'][index]
        if choice is not None:mask[choice['left']:choice['right']]=True
        path=out/(sid+'_mask.npy')
        with path.open('xb') as f:np.save(f,mask)
        frozen.append(dict(sid=sid,cohort=row['cohort'],mask_ref=ref(path),score_ref=v['score_ref'],choice=choice,successful_null=not np.any(v['gain']>0)))
    save(out/'frozen_before_metrics.json',dict(status='ALL19_INTERCEPT_REPAIR_OUTPUTS_FROZEN_BEFORE_CURRENT_METRICS',sources=frozen,selections=selections,weights_ref=ref(ROOT/'model.npz'),all19_previously_exposed=True,new_blind_confirmation=False,utc=helper.utc()))
    rows=[]
    for v,f in zip(items,frozen):
        row=v['row'];sid=row['sid'];human=np.load(PRIOR/'diagnosis_01'/(sid+'_human_targets.npz'),allow_pickle=False)
        labels=human['labels'];target=human['target_precision_difference'];mask=np.load(bound(f['mask_ref']),allow_pickle=False)
        before=critic.metric(v['data']['baseline'],labels);oldmetric=critic.metric(v['data']['original_selected'],labels);after=critic.metric(mask,labels);added=mask&~v['data']['baseline'];positive=v['raw']>0
        rows.append(dict(sid=sid,cohort=row['cohort'],delta={k:after[k]-before[k] for k in ['precision','recall','f1']},minus_old={k:after[k]-oldmetric[k] for k in ['precision','recall','f1']},added_frames=int(added.sum()),successful_null=f['successful_null'],positive_candidates=int(positive.sum()),positive_wrong_sign=int(np.sum(positive&(target<=0))),newframe_precision=None if not added.any() else float(labels[added].mean())))
    def summary(group):
        return dict(sources=len(group),macro_delta={k:float(np.mean([r['delta'][k] for r in group])) for k in ['precision','recall','f1']},macro_minus_old={k:float(np.mean([r['minus_old'][k] for r in group])) for k in ['precision','recall','f1']},precision_up=sum(r['delta']['precision']>0 for r in group),precision_down=sum(r['delta']['precision']<0 for r in group),f1_up=sum(r['delta']['f1']>0 for r in group),f1_down=sum(r['delta']['f1']<0 for r in group),changed=sum(r['added_frames']>0 for r in group),added_frames=sum(r['added_frames'] for r in group),successful_nulls=sum(r['successful_null'] for r in group),worst_f1=min(r['delta']['f1'] for r in group),positive_candidates=sum(r['positive_candidates'] for r in group),positive_wrong_sign=sum(r['positive_wrong_sign'] for r in group))
    result=dict(status='COMPLETED_ONE_INTERCEPT_REPAIR_REVIEW_REQUIRED',summary={**{c:summary([r for r in rows if r['cohort']==c]) for c in selections},'all19':summary(rows)},sources=rows,all19_previously_exposed=True,new_blind_confirmation=False,automatic_production=False,official_joint_score=None,new_8B=0,formal_data_read=False,utc=helper.utc())
    save(out/'result.json',result);print(json.dumps(result['summary']),flush=True)


if __name__=='__main__':
    try:
        require(os.name=='posix','Linux resident only');main()
    except BaseException as error:
        import traceback,uuid
        save(ROOT/('failure_'+uuid.uuid4().hex+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),original_successes_preserved=True,no_automatic_retry=True))
        raise
