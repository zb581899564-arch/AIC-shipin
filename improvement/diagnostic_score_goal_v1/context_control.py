"""One explicit130 context pilot, independent first output QA, and comparison."""
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


def run(root):
    reg=read(root/'context_GPU_registration_29.json')
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Parent retains actual physical GPU')
    require(bound(reg['controller_code'])==Path(__file__).resolve(),'Exact context29 parent code')
    require(reg['expected_pilot_forwards']==130 and reg['max_GPU_seconds']==1800,'Only registered130 pilot')
    require(read(bound(reg['input_acceptance']))['inputs']==335,'All335 first CPU inputs before GPU')
    remain=(dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
    require(remain>reg['max_GPU_seconds']+180,'Leave measured QA and delivery time')
    save(root/'context_parent_claim_29.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'context_GPU_registration_29.json')))
    entries=[]
    try:
        wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        commands=[('GPU',[sys.executable,'-B',str(wrapper),'--name',reg['GPU_job'],'--max-seconds',str(reg['max_GPU_seconds']),
            '--planned-output-bytes','200000000','--capacity-reason',
            'Readonly BASE/PAIR200130 first source-overview inputs; adopted imagepatches/no decoder; actual3video grids CPU-QAd. Live shared resources and measured priorPAIR17GB plus bounded80observation attention; no fixed resource threshold.',
            '--queue-seconds','60','--',sys.executable,'-B','-u',str(bound(reg['GPU_code'])),'--root',str(root)],False),
            ('review',[sys.executable,'-B','-u',str(bound(reg['review_code'])),'--root',str(root)],True)]
        for stage,argv,cpu in commands:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
            if cpu:env['CUDA_VISIBLE_DEVICES']=''
            with (root/('context_'+stage+'_29.log')).open('xb') as log:
                p=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]
                entry=dict(stage=stage,pid=p.pid,start_ticks=ticks,argv=argv,CPU_child=cpu)
                save(root/('context_'+stage+'_launch_29.json'),entry);entries.append(entry)
                code=p.wait();require(code==0,'Actual stage '+stage+' exit '+str(code))
            if stage=='GPU':
                resource=RUN/'controller'/(reg['GPU_job']+'.resource.json');record=read(resource)
                matches=[json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                         if line.strip() and json.loads(line).get('name')==reg['GPU_job']]
                require(matches==[record] and record['status']=='completed' and record['exit_code']==0,'Unique natural GPU terminal')
                save(root/'context_resource_29.json',dict(resource=ref(resource),record=record,unique_ledger_entries=1))
        save(root/'context_terminal_29.json',dict(status='ALL130_CONTEXT_RAW_FIRST_QA_AND_FIXED_COMPARISON_NATURAL_COMPLETE_EXIT0',
            utc=utc(),entries=entries,exit_code=0,comparison=ref(root/'context_comparison_29/result.json'),
            remaining_not_started=True,production_not_started=True))
    except BaseException as error:
        save(root/'context_parent_failure_29.json',dict(utc=utc(),error=repr(error),traceback=traceback.format_exc(),
            entries=entries,preserve_all_success=True,no_automatic_retry=True,failure_not_empty=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);run(parser.parse_args().root)
