"""New, separately admitted five-epoch 8B B training; no implicit test inference."""
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import random
import sys
import time
import traceback

from full_contract import admit, verify_lock, SCOPE
from sft_contract import (require, sha256, BASE_PARAMS, LORA_PARAMS, TOTAL_PARAMS, REVISION,
    language_target_names, validate_trainable_names, verify_live_gpu_reservation)
from train_sft import build_example, unique_parameters, gradient_evidence, load_helper
from verify_saved_smoke import canonical_frozen_hash


def write(path, value):
    path=Path(path)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temp.replace(path)


def execute(contract, config_path, admission_path):
    verify_live_gpu_reservation()
    config=contract['config']; output=Path(config['out_dir']); output.mkdir(parents=True,exist_ok=True)
    report=dict(status='RUNNING_FULL_INTERVAL_SFT',scope=SCOPE,quality_claim=False,
        full_training_completed=False,formal_c_bce_admitted=False,negative_targets_created=False,
        config_sha256=contract['config_sha256'],admission_sha256=contract['admission_sha256'],
        source_lock_sha256=contract['lock_sha256'],train_manifest_sha256=config['train_manifest']['sha256'],
        parents=704,source_groups=602,windows=724,epochs=5,optimizer_steps=0,effective_batches=0,
        epoch_effective_counts={str(epoch):0 for epoch in range(1,6)},updates=[],
        initialization=config['initialization'],final_checkpoint_only=True,uploaded=False)
    started=time.monotonic(); write(output/'progress.json',report)
    try:
        import numpy as np
        import torch
        import transformers
        import peft
        from peft import LoraConfig,PeftModel,get_peft_model
        from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
        require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1', 'unreviewed runtime versions')
        require(torch.cuda.is_available(),'registered CUDA full training required')
        random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])
        torch.cuda.set_device(0); torch.cuda.init(); torch.cuda.manual_seed_all(config['seed'])
        import decord
        tc=load_helper(contract['bound']['temporal_common'],'full_frozen_temporal_common')
        require(tc.MAX_FRAMES==64 and tc.MAX_PIXELS==131072,'processor recipe changed')
        report['environment']=dict(python=sys.executable,torch=torch.__version__,transformers=transformers.__version__,
                                  peft=peft.__version__,decord=decord.__version__)
        torch.cuda.reset_peak_memory_stats()
        base=Qwen3VLForConditionalGeneration.from_pretrained(config['model_dir'],revision=REVISION,
            local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},
            low_cpu_mem_usage=True,attn_implementation='sdpa')
        for parameter in base.parameters(): parameter.requires_grad_(False)
        base.config.use_cache=False
        targets=language_target_names([name for name,module in base.named_modules() if isinstance(module,torch.nn.Linear)],
                                     base.config.text_config.num_hidden_layers)
        model=get_peft_model(base,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,bias='none',
            target_modules=targets,modules_to_save=None,task_type='CAUSAL_LM'))
        trainable=[(name,p) for name,p in unique_parameters(model) if p.requires_grad]
        validate_trainable_names([name for name,_ in trainable])
        require(not any('modules_to_save' in name for name,_ in model.named_parameters()),'unapproved parameter copies')
        inventory=dict(base=sum(p.numel() for name,p in unique_parameters(model) if 'lora_' not in name),
                       lora=sum(p.numel() for name,p in unique_parameters(model) if 'lora_' in name))
        require(inventory==dict(base=BASE_PARAMS,lora=LORA_PARAMS) and TOTAL_PARAMS<=9_000_000_000,
                'actual full B parameter inventory changed')
        report.update(parameter_inventory={**inventory,'total':TOTAL_PARAMS},exact_language_targets=targets,
                      head_added=False,modules_to_save=None)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        model.train()
        for name,module in model.named_modules():
            if name.endswith('.visual'): module.eval()
        frozen_before=canonical_frozen_hash(model,torch)
        report['freeze_evidence']=dict(before_training=frozen_before)
        write(output/'progress.json',report)
        previous_lora={name:p.detach().cpu().clone() for name,p in trainable}
        processor=AutoProcessor.from_pretrained(config['model_dir'],revision=REVISION,local_files_only=True,
                                                min_pixels=131072,max_pixels=131072)
        optimizer=torch.optim.AdamW([p for _,p in trainable],lr=config['lr'],weight_decay=0.0,
                                   betas=tuple(config['adamw_betas']),eps=config['adamw_eps'])
        source_stats={path:(Path(path).stat().st_size,Path(path).stat().st_mtime_ns) for path in contract['sources']}
        with (output/'example_evidence.jsonl').open('x',encoding='utf-8') as evidence_stream:
            for step,batch in enumerate(contract['batches'],1):
                optimizer.zero_grad(set_to_none=True)
                step_losses=[]
                for epoch,index in batch:
                    require(time.monotonic()-started<=config['max_wall_seconds'],'registered full training wall-time exceeded')
                    row=contract['rows'][index]; stat=Path(row['source_path']).stat()
                    require((stat.st_size,stat.st_mtime_ns)==source_stats[row['source_path']], 'training media changed')
                    encoded,keep,evidence=build_example(processor,row,config,tc,torch,np,decord)
                    encoded={key:value.to('cuda:0') for key,value in encoded.items()}
                    result=model(**encoded,logits_to_keep=keep)
                    require(result.loss is not None and bool(torch.isfinite(result.loss)), 'nonfinite/missing CE loss')
                    (result.loss/len(batch)).backward()
                    value=float(result.loss.detach().cpu()); step_losses.append(value)
                    report['effective_batches']+=1; report['epoch_effective_counts'][str(epoch)]+=1
                    evidence.update(epoch=epoch,optimizer_step=step,effective_batch=report['effective_batches'],
                                    accumulation_denominator=len(batch),loss=value)
                    evidence_stream.write(json.dumps(evidence,ensure_ascii=False)+'\n'); evidence_stream.flush()
                    # Persist genuine completed backward counts, not a guessed PID-derived progress.
                    report.update(last_window_id=row['window_id'],wall_seconds=time.monotonic()-started)
                    write(output/'progress.json',report)
                    del result,encoded
                gradients=gradient_evidence(trainable,torch,step)
                norm=torch.nn.utils.clip_grad_norm_([p for _,p in trainable],1.0)
                require(bool(torch.isfinite(norm)) and float(norm)>0,'invalid connected LoRA gradient')
                optimizer.step()
                current={name:p.detach().cpu().clone() for name,p in trainable}
                changed=sum(not torch.equal(current[name],previous_lora[name]) for name in current)
                require(changed>0,'LoRA unchanged after optimizer step')
                previous_lora=current; report['optimizer_steps']=step
                item=dict(optimizer_step=step,effective_batches=report['effective_batches'],
                    accumulated_batches=len(batch),mean_loss=sum(step_losses)/len(step_losses),
                    gradient_norm=float(norm),changed_lora_tensors=changed,lora_gradient_evidence=gradients)
                report['updates'].append(item); write(output/'progress.json',report)
                print(json.dumps(item),flush=True)
        require(report['effective_batches']==3620 and report['optimizer_steps']==227 and
                set(report['epoch_effective_counts'].values())=={724},'incomplete five epochs')
        frozen_after=canonical_frozen_hash(model,torch)
        report['freeze_evidence']['after_training']=frozen_after
        require(frozen_before==frozen_after,'frozen base/vision parameter bytes changed')
        adapter=output/'adapter'; model.save_pretrained(str(adapter),safe_serialization=True)
        saved=json.loads((adapter/'adapter_config.json').read_text())
        require(saved['r']==16 and saved['lora_alpha']==32 and saved['lora_dropout']==.05 and
                saved['bias']=='none' and saved['modules_to_save'] is None,'saved scalar recipe changed')
        # PEFT may minimize complete names to suffixes: verify actual modules and tensor bytes.
        trained={name:p.detach().cpu().clone() for name,p in trainable}
        del optimizer,previous_lora,current
        reloaded=PeftModel.from_pretrained(model.unload(),str(adapter),is_trainable=False)
        actual_targets={name.removeprefix('base_model.model.') for name,module in reloaded.named_modules()
                        if hasattr(module,'lora_A') and 'default' in module.lora_A}
        actual={name:p.detach().cpu() for name,p in unique_parameters(reloaded) if 'lora_' in name}
        require(actual_targets==set(targets) and len(actual_targets)==144 and len(actual)==288,
                'saved target compression changed actual language/vision modules')
        require(set(actual)==set(trained) and all(torch.equal(actual[name],trained[name]) and
                actual[name].dtype==trained[name].dtype for name in actual),'adapter reload tensor bytes differ')
        frozen_reload=canonical_frozen_hash(reloaded,torch)
        with reloaded.disable_adapter(): frozen_off=canonical_frozen_hash(reloaded,torch)
        require(frozen_reload==frozen_off==frozen_before,'reloaded/adapter-off base bytes changed')
        report['freeze_evidence'].update(after_reload=frozen_reload,adapter_off=frozen_off)
        for path,digest in contract['sources'].items(): require(sha256(path)==digest,'source bytes changed during full training')
        verify_lock(contract['lock_path'],contract['lock_sha256'])
        require(sha256(config_path)==contract['config_sha256'] and
                sha256(admission_path)==contract['admission_sha256'],'full run authority changed')
        report.update(status='PASS_FULL_INTERVAL_SFT_TRAINING_ENGINEERING',full_training_completed=True,
            base_frozen=True,vision_frozen=True,adapter_reload_succeeded=True,
            adapter_model_sha256=sha256(adapter/'adapter_model.safetensors'),
            peak_memory_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            loss_finite=all(math.isfinite(item['mean_loss']) for item in report['updates']),
            quality_evaluation_pending=True,dev_evaluated=False,confirm_evaluated=False,test_inference_started=False)
    except Exception as exc:
        report.update(status='STOP_FULL_INTERVAL_SFT',failure_type=type(exc).__name__,failure=str(exc),
                      traceback=traceback.format_exc())
    report.update(wall_seconds=time.monotonic()-started,checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    with (output/'train_report.json').open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    write(output/'progress.json',report)
    print(json.dumps(dict(status=report['status'],optimizer_steps=report['optimizer_steps'],
                         effective_batches=report['effective_batches'])),flush=True)
    return 0 if report['status'].startswith('PASS_') else 4


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True); parser.add_argument('--admission',required=True)
    parser.add_argument('--lock',required=True); parser.add_argument('--expected-lock',required=True)
    parser.add_argument('--check-only',action='store_true'); args=parser.parse_args()
    try: contract=admit(args.config,args.admission,args.lock,args.expected_lock)
    except Exception as exc:
        print(json.dumps(dict(status='STOP_BEFORE_RUNTIME_IMPORTS',failure=type(exc).__name__+': '+str(exc))),flush=True)
        return 3
    if args.check_only:
        print(json.dumps(dict(status='PASS_FULL_AUTHORITY_SOURCE_BYTE_CONTRACT',windows=len(contract['rows']),
            parents=len(contract['sources']),epochs=5,updates=227,effective_batches=3620,training_started=False)),flush=True)
        return 0
    return execute(contract,args.config,args.admission)


if __name__=='__main__': raise SystemExit(main())
