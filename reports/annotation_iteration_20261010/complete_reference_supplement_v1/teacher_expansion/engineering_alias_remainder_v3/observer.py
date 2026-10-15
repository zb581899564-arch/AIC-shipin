"""One observer, every completed scope immutable prefix, actual terminal cost."""
from common import ROOT,read,sha,save,key
from datetime import datetime,timezone
import json,subprocess,sys,time
def emit(event,**kw):print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event=event,**kw),ensure_ascii=False),flush=True)
def run(*args):
 r=subprocess.run([sys.executable,'-B',str(ROOT/'audit.py'),*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
 if r.returncode:emit('CPU_RECEIPT_FAILURE_NO_MODEL_RETRY',exit_code=r.returncode,stderr=r.stderr[-2000:]);raise SystemExit(r.returncode)
def main():
 last=0
 while True:
  active=None
  for n in (34,35,36):
   a=ROOT/f'call{n}'
   if not(a/'request.json').exists():continue
   rows=[]
   for line in(a/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines():
    try:rows.append(json.loads(line))
    except json.JSONDecodeError:break
   done=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('state')=='DONE']
   for w in read(a/'index.json')['windows']:
    target=a/f"w{w['job_index']:02d}_completed_scope_audit.json"
    finished=any(t.get('tool_name')=='write_to_file' and key(t.get('tool_info',{}).get('parameters',{}).get('TargetFile',''))==key(w['proposal_path']) for t in done)
    if finished and not target.exists():
     run('scope',n,w['job_index']);report=read(target);item=report['windows'][-1]
     emit('EACH_SCOPE_IMMUTABLE_PREFIX_SAVED',CLI=n,job_index=w['job_index'],status=item['status'],prefix=report['immutable_prefix'],audit_path=str(target),audit_sha256=sha(target),proposal_sha256=item['proposal_sha256'])
   if(a/'terminal.json').exists() and(a/'audit.json').exists() and not(a/'actual_terminal_receipt.json').exists():
    t=read(a/'terminal.json');audit=read(a/'audit.json');responses=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='agent_response'];usage={}
    for response in responses:
     for k,v in response.get('usage',{}).items():
      if isinstance(v,(int,float)):usage[k]=usage.get(k,0)+v
    receipt=dict(utc=datetime.now(timezone.utc).isoformat(),CLI=n,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),audit_sha256=sha(a/'audit.json'),actual_exit_code=t['exit_code'],actual_wall_seconds=t['wall_seconds'],actual_result_status=audit['actual_result_status'],actual_final_result_usage=audit['actual_result_usage'],observed_DONE_agent_responses=len(responses),observed_DONE_tools=len(done),observed_response_usage_field_sums=usage,usage_is_not_invoice=True,windows=[{k:w[k] for k in ('job_index','status','bound_rows','prior_native_facts_transferred','new_native_frames_planned','new_fact_groups_DONE','proposal_sha256')} for w in audit['windows']],same_index_read_count=audit['same_index_read_count'],context_read_steps=audit['context_read_steps'],actual_tool_ERRORS=audit['errored_tool_attempts'],cash_cost='UNKNOWN_NOT_ZERO',automatic_retry=False,training_admitted=False)
    save(a/'actual_terminal_receipt.json',receipt);emit('NATURAL_TERMINAL_REAL_COST_SAVED',CLI=n,receipt_sha256=sha(a/'actual_terminal_receipt.json'),**{k:receipt[k] for k in ('actual_exit_code','actual_wall_seconds','actual_result_status','windows','cash_cost')})
   if not(a/'terminal.json').exists():active=dict(CLI=n,DONE_tools=len(done))
  stopped=next((ROOT/p for p in ('stopped.json','awaiting_root.json','completion.json') if(ROOT/p).exists()),None)
  if stopped:emit('CONTROLLER_TERMINAL_OBSERVED',path=str(stopped),sha256=sha(stopped));return
  if time.monotonic()-last>=300:emit('ACTUAL_ACTIVE_PROGRESS',active=active);last=time.monotonic()
  time.sleep(10)
if __name__=='__main__':main()
