"""Disjoint remaining sources; adopt completed first8 without repeating them."""
import os,pathlib,json,subprocess,datetime as dt,time
F=pathlib.Path('/home/inspur/aic_video_work/visual_pair_formal_20261018_v1')
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
code=F/'code_v3/visual_pair_formal_v3.py'
out=F/'cpu_remaining_chain_02';out.mkdir();started=time.monotonic()
def save(p,x):
    with p.open('x') as s:json.dump(x,s,indent=2)
def run(stage):
    with (out/(stage+'.log')).open('xb') as log:r=subprocess.run([PY,'-B',str(code),stage],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
    save(out/(stage+'.terminal.json'),dict(exit_code=r.returncode,utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    assert r.returncode==0,stage
assert (F/'prepare_02/pilot8_completion.json').exists()
assert not (F/'input_acceptance_pilot8.json').exists()
run('input_qa_pilot8')
reg=json.loads((F/'parallel_cpu_admission_03.json').read_text());processes=[]
for lo,hi in reg['disjoint_source_ranges']:
    log=(out/('shard_'+str(lo)+'_'+str(hi)+'.log')).open('xb')
    p=subprocess.Popen([PY,'-B',str(code),'prepare_shard',str(lo),str(hi)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
    processes.append((lo,hi,p,log))
results=[]
for lo,hi,p,log in processes:
    exit_code=p.wait();log.close();results.append(dict(lo=lo,hi=hi,exit_code=exit_code))
save(out/'prepare_shards_terminal.json',results)
assert all(r['exit_code']==0 for r in results),'Actual shard failure preserved; no automatic repeats'
pilot=json.loads((F/'prepare_02/pilot8_completion.json').read_text());inputs=pilot['inputs']
for lo,hi in reg['disjoint_source_ranges']:
    inputs+=json.loads((F/'prepare_02'/('shard_'+str(lo)+'_'+str(hi)+'_completion.json')).read_text())['inputs']
assert len(inputs)==316 and len({v['path'] for v in inputs})==316
save(F/'prepare_02/completion.json',dict(status='PASS_REGISTERED_REAL_SPARSE_IMAGE_INPUTS_PREPARED',inputs=inputs,processor_calls=316,new_purpose_native_decode_sources=158,adopted_first8=True,disjoint_workers=reg['workers'],utc=dt.datetime.now(dt.timezone.utc).isoformat()))
run('input_qa_remaining')
save(out/'completion.json',dict(status='PASS_ALL316_FIRST_INPUT_QA_DISJOINT_REMAINING',elapsed_seconds=time.monotonic()-started,utc=dt.datetime.now(dt.timezone.utc).isoformat()))
