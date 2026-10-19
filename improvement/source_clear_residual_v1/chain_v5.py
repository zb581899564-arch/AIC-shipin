"""Unique controller, explicit existing CPU continuation then one GPU job."""
from sr_common import *
import subprocess
import time

def run(script,*args,cpu_only=True):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    if cpu_only:env['CUDA_VISIBLE_DEVICES']=''
    subprocess.run([str(PY),'-B',str(ROOT/'code'/script),*args],env=env,check=True)

def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Parent CUDA remains actual nonempty GPU0')
    require(not(ROOT/'chain_v5_started.json').exists(),'Unique recovery controller cannot restart')
    require(not(ROOT/'gpu_launch.json').exists(),'No GPU may have been attempted before input-only recovery')
    save(ROOT/'chain_v5_started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],argv=sys.argv,utc=utc(),recovery_ref=ref(ROOT/'input_remaining_recovery_v5.json')))
    # The explicit CPU continuation was already launched once, never launch it again.
    claim=read(ROOT/'cpu_remaining_v5_launch.json');pid=claim['pid']
    while not(ROOT/'cpu_completion.json').exists():
        stat=Path('/proc')/str(pid)/'stat'
        require(stat.exists()and stat.read_text().split()[21]==claim['start_ticks']and stat.read_text().split()[2]!='Z','Actual owned CPU preparation exited before complete receipt')
        require(not list(ROOT.glob('prepare_v5_prepare_failure*.json')),'Actual new CPU preparation failed')
        time.sleep(5)
    run('checks.py');run('prepare_v5.py','qa')
    lock=dict(registration_ref=ref(ROOT/'registration.json'),CPU_ref=ref(ROOT/'cpu_completion.json'),first_input_QA_ref=ref(ROOT/'input_qa.json'),checks_ref=ref(ROOT/'targeted_checks.json'),code={p.name:ref(p)for p in sorted((ROOT/'code').glob('*.py'))},utc=utc(),deadline='2026-10-18T08:36:50Z')
    save(ROOT/'source_lock.json',lock)
    name='source_clear33_fullbaseline_verify_and_context_20261018_v1'
    cmd=[str(PY),str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',name,'--max-seconds','5400','--planned-output-bytes','100000000','--capacity-reason','238 first external TIME VERIFY, 8 first VideoXum BASE-context sources; all actual new CPU inputs/first independent QA complete; existing187 B0 and all426 formal features adopted; measured original B peak<23GiB; serialized shared lock protects other jobs','--queue-seconds','600','--',str(PY),'-B',str(ROOT/'code/infer.py'),'infer']
    save(ROOT/'gpu_launch.json',dict(name=name,command=cmd,source_lock_sha256=sha(ROOT/'source_lock.json'),utc=utc()))
    subprocess.run(cmd,check=True)
    terminal=read(RUN/'controller'/(name+'.resource.json'))
    require(terminal['status']=='completed'and terminal.get('returncode',terminal.get('exit_code',0))==0,'Unique natural GPU terminal must succeed')
    save(ROOT/'natural_gpu_terminal_adoption.json',dict(resource_ref=ref(RUN/'controller'/(name+'.resource.json')),natural_completed=True,utc=utc()))
    run('infer.py','replay');run('fit.py')
    save(ROOT/'chain_completion.json',dict(status='EXTERNAL_BASELINE_AND_ONE_HEAD_COMPLETE_REQUIRES_MAIN_PRODUCTION_ADMISSION',utc=utc(),comparison_ref=ref(ROOT/'external_comparison.json'),source_lock_sha256=sha(ROOT/'source_lock.json')))

if __name__=='__main__':
    try:main()
    except BaseException as e:failure('chain',e);raise
