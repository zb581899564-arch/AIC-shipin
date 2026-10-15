"""One detached registered chain; no implicit retry or old launcher reuse."""
import argparse,json,os,subprocess,sys,traceback
from pathlib import Path
from mf_common import *

def run(stage):
    root=ROOT/stage;reg=read(root/'registration.json')
    require(not(root/'chain_started.json').exists(),'A started chain must not restart')
    save(root/'chain_started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],utc=utc(),registration_ref=ref(root/'registration.json'),parent_CUDA=os.environ.get('CUDA_VISIBLE_DEVICES')))
    cpu=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
    script=str(Path(__file__).parent/'stages.py')
    def command(args,env,log):
        with (root/log).open('x') as handle:subprocess.run(args,env=env,stdout=handle,stderr=subprocess.STDOUT,check=True)
    try:
        command([str(PY),'-B',script,'prepare','--stage',stage],cpu,'cpu.log')
        wrapper=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        command([str(PY),'-B',str(wrapper),'--name',reg['gpu_job_name'],'--max-seconds',str(reg['max_GPU_seconds']),
            '--planned-output-bytes',str(reg['planned_output_bytes']),'--capacity-reason','New prompt token inputs adopt complete old native visual caches; no duplicated media/vision tensors; bounded structured raw outputs and CPU QA',
            '--queue-seconds','60','--',str(PY),'-B',script,'infer','--stage',stage],os.environ.copy(),'gpu.log')
        command([str(PY),'-B',script,'output_qa','--stage',stage],cpu,'output_qa.log')
        save(root/'chain_completion.json',dict(status='NATURAL_COMPLETE_NEW_STAGE',completion_ref=ref(root/'completion.json'),utc=utc()))
    except BaseException as error:
        save(root/'chain_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc(),preserve_successful=True,implicit_retry=False));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True);run(p.parse_args().stage)
