"""Unique parent; CPU children mask themselves, shared wrapper owns GPU."""
import subprocess
import sys
import traceback
from common_runtime import *

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Parent actual GPU0 visibility required')
    write(ROOT/'chain_started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],argv=sys.argv,utc=utc()))
    def cpu(name):
        event('CPU_CHILD_START',name=name)
        subprocess.run([str(PYTHON),str(ROOT/'code'/name)],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    cpu('prepare.py')
    wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
    cmd=[str(PYTHON),str(wrapper),'--name','summe25_residual_frozen_vision_features_20261016_v1','--max-seconds','5400','--planned-output-bytes','350000000','--capacity-reason','25 preaccepted external sources only; existing 8B frozen vision image means, no generation; measured CPU inputs separate','--queue-seconds','600','--',str(PYTHON),str(ROOT/'code/features.py')]
    write(ROOT/'feature_gpu_launch.json',dict(command=cmd,utc=utc(),cpu_acceptance_sha256=sha(ROOT/'cpu_acceptance.json')))
    subprocess.run(cmd,check=True)
    cpu('evaluate.py')
    write(ROOT/'completion.json',dict(status='EXTERNAL_EXPERIMENT_FINISHED_SEE_QUALITY_RESULT',utc=utc(),result=read(ROOT/'evaluation/result.json')))

if __name__=='__main__':
    try:main()
    except BaseException as e:
        write(ROOT/'failure.json',dict(utc=utc(),error=repr(e),traceback=traceback.format_exc()))
        raise
