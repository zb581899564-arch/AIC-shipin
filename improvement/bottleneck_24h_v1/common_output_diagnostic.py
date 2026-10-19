"""Reference-assisted common-output feasibility, never predictions or training."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import pathlib,json,hashlib,datetime as dt
import numpy as np
W=pathlib.Path('/home/inspur/aic_video_work');ROOT=W/'bottleneck_24h_20261019_v1'
def read(p):return json.loads(pathlib.Path(p).read_text())
def ref(p):
    p=pathlib.Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def bound(value):
    p=pathlib.Path(value['path']);a=ref(p);assert a['sha256']==value['sha256'] and ('bytes' not in value or a['bytes']==value['bytes']);return p
def save(p,x):
    with pathlib.Path(p).open('x',encoding='utf8') as s:json.dump(x,s,ensure_ascii=False,indent=2,allow_nan=False)
def score(p,tp,g):
    den=np.asarray(g,dtype=float)+p
    return np.divide(2*np.asarray(tp),den,out=np.ones_like(den),where=den!=0).mean(axis=-1)
def common_prefix(groups,labels,baseline,mode):
    """One shared source output for every rater; only a feasible bound, not exact."""
    groups=np.asarray(groups);baseline=np.asarray(baseline,dtype=bool);labels=np.asarray(labels,dtype=bool)
    n=len(baseline);assert labels.ndim==2 and labels.shape[0]==n and groups.shape==(n,)
    assert groups.dtype.kind in 'iu' and groups.min()>=0
    if mode=='replace':fixed=np.zeros(n,bool);allowed=np.ones(n,bool)
    elif mode=='add':fixed=baseline.copy();allowed=~baseline
    elif mode=='delete':fixed=np.zeros(n,bool);allowed=baseline
    else:raise ValueError(mode)
    count=np.bincount(groups[allowed],minlength=int(groups.max())+1);valid=np.flatnonzero(count)
    positives=np.stack([np.bincount(groups[allowed],weights=labels[allowed,r],minlength=len(count)) for r in range(labels.shape[1])],axis=1)
    density=positives.sum(1)/(np.maximum(count,1)*labels.shape[1]);order=valid[np.argsort(-density[valid],kind='stable')]
    fixed_count=int(fixed.sum());fixed_tp=labels[fixed].sum(0);g=labels.sum(0)
    sizes=np.r_[fixed_count,fixed_count+np.cumsum(count[order])]
    tp=np.concatenate([fixed_tp[None,:],fixed_tp[None,:]+np.cumsum(positives[order],axis=0)])
    values=score(sizes[:,None],tp,g);best=int(np.argmax(values))
    chosen=order[:best];mask=fixed | (allowed & np.isin(groups,chosen))
    actual=float(score(int(mask.sum()),labels[mask].sum(0),g));assert abs(actual-float(values[best]))<1e-12
    assert mode!='add' or np.all(mask[baseline]);assert mode!='delete' or not np.any(mask&~baseline)
    return dict(feasible_common_F1=actual,selected_native_frames=int(mask.sum()),added_native_frames=int((mask&~baseline).sum()),removed_native_frames=int((baseline&~mask).sum()),chosen_units=best,available_units=len(valid),optimism='REFERENCE_ASSISTED_FEASIBLE_LOWER_BOUND_ON_BEST_COMMON_SELECTOR_NOT_EXACT_OPTIMUM',mask_saved=False)
def self_check():
    # Contradictory raters must receive one mask, never a per-rater perfect output.
    groups=np.array([0,0,1,1]);labels=np.array([[1,0],[1,0],[0,1],[0,1]],bool);base=np.array([1,1,0,0],bool)
    r=common_prefix(groups,labels,base,'replace');assert abs(r['feasible_common_F1']-2/3)<1e-12
    a=common_prefix(groups,labels,base,'add');d=common_prefix(groups,labels,base,'delete')
    assert a['removed_native_frames']==0 and d['added_native_frames']==0
    empty=common_prefix(groups,np.zeros((4,2),bool),np.zeros(4,bool),'replace');assert empty['feasible_common_F1']==1 and empty['selected_native_frames']==0
def main():
    self_check();reg=read(ROOT/'common_output_registration_01.json');out=ROOT/'common_output_01';out.mkdir()
    rows=[]
    for s in reg['sources']:
        data=np.load(bound(s['data_ref']),allow_pickle=False);base=data['baseline'];groups=data['groups'];clock=read(bound(s['clock_ref']))
        labels=data['labels'] if s['labels_mode']=='in_data' else np.load(bound(s['labels_ref']),allow_pickle=False)['labels']
        assert base.dtype==labels.dtype==np.bool_ and len(base)==len(clock['normalized_exact_pts'])==len(groups)==len(labels)
        assert np.isfinite(groups).all() and labels.shape[1]>0
        g=labels.sum(0);baseline=float(score(int(base.sum()),labels[base].sum(0),g))
        row=dict(sid=s['sid'],cohort=s['cohort'],native_frames=len(base),raters=labels.shape[1],baseline_native_frames=int(base.sum()),baseline_common_F1=baseline,source_ref=s)
        for mode in ['replace','add','delete']:
            row[mode]=common_prefix(groups,labels,base,mode);row[mode]['delta_vs_baseline']=row[mode]['feasible_common_F1']-baseline
        row['replace']['comparison_with_add']=row['replace']['feasible_common_F1']-row['add']['feasible_common_F1']
        row['spatial_IoU']='UNKNOWN_NO_SPATIAL_LABELS';save(out/(s['sid']+'.json'),row);rows.append(row)
    summary={}
    for cohort in sorted({r['cohort'] for r in rows}):
        src=[r for r in rows if r['cohort']==cohort]
        summary[cohort]=dict(sources=len(src),baseline_F1=float(np.mean([r['baseline_common_F1'] for r in src])),**{mode+'_common_feasible_F1':float(np.mean([r[mode]['feasible_common_F1'] for r in src])) for mode in ['replace','add','delete']})
    result=dict(status='COMPLETE_NEW_COMMON_OUTPUT_FEASIBILITY_DIAGNOSTIC_NOT_MODEL_QUALITY',summary=summary,sources=rows,registration_ref=ref(ROOT/'common_output_registration_01.json'),new_model_calls=0,new_fit=0,new_media_decode=0,old_comparison_entry_repeated=False,oracle_masks_saved=False,official_joint_score=None,spatial_contribution='UNKNOWN',historical_exposure=True,production_admitted=False,utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(out/'result.json',result);print(json.dumps(dict(status=result['status'],summary=summary)))
if __name__=='__main__':main()
