"""One final-checkpoint spatial LoRA, then held-out file development generation."""
import argparse
import json
import os
import random
import time
import traceback
from gs_common import ROOT,RUN,paths,read,save,sha,info,parse,geometry,verify_lock

def generate(model,processor,values,item,stage,stream):
    import torch
    prefix=values['input_ids'].shape[1];start=time.monotonic()
    with torch.inference_mode():
        result=model.generate(**{k:v.to('cuda:0') for k,v in values.items()},max_new_tokens=96,
                              do_sample=False,num_beams=1,use_cache=True)
    ids=result[0,prefix:].detach().cpu().tolist()
    raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
    stream.write(json.dumps({'item_id':item['item_id'],'stage':stage,'output_ids':ids,'raw':raw,
                            'input_tokens':prefix,'tensor_file_sha256':sha(item['tensor']),
                            'seconds':time.monotonic()-start},ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
    return raw

def main(confirm):
    paths()
    import numpy as np
    import torch
    from peft import LoraConfig,get_peft_model,PeftModel
    from spatial_baseline import Qwen3VL,parse_focus_norm,compute_crop_size,center_to_box
    from engine import frozen_identity
    from sft_contract import language_target_names,validate_trainable_names,verify_live_gpu_reservation
    from train_sft import fingerprint_base,gradient_evidence,unique_parameters
    verify_live_gpu_reservation();locksha=verify_lock();p=read(ROOT/'protocol.json');recipe=p['train']
    if not os.environ.get('CUDA_VISIBLE_DEVICES'): raise ValueError('actual GPU index required')
    if read(ROOT/'cpu_acceptance.json')['status']!='PASS_200_HUMAN_TRAIN_40_EVAL_REAL_CPU_INPUTS': raise ValueError('real CPU inputs required')
    if confirm and read(ROOT/'selected.json')['screen_result_sha256']!=sha(ROOT/'screen/result.json'): raise ValueError('unfrozen selection')
    role='confirm' if confirm else 'screen';out=ROOT/role;out.mkdir()
    save(out/'started.json',{'pid':os.getpid(),'lock_sha256':locksha,'labels_used_for_inference':False})
    cfg=read(RUN/'b_score_aligned_package_v4/config.json')
    random.seed(recipe['seed']);np.random.seed(recipe['seed']);torch.manual_seed(recipe['seed']);torch.cuda.manual_seed_all(recipe['seed'])
    wrapper=Qwen3VL(cfg['model_dir'],max_pixels=131072,device_map={'':'cuda:0'},attn_implementation='sdpa')
    base=wrapper.model;proc=wrapper.processor
    for parameter in base.parameters(): parameter.requires_grad_(False)
    identity=frozen_identity(base,cfg)
    if confirm:
        report=read(ROOT/'train/train_report.json')
        if sha(ROOT/'train/adapter/adapter_model.safetensors')!=report['adapter_sha256']: raise ValueError('trained adapter changed')
        model=PeftModel.from_pretrained(base,str(ROOT/'train/adapter'),is_trainable=False)
    else:
        targets=language_target_names([n for n,m in base.named_modules() if isinstance(m,torch.nn.Linear)],base.config.text_config.num_hidden_layers)
        model=get_peft_model(base,LoraConfig(r=recipe['rank'],lora_alpha=recipe['alpha'],lora_dropout=recipe['dropout'],
              bias='none',target_modules=targets,modules_to_save=None,task_type='CAUSAL_LM'))
        trainable=[(n,v) for n,v in unique_parameters(model) if v.requires_grad];validate_trainable_names([n for n,v in trainable])
        base_count=sum(v.numel() for n,v in unique_parameters(model) if 'lora_' not in n)
        lora_count=sum(v.numel() for n,v in trainable)
        pipeline=base_count+lora_count+(cfg['complete_parameters']-cfg['base_parameters'])
        if base_count!=cfg['base_parameters'] or pipeline>9000000000: raise ValueError('actual main+aux parameter count')
        save(out/'model_identity.json',{'base':identity,'spatial_lora':lora_count,'integrated_pipeline_parameters':pipeline,
                                      'shared_single_base_with_original_time_adapter':True})
        trainout=ROOT/'train';trainout.mkdir()
        before=fingerprint_base(model,torch)
        model.config.use_cache=False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        model.train()
        for n,m in model.named_modules():
            if n.endswith('.visual'): m.eval()
        optimizer=torch.optim.AdamW([v for n,v in trainable],lr=recipe['lr'],weight_decay=0.0)
        optimizer.zero_grad(set_to_none=True)
        rows=read(ROOT/'train_inputs.json');order=[];position=0;epoch=0;losses=[];steps=[];started=time.monotonic()
        with (trainout/'updates.jsonl').open('x',encoding='utf-8') as stream:
            for micro in range(recipe['steps']*recipe['grad_accum']):
                if time.monotonic()-started>recipe['max_seconds']: raise ValueError('registered training wall time')
                if position==len(order):
                    order=list(range(len(rows)));random.Random(recipe['seed']+epoch).shuffle(order);position=0;epoch+=1
                item=rows[order[position]];position+=1;proof=read(item['proof'])
                if sha(item['tensor'])!=proof['file_sha256']: raise ValueError('training tensor changed')
                values=torch.load(item['tensor'],map_location='cpu',weights_only=True)
                if info(values)!=proof['saved_tensors']: raise ValueError('training tensor identity changed')
                outputs=model(**{k:v.to('cuda:0') for k,v in values.items()},logits_to_keep=proof['assistant_mask']['logits_to_keep'])
                loss=outputs.loss
                if loss is None or not torch.isfinite(loss): raise ValueError('nonfinite CE')
                (loss/recipe['grad_accum']).backward();losses.append(float(loss.detach().cpu()))
                if (micro+1)%recipe['grad_accum']==0:
                    step=(micro+1)//recipe['grad_accum'];grads=gradient_evidence(trainable,torch,step)
                    norm=torch.nn.utils.clip_grad_norm_([v for n,v in trainable],recipe['grad_clip'])
                    if not torch.isfinite(norm) or float(norm)<=0: raise ValueError('nonzero finite gradient required')
                    optimizer.step();optimizer.zero_grad(set_to_none=True)
                    record={'step':step,'microbatches':micro+1,'mean_loss':sum(losses[-recipe['grad_accum']:])/recipe['grad_accum'],
                            'gradient_norm':float(norm),'gradient_evidence':grads}
                    steps.append(record);stream.write(json.dumps(record)+'\n');stream.flush()
                    if step%5==0: print('OPTIMIZER_STEP',step,'LOSS',record['mean_loss'],flush=True)
        model.eval();after=fingerprint_base(model,torch)
        if before!=after: raise ValueError('base/vision freeze violated')
        saved={n:v.detach().cpu().clone() for n,v in unique_parameters(model) if 'lora_' in n}
        adapter=trainout/'adapter';model.save_pretrained(str(adapter),safe_serialization=True)
        model=PeftModel.from_pretrained(model.unload(),str(adapter),is_trainable=False)
        actual={n:v.detach().cpu() for n,v in unique_parameters(model) if 'lora_' in n}
        if set(saved)!=set(actual) or any(not torch.equal(saved[n],actual[n]) for n in saved): raise ValueError('saved adapter reload changed tensors')
        save(trainout/'train_report.json',{'status':'PASS_REAL_50_UPDATES_ADAPTER_RELOAD_BASE_FROZEN','optimizer_steps':len(steps),
             'microbatches':len(losses),'train_examples':len(rows),'loss_first':losses[0],'loss_last':losses[-1],
             'base_fingerprint_before_after':before,'adapter_sha256':sha(adapter/'adapter_model.safetensors'),
             'spatial_lora_parameters':lora_count,'integrated_parameters':pipeline,'seconds':time.monotonic()-started,
             'peak_allocated_mib':torch.cuda.max_memory_allocated()/2**20,'final_step_only':True})
        del optimizer,outputs,loss;torch.cuda.empty_cache()
    model.eval()
    if not confirm: model.gradient_checkpointing_disable()
    model.config.use_cache=True
    items=[r for r in read(ROOT/'eval_inputs.json') if r['role']==role]
    oldbase={r['item_id']:r for r in [json.loads(x) for x in (ROOT.parent/'gnmc_width_iteration_20261013_v1/recovery_01/screen/predictions.jsonl').read_text().splitlines()]}
    with (out/'calls.jsonl').open('x',encoding='utf-8') as calls,(out/'predictions.jsonl').open('x',encoding='utf-8') as predictions:
        for item in items:
            proof=read(item['new_proof']);values=torch.load(item['tensor'],map_location='cpu',weights_only=True)
            if sha(item['tensor'])!=proof['file_sha256'] or info(values)!=proof['saved_tensors']: raise ValueError('eval cached tensor changed')
            baseline=oldbase[item['item_id']]['baseline_box'] if not confirm else None
            if confirm:
                oldproof=read(ROOT.parent/'gnmc_width_iteration_20261013_v1'/item['proof'])
                original=oldproof['stages']['baseline'];original_path=ROOT.parent/'gnmc_width_iteration_20261013_v1'/original['path']
                baseline_values=torch.load(original_path,map_location='cpu',weights_only=True)
                if sha(original_path)!=original['file_sha256'] or info(baseline_values)!=original['tensors']: raise ValueError('old confirmed CPU input changed')
                with model.disable_adapter(): raw=generate(model,proc,baseline_values,{**item,'tensor':str(original_path)},'original_baseline',calls)
                center=parse_focus_norm(raw,item['width'],item['height'])
                if center is None: raise ValueError('original baseline parse failed')
                cw,hf=compute_crop_size(item['width'],item['height'],16,9);baseline=center_to_box(*center,item['width'],item['height'],cw,hf)
            raw=generate(model,proc,values,item,'trained_joint',calls)
            result={'item_id':item['item_id'],'baseline_box':baseline,'reference_used_for_inference':False}
            try: result.update(status='VALID',candidate_box=geometry(parse(raw),item['width'],item['height']))
            except Exception as e: result.update(status='INVALID_PRESERVED',error=repr(e),candidate_box=None)
            predictions.write(json.dumps(result)+'\n');predictions.flush()
            print('GENERATED',role,item['item_id'],result['status'],flush=True)
    save(out/'generation_completion.json',{'status':'COMPLETE_GENERATION_NOT_QUALITY','rows':len(items),
         'calls':len(items)*(2 if confirm else 1),'predictions_sha256':sha(out/'predictions.jsonl'),
         'source_lock_sha256':locksha,'adapter_sha256':sha(ROOT/'train/adapter/adapter_model.safetensors')})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--confirm',action='store_true');args=parser.parse_args()
    try: main(args.confirm)
    except Exception as e:
        p=ROOT/('confirm_failure.json' if args.confirm else 'training_screen_failure.json')
        if not p.exists(): save(p,{'error':repr(e),'traceback':traceback.format_exc(),'preserve_raw_and_success':True})
        raise
