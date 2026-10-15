"""Run the transferred release's real-image preflights; never start training."""
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work')
DATA=ROOT/'datasets/qwen8b_annotation_20261009_v2'
PY=ROOT/'env/qwen3vl_isolated_20260910/bin/python'
MODEL=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/models/Qwen3-VL-8B-Instruct'
assert socket.gethostname()=='inspur-NP5570M5'
assert ROOT.resolve(strict=True)==ROOT and DATA.resolve(strict=True)==DATA
uploaded=json.loads((DATA/'upload_verification.json').read_text())
assert uploaded['status']=='PASS_REMOTE_ZIP_CRC_SAFE_EXTRACTION_ALL_SELECTED_FILE_HASHES'
assert uploaded['zip_sha256']=='45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c'
outputs={task:ROOT/f'runs/qwen_annotation_v2_{task}_preflight_001' for task in ('crop','temporal')}
for output in outputs.values():
    assert output.parent.resolve(strict=True)==output.parent
    assert not output.exists() and not output.is_symlink()
env=os.environ.copy()
env.update({'USE_TF':'0','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
            'CUDA_VISIBLE_DEVICES':'','HF_HOME':str(DATA/'runtime_cache/huggingface'),
            'XDG_CACHE_HOME':str(DATA/'runtime_cache'),'TOKENIZERS_PARALLELISM':'false'})
receipts={}
for task in ('crop','temporal'):
    name='crop' if task=='crop' else 'temporal_fixed'
    command=[str(PY),'-B',str(DATA/'training_v2/train_lora.py'),
             '--config',str(DATA/f'training_v2/configs/{name}.json'),'--dataset-root',str(DATA),
             '--model',str(MODEL),'--output',str(outputs[task])]
    assert '--train' not in command
    print(json.dumps({'stage':'START_REAL_IMAGE_CPU_PREFLIGHT','task':task,'weights_or_optimizer':False}),flush=True)
    log=DATA/f'linux_{task}_preflight.log'
    with log.open('x',encoding='utf-8') as out:
        p=subprocess.Popen(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in p.stdout:
            out.write(line);out.flush()
            print(line.rstrip(),flush=True)
        code=p.wait()
    assert code==0, f'{task} preflight failed; preserve log at {log}'
    receipt=json.loads((outputs[task]/'preflight.json').read_text())
    assert receipt['status']=='PASS_ALL_REAL_IMAGE_ROWS_PROCESSOR_AND_MASK_PREFLIGHT'
    assert not receipt['model_weights_loaded'] and not receipt['optimizer_started']
    expected=(181,148) if task=='crop' else (314,89)
    assert tuple(receipt['stats'][s]['rows'] for s in ('train','validation'))==expected
    receipts[task]={'output':str(outputs[task]),'receipt':receipt}
completion={'utc':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),
            'status':'PASS_LINUX_UPLOAD_SELECTED_HASHES_AND_ALL_REAL_IMAGE_CPU_PREFLIGHTS',
            'dataset':str(DATA),'zip_bytes':uploaded['zip_bytes'],'zip_sha256':uploaded['zip_sha256'],
            'manifest_sha256':uploaded['manifest_sha256'],'cpu_preflights':receipts,
            'weights_loaded':False,'gpu_started':False,'optimizer_started':False,
            'actual_8b_loss_or_optimizer_smoke_performed':False,
            'semantic_event_boundary_review_complete':False,
            'gemini_event_boundaries_used_as_targets':0,
            'training_target':'TVSum human sampled-frame importance and reviewed crop weak labels'}
with (DATA/'linux_readiness_completion.json').open('x',encoding='utf-8') as out:
    json.dump(completion,out,indent=2)
print(json.dumps(completion),flush=True)
