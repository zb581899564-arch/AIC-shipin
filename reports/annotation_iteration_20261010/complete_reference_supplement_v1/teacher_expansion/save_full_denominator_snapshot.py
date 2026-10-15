from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
BASE=Path(__file__).resolve().parent;V3=BASE/'capacity_v3_network';V4=BASE/'capacity_v4_tool_batches'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
wins=[];root=BASE.parent/'03_w11_lawful_observation_completion.json'
resume=V3/'resume_w11_network_recovery_v1';ri=read(resume/'index.json')['window']
wins.append(dict(job_index=3,window_id=ri['window_id'],status='COMPLETE_ROOT_LAWFUL_MEDIA_WITH_REAL_ERROR_PRESERVED_PENDING_SEMANTIC',root_admission={'path':str(root),'sha256':sha(root)},proposal={'path':str(resume/'w03_proposal.json'),'sha256':sha(resume/'w03_proposal.json')},training_admitted=False))
for n in range(1,11):
    a=V3/'call01' if n==1 else V4/f'call{n:02d}'
    idx=read(a/'index.json');audit=read(a/'audit.json') if (a/'audit.json').exists() else None
    for w in idx['windows']:
        report=next((r for r in audit['windows'] if r['job_index']==w['job_index']),None) if audit else None
        status='PENDING_NOT_REGISTERED'
        if report:status='COMPLETE_TOOL_STRUCTURE_PENDING_ROOT_SEMANTIC' if report['status'].startswith('PASS_') else 'FAILED_OR_INCOMPLETE_KEEP_RAW'
        wins.append(dict(job_index=w['job_index'],window_id=w['window_id'],role=w['role'],status=status,audit={'path':str(a/'audit.json'),'sha256':sha(a/'audit.json')} if audit else None,terminal={'path':str(a/'terminal.json'),'sha256':sha(a/'terminal.json')} if (a/'terminal.json').exists() else None,bound_rows=report['bound_rows'] if report else 0,native_DONE=len(report['native_read_done']) if report else 0,clip_DONE=report['clip_read_done'] if report else False,student_preview_DONE=len(report['student_preview_read_done']) if report else 0,proposal_sha256=report['proposal_sha256'] if report else None,training_admitted=False))
assert [w['job_index'] for w in wins]==list(range(3,24))
counts={'complete':sum(w['status'].startswith('COMPLETE') for w in wins),'failed_or_incomplete':sum(w['status'].startswith('FAILED') for w in wins),'pending_not_registered':sum(w['status'].startswith('PENDING') for w in wins)}
ledger=BASE/'global_CLI_ledger.jsonl';ls=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip()]
assert max(s['global_count'] for s in ls)==28
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_21_DENOMINATOR_SNAPSHOT_AFTER_CLI28_NOT_COMPLETION',fixed_denominator=21,counts=counts,windows=wins,global_CLI_calls=28,global_cap=36,remaining_unspent_CLI_capacity=8,ledger={'path':str(ledger),'sha256':sha(ledger)},controller_stopped={'path':str(V4/'controller_stopped.json'),'sha256':sha(V4/'controller_stopped.json')},cash_cost='UNKNOWN_NOT_ZERO',automatic_retry=False,semantic_correctness='UNVERIFIED_PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW',training_admitted=False,new_optimizer_updates=0,new_426=0)
out=BASE/'full_denominator_after_CLI28.json'
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),counts=counts),ensure_ascii=False))
