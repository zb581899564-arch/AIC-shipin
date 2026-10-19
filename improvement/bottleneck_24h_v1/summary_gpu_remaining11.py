# Explicit separate remaining version: preserves livepilot06 and its input/recipe.
# Stronger actualpilot guard, postinitialization RNG restore and own registration11.
"""Explicitly admitted summary-TIME pilot/remaining only. No launcher or generation."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback
import torch
from summary_runtime import (WORK,read,sha,bound,ref,save_json,atomic_torch,InputCache,
                             build_training_tokens,validate_training_tokens)
from summary_contract import require

RUN=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROOT=WORK/'bottleneck_24h_20261019_v1'
DEADLINE='2026-10-19T15:52:37Z'
RECIPE=dict(epochs=1,targets=2236,grad_accum=4,updates=559,pilot_updates=4,
            lr=1e-5,weight_decay=0,grad_clip=1,seed=20261019)
TRAINABLE=re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.summary\.weight$')


def utc():return datetime.now(timezone.utc).isoformat()


def journal(path,event,**values):
    with Path(path).open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(utc=utc(),event=event,**values),allow_nan=False)+'\n')
        stream.flush();os.fsync(stream.fileno())


def cpu_tree(value):
    if isinstance(value,torch.Tensor):return value.detach().cpu().contiguous().clone()
    if isinstance(value,dict):return {k:cpu_tree(v) for k,v in value.items()}
    if isinstance(value,list):return [cpu_tree(v) for v in value]
    if isinstance(value,tuple):return tuple(cpu_tree(v) for v in value)
    return value


def adapter_state(model):
    from peft import get_peft_model_state_dict
    state=cpu_tree(get_peft_model_state_dict(model,adapter_name='summary'))
    require(len(state)==288 and all('lora_' in name for name in state),'Exact288 summary matrices')
    return state


def inventory(model,training):
    parameters=[];base_count=adapter_count=0
    for name,p in model.named_parameters():
        if 'lora_' in name:
            match=TRAINABLE.search(name)
            require(match is not None and p.ndim==2 and
                    (p.shape[0] if match[3]=='A' else p.shape[1])==16 and p.requires_grad is training,
                    'Unexpected summary adapter/trainability: '+name)
            parameters.append(p);adapter_count+=p.numel()
        else:
            require(not p.requires_grad,'Base/vision/embedding/head must remain frozen')
            base_count+=p.numel()
    layers=[m for m in model.modules() if hasattr(m,'lora_A')]
    require(len(parameters)==288 and len(layers)==144 and
            all(set(m.lora_A)=={'summary'} and list(m.active_adapters)==['summary'] and not m.disable_adapters for m in layers)
            and model.active_adapter=='summary' and base_count==8767123696 and adapter_count==15335424,
            'Actual144 language targets/288 rank16 matrices/base inventory')
    total=base_count+adapter_count+15335424+98329
    require(total==8797892873<=9_000_000_000,'Conservative full pipeline inventory')
    return parameters,dict(base=base_count,summary=adapter_count,old_TIME_counted=15335424,
        semantic_counted=98329,conservative_full_pipeline=total,physical_resident=base_count+adapter_count,
        initialized_from_original_TIME=True,old_TIME_second_copy_loaded=False,matrices=288,language_targets=144)


def mask_functions_ast(path):
    import ast
    tree=ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    selected={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()
              for n in tree.body if isinstance(n,ast.FunctionDef) and
              n.name in ('build_training_tokens','validate_training_tokens')}
    require(len(selected)==2,'Both original first-mask helpers required')
    return selected


def registration(root):
    reg=read(root/'summary_GPU_registration_11.json')
    require(reg['schema']=='SOURCE_SUMMARY_TIME_R16_GPU_V1' and reg['phase_admission']=='REMAINING555_ONLY_AFTER_PILOT06' and
            reg['recipe']==RECIPE and reg['deadline_utc']==DEADLINE and reg['max_gpu_seconds']>0,
            'Fixed pilot registration/recipe/deadline')
    here=Path(__file__).resolve().parent
    for filename in ('summary_gpu.py','summary_runtime.py','summary_contract.py'):
        require(bound(reg['code'][filename])==(here/filename).resolve(),'Actual executed code differs: '+filename)
    accepted=read(bound(reg['first_input_acceptance_ref']))
    require(accepted['status']=='PASS_ALL144_FIRST_NEW_TWO_VIEW_CPU_INPUTS_2236_TOKEN_TARGETS' and
            accepted['sources']==25 and accepted['windows']==144 and accepted['original_reviewer_targets']==2236,
            'Complete first input gate required')
    prepared=read(bound(accepted['prepared']))
    mask=read(bound(reg['first_mask_acceptance_ref']))
    require(mask['status']=='PASS_FIRST_ALL2236_ACTUAL_ASSISTANT_MASK_CAUSAL_SHIFT_EOS_AND_TARGET_JOIN' and
            mask['targets']==2236 and mask['windows']==144 and mask['sources']==25 and
            mask['training_targets_ref']==prepared['training_targets'] and
            mask['adopted_input_gate']==reg['first_input_acceptance_ref'],
            'First actual2236 mask/shift/EOS gate required; CPU05 boolean is insufficient')
    require(mask_functions_ast(bound(mask['mask_runtime_snapshot']))==mask['mask_function_AST_sha256']==mask_functions_ast(here/'summary_runtime.py'),
            'Executed training mask functions differ from first independent mask QA')
    require(bound(reg['model_config_ref'])==RUN/'b_score_aligned_package_v4/config.json','Original config only')
    cfg=read(bound(reg['model_config_ref']))
    old=bound(reg['old_time_weights_ref'])
    require(old==Path(cfg['b_adapter'])/'adapter_model.safetensors' and sha(old)==cfg['b_adapter_sha256'] and
            cfg['base_parameters']==8767123696 and cfg['complete_parameters']==8782459120,'Original TIME/base config identity')
    return reg,cfg,prepared


def schedule(prepared):
    rows=[json.loads(line) for line in bound(prepared['training_targets']).read_text().splitlines() if line.strip()]
    require(len(rows)==2236 and len({(r['uid'],r['reviewer']) for r in rows})==2236,'All2236 unique reviewer/window targets')
    windows=defaultdict(set);reviewers=defaultdict(set)
    for row in rows:windows[row['sid']].add(row['uid']);reviewers[row['uid']].add(row['reviewer'])
    require(len(windows)==25 and sum(len(v) for v in windows.values())==144,'All25 sources144 windows')
    totals=Counter()
    for row in rows:
        expected=2236/(25*len(windows[row['sid']])*len(reviewers[row['uid']]))
        require(math.isfinite(row['weight']) and abs(row['weight']-expected)<1e-12 and
                row['empty_means_unselected_source_summary_only'] is True,'Original source/window/reviewer weight')
        totals[row['sid']]+=row['weight']
    require(all(abs(v-2236/25)<1e-9 for v in totals.values()),'Epoch source weight accounting')
    order=torch.randperm(2236,generator=torch.Generator().manual_seed(20261019)).tolist()
    digest=hashlib.sha256(json.dumps(dict(targets=prepared['training_targets'],order=order,recipe=RECIPE),
                                  sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return rows,order,digest


def rng_state():
    import numpy as np
    n=np.random.get_state()
    return dict(torch_rng_state=torch.get_rng_state(),cuda_rng_states=torch.cuda.get_rng_state_all(),
        python_rng_state=random.getstate(),numpy_rng=dict(name=n[0],keys=torch.tensor(n[1].astype('int64')),
        position=n[2],has_gauss=n[3],cached_gaussian=n[4]))


def restore_rng(state):
    import numpy as np
    torch.set_rng_state(state['torch_rng_state']);torch.cuda.set_rng_state_all(state['cuda_rng_states'])
    random.setstate(state['python_rng_state']);n=state['numpy_rng']
    np.random.set_state((n['name'],n['keys'].numpy().astype('uint32'),n['position'],n['has_gauss'],n['cached_gaussian']))


def train(root,phase):
    # No import above changes CUDA_VISIBLE_DEVICES, initializes a model, or enters an old experiment.
    require(os.environ.get('CUDA_VISIBLE_DEVICES') not in (None,''),'GPU wrapper must expose CUDA before import')
    reg,cfg,prepared=registration(root)
    import numpy as np
    import transformers,peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel,set_peft_model_state_dict
    from safetensors.torch import load_file
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1' and torch.cuda.is_available(),'Pinned actual model runtime')
    rows,order,schedule_sha=schedule(prepared)
    output=root/'summary_model_06';output.mkdir(exist_ok=True)
    require(phase in ('pilot','remaining'),'Explicit training phase')
    save_json(output/(phase+'_claim.json'),dict(utc=utc(),pid=os.getpid(),registration=ref(root/'summary_GPU_registration_11.json'),phase=phase))
    completed=successful_micro=0;last_checkpoint=None;raw=[];started=time.monotonic();phase_budget=reg['max_gpu_seconds']
    def deadline():
        require(datetime.now(timezone.utc)<datetime.fromisoformat(DEADLINE.replace('Z','+00:00')) and
                time.monotonic()-started<phase_budget,'No new forward/update after registered deadline/budget')
    try:
        resumed=None;start_step=0
        if phase=='pilot': require(not (output/'progress.pt').exists(),'Existing progress blocks fresh pilot')
        else:
            admission=read(root/'summary_remaining_admission.json')
            require(admission['status']=='ADMIT_EXPLICIT_SUMMARY_REMAINING' and
                    admission['registration_ref']==ref(root/'summary_GPU_registration_11.json') and
                    admission['schedule_sha256']==schedule_sha,'Explicit matching remaining admission required')
            pilot=read(bound(admission['pilot_completion_ref']))
            require(bound(admission['pilot_completion_ref'])==(output/'pilot_completion.json').resolve() and
                    pilot['status']=='PASS_SUMMARY_PILOT4_ENGINEERING_ONLY' and pilot['completed_updates']==4 and
                    pilot['successful_micro']==16 and pilot['reload_QA_forward_count']==2 and
                    pilot['schedule_sha256']==schedule_sha and pilot['reload_all288_exact'] is True,
                    'Actual successful pilot4 and two reload QA gates required before remaining')
            require(admission['deadline_utc']==DEADLINE and admission['max_gpu_seconds']>0,'Explicit remaining deadline/GPU budget')
            phase_budget=admission['max_gpu_seconds']
            checkpoint=bound(admission['progress_ref'])
            require(sha(output/'progress.pt')==sha(checkpoint),'Current progress advanced outside admitted recovery')
            resumed=torch.load(checkpoint,map_location='cpu',weights_only=True)
            start_step=resumed['completed_updates']
            require(start_step==admission['completed_updates'] and resumed['successful_micro']==start_step*4 and
                    4<=start_step<559 and admission['remaining_updates']==559-start_step and
                    resumed['schedule_sha256']==schedule_sha and resumed['recipe']==RECIPE,
                    'Only actual saved successful update boundary may be resumed')
            require(start_step!=4 or admission['progress_ref']==pilot['progress_ref'],
                    'First remaining must adopt exact immutable pilot4 checkpoint')
            completed=start_step;successful_micro=start_step*4;last_checkpoint=ref(checkpoint)
        random.seed(20261019);np.random.seed(20261019);torch.manual_seed(20261019);torch.cuda.manual_seed_all(20261019)
        deadline()
        base=Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=cfg['model_revision'],
            local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
        for p in base.parameters():p.requires_grad_(False)
        before=canonical_frozen_hash(base,torch)
        require(before['parameters']==8767123696 and before['sha256']==cfg['expected_base_sha256'],'Actual original base bytes')
        old_config=read(Path(cfg['b_adapter'])/'adapter_config.json')
        require(old_config['r']==16 and old_config['lora_alpha']==32 and old_config['lora_dropout']==.05 and
                old_config['bias']=='none' and old_config['modules_to_save'] is None and
                set(old_config['target_modules'])=={'q_proj','k_proj','v_proj','o_proj'},'Original TIME rank/config')
        model=PeftModel.from_pretrained(base,cfg['b_adapter'],adapter_name='summary',is_trainable=True)
        for name,p in model.named_parameters():p.requires_grad_(TRAINABLE.search(name) is not None)
        initial=adapter_state(model);original=load_file(str(bound(reg['old_time_weights_ref'])),device='cpu')
        require(set(initial)==set(original) and all(torch.equal(initial[k],original[k].to(initial[k].dtype)) for k in initial),
                'Summary must initialize from original saved TIME values')
        del original
        parameters,inv=inventory(model,True)
        optimizer=torch.optim.AdamW(parameters,lr=1e-5,betas=(.9,.999),eps=1e-8,weight_decay=0)
        if resumed is not None:
            set_peft_model_state_dict(model,resumed['adapter_state_dict'],adapter_name='summary')
            actual=adapter_state(model)
            require(set(actual)==set(resumed['adapter_state_dict']) and all(torch.equal(actual[k],v) for k,v in resumed['adapter_state_dict'].items()),'Exact admitted progress adapter')
            optimizer.load_state_dict(resumed['optimizer_state_dict']);del actual
        inputs=InputCache(prepared['source_catalog'])
        model.config.use_cache=False;model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        model.train()
        for name,module in model.named_modules():
            if name.endswith('.visual'):module.eval()
        native=model.get_base_model()
        # Suffix EOS was first CPU checked; the actual ID comes from the pinned tokenizer.
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
        eos=tokenizer.convert_tokens_to_ids('<|im_end|>')
        require(eos==read(bound(reg['first_mask_acceptance_ref']))['eos_token_id'] and
                all(row['suffix_ids'][-1]==eos for row in rows),'Actual pinned EOS equals first mask gate and every target')
        # Restore only after all model/cache/tokenizer/checkpoint setup is done,
        # immediately before any new micro can consume training randomness.
        if resumed is not None:restore_rng(resumed);del resumed
        def forward(row,training,tag):
            deadline();request,prefix,pixels=inputs.request(row['input_ref'])
            require(request['uid']==row['uid'] and request['sid']==row['sid'],'Supervised request identity')
            tokens=build_training_tokens(prefix,row['suffix_ids'])
            # Exact mask was independently first-checked; here only construct its accepted definition.
            values=dict(input_ids=tokens['full_input_ids'],attention_mask=tokens['attention_mask'],**pixels)
            gpu={k:v.to('cuda:0') for k,v in values.items()}
            journal(output/'micro.jsonl','BEGIN_FORWARD',tag=tag,uid=row['uid'],reviewer=row['reviewer'],training=training)
            result=native.model(**gpu,use_cache=False,return_dict=True)
            hidden=result.last_hidden_state.index_select(1,tokens['causal_logits_indices'].to('cuda:0'))
            logits=native.lm_head(hidden).float()
            target=tokens['targets'].to('cuda:0')
            loss=torch.nn.functional.cross_entropy(logits.reshape(-1,logits.shape[-1]),target.reshape(-1),reduction='mean')
            return loss,logits,tokens
        stop=4 if phase=='pilot' else 559
        for step in range(start_step+1,stop+1):
            optimizer.zero_grad(set_to_none=True)
            for micro in range((step-1)*4,step*4):
                row=rows[order[micro]];loss,logits,tokens=forward(row,True,'train_%04d'%micro)
                value=float(loss.detach().cpu())
                journal(output/'micro.jsonl','RAW_LOSS',micro=micro,step=step,uid=row['uid'],reviewer=row['reviewer'],
                    loss=value if math.isfinite(value) else None,loss_repr=repr(value),weight=row['weight'],suffix_tokens=len(row['suffix_ids']))
                require(math.isfinite(value) and loss.requires_grad,'Finite connected actual sequence CE required')
                (loss*row['weight']/4).backward();successful_micro=micro+1
                journal(output/'micro.jsonl','BACKWARD_COMPLETE',micro=micro,successful_micro=successful_micro)
                del loss,logits,tokens
            gradients=[p.grad for p in parameters]
            require(all(g is not None and bool(torch.isfinite(g).all()) for g in gradients),'All288 actual finite connected gradients required')
            nonzero=sum(bool(torch.count_nonzero(g)) for g in gradients)
            norm=float(torch.nn.utils.clip_grad_norm_(parameters,1.).detach().cpu())
            require(nonzero>0 and math.isfinite(norm) and norm>0,'Nonzero actual gradient connectivity required')
            deadline();optimizer.step();completed=step
            checkpoint=dict(schema='SOURCE_SUMMARY_SUCCESSFUL_UPDATE_PROGRESS_V1',completed_updates=step,successful_micro=successful_micro,
                adapter_state_dict=adapter_state(model),optimizer_state_dict=cpu_tree(optimizer.state_dict()),
                schedule_sha256=schedule_sha,recipe=RECIPE,training_targets_ref=prepared['training_targets'],
                registration_ref=ref(root/'summary_GPU_registration_11.json'),**cpu_tree(rng_state()))
            atomic_torch(output/'progress.pt',checkpoint,replace=True);last_checkpoint=ref(output/'progress.pt')
            journal(output/'updates.jsonl','SUCCESSFUL_UPDATE_PERSISTED',step=step,successful_micro=successful_micro,
                gradient_norm=norm,nonzero_gradient_matrices=nonzero,finite_gradient_matrices=288,progress=last_checkpoint)
            require(all(bool(torch.isfinite(v).all()) for v in checkpoint['adapter_state_dict'].values()),'Finite updated summary matrices')
            inventory(model,True);del checkpoint
        optimizer.zero_grad(set_to_none=True);model.eval();model.gradient_checkpointing_disable()
        for p in model.parameters():p.requires_grad_(False)
        inventory(model,False);final=adapter_state(model)
        require(any(not torch.equal(initial[k],final[k]) for k in initial),'Summary adapter did not change')
        after=canonical_frozen_hash(model,torch)
        require(after==before and sha(bound(reg['old_time_weights_ref']))==cfg['b_adapter_sha256'],'Base/vision/head or original TIME file changed')
        if phase=='pilot':
            # Exactly two registered teacher-forced QA forwards on the same new input.
            with torch.inference_mode():
                qa_loss,qa_logits,_=forward(rows[order[0]],False,'pilot_reload_before')
                before_logits=qa_logits.detach().cpu();del qa_loss,qa_logits
            atomic_torch(output/'reload_before_logits.pt',before_logits);raw.append(ref(output/'reload_before_logits.pt'))
        adapter=output/(phase+'_adapter');adapter.mkdir(exist_ok=False)
        model.save_pretrained(adapter,safe_serialization=True,selected_adapters=['summary'],save_embedding_layers=False)
        weights=list(adapter.rglob('adapter_model.safetensors'));require(len(weights)==1,'Exactly one saved summary adapter')
        saved=load_file(str(weights[0]),device='cpu')
        require(set(saved)==set(final) and all(torch.equal(saved[k],final[k]) for k in saved),'Saved all288 tensors exact')
        del optimizer,parameters
        base=model.unload()
        model=PeftModel.from_pretrained(base,str(weights[0].parent),adapter_name='summary',is_trainable=False).eval()
        for p in model.parameters():p.requires_grad_(False)
        native=model.get_base_model();actual=adapter_state(model)
        require(set(actual)==set(final) and all(torch.equal(actual[k],final[k]) for k in actual),'Reload all288 summary tensors exact')
        inventory(model,False)
        if phase=='pilot':
            with torch.inference_mode():
                qa_loss,qa_logits,_=forward(rows[order[0]],False,'pilot_reload_after')
                after_logits=qa_logits.detach().cpu();del qa_loss,qa_logits
            atomic_torch(output/'reload_after_logits.pt',after_logits);raw.append(ref(output/'reload_after_logits.pt'))
            require(torch.equal(before_logits,after_logits) and bool(torch.isfinite(after_logits).all()),'Reload same-input teacher-forced logits must be exact and finite')
            # Immutable copy is made only once; current progress remains one rolling checkpoint.
            with (output/'progress.pt').open('rb') as src,(output/'pilot_progress.pt').open('xb') as dst:
                for block in iter(lambda:src.read(8<<20),b''):dst.write(block)
                dst.flush();os.fsync(dst.fileno())
            last_checkpoint=ref(output/'pilot_progress.pt')
        for file in adapter.rglob('*'):
            if file.is_file():
                with file.open('rb') as handle:os.fsync(handle.fileno())
        require(canonical_frozen_hash(model,torch)==before and sha(bound(reg['old_time_weights_ref']))==cfg['b_adapter_sha256'],
                'Final frozen base and original TIME bytes')
        save_json(output/(phase+'_completion.json'),dict(status='PASS_SUMMARY_PILOT4_ENGINEERING_ONLY' if phase=='pilot' else 'PASS_SUMMARY_FINAL559_SINGLE_EPOCH',
            utc=utc(),completed_updates=completed,successful_micro=successful_micro,progress_ref=last_checkpoint,
            adapter_weights_ref=ref(weights[0]),adapter_directory=str(weights[0].parent),schedule_sha256=schedule_sha,
            inventory=inv,base_fingerprint=before,original_TIME_weights_ref=reg['old_time_weights_ref'],
            first_mask_acceptance_ref=reg['first_mask_acceptance_ref'],reload_all288_exact=True,
            reload_QA_forward_count=2 if phase=='pilot' else 0,reload_raw_refs=raw,
            remaining_automatically_admitted=False,free_generation_calls=0,training_targets=2236,recipe=RECIPE))
    except BaseException as exc:
        save_json(output/('%s_failure_%s.json'%(phase,os.getpid())),dict(utc=utc(),error=repr(exc),traceback=traceback.format_exc(),
            completed_updates=completed,successful_micro=successful_micro,last_checkpoint=last_checkpoint,
            reload_raw_refs=raw,automatic_retry=False,failure_to_empty=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(ROOT));parser.add_argument('--phase',choices=['remaining'],required=True)
    args=parser.parse_args();actual_root=Path(args.root).resolve(strict=True)
    require(actual_root==ROOT,'Independent registered summary root only')
    train(actual_root,args.phase)
