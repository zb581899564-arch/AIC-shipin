"""Full historical eight-source fixed-budget check, separately admitted only.

Existing identical final or frozen features are adopted, never model-repeated.
No official-data interface, threshold calibration, or production in this file.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import traceback


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def context(root):
    root=Path(root).resolve(strict=True);W=root.parent.parent
    reg=json.loads((root/'registration08.json').read_text())
    old=Path(reg['ranker_root']);train_api=module(old/'rank_train07.py','trained_ranker07_contract08')
    _,_,api,p,common,manifest,Store,canonical,_,accepted=train_api.context(old)
    api.checked(reg['code_ref'],W);api.require(reg['code_ref']==api.ref(__file__),'Exact08 implementation binding')
    done=api.loadref(reg['prior_chain_ref'],W);api.require(done['status']=='FINITE_RELATIVE_RANKER_PILOT_AND_FIRST_REVIEW_COMPLETED','Natural pilot+first review required')
    api.checked(reg['prior_review_ref'],W);api.checked(reg['prior_scope_ref'],W)
    api.require(reg['roles'] in [['head_only'],['head_only','main']],'Fixed two controlled readouts at most')
    return root,W,reg,old,api,p,common,manifest,Store,canonical,accepted,train_api


def prepare(root):
    root,W,reg,old,api,p,common,manifest,Store,canonical,accepted,train_api=context(root)
    import torch
    from transformers import AutoProcessor
    started=time.monotonic();model=manifest['model_spec']
    processor=AutoProcessor.from_pretrained(model['model_dir'],revision=model['revision'],local_files_only=True,trust_remote_code=False)
    store=Store(manifest,'check');feasible=api.loadref(reg['feasibility_ref'],W)
    source_rows=[api.loadref(r,W) for r in feasible['source_refs'] if Path(r['path']).name.startswith('check_')]
    out=root/'inputs08';out.mkdir();cases={};adopted=0;new=0
    for source in source_rows:
        sid=source['source_id'];frames,grid,ordinals=store._source_pixels(sid);clock=store.clocks[sid]
        overview=store.requests[store.by_source[sid][0]]['plan']['videos'][0]
        for block in source['blocks']:
            uid=f'check_{sid}_B{block["index"]:04d}'
            if uid in accepted['case_refs']:
                case=api.loadref(accepted['case_refs'][uid],W)
                api.require(case['block']==block and case['source_sha256']==source['source_sha256'],'Actual identical original case adoption')
                cases[uid]=dict(case_ref=accepted['case_refs'][uid],adopted_input=True);adopted+=1;continue
            api.require(time.monotonic()-started<1200,'Bounded first remaining108 input preparation')
            v,plan=api.build_pixels(torch,frames,grid,ordinals,clock['normalized_exact_pts'],overview,block,sid,source['source_sha256'])
            store._helpers().independent_pixels(frames,grid,v,plan,ordinals,clock['normalized_exact_pts'])
            prefix,text=api.build_text(processor,plan,v['video_grid_thw'],clock['physical_end_exact'],p);v.update(prefix)
            store._helpers().independent_text(processor,plan,v,text)
            pp=out/(uid+'.prefix.pt');torch.save(prefix,pp)
            api.require(all(torch.equal(prefix[k],torch.load(pp,map_location='cpu',weights_only=True)[k]) for k in prefix),'New prefix exact reload')
            case=dict(uid=uid,scope='check',sid=sid,block=block,source_sha256=source['source_sha256'],source_clock_ref=source['clock_ref'],
                prefix_ref=api.ref(pp),plan=plan,text=text,input_signature=common.signature(v),labels_in_text=False)
            cp=out/(uid+'.json');api.save(cp,case);cases[uid]=dict(case_ref=api.ref(cp),adopted_input=False);new+=1
        store.close()
    api.require(len(source_rows)==8 and len(cases)==136 and adopted==28 and new==108,'All136 blocks/all8 sources, exactly108 first new real inputs')
    result=dict(status='PASS_FULL8_FIRST108_INPUTS_AND28_ADOPTED',case_refs=cases,sources=8,blocks=136,new_inputs=108,adopted_inputs=28,
        seconds=time.monotonic()-started,new_media_decodes=0,new_image_processor=0,registration_ref=api.ref(root/'registration08.json'))
    api.save(root/'input_acceptance08.json',result)


def gpu(root):
    root,W,reg,old,api,p,common,manifest,Store,canonical,accepted,train_api=context(root)
    import sys,re
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch,peft,transformers
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig,get_peft_model,get_peft_model_state_dict,set_peft_model_state_dict
    require=api.require;require(torch.cuda.is_available() and os.environ.get('CUDA_VISIBLE_DEVICES') not in ('',None,'-1'),'Actual shared CUDA reservation')
    a=json.loads((root/'gpu_admission08.json').read_text());inputs=api.loadref(a['input_acceptance_ref'],W)
    require(a['registration_ref']==api.ref(root/'registration08.json') and a['approved'],'Separate actual full8 GPU admission')
    complete=api.loadref(json.loads((old/'review_admission07.json').read_text())['gpu_completion_ref'],W)
    training=api.loadref(complete['training_ref'],W);final=torch.load(api.checked(training['final_weights_ref'],W),map_location='cpu',weights_only=True)
    initial=torch.load(api.checked(final['definition']['initial_adapter_ref'],W),map_location='cpu',weights_only=True)
    frozen_head=torch.load(api.checked(training['head_only_ref'],W),map_location='cpu',weights_only=True)['weight'][0]
    case_refs=inputs['case_refs'];cases={u:api.loadref(r['case_ref'],W) for u,r in case_refs.items()}
    values={};store=Store(manifest,'check')
    for uid,case in sorted(cases.items(),key=lambda row:(row[1]['sid'],row[0])):
        if case_refs[uid]['adopted_input']:continue
        sid=case['sid'];frames,grid,ordinals=store._source_pixels(sid);clock=store.clocks[sid]
        overview=store.requests[store.by_source[sid][0]]['plan']['videos'][0]
        v,plan=api.build_pixels(torch,frames,grid,ordinals,clock['normalized_exact_pts'],overview,case['block'],sid,case['source_sha256'])
        v.update(torch.load(api.checked(case['prefix_ref'],W),map_location='cpu',weights_only=True))
        require(plan==case['plan'] and common.signature(v)==case['input_signature'],'Adopt actual first input QA')
        values[uid]=v
    store.close();require(len(values)==108,'Exactly108 new real model inputs')
    spec=manifest['model_spec'];model=Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'],revision=spec['revision'],local_files_only=True,
        trust_remote_code=False,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    for v in model.parameters():v.requires_grad_(False)
    before=canonical(model,torch);require(before['sha256']==spec['base_sha256'],'Frozen original BASE')
    targets=[n for n,m in model.named_modules() if re.search(r'language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$',n)]
    model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0,bias='none',target_modules=targets,task_type='CAUSAL_LM'),adapter_name='rank07')
    native=model.get_base_model()
    for name,v in model.named_parameters():
        if 'lora_' in name:v.data=v.data.float()
        v.requires_grad_(False)
    model.eval();out=root/'outputs08';out.mkdir();outputs={};calls=0;start=time.monotonic()
    def event(name,**data):
        with (root/'events08.jsonl').open('a') as f:f.write(json.dumps(dict(event=name,**data),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def guard(module,args):
        nonlocal calls
        require(not any(v.requires_grad for v in model.parameters()),'Full8 inference must remain frozen')
        require(model.active_adapter=='rank07' and all(list(m.active_adapters)==['rank07'] and not m.disable_adapters for m in model.modules() if hasattr(m,'lora_A')),'Actual one explicitly restored adapter')
        require(time.monotonic()-start<1200,'Bounded full8 model budget');calls+=1
    handle=native.model.register_forward_pre_hook(guard)
    old_initial={api.loadref(r,W)['uid']:r for r in complete['initial_feature_refs']}
    old_final={api.loadref(r,W)['uid']:r for r in complete['final_output_refs']}
    for role in reg['roles']:
        state=initial if role=='head_only' else final['lora'];head=frozen_head if role=='head_only' else final['head']['weight'][0]
        set_peft_model_state_dict(model,state,adapter_name='rank07')
        actual=get_peft_model_state_dict(model,adapter_name='rank07')
        require(all(v.dtype==torch.float32 and torch.equal(v.detach().cpu().view(torch.uint8),state[n].view(torch.uint8)) for n,v in actual.items()),'Exact FP32 role reload')
        role_refs=[]
        for uid,case in sorted(cases.items()):
            if case_refs[uid]['adopted_input']:
                parent=old_initial[uid] if role=='head_only' else old_final[uid];record=api.loadref(parent,W)
                f=torch.load(api.checked(record['feature_ref'],W),map_location='cpu',weights_only=True)
                z=float(torch.dot(head,f));ref_feature=record['feature_ref'];adopt=True
            else:
                event('BEGIN_NEW_FEATURE',role=role,uid=uid)
                v=values[uid]
                with torch.inference_mode():
                    hidden=native.model(**{k:t.to('cuda:0') for k,t in v.items()},use_cache=False,return_dict=True).last_hidden_state
                    require(hidden.shape==(1,v['input_ids'].shape[1],4096),'Real last-prefill feature position')
                    f=torch.nn.functional.layer_norm(hidden[0,-1].float(),(4096,),eps=1e-5).cpu().clone()
                require(bool(torch.isfinite(f).all()),'Finite new fullsource feature')
                fp=out/(role+'_'+uid+'.pt');torch.save(f,fp);z=float(torch.dot(head,f));ref_feature=api.ref(fp);adopt=False;parent=None
            record=dict(uid=uid,role=role,score=z,feature_ref=ref_feature,
                feature_sha256=hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest(),input_signature=case['input_signature'],
                adopted_prior_model=adopt,prior_output_ref=parent,actual_model_calls=0 if adopt else 1)
            rp=out/(role+'_'+uid+'.json');api.save(rp,record);role_refs.append(api.ref(rp))
            event('ACCEPTED',role=role,uid=uid,adopted=adopt,output_ref=role_refs[-1])
        outputs[role]=role_refs
    handle.remove();after=canonical(model,torch);require(before==after and calls==108*len(reg['roles']),'Exact frozen BASE and new-call denominator')
    api.save(root/'gpu_completion08.json',dict(status='COMPLETE_FULL8_RANK_FEATURES_NOT_QUALITY',outputs=outputs,
        actual_model_calls=calls,adopted_models=28*len(reg['roles']),new_updates=0,base_before=before,base_after=after,seconds=time.monotonic()-start,
        final_ranker_ref=training['final_weights_ref'],frozen_head_ref=training['head_only_ref'],check_labels_read=False))


def review(root):
    root,W,reg,old,api,p,common,manifest,Store,canonical,accepted,train_api=context(root)
    import torch,numpy as np
    decision=json.loads((root/'review_admission08.json').read_text());c=api.loadref(decision['gpu_completion_ref'],W)
    api.require(decision['natural_wrapper_exit_code']==0 and c['status']=='COMPLETE_FULL8_RANK_FEATURES_NOT_QUALITY','Natural full8 model completion')
    select=module(api.checked(reg['selection_code_ref'],W),'fixed_native_selection08').select_fixed_budget
    utility=module(W/'evidence_reset_goal_20261020_v1/diagnostic.py','adopted_native_utility08').utility
    inputs=api.loadref(json.loads((root/'gpu_admission08.json').read_text())['input_acceptance_ref'],W)
    cases={uid:api.loadref(r['case_ref'],W) for uid,r in inputs['case_refs'].items()}
    final=torch.load(api.checked(c['final_ranker_ref'],W),map_location='cpu',weights_only=True)
    base_head=torch.load(api.checked(c['frozen_head_ref'],W),map_location='cpu',weights_only=True)['weight'][0]
    metrics={}
    for role,refs in c['outputs'].items():
        head=base_head if role=='head_only' else final['head']['weight'][0];scores={}
        for reference in refs:
            r=api.loadref(reference,W);case=cases[r['uid']]
            if r['adopted_prior_model']:
                # Prior output QA already succeeded; adopt its feature proof, no model replay.
                prior=api.loadref(r['prior_output_ref'],W);api.require(prior['feature_ref']==r['feature_ref'],'Exact original accepted feature adopted')
            f=torch.load(api.checked(r['feature_ref'],W),map_location='cpu',weights_only=True)
            api.require(hashlib.sha256(f.view(torch.uint8).numpy().tobytes()).hexdigest()==r['feature_sha256'] and r['input_signature']==case['input_signature'],'Independent fullsource bytes/input ownership')
            z=float(torch.dot(head,f));api.require(abs(z-r['score'])<=1e-6*(1+abs(z)),'Independent exact CPU scalar readout')
            scores[r['uid']]=z
        api.require(len(scores)==136,'All136 scored blocks before source comparison')
        rows=[];store=Store(manifest,'check');selections={}
        for sid in sorted(store.source_ids):
            human=store.source_supervision(sid);n=len(human['clock']['normalized_exact_pts']);baseline=set(human['baseline'])
            api.require(all(len(m)==n and all(m) for m in human['known_masks']),'UNKNOWN is not negative or padded')
            labels=np.zeros((n,len(human['raters'])),dtype=bool)
            for col,truth in enumerate(human['raters']):labels[sorted(truth),col]=True
            blocks=[dict(case['block'],score=scores[uid]) for uid,case in cases.items() if case['sid']==sid]
            chosen,info=select(n,baseline,blocks);selections[sid]=chosen
            rows.append(dict(source_id=sid,f1=utility(chosen,labels),baseline_f1=utility(baseline,labels),**info))
        store.close();api.save(root/(role+'_native_selections08.json'),selections)
        metrics[role]=dict(macro_f1=sum(r['f1'] for r in rows)/8,baseline_f1=sum(r['baseline_f1'] for r in rows)/8,
            improved=sum(r['f1']>r['baseline_f1'] for r in rows),worsened=sum(r['f1']<r['baseline_f1'] for r in rows),
            added=sum(r['added'] for r in rows),removed=sum(r['removed'] for r in rows),per_source=rows)
    api.save(root/'comparison08.json',dict(status='COMPLETE_FULL8_FIXED_BUDGET_DIAGNOSTIC_REQUIRES_MAIN_REVIEW',metrics=metrics,
        actual_model_calls=c['actual_model_calls'],old_models_adopted=c['adopted_models'],all_source_frame_budgets_exact=True,
        historical_exposed=True,summary_temporal_proxy_only=True,official_joint_score='UNKNOWN',automatic_production=False))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);a.add_argument('--phase',choices=['prepare','gpu','review'],required=True);args=a.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        with (Path(args.run_root)/('failure_'+args.phase+'08.json')).open('x') as f:json.dump(dict(status='ACTUAL_FAILURE_NOT_EMPTY_OR_NEGATIVE',traceback=traceback.format_exc()),f,indent=2)
        raise
