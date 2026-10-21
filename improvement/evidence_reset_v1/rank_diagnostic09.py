"""New read-only question on07 caches: fit failure versus transfer/confounding.

No fitting, gradients, model call, input rebuilding, checkpoint choice or new
selector. Swap-even/odd margins are descriptive counterfactual algebra only.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def sigmoid(x):return 1/(1+math.exp(-x)) if x>=0 else math.exp(x)/(1+math.exp(x))


def metrics(rows):
    ss=sorted({r['source_id'] for r in rows});result={}
    for name in ['correct','brier']:
        result[name]=sum(sum(r[name] for r in rows if r['source_id']==s)/sum(r['source_id']==s for r in rows) for s in ss)/len(ss)
    return dict(sources=len(ss),pairs=len(rows),source_macro_accuracy=result['correct'],source_macro_brier=result['brier'])


def score_row(source,margin,target):
    p=sigmoid(margin)
    return dict(source_id=source,margin=margin,target=target,probability=p,
        correct=.5 if margin==0 else float((p>.5)==(target>.5)),brier=(p-target)**2)


def main(root):
    started=time.monotonic();N=Path(root).resolve(strict=True);P=N.parent/'relative_ranker06'
    trainer=module(P/'rank_train07.py','adopted_ranker07_diagnosis09')
    _,W,api,p,common,manifest,Store,canonical,admission,accepted=trainer.context(P)
    reg=json.loads((N/'registration09.json').read_text());api.require(reg['code_ref']==api.ref(__file__),'Exact independent diagnostic implementation')
    chain=api.loadref(reg['prior_chain_ref'],W);review=api.loadref(chain['review_ref'],W)
    api.require(review['status']=='STOP_RELATIVE_RANKER_PILOT','Do not revive failed main pilot')
    import torch,numpy as np
    complete=api.loadref(json.loads((P/'review_admission07.json').read_text())['gpu_completion_ref'],W)
    t=api.loadref(complete['training_ref'],W)
    head=torch.load(api.checked(t['head_only_ref'],W),map_location='cpu',weights_only=True)['weight'][0]
    initial={api.loadref(r,W)['uid']:r for r in complete['initial_feature_refs']}
    final={api.loadref(r,W)['uid']:r for r in complete['final_output_refs']}
    train=api.loadref(accepted['train_target_ref'],W);check=api.loadref(accepted['check_target_ref'],W)
    def feature(reference):
        row=api.loadref(reference,W)
        return torch.load(api.checked(row['feature_ref'],W),map_location='cpu',weights_only=True)
    scores={u:float(torch.dot(head,feature(r))) for u,r in initial.items()}
    train_rows=[score_row(r['source_id'],scores[r['left']]-scores[r['right']],r['preference_left']) for r in train]
    decomposed={};cosines={}
    for role in ['head_only','main']:
        values=scores if role=='head_only' else {u:api.loadref(r,W)['score'] for u,r in final.items()}
        rows={k:[] for k in ['real','donor_swapped','swap_odd','swap_even','always_earlier']}
        for r in check:
            real=values[r['left']]-values[r['right']];swap=values[r['left']+'.swap']-values[r['right']+'.swap']
            for k,z,y in [('real',real,r['preference_left']),('donor_swapped',swap,1-r['preference_left']),
                ('swap_odd',(real-swap)/2,r['preference_left']),('swap_even',(real+swap)/2,r['preference_left']),
                ('always_earlier',1.,r['preference_left'])]:rows[k].append(score_row(r['source_id'],z,y))
        decomposed[role]={k:metrics(v) for k,v in rows.items()}
        decomposed[role]['rows']=rows
    feature_summary={}
    for scope,targets in [('train',train),('check',check)]:
        cs=[];ds=[]
        for r in targets:
            a=feature(initial[r['left']]);b=feature(initial[r['right']])
            cs.append(float(torch.nn.functional.cosine_similarity(a,b,dim=0)));ds.append(float(torch.linalg.vector_norm(a-b)))
        feature_summary[scope]=dict(pair_cosine_mean=float(np.mean(cs)),pair_cosine_min=float(np.min(cs)),
            normalized_pair_delta_norm_mean=float(np.mean(ds)),all_normalized_feature_norm=64.)
    events=[json.loads(s) for s in (P/'rank_events07.jsonl').read_text().splitlines() if s.strip()]
    updates=[r for r in events if r['event']=='OPTIMIZER_STEP']
    raw_losses=[json.loads(f.read_text())['unweighted_loss'] for f in sorted((P/'rank_outputs07').glob('train_pair_*.json'))]
    result=dict(status='COMPLETE_NEW_CPU_FIT_TRANSFER_AND_SWAP_DECOMPOSITION_NOT_A_SELECTOR',
        original_main_status=review['status'],frozen_head_training=metrics(train_rows),
        adopted_frozen_head_check=review['metrics']['head_only'],
        descriptive_decomposition=decomposed,feature_summary=feature_summary,
        actual_training_trace=dict(recorded_updates=len(updates),initial_lora_gradient_norm=updates[0]['lora_gradient_norm'],
            later_nonzero_lora_gradients=sum(r['lora_gradient_norm']>0 for r in updates[1:]),
            median_lora_gradient_norm=float(np.median([r['lora_gradient_norm'] for r in updates])),
            recorded_pair_losses=len(raw_losses),first10_loss_mean=float(np.mean(raw_losses[:10])),last10_loss_mean=float(np.mean(raw_losses[-10:]))),
        caveat='Different pairs have different losses; this is not final train quality for the adapted model. Swap-even is not a pure position causal effect: counterfactual timestamps/Overview can conflict with donor content. Neither component is an admitted selector.',
        seconds=time.monotonic()-started,new_model_calls=0,new_optimizer_updates=0,automatic_production=False)
    api.save(N/'completion09.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='descriptive_decomposition'}|{'decomposition':{r:{k:v for k,v in rows.items() if k!='rows'} for r,rows in decomposed.items()}}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args();main(args.run_root)
