"""Explicit CPU capacity pilot, remaining-only preparation, or final package."""
import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'pair_code_17'))
from pair_common import read,save,ref,bound,require,utc
sys.path.insert(0, str(Path(__file__).resolve().parent))


def run(root,phase,rp):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only this CPU supervisor masks itself')
    reg=read(rp);require(bound(reg['controller_code'])==Path(__file__).resolve(),'Exact utility65 CPU supervisor')
    deadline=dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))
    require((deadline-dt.datetime.now(dt.timezone.utc)).total_seconds()>reg['max_seconds']+120,'Leave budget for independent completion inspection')
    if phase=='package':
        require(reg['schema']=='STAR_EXACT_OBSERVATION_PACKAGE_V72','Explicit final package registration')
        argv=[sys.executable,'-B','-u',str(bound(reg['code'])),'--root',str(root),'--registration',str(rp)]
    else:
        original_path=root/'star_production_CPU_registration_72.json';original=read(original_path)
        require(original['schema']=='STAR_PRODUCTION_OBSERVATION_CPU_V72','Exact first production CPU registration')
        if phase=='pilot32':require(rp.resolve()==original_path.resolve(),'Only first explicit32 CPU capacity pilot')
        else:
            require(phase=='remaining' and reg['schema']=='STAR_PRODUCTION_REMAINING_CPU_V72'
                and reg['original_registration']==ref(original_path)
                and rp.resolve()==(root/'star_production_remaining_admission_72.json').resolve(),
                'Only explicit same-domain fixed remaining continuation')
        argv=[sys.executable,'-B','-u',str(bound(original['preparation_code'])),'--root',str(root),'--phase',phase]
    prefix='star_production_'+phase+'_72'
    save(root/(prefix+'_claim.json'),dict(utc=utc(),registration=ref(rp),phase=phase,pid=os.getpid()))
    entry=None
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
        with (root/(prefix+'.log')).open('xb') as stream:
            p=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]
            entry=dict(argv=argv,pid=p.pid,start_ticks=ticks,CPU_child=True)
            save(root/(prefix+'_launch.json'),entry);code=p.wait()
            save(root/(prefix+'_exit.json'),dict(utc=utc(),actual_exit_code=code,entry=entry))
            require(code==0,'Actual utility65 '+phase+' exit '+str(code))
        save(root/(prefix+'_terminal.json'),dict(status='EXPLICIT_STAR_CPU_NATURAL_COMPLETE_EXIT0',utc=utc(),exit_code=0,
            entry=entry,automatic_remaining=False,automatic_GPU=False,automatic_package=False))
    except BaseException as e:
        save(root/(prefix+'_failure.json'),dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),entry=entry,
            preserve_all_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['pilot32','remaining','package'],required=True)
    p.add_argument('--registration',type=Path,required=True);a=p.parse_args();run(a.root,a.phase,a.registration)
