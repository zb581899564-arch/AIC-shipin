"""Independent paired evaluation and artifact verification; no model calls."""
import hashlib
import json
import math
import sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from safetensors.torch import load_file

ROOT=Path('/home/inspur/aic_video_work')
R=ROOT/'runs/annotation_finetune_20261009_v3'
DATA=ROOT/'datasets/qwen8b_annotation_20261009_v2'
sys.path.insert(0,str(DATA/'training_v2'))
from sft_contract import decode_output
from evaluate_predictions import rank_correlation
assert (R/'completion.json').exists()
completion=json.loads((R/'completion.json').read_text())
assert completion['status']=='PASS_TWO_REAL_LORA_PILOTS_AND_HELD_OUT_GENERATION_EVALUATION'
def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
labels=rows(DATA/'training_v2/data/temporal_fixed_validation.jsonl')
train=rows(DATA/'training_v2/data/temporal_fixed_train.jsonl')
all_train=[v/20 for r in train for v in json.loads(r['messages'][1]['content'])['scores_x20']]
constant=float(np.mean(all_train))
conditions={c:{r['id']:r for r in rows(R/f'temporal_{c}_predictions.jsonl')} for c in ('adapter','base')}
paired_ids={r['id'] for r in labels if all(conditions[c][r['id']]['valid'] for c in conditions)}
assert paired_ids
summary={}
for c in conditions:
    errors=[];reference=[];groups={}
    for r in labels:
        if r['id'] not in paired_ids:continue
        gold=json.loads(r['messages'][1]['content'])['scores_x20']
        predicted=decode_output(conditions[c][r['id']]['answer'],r['task'],image_count=len(r['images']))['scores_x20']
        errors.extend((np.array(predicted)-np.array(gold))/20)
        reference.extend(np.array(gold)/20-constant)
        p,g=groups.setdefault(r['source_group'],([],[]));p.extend(predicted);g.extend(gold)
    summary[c]={'matched_rows':len(paired_ids),'matched_frames':len(errors),
                'mae':float(np.mean(np.abs(errors))),'rmse':float(np.sqrt(np.mean(np.square(errors)))),
                'constant_train_mean_mae_on_same_frames':float(np.mean(np.abs(reference))),
                'per_source_spearman':{s:rank_correlation(p,g) for s,(p,g) in groups.items()}}
artifact_check={}
for task in ('crop','temporal'):
    output=Path(completion['train_outputs'][task])
    path=output/'adapter/adapter_model.safetensors'
    values=load_file(str(path),device='cpu')
    state=json.loads((output/'trainer/trainer_state.json').read_text())
    assert state['global_step']==(12 if task=='crop' else 20)
    checkpoint=load_file(str(output/f"trainer/checkpoint-{state['global_step']}/adapter_model.safetensors"),device='cpu')
    assert len(values)==288 and set(values)==set(checkpoint)
    assert all(torch.equal(t,checkpoint[n]) and bool(torch.isfinite(t).all()) for n,t in values.items())
    assert all(bool((t!=0).any()) for n,t in values.items() if 'lora_B' in n)
    artifact_check[task]={'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),
                          'optimizer_steps':state['global_step'],'lora_tensor_count':len(values),
                          'checkpoint_final_tensors_equal':True}
ledger=rows(ROOT/'improvement_round1/gpu_ledger.jsonl')
own=[x for x in ledger if x['name'].startswith('aic_ANNOTV2_')]
assert len(own)==7 and len({x['name'] for x in own})==len(own)
assert all(math.isfinite(x['charged_seconds']) and x['charged_seconds']>0 for x in own)
assert not (ROOT/'improvement_round1/active_gpu_job.json').exists()
receipt={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_ARTIFACTS_PAIRED_COMPARISON_AND_UNIQUE_LEDGER',
 'metrics':completion['metrics'],'matched_temporal_comparison':summary,'constant_train_mean':constant,
 'adapter_artifacts':artifact_check,'gpu_terminal_jobs':own,'new_campaign_charged_seconds':sum(x['charged_seconds'] for x in own),
 'failed_attempts_preserved':sum(x['status']=='failed' for x in own),'new_optimizer_steps':32,
 'production_model_replaced':False,'official_score':None,'CUDA_initialized':torch.cuda.is_initialized(),
 'new_8b_model_calls':0,'new_optimizer_updates_in_this_audit':0}
with (R/'independent_final_audit.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
