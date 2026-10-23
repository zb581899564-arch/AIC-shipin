"""Within-query human preferences; unannotated cells stay unknown, not negatives."""
import hashlib
import numpy as np
from qv_common47 import checked, read


def source_queries(source):
    result = []
    for row in read(checked(source['annotations'])):
        ids = np.asarray(row['relevant_clip_ids'], dtype=np.int64)
        votes = np.asarray(row['saliency_scores'], dtype=np.float64)
        if votes.shape != (len(ids), 3) or (votes < 0).any() or (votes > 4).any():
            raise ValueError('Original all-three-rater saliency domain differs')
        if len(set(ids.tolist())) != len(ids) or (ids < 0).any() or (ids >= source['cells']).any():
            raise ValueError('Original annotated clip IDs outside actual input cells')
        pairs = []
        for i in range(len(ids)):
            for j in range(len(ids)):
                difference = votes[i]-votes[j]
                if difference.mean() >= 1 and (difference > 0).sum() >= 2:
                    key = hashlib.sha256(f"QV47/{row['qid']}/{ids[i]}/{ids[j]}".encode()).hexdigest()
                    pairs.append(dict(high=int(ids[i]),low=int(ids[j]),
                        three_vote_differences=difference.tolist(),order_hash=key))
        pairs.sort(key=lambda p:p['order_hash'])
        result.append(dict(qid=row['qid'],ids=ids.tolist(),votes=votes.tolist(),pairs=pairs[:32]))
    return result


def query_metrics(scores, query):
    ids = np.asarray(query['ids'], dtype=np.int64)
    values = np.asarray(query['votes'], dtype=np.float64)
    order = np.argsort(-np.asarray(scores)[ids], kind='stable')
    discount = np.log2(np.arange(len(ids))+2)
    ndcg = []
    for reviewer in range(3):
        gains = np.exp2(values[:,reviewer])-1
        denominator = (np.sort(gains)[::-1]/discount).sum()
        ndcg.append(float((gains[order]/discount).sum()/denominator) if denominator else None)
    valid = [x for x in ndcg if x is not None]
    decisions = []
    for pair in query['pairs']:
        delta = float(scores[pair['high']]-scores[pair['low']])
        decisions.append(1. if delta > 0 else 0. if delta < 0 else .5)
    return dict(all_reviewer_NDCG=float(np.mean(valid)) if valid else None,
        confident_pair_accuracy=float(np.mean(decisions)) if decisions else None,
        confident_pairs=len(decisions),annotated_cells=len(ids),unknown_cells_not_scored=True)


def contracts():
    import torch
    # Every original reviewer contributes; negative/unknown labels are not coerced to bool.
    differences=torch.tensor([4.,-2.,2.]);target=(differences+4)/8
    x=torch.tensor(0.,requires_grad=True)
    torch.nn.functional.binary_cross_entropy_with_logits(x.expand(3),target).backward()
    if x.grad is None or not torch.isfinite(x.grad) or not float(x.grad)<0:
        raise ValueError('All-rater pair loss gradient invalid')
    q=dict(ids=[1,3],votes=[[4,3,2],[0,1,2]],pairs=[dict(high=1,low=3)])
    good=query_metrics(np.array([999,1,999,0,999]),q)
    if good['all_reviewer_NDCG'] != 1. or good['confident_pair_accuracy'] != 1.:
        raise ValueError('Unknown-mask/rater metric contract differs')
    return dict(state='PASS',checks=3,all_rater_gradient=True,
        outside_query_cells_unknown=True,no_most_favorable_reviewer=True)
