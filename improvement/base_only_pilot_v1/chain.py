"""One fixed 12-call job, its new CPU output replay and independent evaluation."""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/base_only_pilot')
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
CODE=ROOT/'code/pilot_revision_02.py'
EVAL=ROOT.parent/'temporal_diagnosis/code/evaluate_base_only12.py'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
def main():
    if not os.environ.get('CUDA_VISIBLE_DEVICES'):
        raise ValueError('Parent must keep actual nonempty CUDA index')
    p=read(ROOT/'protocol.json')
    if dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat(p['deadline']):
        raise ValueError('No new experiment after deadline')
    if read(ROOT/'admission.json')['source_lock_sha256']!=sha(ROOT/'source_lock.json'):
        raise ValueError('Actual CPU input admission missing')
    name=p['gpu_name'];ledger=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    if (RUN/('controller/'+name+'.resource.json')).exists() or any(json.loads(x)['name']==name for x in ledger.read_text().splitlines() if x.strip()):
        raise ValueError('Job name already has terminal evidence; do not repeat')
    out=ROOT/'chain_01';out.mkdir(exist_ok=False)
    save(out/'claim.json',{'pid':os.getpid(),'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_lock_sha256':sha(ROOT/'source_lock.json'),'chain_code_sha256':sha(__file__),
        'evaluation_code_sha256':sha(EVAL),'evaluation_policy_sha256':sha(ROOT.parent/'temporal_diagnosis/base_only_eval_01/policy_01.json'),
        'parent_CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES']})
    commands=[('gpu',[PY,str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',name,
        '--max-seconds',str(p['max_gpu_seconds']),'--planned-output-bytes',str(p['planned_output_bytes']),
        '--capacity-reason','12 unchanged external64 inputs; prior originalB peak22.4GiB on actual48GBAda, no conflicting GPU; current memory/disk checked; Java1JVMCPU separate',
        '--queue-seconds','900','--',PY,'-B',str(CODE),'infer',str(ROOT)]),
        ('replay',[PY,'-B',str(CODE),'replay',str(ROOT)]),
        ('evaluation',[PY,'-B',str(EVAL),'evaluate'])]
    try:
        for stage,command in commands:
            env=dict(os.environ)
            if stage!='gpu':env['CUDA_VISIBLE_DEVICES']=''
            save(out/(stage+'.launch.json'),{'command':command,'CPU_only':stage!='gpu','utc':dt.datetime.now(dt.timezone.utc).isoformat()})
            with (out/(stage+'.log')).open('x') as f:
                result=subprocess.run(command,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
            if result.returncode:raise RuntimeError(stage+' exit '+str(result.returncode))
        save(out/'completion.json',{'status':'COMPLETE_NEW_BASE_ONLY_PILOT_AND_DEVELOPMENT_EVALUATION_NOT_PRODUCTION',
            'source_lock_sha256':sha(ROOT/'source_lock.json'),'gpu_completion_sha256':sha(ROOT/'gpu_01/completion.json'),
            'CPU_replay_completion_sha256':sha(ROOT/'replay_01/completion.json'),'new_test_calls':0,'new_ZIPs':0})
    except BaseException as e:
        save(out/'failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'successful_stages_and_calls_preserved':True})
        raise


if __name__=='__main__':main()
