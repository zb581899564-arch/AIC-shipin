"""Preregistered new decision calibration only if original raw heads all fail dev."""
import subprocess
import sys
import time
import traceback
from common_runtime import *

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU only')
    write(ROOT/'calibration04_started.json',dict(pid=os.getpid(),utc=utc(),argv=sys.argv,protocol_sha256=sha(ROOT/'calibration_protocol_04.json')))
    started=time.monotonic()
    while not (ROOT/'evaluation_recovery03_completion.json').exists():
        require(not (ROOT/'evaluation_recovery03_failure.json').exists(),'Original fitting engineering failure; no calibration recovery')
        require(time.monotonic()-started<900,'Wait for original bounded four-head fitting exceeded')
        time.sleep(5)
    result=read(ROOT/'evaluation/result.json')
    if result['status']!='STOP_NO_DEV_HEAD_PASSED':
        write(ROOT/'calibration04_completion.json',dict(status='NOT_EXECUTED_ORIGINAL_HEAD_HAS_DEV_ADMISSION',original_result_status=result['status'],new_bias_evaluations=0));return
    subprocess.run([str(PYTHON),str(ROOT/'code/calibrate04.py')],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    write(ROOT/'calibration04_completion.json',dict(status='COMPLETE_REGISTERED_BIAS_CALIBRATION_NO_OPTIMIZER',result=read(ROOT/'calibration04/result.json'),utc=utc()))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        write(ROOT/'calibration04_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
