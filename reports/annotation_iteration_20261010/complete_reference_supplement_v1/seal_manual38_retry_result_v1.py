"""Record actual manual retry, preserved failure and one accepted finite reference."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent
C=R/'teacher_expansion/manual_CLI38_retry_v1/call38'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
t,a,cost=read(C/'terminal.json'),read(C/'audit.json'),read(C/'actual_terminal_cost.json')
stop=read(C/'owned_stop_request.json');reg=read(R/'denominator24_v19.json')
assert t['exit_code']==1 and t['stop_reason']=='OWNED_SCHEMA_OR_RAW_STOP_NO_RETRY'
assert a['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST' and not a['continuation_decision']['further_CLI_allowed']
assert cost['terminal_sha256']==bind(C/'terminal.json')['sha256'] and cost['raw_sha256']==bind(C/'stream.jsonl')['sha256']
assert stop['actual_tool_step']==203 and stop['reason']['reason']=='ORIGINAL_CLOSED_FACT_SCHEMA_REJECTED'
bad=read(C/'first_failed_fact_original_bytes.json')
assert isinstance(bad,list) and len(bad)==4 and [x['slot'] for x in bad]==list(range(4))
assert Path(stop['failed_original_payload_copy']).read_bytes()==(C/'w22_group04.json').read_bytes()
rows=[json.loads(x) for x in (C/'stream.jsonl').read_bytes().splitlines()]
done={}
for row in rows:
    s=row.get('step_update',{})
    if s.get('step_type')=='tool' and s.get('state')=='DONE':done[s['step_index']]=s
assert len(done)==140 and not any(row.get('step_update',{}).get('state')=='ERROR' for row in rows)
ledger=R/'teacher_expansion/global_CLI_ledger.jsonl'
entries=[json.loads(x) for x in ledger.read_bytes().splitlines()]
terms=[x for x in entries if x['event']=='TERMINAL' and x['global_count']==38]
assert len(terms)==1 and terms[0]['terminal_sha256']==bind(C/'terminal.json')['sha256']
assert max(x['global_count'] for x in entries)==38
assert (reg['qualified_references'],reg['rejected_references'],reg['pending_references'],reg['accepted_train_windows'])==(18,4,2,8)
proof=read(R/'21_cjibt_w16_complete_reference_CLI38_v1_acceptance.json')
assert proof['status']=='PASS_BOUND_COMPLETE_FINITE_REFERENCE_NOT_BATCH_ADMISSION' and not proof['verified']['admitted']
result=dict(status='MANUAL38_API_ACCESS_RECOVERED_ONE_FINITE_REFERENCE_ACCEPTED_W22_SCHEMA_STOP_W23_PENDING_NOT_TRAINING',
 utc=datetime.now(timezone.utc).isoformat(),human_authorization=bind(R/'manual_CLI38_user_retry_authorization_v1.json'),
 actual_model='gemini-3.8-flash-high',API_access_observed=True,
 actual_successful_tool_DONE=140,actual_media_DONE=97,actual_native_images_DONE=88,
 actual_tool_ERROR=0,first_schema_failure=dict(job_index=22,group=4,actual_DONE_step=203,
 original_payload_type='list',expected_outer_object_keys=['group','items'],
 diagnosis='Bare four-item array omitted the required group/items outer object; the closed original validator raised TypeError on dict array entries.',
 original_payload=bind(C/'first_failed_fact_original_bytes.json'),validation=bind(C/'w22_g04_immediate_fact_schema.json'),
 later_grace_output_group05_preserved=bind(C/'w22_group05.json'),no_automatic_reformat_or_acceptance=True),
 windows={'21':dict(completed_scope=bind(C/'w21_completed_scope_audit.json'),semantic_adjudication=bind(R/'21_cjibt_w16_root_eval_decision_CLI38_v1.json'),
 reference=bind(R/'21_cjibt_w16_complete_reference_CLI38_v1.json'),original_contract_acceptance=bind(R/'21_cjibt_w16_complete_reference_CLI38_v1_acceptance.json'),
 raw_teacher_all_NO_not_adopted=True,finite_preteacher_events=3,consequential_UNKNOWN_preserved=True,training_admitted=False),
 '22':dict(native_images_DONE=24,full_native64_completed=False,full_proposal_completed=False,reference_admitted=False),
 '23':dict(started=False,reference_admitted=False)},
 terminal=bind(C/'terminal.json'),whole_audit=bind(C/'audit.json'),owned_stop=bind(C/'owned_stop_request.json'),
 actual_cost=bind(C/'actual_terminal_cost.json'),wall_seconds=t['wall_seconds'],cash_cost='UNKNOWN_NOT_ZERO',
 unique_global_terminal_verified=True,ledger=bind(ledger),registry=bind(R/'denominator24_v19.json'),
 qualified_references=18,rejected_references=4,pending_references=2,accepted_train_windows=8,
 new_optimizer_updates=0,new_submission_zip=False,no39=True,automatic_retry=False,
 ROOT_scope_verifier_erratum=dict(original_helper=bind(R/'accept_teacher_manual38_scope_binding_v1.py'),
 preserved_failure_log=bind(R/'plan_review/ROOT_manual38_w21_wrapper_execution_v1.log'),
 correction_helper=bind(R/'accept_teacher_manual38_scope_binding_v2.py'),
 correction='Only JSON-normalize CPU tuple/list representation for equality to persisted scope; scalar values and all strict checks unchanged.',
 first_attempt_stdout_session_metadata_not_retained=True,successful_execution_log=bind(R/'plan_review/ROOT_manual38_w21_wrapper_execution_v2.log')),
 next_work='Before another model call: explicit new bounded dispatch record, per-group closed schema reminder, preserve completed21 and all old failures; complete22/23 and all evaluation reference gates before actual Linux preflight/training.')
out=R/'manual38_retry_actual_result_v1.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps(bind(out),ensure_ascii=False))
