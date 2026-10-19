"""Single-use CPU or shared GPU/QA/evaluation confirmation stage."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

from roi_confirm_recovery import config,WORK,PYTHON,read,save,ref,require,utc


def run(root,phase):
    reg=config(root);require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Parent retains actual physical GPU index')
    save(root/('roi_confirm_remaining19_'+phase+'_claim_12.json'),dict(utc=utc(),pid=os.getpid(),registration=ref(root/'roi_confirm_remaining19_registration_12.json')))
    entries=[]
    try:
        base=[str(PYTHON),'-B','-u',str(root/'roi_confirm_recovery_code_12/roi_confirm_recovery.py')]
        if phase=='cpu':
            commands=[('inherit_inputs',base+['inherit_inputs','--root',str(root)],True)]
        else:
            require((root/'roi_confirm_remaining19_inputs_12/input_acceptance.json').is_file(),'All actual first confirmation input QA before GPU')
            require((dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()>1320,
                    'Leave time for1200-second GPU plus QA before10h deadline')
            wrapper=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
            cmd=[str(PYTHON),'-B',str(wrapper),'--name',reg['GPU_job'],'--max-seconds','1200',
                 '--planned-output-bytes','150000000','--capacity-reason',
                 'Remaining19 original BASE and19 spatial readouts only; first completed but unrecorded source excluded, no call repeated. Measured static vision readout17418MiB and under150MB output; current shared resources checked separately.',
                 '--queue-seconds','60','--']+base+['infer','--root',str(root)]
            commands=[('GPU',cmd,False),('output_qa',base+['output_qa','--root',str(root)],True),
                      ('evaluate',base+['evaluate','--root',str(root)],True)]
        for name,cmd,cpu in commands:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
            if cpu:env['CUDA_VISIBLE_DEVICES']=''
            with (root/('roi_confirm_remaining19_'+phase+'_'+name+'_12.log')).open('xb') as log:
                p=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                stat=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()
                entry=dict(stage=name,pid=p.pid,start_ticks=stat[19],argv=cmd,CPU_child=cpu)
                save(root/('roi_confirm_remaining19_'+phase+'_'+name+'_launch_12.json'),entry);entries.append(entry)
                rc=p.wait();require(rc==0,'First confirmation stage naturally failed: '+name+' exit='+str(rc))
            if name=='GPU':
                path=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(reg['GPU_job']+'.resource.json')
                resource=read(path)
                ledger=[json.loads(v) for v in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                        if v.strip() and json.loads(v).get('name')==reg['GPU_job']]
                require(ledger==[resource] and resource['status']=='completed' and resource['exit_code']==0,'Unique actual completed/exit0 confirmation GPU')
                save(root/'roi_confirm_remaining19_resource_12.json',dict(resource=ref(path),record=resource,unique_ledger_entries=1))
        save(root/('roi_confirm_remaining19_'+phase+'_terminal_12.json'),dict(status='NATURAL_COMPLETE_REGISTERED_CONFIRM_STAGES',
             entries=entries,exit_code=0,utc=utc(),no_426_or_package_started=True))
    except BaseException as e:
        save(root/('roi_confirm_remaining19_'+phase+'_failure_12.json'),dict(error=repr(e),traceback=traceback.format_exc(),entries=entries,
             preserve_all_success=True,do_not_repeat_success=True,utc=utc()));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['cpu','gpu'],required=True)
    a=p.parse_args();run(a.root,a.phase)
