"""Finite four-head fit; historically exposed but train-isolated source evaluation."""
import sys
from common_runtime import *

def main():
    import numpy as np
    import torch
    from scipy_bridge_reuse import loadmat
    sys.path.insert(0,str(ROOT))
    from score_residual_head_v1.contracts import build_contract
    from score_residual_head_v1.head import TrainingVideo,train_head,native_prediction,ResidualHead
    torch.set_num_threads(2)
    proto=read(ROOT/'protocol.json'); read(ROOT/'feature_completion.json')
    calibration=read(ROOT/'calibration_protocol_04.json')
    require(read(ROOT/'evaluation/result.json')['status']=='STOP_NO_DEV_HEAD_PASSED','Only no-original-dev-PASS branch')
    require(not (ROOT/'evaluation/selection_before_holdout.json').exists() and not (ROOT/'evaluation/holdout.json').exists(),'Original head holdout was opened')
    for src in proto['sources']:
        if src['role']=='holdout':require(not (ROOT/'label_arrays'/(src['name']+'.npy')).exists(),'Heldout MAT opened before calibration freeze')
    out=ROOT/'calibration04';out.mkdir(exist_ok=False)
    examples={}; refs={}; raw_features={}; natives={}
    for src in proto['sources']:
        sid=src['id']; native=np.load(ROOT/'inputs'/sid/'native.npz')
        vision=np.load(ROOT/'features'/sid/'vision.npy').astype(np.float32)
        require(vision.shape[0]==len(native['sample_ordinals']),'Feature identity')
        # Four predeclared feature families: instantaneous vision, local mean,
        # absolute temporal change, original baseline cell occupancy.
        local=np.stack([vision[max(0,j-4):min(len(vision),j+5)].mean(0) for j in range(len(vision))])
        delta=np.abs(vision-np.vstack([vision[:1],vision[:-1]]))
        occupancy=np.array([native['baseline'][native['groups']==j].mean() for j in range(len(vision))],np.float32)[:,None]
        raw_features[sid]=np.concatenate([vision,local,delta,occupancy],axis=1)
        natives[sid]={k:native[k] for k in native.files}
    train_ids=[s['id'] for s in proto['sources'] if s['role']=='train']
    normalization=np.load(ROOT/'evaluation/normalization.npz')
    mean=normalization['mean'];std=normalization['std']
    import shutil
    shutil.copyfile(ROOT/'evaluation/normalization.npz',out/'normalization.npz')
    def load_reference(src):
        sid=src['id'];gt=ROOT/'GT'/(src['name']+'.mat')
        require(sha(gt)==src['annotation_sha256'],'Original human MAT changed')
        scores=np.asarray(loadmat(gt)['user_score'])
        require(scores.ndim==2 and len(scores)==len(natives[sid]['baseline']) and np.isfinite(scores).all(),'No label stretching/truncation allowed')
        return scores>0
    # Holdout outcomes are not opened or computed until the selection is saved.
    for src in proto['sources']:
        sid=src['id']
        if src['role']=='holdout':soft=[None]*len(natives[sid]['baseline'])
        else:
            refs[sid]=load_reference(src)
            soft=refs[sid].mean(1).tolist()
        c=read(ROOT/'inputs'/sid/'clock.json')
        contract=build_contract(natives[sid]['groups'].tolist(),natives[sid]['baseline'].tolist(),soft,len(raw_features[sid]),c['normalized_exact_pts'])
        feats=torch.from_numpy(((raw_features[sid]-mean)/std).clip(-10,10).copy())
        examples[sid]=TrainingVideo(sid,feats,contract)
    def metrics(mask,sid):
        p=np.asarray(mask,dtype=bool);g=refs[sid]
        inter=(g&p[:,None]).sum(0);pred=int(p.sum());gt=g.sum(0)
        require(bool((gt>0).all()),'Unexpected empty human rater: handle explicitly in new protocol')
        return dict(f1=float((2*inter/(pred+gt)).mean()),precision=float((inter/max(1,pred)).mean()),recall=float((inter/gt).mean()),frames=pred,native_frames=len(p))
    baseline={sid:metrics(v.contract.baseline_native,sid) for sid,v in examples.items() if sid in refs}
    write(out/'adopted_baseline_metrics.json',dict(scope='Original successful B0 on SumMe, NOT exact VERIFY40.46 outputs; no official joint GT',sources=baseline))
    def result(model,role):
        rows=[]
        for s in proto['sources']:
            if s['role']!=role:continue
            sid=s['id'];v=examples[sid]
            with torch.no_grad():mask=native_prediction(model(v.features),v.contract)
            m=metrics(mask,sid);b=baseline[sid]
            rows.append(dict(id=sid,name=s['name'],baseline=b,candidate=m,delta=m['f1']-b['f1'],changed_frames=sum(x!=y for x,y in zip(mask,v.contract.baseline_native))))
        return dict(role=role,sources=rows,macro_delta=float(np.mean([x['delta'] for x in rows])),macro_f1=float(np.mean([x['candidate']['f1'] for x in rows])),worst_delta=min(x['delta'] for x in rows),changed_sources=sum(x['changed_frames']>0 for x in rows),empty_sources=sum(x['candidate']['frames']==0 for x in rows))
    def passes(r):
        return r['macro_delta']>=0.005 and r['worst_delta']>=-0.10 and r['changed_sources']>=2 and r['empty_sources']<=1
    import math
    candidates=[]
    for arm in proto['training']['arms']:
        for seed in proto['training']['seeds']:
            original_label=arm+'_'+str(seed)
            receipt=read(ROOT/'evaluation'/(original_label+'.json'))['training']
            for tau in calibration['thresholds_probability']:
                label=original_label+'_TAU%02d'%round(tau*100)
                model=ResidualHead(examples[train_ids[0]].features.shape[1],64)
                model.load_state_dict(torch.load(ROOT/'evaluation'/(original_label+'.pt'),weights_only=True));model.eval()
                with torch.no_grad():model.network[-1].bias.add_(-math.log(tau/(1-tau)))
                dev=result(model,'dev')
                write(out/(label+'.json'),dict(original_head=original_label,tau=tau,dev=dev,dev_pass=passes(dev),old_head_failure_unchanged=True,new_optimizer_updates=0))
                candidates.append((dev['macro_f1'],label,dev,dict(original_label=original_label,tau=tau)))
                event('CALIBRATION_DEV_DONE',label=label,macro_delta=dev['macro_delta'],passed=passes(dev))
    eligible=[x for x in candidates if passes(x[2])]
    if not eligible:
        write(out/'result.json',dict(status='STOP_NO_CALIBRATED_DEV_HEAD_PASSED',new_production_allowed=False,candidates=[dict(label=x[1],dev=x[2]) for x in candidates],old_failures_unchanged=True))
        return
    chosen=sorted(eligible,key=lambda x:(-x[0],x[1]))[0];label=chosen[1]
    model=ResidualHead(examples[train_ids[0]].features.shape[1],64)
    model.load_state_dict(torch.load(ROOT/'evaluation'/(chosen[3]['original_label']+'.pt'),weights_only=True));model.eval()
    with torch.no_grad():model.network[-1].bias.add_(-math.log(chosen[3]['tau']/(1-chosen[3]['tau'])))
    torch.save(model.state_dict(),out/(label+'.pt'))
    write(out/'selection_before_holdout.json',dict(label=label,weights_sha256=sha(out/(label+'.pt')),normalization_sha256=sha(out/'normalization.npz'),chosen_only_from_dev=True,historical_exposure_disclosed=True))
    for src in proto['sources']:
        if src['role']=='holdout':
            sid=src['id'];refs[sid]=load_reference(src)
            baseline[sid]=metrics(examples[sid].contract.baseline_native,sid)
    model=ResidualHead(examples[train_ids[0]].features.shape[1],64);model.load_state_dict(torch.load(out/(label+'.pt'),weights_only=True));model.eval()
    held=result(model,'holdout');write(out/'holdout.json',held)
    write(out/'result.json',dict(status='PASS_SOURCE_ISOLATED_SUMMARY_PROXY' if passes(held) else 'STOP_HELDOUT_PROXY_REJECTED',selected=label,holdout=held,new_production_allowed=passes(held),scope='Historically exposed SumMe human summary proxy, source held out only for this new head; no spatial/official joint score claim',head_parameters=model.parameter_count,resident_parameters=8782459120+model.parameter_count))
    event('EXTERNAL_EXPERIMENT_COMPLETE',passed=passes(held),label=label,macro_delta=held['macro_delta'])

if __name__=='__main__':main()
