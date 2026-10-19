"""Single fixed source-conditioned relative-gain critic; CPU only, no IO on import."""
from __future__ import annotations
from fractions import Fraction
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import time
import traceback
import numpy as np
import direct_box_math_v84 as geometry84
import direct_box_trust_projection_v124 as trust124

PCA_DIM=32
FEATURES=107
ADDITIONAL_PARAMETERS=4096+4096*32+107+107+11
PIPELINE_PARAMETERS=8790237452+ADDITIONAL_PARAMETERS
RECIPE=dict(train_sources=602,pca_components=32,hidden='EXISTING105_F32_L2_H4096',pca='TRAIN_ONLY_CENTERED_NOT_WHITENED_MAX_ABS_LOADING_POSITIVE',
    feature='DELTA_GEOMETRY11_CONCAT_PC32_OUTER_DELTA_NORMALIZED_XYW3_C_ORDER',intercept=False,independent_hidden_term=False,
    ridge=1.,source_weight='SUM602_OF_MEAN24_ROW_SSE_PLUS_ONE_BETA_SQUARED',feature_RMS='SOURCE_EQUAL_TRAIN107_RMS_ZERO_COLUMNS_USE1',
    target='ORIGINAL_HUMAN_IOU_PROJECTED_PROPOSAL_MINUS_BASELINE',baselines_per_source=6,proposals_per_baseline=2,
    proposals=['POOL_NEXT_MOD6','ACTUAL105_DIRECT'],trust='EXACT124_1024_GRID_IOU_AT_LEAST9_OVER10',
    reverse='NEGATE_ACTUAL_SAME_B_P_FEATURE_AND_GAIN_WITHOUT_REPROJECTING',rows_per_source=24,total_projections=7224,total_rows=14448,
    accept='PREDICTED_GAIN_STRICTLY_GREATER_THAN0',fit_count=1,development_scopes=[20,19],development_not_blind=True)


def require(value,message):
    if not value:raise ValueError(message)


def geometry11(box,W,H):
    require(geometry84.legal_native(box,W,H),'Only original legal native3 geometry')
    x,y,w=np.asarray(box,np.float64)/np.array([W,H,W],np.float64);h=9*float(box[2])/(16*H)
    return np.array([x,y,w,h,x*x,y*y,w*w,h*h,x*y,x*w,y*h],np.float64)


def trust_project_native3(base,direct,W,H):
    """Same fixed124 policy, integer vectorized grid; exact final certificate."""
    require(geometry84.legal_native(base,W,H) and geometry84.legal_native(direct,W,H),'Original native3 baseline and actual DIRECT')
    limit=np.iinfo(np.int64).max
    require(max(W,H)*2048<=limit and W*H*2560<=limit,'Exact int64 arithmetic capacity, no overflow in fixed grid/area comparison')
    b=np.asarray(base,np.int64);d=np.asarray(direct,np.int64);k=np.arange(1024,0,-1,dtype=np.int64)
    numerator=b[None,:]*1024+k[:,None]*(d-b)[None,:];q,r=np.divmod(numerator,1024)
    rounded=q+(2*r>1024);w=np.clip(rounded[:,2],1,min(W,16*H//9))
    x=np.minimum(np.maximum(rounded[:,0],0),W-w);y=np.minimum(np.maximum(rounded[:,1],0),(16*H-9*w)//16)
    iw=np.maximum(0,np.minimum(16*(x+w),16*(b[0]+b[2]))-np.maximum(16*x,16*b[0]))
    ih=np.maximum(0,np.minimum(16*y+9*w,16*b[1]+9*b[2])-np.maximum(16*y,16*b[1]))
    intersection=iw*ih;union=144*w*w+144*b[2]*b[2]-intersection
    valid=np.flatnonzero(10*intersection>=9*union)
    if len(valid):
        i=int(valid[0]);box=[int(x[i]),int(y[i]),int(w[i])];alpha=int(k[i])
    else:box=list(map(int,base));alpha=0
    exact=trust124.exact_iou(box,base);require(exact>=Fraction(9,10),'Exact124 final rational certificate')
    return dict(box3=box,alpha_k=alpha,fallback=alpha==0,exact_iou=dict(numerator=exact.numerator,denominator=exact.denominator))


def fit_pca(normalized_hidden):
    h=np.asarray(normalized_hidden,np.float64)
    require(h.ndim==2 and h.shape[1]==4096 and h.shape[0]>32 and bool(np.isfinite(h).all()),'Original train-only normalized hidden4096')
    mean=h.mean(axis=0);centered=h-mean;gram=centered@centered.T
    values,vectors=np.linalg.eigh(gram);order=np.argsort(values)[::-1][:32];eigen=values[order]
    require(bool((eigen>0).all()),'At least32 train-only positive PCA directions; do not reduce dimension after inspection')
    components=centered.T@vectors[:,order]/np.sqrt(eigen)[None,:]
    components/=np.linalg.norm(components,axis=0)[None,:]
    for column in range(32):
        pivot=int(np.argmax(np.abs(components[:,column])))
        if components[pivot,column]<0:components[:,column]*=-1
    require(np.allclose(components.T@components,np.eye(32),rtol=1e-7,atol=1e-7),'Finite orthonormal train PCA32')
    return mean,components,dict(explained_variance_fraction=float(eigen.sum()/np.trace(gram)),training_rows=len(h),development_rows_used=0)


def relative_features(pc32,baseline,proposal,W,H):
    pc=np.asarray(pc32,np.float64);require(pc.shape==(32,) and bool(np.isfinite(pc).all()),'Fixed finite source-only PCA32')
    delta=geometry11(proposal,W,H)-geometry11(baseline,W,H)
    xyw=(np.asarray(proposal,np.float64)-np.asarray(baseline,np.float64))/np.array([W,H,W],np.float64)
    result=np.concatenate((delta,np.outer(pc,xyw).reshape(-1)))
    require(result.shape==(107,) and bool(np.isfinite(result).all()),'Antisymmetric107 feature without intercept or independent h')
    return result


def fit_ridge(source_features,source_gains):
    features=np.asarray(source_features,np.float64);gains=np.asarray(source_gains,np.float64)
    require(features.ndim==3 and features.shape[1:]==(24,107) and gains.shape==features.shape[:2]
        and bool(np.isfinite(features).all()) and bool(np.isfinite(gains).all()),'Source-owned24-row exact features and gains')
    rms=np.sqrt(np.mean(np.mean(features*features,axis=1),axis=0));rms[rms==0]=1.
    x=(features/rms).reshape(-1,107);y=gains.reshape(-1);denominator=24
    covariance=(x.T@x)/denominator;rhs=(x.T@y)/denominator
    joint=np.linalg.solve(covariance+np.eye(107),rhs)
    geom=np.linalg.solve(covariance[:11,:11]+np.eye(11),rhs[:11])
    require(bool(np.isfinite(joint).all()) and bool(np.isfinite(geom).all()),'One finite ridge1 solve, no hyperparameter scan')
    return rms,joint,geom,dict(JOINT_train_MSE=float(np.mean((x@joint-y)**2)),GEOM11_train_MSE=float(np.mean((x[:,:11]@geom-y)**2)))


def fit_critic(sources,targets,normalized_hidden,direct_boxes,*,check_budget=lambda:None):
    require(len(sources)==len(targets)==602 and len({s['source_id'] for s in sources})==602,'Exactly602 unique train sources')
    labels={t['source_id']:t for t in targets};h=np.asarray(normalized_hidden,np.float64);direct=np.asarray(direct_boxes)
    require(h.shape==(602,4096) and direct.shape==(602,3) and len(labels)==602 and set(labels)=={s['source_id'] for s in sources},'Exact cache/target/train owner inventory')
    check_budget();mean,components,pca=fit_pca(h);pcs=(h-mean)@components
    x=np.empty((602,24,107),np.float64);y=np.empty((602,24),np.float64);self_rows=0;projected=0
    for index,s in enumerate(sources):
        check_budget();t=labels[s['source_id']];W,H=s['width'],s['height'];pool=s['pool']
        require(s['role']==t['role']=='train' and len(pool)==6 and t['source_sha256']==s['source_sha256']
            and t['width']==W and t['height']==H and t['reference_modified'] is False,'Original unchanged source-owned train GT/native6pool')
        target=t['original_reference_xywh'];geometry84.target_xywh(target,W,H);row=0
        for baseline_index,baseline in enumerate(pool):
            for proposal in (pool[(baseline_index+1)%6],list(map(int,direct[index]))):
                p=trust_project_native3(baseline,proposal,W,H)['box3'];projected+=1
                feature=relative_features(pcs[index],baseline,p,W,H)
                gain=geometry84.crop_iou(p,target,W,H)-geometry84.crop_iou(baseline,target,W,H)
                x[index,row]=feature;y[index,row]=gain;x[index,row+1]=-feature;y[index,row+1]=-gain
                if p==baseline:
                    require(np.count_nonzero(feature)==0 and gain==0.,'Actual self exactly0');self_rows+=2
                require(np.array_equal(x[index,row+1],-x[index,row]) and y[index,row+1]==-y[index,row],'Exact actual-same-pair reverse, no second projection')
                row+=2
    check_budget();rms,joint,geom,fit=fit_ridge(x,y)
    state=dict(hidden_mean=mean,PCA_components=components,RMS=rms,JOINT_beta=joint,GEOM11_beta=geom)
    return state,dict(pca=pca,fit=fit,train_sources=602,projections=projected,rows=602*24,self_rows=self_rows,
        source_equal=True,reverse_projection_calls=0,fit_count=1,intercept=False,additional_parameters=ADDITIONAL_PARAMETERS,
        pipeline_parameters=PIPELINE_PARAMETERS,recipe=RECIPE)


def validate_state(state):
    shapes=dict(hidden_mean=(4096,),PCA_components=(4096,32),RMS=(107,),JOINT_beta=(107,),GEOM11_beta=(11,))
    require(set(state)==set(shapes),'Exact critic state with no hidden intercept/model')
    for key,shape in shapes.items():
        value=state[key];require(isinstance(value,np.ndarray) and value.dtype==np.float64 and value.shape==shape and bool(np.isfinite(value).all()),'Finite F64 critic array '+key)
    require(bool((state['RMS']>0).all()),'Positive train-only feature RMS')


def save_reload_state(path,state):
    validate_state(state);path=Path(path)
    with path.open('xb') as stream:np.savez(stream,**state);stream.flush();os.fsync(stream.fileno())
    with np.load(path,allow_pickle=False) as loaded:reloaded={k:loaded[k].copy() for k in loaded.files}
    validate_state(reloaded);require(all(np.array_equal(state[k],reloaded[k]) for k in state),'Actual final state save/reload exact')
    return reloaded


def predict_gain(state,normalized_hidden,baseline,proposal,W,H,*,arm='JOINT'):
    h=np.asarray(normalized_hidden,np.float64);require(h.shape==(4096,) and bool(np.isfinite(h).all()),'Existing105 normalized source-only feature')
    pc=(h-state['hidden_mean'])@state['PCA_components'];feature=relative_features(pc,baseline,proposal,W,H)/state['RMS']
    if arm=='JOINT':return float(feature@state['JOINT_beta'])
    require(arm=='GEOM11','Only frozen JOINT or same-ridge GEOM11 control')
    return float(feature[:11]@state['GEOM11_beta'])


def evaluate_scope(state,sources,targets,normalized_hidden,direct_boxes,controls,*,scope):
    require(scope in ('native20','historical19'),'Only two pre-registered exposed development scopes')
    n=20 if scope=='native20' else 19;h=np.asarray(normalized_hidden,np.float64);direct=np.asarray(direct_boxes)
    labels={t['source_id']:t for t in targets};ids=[s['source_id'] for s in sources]
    require(len(sources)==len(targets)==len(set(ids))==n and set(labels)==set(ids) and h.shape==(n,4096) and direct.shape==(n,3),'Exact fixed unweighted development owners')
    require(set(controls)=={'OLD70_BETA_GEOMETRY','OLD47_GEOM11','OLD33_GEOM13'} and all(set(c['source_ids'])==set(ids) and len(c['source_ids'])==n for c in controls.values()),'Same-scope three geometry controls, no20 means in19')
    rows={arm:[] for arm in ('JOINT','GEOM11','ALWAYS_ACCEPT124')};true_rejects=0
    for index,s in enumerate(sources):
        t=labels[s['source_id']];W,H=s['width'],s['height'];base=s['pool'][0];require(base==s['baseline_box'] and s['original_BASE_observed'] is True
            and t['source_sha256']==s['source_sha256'] and t['reference_modified'] is False,'Immutable observed B0 and source-owned original GT')
        p=trust_project_native3(base,list(map(int,direct[index])),W,H)['box3'];old=geometry84.crop_iou(base,t['original_reference_xywh'],W,H)
        for arm in rows:
            value=None if arm=='ALWAYS_ACCEPT124' else predict_gain(state,h[index],base,p,W,H,arm=arm)
            chosen=p if value is None or value>0 else base
            if arm=='JOINT' and p!=base and chosen==base:true_rejects+=1
            require(predict_gain(state,h[index],base,base,W,H,arm='JOINT')==0.
                and predict_gain(state,h[index],p,base,W,H,arm='JOINT')==-predict_gain(state,h[index],base,p,W,H,arm='JOINT'),'Exact self0/swap negative')
            iou=geometry84.crop_iou(chosen,t['original_reference_xywh'],W,H)
            rows[arm].append(dict(source_id=s['source_id'],source_sha256=s['source_sha256'],baseline_iou=float(old),selected_iou=float(iou),gain=float(iou-old),
                baseline_box=base,trust_box=p,native_box=chosen,predicted_gain=value,changed=chosen!=base,trust_changed=p!=base))
    reports={}
    for arm,items in rows.items():
        mean=float(np.mean([r['selected_iou'] for r in items]));baseline=float(np.mean([r['baseline_iou'] for r in items]))
        checks=dict(exact_sources=len(items)==n,minimum_gain=mean-baseline>=.01,at_least5_improved=sum(r['gain']>0 for r in items)>=5,
            worst_loss_at_most_point1=max(0.,max(-r['gain'] for r in items))<=.1,actual_change=any(r['changed'] for r in items),invalid0=True)
        checks.update({'beats_'+name:mean>c['mean_iou'] for name,c in controls.items()})
        reports[arm]=dict(summary=dict(sources=n,mean_selected_iou=mean,mean_baseline_iou=baseline,mean_gain=mean-baseline,
            improved=sum(r['gain']>0 for r in items),worst_loss=max(0.,max(-r['gain'] for r in items)),changed=sum(r['changed'] for r in items),invalid=0),
            quality=dict(admitted=all(checks.values()),checks=checks),rows=items)
    joint=reports['JOINT'];joint['quality']['checks'].update(actual_changed_trust_rejected=true_rejects>=1,
        beats_always_accept124=joint['summary']['mean_selected_iou']>reports['ALWAYS_ACCEPT124']['summary']['mean_selected_iou'],
        beats_same_ridge_GEOM11=joint['summary']['mean_selected_iou']>reports['GEOM11']['summary']['mean_selected_iou'],selfzero_swap_exact=True)
    joint['quality']['admitted']=all(joint['quality']['checks'].values())
    return dict(scope=scope,arms=reports,JOINT_admitted=joint['quality']['admitted'],changed_trust_rejected=true_rejects,historical_not_blind=True,
        static_not_official_joint_quality=True,new_model_calls=0,new_fit=0)


def _json_value(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)


def _save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False,default=_json_value);f.write('\n');f.flush();os.fsync(f.fileno())


def run(root,registration):
    import torch
    import direct_box_math_preclamp_v105 as math105
    import direct_box_review_v84 as review84
    root=Path(root).resolve();registration=Path(registration).resolve()
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and root.is_relative_to(review84.WORK)
        and registration==root/'direct_box_relative_critic_registration_128.json','One explicit CPU-only128 registration')
    reg=review84.read(registration);load=lambda r:review84.read(review84.bound(r))
    require(reg['schema']=='FROZEN_SOURCE_CONDITIONED_RELATIVE_GAIN_CRITIC_CPU_V128' and reg['recipe']==RECIPE
        and review84.bound(reg['code'])==Path(__file__).resolve() and review84.bound(reg['math105_code'])==Path(math105.__file__).resolve()
        and review84.bound(reg['trust124_code'])==Path(trust124.__file__).resolve()
        and review84.bound(reg['frozen_review84_code'])==Path(review84.__file__).resolve(),'Exact registered128 recipe and frozen helpers')
    budget=load(reg['trial_budget']);deadline=dt.datetime.fromisoformat(budget['deadline_utc'].replace('Z','+00:00'))
    start=dt.datetime.fromisoformat(budget['start_utc'].replace('Z','+00:00'))
    require(0<(deadline-start).total_seconds()<=600,'One immutable whole127/QA/128/development budget of at most600 seconds')
    def check_budget():require(dt.datetime.now(dt.timezone.utc)<deadline,'Whole relative-critic trial budget expired; preserve success and STOP')
    check_budget();qa=load(reg['train_feature_acceptance']);weights=('training_completion','adapter_weights','head_weights')
    require(qa['status']=='PASS_DIRECT_BOX127_TRAIN602_FIRST_RAW_HEAD_NATIVE_CPU_QA'
        and qa['feature_schema']=='DIRECT_BOX127_ACCEPTED_TRAIN602_SOURCE_FEATURES' and qa['accepted_features']==reg['accepted_features']
        and all(qa[k]==reg[k] for k in weights),'Only actual accepted602 final105 first features, never repeat raw QA')
    trained=load(reg['training_completion'])
    require(trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY' and trained['completed_updates']==778
        and trained['successful_micro']==trained['actual_training_forwards']==3112 and trained['total_adopted_plus_new_updates']==798
        and all(trained[k]==reg[k] for k in ('adapter_weights','head_weights')),'Frozen supervised final105 model identity')
    with np.load(review84.bound(reg['accepted_features']),allow_pickle=False) as f:cache={k:f[k].copy() for k in f.files}
    sources=[s for s in load(reg['train_source_catalog'])['sources'] if s['role']=='train'];targets=load(reg['train_targets'])['sources']
    require(len(sources)==602 and cache['normalized_hidden4096'].dtype==np.float32 and cache['normalized_hidden4096'].shape==(602,4096)
        and cache['native_DIRECT3'].dtype==np.int64 and cache['native_DIRECT3'].shape==(602,3)
        and len(cache['source_ids'])==len(set(cache['source_ids'].tolist()))==602,'Complete compact accepted127 source-only cache')
    lookup={str(s):i for i,s in enumerate(cache['source_ids'])};indices=[]
    for source in sources:
        i=lookup[source['source_id']]
        require(str(cache['source_sha256'][i])==source['source_sha256'] and int(cache['width'][i])==source['width']
            and int(cache['height'][i])==source['height'],'Exact127 cache/native source/hash/dimensions')
        indices.append(i)
    hidden=cache['normalized_hidden4096'][indices];direct=cache['native_DIRECT3'][indices]
    require(bool(np.isfinite(hidden).all()) and np.allclose(np.linalg.norm(hidden.astype(np.float64),axis=1),1.,atol=1e-6,rtol=0.),'Actual105 F32 L2 cache, no reprocessing or replacement feature')
    out=root/'direct_box_relative_critic_128';out.mkdir(exist_ok=False);started=time.monotonic()
    try:
        check_budget();state,fit=fit_critic(sources,targets,hidden,direct,check_budget=check_budget)
        state_path=out/'state.npz';state=save_reload_state(state_path,state);check_budget()
        _save(out/'fit.json',dict(fit,state=review84.ref(state_path),registration=review84.ref(registration),trial_budget=reg['trial_budget'],exact_save_reload=True))
        evaluations={}
        for scope in ('native20','historical19'):
            check_budget();entry=reg['development'][scope];accepted=load(entry['output_acceptance'])
            expected_status='PASS_DIRECT_BOX105_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA' if scope=='native20' else 'PASS_DIRECT_BOX109_CONFIRM19_FIRST_RAW_HEAD_CPU_QA'
            require(accepted['status']==expected_status and all(accepted[k]==reg[k] for k in weights),'Existing same-model39 firstQA only, no forward/head replay')
            wanted='screen' if scope=='native20' else 'confirm'
            dev_sources=[s for s in load(entry['source_catalog'])['sources'] if s['role']==wanted]
            predictions={p['source_id']:p for p in accepted['predictions']};dev_h=[];dev_direct=[]
            for source in dev_sources:
                p=predictions[source['source_id']];request=load(p['input'])
                require(p['source_sha256']==request['source_sha256']==source['source_sha256']
                    and request['source_id']==source['source_id'] and request['width']==source['width'] and request['height']==source['height'],'Exact existing development source/input/feature ownership')
                original=torch.load(review84.bound(p['raw_hidden']),map_location='cpu',weights_only=True)
                require(original.dtype==torch.float32 and tuple(original.shape)==(4096,) and not original.requires_grad,'Previously QA accepted original F32hidden4096')
                dev_h.append(math105.normalize_hidden(original).numpy());dev_direct.append(p['native_boxes']['DIRECT'])
            # Targets are CPU-only and are opened after the single final state is saved/reloaded.
            dev_targets=load(entry['CPU_targets'])['sources'];control_result=load(entry['geometry_controls'])
            controls=review84.controls_from_utility70(control_result,[s['source_id'] for s in dev_sources]) if scope=='native20' else control_result['controls']
            check_budget();evaluations[scope]=evaluate_scope(state,dev_sources,dev_targets,np.stack(dev_h),np.asarray(dev_direct),controls,scope=scope);check_budget()
        admitted=all(e['JOINT_admitted'] for e in evaluations.values());check_budget()
        _save(out/'result.json',dict(status=('PASS_' if admitted else 'STOP_')+'DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC',
            admitted_arms=['JOINT'] if admitted else [],evaluations=evaluations,registration=review84.ref(registration),state=review84.ref(state_path),
            train_feature_acceptance=reg['train_feature_acceptance'],trial_budget=reg['trial_budget'],training_completion=reg['training_completion'],
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],recipe=RECIPE,fit=fit,elapsed_CPU_seconds=time.monotonic()-started,
            additional_parameters=ADDITIONAL_PARAMETERS,pipeline_parameters=PIPELINE_PARAMETERS,exact_save_reload=True,new_model_calls=0,
            historical_development_not_confirmation=True,automatic_fresh8=False,production_admitted=False,original_STOPs_unchanged=True))
    except BaseException as error:
        _save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,automatic_retry=False,new_model_calls=0,original_STOPs_unchanged=True));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--registration',type=Path,required=True)
    args=parser.parse_args();run(args.root,args.registration)
