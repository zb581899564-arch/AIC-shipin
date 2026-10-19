"""Explicit supervised CPU/pilot/remaining stages, recording actual exits."""
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


def run(root,phase):
    cp=root/'utility_value_CPU_registration_55.json';cpu=read(cp)
    require(bound(cpu['controller_code'])==Path(__file__).resolve(),'Exact supervised utility56 parent')
    if phase=='cpu':
        reg=cpu;budget=900;rp=cp
        commands=[('targets',[sys.executable,'-B','-u',str(bound(cpu['preparation_code'])),'--root',str(root)],True)]
    else:
        require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'GPU parent retains actual CUDA index')
        original=read(root/'utility_value_GPU_registration_55.json')
        require(read(bound(original['input_acceptance']))['status']=='PASS_UTILITY55_TRAIN_TARGETS_AND_ADOPTED_INPUTS_CPU',
            'Actual target/input adoption acceptance before GPU')
        rp=root/('utility_value_GPU_registration_55.json' if phase=='pilot4' else 'utility_value_remaining_admission_55.json')
        reg=read(rp);budget=reg['max_seconds']
        require(budget==(1200 if phase=='pilot4' else 4200),'Explicit per-phase budget')
        if phase=='remaining496':
            require(reg['original_GPU_registration']==ref(root/'utility_value_GPU_registration_55.json')
                and read(bound(reg['pilot_output_acceptance']))['status']=='PASS_UTILITY_PILOT4_FIRST_ENGINEERING_QA',
                'Only accepted immutable pilot can continue')
        wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        gpu=[sys.executable,'-B',str(wrapper),'--name',reg['GPU_job'],'--max-seconds',str(budget),
            '--planned-output-bytes','1000000000','--capacity-reason',
            'Fresh language-only continuous IoU gain gradient arm using adopted CPU inputs; actual live shared resources checked. Pilot measures double-order gradient graph peak/cost before explicit remaining continuation. No fixed utilization or free-memory thresholds.',
            '--queue-seconds','60','--',sys.executable,'-B','-u',str(bound(original['GPU_code'])),'--root',str(root),'--phase',phase]
        commands=[('GPU',gpu,False),('first_output_QA',[sys.executable,'-B','-u',str(bound(original['review_code'])),
            '--root',str(root),'--stage','pilot' if phase=='pilot4' else 'final'],True)]
    remaining=(dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
    require(remaining>budget+120,'Leave independent QA inside Goal window')
    save(root/('utility_'+phase+'_parent_claim_56.json'),dict(utc=utc(),pid=os.getpid(),registration=ref(rp),phase=phase))
    entries=[]
    try:
        for name,argv,is_cpu in commands:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
            if is_cpu:env['CUDA_VISIBLE_DEVICES']=''
            with (root/('utility_'+phase+'_'+name+'_56.log')).open('xb') as log:
                p=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]
                entry=dict(stage=name,argv=argv,pid=p.pid,start_ticks=ticks,CPU_child=is_cpu)
                save(root/('utility_'+phase+'_'+name+'_launch_56.json'),entry);entries.append(entry)
                code=p.wait()
                save(root/('utility_'+phase+'_'+name+'_exit_56.json'),dict(utc=utc(),actual_exit_code=code,entry=entry))
                require(code==0,'Actual utility '+phase+'/'+name+' exit '+str(code))
            if name=='GPU':
                resource=RUN/'controller'/(reg['GPU_job']+'.resource.json');record=read(resource)
                ledger=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                    if x.strip() and json.loads(x).get('name')==reg['GPU_job']]
                require(ledger==[record] and record['status']=='completed' and record['exit_code']==0,'Unique actual shared resource/ledger')
                save(root/('utility_'+('pilot' if phase=='pilot4' else 'remaining')+'_resource_receipt_56.json'),
                    dict(record=record,resource=ref(resource),unique_ledger_entries=1))
        save(root/('utility_'+phase+'_terminal_56.json'),dict(status='REGISTERED_UTILITY_STAGES_NATURAL_COMPLETE_EXIT0',
            utc=utc(),exit_code=0,entries=entries,automatic_remaining=False,confirm_started=False,production_started=False))
    except BaseException as e:
        save(root/('utility_'+phase+'_parent_failure_56.json'),dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),
            entries=entries,preserve_all_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--phase',choices=['cpu','pilot4','remaining496'],required=True);a=p.parse_args();run(a.root,a.phase)
