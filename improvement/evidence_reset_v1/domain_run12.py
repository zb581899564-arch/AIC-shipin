"""One frozen72-feature collection and matched convex training-domain controls."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import traceback


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def context(root):
    N=Path(root).resolve(strict=True);inputs=module(N/'domain_inputs11.py','domain_inputs_contract12')
    _,R,W,api,p,common,manifest,Store,reg,inv,protocol=inputs.context(N)
    a=json.loads((N/'gpu_admission12.json').read_text());api.require(a['approved'] and a['code_ref']==api.ref(__file__),'Separate exact12 GPU decision')
    accepted=api.loadref(a['input_acceptance_ref'],W);api.require(accepted['status']=='PASS_FIRST72_DOMAIN_FEATURE_INPUTS','All first new72 native inputs required')
    return N,R,W,inputs,api,p,common,manifest,Store,inv,protocol,a,accepted


def features(root):
    N,R,W,inputs,api,p,common,manifest,Store,inv,protocol,admission,accepted=context(root)
    import sys,re
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch,peft,transformers
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig,get_peft_model,get_peft_model_state_dict,set_peft_model_state_dict
    require=api.require;require(os.environ.get('CUDA_VISIBLE_DEVICES') not in ('',None,'-1') and torch.cuda.is_available(),'Actual shared CUDA reservation')
    require(peft.__version__=='0.17.1' and transformers.__version__=='4.57.1','Actual pinned model implementation')
    store=Store(manifest,'check');dictionary=store._dictionary_helper();all_values={};cases={}
    for reference in accepted['source_refs']:
        s=api.loadref(reference,W);frames,grid,ordinals=inputs.load_source11(s,api,W,torch,dictionary)
        clock=api.loadref(s['clock_ref'],W);lookup={o:i for i,o in enumerate(ordinals)}
        overview=dict(role='Overview',cells=[lookup[o] for o in s['Overview_ordinals']],origin_exact='0')
        for uid,ref_case in accepted['case_refs'].items():
            if not uid.startswith('train_'+s['sid']+'_'):continue
            case=api.loadref(ref_case,W);v,plan=api.build_pixels(torch,frames,grid,ordinals,clock['normalized_exact_pts'],overview,case['block'],s['sid'],s['source_sha256'])
            v.update(torch.load(api.checked(case['prefix_ref'],W),map_location='cpu',weights_only=True))
            require(plan==case['plan'] and common.signature(v)==case['input_signature'],'Actual first accepted native tensor bytes adopted, not re-encoded')
            all_values[uid]=v;cases[uid]=case
    require(len(all_values)==72,'All72 actual domain inputs before first model forward')
    spec=manifest['model_spec'];model=Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'],revision=spec['revision'],local_files_only=True,
        trust_remote_code=False,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    for v in model.parameters():v.requires_grad_(False)
    # Canonical base hash implementation was already byte-bound by the original07 context.
    trainer=module(R/'relative_ranker06/rank_train07.py','old_ranker_hash_contract12');canonical=trainer.context(R/'relative_ranker06')[7]
    before=canonical(model,torch);require(before['sha256']==spec['base_sha256'],'Original BASE bytes')
    names=[n for n,m in model.named_modules() if re.search(r'language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$',n)]
    require(len(names)==144,'Exactly original attention injection locations')
    model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0,bias='none',target_modules=names,task_type='CAUSAL_LM'),adapter_name='rank07')
    for n,v in model.named_parameters():
        if 'lora_' in n:v.data=v.data.float()
        v.requires_grad_(False)
    initial=torch.load(api.checked(admission['initial_zero_adapter_ref'],W),map_location='cpu',weights_only=True)
    set_peft_model_state_dict(model,initial,adapter_name='rank07')
    actual=get_peft_model_state_dict(model,adapter_name='rank07')
    require(all(v.dtype==torch.float32 and torch.equal(v.detach().cpu().view(torch.uint8),initial[k].view(torch.uint8)) for k,v in actual.items()),'Exact original initial FP32 zeroB adapter for old-feature equivalence')
    require(all(int(torch.count_nonzero(v))==0 for k,v in actual.items() if 'lora_B' in k),'No trained07 adapter may enter this domain experiment')
    model.eval();native=model.get_base_model();calls=0;start=time.monotonic();out=N/'features12';out.mkdir();refs=[]
    old=json.loads((R/'relative_ranker06/gpu_completion07.json').read_text());signature_outputs={}
    for r in old['initial_feature_refs']:
        row=api.loadref(r,W);signature_outputs[json.dumps(row['input_signature'],sort_keys=True)]=r
    def event(name,**values):
        with (N/'feature_events12.jsonl').open('a') as f:f.write(json.dumps(dict(event=name,**values),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def guard(module,args):
        nonlocal calls
        require(time.monotonic()-start<900 and not any(v.requires_grad for v in model.parameters()),'Finite frozen feature model')
        require(model.active_adapter=='rank07' and all(not m.disable_adapters and list(m.active_adapters)==['rank07'] for m in model.modules() if hasattr(m,'lora_A')),'Only explicit zeroB adapter active')
        calls+=1
    handle=native.model.register_forward_pre_hook(guard)
    for uid,v in sorted(all_values.items()):
        key=json.dumps(cases[uid]['input_signature'],sort_keys=True);prior=signature_outputs.get(key)
        if prior is not None:
            row=api.loadref(prior,W);f=torch.load(api.checked(row['feature_ref'],W),map_location='cpu',weights_only=True);fr=row['feature_ref'];adopted=True
        else:
            event('BEGIN_FIRST_FEATURE',uid=uid,input_ref=accepted['case_refs'][uid])
            with torch.inference_mode():
                hidden=native.model(**{k:t.to('cuda:0') for k,t in v.items()},use_cache=False,return_dict=True).last_hidden_state
                require(hidden.shape==(1,v['input_ids'].shape[1],4096),'Actual last causal prefill token representation')
                f=torch.nn.functional.layer_norm(hidden[0,-1].float(),(4096,),eps=1e-5).cpu().clone()
            require(bool(torch.isfinite(f).all()),'Finite frozen feature')
            fp=out/(uid+'.pt');torch.save(f,fp);fr=api.ref(fp);adopted=False
        row=dict(uid=uid,input_signature=cases[uid]['input_signature'],source_sha256=cases[uid]['source_sha256'],feature_ref=fr,
            feature_sha256=hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest(),actual_model_calls=0 if adopted else 1,
            prior_identical_output_ref=prior,feature_definition='exact07_initial_zeroB,lastprefill4096,fixedLayerNorm1e-5',labels_read=False)
        rp=out/(uid+'.json');api.save(rp,row);refs.append(api.ref(rp));signature_outputs[key]=refs[-1]
        event('FEATURE_ACCEPTED',uid=uid,output_ref=refs[-1],adopted=adopted)
    handle.remove();after=canonical(model,torch);require(before==after,'All original BASE and vision bytes frozen')
    actual=get_peft_model_state_dict(model,adapter_name='rank07')
    require(all(torch.equal(v.detach().cpu().view(torch.uint8),initial[k].view(torch.uint8)) for k,v in actual.items()),'All adapter bytes unchanged,0Qwen updates')
    require(len(refs)==72 and 0<=calls<=72,'Exact72case logical feature denominator')
    api.save(N/'gpu_completion12.json',dict(status='COMPLETE_FROZEN_DOMAIN_FEATURES_NOT_QUALITY',feature_refs=refs,
        logical_cases=72,actual_model_calls=calls,adopted_cases=72-calls,new_Qwen_updates=0,base_before=before,base_after=after,
        initial_zero_adapter_ref=admission['initial_zero_adapter_ref'],seconds=time.monotonic()-start,labels_read=False))


def convex_fit(np,X,y):
    """Strictly convex source-matched pair BCE; no validation-driven tuning."""
    n,d=X.shape;lam=float(np.sum(X*X)/(n*n))
    if not lam>0:raise ValueError('Degenerate zero feature-difference matrix')
    U,S,V=np.linalg.svd(X,full_matrices=False);keep=S>np.finfo(float).eps*max(X.shape)*S[0]
    B=U[:,keep]*S[keep];V=V[keep];t=np.zeros(B.shape[1]);trace=[]
    def state(t):
        z=B@t;prob=np.exp(-np.logaddexp(0,-z));loss=float(np.mean(np.logaddexp(0,z)-y*z)+.5*lam*(t@t))
        grad=B.T@(prob-y)/n+lam*t
        return loss,prob,grad
    for iteration in range(32):
        loss,prob,g=state(t)
        full_gradient=X.T@(prob-y)/n+lam*(V.T@t)
        if float(np.max(np.abs(full_gradient)))<=1e-10:break
        H=B.T@((prob*(1-prob)/n)[:,None]*B)+lam*np.eye(len(t));step=np.linalg.solve(H,g);alpha=1.
        for backtrack in range(40):
            candidate=t-alpha*step;new_loss,_,_=state(candidate)
            if new_loss<=loss-1e-4*alpha*float(g@step):break
            alpha*=.5
        else:raise ValueError('Convex training-only line search did not accept a finite step')
        t=candidate;trace.append(dict(update=len(trace)+1,objective=new_loss,step=alpha,prior_gradient_infinity=float(np.max(np.abs(g)))))
    w=V.T@t;z=X@w;prob=np.exp(-np.logaddexp(0,-z));residual=X.T@(prob-y)/n+lam*w
    if not np.isfinite(w).all() or float(np.max(np.abs(residual)))>1e-10:raise ValueError('Final full4096 gradient residual not converged')
    return w,dict(lambda_rule='trace(X X^T)/n_pairs^2, training features only',lambda_value=lam,updates=len(trace),
        full_gradient_infinity=float(np.max(np.abs(residual))),span_dimension=int(keep.sum()),training_only_trace=trace)


def fit(root):
    N,R,W,inputs,api,p,common,manifest,Store,inv,protocol,admission,accepted=context(root)
    import torch,numpy as np
    require=api.require;decision=json.loads((N/'fit_admission12.json').read_text());c=api.loadref(decision['gpu_completion_ref'],W)
    require(c['status']=='COMPLETE_FROZEN_DOMAIN_FEATURES_NOT_QUALITY' and decision['natural_wrapper_exit_code']==0,'Unique natural feature completion before CPU targets/fit')
    values={};qa=0
    for r in c['feature_refs']:
        row=api.loadref(r,W);f=torch.load(api.checked(row['feature_ref'],W),map_location='cpu',weights_only=True)
        case=api.loadref(accepted['case_refs'][row['uid']],W)
        require(tuple(f.shape)==(4096,) and f.dtype==torch.float32 and bool(torch.isfinite(f).all()) and
            hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest()==row['feature_sha256'] and row['input_signature']==case['input_signature'],'First independent real feature/native input output QA')
        values[row['uid']]=f.numpy().astype(float);qa+=1
    require(qa==72,'All72 first independent feature QA before fitting')
    old=json.loads((R/'relative_ranker06/gpu_completion07.json').read_text())
    for r in old['initial_feature_refs']:
        row=api.loadref(r,W);f=torch.load(api.checked(row['feature_ref'],W),map_location='cpu',weights_only=True)
        values[row['uid']]=f.numpy().astype(float)
    old_accept=json.loads((R/'relative_ranker06/input_acceptance06.json').read_text())
    train_old=api.loadref(old_accept['train_target_ref'],W);check=api.loadref(old_accept['check_target_ref'],W)
    selected={s['source_id'] for s in inv['selected_SumMe']}
    targets={'SumMe':[r for r in train_old if r['source_id'] in selected], 'VideoXum':api.loadref(accepted['training_target_ref'],W)}
    heads={};metrics={};receipts={}
    def metric(rows,head,swap=False):
        out=[]
        for row in rows:
            suffix='.swap' if swap else '';margin=float((values[row['left']+suffix]-values[row['right']+suffix])@head/64)
            y=1-row['preference_left'] if swap else row['preference_left'];prob=float(np.exp(-np.logaddexp(0,-margin)))
            out.append(dict(source_id=row['source_id'],pair_id=row['pair_id'],probability=prob,target=y,
                correct=.5 if margin==0 else float((margin>0)==(y>.5)),brier=(prob-y)**2))
        ids=sorted({r['source_id'] for r in out});means={}
        for k in ['correct','brier']:means[k]=sum(sum(r[k] for r in out if r['source_id']==s)/sum(r['source_id']==s for r in out) for s in ids)/len(ids)
        return dict(source_macro_accuracy=means['correct'],source_macro_brier=means['brier'],sources=len(ids),pairs=len(out),rows=out)
    for arm,rows in targets.items():
        require(len(rows)==36 and len({r['source_id'] for r in rows})==18 and all(r['source_pair_count']==2 for r in rows),'Matched36pairs18sources per arm')
        X=np.vstack([(values[r['left']]-values[r['right']])/64 for r in rows]);y=np.asarray([r['preference_left'] for r in rows])
        w,receipt=convex_fit(np,X,y);heads[arm]=w
        fp=N/('head_'+arm+'12.pt');torch.save(dict(weight=torch.from_numpy(w.copy())),fp)
        loaded=torch.load(fp,map_location='cpu',weights_only=True)['weight'];require(torch.equal(loaded.view(torch.uint8),torch.from_numpy(w).view(torch.uint8)),'Exact final float64 head save/reload')
        probe=values[check[0]['left']];difference=abs(float(loaded@torch.from_numpy(probe)/64)-float(w@probe/64));require(difference<1e-10,'Independent torch64 versus numpy64 scalar readout')
        receipt.update(weight_ref=api.ref(fp),parameters=4096,FP64_save_reload_exact=True,independent_readout_difference=difference)
        api.save(N/('solver_'+arm+'12.json'),receipt);receipts[arm]=receipt
        metrics[arm]=dict(train=metric(rows,w),check=metric(check,w),donor_swapped=metric(check,w,True))
    vx=metrics['VideoXum'];sm=metrics['SumMe'];reasons=[]
    if vx['check']['source_macro_accuracy']<.75:reasons.append('DOMAIN_REAL_CONTENT_ACCURACY_BELOW_POINT75')
    if vx['donor_swapped']['source_macro_accuracy']<.75:reasons.append('DOMAIN_DONOR_CONTENT_CONTROL_BELOW_POINT75')
    if not vx['check']['source_macro_accuracy']>sm['check']['source_macro_accuracy']:reasons.append('NO_MATCHED_REFERENCE_DOMAIN_RANKING_ADVANTAGE')
    if not vx['check']['source_macro_brier']<sm['check']['source_macro_brier']:reasons.append('NO_MATCHED_DOMAIN_SOFT_BRIER_ADVANTAGE')
    improved=[]
    for sid in sorted({r['source_id'] for r in check}):
        a=[r['correct'] for r in vx['check']['rows'] if r['source_id']==sid];b=[r['correct'] for r in sm['check']['rows'] if r['source_id']==sid]
        if sum(a)/len(a)>sum(b)/len(b):improved.append(sid)
    if len(improved)<2:reasons.append('DOMAIN_ADVANTAGE_TOO_FEW_SOURCES')
    result=dict(status='STOP_MATCHED_DOMAIN_PREFILL_LINEAR_RANKING' if reasons else 'ELIGIBLE_FOR_SEPARATE_FULL_SOURCE_FIXED_BUDGET_REVIEW',
        stop_reasons=reasons,metrics=metrics,source_advantage=improved,solver_receipts=receipts,
        first_feature_output_QA='72PASS',new_frozen_model_calls=c['actual_model_calls'],new_Qwen_updates=0,new_CPU_head_fits=2,
        actual_Newton_updates=sum(r['updates'] for r in receipts.values()),historical_exposed=True,official_score='UNKNOWN',
        old07_STOP_unchanged=True,automatic_production=False,official_submissions=0)
    api.save(N/'review12.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['metrics','solver_receipts']}|{'metrics':{a:{s:{k:v for k,v in row.items() if k!='rows'} for s,row in arm.items()} for a,arm in metrics.items()}}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);a.add_argument('--phase',choices=['features','fit'],required=True);args=a.parse_args()
    try:features(args.run_root) if args.phase=='features' else fit(args.run_root)
    except BaseException:
        with (Path(args.run_root)/('failure_'+args.phase+'12.json')).open('x') as f:json.dump(dict(status='ACTUAL_FAILURE_PRESERVE_ALL_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()),f,indent=2)
        raise
