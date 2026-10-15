"""One owned sequential pilot: two adapters and held-out matched-base evaluation."""
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve().parent
ROOT=Path('/home/inspur/aic_video_work')
DATA=ROOT/'datasets/qwen8b_annotation_20261009_v2'
PY=ROOT/'env/qwen3vl_isolated_20260910/bin/python'
MODEL=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/models/Qwen3-VL-8B-Instruct'
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
RUNNER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def write(name,value):
    p=HERE/name;t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(value,indent=2));t.replace(p)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def gpu_job(name,command,outputs):
    job='aic_ANNOTV2_'+name+'_03'
    assert not any(p.exists() for p in outputs),'Never repeat a completed or partial output'
    write('state.json',{'utc':utc(),'stage':'RUNNING_'+name.upper(),'job':job,'command':command})
    cmd=[str(PY),'-B',str(RUNNER),'--name',job,'--max-seconds','7200',
         '--planned-output-bytes',str(1<<30),'--capacity-reason',
         'New approved 8B annotation pilot: immutable selected PNGs, separate LoRA output/checkpoint and fixed held-out generation; live shared lock and actual remaining capacity',
         '--',*command]
    with (HERE/(name+'.runner.log')).open('x') as f:
        code=subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'USE_TF':'0'})
    resource_path=RUN/'controller'/f'{job}.resource.json'
    resource=json.loads(resource_path.read_text()) if resource_path.exists() else None
    if code or not resource or resource['status']!='completed':
        raise RuntimeError({'job':job,'exit_code':code,'resource':resource,'log':str(HERE/(name+'.runner.log'))})
    ledger=[json.loads(s) for s in (ROOT/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
    matches=[x for x in ledger if x['name']==job]
    assert len(matches)==1 and matches[0]==resource
    write(name+'.resource.json',resource)
    return resource
def main():
    assert socket.gethostname()=='inspur-NP5570M5'
    lock=(HERE/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (HERE/'started.json').exists(),'Never relaunch this run'
    assert sha(RUNNER)=='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec'
    assert sha(DATA/'training_v2/selected_manifest.json')=='adfe72e2318ec11913175fefb2ba987393d8f442a097efc16b2474a112b94ba1'
    readiness=json.loads((DATA/'linux_readiness_completion.json').read_text())
    assert readiness['status']=='PASS_LINUX_UPLOAD_SELECTED_HASHES_AND_ALL_REAL_IMAGE_CPU_PREFLIGHTS'
    write('started.json',{'utc':utc(),'pid':os.getpid(),'user_authorization':'开始安排任务，进行微调',
                         'dataset':str(DATA),'separate_adapters':True,'production_change':False})
    write('state.json',{'utc':utc(),'stage':'BINDING_MODEL_AND_CODE_IDENTITY'})
    model_files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in MODEL.glob('*.safetensors')}
    assert len(model_files)==4
    write('source_binding.json',{'utc':utc(),'model_files':model_files,'model_config_sha256':sha(MODEL/'config.json'),
        'selected_manifest_sha256':sha(DATA/'training_v2/selected_manifest.json'),
        'wrapper_sha256':{p.name:sha(p) for p in HERE.glob('*.py')},
        'gpu_runner_sha256':sha(RUNNER),'disk_free_before':shutil.disk_usage(ROOT).free})
    receipts={}
    recovered=ROOT/'runs/annotation_finetune_20261009_v2/crop_train'
    recovery=json.loads((HERE/'crop_recovery_acceptance.json').read_text())
    assert recovery['status']=='PASS_RECOVER_ACTUAL_COMPLETED_CROP_TRAINING_NO_RETRAIN'
    assert sha(recovered/'adapter/adapter_model.safetensors')==recovery['adapter_sha256']
    train_outputs={'crop':recovered,'temporal':HERE/'temporal_train'}
    receipts['crop_train']=recovery
    for task,config in [('crop','crop'),('temporal','temporal_fixed')]:
        if task=='crop':continue
        out=train_outputs[task]
        receipts[task+'_train']=gpu_job(task+'_train',[str(PY),'-B',str(HERE/'observed_train.py'),
            '--dataset-root',str(DATA),'--config',str(DATA/f'training_v2/configs/{config}.json'),
            '--model',str(MODEL),'--output',str(out)],[out])
        acceptance=json.loads((out/'training_acceptance.json').read_text())
        assert acceptance['status']=='PASS_REAL_LORA_TRAINING_FINITE_LOSS_GRADIENTS_AND_WEIGHT_CHANGES'
    metrics={}
    for task,config in [('crop','crop'),('temporal','temporal_fixed')]:
        recipe=json.loads((DATA/f'training_v2/configs/{config}.json').read_text())
        targets=DATA/recipe['validation_file']
        for condition in ('adapter','base'):
            prediction=HERE/f'{task}_{condition}_predictions.jsonl'
            command=[str(PY),'-B',str(HERE/'observed_predict.py'),*(['--base-comparison'] if condition=='base' else []),
                     '--dataset-root',str(DATA),'--data',str(targets),'--model',str(MODEL),
                     '--adapter',str(train_outputs[task]/'adapter'),
                     '--output',str(prediction)]
            receipts[task+'_'+condition]=gpu_job(task+'_'+condition,command,[prediction])
            report=HERE/f'{task}_{condition}_evaluation.json'
            subprocess.run([str(PY),'-B',str(DATA/'training_v2/evaluate_predictions.py'),
                            '--targets',str(targets),'--predictions',str(prediction),'--output',str(report)],check=True)
            metrics[task+'_'+condition]=json.loads(report.read_text())
    artifacts={p.relative_to(HERE).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}
               for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.safetensors','.json','.jsonl')
               and p.name not in ('state.json','completion.json')}
    completion={'utc':utc(),'status':'PASS_TWO_REAL_LORA_PILOTS_AND_HELD_OUT_GENERATION_EVALUATION',
                'metrics':metrics,'resources':receipts,'artifacts':artifacts,'train_outputs':{k:str(v) for k,v in train_outputs.items()},'crop_completed_output_recovered_without_retraining':True,
                'official_score':None,'production_adapter_replaced':False,
                'temporal_target':'TVSum sampled-frame human importance; not semantic action boundaries',
                'crop_reference':'Reviewed weak labels; not independent human gold'}
    write('completion.json',completion)
    write('state.json',{'utc':utc(),'stage':completion['status'],'completed':True})
if __name__=='__main__':
    try:main()
    except BaseException:
        write('failure.json',{'utc':utc(),'traceback':traceback.format_exc(),'status':'FAILED_PRESERVE_OUTPUTS'})
        write('state.json',{'utc':utc(),'stage':'FAILED_PRESERVE_OUTPUTS'})
        raise
