"""Explicit post-feature recovery: zero repeated decode/forward/optimizer."""
import subprocess
import sys
import traceback
from common_runtime import *

if __name__=='__main__':
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only explicit recovery')
    require(read(ROOT/'feature_completion.json')['status']=='PASS_25_NEW_FROZEN_FEATURES','Successful feature work required')
    require((ROOT/'failure.json').exists() and not (ROOT/'evaluation').exists(),'Only original pre-training dependency failure')
    write(ROOT/'evaluation_recovery03_started.json',dict(pid=os.getpid(),argv=sys.argv,utc=utc(),old_failure_sha256=sha(ROOT/'failure.json'),feature_completion_sha256=sha(ROOT/'feature_completion.json')))
    try:
        subprocess.run([str(PYTHON),str(ROOT/'code/evaluate_recovery03.py')],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
        write(ROOT/'evaluation_recovery03_completion.json',dict(status='POST_FEATURE_EVALUATION_RECOVERY_COMPLETE',utc=utc(),result=read(ROOT/'evaluation/result.json')))
    except BaseException as error:
        write(ROOT/'evaluation_recovery03_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
