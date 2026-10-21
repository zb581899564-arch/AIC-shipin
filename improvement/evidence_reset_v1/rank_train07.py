"""One49-pair scalar ranking adaptation; no timestamp-token SFT or cutoff.

The GPU phase reads training targets only. Held-out preferences are read only
by the independent CPU review after the natural shared-wrapper completion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import time
import traceback


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def cpu_tree(value,torch):
    if isinstance(value,torch.Tensor):return value.detach().cpu().contiguous().clone()
    if isinstance(value,dict):return {k:cpu_tree(v,torch) for k,v in value.items()}
    if isinstance(value,list):return [cpu_tree(v,torch) for v in value]
    if isinstance(value,tuple):return tuple(cpu_tree(v,torch) for v in value)
    return value


def pair_loss(torch,left,right,target,weight=1.0):
    y=torch.as_tensor(target,dtype=left.dtype,device=left.device)
    return torch.nn.functional.binary_cross_entropy_with_logits(left-right,y)*weight


def pair_weight(row):return 49/(25*row['source_pair_count'])/2


def tensor_bytes(value,torch):
    if isinstance(value,torch.Tensor):return value.numel()*value.element_size()
    if isinstance(value,dict):return sum(tensor_bytes(v,torch) for v in value.values())
    if isinstance(value,(tuple,list)):return sum(tensor_bytes(v,torch) for v in value)
    return 0


def durable_progress(out,progress,torch):
    # This estimate scales with the actual state; it is not a machine-wide floor.
    estimate=tensor_bytes(progress,torch)+65536*(1+len(progress.get('gradients',{})))
    if shutil.disk_usage(out).free<estimate:
        raise ValueError('Current free bytes cannot hold the next actual atomic checkpoint: '+str(estimate))
    tmp=out/'latest_progress.tmp.pt'
    with tmp.open('wb') as f:
        torch.save(progress,f);f.flush();os.fsync(f.fileno())
    os.replace(tmp,out/'latest_progress.pt')


def context(root):
    root=Path(root).resolve(strict=True)
    api=module(root/'rank_native06.py','rank_input_contract07')
    _,W,reg,protocol,common,manifest,Store,canonical=api.context(root)
    admission=json.loads((root/'gpu_admission07.json').read_text())
    api.checked(admission['code_ref'],W)
    api.require(admission['code_ref']==api.ref(Path(__file__)), 'Exact admitted trainer bytes')
    api.require(admission['approved'] is True and admission['registration_ref']==api.ref(root/'registration06.json'), 'Independent new GPU admission required')
    accepted=api.loadref(admission['input_acceptance_ref'],W)
    api.require(accepted['status']=='PASS_FIRST_NATIVE_RELATIVE_RANKER_INPUTS','All real/counterfactual CPU inputs before GPU')
    return root,W,api,protocol,common,manifest,Store,canonical,admission,accepted


def train(root):
    started=time.monotonic()
    root,W,api,p,common,manifest,Store,canonical,admission,accepted=context(root)
    import sys
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch,transformers,peft,re
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig,get_peft_model,get_peft_model_state_dict,set_peft_model_state_dict
    require=api.require
    require(os.environ.get('CUDA_VISIBLE_DEVICES') not in ('',None,'-1') and torch.cuda.is_available(),'Actual shared CUDA reservation')
    require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1','Pinned Qwen/PEFT')
    torch.manual_seed(p['seed']);torch.cuda.manual_seed_all(p['seed']);random.seed(p['seed'])
    log=root/'rank_events07.jsonl';out=root/'rank_outputs07';out.mkdir();initial_dir=out/'initial_features';initial_dir.mkdir()
    def event(name,**values):
        with log.open('a') as f:f.write(json.dumps(dict(event=name,**values),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def deadline():require(time.monotonic()-started<p['max_gpu_seconds'],'Finite2400s GPU pilot budget')
    cases={uid:api.loadref(r,W) for uid,r in accepted['case_refs'].items()}
    values={}
    for scope in ['train','check']:
        store=Store(manifest,scope)
        ids=sorted([u for u,c in cases.items() if c['scope']==scope],key=lambda u:(cases[u]['sid'],u))
        for uid in ids:
            deadline();case=cases[uid];sid=case['sid'];frames,grid,ordinals=store._source_pixels(sid);clock=store.clocks[sid]
            overview=store.requests[store.by_source[sid][0]]['plan']['videos'][0]
            v,plan=api.build_pixels(torch,frames,grid,ordinals,clock['normalized_exact_pts'],overview,case['block'],sid,case['source_sha256'])
            require(plan==case['plan'],'Runtime real frame/timestamp plan differs from first CPU acceptance')
            prefix=torch.load(api.checked(case['prefix_ref'],W),map_location='cpu',weights_only=True);v.update(prefix)
            require(common.signature(v)==case['input_signature'],'Actual runtime four-tensor bytes differ')
            values[uid]=v
        store.close()
    swap_rows=[api.loadref(r,W) for r in accepted['swap_refs']]
    require(len(values)==126 and len(swap_rows)==28,'All126 real plus28 registered control inputs')
    for row in swap_rows:
        cf=api.swapped_excerpt(torch,values[row['uid']],values[row['donor_uid']])
        require(common.signature(cf)==row['input_signature'],'Counterfactual pixel ownership/signature changed')
    event('ALL_LIVE_INPUTS_ADOPTED',real=126,counterfactual=28,media_decode=0,image_processor=0)
    spec=manifest['model_spec']
    base=Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'],revision=spec['revision'],local_files_only=True,
        trust_remote_code=False,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    for parameter in base.parameters():parameter.requires_grad_(False)
    before=canonical(base,torch)
    require(before['parameters']==p['base_parameters'] and before['sha256']==spec['base_sha256'],'Original BASE exact bytes')
    names=[n for n,m in base.named_modules() if re.search(r'language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$',n)]
    require(len(names)==144,'Only144 original language attention targets')
    model=get_peft_model(base,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.0,bias='none',target_modules=names,
                         modules_to_save=None,task_type='CAUSAL_LM'),adapter_name='rank07')
    native=model.get_base_model()
    for name,parameter in model.named_parameters():
        if 'lora_' in name:parameter.data=parameter.data.float()
        parameter.requires_grad_(False)
    params={n:v for n,v in model.named_parameters() if 'lora_' in n}
    require(len(params)==288 and sum(v.numel() for v in params.values())==15335424,'Actual rank16/288 FP32 matrices')
    require(all('language_model' in n and 'rank07' in n and v.dtype==torch.float32 for n,v in params.items()),'No vision or oldTIME adaptation')
    initial_state=cpu_tree(get_peft_model_state_dict(model,adapter_name='rank07'),torch)
    require(all(bool(torch.isfinite(v).all()) for v in initial_state.values()) and
            all(int(torch.count_nonzero(v))==0 for k,v in initial_state.items() if 'lora_B' in k),'Zero initialized LoRA_B')
    torch.save(initial_state,out/'initial_adapter07.pt')
    definition=dict(adapter_name='rank07',rank=16,alpha=32,dropout=0.0,target_modules=names,head_parameters=4096,
        base_parameters=before['parameters'],new_lora_parameters=15335424,
        actual_resident_parameters=before['parameters']+15335424+4096,
        complete_pipeline_parameters=8797896969,normalization='fixedLayerNorm eps1e-5, no learned affine',
        initial_adapter_ref=api.ref(out/'initial_adapter07.pt'))
    require(definition['complete_pipeline_parameters']<=9000000000,'Complete pipeline <=9B')
    api.save(root/'model_definition07.json',definition)
    head=torch.nn.Linear(4096,1,bias=False,device='cuda:0',dtype=torch.float32)
    torch.nn.init.zeros_(head.weight);head.requires_grad_(False)
    count={'forwards':0,'backwards':0,'lora_optimizer_steps':0,'cpu_head_only_steps':0};mode=['initial']
    def inventory(training):
        require(model.active_adapter=='rank07' and all(not m.disable_adapters and list(m.active_adapters)==['rank07'] for m in model.modules() if hasattr(m,'lora_A')),'Exact active rank07 adapter')
        require(all(v.requires_grad is training for v in params.values()) and head.weight.requires_grad is training,'Exact train/inference allowlist')
        require(all(not v.requires_grad for n,v in model.named_parameters() if 'lora_' not in n),'Frozen BASE/vision/embeddings')
    def guard(module,args):
        deadline();inventory(mode[0]=='train');count['forwards']+=1
    handle=native.model.register_forward_pre_hook(guard)
    def feature(v,*,gradient):
        placed={k:t.to('cuda:0') for k,t in v.items()}
        context_manager=torch.enable_grad() if gradient else torch.inference_mode()
        with context_manager:
            result=native.model(**placed,use_cache=False,return_dict=True)
            hidden=result.last_hidden_state
            require(hidden.shape==(1,v['input_ids'].shape[1],4096),'Actual4096 last causal prefill representation')
            f=torch.nn.functional.layer_norm(hidden[0,-1].float(),(4096,),eps=1e-5)
            require(bool(torch.isfinite(f).all()) and bool(f.abs().max()>0),'Finite nonconstant normalized feature')
        return f
    def variant(uid,swap=None):
        return values[uid] if swap is None else api.swapped_excerpt(torch,values[uid],values[swap])
    model.eval();initial={};initial_refs=[]
    sequence=[(uid,None) for uid in sorted(values)]+[(r['uid'],r['donor_uid']) for r in swap_rows]
    for uid,donor in sequence:
        deadline();key=uid+('.swap' if donor else '');event('BEGIN_INITIAL_FEATURE',uid=key,input_ref=accepted['case_refs'][uid])
        v=variant(uid,donor);f=feature(v,gradient=False).detach().cpu().clone()
        path=initial_dir/(key+'.pt');torch.save(f,path)
        record=dict(uid=key,input_signature=common.signature(v),weights='originalBASE_plus_zeroB_rank07',feature_ref=api.ref(path),
                    feature_sha256=hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest(),actual_model_calls=1)
        api.save(initial_dir/(key+'.json'),record);initial[key]=f;initial_refs.append(api.ref(initial_dir/(key+'.json')))
        event('INITIAL_ACCEPTED',uid=key,output_ref=initial_refs[-1])
    require(count['forwards']==154,'Exactly154 initial real/control feature forwards')
    api.save(root/'initial_feature_acceptance07.json',dict(status='PASS154_REAL_AND_CONTROL_FROZEN_FEATURES',refs=initial_refs,
        forward_calls=154,all_before_training=True,feature_dimension=4096,model_definition_ref=api.ref(root/'model_definition07.json')))
    # Only train targets enter this process. Check preferences remain unread.
    train_pairs=api.loadref(accepted['train_target_ref'],W)
    require(len(train_pairs)==49 and len({r['source_id'] for r in train_pairs})==25,'49 actual human relative pairs/all25sources')
    train_pairs=sorted(train_pairs,key=lambda r:hashlib.sha256(('AIC_RANK_TRAIN07:'+r['pair_id']).encode()).hexdigest())
    require(all(0<=r['preference_left']<=1 and r['left'].startswith('train_') and r['right'].startswith('train_') for r in train_pairs),'Training scope only')
    cpu_head=torch.nn.Linear(4096,1,bias=False,dtype=torch.float32);torch.nn.init.zeros_(cpu_head.weight)
    cpu_opt=torch.optim.AdamW(cpu_head.parameters(),lr=.001,betas=(.9,.999),eps=1e-8,weight_decay=0)
    cpu_opt.zero_grad(set_to_none=True);cpu_losses=[]
    for i,row in enumerate(train_pairs):
        loss=pair_loss(torch,cpu_head(initial[row['left']]).squeeze(),cpu_head(initial[row['right']]).squeeze(),
                       row['preference_left'],pair_weight(row));loss.backward();cpu_losses.append(float(loss.detach()))
        if (i+1)%2==0 or i+1==49:
            torch.nn.utils.clip_grad_norm_(cpu_head.parameters(),1);cpu_opt.step();cpu_opt.zero_grad(set_to_none=True);count['cpu_head_only_steps']+=1
    require(count['cpu_head_only_steps']==25,'Same25 optimizer update budget for head-only')
    torch.save(cpu_tree(cpu_head.state_dict(),torch),out/'head_only07.pt')
    api.save(out/'head_only_completion07.json',dict(status='COMPLETE_FIXED_BASE_HEAD_ONLY_CONTROL',pairs=49,updates=25,
        weights_ref=api.ref(out/'head_only07.pt'),first_loss=cpu_losses[0],last_loss=cpu_losses[-1],new_model_calls=0))
    # Actual attention adaptation is the only difference from the matched control.
    for v in params.values():v.requires_grad_(True)
    head.requires_grad_(True);mode[0]='train';model.train()
    for m in model.modules():
        if isinstance(m,torch.nn.Dropout):m.p=0.0
    model.config.use_cache=False;native.config.text_config.use_cache=False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads()
    opt=torch.optim.AdamW([{'params':list(params.values()),'lr':1e-5},{'params':list(head.parameters()),'lr':.001}],
                          betas=(.9,.999),eps=1e-8,weight_decay=0)
    opt.zero_grad(set_to_none=True);losses=[]
    for i,row in enumerate(train_pairs):
        deadline();event('BEGIN_TRAIN_PAIR',pair_id=row['pair_id'],pair_index=i,optimizer_step=count['lora_optimizer_steps'])
        fa=feature(values[row['left']],gradient=True);fb=feature(values[row['right']],gradient=True)
        za=head(fa).squeeze();zb=head(fb).squeeze();target=row['preference_left']
        unweighted=pair_loss(torch,za,zb,target);loss=unweighted*pair_weight(row)
        require(bool(torch.isfinite(loss)),'Finite pairwise scalar objective')
        raw=dict(pair_id=row['pair_id'],index=i,target=target,score_left=float(za.detach()),score_right=float(zb.detach()),
            unweighted_loss=float(unweighted.detach()),source_weight=49/(25*row['source_pair_count']),scaled_loss=float(loss.detach()),
            input_refs=[accepted['case_refs'][row['left']],accepted['case_refs'][row['right']]])
        api.save(out/(f'train_pair_{i:03d}.json'),raw)
        loss.backward();count['backwards']+=1;losses.append(raw['unweighted_loss'])
        if (i+1)%2==0 or i+1==49:
            hn=torch.nn.utils.clip_grad_norm_(head.parameters(),1.0);ln=torch.nn.utils.clip_grad_norm_(list(params.values()),1.0)
            require(bool(torch.isfinite(hn)) and bool(torch.isfinite(ln)) and float(hn)>0,'Finite nonzero head learning signal and finite LoRA gradients')
            opt.step();opt.zero_grad(set_to_none=True);count['lora_optimizer_steps']+=1
            event('OPTIMIZER_STEP',step=count['lora_optimizer_steps'],head_gradient_norm=float(hn),lora_gradient_norm=float(ln),pairs=i+1)
        # Explicitly mutable operational state, including odd-micro gradients.
        progress=dict(cursor=i+1,counts=dict(count),lora=cpu_tree(get_peft_model_state_dict(model,adapter_name='rank07'),torch),
            head=cpu_tree(head.state_dict(),torch),optimizer=cpu_tree(opt.state_dict(),torch),
            gradients={n:None if v.grad is None else v.grad.detach().cpu().clone() for n,v in params.items()},
            head_gradient=None if head.weight.grad is None else head.weight.grad.detach().cpu().clone(),
            torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state(),order=[r['pair_id'] for r in train_pairs])
        durable_progress(out,progress,torch)
        event('PAIR_DURABLE',pair_id=row['pair_id'],cursor=i+1,checkpoint_ref=api.ref(out/'latest_progress.pt'))
        del fa,fb,za,zb,loss,unweighted,progress
    require(count['backwards']==49 and count['lora_optimizer_steps']==25,'Exact49pairs/25updates, no repeated pair')
    model.eval();model.gradient_checkpointing_disable();model.disable_input_require_grads()
    for v in params.values():v.requires_grad_(False)
    head.requires_grad_(False);mode[0]='final';inventory(False)
    final_state=cpu_tree(get_peft_model_state_dict(model,adapter_name='rank07'),torch)
    changed=[n for n in initial_state if not torch.equal(initial_state[n].view(torch.uint8),final_state[n].view(torch.uint8))]
    require(any('lora_A' in n for n in changed) and any('lora_B' in n for n in changed) and bool(head.weight.abs().max()>0),'Actual A/B attention and scalar head updates required')
    final=dict(lora=final_state,head=cpu_tree(head.state_dict(),torch),definition=definition,protocol_ref=api.ref(root/'protocol06.json'))
    torch.save(final,out/'final_ranker07.pt')
    loaded=torch.load(out/'final_ranker07.pt',map_location='cpu',weights_only=True)
    set_peft_model_state_dict(model,loaded['lora'],adapter_name='rank07');head.load_state_dict(loaded['head'])
    actual=cpu_tree(get_peft_model_state_dict(model,adapter_name='rank07'),torch)
    require(all(actual[n].dtype==torch.float32 and torch.equal(actual[n].view(torch.uint8),loaded['lora'][n].view(torch.uint8)) for n in actual), 'Saved/reloaded FP32 adapter exact')
    require(torch.equal(head.weight.detach().cpu().view(torch.uint8),loaded['head']['weight'].view(torch.uint8)),'Saved/reloaded head exact')
    api.save(out/'training_completion07.json',dict(status='COMPLETE_REAL25_UPDATE_RELATIVE_RANKER',pairs=49,updates=25,
        backward_calls=49,changed_lora_matrices=len(changed),base_before=before,head_only_updates=25,
        final_weights_ref=api.ref(out/'final_ranker07.pt'),head_only_ref=api.ref(out/'head_only07.pt'),
        FP32_save_reload_exact=True,first_loss=losses[0],last_loss=losses[-1],no_checkpoint_selection=True))
    # Final real and explicit Excerpt-swap features, once each; targets unread.
    final_dir=out/'final_features';final_dir.mkdir();output_refs=[]
    check_seq=[(u,None) for u in sorted(values) if u.startswith('check_')]+[(r['uid'],r['donor_uid']) for r in swap_rows]
    require(len(check_seq)==56,'28 real and28 counterfactual heldout inputs')
    for uid,donor in check_seq:
        key=uid+('.swap' if donor else '');event('BEGIN_FINAL_CHECK',uid=key)
        v=variant(uid,donor);f=feature(v,gradient=False).detach().cpu().clone()
        fpath=final_dir/(key+'.pt');torch.save(f,fpath)
        with torch.inference_mode():z=float(head(f.to('cuda:0')).squeeze().cpu())
        record=dict(uid=key,feature_ref=api.ref(fpath),score=z,feature_sha256=hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest(),
            input_signature=common.signature(v),model_weights_ref=api.ref(out/'final_ranker07.pt'),actual_model_calls=1,check_labels_read=False)
        dst=final_dir/(key+'.json');api.save(dst,record);output_refs.append(api.ref(dst));event('FINAL_CHECK_ACCEPTED',uid=key,output_ref=output_refs[-1])
    handle.remove();after=canonical(model,torch)
    require(after==before,'BASE and vision must remain bitexact frozen')
    require(count['forwards']==308,'154INIT +98training +56final actual native top-level forwards')
    require(count['backwards']==49 and count['cpu_head_only_steps']==25 and count['lora_optimizer_steps']==25,'Exact controlled learning counts')
    summary=dict(status='COMPLETE_NATIVE_RELATIVE_RANKER_PILOT_NOT_QUALITY',counts=count,base_before=before,base_after=after,
        initial_feature_refs=initial_refs,final_output_refs=output_refs,training_ref=api.ref(out/'training_completion07.json'),
        seconds=time.monotonic()-started,new_media_decode=0,head_only_updates=25,main_updates=25,check_labels_read=False,
        actual_resident_parameters=definition['actual_resident_parameters'],complete_pipeline_parameters=8797896969,automatic_production=False)
    api.save(root/'gpu_completion07.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ['initial_feature_refs','final_output_refs']}))


def review(root):
    root,W,api,p,common,manifest,Store,canonical,admission,accepted=context(root)
    import torch,numpy as np
    require=api.require
    review_decision=json.loads((root/'review_admission07.json').read_text())
    require(review_decision['gpu_admission_ref']==api.ref(root/'gpu_admission07.json') and review_decision['natural_wrapper_exit_code']==0,
            'Separate natural-completion review decision; original GPU admission is immutable')
    complete=api.loadref(review_decision['gpu_completion_ref'],W)
    require(complete['status']=='COMPLETE_NATIVE_RELATIVE_RANKER_PILOT_NOT_QUALITY','Natural complete GPU stage')
    labels=api.loadref(accepted['check_target_ref'],W)
    require(len(labels)==14 and len({r['source_id'] for r in labels})==8,'Complete14heldout pairs/all8sources')
    outputs={}
    training=api.loadref(complete['training_ref'],W)
    final_weights=torch.load(api.checked(training['final_weights_ref'],W),map_location='cpu',weights_only=True)
    head=final_weights['head']['weight'][0]
    for reference in complete['final_output_refs']:
        record=api.loadref(reference,W);feature=torch.load(api.checked(record['feature_ref'],W),map_location='cpu',weights_only=True)
        require(tuple(feature.shape)==(4096,) and feature.dtype==torch.float32 and bool(torch.isfinite(feature).all()),'Exact saved finite normalized feature')
        require(hashlib.sha256(feature.view(torch.uint8).numpy().tobytes()).hexdigest()==record['feature_sha256'],'Actual feature byte proof')
        z=float(torch.dot(head,feature));require(abs(z-record['score'])<=1e-4*(1+abs(z)),'Independent CPU feature-head scalar replay')
        original_uid=record['uid'].removesuffix('.swap');case=api.loadref(accepted['case_refs'][original_uid],W)
        require(record['model_weights_ref']==api.ref(root/'rank_outputs07/final_ranker07.pt'),'Exact final checkpoint')
        if record['uid'].endswith('.swap'):
            required=next(api.loadref(r,W)['input_signature'] for r in accepted['swap_refs'] if Path(r['path']).name==original_uid+'.swap.json')
        else:required=case['input_signature']
        require(record['input_signature']==required,'Independent source/block/counterfactual signature')
        outputs[record['uid']]=z
    require(len(outputs)==56,'All56 first independent output QA')
    control=torch.load(api.checked(training['head_only_ref'],W),map_location='cpu',weights_only=True)['weight'][0]
    initial_scores={}
    for reference in complete['initial_feature_refs']:
        row=api.loadref(reference,W)
        if not row['uid'].startswith('check_'):continue
        f=torch.load(api.checked(row['feature_ref'],W),map_location='cpu',weights_only=True)
        require(tuple(f.shape)==(4096,) and f.dtype==torch.float32 and bool(torch.isfinite(f).all()) and
                hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest()==row['feature_sha256'], 'Independent initial-control feature bytes')
        initial_scores[row['uid']]=float(torch.dot(control,f))
    require(len(initial_scores)==56,'All original check/control frozen features adopted once')
    def sigmoid(v):return 1/(1+math.exp(-v)) if v>=0 else math.exp(v)/(1+math.exp(v))
    def metrics(scores,swap):
        rows=[]
        for r in labels:
            suffix='.swap' if swap else '';z=scores[r['left']+suffix]-scores[r['right']+suffix]
            target=(1-r['preference_left']) if swap else r['preference_left'];pred=sigmoid(z)
            correct=.5 if z==0 else float((pred>.5)==(target>.5))
            rows.append(dict(pair_id=r['pair_id'],sid=r['source_id'],probability=pred,target=target,
                             correct=correct,brier=(pred-target)**2,logloss=float(np.logaddexp(0,z)-target*z)))
        sources=sorted({r['sid'] for r in rows});averages={}
        for key in ['correct','brier','logloss']:
            averages[key]=sum(sum(r[key] for r in rows if r['sid']==s)/sum(r['sid']==s for r in rows) for s in sources)/len(sources)
        return dict(source_macro_accuracy=averages['correct'],source_macro_brier=averages['brier'],source_macro_logloss=averages['logloss'],sources=len(sources),pairs=len(rows),rows=rows)
    measured=dict(main=metrics(outputs,False),main_swapped=metrics(outputs,True),head_only=metrics(initial_scores,False),head_only_swapped=metrics(initial_scores,True))
    reasons=[];main=measured['main'];control=measured['head_only']
    if main['source_macro_accuracy']<.70:reasons.append('MAIN_HELDOUT_PAIR_ACCURACY_BELOW_POINT70')
    if not main['source_macro_accuracy']>control['source_macro_accuracy']:reasons.append('MAIN_NOT_BETTER_THAN_FROZEN_HEAD_CONTROL')
    if not main['source_macro_brier']<control['source_macro_brier']:reasons.append('MAIN_SOFT_PREFERENCE_BRIER_NOT_BETTER_THAN_CONTROL')
    if measured['main_swapped']['source_macro_accuracy']<.70:reasons.append('EXCERPT_SWAP_DONOR_CONTENT_CONTROL_FAILED')
    result=dict(status='STOP_RELATIVE_RANKER_PILOT' if reasons else 'ELIGIBLE_FOR_SEPARATE_FIXED_BUDGET_FULL8_CHECK',
        stop_reasons=reasons,metrics=measured,independent_output_QA='56PASS',
        current_official_score='UNKNOWN',historical_exposed=True,summary_proxy_not_official_joint_truth=True,
        no_automatic_formal_production=True,protected40_47_unchanged=True)
    api.save(root/'review07.json',result);print(json.dumps({k:v for k,v in result.items() if k!='metrics'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);a.add_argument('--phase',choices=['train','review'],required=True);args=a.parse_args()
    try:train(args.run_root) if args.phase=='train' else review(args.run_root)
    except BaseException:
        root=Path(args.run_root)
        with (root/('failure_'+args.phase+'07.json')).open('x') as f:json.dump(dict(status='ACTUAL_FAILURE_PRESERVE_ALL_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()),f,indent=2)
        raise
