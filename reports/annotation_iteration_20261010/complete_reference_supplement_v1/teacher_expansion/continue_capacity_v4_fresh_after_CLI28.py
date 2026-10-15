"""New owned scheduler for fixed untouched calls3..10; never retries call02."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,copy
BASE=Path(__file__).resolve().parent;ROOT=BASE/'capacity_v4_tool_batches'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
admission=ROOT/'root_fresh_continuation_admission_after_CLI28.json'
gate=read(admission)
assert gate['status']=='ROOT_APPROVED_FRESH_CALLS3_TO10_AFTER_CLI28'
assert gate['diagnosis_sha256']==sha(ROOT/'read_only_network_diagnosis_after_CLI28.json')
assert gate['failed_terminal_sha256']==sha(ROOT/'call02/terminal.json')
assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json')
binding=ROOT/'fresh_continuation_after_CLI28_binding.json';bound=read(binding)
assert gate['binding_sha256']==sha(binding) and bound['runner_sha256']==sha(Path(__file__))
for p,h in bound['inputs'].items():assert sha(Path(p))==h
old=read(ROOT/'call02/terminal.json');assert old['CLI_after']==28 and old['exit_code']==1
audit=read(ROOT/'call02/audit.json');assert audit['actual_nonself_tool_calls']==0
ledger=BASE/'global_CLI_ledger.jsonl';counts=[json.loads(s)['global_count'] for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip()]
assert max(counts)==28
for n in range(3,11):
    a=ROOT/f'call{n:02d}';fr=read(a/'freeze.json')
    assert not (a/'request.json').exists() and fr['CLI_after']==26+n and fr['timeout_seconds']==7200 and fr['automatic_retry'] is False
    for p,h in fr['inputs'].items():assert sha(Path(p))==h
save(ROOT/'fresh_continue_after_CLI28_registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),calls=list(range(3,11)),jobs=list(range(8,24)),CLI_numbers=list(range(29,37)),source_sha256=sha(Path(__file__)),root_admission_sha256=sha(admission),binding_sha256=sha(binding),diagnosis_sha256=sha(ROOT/'read_only_network_diagnosis_after_CLI28.json'),failed_CLI28_terminal_sha256=sha(ROOT/'call02/terminal.json'),failed_CLI28_raw_sha256=sha(ROOT/'call02/stream.jsonl'),failed_CLI28_audit_sha256=sha(ROOT/'call02/audit.json'),failed_jobs6_7_not_retried=True,automatic_retry=False,fixed_full_denominator=24))
def snapshot24(cli):
    registry=Path(bound['root_denominator']['path']);base=read(registry);records=copy.deepcopy(base['records'])
    assert len(records)==24
    for k in range(2,11):
        b=ROOT/f'call{k:02d}';bi=read(b/'index.json');ba=read(b/'audit.json') if (b/'audit.json').exists() else None
        for w in bi['windows']:
            r=records[w['window_id']];report=next((s for s in ba['windows'] if s['window_id']==w['window_id']),None) if ba else None
            r['teacher_observation']=dict(job_index=w['job_index'],status=report['status'] if report else 'PENDING_NOT_REGISTERED',bound_rows=report['bound_rows'] if report else 0,audit_path=str(b/'audit.json') if ba else None,audit_sha256=sha(b/'audit.json') if ba else None,proposal_sha256=report['proposal_sha256'] if report else None,semantic_correctness='PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW')
    save(ROOT/f'full_denominator24_after_CLI{cli:02d}.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_FIXED24_SNAPSHOT_WITH_ROOT_REFERENCE_AUTHORITY_PRESERVED',fixed_denominator=24,root_registry={'path':str(registry),'sha256':sha(registry)},root_qualified_references_at_frozen_registry=base['qualified_references'],records=records,global_CLI_calls=cli,global_CLI_cap=36,failed_jobs6_7_not_retried=True,new_optimizer_updates=0,new_426=0,cash_cost='UNKNOWN_NOT_ZERO'))
for n in range(3,11):
    a=ROOT/f'call{n:02d}';assert not (a/'request.json').exists()
    subprocess.run([sys.executable,str(ROOT/'run_pair.py'),str(n)],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'audit_pair.py'),str(n)],cwd=ROOT,check=True)
    au=read(a/'audit.json');t=read(a/'terminal.json')
    snapshot24(t['CLI_after'])
    save(ROOT/f"status_after_CLI{t['CLI_after']:02d}.json",dict(utc=datetime.now(timezone.utc).isoformat(),CLI_after=t['CLI_after'],audit_path=str(a/'audit.json'),audit_sha256=sha(a/'audit.json'),terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),windows=au['windows'],cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False,failed_jobs6_7_not_retried=True))
    print(json.dumps(dict(event='FRESH_CALL_TERMINAL_AUDITED',call=n,global_CLI_calls=t['CLI_after'],window_statuses=[dict(job_index=w['job_index'],status=w['status']) for w in au['windows']],terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl')),ensure_ascii=False),flush=True)
    if t['exit_code']!=0 or au['tool_issues'] or any(w['schema_issues'] or w['proposal_issues'] for w in au['windows']):
        save(ROOT/'fresh_continue_after_CLI28_stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='ENGINEERING_OR_SCHEMA_FAILURE_NO_AUTOMATIC_RETRY',pending_calls=list(range(n+1,11))));sys.exit(2)
    if au.get('actual_result_status')!='SUCCESS' or au.get('error_message_steps'):
        save(ROOT/'fresh_continue_after_CLI28_awaiting_root.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='COMPLETE_WORK_WITH_REAL_ERROR_REQUIRES_ROOT_REVIEW',pending_calls=list(range(n+1,11))));sys.exit(3)
save(ROOT/'fresh_continue_after_CLI28_completion.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE_FIXED_16_FRESH_STRUCTURES_PENDING_ROOT_SEMANTIC',fresh_windows=16,total_teacher_denominator=21,failed_jobs6_7_not_retried=True,failed_HT5_W10_not_retried=True,global_CLI_calls=36,cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False,new_optimizer_updates=0,new_426=0))
