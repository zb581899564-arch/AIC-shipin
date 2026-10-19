"""Unique registered CPU text acceptance then shared GPU semantic extraction."""
import subprocess
import sys
import traceback
from common_runtime import *

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Actual parent GPU0 visibility')
    write(ROOT/'chain_started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],argv=sys.argv,utc=utc()))
    proto=read(ROOT/'protocol.json')
    subprocess.run([str(PYTHON),str(ROOT/'code/semantic09.py'),'prepare'],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    subprocess.run([str(PYTHON),str(ROOT/'code/semantic09.py'),'qa'],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    write(ROOT/'source_lock.json',dict(protocol_sha256=sha(ROOT/'protocol.json'),cpu_acceptance_sha256=sha(ROOT/'cpu_acceptance.json'),code={p.name:sha(p) for p in sorted((ROOT/'code').glob('*.py'))}))
    cmd=[str(PYTHON),str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',proto['job_name'],'--max-seconds',str(proto['max_gpu_seconds']),'--planned-output-bytes','500000000','--capacity-reason','Reuses 11.38GB accepted CPU tensors; new text-conditioned BASE representations and one control, no generated labels or model training; new outputs bounded 0.5GB','--queue-seconds','600','--',str(PYTHON),str(ROOT/'code/semantic09.py'),'infer']
    write(ROOT/'gpu_launch.json',dict(command=cmd,utc=utc(),source_lock_sha256=sha(ROOT/'source_lock.json')))
    subprocess.run(cmd,check=True)
    write(ROOT/'chain_completion.json',dict(status='SEMANTIC_EXTRACTION_COMPLETE_SEPARATE_CPU_HEAD_GATE_REQUIRED',utc=utc(),completion_sha256=sha(ROOT/'completion.json')))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        write(ROOT/'chain_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()));raise
