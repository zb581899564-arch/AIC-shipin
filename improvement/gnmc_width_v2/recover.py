"""Explicit namespace repair: reuse all40 accepted sources, no prepare/download calls."""
import datetime as dt
import json
import os
import subprocess
import traceback
import sys
from pathlib import Path
from gw_common import ROOT, OUT, RUN, PYTHON, read, save, sha, paths

def execute(role):
    name=f'gnmc_width_{role}20_original_b_20261013_v2'
    args=[PYTHON,str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',name,
        '--max-seconds','1200','--planned-output-bytes','8388608','--capacity-reason',
        'Explicit namespace-only recovery, reuse40acceptedRGB/80CPU tensors; previous62.105s failed before any real answer; no data preparation repeated',
        '--queue-seconds','900','--',PYTHON,str(OUT/'code/infer.py'),'--role',role]
    save(OUT/f'{role}_gpu_launch.json',{'name':name,'command':args,'source_lock_sha256':sha(OUT/'source_lock.json'),
        'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES')})
    with (OUT/f'{role}_wrapper.log').open('x') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
    resource=read(RUN/'controller'/f'{name}.resource.json')
    matching=[json.loads(s) for s in (ROOT.parent/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if s and json.loads(s)['name']==name]
    if len(matching)!=1 or matching[0]!=resource or resource['status']!='completed' or resource['exit_code']!=0:
        raise ValueError('unique actual terminal/resource ledger mismatch')
    save(OUT/f'{role}_resource.json',resource)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
             PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    with (OUT/f'{role}_replay.log').open('x') as f:
        subprocess.run([PYTHON,str(OUT/'code/evaluate.py'),'--role',role],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)

def main():
    paths()
    import engine
    if Path(sys.modules['common'].__file__) != RUN/'b_score_aligned_package_v4/common.py' or not callable(engine.require):
        raise ValueError('original engine/common namespace not restored')
    if not os.environ.get('CUDA_VISIBLE_DEVICES'):raise ValueError('parent GPU visibility missing')
    if sha(ROOT/'source_lock.json')!='bd88d52a3e18aaced8661f658bb6d5a402ac241e09d4dc69f606dbdabcb50848':
        raise ValueError('original successful input/source lock changed')
    failure=read(ROOT/'screen_inference_failure.json')
    if failure['error']!='NameError("name \'require\' is not defined")':raise ValueError('not the audited namespace failure')
    if (ROOT/'screen/calls.jsonl').exists() or (ROOT/'screen/model_identity.json').exists():
        raise ValueError('previous real successes exist; this recovery cannot repeat them')
    acceptance=read(ROOT/'input_acceptance.json')
    if acceptance['items']!=40 or acceptance['stages']!=80:raise ValueError('accepted denominator changed')
    old=read(ROOT/'source_lock.json')
    for rel,digest in old['files'].items():
        if sha(ROOT/rel)!=digest:raise ValueError('frozen original input/code changed:'+rel)
    new=dict(old['files'])
    for p in (OUT/'code').glob('*.py'):new[str(p.relative_to(ROOT))]=sha(p)
    new['recovery_01/recovery_protocol.json']=sha(OUT/'recovery_protocol.json')
    external=dict(old['external_files'])
    external[str(RUN/'b_score_aligned_package_v4/common.py')]=sha(RUN/'b_score_aligned_package_v4/common.py')
    save(OUT/'source_lock.json',{'files':new,'external_files':external,
        'original_source_lock_sha256':sha(ROOT/'source_lock.json'),'repair':'namespace common->gw_common only',
        'old_fee_preserved_seconds':62.10517555847764,'input_prepare_model_successes_repeated':False})
    save(OUT/'chain_started.json',{'pid':os.getpid(),'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES']})
    execute('screen')
    s=read(OUT/'screen/result.json')
    if s['status']!='PASS_REGISTERED_STATIC_SCREEN_ONLY':
        save(OUT/'completion.json',{'status':'STOP_SCREEN_REJECTED_NO_CONFIRM_GPU_NO_PRODUCTION',
            'screen_result_sha256':sha(OUT/'screen/result.json'),'new_submission_zips':0,
            'charged_seconds':read(OUT/'screen_resource.json')['charged_seconds']});return
    save(OUT/'selected.json',{'arm':'FIX_ORIGINAL_FOCUS_PREDICT_CONTINUOUS_WIDTH_ONLY',
        'screen_result_sha256':sha(OUT/'screen/result.json'),'source_lock_sha256':sha(OUT/'source_lock.json')})
    execute('confirm')
    c=read(OUT/'confirm/result.json')
    save(OUT/'completion.json',{'status':'PASS_STATIC_REFERENCE_ONLY_PRODUCTION_REQUIRES_SEPARATE_ADMISSION'
        if c['status']=='PASS_REGISTERED_STATIC_CONFIRM_ONLY' else 'STOP_CONFIRM_REJECTED_NO_PRODUCTION',
        'confirm_result_sha256':sha(OUT/'confirm/result.json'),'new_submission_zips':0,
        'charged_seconds':sum(read(OUT/f'{role}_resource.json')['charged_seconds'] for role in ['screen','confirm'])})

if __name__=='__main__':
    try:main()
    except Exception as e:
        p=OUT/'chain_failure.json'
        if not p.exists():save(p,{'status':'STOP_PRESERVE_FAILURE_AND_ALL_SUCCESS','error':repr(e),'traceback':traceback.format_exc()})
        raise
