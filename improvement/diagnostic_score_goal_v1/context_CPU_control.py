"""Unique first335 context inputs CPU launcher; no GPU or implicit continuation."""
import argparse
from pathlib import Path
import sys
import subprocess
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import *

def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only CPU controller masks itself')
    reg=read(root/'context_CPU_registration_28.json')
    require(bound(reg['CPU_controller'])==Path(__file__).resolve(),'Explicit context CPU controller')
    argv=[sys.executable,'-B','-u',str(bound(reg['preparation_code'])),'--root',str(root)]
    start=time.monotonic()
    try:
        with (root/'context_CPU_28.log').open('xb') as log:
            p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ))
            ticks=(Path('/proc')/str(p.pid)/'stat').read_text().split(') ',1)[1].split()[19]
            save(root/'context_CPU_child_28.json',dict(pid=p.pid,start_ticks=ticks,argv=argv,utc=utc()))
            code=p.wait()
        require(code==0,'Actual context CPU preparation exit '+str(code))
        gate=root/'context_inputs_28/input_acceptance.json'
        require(read(gate)['status']=='PASS_ALL_NEW_SOURCE_OVERVIEW_CONTEXT_INPUTS','All335 first context input QA')
        save(root/'context_CPU_terminal_28.json',dict(status='ALL335_CONTEXT_FIRST_CPU_QA_NATURAL_COMPLETE_EXIT0',
            exit_code=code,utc=utc(),elapsed_seconds=time.monotonic()-start,input_acceptance=ref(gate),
            new_models=0,new_training=0,new_media=0,real_vision_processor=0,GPU_not_launched=True))
    except BaseException as error:
        save(root/'context_CPU_failure_28.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,
             no_automatic_retry=True))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
