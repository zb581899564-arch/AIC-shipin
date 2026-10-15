"""Read only existing real streams, metadata only; no model invocation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[2]
files=[]
for p in BASE.rglob('stream.jsonl'):
    if 'synthetic_contract_tests' in p.parts:continue
    raw=p.read_bytes();rows=[]
    for line in raw.splitlines():
        try:rows.append(json.loads(line))
        except (json.JSONDecodeError,UnicodeDecodeError):break
    bursts=[];current=[];response=None;active=set();maxactive=0;overlaps=[]
    for r in rows:
        t=r.get('step_update',{});kind=t.get('step_type');state=t.get('state');step=t.get('step_index')
        if kind=='agent_response':
            if current:bursts.append(dict(response_step=response,tools=current));current=[]
            if state=='DONE':response=step
        if kind=='tool':
            if state=='ACTIVE':
                if active:overlaps.append({'new_step':step,'existing_steps':sorted(active)})
                active.add(step);maxactive=max(maxactive,len(active))
            if state=='DONE':
                active.discard(step)
                params=t.get('tool_info',{}).get('parameters',{})
                current.append(dict(step=step,tool=t.get('tool_name'),path=params.get('AbsolutePath') or params.get('TargetFile')))
    if current:bursts.append(dict(response_step=response,tools=current))
    viewbursts=[b for b in bursts if len(b['tools'])>1 and all(t['tool']=='view_file' for t in b['tools'])]
    files.append(dict(path=str(p),sha256_at_read=hashlib.sha256(raw).hexdigest(),bytes_at_read=len(raw),max_tools_between_agent_responses=max([len(b['tools']) for b in bursts] or [0]),max_active_tools=maxactive,view_file_multi_tool_bursts=viewbursts,overlap_metadata=overlaps))
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='READ_ONLY_EXISTING_REAL_STREAM_METADATA_NOT_NEW_MODEL_TEST',files=files,new_model_calls=0,synthetic_streams_excluded=True,tool_batch_definition='Consecutive tool DONE events after one DONE agent_response with no intervening agent_response update',concurrency_definition='Multiple tool ACTIVE steps before earlier tool DONE',semantic_contents_not_exported=True)
out=ROOT/'tool_batch_existing_stream_evidence_v1.json'
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),streams=len(files),multi_view_streams=[f for f in files if f['view_file_multi_tool_bursts']],max_active_tools=max([f['max_active_tools'] for f in files] or [0])),ensure_ascii=False))
