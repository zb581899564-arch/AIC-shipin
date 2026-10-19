"""Conditional production only after immutable actual semantic OOF admission."""
import subprocess
import sys
import traceback
from common_runtime import *

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Actual parent GPU0 visibility')
    from production_semantic10 import checked_registration
    reg=checked_registration();lock=read(ROOT/'source_lock.json')
    for name,digest in lock['files'].items():require(sha(ROOT/name)==digest,'Frozen production source changed: '+name)
    write(ROOT/'chain_started.json',dict(utc=utc(),pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],argv=sys.argv))
    def cpu(script,*args):
        event('CPU_CHILD_START',script=script,args=list(args))
        subprocess.run([str(PYTHON),str(ROOT/'code'/script),*args],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    cpu('production_prepare.py')
    cpu('production_semantic10.py','prepare');cpu('production_semantic10.py','qa')
    write(ROOT/'input_source_lock.json',dict(registration_sha256=sha(ROOT/'production_registration.json'),original_CPU_acceptance_sha256=sha(ROOT/'cpu_acceptance.json'),query_manifest_sha256=sha(ROOT/'query09/cpu_acceptance.json'),independent_text_QA_sha256=sha(ROOT/'query09/independent_text_QA.json')))
    cmd=[str(PYTHON),str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',reg['GPU_job_name'],'--max-seconds',str(reg['GPU_max_seconds']),'--planned-output-bytes',str(reg['future_feature_and_package_bytes']),'--capacity-reason','One registered semantic head; all426 native image CPU inputs and new text QA accepted; frozen BASE context inference, no teacher/test labels/training; outputs estimated from actual source clocks','--queue-seconds','600','--',str(PYTHON),str(ROOT/'code/production_semantic10.py'),'infer']
    write(ROOT/'gpu_launch.json',dict(utc=utc(),command=cmd,input_source_lock_sha256=sha(ROOT/'input_source_lock.json')))
    subprocess.run(cmd,check=True)
    cpu('production_semantic_apply10.py');cpu('production_semantic_package10.py')
    write(ROOT/'completion.json',dict(status='COMPLETE_ONE_NEW_CONTEXT_SEMANTIC_HEAD_ZIP_OFFICIAL_EFFECT_UNKNOWN',package=read(ROOT/'package/completion.json'),utc=utc()))

if __name__=='__main__':
    try:main()
    except BaseException as error:
        write(ROOT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()));raise
