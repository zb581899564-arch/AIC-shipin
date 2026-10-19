"""After first descriptor success, preserve25 audio successes and old failure."""
import os,sys,json,subprocess,time,datetime
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def save(name,value):
    with(ROOT/name).open('x')as f:json.dump(value,f,indent=2,allow_nan=False)


def main():
    start=time.monotonic();assert os.environ.get('CUDA_VISIBLE_DEVICES')
    assert(ROOT/'production_controller_failure.json').exists()
    assert not(ROOT/'packages').exists(),'No duplicate successful package call'
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','PYTHONDONTWRITEBYTECODE':'1'}
    def run(p,*args):subprocess.run([PY,'-B',str(p),*args],env=env,check=True)
    for name in ['SEMANTIC_EVENT_RANK','EVENT_REFERENCE_MEMORY']:run(ROOT/'production_code_v1/package_event.py',name)
    run(ROOT/'production_recovery_code_v2/formal_audio_remaining_v2.py')
    run(ROOT/'production_code_v1/package_event.py','EVENT_AUDIO_VISUAL')
    completed={}
    for name in ['SEMANTIC_EVENT_RANK','EVENT_REFERENCE_MEMORY','EVENT_AUDIO_VISUAL']:
        with(ROOT/'packages'/name/'completion.json').open()as f:completed[name]=json.load(f)
    save('production_recovery_completion_02.json',dict(status='COMPLETED_EXIT0_ALL_THREE_EXPLORATORY_PACKAGES',packages=completed,elapsed_remaining_seconds=time.monotonic()-start,old_failure_preserved=True,successes_adopted=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),website_submitted=False))


if __name__=='__main__':
    try:main()
    except BaseException as e:
        import traceback
        save('production_recovery_failure_02.json',dict(error=repr(e),traceback=traceback.format_exc(),successes_preserved=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        raise
