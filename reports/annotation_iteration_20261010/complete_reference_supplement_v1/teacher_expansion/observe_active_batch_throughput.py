"""Performance observation only; never a scientific/admission gate or retry trigger."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
a=Path(sys.argv[1]).resolve();count=int(sys.argv[2]);raw=(a/'stream.jsonl').read_bytes();idx=json.loads((a/'index.json').read_text(encoding='utf-8-sig'));rows=[]
for line in raw.splitlines():
    try:rows.append(json.loads(line))
    except (json.JSONDecodeError,UnicodeDecodeError):break
def key(p):return str(Path(p).resolve()).casefold()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
owner=None;tools=[];responses={}
for r in rows:
    t=r.get('step_update',{})
    if t.get('state')!='DONE':continue
    if t.get('step_type')=='agent_response':owner=t.get('step_index');responses[owner]=dict(step=owner,duration_seconds=t.get('duration_seconds'),usage=t.get('usage'))
    if t.get('step_type')=='tool':
        p=t.get('tool_info',{}).get('parameters',{})
        tools.append(dict(step=t.get('step_index'),response_step=owner,tool=t.get('tool_name'),path=key(p.get('AbsolutePath') or p.get('TargetFile')),tool_duration_seconds=t.get('duration_seconds')))
window=idx['windows'][0];groups=[]
for g in window['groups'][:count]:
    paths=[key(f['path']) for f in g['frames']]
    seen=[t for t in tools if t['tool']=='view_file' and t['path'] in paths]
    writes=[t for t in tools if t['tool']=='write_to_file' and t['path']==key(g['output_path'])]
    assert len(seen)==4 and len(writes)==1, 'Requested milestone has not actually completed'
    owners=sorted({t['response_step'] for t in seen})
    groups.append(dict(group=g['group'],read_tools=seen,read_responses=[responses[o] for o in owners if o is not None],write_tool=writes[0],write_response=responses.get(writes[0]['response_step']),four_reads_in_one_response=len(owners)==1,observed_tool_order_exact=[t['path'] for t in seen]==paths,model_received_all_four_before_fact_request=writes[0]['response_step'] is not None and writes[0]['response_step']>max(t['step'] for t in seen),fact_output_sha256=sha(g['output_path'])))
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_BATCH_THROUGHPUT_OBSERVATION_ONLY_NOT_SCIENTIFIC_GATE',window_id=window['window_id'],job_index=window['job_index'],completed_groups=count,groups=groups,active_raw_source=str(a/'stream.jsonl'),active_raw_sha256_at_read=hashlib.sha256(raw).hexdigest(),active_raw_bytes_at_read=len(raw),observer_sha256=sha(Path(__file__)),parent_terminal_present=(a/'terminal.json').exists(),does_not_trigger_retry_or_change_labels=True,training_admitted=False,new_model_calls=0,cash_cost='UNKNOWN_NOT_ZERO')
out=a/f'first_{count:02d}_groups_batch_throughput.json'
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),groups=[dict(group=g['group'],read_response_steps=[r['step'] for r in g['read_responses']],write_response_step=g['write_tool']['response_step'],four_reads_in_one_response=g['four_reads_in_one_response'],read_model_seconds=sum(r.get('duration_seconds',0) for r in g['read_responses'])) for g in groups]),ensure_ascii=False))
