"""One CPU-only research controller. Production always needs main review."""
from event_common import *
import subprocess
import time


def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Parent keeps original physical GPU visibility; CPU children mask themselves')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-18T14:00:00+00:00'),'Reserve2 hours for fallback delivery; no new main controller after14Z')
    require(not(ROOT/'controller_started.json').exists(),'Never relaunch completed/attempted controller')
    save(ROOT/'controller_started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],argv=sys.argv,utc=utc()))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    started=time.monotonic()
    for script,args in [('event_checks.py',[]),('event_runtime.py',['prepare']),('event_runtime.py',['fit']),('event_runtime.py',['evaluate'])]:
        subprocess.run([str(PY),'-B',str(ROOT/'code_v1'/script),*args],env=env,check=True)
    save(ROOT/'controller_completion.json',dict(status='COMPLETED_EXIT0_CPU_RESEARCH_ONLY',elapsed_seconds=time.monotonic()-started,development_completion_ref=ref(ROOT/'development_completion.json'),new_GPU=0,new_model_download=0,production_started=False,utc=utc()))


if __name__=='__main__':
    try:main()
    except BaseException as error:failure('controller',error);raise
