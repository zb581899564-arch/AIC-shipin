"""Unique read-only-data observation audit controller, CPU only."""
import argparse
from pathlib import Path
import sys
import subprocess
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import *

def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only controller')
    reg=read(root/'observation_registration_27.json')
    require(bound(reg['controller'])==Path(__file__).resolve(),'Exact observation controller')
    argv=[sys.executable,'-B','-u',str(bound(reg['code'])),'--root',str(root)]
    start=time.monotonic()
    try:
        with (root/'observation_CPU_27.log').open('xb') as log:
            p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ))
            ticks=(Path('/proc')/str(p.pid)/'stat').read_text().split(') ',1)[1].split()[19]
            save(root/'observation_child_27.json',dict(utc=utc(),pid=p.pid,start_ticks=ticks,argv=argv))
            code=p.wait()
        require(code==0,'Actual observation CPU failed exit '+str(code))
        result=root/'observation_audit_27/result.json'
        require(read(result)['status']=='COMPLETE_FIRST_NESTED_OBSERVABILITY_METADATA_NOT_MODEL_QUALITY','Complete real observation audit')
        save(root/'observation_terminal_27.json',dict(status='OBSERVATION_AUDIT_NATURAL_COMPLETE_EXIT0',exit_code=code,
            result=ref(result),elapsed_seconds=time.monotonic()-start,model_calls=0,media_reads=0,processor_calls=0,utc=utc()))
    except BaseException as error:
        save(root/'observation_failure_27.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
