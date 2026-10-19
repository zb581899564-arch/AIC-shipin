"""One frozen source-balanced reference-event index; no threshold search."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
from event_runtime import *

OUT=ROOT/'event_memory_01'


def predict(x,model):
    z=(x-model['mean'])/model['std']
    bank=model['bank']
    # One representative per original source prevents long videos dominating.
    distances=[];qualities=[]
    for source in np.unique(model['source_codes']):
        idx=np.flatnonzero(model['source_codes']==source)
        d=((z[:,None,:]-bank[idx][None,:,:])**2).sum(2)
        nearest=d.argmin(1)
        distances.append(d[np.arange(len(z)),nearest])
        qualities.append(model['target'][idx[nearest]])
    ds=np.stack(distances,1);qs=np.stack(qualities,1)
    order=np.argsort(ds,axis=1,kind='stable')[:,:5]
    d=np.take_along_axis(ds,order,1);q=np.take_along_axis(qs,order,1)
    zeros=d==0
    weights=1/(d+1e-8)
    weights=np.where(zeros.any(1)[:,None],zeros.astype(float),weights)
    result=(weights*q).sum(1)/weights.sum(1)
    require(np.isfinite(result).all() and np.all((result>=-.5-1e-12)&(result<=1+1e-12)),'Valid bounded reference-event quality')
    return result


def build():
    cpu();require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'Main experiment cutoff')
    OUT.mkdir()
    protocol=read(ROOT/'event_memory_protocol_01.json')
    adopted=dict(np.load(bound(read(ROOT/'frozen_selection.json')['weights_ref'])))
    xs=[];ys=[];codes=[];inputs=[]
    for code,s in enumerate(s for s in read(ROOT/'registration.json')['sources'] if s['group']=='train'):
        row=read(ROOT/'train_inputs'/(s['sid']+'.json'))
        d=np.load(bound(row['input_ref']))
        xs.append(d['x']);ys.append(d['target']);codes.append(np.full(len(d['x']),code,np.int64));inputs.append(ref(ROOT/'train_inputs'/(s['sid']+'.json')))
    x=np.concatenate(xs)
    model={k:adopted[k] for k in ['pca_mean','pca_components','mean','std','rho_train']}
    model.update(bank=(x-adopted['mean'])/adopted['std'],target=np.concatenate(ys),source_codes=np.concatenate(codes))
    require(len(np.unique(model['source_codes']))==25 and model['bank'].shape[1]==102,'All25 fixed source banks')
    np.savez(OUT/'model.npz',**model)
    restored=dict(np.load(OUT/'model.npz'))
    require(all(np.array_equal(restored[k],v) for k,v in model.items()),'Actual index save/reload equality')
    # Synthetic exact query checks local indexing, not candidate quality.
    tiny={k:np.asarray(v) for k,v in dict(mean=np.zeros(1),std=np.ones(1),bank=[[0.],[2.],[4.],[6.],[8.]],target=[.1,.2,.3,.4,.5],source_codes=[0,1,2,3,4]).items()}
    require(np.allclose(predict(np.array([[0.]]),tiny),[.1]),'Exact matching source-zero case')
    require(predict(np.empty((0,102)),model).shape==(0,),'Legal zero proposal query')
    save(OUT/'frozen_selection.json',dict(status='FROZEN_SOURCE_BALANCED_EVENT_MEMORY',weights_ref=ref(OUT/'model.npz'),protocol_ref=ref(ROOT/'event_memory_protocol_01.json'),adopted_source_lock_ref=ref(ROOT/'source_lock.json'),train_inputs=inputs,learned_tensor_scalars=sum(v.size for v in model.values()),training_candidates=len(x),source_count=25,neighbours=5,save_reload_passed=True,diagnostic_not_yet_evaluated=True,code_ref=ref(Path(__file__)),utc=utc()))


def evaluate():
    cpu();frozen=read(OUT/'frozen_selection.json');model=dict(np.load(bound(frozen['weights_ref'])));items=[]
    for s in read(ROOT/'registration.json')['sources']:
        if s['group']!='check':continue
        d=load_source(s,True)
        r=read(ROOT/'diagnostic_inputs'/(s['sid']+'.json'));x=np.load(bound(r['input_ref']))['x'];c=r['candidates']
        q=predict(x,model);k=np.asarray([p['added_frames']for p in c],float)
        gain=2*k*q/(d['baseline'].sum()+k+len(d['baseline'])*float(model['rho_train']))
        idx=None if not len(gain) or gain.max()<=0 else int(gain.argmax())
        action=None if idx is None else dict(sid=s['sid'],candidate_index=idx,added_frames=c[idx]['added_frames'],predicted_gain=float(gain[idx]))
        items.append(dict(d=d,c=c,q=q,gain=gain,action=action))
    selected=knapsack([v['action']for v in items if v['action']],sum(int(v['d']['baseline'].sum())for v in items)//10)
    rows=[]
    for v in items:
        d=v['d'];mask=d['baseline'].copy();idx=None
        if d['sid']in selected:
            idx=v['action']['candidate_index'];c=v['c'][idx];mask[c['left']:c['right']]=True
        b,n=metric(d['baseline'],d['labels']),metric(mask,d['labels']);added=mask&~d['baseline']
        qtrue,_=targets(d['baseline'],d['labels'],v['c'])
        rows.append(dict(sid=d['sid'],baseline=b,candidate=n,delta=n['f1']-b['f1'],chosen=None if idx is None else v['c'][idx],added_frames=int(added.sum()),predicted_quality=None if idx is None else float(v['q'][idx]),true_quality=None if idx is None else float(qtrue[idx]),actual_added_rater_precision=None if not added.any()else float(d['labels'][added].mean()),historically_exposed=True))
        np.savez(OUT/(d['sid']+'_output.npz'),selected=mask,predicted_quality=v['q'],estimated_gain=v['gain'])
    summary=dict(sources=len(rows),macro_delta=float(np.mean([r['delta']for r in rows])),improved_sources=sum(r['delta']>0 for r in rows),decreased_sources=sum(r['delta']<0 for r in rows),changed_sources=sum(r['added_frames']>0 for r in rows),added_frames=sum(r['added_frames']for r in rows),worst_delta=min(r['delta']for r in rows),actual_added_seconds=sum(float(F(r['chosen']['added_duration_exact']))for r in rows if r['chosen']))
    save(OUT/'external_evaluation.json',dict(status='FROZEN_MEMORY_EXPOSED_DIAGNOSTIC_ONLY',summary=summary,sources=rows,no_new_blind_claim=True,no_retuning=True,utc=utc()))
    save(OUT/'completion.json',dict(status='COMPLETED_CPU_REFERENCE_INDEX_RESEARCH_ONLY',evaluation_ref=ref(OUT/'external_evaluation.json'),frozen_ref=ref(OUT/'frozen_selection.json'),new_GPU_calls=0,new_media_decode=0,production_started=False,utc=utc()))
    print(json.dumps(clean(summary)),flush=True)


if __name__=='__main__':
    try:
        if sys.argv[1]=='build':build()
        elif sys.argv[1]=='evaluate':evaluate()
        else:raise ValueError('Explicit build/evaluate stage required')
    except BaseException as error:
        failure('event_memory_'+sys.argv[1],error)
        raise
