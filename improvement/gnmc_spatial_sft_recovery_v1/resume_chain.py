"""Recover only unfinished HTTP429 preparation, then original registered recipe."""
import datetime as dt
import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work/gnmc_spatial_sft_iteration_20261013_v1')
sys.path.insert(0,str(ROOT/'code'))
from gs_common import PYTHON,read,save,sha
from controller import gpu,run_cpu

def main():
    out=ROOT/'recovery_01'
    failure=read(ROOT/'prepare_failure.json')
    if '429' not in failure['error'] or (ROOT/'training_gpu_launch.json').exists(): raise ValueError('not the registered pre-GPU rate-limit failure')
    if not os.environ.get('CUDA_VISIBLE_DEVICES'): raise ValueError('parent needs actual GPU index')
    save(out/'started.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'pid':os.getpid(),
          'failed_entry_not_restarted':True,'successful_inputs_reused':True})
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(ROOT/'code'))
    subprocess.run([PYTHON,str(out/'code/prepare_resume.py')],env=env,check=True)
    p=read(ROOT/'protocol.json');gpu(p['GPU_job']);run_cpu('evaluate.py','--role','screen')
    s=read(ROOT/'screen/result.json')
    if s['status']!='PASS_REGISTERED_STATIC_GATE':
        save(out/'completion.json',{'status':'STOP_TRAINED_SCREEN_REJECTED_CONFIRM_NOT_RUN',
             'screen_result_sha256':sha(ROOT/'screen/result.json'),'optimizer_steps':50,'new_submission_zips':0});return
    save(ROOT/'selected.json',{'screen_result_sha256':sha(ROOT/'screen/result.json'),
          'final_adapter_sha256':sha(ROOT/'train/adapter/adapter_model.safetensors'),'parameters_changed_after_screen':False})
    gpu(p['confirm_GPU_job'],True);run_cpu('evaluate.py','--role','confirm')
    c=read(ROOT/'confirm/result.json')
    save(out/'completion.json',{'status':'PASS_STATIC_RESEARCH_NOT_VIDEO_PRODUCTION' if c['status']=='PASS_REGISTERED_STATIC_GATE'
         else 'STOP_CONFIRM_REJECTED','confirm_result_sha256':sha(ROOT/'confirm/result.json'),
         'new_submission_zips':0,'production_admitted':False})

if __name__=='__main__':
    try:main()
    except Exception as e:
        out=ROOT/'recovery_01/failure.json'
        if not out.exists():save(out,{'error':repr(e),'traceback':traceback.format_exc(),'preserve_all_success':True})
        raise
