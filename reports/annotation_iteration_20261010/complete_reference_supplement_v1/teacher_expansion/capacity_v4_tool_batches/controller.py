from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess,hashlib
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FIXED_V4' and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json')
save(ROOT/'controller_registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),fixed_calls=list(range(2,11)),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),automatic_retry=False,global_final_cap=36))
for n in range(2,11):
    a=ROOT/f'call{n:02d}';assert not (a/'request.json').exists(),'No repeat model CLI'
    subprocess.run([sys.executable,str(ROOT/'run_pair.py'),str(n)],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'audit_pair.py'),str(n)],cwd=ROOT,check=True)
    au=read(a/'audit.json');t=read(a/'terminal.json')
    save(ROOT/f"status_after_CLI{t['CLI_after']:02d}.json",dict(utc=datetime.now(timezone.utc).isoformat(),CLI_after=t['CLI_after'],audit_path=str(a/'audit.json'),audit_sha256=sha(a/'audit.json'),terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),windows=au['windows'],cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False))
    print(json.dumps(dict(event='CALL_TERMINAL_AUDITED',call=n,global_CLI_calls=t['CLI_after'],window_statuses=[dict(job_index=w['job_index'],status=w['status']) for w in au['windows']],terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl')),ensure_ascii=False),flush=True)
    if t['exit_code']!=0 or au['tool_issues'] or any(w['schema_issues'] or w['proposal_issues'] for w in au['windows']):
        save(ROOT/'controller_stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='ENGINEERING_OR_SCHEMA_FAILURE_NO_AUTOMATIC_RETRY',pending_calls=list(range(n+1,11))));sys.exit(2)
    if au.get('actual_result_status')!='SUCCESS' or au.get('error_message_steps'):
        save(ROOT/'controller_awaiting_root.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='COMPLETE_WORK_WITH_REAL_ERROR_REQUIRES_ROOT_REVIEW',pending_calls=list(range(n+1,11))));sys.exit(3)
save(ROOT/'completion.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE_18_FRESH_TOOL_STRUCTURES_PENDING_SEMANTIC_REVIEW',fixed_fresh_denominator=18,total_reference_denominator=21,global_CLI_calls=36,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0,new_426=0))
