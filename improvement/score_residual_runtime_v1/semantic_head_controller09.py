"""One conditional CPU continuation of registered head fits; never starts GPU."""
import subprocess
import sys
import time
import traceback
from common_runtime import *

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU continuation masks only itself')
    write(ROOT/'head_started09.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],argv=sys.argv,utc=utc()))
    start=time.monotonic()
    while not (ROOT/'chain_completion.json').exists():
        require(not (ROOT/'chain_failure.json').exists(),'Feature parent failed; no head fit permitted')
        require(time.monotonic()-start<4500,'Completion wait ended; observation timeout is not GPU failure')
        time.sleep(15)
    resource=RUN/'controller'/(read(ROOT/'protocol.json')['job_name']+'.resource.json')
    # Shared wrapper terminal receipt and natural parent completion are both
    # mandatory; no lock/PID absence is used to infer model success.
    require(resource.exists(),'Missing terminal resource receipt')
    terminal=read(resource);require(terminal['status']=='completed' and terminal['exit_code']==0,'Actual shared GPU terminal failed')
    write(ROOT/'adopted_feature_terminal09.json',dict(chain_completion_sha256=sha(ROOT/'chain_completion.json'),resource_path=str(resource),resource_sha256=sha(resource),completion_sha256=sha(ROOT/'completion.json')))
    subprocess.run([str(PYTHON),str(ROOT/'head_code09/semantic_oof09.py')],check=True)
    write(ROOT/'head_completion09.json',dict(utc=utc(),result=read(ROOT/'semantic_oof09/result.json')))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        write(ROOT/'head_controller09_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()));raise
