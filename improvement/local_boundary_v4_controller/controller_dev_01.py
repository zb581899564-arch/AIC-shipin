import os,sys,json,datetime,subprocess,traceback
from pathlib import Path
META=Path(__file__).resolve().parent
BASE=META.parent/'local_boundary_v4/dev'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
def put(path,value):
 with path.open('x') as f: json.dump(value,f,indent=2)
def main():
 if os.environ.get('CUDA_VISIBLE_DEVICES')!='0': raise ValueError('Parent actual GPU0 visibility required')
 put(BASE/'controller_launch_claim_01.json',{'pid':os.getpid(),'argv':sys.argv,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_budget':37,'nominal':40,'skip':3})
 try:
  for stage,file in [('admit','admit_dev_01.py'),('chain','chain_dev_01.py')]:
   env=os.environ.copy()
   if stage=='admit': env['CUDA_VISIBLE_DEVICES']=''
   env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
   with (BASE/('controller_'+stage+'_01.log')).open('x') as log:
    done=subprocess.run([PY,'-u',str(META/file)],env=env,stdout=log,stderr=subprocess.STDOUT)
   put(BASE/('controller_'+stage+'_exit_01.json'),{'exit_code':done.returncode})
   if done.returncode: raise RuntimeError(stage+' failed; no retries')
 except BaseException as e:
  put(BASE/'controller_failure_01.json',{'error':repr(e),'traceback':traceback.format_exc(),'preserve_all':True})
  raise
if __name__=='__main__': main()
