from common import ROOT,V5,read,sha,save
from datetime import datetime,timezone
import json,sys
def main(n):
 a=ROOT/f'call{n}';d=V5/f'call{n}';d.mkdir(exist_ok=True);target=d/'actual_terminal_cost.json'
 if target.exists():return
 t=read(a/'terminal.json');audit=read(a/'audit.json');responses=[];tools=[]
 for line in(a/'stream.jsonl').read_bytes().splitlines():
  try:r=json.loads(line)
  except Exception:break
  s=r.get('step_update',{})
  if s.get('state')=='DONE' and s.get('step_type')=='agent_response':responses.append(s)
  if s.get('state')=='DONE' and s.get('step_type')=='tool':tools.append(s)
 sums={}
 for response in responses:
  for k,v in response.get('usage',{}).items():
   if isinstance(v,(int,float)):sums[k]=sums.get(k,0)+v
 save(target,dict(utc=datetime.now(timezone.utc).isoformat(),CLI=n,actual_terminal=t,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),original_strict_audit_sha256=sha(a/'audit.json'),actual_result_status=audit['actual_result_status'],actual_final_result_usage=audit['actual_result_usage'],observed_DONE_agent_responses=len(responses),observed_DONE_tools=len(tools),observed_response_usage_field_sums=sums,usage_not_invoice=True,cash_cost='UNKNOWN_NOT_ZERO',old_cost_preserved=True,new_model_calls_in_CPU_recording=0))
 print(json.dumps(dict(event='ACTUAL_TERMINAL_COST_PRESERVED',CLI=n,path=str(target),sha256=sha(target),wall_seconds=t['wall_seconds'],exit_code=t['exit_code']),ensure_ascii=False),flush=True)
if __name__=='__main__':main(int(sys.argv[1]))
