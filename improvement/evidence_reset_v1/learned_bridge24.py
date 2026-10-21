"""First learned20 fixed-K readout; immutable18 control results are adopted."""
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
    from factor_expected18 import select
    N=Path(__file__).resolve().parent;R=N.parent;W=R.parent;t=time.monotonic()
    reg=json.loads((N/'registration24.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        assert ref(r['path'])==r;return json.loads(Path(r['path']).read_text())
    protocol=read(reg['protocol_ref']);assert protocol['sources']==['S02','S06','S08','S23']
    old=read(reg['completion18_ref']);prior=read(reg['decisions18_ref'])['selected']['train']
    process=read(reg['completion23_ref']);assert process['status']=='ELIGIBLE_FOR_SEPARATE_BROADER_TRAINING_REVIEW_ONLY'
    accept=read(reg['acceptance23_ref']);cases=read(accept['cases_ref'])
    output23=read(reg['gpu_completion23_ref']);scores={r['uid']:r for v in output23['score_refs']for r in [read(v)]}
    oldreg=read(reg['registration19_ref']);coll=read(oldreg['train_collection_ref']);manifest=read(coll['asset_manifest_ref'])
    sys.path.insert(0,oldreg['prior_code_root'])
    from improvement.native_preference_v1.inputs import NativeInputStore
    store=NativeInputStore(manifest,'train');oldrows={v['source_id']:v for v in old['metrics']['train']['per_source']}
    rows=[]
    def utility(selected,labels):
        tp=labels[sorted(selected)].sum(axis=0,dtype=np.int64);gt=labels.sum(axis=0,dtype=np.int64);den=len(selected)+gt
        return float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())
    for sid in protocol['sources']:
        h=store.source_supervision(sid);n=len(h['clock']['normalized_exact_pts']);b=set(h['baseline'])
        assert all(len(v)==n and all(v)for v in h['known_masks'])and h['source_sha256']==oldrows[sid]['source_sha256']
        labels=np.zeros((n,len(h['raters'])),bool)
        for j,r in enumerate(h['raters']):labels[sorted(r),j]=True
        source_cases=[v for v in cases.values()if v['sid']==sid];actions=[]
        for c in source_cases:
            w=read(c['window_ref']);actions.append([w['slots'][j]['selected_ordinals']for j in c['slots']])
        arms={}
        for arm in ['real','shifted']:
            logits=[scores[c['uid']][arm]for c in source_cases];selected,stats=select(actions,logits,b,n)
            previous=set(prior[sid][arm]);value=utility(selected,labels);control=oldrows[sid]['arms'][arm]['f1']
            arms[arm]=dict(F1=value,delta_vs_same_untrained_readout=value-control,
                delta_vs_protected=value-oldrows[sid]['baseline_f1'],adopted_untrained_F1=control,
                added_due_learning=len(selected-previous),deleted_due_learning=len(previous-selected),
                added_vs_protected=len(selected-b),deleted_vs_protected=len(b-selected),stats=stats)
            assert len(selected)==len(previous)==len(b)
        rows.append(dict(sid=sid,baseline_F1=oldrows[sid]['baseline_f1'],adopted_uniform_F1=oldrows[sid]['arms']['uniform']['f1'],arms=arms))
    store.close();macro={arm:dict(F1=float(np.mean([v['arms'][arm]['F1']for v in rows])),
        delta_vs_same_untrained_readout=float(np.mean([v['arms'][arm]['delta_vs_same_untrained_readout']for v in rows])),
        delta_vs_protected=float(np.mean([v['arms'][arm]['delta_vs_protected']for v in rows])),
        added_due_learning=sum(v['arms'][arm]['added_due_learning']for v in rows),deleted_due_learning=sum(v['arms'][arm]['deleted_due_learning']for v in rows))for arm in ['real','shifted']}
    output=dict(status='LEARNED_FIXEDK_BRIDGE_ONLY_NOT_TRAINING_OR_PRODUCTION_ADMISSION',rows=rows,macro=macro,
        macro_protected=float(np.mean([v['baseline_F1']for v in rows])),macro_adopted_uniform=float(np.mean([v['adopted_uniform_F1']for v in rows])),
        controls_adopted_not_recomputed=True,new_model_calls=0,new_updates=0,seconds=time.monotonic()-t,
        primary_readout='FIXED_PROTECTED_K_ONLY',MAP_diagnostic_only=True,new_ZIP=0,official_submissions=0)
    with(N/'completion24.json').open('x')as f:json.dump(output,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(N/'completion24.json'),summary=output)))


if __name__=='__main__':main()
