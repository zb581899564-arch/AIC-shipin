"""One explicitly registered direct-box stage, with real child/exit ownership."""
import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK,RUN,read,bound,ref,save,require,utc

DEADLINE='2026-10-18T03:22:24Z'


def command(root,reg):
    require(reg['schema']=='DIRECT_BOX_EXPLICIT_EXECUTION_V85' and reg['deadline_utc']==DEADLINE,
        'Exact one-stage registration and original Goal deadline')
    require(bound(reg['controller_code'])==Path(__file__).resolve(),'Exact controller source')
    child=bound(reg['child_code']);science=bound(reg['science_registration'])
    require(child.parent==(root/'direct_box_code_84').resolve() and science.is_relative_to(root)
        and child.name.startswith('direct_box_') and child.suffix=='.py','Only explicitly bound direct-box project code')
    args=reg['child_args'];require(isinstance(args,list) and all(isinstance(x,str) for x in args)
        and '--root' not in args and type(reg['GPU']) is bool,'Explicit array argv, no alternate root')
    argv=[sys.executable,'-B','-u',str(child),'--root',str(root),*args]
    if reg['GPU']:
        require(type(reg['planned_output_bytes']) is int and reg['planned_output_bytes']>0
            and isinstance(reg['capacity_reason'],str) and reg['capacity_reason'].strip(),'Measured GPU capacity admission')
        argv=[sys.executable,'-B',str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name',reg['GPU_job'],'--max-seconds',str(reg['max_seconds']),
            '--planned-output-bytes',str(reg['planned_output_bytes']),'--capacity-reason',reg['capacity_reason'],
            '--queue-seconds','60','--',*argv]
    return argv


def run(root,rp):
    root=Path(root).resolve();rp=Path(rp).resolve()
    require(sys.platform=='linux' and root.is_relative_to(WORK) and rp.is_relative_to(root),'Linux same-root explicit execution')
    reg=read(rp);require(type(reg['max_seconds']) is int and reg['max_seconds']>0,'Finite explicit runtime budget')
    require((dt.datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()>reg['max_seconds']+120,
        'Keep actual stage and independent inspection inside Goal window')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Parent preserves actual physical GPU index')
    argv=command(root,reg);stage=reg['stage']
    require(stage and all(c.isalnum() or c=='_' for c in stage),'Exact stage artifact namespace')
    prefix='direct_box_'+stage+'_85';entry=None
    save(root/(prefix+'_claim.json'),dict(utc=utc(),registration=ref(rp),stage=stage,controller_pid=os.getpid(),automatic_next_stage=False))
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if reg['GPU'] else '',PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (root/(prefix+'.log')).open('xb') as stream:
            p=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]
            entry=dict(argv=argv,pid=p.pid,start_ticks=ticks,CPU_child=not reg['GPU'])
            save(root/(prefix+'_launch.json'),entry);exit_code=p.wait()
            save(root/(prefix+'_exit.json'),dict(utc=utc(),entry=entry,actual_exit_code=exit_code))
            require(exit_code==0,'Actual registered direct-box stage failed: '+str(exit_code))
        resource=None
        if reg['GPU']:
            path=RUN/'controller'/(reg['GPU_job']+'.resource.json');record=read(path)
            rows=[__import__('json').loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                if line.strip() and __import__('json').loads(line).get('name')==reg['GPU_job']]
            require(rows==[record] and record['status']=='completed' and record['exit_code']==0
                and record['command']==argv[argv.index('--')+1:],'Unique same-command natural GPU terminal')
            receipt=root/(prefix+'_resource.json');save(receipt,dict(resource=ref(path),record=record,unique_ledger_entries=1));resource=ref(receipt)
        save(root/(prefix+'_terminal.json'),dict(status='DIRECT_BOX_REGISTERED_STAGE_NATURAL_COMPLETE_EXIT0',utc=utc(),
            stage=stage,entry=entry,registration=ref(rp),exit_code=exit_code,resource=resource,automatic_next_stage=False))
    except BaseException as error:
        save(root/(prefix+'_failure.json'),dict(utc=utc(),stage=stage,entry=entry,registration=ref(rp),error=repr(error),
            traceback=traceback.format_exc(),preserve_all_success_and_failure=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True)
    a=p.parse_args();run(a.root,a.registration)
