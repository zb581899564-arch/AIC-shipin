from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent
a=ROOT/f'call{int(sys.argv[1]):02d}';raw=(a/'stream.jsonl').read_bytes();rows=[]
for line in raw.splitlines():
    try:rows.append(json.loads(line))
    except (json.JSONDecodeError,UnicodeDecodeError):break
responses=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='agent_response']
tools=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='READONLY_ACTIVE_STREAM_CAPACITY_SNAPSHOT_NOT_TERMINAL',source=str(a/'stream.jsonl'),source_bytes_at_read=len(raw),source_sha256_at_read=hashlib.sha256(raw).hexdigest(),responses=len(responses),recent10_responses=responses[-10:],recent10_response_seconds=sum(r.get('duration_seconds',0) for r in responses[-10:]),recent10_tools=tools[-10:],error_message_updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message'],does_not_change_frozen_cap=True,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO')
with (a/'response_capacity_snapshot_v1.json').open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(a/'response_capacity_snapshot_v1.json'),sha256=hashlib.sha256((a/'response_capacity_snapshot_v1.json').read_bytes()).hexdigest(),recent10_response_seconds=v['recent10_response_seconds']),ensure_ascii=False))
