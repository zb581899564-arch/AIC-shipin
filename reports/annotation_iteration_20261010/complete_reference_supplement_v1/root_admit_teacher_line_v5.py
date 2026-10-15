"""Admit only fresh35/36 after actual completed34 and independent root media checks."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
R=Path(__file__).resolve().parent
V5=R/'teacher_expansion/engineering_alias_remainder_v5_line_representation_controller'
V4=V5.parent/'engineering_alias_remainder_v4_bootstrap_file'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p): return dict(path=str(p),sha256=sha(p))
pre=read(R/'root_teacher_line_v5_preparation_review.json')
assert pre['execution_binding_sha256']==sha(V5/'execution_code_binding.json')
assert pre['dry_run_sha256']==sha(V5/'dry_run_acceptance.json')
binding=read(V5/'execution_code_binding.json')
for p,s in {**binding['sources'],**binding['frozen_prior_inputs']}.items(): assert sha(p)==s,p
terminal=read(V4/'call34/terminal.json')
assert terminal['exit_code']==0 and terminal['child_process_created'] is True and terminal['stop_reason'] is None
assert terminal['stream_sha256']==sha(V4/'call34/stream.jsonl')
old=read(V4/'call34/audit.json'); proof=read(V5/'call34/line_representation_final.json')
assert (V4/'stopped.json').exists()
assert proof['status']=='ACCEPT_ACTUAL_SUPPLY_LINE_REPRESENTATION_ONLY_PENDING_ROOT_SEMANTIC'
assert proof['original_audit_sha256']==sha(V4/'call34/audit.json')
assert proof['terminal_sha256']==sha(V4/'call34/terminal.json')
fixed=proof['representation_audit']
assert fixed['actual_stream_SHA']==old['actual_stream_SHA']==terminal['stream_sha256']
assert fixed['actual_result_status']=='SUCCESS' and not fixed['reported_nonmedia_errors']
assert not fixed['tool_issues'] and not fixed['errored_tool_attempts'] and not fixed['unfinished_tool_attempts']
assert fixed['expected_core_tool_calls']==fixed['actual_core_tool_calls']==143
assert fixed['expected_supply_with_context']==fixed['actual_supply_with_context']==144
assert [w['job_index'] for w in fixed['windows']]==[17,18]
assert all(w['bound_rows']==64 and w['status'].startswith('PASS_') for w in fixed['windows'])
assert {i['reason'] for i in old['tool_issues']}=={'BOOTSTRAP_NOT_EXACTLY_ONCE_FIRST_FULL_DONE','BOOTSTRAP_ACK_MISSING_WRONG_OR_ORDER'}
media=[]
for n,name in [(17,'17_eyq_w04_lawful_observation_completion.json'),(18,'18_j0n_w02_lawful_observation_completion.json')]:
    p=R/name; x=read(p)
    assert x['original_pngs_delivered']==64 and x['effective_pngs_delivered']==8 and x['native_video_delivered']
    assert not x['tool_issues'] and not x['proposal_geometry_identity_issues']
    assert sha(x['prefix_audit']['path'])==x['prefix_audit']['sha256']
    assert sha(x['stream_prefix']['path'])==x['stream_prefix']['sha256']
    media.append(bind(p))
assert max(json.loads(s)['global_count'] for s in(V5.parent/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines())==34
assert not any((V4/f'call{n}/request.json').exists() for n in (35,36))
assert not (V5/'registered.json').exists()
out=V5/'root_start_admission.json'
value=dict(status='ROOT_APPROVED_START_LINE_REPRESENTATION_V5_FIXED_CLI35_36',
    utc=datetime.now(timezone.utc).isoformat(), execution_binding_sha256=sha(V5/'execution_code_binding.json'),
    dry_run_sha256=sha(V5/'dry_run_acceptance.json'), root_preparation_review=bind(R/'root_teacher_line_v5_preparation_review.json'),
    actual34_terminal=bind(V4/'call34/terminal.json'), actual34_original_strict_audit=bind(V4/'call34/audit.json'),
    actual34_new_representation_proof=bind(V5/'call34/line_representation_final.json'), root_actual_media_checks=media,
    original_v4_STOP_and_all_failures_preserved=True, current_actual_global_count=34, global_cap=36,
    fresh_dispatch_only={'35':[19,20],'36':[21,22,23]}, no_repeat34=True, no_retry35_36=True, no37=True,
    semantic_admission_separate=True, no_training_started_by_this_gate=True, cash_cost='UNKNOWN_NOT_ZERO')
with out.open('x',encoding='utf-8') as f: json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(out),ensure_ascii=False))
