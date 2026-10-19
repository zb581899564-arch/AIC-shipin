"""One explicit CPU subprocess and its actual natural exit receipt."""
import argparse
from pathlib import Path
import sys
import time
import traceback
import subprocess
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import *


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only controller')
    reg=read(root/'marginal_utility_registration_25.json')
    require(bound(reg['controller'])==Path(__file__).resolve(), 'Actual frozen CPU controller')
    argv=[sys.executable,'-B','-u',str(bound(reg['code'])),'--root',str(root)]
    start=time.monotonic()
    try:
        with (root/'marginal_utility_CPU_25.log').open('xb') as log:
            process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ))
            ticks=(Path('/proc')/str(process.pid)/'stat').read_text().split(') ',1)[1].split()[19]
            save(root/'marginal_utility_child_25.json',dict(utc=utc(),pid=process.pid,start_ticks=ticks,argv=argv,CPU_only=True))
            code=process.wait()
        require(code==0, 'Actual CPU utility process failed with exit '+str(code))
        result=root/'marginal_utility_25/result.json'
        require(read(result)['status']=='COMPLETE_ONE_FROZEN_CONDITIONAL_UTILITY_AND_CONTROLS_NOT_PRODUCTION',
                'Natural exit without complete first fit result')
        save(root/'marginal_utility_terminal_25.json',dict(status='CPU_FIT_READOUT_COMPARE_NATURAL_COMPLETE_EXIT0',
             utc=utc(),exit_code=code,argv=argv,elapsed_seconds=time.monotonic()-start,result=ref(result),
             new_8B_forwards=0,new_optimizer_updates=0,new_PCA_fits=0,new_closed_form_fits=2))
    except BaseException as error:
        save(root/'marginal_utility_failure_25.json',dict(utc=utc(),error=repr(error),traceback=traceback.format_exc(),
             preserve_all_success=True,no_automatic_retry=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
