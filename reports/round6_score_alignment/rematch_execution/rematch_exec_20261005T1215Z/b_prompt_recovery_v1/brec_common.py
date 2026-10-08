"""Independent namespace and exact success authority for historical B1."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
CAD=RUN/'context_advisory_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def utc():return datetime.now(timezone.utc).isoformat()

def save(path,value,fresh=True):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if fresh:
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    else:
        tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(p)

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def helpers():
    sys.path.insert(0,str(CAD))
    rt=load(CAD/'runtime.py','brec_original_cad_runtime')
    student,old,frames,production=rt.bind_helpers()
    ex=load(CAD/'experiment.py','brec_original_cad_experiment')
    import context_contract as cc
    return rt,ex,cc,student,old,frames,production

def verify():
    lock=read(HERE/'source_lock.json')
    for p,s in lock['files'].items():require(sha(p)==s,'frozen recovery dependency changed: '+p)
    return lock

def state(stage,**kw):
    value=dict(stage=stage,utc=utc(),pid=__import__('os').getpid(),new_optimizer_updates=0,
        new_32B_calls=0,official_score=None,uploaded=False,**kw)
    save(HERE/'progress.json',value,fresh=False);print(json.dumps(value),flush=True)

def local_request(job,ix,arm,identity,ex):
    return {'kind':'local','window':job['windows'][ix]['window'],'arm':arm,
        'prompt':ex.base_texts(None)[arm],'model':identity,'max_input':16384,'max_output':256,
        'allow_empty':arm!='B1','context_audit':{}}

def old_path(scope,job,ix,arm,cc):
    root=CAD/('developer_01' if scope=='developer' else scope+'_01')
    return root/'local'/cc.digest(job['video_id'])/str(ix)/arm/'done.json'

def done_path(scope,job,ix,arm,cc):
    original=old_path(scope,job,ix,arm,cc)
    if scope!='rematch' and original.exists():return original
    return HERE/(scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/arm/'done.json'

def checked(path,job,ix,arm,ex):
    value=read(path)
    ex.checked_done(path,local_request(job,ix,arm,value['model_identity'],ex))
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=job['windows'][ix]['window']
    require(value['arm']==arm and value['window']==w and value['context_audit']=={},'wrong historical arm/window/context')
    parsed,errors,_=parse_segments(value['raw_output'],w['window_duration_sec'],allow_empty=arm!='B1')
    require(not errors and parsed==value['parsed_segments'],'original historical arm validator differs')
    native=native_segment_ranges(parsed,value['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in native]==value['native_frame_realizability']['ranges'],'native source selection changed')
    raw=read(value['raw_receipt'])
    require(raw['raw_output']==value['raw_output'] and raw['overview_adapter_disabled'] is False,'original local raw differs')
    import math
    require(raw['selected_token_scores'] and all(isinstance(s,(float,int)) and math.isfinite(s) for s in raw['selected_token_scores']),'nonfinite original scores')
    return value
