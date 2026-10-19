"""One explicit admitted CPU production chain; no experiment or GPU launcher."""
import os,sys,json,subprocess,time,datetime
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def save(name,value):
    with (ROOT/name).open('x',encoding='utf8')as f:json.dump(value,f,indent=2,allow_nan=False)


def main():
    start=time.monotonic()
    with(ROOT/'production_admission.json').open()as f:admission=json.load(f)
    names=list(admission['mechanisms'])
    assert len(names)in(1,3)and admission['allow_formal_first_descriptor_QA']
    assert not(ROOT/'formal_inputs_01').exists()and not(ROOT/'packages').exists(),'No duplicate initial launcher'
    assert os.environ.get('CUDA_VISIBLE_DEVICES'),'Parent CUDA identity preserved'
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','PYTHONDONTWRITEBYTECODE':'1'}
    def run(name,*args):subprocess.run([PY,'-B',str(ROOT/'production_code_v1'/name),*args],env=env,check=True)
    run('formal_inputs.py')
    if'EVENT_AUDIO_VISUAL'in names:run('formal_audio.py')
    for name in names:run('package_event.py',name)
    completion={}
    for name in names:
        with(ROOT/'packages'/name/'completion.json').open()as f:completion[name]=json.load(f)
    save('production_controller_completion.json',dict(status='COMPLETED_EXIT0_ALL_ADMITTED_CPU_PACKAGES',packages=completion,elapsed_seconds=time.monotonic()-start,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),no_new_GPU=True,website_submitted=False))


if __name__=='__main__':
    try:main()
    except BaseException as e:
        import traceback
        save('production_controller_failure.json',dict(error=repr(e),traceback=traceback.format_exc(),successes_preserved=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        raise
