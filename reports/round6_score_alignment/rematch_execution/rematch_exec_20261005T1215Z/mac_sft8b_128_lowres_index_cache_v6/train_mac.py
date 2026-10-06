"""Mac-only 128-frame B fork of frozen full trainer; real probe precedes full run."""
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import random
import resource
import sys
import time
import traceback

from mac_contract import admit, verify_lock, SCOPE, verify_live_gpu_reservation
from sft_contract import (require, sha256, BASE_PARAMS, LORA_PARAMS, TOTAL_PARAMS, REVISION,
    language_target_names, validate_trainable_names)
from train_sft import unique_parameters, gradient_evidence
from mac_inputs import build_example, frozen_prompt
from hash_helpers import canonical_frozen_hash


def write(path, value):
    path=Path(path)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temp.replace(path)

def sample_memory(report,torch,stage):
    driver=torch.mps.driver_allocated_memory()/2**20
    report['peak_mps_driver_mib']=max(report.get('peak_mps_driver_mib',0),driver)
    report['memory_last_sample']=dict(stage=stage,allocated_mib=torch.mps.current_allocated_memory()/2**20,
        driver_mib=driver,rss_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        recommended_max_memory_bytes=torch.mps.recommended_max_memory())


def execute(contract, config_path, admission_path):
    verify_live_gpu_reservation()
    config=contract['config']; output=Path(config['out_dir']); output.mkdir(parents=True,exist_ok=True)
    report=dict(status='RUNNING_MAC_'+config['phase'].upper()+'_INTERVAL_SFT',scope=SCOPE,quality_claim=False,
        full_training_completed=False,formal_c_bce_admitted=False,negative_targets_created=False,
        config_sha256=contract['config_sha256'],admission_sha256=contract['admission_sha256'],
        source_lock_sha256=contract['lock_sha256'],train_manifest_sha256=config['train_manifest']['sha256'],
        parents=len({row['parent_sample_id'] for row in contract['rows']}),source_groups=len({row['youtube_id'] for row in contract['rows']}),windows=len(contract['rows']),epochs=config['epochs'],optimizer_steps=0,effective_batches=0,
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
        require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1' and torch.__version__=='2.5.1',
                'unreviewed runtime versions')
        require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK','0')=='0','implicit CPU fallback is not admitted')
        require(torch.backends.mps.is_available(),'registered MPS training required')
        random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])
        torch.mps.manual_seed(config['seed'])
        # Small CPU/MPS equivalence checks are part of this registered probe's charged wall time.
        import unittest
        import test_deepstack
        checked=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test_deepstack))
        require(checked.wasSuccessful() and checked.testsRun==3,'DeepStack forward/backward equivalence failed')
        report['deepstack_equivalence_tests']=dict(tests=3,failures=0,errors=0,
            cpu_bf16_and_fp16=True,mps_bf16=True,forward_and_gradient_bitwise_equal=True)
        random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])
        torch.mps.manual_seed(config['seed'])
        report['initialization_seed_restored_after_tests']=config['seed']
        decord=None  # New sequential PyAV input path.
        tc=frozen_prompt(contract['bound']['temporal_common'])
        require(tc.MAX_FRAMES==128 and tc.MAX_PIXELS==32768,'processor recipe changed')
        report['environment']=dict(python=sys.executable,torch=torch.__version__,transformers=transformers.__version__,
                                  peft=peft.__version__,av=__import__('av').__version__)
        report['peak_mps_driver_mib']=torch.mps.driver_allocated_memory()/2**20
        report['mps_recommended_max_memory_bytes']=torch.mps.recommended_max_memory()
        base=Qwen3VLForConditionalGeneration.from_pretrained(config['model_dir'],revision=REVISION,
            local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'mps'},
            low_cpu_mem_usage=True,attn_implementation='sdpa')
        for parameter in base.parameters(): parameter.requires_grad_(False)
        base.config.use_cache=False
        from mps_deepstack import install
        require(config['precision']=='bf16' and config['mps_deepstack_indexing']=='FP32_INDEX_ADD_CAST_BACK_BF16',
                'DeepStack workaround protocol changed')
        report['deepstack_workaround']=install(base,torch)
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
        sample_memory(report,torch,'after_base_load_and_frozen_hash')
        write(output/'progress.json',report)
        previous_lora={name:p.detach().cpu().clone() for name,p in trainable}
        processor=AutoProcessor.from_pretrained(config['model_dir'],revision=REVISION,local_files_only=True,
                                                min_pixels=32768,max_pixels=32768)
        optimizer=torch.optim.AdamW([p for _,p in trainable],lr=config['lr'],weight_decay=0.0,
                                   betas=tuple(config['adamw_betas']),eps=config['adamw_eps'])
        source_stats={path:(Path(path).stat().st_size,Path(path).stat().st_mtime_ns) for path in contract['sources']}
        with (output/'example_evidence.jsonl').open('x',encoding='utf-8') as evidence_stream:
            for step,batch in enumerate(contract['batches'],1):
                optimizer.zero_grad(set_to_none=True)
                step_losses=[]
                for epoch,index in batch:
                    require(time.monotonic()-started<=config['max_wall_seconds'],'registered full training wall-time exceeded')
                    row=contract['rows'][index]; runtime_source=contract['source_map'][row['source_path']]; stat=Path(runtime_source).stat()
                    require((stat.st_size,stat.st_mtime_ns)==source_stats[runtime_source], 'training media changed')
                    encoded,keep,evidence=build_example(processor,row,config,tc,torch,np,decord)
                    encoded={key:value.to('mps') for key,value in encoded.items()}
                    report.update(current_sequence_length=int(encoded['input_ids'].shape[1]),
                                  current_window_id=row['window_id'],wall_seconds=time.monotonic()-started)
                    sample_memory(report,torch,'before_forward')
                    write(output/'progress.json',report)
                    write(output/'current_example.json',dict(window_id=row['window_id'],
                        expanded_sequence_length=evidence['expanded_sequence_length'],
                        sampled_frames=evidence['clip_identity']['n_sampled'],
                        video_grid_thw=encoded['video_grid_thw'].detach().cpu().tolist()))
                    result=model(**encoded,logits_to_keep=keep)
                    sample_memory(report,torch,'after_forward')
                    require(result.loss is not None and bool(torch.isfinite(result.loss)), 'nonfinite/missing CE loss')
                    (result.loss/len(batch)).backward()
                    sample_memory(report,torch,'after_backward')
                    value=float(result.loss.detach().cpu()); step_losses.append(value)
                    report['effective_batches']+=1; report['epoch_effective_counts'][str(epoch)]+=1
                    evidence.update(epoch=epoch,optimizer_step=step,effective_batch=report['effective_batches'],
                                    accumulation_denominator=len(batch),loss=value)
                    evidence_stream.write(json.dumps(evidence,ensure_ascii=False)+'\n'); evidence_stream.flush()
                    # Persist genuine completed backward counts, not a guessed PID-derived progress.
                    report.update(last_window_id=row['window_id'],wall_seconds=time.monotonic()-started,peak_mps_driver_mib=max(report['peak_mps_driver_mib'],torch.mps.driver_allocated_memory()/2**20))
                    write(output/'progress.json',report)
                    del result,encoded
                    torch.mps.synchronize();torch.mps.empty_cache()
                    sample_memory(report,torch,'after_microbatch_cache_release')
                    report['cache_release_count']=report.get('cache_release_count',0)+1
                    write(output/'progress.json',report)
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
        require(report['effective_batches']==config['expected_effective_batches'] and report['optimizer_steps']==config['expected_optimizer_steps'] and
                (config['phase']=='probe' or set(report['epoch_effective_counts'].values())=={724}),'incomplete five epochs')
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
        report.update(status=('PASS_MAC_8B_128_PROBE' if config['phase']=='probe' else 'PASS_MAC_FULL_INTERVAL_SFT_TRAINING_ENGINEERING'),full_training_completed=config['phase']=='full',
            base_frozen=True,vision_frozen=True,adapter_reload_succeeded=True,
            adapter_model_sha256=sha256(adapter/'adapter_model.safetensors'),
            peak_memory_allocated_mib=report['peak_mps_driver_mib'],
            loss_finite=all(math.isfinite(item['mean_loss']) for item in report['updates']),
            quality_evaluation_pending=True,dev_evaluated=False,confirm_evaluated=False,test_inference_started=False)
    except Exception as exc:
        report.update(status='STOP_FULL_INTERVAL_SFT',failure_type=type(exc).__name__,failure=str(exc),
                      traceback=traceback.format_exc())
        if 'torch' in locals() and torch.backends.mps.is_available():
            try:sample_memory(report,torch,'failure')
            except Exception as memory_error:report['memory_sampling_failure']=str(memory_error)
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
    parser.add_argument('--phase',choices=['probe','full'],required=True)
    parser.add_argument('--check-only',action='store_true'); args=parser.parse_args()
    try: contract=admit(args.config,args.admission,args.lock,args.expected_lock,args.phase)
    except Exception as exc:
        print(json.dumps(dict(status='STOP_BEFORE_RUNTIME_IMPORTS',failure=type(exc).__name__+': '+str(exc))),flush=True)
        return 3
    if args.check_only:
        print(json.dumps(dict(status='PASS_FULL_AUTHORITY_SOURCE_BYTE_CONTRACT',windows=len(contract['rows']),
            parents=len(contract['sources']),epochs=5,updates=contract['config']['expected_optimizer_steps'],effective_batches=contract['config']['expected_effective_batches'],training_started=False)),flush=True)
        return 0
    return execute(contract,args.config,args.admission)


if __name__=='__main__': raise SystemExit(main())
