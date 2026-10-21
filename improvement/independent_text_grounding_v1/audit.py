"""First independent dense, tie-aware AP recomputation; no inference or fitting."""
import numpy as np
from common import ROOT,checked,read,ref,write


def dense_ap(scores,positive,counts):
    labels=np.concatenate([np.r_[np.ones(int(p)),np.zeros(int(n-p))] for p,n in zip(positive,counts)])
    values=np.repeat(scores,counts)
    order=np.argsort(-values,kind='stable')
    sorted_values=values[order];truth=labels[order]
    tp=np.cumsum(truth);totals=np.arange(1,len(order)+1)
    boundaries=np.r_[np.flatnonzero(np.diff(sorted_values)),len(order)-1]
    recall=tp[boundaries]/truth.sum()
    precision=tp[boundaries]/totals[boundaries]
    return float(np.sum(np.diff(np.r_[0,recall])*precision))


def main():
    source=read(ROOT/'input_acceptance.json');review=read(ROOT/'review.json')
    checks=0
    for i,row in enumerate(source['sources']):
        scores=np.load(ROOT/'outputs'/row['sid']/'scores.npy',allow_pickle=False)
        target=np.load(checked(row['target']),allow_pickle=False);counts=target['counts']
        ids=row['query_ids'];other=source['sources'][(i+1)%8]['query_ids']
        expected=next(r for r in review['sources'] if r['sid']==row['sid'])
        for j,qid in enumerate(ids):
            streams=dict(correct=scores[:,qid],within_query_swap=scores[:,ids[(j+1)%len(ids)]],
                         cross_video_query_swap=scores[:,other[j%len(other)]],
                         temporal_shift=np.roll(scores[:,qid],len(counts)//2))
            for name,values in streams.items():
                measured=dense_ap(values,target['positive'][j],counts)
                assert abs(measured-expected['events'][j]['AP'][name])<1e-12
                checks+=1
    write(ROOT/'independent_cpu_audit.json',dict(status='PASS_DENSE_TIE_AWARE_AP',comparisons=checks,
              review=ref(ROOT/'review.json'),new_model_calls=0,new_fit=0))


if __name__=='__main__':
    main()
