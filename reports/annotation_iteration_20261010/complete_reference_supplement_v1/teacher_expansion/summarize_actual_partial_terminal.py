from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
a=Path(sys.argv[1]).resolve()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=read(a/'terminal.json');au=read(a/'audit.json');idx=read(a/'index.json')
assert t['stream_sha256']==sha(a/'stream.jsonl')
rows=[json.loads(s) for s in (a/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
responses=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='agent_response']
tools=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
wins=[]
for w,report in zip(idx['windows'],au['windows']):
    writes=[s.get('tool_info',{}).get('parameters',{}).get('TargetFile') for s in tools if s.get('tool_name')=='write_to_file']
    donegroups=[g['group'] for g in w['groups'] if g['output_path'] in writes]
    wins.append(dict(job_index=w['job_index'],window_id=w['window_id'],structure_status=report['status'],actual_native_DONE=len(report['native_read_done']),actual_fact_group_write_DONE=donegroups,actual_clip_DONE=report['clip_read_done'],actual_student_preview_DONE=len(report['student_preview_read_done']),proposal_write_DONE=w['proposal_path'] in writes,proposal_sha256=report['proposal_sha256'],remaining_native_frames=[f['frame_id'] for g in w['groups'] for f in g['frames'] if f['frame_id'] not in {f['frame_id'] for f in report['native_read_done']}],training_admitted=False))
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_TERMINAL_OBSERVED_USAGE_NOT_BILLING_NOT_SEMANTIC_VERDICT',CLI_after=t['CLI_after'],terminal=t,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),audit_sha256=sha(a/'audit.json'),windows=wins,observed_DONE_agent_responses=len(responses),observed_DONE_tools=len(tools),observed_response_usage_field_sums={k:sum(s.get('usage',{}).get(k,0) for s in responses) for k in ('input_tokens','output_tokens','thinking_tokens','cache_read_tokens','total_tokens')},usage_field_sums_are_observed_stream_only_not_final_invoice=True,cash_cost='UNKNOWN_NOT_ZERO',error_message_updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message'],unfinished_tool_attempts=au.get('unfinished_tool_attempts'),independent_completed_first_scope_preserved=(a/f"w{idx['windows'][0]['job_index']:02d}_completed_scope_audit.json").exists(),automatic_retry=False)
out=a/'actual_partial_terminal_receipt.json'
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),CLI_after=t['CLI_after'],windows=wins,observed_response_count=len(responses)),ensure_ascii=False))
