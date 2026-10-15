"""Compact read-only progress from actual AGY tool terminal events."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
number=int(sys.argv[1]); assert number in (39,40)
R=Path(__file__).resolve().parent/'teacher_expansion'/('schema_recovery_22_23_v1' if number==39 else 'schema_recovery_23_continuation_v2')
a=R/f'call{number}'; p=a/'stream.jsonl'
rows=[]
if p.exists():
 for line in p.read_text(encoding='utf-8').splitlines():
  try: rows.append(json.loads(line))
  except json.JSONDecodeError: pass
steps=[x['step_update'] for x in rows if x.get('event')=='step_update' and x['step_update'].get('step_type')=='tool']
done={x['step_index']:x for x in steps if x.get('state')=='DONE'}
errors=[x for x in steps if x.get('state')=='ERROR']
value={'utc':datetime.now(timezone.utc).isoformat(),'CLI':number,'raw_bytes':p.stat().st_size if p.exists() else 0,
 'unique_DONE_tools':len(done),'ERROR_tools':errors,'last_tool_updates':steps[-1:],
 'fact_groups_created':len(list(a.glob(f'w{number-17}_group[0-9][0-9].json')))}
for name in ('terminal.json','completion.json','stopped.json','owned_stop_request.json'):
 if (a/name).exists():
  receipt=json.loads((a/name).read_text(encoding='utf-8'))
  value[name]={k:v for k,v in receipt.items() if k!='outputs'}
for name in ('audit.json','actual_terminal_cost.json'):
 if (a/name).exists():
  receipt=json.loads((a/name).read_text(encoding='utf-8'))
  value[name]={k:receipt[k] for k in ('status','actual_result_status','continuation_decision','wall_seconds','actual_usage') if k in receipt}
print(json.dumps(value,ensure_ascii=False))
