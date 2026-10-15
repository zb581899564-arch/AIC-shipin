"""Independent representation proof; original v4 audit files never overwritten."""
from common import ROOT,V5,read,sha,save,key
from datetime import datetime,timezone
from pathlib import Path
import json,sys
import engine,original_engine
ALLOWED={'BOOTSTRAP_NOT_EXACTLY_ONCE_FIRST_FULL_DONE','BOOTSTRAP_ACK_MISSING_WRONG_OR_ORDER'}
def reconstruct(number,job=None):
 a=ROOT/f'call{number}';outdir=V5/f'call{number}';outdir.mkdir(exist_ok=True)
 if job is None:
  terminal=read(a/'terminal.json');raw=(a/'stream.jsonl').read_bytes();assert sha(a/'stream.jsonl')==terminal['stream_sha256'];original_path=a/'audit.json';target=outdir/'line_representation_final.json'
 else:
  original_path=a/f'w{job:02d}_completed_scope_audit.json';prior=read(original_path);prefix=Path(prior['immutable_prefix']['path']);assert sha(prefix)==prior['immutable_prefix']['sha256'];raw=prefix.read_bytes();terminal=None;target=outdir/f'w{job:02d}_line_representation_scope.json'
 assert original_path.exists() and not target.exists()
 original=original_engine.inspect(a,raw,job,terminal);fixed=engine.inspect(a,raw,job,terminal)
 original_saved=read(original_path)
 assert original_saved['actual_stream_SHA']==original['actual_stream_SHA']==fixed['actual_stream_SHA']
 reasons={i['reason'] for i in original['tool_issues']}
 strict=not fixed['tool_issues'] and not fixed['errored_tool_attempts'] and not fixed['unfinished_tool_attempts'] and all(w['status'].startswith('PASS_') for w in fixed['windows']) and fixed['bootstrap_successful_complete'] and fixed['bootstrap_ack_complete']
 if job is None:
  strict=strict and terminal['exit_code']==0 and terminal.get('child_process_created') is True and terminal.get('stop_reason') is None and fixed['actual_result_status']=='SUCCESS' and not fixed['reported_nonmedia_errors']
 else:strict=strict and not fixed['reported_nonmedia_errors']
 strict=strict and bool(reasons) and reasons<=ALLOWED
 idx=read(a/'index.json');payload=Path(idx['bootstrap_instruction_path']).read_bytes()
 strict=strict and payload.endswith(bytes([10])) and bytes([13]) not in payload
 proof=dict(utc=datetime.now(timezone.utc).isoformat(),status='ACCEPT_ACTUAL_SUPPLY_LINE_REPRESENTATION_ONLY_PENDING_ROOT_SEMANTIC' if strict else 'REJECT_ACTUAL_OTHER_FAILURE_NO_MODEL_RETRY',CLI=number,scope_stop_job=job,original_v4_strict_rejection_preserved=True,original_audit_path=str(original_path),original_audit_sha256=sha(original_path),original_v4_tool_issues=original['tool_issues'],original_v4_only_representation_and_ACK_dependency_reasons=bool(reasons) and reasons<=ALLOWED,actual_bootstrap=dict(path=idx['bootstrap_instruction_path'],sha256=sha(idx['bootstrap_instruction_path']),bytes=len(payload),Python_splitlines_count=len(payload.splitlines()),count_LF=payload.count(bytes([10])),Go_split_LF_count=payload.count(bytes([10]))+1,ends_with_LF=payload.endswith(bytes([10])),strict_exact_metadata_required=True,actual_tool_attempts=fixed['bootstrap_attempts']),original_immutable_prefix=original_saved.get('immutable_prefix'),terminal_sha256=sha(a/'terminal.json') if terminal else None,actual_terminal=terminal,actual_usage=fixed['actual_result_usage'],representation_audit=fixed,semantic_correctness='PENDING_ROOT_INDEPENDENT_ACTUAL_REVIEW',training_admitted=False,no_old_audit_or_freeze_changed=True,new_model_calls_in_reconstruction=0,cash_cost='UNKNOWN_NOT_ZERO')
 save(target,proof)
 print(json.dumps(dict(CLI=number,scope=job,status=proof['status'],path=str(target),sha256=sha(target),windows=[dict(job_index=w['job_index'],status=w['status']) for w in fixed['windows']]),ensure_ascii=False),flush=True)
 return proof
if __name__=='__main__':
 if sys.argv[1]=='scope':reconstruct(int(sys.argv[2]),int(sys.argv[3]))
 else:reconstruct(int(sys.argv[1]))
