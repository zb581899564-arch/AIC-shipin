"""Unique first crop31 CPU preparation only; never starts GPU."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from crop_common_v31 import *


def run(root):
    reg=registration(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only CPU process masks itself')
    require(bound(reg['CPU_controller'])==Path(__file__).resolve(),'Exact31 CPU controller')
    argv=[sys.executable,'-B','-u',str(bound(reg['preparation_code'])),'--root',str(root)];start=time.monotonic()
    try:
        with (root/'crop_CPU_31.log').open('xb') as log:
            p=subprocess.Popen(argv,cwd=root,env=dict(os.environ),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]
            save(root/'crop_CPU_child_31.json',dict(pid=p.pid,start_ticks=ticks,argv=argv,utc=utc()))
            code=p.wait();require(code==0,'Actual firstcropCPU preparation exit '+str(code))
        gate=root/'crop_inputs_31/input_acceptance.json'
        require(read(gate)['status']=='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA','All first crop-derived inputs accepted')
        save(root/'crop_CPU_terminal_31.json',dict(status='ALL_CROP31_FIRST_CPU_QA_NATURAL_COMPLETE_EXIT0',utc=utc(),
            exit_code=code,input_acceptance=ref(gate),elapsed_seconds=time.monotonic()-start,new_model=0,new_training=0,GPU_not_started=True))
    except BaseException as error:
        save(root/'crop_CPU_failure_31.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,
            no_automatic_retry=True));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);run(parser.parse_args().root)
