"""Actual reference sufficiency, never a training/model or quality metric."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
R=Path(__file__).parent
OLD=R.parent/'slot6_silver24_v1'
V=R/'teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
registry=read(R/'denominator24_v16.json');plan=read(OLD/'source_window_plan.json')
jobs={j['window']['window_id']:j for j in plan['jobs']};references={}
assert len(jobs)==len(registry['records'])==24
for k,row in registry['records'].items():
 if row.get('reference'):
  p=Path(row['reference']['path']);assert sha(p)==row['reference']['sha256'];references[k]=read(p)
sys.path.insert(0,str(R/'runtime'));from scientific_gate import reference_coverage
sys.path.insert(0,str(OLD));import quality_contract
coverage_exception=None
try:coverage=reference_coverage(jobs,references,quality_contract)
except ValueError as exc:coverage=None;coverage_exception=str(exc)
assert coverage is None and coverage_exception
classification=read(V/'actual_CLI35_terminal_classification_v1.json')
for field in ('terminal','raw','whole_audit','cost'):
 assert sha(classification[field]['path'])==classification[field]['sha256']
raw=read(V/'call35/terminal.json');assert raw['wall_seconds']==classification['actual_wall_seconds']
assert classification['actual_ACK_written'] is False
assert sum(classification[k] for k in ('actual_native_reads','actual_fact_groups','actual_clips','actual_effective_previews','actual_proposals'))==0
assert not list(V.parent.glob('*/call36/request.json'))
roles={}
for role in ('train','process_dev','locked_evaluation'):
 planned=[k for k,j in jobs.items() if j['role']==role]
 accepted=[k for k in planned if k in references]
 missing=[dict(job_index=i,window_id=j['window']['window_id'],source_group=j['source_group']) for i,j in enumerate(plan['jobs']) if j['role']==role and j['window']['window_id'] not in references]
 roles[role]=dict(planned=len(planned),accepted=len(accepted),accepted_sources=len({jobs[k]['source_group'] for k in accepted}),missing=missing)
assert roles['locked_evaluation']['planned']==8 and roles['locked_evaluation']['accepted']==3
assert [m['job_index'] for m in roles['locked_evaluation']['missing']]==list(range(19,24))
report=dict(status='STOP_CURRENT_FULL_REFERENCE_ADMISSION_NO_GPU_NEW_ENGINEERING_PREPARATION_ONLY',utc=datetime.now(timezone.utc).isoformat(),registry=bind(R/'denominator24_v16.json'),actual_CLI35_classification=bind(V/'actual_CLI35_terminal_classification_v1.json'),actual_CLI35_whole_REJECT_preserved=True,global_teacher_calls=35,global_cap=36,unused_CLI36_not_started=True,missing_evaluation_gate_actual_exception=coverage_exception,reference_denominator=roles,training_reference_admission_is_not_complete_batch_admission=True,source_transfer_pending_user_reply=True,new_optimizer_updates=0,new_model_calls_by_this_verifier=0,new_native_decodes=0,new_submission_zip=False,root_verifier=bind(__file__),next_engineering_candidate='New independent front-looking CLI36-only 19..23 route, 7200s cap unchanged; preparation review and separate ROOT gate required; old36 controller stays STOP')
p=R/'root_cli35_stop_full_reference_gap_v1.json'
with p.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(p),sha256=sha(p),role_counts={k:{x:v[x] for x in ('planned','accepted','accepted_sources')} for k,v in roles.items()},actual_gate_error=coverage_exception),ensure_ascii=False))

