"""Independent CPU arithmetic on first saved scores; no model calls or refitting."""
import json
import numpy as np

from common import ROOT, checked, read, reference, write_new


def manual_f1(scores, baseline, labels):
    # Deliberately independent of common.mean_pair_f1/binary_membership.
    # Validate raw arrays before any bool conversion can hide unknowns.
    baseline, labels = np.asarray(baseline), np.asarray(labels)
    for name, value, ndim in (('baseline', baseline, 1), ('labels', labels, 2)):
        if (value.ndim != ndim or not value.size or value.dtype.kind not in 'bifu'
                or not np.isfinite(value).all()
                or not ((value == 0) | (value == 1)).all()):
            raise ValueError(f'Invalid binary {name} for independent F1')
    if len(labels) != len(baseline):
        raise ValueError('Independent F1 requires equal native-frame domains')
    n,k = len(baseline),int(baseline.sum())
    if scores is None:
        selected = set(np.flatnonzero(baseline).tolist())
    else:
        scores = np.asarray(scores)
        if (scores.ndim != 1 or scores.dtype.kind not in 'fiu'
                or len(scores) != (n+63)//64 or not np.isfinite(scores).all()):
            raise ValueError('Invalid independent native-cell scores')
        # Python scalar ints negate exactly, including uint64 and signed minima;
        # coercing to float here could erase distinct large integer scores.
        selected = set(sorted(range(n),key=lambda i:(-scores[i//64].item(),i))[:k])
    total = 0.0
    for col in range(labels.shape[1]):
        human = set(np.flatnonzero(labels[:,col]).tolist())
        denominator = len(selected)+len(human)
        total += 2*len(selected & human)/denominator if denominator else 0.0
    return total/labels.shape[1]


def main():
    import torch
    import torch.nn.functional as F

    result=read(ROOT/'review.json')
    frozen=read(ROOT/'frozen_final.json')
    checked(frozen['checkpoint'])
    sources={s['sid']:s for s in read(ROOT/'registration.json')['sources']}
    ridge=np.load(ROOT/'ridge_control.npz',allow_pickle=False)
    checks=[]
    for row in result['dev']+result['results']:
        s=sources[row['sid']]
        original=np.load(checked(s['comparison_ref']),allow_pickle=False)
        baseline,labels=original['baseline'],original['labels']
        known_keys={key for key in original.files if 'known' in key.lower()}
        if not known_keys <= {'known'}:
            raise ValueError('Unregistered known-label mask in independent audit')
        if 'known' in known_keys:
            known=original['known']
            if known.dtype != np.bool_ or known.shape != labels.shape or not known.all():
                raise ValueError('Unknown reviewer labels cannot enter complete-source audit')
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
