"""Only new known-mask and tied-AP contracts, not old model/profile reruns."""
import numpy as np
import torch
from sklearn.metrics import average_precision_score
from pilot15_common import ROOT, ENGINEERING, read, ref, save
from pilot15_review import average_precision


def main():
    # The middle temporal cell is entirely UN: it must contribute no gradient.
    labels=np.asarray([1,-1,0,-1,-1,-1,0,1],dtype=np.int8)
    bounds=[(0,3),(3,6),(6,8)]
    counts=np.asarray([(labels[a:b]>=0).sum() for a,b in bounds],dtype=np.float32)
    positive=np.asarray([(labels[a:b]==1).sum() for a,b in bounds],dtype=np.float32)
    targets=np.divide(positive,counts,out=np.zeros_like(positive),where=counts>0)
    logits=torch.tensor([.3,-.8,.1],requires_grad=True)
    loss=(torch.nn.functional.binary_cross_entropy_with_logits(logits,torch.from_numpy(targets),reduction='none')
        *torch.from_numpy(counts/counts.sum())).sum()
    loss.backward()
    if logits.grad[1]!=0 or not (logits.grad[[0,2]].abs()>0).all():
        raise ValueError('Uncertainty affected training or known cells lost gradients')
    for scores in [np.asarray([.4,.4,.2,.1]),np.ones(4)]:
        truth=np.asarray([1,0,1,0])
        if abs(average_precision(scores,truth)-average_precision_score(truth,scores))>1e-12:
            raise ValueError('Tied-score independent AP differs')
    previous=ENGINEERING/'crossdata12/new_cpu_contracts.json'
    if read(previous)['status']!='PASS':raise ValueError('Previously accepted original UMT contracts absent')
    save(ROOT/'new_CPU_contracts.json',dict(status='PASS',new_checks=3,
        cases=['UN_zero_gradient_known_cells_nonzero','tied_AP','all_equal_AP'],
        adopted_original_UMT_path_checks=ref(previous),old_success_not_rerun=True))


if __name__=='__main__':main()
