"""Independent authorized 3-epoch run and same-input constrained comparisons."""
import datetime as dt,fcntl,hashlib,json,os,socket,subprocess,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=Path('/home/inspur/aic_video_work')
DATA=ROOT/'datasets/qwen8b_annotation_20261009_v2';PY=ROOT/'env/qwen3vl_isolated_20260910/bin/python'
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
MODEL=RUN/'models/Qwen3-VL-8B-Instruct';RUNNER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(n,v):
    p=H/n;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2));t.replace(p)
def job(name,args):
    name='aic_ANNITER10_'+name+'_01';save('state.json',{'utc':utc(),'stage':name,'command':list(map(str,args))})
    cmd=[str(PY),'-B',str(RUNNER),'--name',name,'--max-seconds','14400','--planned-output-bytes',str(2<<30),
         '--capacity-reason','User authorized independent annotation iteration; existing immutable PNGs/model, measured pilot peaks and current shared conflicts; separate adapter plus exact full validation outputs',
         '--',str(PY),'-B',*map(str,args)]
    with (H/(name+'.log')).open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'USE_TF':'0'})
    path=RUN/'controller'/(name+'.resource.json');receipt=json.loads(path.read_text())
    ledger=[json.loads(s) for s in (ROOT/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
    matches=[v for v in ledger if v['name']==name]
    assert len(matches)==1 and matches[0]==receipt
    save(name+'.resource.json',receipt)
    if r.returncode or receipt['status']!='completed':raise RuntimeError({'job':name,'receipt':receipt})
def main():
    assert socket.gethostname()=='inspur-NP5570M5'
    lock=(H/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (H/'started.json').exists()
    assert sha(RUNNER)=='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec'
    assert sha(DATA/'training_v2/selected_manifest.json')=='adfe72e2318ec11913175fefb2ba987393d8f442a097efc16b2474a112b94ba1'
    save('started.json',{'utc':utc(),'pid':os.getpid(),'authorization':'主控代替Pro，深度调研讨论，执行到可提交ZIP；保留生产，质量优先',
                       'source_sha':{p.name:sha(p) for p in H.glob('*.py')},'protocol_sha256':sha(H/'PLAN.md')})
    out=H/'train';assert not out.exists()
    job('train',[H/'observed_train.py','--dataset-root',DATA,'--config',H/'temporal_config.json','--model',MODEL,'--output',out])
    accept=json.loads((out/'training_acceptance.json').read_text());assert accept['result']['global_step']>=200
    targets=DATA/'training_v2/data/temporal_fixed_validation.jsonl'
    arms={'new':out/'adapter','base':None,'pilot':ROOT/'runs/annotation_finetune_20261009_v3/temporal_train/adapter',
          'production_B':RUN/'temporal_sft8b_full_v1/train_01/adapter'}
    for arm,adapter in arms.items():
        dest=H/(arm+'_predictions.jsonl');assert not dest.exists()
        args=[H/'predict_scores.py','--root',DATA,'--model',MODEL,'--data',targets,'--output',dest]
        if adapter:args+=['--adapter',adapter]
        job(arm,args)
    job('vision',[H/'vision_dependency.py','--root',DATA,'--model',MODEL,'--adapter',out/'adapter','--output',H/'vision_dependency.json'])
    save('completion.json',{'utc':utc(),'status':'REAL_TRAINING_FULL_GENERATION_COMPLETE_QUALITY_PENDING',
         'adapter_sha256':sha(out/'adapter/adapter_model.safetensors'),'optimizer_steps':accept['result']['global_step'],
         'production_replaced':False,'new_contest_package':False})
    save('state.json',{'utc':utc(),'stage':'COMPLETE_AWAIT_INDEPENDENT_CPU_QUALITY'})
if __name__=='__main__':
    try:main()
    except BaseException:
        save('failure.json',{'utc':utc(),'traceback':traceback.format_exc()});save('state.json',{'utc':utc(),'stage':'FAILED_PRESERVE_OUTPUTS'});raise
