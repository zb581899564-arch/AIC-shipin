"""Accept actual post-error tool completion, preserving all transport failures."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
P=ROOT/'teacher_expansion/capacity_v3_network/resume_w11_network_recovery_v1'
PARENT=ROOT/'teacher_expansion/call00'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def norm(p):return str(Path(p).resolve()).casefold()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
a=read(P/'audit.json');receipt=read(P/'current_turn_completion_error_receipt.json');freeze=read(P/'freeze.json');terminal=read(P/'terminal.json')
assert a['status']=='STOP_RESUME_STRUCTURE_OR_COMPLETION_FAILED_KEEP_RAW'
for p,digest in freeze['inputs'].items():assert sha(Path(p))==digest
for name,field in [('stream.jsonl','raw_sha256'),('terminal.json','terminal_sha256'),('request.json','request_sha256'),('audit.json','original_audit_sha256')]:assert sha(P/name)==receipt[field]
assert terminal['exit_code']==0 and terminal['stop_reason'] is None
assert receipt['actual_result_status']=='ERROR' and not receipt['tool_issues'] and not receipt['schema_issues']
assert not a['tool_issues'] and not a['schema_issues']
assert a['inherited_native_pngs']==64 and a['inherited_clip_reads']==1 and a['teacher_preview_frames_total']==8
assert a['logical_proposal_count']==1 and sha(P/'w03_proposal.json')==a['proposal_sha256']
tools=receipt['actual_new_tools'];errors=receipt['current_stream_error_message_steps']
assert len(tools)==8 and all(t['state']=='DONE' for t in tools)
assert [t['step_index'] for t in tools]==[175,177,179,181,183,185,187,189]
assert len(errors)==1 and errors[0]['step_index']==173 and errors[0]['step_index']<tools[0]['step_index']
assert receipt['current_stream_agent_response_steps'][-1]['step_index']==190
reads={norm(x) for x in freeze['read_whitelist']+freeze['self_read_whitelist']}
writes={norm(x) for x in freeze['write_whitelist']}
for t in tools:
    par=t['tool_info']['parameters']
    if t['tool_name']=='view_file':assert norm(par['AbsolutePath']) in reads
    elif t['tool_name']=='write_to_file':assert norm(par['TargetFile']) in writes
    else:raise ValueError('Unexpected tool')
obs=ROOT.parent/'slot6_silver24_v1/observations/03_AwmHb44_ouw_W11'
m=read(obs/'manifest.json');student=read(obs/'student_views/receipt.json')
supplied={norm(r['path']) for r in a['inherited_actual_supply']+a['actual_new_supply'] if r['tool']=='view_file'}
for r in m['frames']:assert norm(r['path']) in supplied and sha(Path(r['path']))==r['png_sha256']
assert norm(m['clip_path']) in supplied and sha(Path(m['clip_path']))==m['clip_sha256']
preview_ids=set(a['inherited_student_preview_frames']+a['new_student_preview_frames']);assert len(preview_ids)==8
for r in student['frames']:
    if r['frame_id'] in preview_ids:assert norm(r['path']) in supplied and sha(Path(r['path']))==r['png_sha256']
completion=dict(status='PASS_ACTUAL_COMPLETE_LAWFUL_MEDIA_AND_PROPOSAL_WITH_EARLY_TRANSPORT_ERROR_PRESERVED',utc=datetime.now(timezone.utc).isoformat(),
 window_id=m['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,
 tool_issues=[],proposal_geometry_identity_issues=[],
 prior_failed_audit=bound(P/'audit.json'),current_turn_completion=bound(P/'current_turn_completion_error_receipt.json'),
 prior_timeout_terminal=bound(PARENT/'terminal.json'),prior_timeout_raw=bound(PARENT/'stream.jsonl'),
 resume_terminal=bound(P/'terminal.json'),resume_raw=bound(P/'stream.jsonl'),proposal=bound(P/'w03_proposal.json'),freeze=bound(P/'freeze.json'),
 actual_AGY_result_status='ERROR',early_error_step=173,subsequent_completed_tools=8,last_completed_agent_response=190,
 error_attribution='Current turn early request failed; the actual subsequent completed tools and single proposal are separately accepted. No claim that AGY result was SUCCESS.',
 completed_work_after_error_not_repeated=True,media_success_identity_preserved=True,whole_domain_NO_is_real_generated_proposal_not_failure_fallback=True,
 semantic_correctness='UNVERIFIED_PENDING_ROOT_REFERENCE',training_admitted=False,human_gold=False,new_model_calls='REAL_GENERATIVE_USAGE_RECORDED_IN_ORIGINAL_RECEIPT',CLI_after=26,cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0)
save(ROOT/'03_w11_lawful_observation_completion.json',completion)
print(json.dumps(dict(status=completion['status'],training_admitted=False)))
