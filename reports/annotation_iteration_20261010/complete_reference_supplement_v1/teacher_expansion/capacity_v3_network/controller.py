from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess,hashlib
from admission import assert_root_resume_admission
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
resume=ROOT/'resume_w11_network_recovery_v1'
root_admission=assert_root_resume_admission()
assert not (ROOT/'controller_registered.json').exists(),'No duplicate controller'
save(ROOT/'controller_registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),fixed_calls=list(range(1,11)),root_resume_admission=root_admission,automatic_retry=False,global_final_cap=36))
for n in range(1,11):
    a=ROOT/f'call{n:02d}'
    assert not (a/'request.json').exists(),'No repeat model CLI'
    subprocess.run([sys.executable,str(ROOT/'run_pair.py'),str(n)],cwd=ROOT,check=True)
    assert (a/'terminal.json').exists(),'Missing true terminal'
    subprocess.run([sys.executable,str(ROOT/'audit_pair.py'),str(n)],cwd=ROOT,check=True)
    result=read(a/'audit.json');terminal=read(a/'terminal.json')
    windows=[dict(job_index=3,window_id=read(resume/'audit.json')['window_id'],status='PASS_ROOT_LAWFUL_COMPLETION_WITH_REAL_ERROR_PRESERVED_PENDING_SEMANTIC_REVIEW',proposal_path=str(resume/'w03_proposal.json'),root_admission=root_admission,prior_STOP_audit_sha256=sha(resume/'audit.json'))]
    for k in range(1,11):
        b=ROOT/f'call{k:02d}'
        if (b/'audit.json').exists():
            au=read(b/'audit.json')
            for w in au['windows']:windows.append(dict(job_index=w['job_index'],window_id=w['window_id'],status=w['status'],bound_rows=w['bound_rows'],audit_sha256=sha(b/'audit.json'),proposal_path=str(b/f"w{w['job_index']:02d}_proposal.json")))
        else:
            for w in read(b/'index.json')['windows']:windows.append(dict(job_index=w['job_index'],window_id=w['window_id'],status='PENDING',training_admitted=False))
    snapshot=dict(utc=datetime.now(timezone.utc).isoformat(),fixed_denominator=21,windows=windows,global_CLI_calls=terminal['CLI_after'],cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False,new_training=0,new_426=0,
      original_timeout_and_network_failure_preserved=True,semantic_correctness='PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW')
    save(ROOT/f"status_after_CLI{terminal['CLI_after']:02d}.json",snapshot)
    print(json.dumps(dict(event='CALL_TERMINAL_AUDITED',call=n,global_CLI_calls=terminal['CLI_after'],window_statuses=[dict(job_index=w['job_index'],status=w['status']) for w in result['windows']],terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl')),ensure_ascii=False),flush=True)
    # Do not blindly spend following fixed calls after a material engineering failure.
    if terminal['exit_code']!=0 or result['tool_issues'] or any(w['schema_issues'] or w['proposal_issues'] for w in result['windows']):
        save(ROOT/'controller_stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='ENGINEERING_OR_SCHEMA_FAILURE_NO_AUTOMATIC_RETRY',audit_sha256=sha(a/'audit.json'),pending_calls=list(range(n+1,11))))
        print(json.dumps(dict(event='STOP_KEEP_RAW_NO_RETRY',after_call=n)),flush=True);sys.exit(2)
    if result.get('actual_result_status')!='SUCCESS' or result.get('error_message_steps'):
        save(ROOT/'controller_awaiting_root.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='ACTUAL_COMPLETE_WORK_WITH_RESULT_OR_EARLY_ERROR_REQUIRES_ROOT_ADMISSION',audit_sha256=sha(a/'audit.json'),pending_calls=list(range(n+1,11))))
        print(json.dumps(dict(event='COMPLETE_WORK_KEEP_REAL_ERROR_AWAIT_ROOT',after_call=n)),flush=True);sys.exit(3)
save(ROOT/'completion.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE_21_TOOL_STRUCTURES_PENDING_SEMANTIC_REVIEW',fixed_denominator=21,global_CLI_calls=36,training_admitted=False,new_training=0,new_426=0,cash_cost='UNKNOWN_NOT_ZERO'))
