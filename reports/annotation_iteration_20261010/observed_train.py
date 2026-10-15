"""Observe the unchanged selected training entry; do not cache validation logits."""
import argparse
import hashlib
import json
import math
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset-root',required=True)
    p.add_argument('--config',required=True)
    p.add_argument('--model',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    output=Path(a.output)
    root=Path(a.dataset_root)
    assert not output.exists()
    import torch
    import transformers
    from transformers import TrainerCallback
    def emit(value):
        value={'utc':datetime.now(timezone.utc).isoformat(),**value}
        print(json.dumps(value),flush=True)
        with (output/'optimizer_observations.jsonl').open('a') as f:
            f.write(json.dumps(value)+'\n')
    def signature(model):
        h=hashlib.sha256();count=0
        for name,param in sorted(model.named_parameters()):
            if param.requires_grad:
                assert 'lora_' in name and 'visual' not in name and 'vision' not in name
                h.update(name.encode());h.update(param.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
                count+=param.numel()
        assert count>0
        return h.hexdigest(),count
    class Observe(TrainerCallback):
        def on_train_begin(self,args,state,control,model=None,**kwargs):
            self.initial,self.count=signature(model)
            torch.cuda.reset_peak_memory_stats()
            emit({'stage':'REAL_TRAIN_BEGIN','trainable_parameters':self.count,
                  'initial_lora_sha256':self.initial,'steps_planned':state.max_steps,
                  'prediction_loss_only':args.prediction_loss_only})
        def on_pre_optimizer_step(self,args,state,control,model=None,**kwargs):
            self.actual_step_lr=kwargs['optimizer'].param_groups[0]['lr']
            if state.global_step==0:
                total=0.0;nonzero=0
                for name,param in model.named_parameters():
                    if param.requires_grad and param.grad is not None:
                        assert bool(torch.isfinite(param.grad).all()),'Nonfinite first-step gradients'
                        norm=float(param.grad.float().norm().item())
                        total+=norm*norm;nonzero+=norm>0
                assert total>0 and nonzero>0
                emit({'stage':'FIRST_REAL_GRADIENTS','norm':math.sqrt(total),'nonzero_gradient_tensors':nonzero})
        def on_step_end(self,args,state,control,model=None,**kwargs):
            row={'stage':'REAL_OPTIMIZER_STEP','global_step':state.global_step,
                 'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                 'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
            if state.global_step<=2:
                now,count=signature(model)
                assert count==self.count
                if self.actual_step_lr>0:
                    assert now!=self.initial,'Positive-LR optimizer step did not change LoRA weights'
                row.update({'lora_changed':now!=self.initial,'actual_step_learning_rate':self.actual_step_lr,'lora_sha256':now})
            emit(row)
        def on_log(self,args,state,control,logs=None,**kwargs):
            if logs:emit({'stage':'TRAINER_LOG','global_step':state.global_step,'metrics':logs})
        def on_train_end(self,args,state,control,model=None,**kwargs):
            final,count=signature(model)
            assert final!=self.initial and state.global_step>0
            emit({'stage':'REAL_TRAIN_END','global_step':state.global_step,'final_lora_sha256':final,
                  'initial_lora_sha256':self.initial,'trainable_parameters':count,
                  'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                  'peak_reserved_bytes':torch.cuda.max_memory_reserved()})
    # accelerate 1.2.1 lacks keep_torch_compile; no compiled model is used here.
    import inspect
    from accelerate import Accelerator
    from accelerate.utils.other import is_compiled_module
    unwrap=Accelerator.unwrap_model
    if 'keep_torch_compile' not in inspect.signature(unwrap).parameters:
        def compatible_unwrap(self,model,*values,keep_torch_compile=True,**options):
            assert type(keep_torch_compile) is bool and not is_compiled_module(model)
            return unwrap(self,model,*values,**options)
        Accelerator.unwrap_model=compatible_unwrap
    original=transformers.Trainer
    class ObservedTrainer(original):
        def __init__(self,*args,**kwargs):
            kwargs['args'].prediction_loss_only=True
            emit({'stage':'OBSERVED_TRAINER_ATTACHED','validation_loss_only':True})
            callbacks=list(kwargs.pop('callbacks',[]) or [])+[Observe()]
            super().__init__(*args,callbacks=callbacks,**kwargs)
        def compute_loss(self,model,inputs,return_outputs=False,**kwargs):
            result=super().compute_loss(model,inputs,return_outputs=return_outputs,**kwargs)
            loss=result[0] if return_outputs else result
            assert bool(torch.isfinite(loss).all()),'Nonfinite model loss'
            return result
    transformers.Trainer=ObservedTrainer
    sys.path.insert(0,str(root/'training_v2'))
    sys.argv=[str(root/'training_v2/train_lora.py'),'--config',a.config,'--dataset-root',a.dataset_root,
              '--model',a.model,'--output',a.output,'--train']
    source=Path(sys.argv[0]).read_text()
    old='    from transformers import Qwen3VLForConditionalGeneration, Trainer, TrainingArguments'
    new='    from transformers import Qwen3VLForConditionalGeneration, TrainingArguments\n    Trainer = __observed_trainer'
    assert source.count(old)==1
    source=source.replace(old,new)
    exec(compile(source,sys.argv[0],'exec'),{'__name__':'__main__','__file__':sys.argv[0],'__observed_trainer':ObservedTrainer})
    assert (output/'adapter/adapter_model.safetensors').exists()
    assert (output/'train_metrics.json').exists()
    observations=[json.loads(s) for s in (output/'optimizer_observations.jsonl').read_text().splitlines()]
    assert any(x.get('stage')=='FIRST_REAL_GRADIENTS' for x in observations)
    assert any(x.get('lora_changed') is True for x in observations)
    ending=[x for x in observations if x.get('stage')=='REAL_TRAIN_END']
    assert len(ending)==1
    receipt={'status':'PASS_REAL_LORA_TRAINING_FINITE_LOSS_GRADIENTS_AND_WEIGHT_CHANGES',
             'utc':datetime.now(timezone.utc).isoformat(),'result':ending[0],
             'train_metrics':json.loads((output/'train_metrics.json').read_text()),
             'validation_loss_only':True,'production_adapter_replaced':False}
    with (output/'training_acceptance.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
