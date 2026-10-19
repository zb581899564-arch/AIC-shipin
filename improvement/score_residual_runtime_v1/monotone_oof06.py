"""One new smaller source-relative recipe; OOF is not fresh blind confirmation."""
import sys
from common_runtime import *

def main():
    import numpy as np
    import torch
    sys.path.insert(0,str(ROOT))
    from monotone_head06 import TrainingVideo,ResidualHead,train_head,native_prediction
    from score_residual_head_v1.contracts import build_contract
    from scipy_bridge_reuse import loadmat
    torch.set_num_threads(2)
    require(read(ROOT/'relative_oof05/result.json')['status']=='STOP_MONOTONE_OOF_REJECTED','Previous actual failure preserved')
    proto=read(ROOT/'monotone_oof_protocol06.json');out=ROOT/'monotone_oof06';out.mkdir(exist_ok=False)
    examples={};refs={};baseline={}
    for s in proto['sources']:
        sid=s['id'];n=np.load(ROOT/'inputs'/sid/'native.npz');v=np.load(ROOT/'features'/sid/'vision.npy').astype(np.float32)
        center=v.mean(axis=0,dtype=np.float64).astype(np.float32)
        scale=max(1e-6,float(np.sqrt(np.mean((v-center).astype(np.float64)**2))))
        local=np.stack([v[max(0,j-4):min(len(v),j+5)].mean(0) for j in range(len(v))])
        delta=np.abs(v-np.vstack([v[:1],v[:-1]]));ds=max(1e-6,float(np.sqrt(np.mean(delta.astype(np.float64)**2))))
        occupancy=np.array([n['baseline'][n['groups']==j].mean() for j in range(len(v))],np.float32)[:,None]
        x=np.concatenate([(v-center)/scale,(local-center)/scale,delta/ds,occupancy-occupancy.mean()],axis=1)
        require(np.isfinite(x).all(),'Finite label-free within-source features')
        gt=ROOT/'GT'/(s['name']+'.mat');require(sha(gt)==s['annotation_sha256'],'Original research human reference changed')
        scores=loadmat(gt)['user_score'];require(scores.shape[0]==len(n['baseline']),'No reference resampling')
        refs[sid]=scores>0
        c=build_contract(n['groups'].tolist(),n['baseline'].tolist(),refs[sid].mean(1).tolist(),len(v),read(ROOT/'inputs'/sid/'clock.json')['normalized_exact_pts'])
        rater_counts=np.zeros((len(c.n),refs[sid].shape[1]),dtype=np.float32)
        np.add.at(rater_counts,np.asarray(c.native_unit),refs[sid].astype(np.float32))
        examples[sid]=TrainingVideo(sid,torch.from_numpy(x.copy()),c,torch.from_numpy(rater_counts))
        write(out/(sid+'_feature_transform.json'),dict(center_axis='time',RMS_axes='all_times_and_4096_dimensions',source_RMS=scale,delta_RMS=ds,epsilon=1e-6,original_frozen_feature_sha256=sha(ROOT/'features'/sid/'vision.npy'),no_label_in_feature_transform=True))
    def metric(mask,sid):
        p=np.array(mask,dtype=bool);g=refs[sid];count=int(p.sum());inter=(g&p[:,None]).sum(0);gcount=g.sum(0)
        require(bool((gcount>0).all()),'Unexpected empty rater')
        return dict(f1=float((2*inter/(count+gcount)).mean()),precision=float((inter/max(1,count)).mean()),recall=float((inter/gcount).mean()),selected=count)
    for sid,v in examples.items():baseline[sid]=metric(v.contract.baseline_native,sid)
    oof=[];training=[]
    for fold in range(5):
        train_ids=[s['id'] for s in proto['sources'] if s['fold']!=fold];held_ids=[s['id'] for s in proto['sources'] if s['fold']==fold]
        require(len(train_ids)==20 and len(held_ids)==5 and not set(train_ids)&set(held_ids),'Source-isolated new head fitting')
        event('MONOTONE_OOF_TRAIN_START',fold=fold,train_sources=train_ids,held_sources=held_ids)
        model,receipt=train_head([examples[x] for x in train_ids],'SCORE',105,updates=100,hidden_dim=8,learning_rate=.003,margin=1.,score_weight=10.)
        path=out/('fold%d.pt'%fold);torch.save(model.state_dict(),path)
        training.append(dict(fold=fold,training=receipt,weights_sha256=sha(path)))
        for sid in held_ids:
            v=examples[sid]
            with torch.no_grad():r=model(v.features).detach();mask=native_prediction(r,v.contract)
            m=metric(mask,sid);b=baseline[sid]
            oof.append(dict(id=sid,fold=fold,baseline=b,candidate=m,delta=m['f1']-b['f1'],changed_frames=sum(x!=y for x,y in zip(mask,v.contract.baseline_native))))
        rows=[z for z in oof if z['fold']==fold]
        write(out/('fold%d.json'%fold),dict(training=receipt,sources=rows,macro_delta=float(np.mean([x['delta'] for x in rows]))))
        event('MONOTONE_OOF_FOLD_DONE',fold=fold,macro_delta=float(np.mean([x['delta'] for x in rows])))
    require(len(oof)==25 and len({x['id'] for x in oof})==25,'No source omitted from OOF denominator')
    delta=float(np.mean([x['delta'] for x in oof]));fold_deltas=[float(np.mean([x['delta'] for x in oof if x['fold']==k])) for k in range(5)]
    worst=min(x['delta'] for x in oof);changed=sum(x['changed_frames']>0 for x in oof);empty=sum(x['candidate']['selected']==0 for x in oof)
    passed=delta>=.005 and min(fold_deltas)>=-.01 and worst>=-.10 and changed>=10 and empty<=5
    evidence=dict(macro_delta=delta,fold_macro_deltas=fold_deltas,worst_source_delta=worst,changed_sources=changed,empty_sources=empty,sources=oof,interpretation='Historically exposed reference; training-source isolated OOF for this recipe, not fresh blind/general unbiased/official joint confirmation')
    write(out/'oof_result.json',dict(status='PASS_FIXED_EXPLORATORY_OOF_GATE' if passed else 'STOP_MONOTONE_OOF_REJECTED',passed=passed,**evidence))
    if not passed:
        write(out/'result.json',dict(status='STOP_MONOTONE_OOF_REJECTED',new_production_allowed=False,new_optimizer_updates=500,**evidence));return
    # The final model has no separate unseen reference. Its production use is
    # explicitly a bounded unknown-effect exploration, not OOF score attribution.
    event('MONOTONE_FINAL25_TRAIN_START')
    final,receipt=train_head([examples[s['id']] for s in proto['sources']],'SCORE',105,updates=100,hidden_dim=8,learning_rate=.003,margin=1.,score_weight=10.)
    path=out/'final25.pt';torch.save(final.state_dict(),path)
    check=ResidualHead(examples[proto['sources'][0]['id']].features.shape[1],8);check.load_state_dict(torch.load(path,weights_only=True))
    require(all(torch.equal(a,b) for a,b in zip(final.parameters(),check.parameters())),'Final actual head save/reload')
    write(out/'final_training.json',receipt)
    write(out/'result.json',dict(status='PASS_OOF_EXPLORATION_FINAL25_NO_POSTFIT_QUALITY_REFERENCE',new_production_allowed=True,new_optimizer_updates=600,weights_path=str(path),weights_sha256=sha(path),head_parameters=final.parameter_count,resident_parameters=8782459120+final.parameter_count,training=receipt,**evidence))
    event('MONOTONE_OOF_COMPLETE',passed=True,macro_delta=delta)

if __name__=='__main__':
    try:main()
    except BaseException as error:
        import traceback
        write(ROOT/'monotone_oof06_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
