"""Not a launcher by itself: demands a unique frozen production registration."""
import subprocess
import sys
import traceback
from common_runtime import *

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Parent actual GPU0 visibility')
    reg=read(ROOT/'production_registration.json')
    require(read(reg['external_result']['path'])['new_production_allowed'] is True and sha(reg['external_result']['path'])==reg['external_result']['sha256'],'Frozen actual external gate')
    for name,digest in read(ROOT/'source_lock.json')['files'].items():require(sha(ROOT/name)==digest,'Frozen production source changed '+name)
    write(ROOT/'chain_started.json',dict(utc=utc(),pid=os.getpid(),argv=sys.argv))
    def cpu(name):
        event('CPU_CHILD_START',name=name)
        subprocess.run([str(PYTHON),str(ROOT/'code'/name)],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    cpu('production_prepare.py')
    cmd=[str(PYTHON),str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name','score_residual426_frozen_vision_20261016_v1','--max-seconds','5400','--planned-output-bytes','1000000000','--capacity-reason','One externally frozen human-supervised residual head on original VERIFY baseline; first new vision features only, old successful generation reused','--queue-seconds','600','--',str(PYTHON),str(ROOT/'code/production_features.py')]
    write(ROOT/'feature_gpu_launch.json',dict(utc=utc(),command=cmd,cpu_acceptance_sha256=sha(ROOT/'cpu_acceptance.json')))
    subprocess.run(cmd,check=True)
    cpu('production_monotone_apply.py');cpu('production_package.py')
    write(ROOT/'completion.json',dict(status='COMPLETE_ONE_NEW_PROXY_QUALIFIED_SUBMISSION_ZIP',package=read(ROOT/'package/completion.json'),utc=utc()))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        write(ROOT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
