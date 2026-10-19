"""Only16unprepared sources after registered original source-color failure."""
import os,pathlib,json,subprocess,datetime as dt,time,hashlib
F=pathlib.Path('/home/inspur/aic_video_work/visual_pair_formal_20261018_v1');PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
code=F/'code_v5/visual_pair_formal_v5.py';out=F/'cpu_remaining_chain_05';out.mkdir()
def save(p,x):
    with p.open('x') as s:json.dump(x,s,indent=2)
def ref(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
started=time.monotonic()
with (out/'prepare_remaining16.log').open('xb') as log:r=subprocess.run([PY,'-B',str(code),'prepare_shard','30','46'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
save(out/'prepare_remaining16.terminal.json',dict(exit_code=r.returncode))
assert r.returncode==0,'Actual remainingfailure preserved, no automaticrepeat'
reg=json.loads((F/'registration_01.json').read_text());inputs=[]
for case in reg['cases']:
    for order in ['AB','BA']:inputs.append(ref(F/'prepare_02'/case['sid']/(order+'.json')))
assert len(inputs)==316
save(F/'prepare_02/completion.json',dict(status='PASS_REGISTERED_REAL_SPARSE_IMAGE_INPUTS_PREPARED',inputs=inputs,adopted_successful142_sources=True,remaining_first_sources=16,original_color_recipe_restored=True,utc=dt.datetime.now(dt.timezone.utc).isoformat()))
with (out/'input_qa_remaining.log').open('xb') as log:r=subprocess.run([PY,'-B',str(code),'input_qa_remaining'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
save(out/'input_qa_remaining.terminal.json',dict(exit_code=r.returncode))
assert r.returncode==0
save(out/'completion.json',dict(status='PASS_ALL316_FIRST_INPUT_QA_COLOR_REMAINING',elapsed=time.monotonic()-started,utc=dt.datetime.now(dt.timezone.utc).isoformat()))
