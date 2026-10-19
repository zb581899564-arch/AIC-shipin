"""Explicit single-use ROI CPU/preflight or shared-GPU readout controller."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import traceback

from roi_runtime import WORK,PYTHON,read,save,ref,require,registration,utc


def run(root,phase):
    reg=registration(root)
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'Parent keeps actual physical GPU index')
    save(root/('roi_'+phase+'_claim_06.json'),dict(utc=utc(),pid=os.getpid(),phase=phase,registration=ref(root/'roi_registration_06.json')))
    entries=[]
    try:
        base=[str(PYTHON),'-B','-u',str(root/'roi_code_06/roi_runtime.py')]
        if phase=='cpu':
            commands=[('prepare',base+['prepare','--root',str(root)],True),
                      ('input_qa',base+['input_qa','--root',str(root)],True)]
        else:
            require(phase in ('pilot32','remaining590'),'Explicit registered readout stage')
            require((root/'roi_inputs_06/input_acceptance.json').is_file(),'All622 actual CPU inputs before any GPU')
            if phase=='remaining590':
                require((root/'roi_remaining_admission_07.json').is_file(),'Measured pilot32 mapping/cost decision required')
            wrapper=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
            budget=reg['GPU_seconds'][phase]
            remain=(dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
            require(remain>budget+120,'Leave time for output QA and delivery within10h')
            cmd=[str(PYTHON),'-B',str(wrapper),'--name',reg['GPU_jobs'][phase],'--max-seconds',str(budget),
                 '--planned-output-bytes',str(reg['planned_output_bytes'][phase]),'--capacity-reason',
                 'First spatial patch features from already accepted external inputs, no JPEG decode or old forward repeated. Live shared-resource check and measured raw-token plus pooled-output estimate; no fixed capacity threshold.',
                 '--queue-seconds','60','--']+base+['infer','--root',str(root),'--stage',phase]
            commands=[('GPU',cmd,False),('output_qa',base+['output_qa','--root',str(root),'--stage',phase],True)]
        for name,cmd,cpu in commands:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
            if cpu:env['CUDA_VISIBLE_DEVICES']=''
            with (root/('roi_'+phase+'_'+name+'_06.log')).open('xb') as log:
                p=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                stat=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()
                entry=dict(stage=name,argv=cmd,pid=p.pid,start_ticks=stat[19],CPU_child=cpu)
                save(root/('roi_'+phase+'_'+name+'_launch_06.json'),entry);entries.append(entry)
                code=p.wait();require(code==0,'First stage naturally failed: '+name+' exit='+str(code))
        if phase!='cpu':
            path=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(reg['GPU_jobs'][phase]+'.resource.json')
            record=read(path)
            matches=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                     if x.strip() and json.loads(x).get('name')==reg['GPU_jobs'][phase]]
            require(matches==[record] and record['status']=='completed' and record['exit_code']==0,'Unique shared GPU natural terminal')
            save(root/('roi_'+phase+'_resource_06.json'),dict(resource=ref(path),record=record,unique_ledger_entries=1))
        save(root/('roi_'+phase+'_terminal_06.json'),dict(status='NATURAL_COMPLETE_REGISTERED_STAGES',exit_code=0,
             entries=entries,utc=utc(),no_426_or_package_started=True))
    except BaseException as e:
        save(root/('roi_'+phase+'_failure_06.json'),dict(error=repr(e),traceback=traceback.format_exc(),entries=entries,
             preserve_all_success=True,no_automatic_retry=True,utc=utc()));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--phase',choices=['cpu','pilot32','remaining590'],required=True);a=p.parse_args();run(a.root,a.phase)
