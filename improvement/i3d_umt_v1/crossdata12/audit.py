"""Independent CPU arithmetic on first saved scores; no model calls or refitting."""
import json
import numpy as np
import torch
import torch.nn.functional as F

from common import ROOT, checked, read, reference, write_new


def manual_f1(scores, baseline, labels):
    n,k = len(baseline),int(baseline.sum())
    if scores is None:
        selected = set(np.flatnonzero(baseline).tolist())
    else:
        assert len(scores)==(n+63)//64 and np.isfinite(scores).all()
        selected = set(sorted(range(n),key=lambda i:(-float(scores[i//64]),i))[:k])
    total = 0.0
    for col in range(labels.shape[1]):
        human = set(np.flatnonzero(labels[:,col]).tolist())
        denominator = len(selected)+len(human)
        total += 2*len(selected & human)/denominator if denominator else 0.0
    return total/labels.shape[1]


def main():
    result=read(ROOT/'review.json')
    frozen=read(ROOT/'frozen_final.json')
    checked(frozen['checkpoint'])
    sources={s['sid']:s for s in read(ROOT/'registration.json')['sources']}
    ridge=np.load(ROOT/'ridge_control.npz',allow_pickle=False)
    checks=[]
    for row in result['dev']+result['results']:
        s=sources[row['sid']]
        original=np.load(checked(s['comparison_ref']),allow_pickle=False)
        baseline,labels=original['baseline'].astype(bool),original['labels'].astype(bool)
        groups=np.load(ROOT/'inputs'/row['sid']/'groups.npy',allow_pickle=False)
        assert np.array_equal(groups,np.arange(len(baseline))//64)
        primary=np.load(ROOT/'outputs'/f'{row["sid"]}.npz',allow_pickle=False)
        feature_ref=read(ROOT/'features'/row['sid']/'acceptance.json')['features']
        values=np.load(checked(feature_ref),allow_pickle=False)
        values=F.normalize(torch.from_numpy(values),p=2,dim=-1).numpy()
        linear=(values-ridge['mx'])@ridge['coef']+float(ridge['my'])
        scores=dict(umt=primary['real'],content_shift=primary['shifted'],ridge=linear,
                    inherited_external_control=None)
        recomputed={key:manual_f1(v,baseline,labels) for key,v in scores.items()}
        assert all(abs(recomputed[key]-row['metrics'][key])<1e-12 for key in recomputed)
        checks.append(dict(sid=row['sid'],role=row['role'],metrics=recomputed))
    held=[r for r in checks if r['role']=='held_dataset']
    macro={key:sum(r['metrics'][key] for r in held)/len(held) for key in held[0]['metrics']}
    assert all(abs(macro[key]-result['macro_mean_pair_F1'][key])<1e-12 for key in macro)
    registration=read(ROOT/'registration.json')
    checked(registration['protected_baseline'])
    feature_batches=sum(len(list((ROOT/'features'/sid).glob('batch_*.npy'))) for sid in sources)
    write_new(ROOT/'independent_cpu_audit.json',dict(status='PASS_SAVED_OUTPUT_NATIVE_GROUPS_ALL_RATERS_AND_MACRO',
              sources=len(checks),held_sources=len(held),metrics_per_source=4,
              first_batched_I3D_calls=feature_batches,training_updates=len((ROOT/'training_journal.jsonl').read_text().splitlines()),
              new_model_calls=0,new_fits=0,review=reference(ROOT/'review.json'),
              frozen_checkpoint=frozen['checkpoint'],baseline_unchanged=True))


if __name__=='__main__':
    main()
