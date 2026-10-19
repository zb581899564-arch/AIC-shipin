"""First independent CPU output QA for every formal visual comparison."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import datetime as dt, hashlib, json, math, pathlib
from transformers import AutoTokenizer
W=pathlib.Path('/home/inspur/aic_video_work');F=W/'visual_pair_formal_20261018_v1'
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
JOB='visual_pair_formal158_base_order316_20261018_v1'
def read(p):return json.loads(pathlib.Path(p).read_text())
def ref(p):
    p=pathlib.Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def bound(r):
    p=pathlib.Path(r['path']);a=ref(p);assert a['sha256']==r['sha256'] and ('bytes' not in r or a['bytes']==r['bytes']);return p
def save(p,x):
    with pathlib.Path(p).open('x') as stream:json.dump(x,stream,ensure_ascii=False,indent=2,allow_nan=False)
assert dt.datetime.now(dt.timezone.utc)<dt.datetime(2026,10,18,16,tzinfo=dt.timezone.utc)
reg=read(F/'registration_01.json');resource_path=RUN/'controller'/(JOB+'.resource.json');resource=read(resource_path)
assert resource['status']=='completed' and resource['exit_code']==0 and resource['name']==JOB
ledger=[json.loads(line) for line in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
matches=[r for r in ledger if r.get('name')==JOB];assert len(matches)==1 and matches[0]==resource
completion=read(F/'gpu_01/completion.json');assert completion['status']=='PASS_REGISTERED_ACTUAL_BASE_PREFERENCES_NO_OPTIMIZER'
assert len(completion['outputs'])==316 and completion['actual_loaded_parameters']==8782459120
accepted=read(F/'input_acceptance_01.json')['inputs'];assert len(accepted)==316
cfg=read(bound(reg['model_config_ref']));tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
generation=read(bound(reg['processor_asset_refs']['generation_config.json']));eos=generation['eos_token_id'];eos=[eos] if isinstance(eos,int) else eos
outputs={};records=[]
for value in completion['outputs']:
    done=read(bound(value));proof=read(bound(done['input_ref']));raw=read(bound(done['raw_ref']))
    request=read(pathlib.Path(value['path']).parent/'request.json')
    assert done['input_ref'] in accepted and done['status']=='ACTUAL_MODEL_PREFERENCE_OK'
    assert request['input_ref']==done['input_ref'] and request['input_signature']==proof['tensor_signature'] and request['role']=='BASE_ALL144_ADAPTERS_DISABLED' and request['model_call_begin']
    assert raw['actual_model_call'] and raw['role']=='BASE_DISABLED' and raw['ids'][-1] in eos
    assert len(raw['ids'])==len(raw['scores']) and all(math.isfinite(float(v)) for v in raw['scores'])
    text=tokenizer.decode(raw['ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
    assert text==raw['raw'] and json.loads(text)=={'choice':done['choice']} and done['choice'] in ['A','B','TIE','NEITHER']
    assert done['sid']==proof['sid'] and done['order']==proof['order']
    key=(done['sid'],done['order']);assert key not in outputs;outputs[key]=done['choice'];records.append(value)
assert len(outputs)==316
decisions=[]
for case in reg['cases']:
    ab=outputs[(case['sid'],'AB')];ba=outputs[(case['sid'],'BA')]
    decisions.append(dict(sid=case['sid'],AB=ab,BA=ba,keep=ab=='B' and ba=='A'))
kept=[d['sid'] for d in decisions if d['keep']]
result=dict(status='PASS_ALL316_FIRST_INDEPENDENT_RAW_TOKEN_PARSER_REQUEST_ROLE_QA',kept_sids=kept,rejected_sources=158-len(kept),decisions=decisions,all316ref=records,gpu_completion_ref=ref(F/'gpu_01/completion.json'),resource_ref=ref(resource_path),input_acceptance_ref=ref(F/'input_acceptance_01.json'),registration_ref=ref(F/'registration_01.json'),labels_or_official_metric_read=False,new_model_or_processor_calls=0,utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(F/'output_acceptance_01.json',result)
print(json.dumps(dict(status=result['status'],kept=len(kept),rejected=158-len(kept))))
