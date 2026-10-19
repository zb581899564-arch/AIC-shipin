"""Adopt successful first8; run only first remaining CPU preparation/QA."""
import pathlib,os,subprocess,json,datetime as dt,time
F=pathlib.Path('/home/inspur/aic_video_work/visual_pair_formal_20261018_v1')
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
code=F/'code_v2/visual_pair_formal_v2.py'
assert (F/'prepare_02/pilot8_completion.json').is_file()
assert not (F/'input_acceptance_pilot8.json').exists()
out=F/'cpu_remaining_chain_01';out.mkdir();started=time.monotonic()
for stage in ['input_qa_pilot8','prepare_remaining','input_qa_remaining']:
    with (out/(stage+'.log')).open('xb') as log:
        result=subprocess.run([PY,'-B',str(code),stage],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
    with (out/(stage+'.terminal.json')).open('x') as stream:json.dump(dict(stage=stage,exit_code=result.returncode,utc=dt.datetime.now(dt.timezone.utc).isoformat()),stream)
    if result.returncode:raise RuntimeError('First CPU stage failure preserved: '+stage)
with (out/'completion.json').open('x') as stream:json.dump(dict(status='PASS_ALL316_PREPARE_AND_FIRST_INPUT_QA',elapsed_seconds=time.monotonic()-started,utc=dt.datetime.now(dt.timezone.utc).isoformat()),stream)
