"""One explicitly admitted reference/CPU/GPU scope; never auto-expands scope."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK,RUN,read,save,ref,bound,require,utc


def run(root,scope,phase,registration):
    reg=read(registration)
    require(bound(reg['controller_code'])==Path(__file__).resolve(),'Exact explicit utility62 supervisor')
    if phase=='reference':
        require(scope in ('screen','confirm') and reg['schema']=='UTILITY_FIXED_PROFILE_REFERENCE_METADATA_V57','Explicit metadata scope')
        commands=[('reference',[sys.executable,'-B','-u',str(bound(reg['code'])),'--root',str(root),'--scope',scope],True)]
    elif phase=='CPU':
        require(scope in ('resized20','resized19','production') and reg['scope']==scope,'Explicit first CPU scope')
        commands=[('CPU',[sys.executable,'-B','-u',str(bound(reg['preparation_code'])),'--root',str(root),'--scope',scope],True)]
    else:
        require(phase=='GPU' and reg['scope']==scope and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Explicit live GPU scope')
        deadline=dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))
        require((deadline-dt.datetime.now(dt.timezone.utc)).total_seconds()>reg['max_seconds']+120,'Leave independent QA insideGoal')
        wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        argv=[sys.executable,'-B',str(wrapper),'--name',reg['GPU_job'],'--max-seconds',str(reg['max_seconds']),
            '--planned-output-bytes',str(reg['planned_output_bytes']),'--capacity-reason',reg['capacity_reason'],
            '--queue-seconds','60','--',sys.executable,'-B','-u',str(bound(reg['GPU_code'])),'--root',str(root),
            '--scope',scope,'--registration',str(registration)]
        commands=[('GPU',argv,False),('output_QA',[sys.executable,'-B','-u',str(bound(reg['review_code'])),
            '--root',str(root),'--scope',scope,'--registration',str(registration)],True)]
    prefix='utility_'+phase+'_'+scope+'_62'
    save(root/(prefix+'_claim.json'),dict(utc=utc(),registration=ref(registration),phase=phase,scope=scope,pid=os.getpid()))
    entries=[]
    try:
        for name,argv,cpu in commands:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
            if cpu:env['CUDA_VISIBLE_DEVICES']=''
            with (root/(prefix+'_'+name+'.log')).open('xb') as log:
                child=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]
                entry=dict(stage=name,argv=argv,pid=child.pid,start_ticks=ticks,CPU_child=cpu);entries.append(entry)
                save(root/(prefix+'_'+name+'_launch.json'),entry);code=child.wait()
                save(root/(prefix+'_'+name+'_exit.json'),dict(utc=utc(),actual_exit_code=code,entry=entry))
                require(code==0,'Actual utility62 '+scope+'/'+name+' exit '+str(code))
            if name=='GPU':
                resource=RUN/'controller'/(reg['GPU_job']+'.resource.json');record=read(resource)
                ledger=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                    if x.strip() and json.loads(x).get('name')==reg['GPU_job']]
                require(ledger==[record] and record['status']=='completed' and record['exit_code']==0,'Unique actual scope resource/ledger')
                save(root/('utility_'+scope+'_resource_receipt_60.json'),dict(record=record,resource=ref(resource),unique_ledger_entries=1))
        save(root/(prefix+'_terminal.json'),dict(status='REGISTERED_UTILITY_SCOPE_NATURAL_COMPLETE_EXIT0',exit_code=0,
            utc=utc(),scope=scope,phase=phase,entries=entries,automatic_next_scope=False,automatic_packaging=False))
    except BaseException as e:
        save(root/(prefix+'_failure.json'),dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),entries=entries,
            preserve_all_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--scope',required=True)
    p.add_argument('--phase',choices=['reference','CPU','GPU'],required=True);p.add_argument('--registration',type=Path,required=True)
    a=p.parse_args();run(a.root,a.scope,a.phase,a.registration)
