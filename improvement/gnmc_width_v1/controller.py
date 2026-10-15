"""One claimed research chain; never launches production or packages a candidate."""
import datetime as dt
import json
import os
import shutil
import socket
import subprocess
import traceback
from common import ROOT, RUN, PYTHON, read, save, sha

def child(script,*args,cpu=False):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
             TOKENIZERS_PARALLELISM='false',PYTHONNOUSERSITE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    if cpu: env['CUDA_VISIBLE_DEVICES']=''
    log=ROOT/(script.replace('.py','')+'_'+('_'.join(args).replace('--','') or 'once')+'.log')
    with log.open('x') as f:
        subprocess.run([PYTHON,str(ROOT/'code'/script),*args],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)

def gpu(role):
    name=f'gnmc_width_{role}20_original_b_20261013_v1'
    args=[PYTHON,str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',name,
        '--max-seconds','1200','--planned-output-bytes','8388608','--capacity-reason',
        'One40-call static width diagnostic; CPU images/tensors already resident, old measured base peak17.7GiB; live shared lock/resource check protects external work',
        '--queue-seconds','900','--',PYTHON,str(ROOT/'code/infer.py'),'--role',role]
    save(ROOT/f'{role}_gpu_launch.json',{'name':name,'command':args,'source_lock_sha256':sha(ROOT/'source_lock.json'),
        'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES')})
    with (ROOT/f'{role}_wrapper.log').open('x') as f: subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
    resource=read(RUN/'controller'/f'{name}.resource.json')
    ledger=ROOT.parent/'improvement_round1/gpu_ledger.jsonl'
    entries=[json.loads(s) for s in ledger.read_text().splitlines() if s]
    matching=[r for r in entries if r['name']==name]
    if len(matching)!=1 or matching[0]!=resource or resource['status']!='completed' or resource['exit_code']!=0:
        raise ValueError('unique successful GPU terminal/resource ledger not established')
    save(ROOT/f'{role}_resource.json',resource)
    child('evaluate.py','--role',role,cpu=True)

def main():
    assert socket.gethostname()=='inspur-NP5570M5'
    if not os.environ.get('CUDA_VISIBLE_DEVICES'): raise ValueError('parent must retain registered actual GPU index')
    save(ROOT/'chain_started.json',{'pid':os.getpid(),'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES']})
    child('prepare.py',cpu=True)
    dependencies=[RUN/'b_score_aligned_package_v4/config.json',RUN/'b_score_aligned_package_v4/spatial_baseline.py',
                  RUN/'b_score_aligned_package_v4/contracts.py',RUN/'b_score_aligned_package_v4/engine.py',
                  RUN/'temporal_sft8b_v1/sft_contract.py',RUN/'resource_unlimited_v1_20261007/gpu_run.py']
    files={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and
        (p.parent.name in ['code','proofs','tensors','rgb','media','control','reference'] or p.name in
         ['inputs.json','protocol.json','purpose_reply.json','official_rule_check.json','input_acceptance.json','media_plan.json'])}
    save(ROOT/'source_lock.json',{'files':files,'external_files':{str(p):sha(p) for p in dependencies},
        'scope':'NONCOMMERCIAL_STATIC16_RESEARCH_NO_PRODUCTION','actual_complete_pipeline_parameters':8782459120})
    gpu('screen')
    screened=read(ROOT/'screen/result.json')
    if screened['status']!='PASS_REGISTERED_STATIC_SCREEN_ONLY':
        save(ROOT/'completion.json',{'status':'STOP_SCREEN_REJECTED_NO_CONFIRM_GPU_NO_PRODUCTION',
            'screen_result_sha256':sha(ROOT/'screen/result.json'),'new_submission_zips':0,
            'charged_seconds':read(ROOT/'screen_resource.json')['charged_seconds']});return
    save(ROOT/'selected.json',{'arm':'FIX_ORIGINAL_FOCUS_PREDICT_CONTINUOUS_WIDTH_ONLY',
        'screen_result_sha256':sha(ROOT/'screen/result.json'),'source_lock_sha256':sha(ROOT/'source_lock.json')})
    gpu('confirm')
    confirmed=read(ROOT/'confirm/result.json')
    save(ROOT/'completion.json',{'status':'PASS_STATIC_REFERENCE_ONLY_PRODUCTION_REQUIRES_SEPARATE_ADMISSION'
        if confirmed['status']=='PASS_REGISTERED_STATIC_CONFIRM_ONLY' else 'STOP_CONFIRM_REJECTED_NO_PRODUCTION',
        'confirm_result_sha256':sha(ROOT/'confirm/result.json'),'new_submission_zips':0,
        'charged_seconds':sum(read(ROOT/f'{role}_resource.json')['charged_seconds'] for role in ['screen','confirm'])})

if __name__=='__main__':
    try: main()
    except Exception as e:
        p=ROOT/'chain_failure.json'
        if not p.exists():save(p,{'status':'STOP_PRESERVE_RAW_AND_ALL_SUCCESS_NO_AUTO_RERUN','error':repr(e),'traceback':traceback.format_exc()})
        raise
