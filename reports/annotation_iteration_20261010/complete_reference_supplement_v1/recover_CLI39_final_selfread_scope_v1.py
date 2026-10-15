"""Typed ROOT scope recovery; preserves whole rejection and all original costs."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent;N=R/'teacher_expansion/schema_recovery_22_23_v1';A=N/'call39'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
review=R/'plan_review/CLI39_final_selfread_independent_scope_recovery_v1.json'
assert sha(review)=='ee71bcb64f79cf4f01600ee5ec76c82de48bcc1e395471f01f20d889340ef387'
assert read(review)['status']=='PASS_INDEPENDENT_CLI39_FINAL_SELFREAD_COMPLETE_SCOPE_RECOVERY_NOT_TRAINING'
t,w,s=map(read,[A/'terminal.json',A/'audit.json',A/'w22_completed_scope_audit.json'])
assert t['child_process_created'] and t['exit_code']==0 and t['stop_reason'] is None and t['launch_exception'] is None
assert w['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST' and w['actual_result_status']=='SUCCESS'
assert w['continuation_decision']['issues']==['TOOL_AFTER_FINAL_PROPOSAL_TERMINAL_INSTRUCTION']
assert w['continuation_decision']['whole_success'] and not w['continuation_decision']['eligible']
assert not any(w[k] for k in ('immutable_drift','rewritten_output_attempts','repeated_media_attempts','tool_issues'))
assert s['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC' and s['windows'][-1]['bound_rows']==64
for key in ('tool_issues','additional_scope_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'):assert not s[key]
assert sha(A/'stream.jsonl')==t['stream_sha256']
assert read(A/'actual_terminal_cost.json')['terminal_sha256']==sha(A/'terminal.json')
prefix=Path(s['immutable_prefix']['path']);assert sha(prefix)==s['immutable_prefix']['sha256']
assert (A/'stream.jsonl').read_bytes().startswith(prefix.read_bytes())
for x in s['immutable_actual_outputs']:assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
rows=[json.loads(x) for x in (A/'stream.jsonl').read_text(encoding='utf-8').splitlines()]
tools=[x['step_update'] for x in rows if x.get('step_update',{}).get('step_type')=='tool']
last=[x for x in tools if x['step_index']==204]
assert [x['state'] for x in last]==['ACTIVE','DONE'] and all(x['tool_name']=='view_file' and Path(x['tool_info']['parameters']['AbsolutePath'])==A/'w22_proposal.json' for x in last)
assert not any(x['step_index']>204 for x in tools)
wrapper=R/'22_yi4_w03_lawful_observation_completion_CLI39_v1.json';lawful=read(wrapper)
assert sha(wrapper)=='9635f8ae73ab16a9a6936ceead46fa540d267ce879155d90bb242d23fcf1d34a'
assert lawful['global_CLI']==39 and lawful['window_id']=='Yi4Ij2NM7U4:SLOT6:3' and lawful['ordered_actual_core_count']==128
ledger=[json.loads(x) for x in (R/'teacher_expansion/global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines()]
assert max(x['global_count'] for x in ledger)==39
terms=[x for x in ledger if x['global_count']==39 and x['event']=='TERMINAL']
assert len(terms)==1 and terms[0]['terminal_sha256']==sha(A/'terminal.json') and terms[0]['raw_sha256']==sha(A/'stream.jsonl')
value=dict(status='ROOT_CONFIRMED_CLI39_NATURAL_SUCCESS_VALID_JOB22_SCOPE_ONLY_FINAL_PROPOSAL_SELFREAD_WHOLE_REJECT_PRESERVED',
 utc=datetime.now(timezone.utc).isoformat(),CLI=39,window_id=lawful['window_id'],ROOT_actual_scope_independently_verified=True,
 old_whole_REJECTED_preserved=True,allowed_whole_issue='TOOL_AFTER_FINAL_PROPOSAL_TERMINAL_INSTRUCTION',final_proposal_selfread_step=204,
 bindings={str(A/n):sha(A/n) for n in ('terminal.json','stream.jsonl','audit.json','w22_completed_scope_audit.json','actual_terminal_cost.json')},
 lawful_observation_binding=bound(wrapper),independent_actual_scope_review=bound(review),
 semantic_adjudication_still_required=True,training_admitted=False,old_40_gate_not_overridden=True,
 new_route_only='EXPLICIT_FRESH_CLI40_JOB23_AFTER_NEW_SOURCE_GATE',new_model_calls=0,new_optimizer_updates=0)
p=R/'schema_recovery_CLI39_final_selfread_root_recovery_v1.json'
with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps(bound(p),ensure_ascii=False))
