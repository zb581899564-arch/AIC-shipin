"""Unique prepare -> shared GPU SFT+screen -> CPU -> conditional confirmation."""
import datetime as dt
import json
import os
import subprocess
import traceback
from gws_common import ROOT,RUN,PYTHON,read,save,sha

def run_cpu(script,*args):
    env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
    subprocess.run([PYTHON,str(ROOT/'code'/script),*args],env=env,check=True)

def gpu(name,confirm=False):
    p=read(ROOT/'protocol.json');wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
    cmd=[PYTHON,str(wrapper),'--name',name,'--max-seconds',str(1200 if confirm else 3900),
         '--planned-output-bytes','134217728','--capacity-reason','registered small native16 image LoRA plus final adapter and generation; frozen base/no full checkpoint',
         '--queue-seconds','900','--',PYTHON,str(ROOT/'code/train_screen.py')]
    if confirm: cmd.append('--confirm')
    save(ROOT/('confirm_gpu_launch.json' if confirm else 'training_gpu_launch.json'),{'command':cmd,'utc':dt.datetime.now(dt.timezone.utc).isoformat()})
    subprocess.run(cmd,check=True)
    resource=RUN/'controller'/f'{name}.resource.json';rec=read(resource)
    ledger=ROOT.parent/'improvement_round1/gpu_ledger.jsonl'
    matches=[json.loads(l) for l in ledger.read_text().splitlines() if json.loads(l).get('name')==name]
    terminal=[r for r in matches if r.get('status') in ('completed','failed','timeout','terminated')]
    if rec.get('status')!='completed' or rec.get('exit_code')!=0 or len(terminal)!=1 or terminal[0]!=rec:
        raise ValueError('unique completed shared GPU resource/ledger required')
    save(ROOT/('confirm_resource.json' if confirm else 'training_resource.json'),rec)

def main():
    save(ROOT/'chain_started.json',{'pid':os.getpid(),'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),'production_admitted':False})
    if not os.environ.get('CUDA_VISIBLE_DEVICES'): raise ValueError('parent CUDA index must be nonempty')
    run_cpu('prepare.py');p=read(ROOT/'protocol.json')
    gpu(p['GPU_job']);run_cpu('evaluate.py','--role','screen')
    result=read(ROOT/'screen/result.json')
    if result['status']!='PASS_REGISTERED_STATIC_GATE':
        save(ROOT/'completion.json',{'status':'STOP_TRAINED_SCREEN_REJECTED_CONFIRM_NOT_RUN','screen_result_sha256':sha(ROOT/'screen/result.json'),
             'optimizer_steps':50,'new_submission_zips':0,'production_admitted':False});return
    save(ROOT/'selected.json',{'screen_result_sha256':sha(ROOT/'screen/result.json'),
          'final_adapter_sha256':sha(ROOT/'train/adapter/adapter_model.safetensors'),'parameters_changed_after_screen':False})
    gpu(p['confirm_GPU_job'],True);run_cpu('evaluate.py','--role','confirm')
    result=read(ROOT/'confirm/result.json')
    save(ROOT/'completion.json',{'status':'PASS_STATIC_RESEARCH_NOT_VIDEO_PRODUCTION' if result['status']=='PASS_REGISTERED_STATIC_GATE'
         else 'STOP_CONFIRM_REJECTED','confirm_result_sha256':sha(ROOT/'confirm/result.json'),
         'new_submission_zips':0,'production_admitted':False})

if __name__=='__main__':
    try: main()
    except Exception as e:
        if not (ROOT/'chain_failure.json').exists(): save(ROOT/'chain_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'preserve_all_success_no_retry':True})
        raise
