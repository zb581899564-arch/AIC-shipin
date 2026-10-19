"""One explicit pilot4 or separately admitted remaining496; no implicit stages."""
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
    original=read(root/'crop_GPU_registration_32.json')
    require(bound(original['controller_code'])==Path(__file__).resolve(),'Exact frozen crop GPU parent')
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'GPU parent retains actual physical index')
    if phase=='pilot4':
        reg=original;number='32';stage='BASE';budget=1200
    else:
        require(phase=='remaining496','Explicit crop phase only')
        reg=read(root/'crop_remaining_admission_33.json');number='33';stage='TRAINED';budget=3600
        require(reg['original_pilot_registration']==ref(root/'crop_GPU_registration_32.json') and
            reg['GPU_code']==original['GPU_code'] and reg['input_acceptance']==original['input_acceptance'],
            'Only exact remaining496 continuation')
        require(read(bound(reg['BASE_output_acceptance']))['status']=='PASS_CROP_BASE_SCREEN_AND_PILOT4_FIRST_QA',
                'Pilot first actual raw/gradient/RNG/Adam QA before continuation')
    require(read(bound(original['input_acceptance']))['status']=='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA',
            'All actual new crop CPU input QA before GPU')
    remain=(dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
    require(remain>budget+180,'Leave QA and delivery within original Goal window')
    save(root/('crop_'+phase+'_parent_claim_'+number+'.json'),dict(utc=utc(),pid=os.getpid(),phase=phase,
        registration=ref(root/('crop_GPU_registration_32.json' if phase=='pilot4' else 'crop_remaining_admission_33.json'))))
    entries=[]
    try:
        wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        gpu=[sys.executable,'-B',str(wrapper),'--name',reg['GPU_job'],'--max-seconds',str(budget),
            '--planned-output-bytes','600000000','--capacity-reason',
            'New source+actualcropA/B language-only r8 training. All first new CPU inputs accepted; original RGB/source patches adopted. Current shared host/GPU/capacity inspected, actual3image grids and measured prior r8 peak; no fixed resource thresholds.',
            '--queue-seconds','60','--',sys.executable,'-B','-u',str(bound(original['GPU_code'])),'--root',str(root),'--phase',phase]
        commands=[('GPU',gpu,False),('first_output_QA',[sys.executable,'-B','-u',str(bound(original['review_code'])),
            '--root',str(root),'--stage',stage],True)]
        if phase=='remaining496':commands.append(('comparison',[sys.executable,'-B','-u',str(bound(reg['comparison_code'])),
            '--root',str(root)],True))
        for name,argv,cpu in commands:
            env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
            if cpu:env['CUDA_VISIBLE_DEVICES']=''
            with (root/('crop_'+phase+'_'+name+'_'+number+'.log')).open('xb') as log:
                p=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]
                entry=dict(stage=name,argv=argv,pid=p.pid,start_ticks=ticks,CPU_child=cpu)
                save(root/('crop_'+phase+'_'+name+'_launch_'+number+'.json'),entry);entries.append(entry)
                code=p.wait();require(code==0,'Actual crop '+phase+'/'+name+' exit '+str(code))
            if name=='GPU':
                resource=RUN/'controller'/(reg['GPU_job']+'.resource.json');record=read(resource)
                ledger=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                    if x.strip() and json.loads(x).get('name')==reg['GPU_job']]
                require(ledger==[record] and record['status']=='completed' and record['exit_code']==0,
                        'Actual unique shared GPU completed/exit0 terminal')
                save(root/('crop_'+phase+'_resource_'+number+'.json'),dict(record=record,resource=ref(resource),unique_ledger_entries=1))
        save(root/('crop_'+phase+'_terminal_'+number+'.json'),dict(status='REGISTERED_CROP_STAGES_NATURAL_COMPLETE_EXIT0',
            utc=utc(),exit_code=0,entries=entries,automatic_remaining=False,confirm_started=False,production_started=False))
    except BaseException as error:
        save(root/('crop_'+phase+'_parent_failure_'+number+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),
            entries=entries,utc=utc(),preserve_all_success=True,no_automatic_retry=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--phase',choices=['pilot4','remaining496'],required=True);args=parser.parse_args();run(args.root,args.phase)
