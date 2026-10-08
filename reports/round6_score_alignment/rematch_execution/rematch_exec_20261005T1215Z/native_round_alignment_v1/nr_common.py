"""Independent native-nearest input and exact unchanged-success authority."""
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
    rt=load(CAD/'runtime.py','nr_original_cad_runtime')
    student,old,frames,production=rt.bind_helpers()
    ex=load(CAD/'experiment.py','nr_original_cad_experiment')
    import context_contract as cc
    return rt,ex,cc,student,old,frames,production

def verify():
    lock=read(HERE/'source_lock.json')
    for p,s in lock['files'].items():require(sha(p)==s,'frozen native-nearest-alignment dependency changed: '+p)
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
    upstream=load(RUN/'b_prompt_recovery_v1/brec_common.py','nr_preserved_base_authority')
    rt,ex,cc,student,old,frames,production=helpers()
    return upstream.checked(base_path(scope,job,ix,cc),base_job(job),ix,'B0',ex)

def local_request(job,ix,arm,identity,ex):
    require(arm=='Q','only one native-nearest-alignment arm')
    return dict(kind='local',window=job['windows'][ix]['window'],arm='Q',
        prompt=ex.base_texts(None)['B0'],model=identity,max_input=16384,max_output=256,
        allow_empty=True,context_audit={},sampling_recipe='NATIVE_NEAREST64_SAME_COUNT_ENDPOINTS',
        video_size={'shortest_edge':4096,'longest_edge':25165824},
        spatial_resolution_tradeoff='SAME_FRAME_COUNT_PIXEL_GRID_AND_B0_PROMPT')

def done_path(scope,job,ix,arm,cc):
    require(arm=='Q','wrong new arm')
    if job['windows'][ix]['window']==job['windows'][ix]['base_window'] and scope!='rematch':
        return base_path(scope,job,ix,cc)
    if job['windows'][ix]['window']==job['windows'][ix]['base_window'] and scope=='rematch':
        return HERE/'rematch_01/aliases'/cc.digest(job['video_id'])/(str(ix)+'.json')
    return HERE/(scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'Q/done.json'

def checked(path,job,ix,arm,ex):
    if '/rematch_01/aliases/' in str(path):return checked_v14_alias(path,job,ix,ex)
    if '/context_advisory_v1/' in str(path):
        scope='nontest' if '/nontest_01/' in str(path) else 'developer'
        require(str(path)==str(base_path(scope,job,ix,ex.cc)) and
            job['windows'][ix]['window']==job['windows'][ix]['base_window'],'reuse requires original exact window')
        return checked_base(scope,job,ix)
    value=read(path);ex.checked_done(path,local_request(job,ix,arm,value['model_identity'],ex))
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=job['windows'][ix]['window']
    require(value['arm']=='Q' and value['window']==w and value['context_audit']=={},'wrong round_alignment window/arm/context')
    parsed,errors,_=parse_segments(value['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==value['parsed_segments'],'original unchanged validator differs')
    native=native_segment_ranges(parsed,value['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in native]==value['native_frame_realizability']['ranges'],'original native selection differs')
    raw=read(value['raw_receipt'])
    require(raw['raw_output']==value['raw_output'] and raw['overview_adapter_disabled'] is False,'new round_alignment raw identity')
    import math
    require(raw['selected_token_scores'] and all(isinstance(s,(float,int)) and math.isfinite(s) for s in raw['selected_token_scores']),'invalid actual token scores')
    return value

def checked_v14_alias(path,job,ix,ex):
    """Exact old success projection; no new raw response or model call."""
    alias=read(path);source=RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl'
    require(alias['source']==str(source) and sha(source)==alias['source_sha256'] and
        alias['window']==job['windows'][ix]['window']==job['windows'][ix]['base_window'] and
        alias['video_id']==job['video_id'] and alias['index']==ix,'V14 alias exact authority differs')
    row=next(x for x in (read_line(s) for s in source.read_text().splitlines() if s.strip()) if x['video_id']==job['video_id'])
    original=row['windows'][ix];require(ex.cc.digest(original)==alias['original_window_digest'],'old original response changed')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=alias['window'];parsed,errors,_=parse_segments(original['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==original['parsed_segments'] and original['output_valid'] and
        original['video_identity']==alias['actual_processor_identity'],'accepted V14 raw/input identity differs')
    ranges=native_segment_ranges(parsed,original['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in ranges]==original['native_frame_realizability']['ranges'],'old native selection differs')
    return dict(original,window=w,model_identity=read(HERE/'input_01/resume_manifest.json')['model_identity'],
        original_success_alias=str(path),new_model_calls=0,reused_original_T_temporal_window=True)

def read_line(s):return json.loads(s)

def v14_authority(student,model_identity):
    """Original full accepted bytes and model, before any projection is allowed."""
    source=RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl'
    stage=read(source.parent/'temporal.stage.json');complete=read(RUN/'teacher_student_autopilot_v14/student_01/student_completion.json')
    require(stage['status']=='PASS_TEMPORAL_EXECUTION' and stage['invalid_windows']==0 and stage['videos']==426 and
        stage['windows']==521 and stage['output_sha256']==sha(source) and stage['input_contract']==student.INPUT_CONTRACT and
        stage['selected_adapter_sha256']==complete['selected_adapter_sha256']==model_identity['adapter_sha256'],
        'V14 exact terminal/model/inputs differ')
    rows=[read_line(s) for s in source.read_text().splitlines() if s.strip()]
    require(len(rows)==426 and len({r['video_id'] for r in rows})==426 and sum(len(r['windows']) for r in rows)==521,'V14 full denominator')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    for row in rows:
        for original in row['windows']:
            duration=original['end_sec']-original['start_sec'];e=original['video_identity']
            parsed,errors,_=parse_segments(original['raw_output'],duration,allow_empty=True)
            require(not errors and parsed==original['parsed_segments'] and original['output_valid'] and
                0<e['input_tokens']<=16384 and not e['truncation'],'old V14 original validator/input bound')
            ranges=native_segment_ranges(parsed,e['window_source_pts_sec'],e['native_processor_identity']['window_start'],duration)
            require([list(x) for x in ranges]==original['native_frame_realizability']['ranges'],'old V14 native selection')
    return source,stage,{r['video_id']:r for r in rows}

def prepare_v14_aliases(jobs,ex,student):
    """New cross-consumer CPU handoff only for unchanged input windows."""
    source,stage,oldrows=v14_authority(student,read(HERE/'input_01/resume_manifest.json')['model_identity']);digest=sha(source)
    from transformers import AutoProcessor
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    from engine import prompt_for
    rt,_,cc,_,_,_,_=helpers()
    require(prompt_for(processor,True)==rt.prompt(processor,ex.base_texts(None)['B0']),'old/current B0 full processor text differs')
    aliases=[]
    for job in jobs:
        require(len(oldrows[job['video_id']]['windows'])==len(job['windows']),'V14 original natural windows differ')
        for ix,part in enumerate(job['windows']):
            if part['window']!=part['base_window']:continue
            original=oldrows[job['video_id']]['windows'][ix]
            require(original['start_sec']==part['start_sec'] and original['end_sec']==part['end_sec'],'old window domain differs')
            encoded,evidence=student.production_encode(processor,part['window'])
            require(evidence==original['video_identity'] and int(encoded['input_ids'].shape[1])==original['video_identity']['input_tokens'],'actual new-consumer cache input/processor mismatch')
            path=done_path('rematch',job,ix,'Q',cc)
            save(path,dict(status='PASS_EXACT_V14_UNCHANGED_REQUEST_CPU_HANDOFF',source=str(source),source_sha256=digest,
                video_id=job['video_id'],index=ix,window=part['window'],original_window_digest=cc.digest(original),
                actual_processor_identity=evidence,new_model_calls=0,new_optimizer_updates=0,
                original_cost_preserved=True,not_new_raw_or_generation=True))
            checked_v14_alias(path,job,ix,ex);aliases.append({'path':str(path),'sha256':sha(path)});del encoded
    save(HERE/'rematch_01/alias_handoff.json',dict(status='PASS_ALL_EXACT_UNCHANGED_V14_TEMPORAL_INPUTS',aliases=aliases,
        original_temporal_sha256=digest,new_model_calls=0,new_optimizer_updates=0,original_costs_preserved=True))
