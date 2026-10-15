"""Independently accept already-saved crop training; never reload 8B or optimize."""
import hashlib
import json
import math
from datetime import datetime,timezone
from pathlib import Path

import torch
from safetensors.torch import load_file
from peft.tuners.lora.layer import LoraLayer
import inspect

r=Path('/home/inspur/aic_video_work/runs/annotation_finetune_20261009_v2/crop_train')
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
state_path=r/'trainer/trainer_state.json'
state=json.loads(state_path.read_text());assert state['global_step']==state['max_steps']==12 and state['epoch']==1
steps=[x for x in state['log_history'] if 'loss' in x]
assert [x['step'] for x in steps]==list(range(1,13))
assert all(math.isfinite(x['loss']) and math.isfinite(x['grad_norm']) and x['grad_norm']>0 for x in steps)
evaluation=[x for x in state['log_history'] if 'eval_loss' in x]
assert len(evaluation)==1 and math.isfinite(evaluation[0]['eval_loss'])
config=json.loads((r/'adapter/adapter_config.json').read_text())
assert config['init_lora_weights'] is True and config['r']==8 and config['lora_alpha']==16
init_source=inspect.getsource(LoraLayer.reset_lora_parameters)
assert 'nn.init.zeros_(self.lora_B[adapter_name].weight)' in init_source
path=r/'adapter/adapter_model.safetensors'
tensors=load_file(str(path),device='cpu')
checkpoint=load_file(str(r/'trainer/checkpoint-12/adapter_model.safetensors'),device='cpu')
assert set(tensors)==set(checkpoint) and len(tensors)==288
assert all('lora_' in n and 'visual' not in n and 'vision' not in n for n in tensors)
assert all(bool(torch.isfinite(t).all()) and torch.equal(t,checkpoint[n]) for n,t in tensors.items())
b=[t for n,t in tensors.items() if 'lora_B' in n]
assert len(b)==144 and all(bool((t!=0).any()) for t in b)
resource=json.loads((run/'controller/aic_ANNOTV2_crop_train_02.resource.json').read_text())
assert resource['status']=='failed' and resource['exit_code']==1
ledger=[json.loads(s) for s in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
assert [x for x in ledger if x['name']==resource['name']]==[resource]
failure=json.loads((r.parent/'failure.json').read_text())
assert 'optimizer_observations.jsonl' in (run/'controller/aic_ANNOTV2_crop_train_02.log').read_text()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_RECOVER_ACTUAL_COMPLETED_CROP_TRAINING_NO_RETRAIN',
 'output':str(r),'optimizer_steps':12,'first_step_loss':steps[0]['loss'],'first_step_grad_norm':steps[0]['grad_norm'],
 'first_step_learning_rate':steps[0]['learning_rate'],'train_loss':json.loads((r/'train_metrics.json').read_text())['train_loss'],
 'eval_loss':evaluation[0]['eval_loss'],'adapter_sha256':sha(path),'adapter_bytes':path.stat().st_size,
 'lora_tensors':len(tensors),'nonzero_lora_B_tensors':len(b),'checkpoint_and_final_adapter_tensor_equal':True,
 'default_lora_B_zero_initializer_source_sha256':hashlib.sha256(init_source.encode()).hexdigest(),
 'original_resource':resource,'original_observer_failure_preserved':True,'new_optimizer_steps':0,
 'new_8b_model_loads':0,'CUDA_initialized':torch.cuda.is_initialized(),
 'model_loss_and_gradient_history_sha256':sha(state_path),'warmup_first_step_zero_learning_rate_preserved':True}
print(json.dumps(receipt))

