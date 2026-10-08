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
    rt=load(CAD/'runtime.py','nd_original_cad_runtime')
    student,old,frames,production=rt.bind_helpers()
    ex=load(CAD/'experiment.py','nd_original_cad_experiment')
    import context_contract as cc
    return rt,ex,cc,student,old,frames,production

def verify():
    lock=read(HERE/'source_lock.json')
    for p,s in lock['files'].items():require(sha(p)==s,'frozen nested-density dependency changed: '+p)
    return lock

def state(stage,**kw):
    value=dict(stage=stage,utc=utc(),pid=__import__('os').getpid(),new_optimizer_updates=0,
        new_32B_calls=0,official_score=None,uploaded=False,**kw)
    save(HERE/'progress.json',value,fresh=False);print(json.dumps(value),flush=True)

def base_job(job):
    import copy
    value=copy.deepcopy(job)
    for part in value['windows']:
        part['window']=part['base_window'];part.pop('base_window',None)
    return value

def base_path(scope,job,ix,cc):
    return CAD/('developer_01' if scope=='developer' else scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'B0/done.json'

def checked_base(scope,job,ix):
    upstream=load(RUN/'b_prompt_recovery_v1/brec_common.py','nd_preserved_base_authority')
    rt,ex,cc,student,old,frames,production=helpers()
    return upstream.checked(base_path(scope,job,ix,cc),base_job(job),ix,'B0',ex)

def local_request(job,ix,arm,identity,ex):
    require(arm=='D','only one nested-density arm')
    return dict(kind='local',window=job['windows'][ix]['window'],arm='D',
        prompt=ex.base_texts(None)['B0'],model=identity,max_input=16384,max_output=256,
        allow_empty=True,context_audit={},sampling_recipe='BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS',
        video_size={'shortest_edge':4096,'longest_edge':25165824},
        spatial_resolution_tradeoff='SAME_TOTAL_VIDEO_PIXEL_BUDGET_ACTUAL_GRID_RECORDED_NOT_ASSUMED_EQUAL')

def done_path(scope,job,ix,arm,cc):
    require(arm=='D','wrong new arm')
    return HERE/(scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'D/done.json'

def checked(path,job,ix,arm,ex):
    value=read(path);ex.checked_done(path,local_request(job,ix,arm,value['model_identity'],ex))
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=job['windows'][ix]['window']
    require(value['arm']=='D' and value['window']==w and value['context_audit']=={},'wrong density window/arm/context')
    parsed,errors,_=parse_segments(value['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==value['parsed_segments'],'original unchanged validator differs')
    native=native_segment_ranges(parsed,value['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in native]==value['native_frame_realizability']['ranges'],'original native selection differs')
    raw=read(value['raw_receipt'])
    require(raw['raw_output']==value['raw_output'] and raw['overview_adapter_disabled'] is False,'new density raw identity')
    import math
    require(raw['selected_token_scores'] and all(isinstance(s,(float,int)) and math.isfinite(s) for s in raw['selected_token_scores']),'invalid actual token scores')
    return value
