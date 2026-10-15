"""Preserve exact terminal error evidence without retry or media observation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE/'remaining_CLI33_36_same_index_selfcheck_v2';A=ROOT/'call07'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
idx=read(A/'index.json');terminal=read(A/'terminal.json');audit=read(A/'audit.json');receipt=read(A/'actual_partial_terminal_receipt.json')
assert sha(A/'stream.jsonl')==terminal['stream_sha256']
rows=[json.loads(s) for s in (A/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'];latest={s['step_index']:s for s in updates}
errors=[s for s in latest.values() if s.get('state')=='ERROR'];w=next(w for w in idx['windows'] if w['job_index']==17);g=w['groups'][8]
comparisons=[]
for s,f in zip(errors,g['frames'][:3]):
 actual=s['tool_info']['parameters']['AbsolutePath'];assert actual!=f['path']
 assert Path(f['path']).exists() and sha(f['path'])==f['png_sha256']
 comparisons.append(dict(step=s['step_index'],actual_wrong_AbsolutePath=actual,expected_literal_AbsolutePath=f['path'],expected_png_current_sha256=sha(f['path']),expected_png_frozen_sha256=f['png_sha256'],expected_png_exists=True,actual_wrong_path_exists=Path(actual).exists(),actual_ERROR_stream_metadata=s))
assert len(errors)==3 and not any((ROOT/f'call{n:02d}/request.json').exists() for n in (8,9,10))
result=next(r['result'] for r in reversed(rows) if r.get('event')=='result')
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='REAL_NATIVE_PATH_ENGINEERING_FAILURE_KEEP_ORIGINAL_STOP_NO_RETRY',global_CLI=33,
 recorder_source_sha256=sha(Path(__file__)),terminal=ref(A/'terminal.json'),raw=ref(A/'stream.jsonl'),audit=ref(A/'audit.json'),freeze=ref(A/'freeze.json'),index=ref(A/'index.json'),actual_partial_receipt=ref(A/'actual_partial_terminal_receipt.json'),stopped=ref(ROOT/'stopped.json'),full24=ref(ROOT/'full_denominator24_after_CLI33.json'),
 actual_exit_code=terminal['exit_code'],actual_wall_seconds=terminal['wall_seconds'],actual_AGY_result_status=result['status'],AGY_result_does_not_override_actual_media_errors=True,
 actual_wrong_native_path_comparisons=comparisons,actual_nonmedia_error_message_steps=audit['error_message_steps'],actual_unfinished_tools=audit['unfinished_tool_attempts'],
 failure_classification='MODEL_TOOL_ARGUMENT_NATIVE_ORDINAL_PATH_DIFFERS_FROM_FROZEN_INDEX',correct_frozen_PNGs_exist_and_SHA_equal=True,no_evidence_of_source_missing_or_SHA_drift=True,no_authentication_error_claim=True,
 first_job16_completed_prefix=ref(A/'w16_completed_scope_audit.json'),job16_preserved_no_repeat=True,
 job17_actual_native_DONE=33,job17_bound_facts=32,job17_clip_DONE=False,job17_preview_DONE=0,job17_proposal_missing=True,
 observed_DONE_agent_responses=receipt['observed_DONE_agent_responses'],observed_DONE_tools=receipt['observed_DONE_tools'],actual_final_result_usage=result.get('usage'),observed_response_usage_field_sums=receipt['observed_response_usage_field_sums'],usage_not_invoice=True,cash_cost='UNKNOWN_NOT_ZERO',
 pending_unregistered_CLI=[34,35,36],pending_fixed_jobs=list(range(18,24)),automatic_retry=False,new_teacher_calls=0,new_decode=0,new_media_observation=0,new_optimizer=0)
p=A/'engineering_wrong_native_ordinal_paths_CLI33.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(receipt=ref(p),comparisons=[dict(step=c['step'],wrong=Path(c['actual_wrong_AbsolutePath']).name,expected=Path(c['expected_literal_AbsolutePath']).name) for c in comparisons],actual_wall_seconds=terminal['wall_seconds'],actual_final_usage=result.get('usage'),pending_unregistered_CLI=[34,35,36]),ensure_ascii=False))
