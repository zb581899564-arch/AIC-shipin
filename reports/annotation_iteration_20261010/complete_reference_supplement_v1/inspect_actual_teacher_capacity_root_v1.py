"""Read actual historical terminal/raw, not a new model or runtime capacity guarantee."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).parent;B=R/'teacher_expansion'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=[]
for rel in ('capacity_v4_tool_batches/call03','remaining_CLI32_36_literal_paths_v1/call06','capacity_v3_network/call01','engineering_alias_remainder_v4_bootstrap_file/call34'):
 a=B/rel;t=read(a/'terminal.json');assert sha(a/'stream.jsonl')==t['stream_sha256']
 rows=[json.loads(x) for x in (a/'stream.jsonl').read_bytes().splitlines() if x.strip()]
 latest={}
 for r in rows:
  u=r.get('step_update',{})
  if u.get('step_type')=='tool':latest[u['step_index']]=u
 done=[u for u in latest.values() if u.get('state')=='DONE']
 out.append(dict(CLI=t['CLI_after'],terminal=dict(path=str(a/'terminal.json'),sha256=sha(a/'terminal.json')),raw=dict(path=str(a/'stream.jsonl'),sha256=sha(a/'stream.jsonl')),wall_seconds=t['wall_seconds'],stop_reason=t['stop_reason'],DONE_tool_count=len(done),seconds_per_DONE_tool=t['wall_seconds']/len(done),linear_502_seconds=t['wall_seconds']*502/len(done),linear_202_seconds=t['wall_seconds']*202/len(done),linear_302_seconds=t['wall_seconds']*302/len(done),new_model_calls=0))
assert out[0]['DONE_tool_count']==181 and out[1]['DONE_tool_count']==191 and out[2]['DONE_tool_count']==134
p=R/'root_actual_teacher_capacity_v1.json'
v=dict(status='ACTUAL_HISTORICAL_FRESH_CAPACITY_RISK_EVIDENCE_NOT_RUNTIME_GUARANTEE',utc=datetime.now(timezone.utc).isoformat(),actual_cases=out,sole_36_five_windows_502_tools_7200_s_not_supported_as_robust_capacity=True,old34_is_partially_inherited_not_five_fresh_baseline=True,required_average_seconds_per_tool_502=7200/502,conditional_two_call_2_plus_3_capacity_has_more_margin=True,user_numeric_call_cap_not_asserted=True,new_model_calls=0,new_optimizer_updates=0,root_verifier=dict(path=str(Path(__file__)),sha256=sha(__file__)))
with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(p),sha256=sha(p),cases=[{k:r[k] for k in ('CLI','wall_seconds','DONE_tool_count','linear_502_seconds','linear_202_seconds','linear_302_seconds')} for r in out]),ensure_ascii=False))

