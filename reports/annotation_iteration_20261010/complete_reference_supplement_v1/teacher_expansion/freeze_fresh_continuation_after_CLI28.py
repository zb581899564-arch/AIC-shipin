from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,ast
BASE=Path(__file__).resolve().parent;ROOT=BASE/'capacity_v4_tool_batches'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
runner=BASE/'continue_capacity_v4_fresh_after_CLI28.py';ast.parse(runner.read_text(encoding='utf-8-sig'))
registry=BASE.parent/'denominator24_v5.json';den=read(registry);assert den['fixed_denominator']==24 and len(den['records'])==24
jobs=BASE.parents[1]/'slot6_silver24_v1/observations/jobs.json';paths=read(jobs)['jobs'];assert len(paths)==24
ids=[read(Path(p)/'manifest.json')['window_id'] for p in paths];assert set(ids)==set(den['records']) and len(set(ids))==24
inp={str(p):sha(p) for p in [runner,ROOT/'read_only_network_diagnosis_after_CLI28.json',ROOT/'call02/terminal.json',ROOT/'call02/stream.jsonl',ROOT/'call02/audit.json',ROOT/'dry_run_acceptance.json',registry,jobs]}
for r in den['records'].values():
    if r.get('reference'):
        p=Path(r['reference']['path']);assert sha(p)==r['reference']['sha256'];inp[str(p)]=sha(p)
checks=[]
for n in range(3,11):
    a=ROOT/f'call{n:02d}';fr=read(a/'freeze.json');assert not (a/'request.json').exists()
    assert fr['CLI_after']==26+n and fr['timeout_seconds']==7200 and fr['fixed_job_indices']==[2*n+2,2*n+3]
    for p,h in fr['inputs'].items():assert sha(Path(p))==h
    for p in (a/'freeze.json',a/'index.json'):inp[str(p)]=sha(p)
    checks.append(dict(call=n,job_indices=fr['fixed_job_indices'],CLI_after=fr['CLI_after'],all_frozen_inputs_SHA_actual_PASS=True))
binding=ROOT/'fresh_continuation_after_CLI28_binding.json'
save(binding,dict(utc=datetime.now(timezone.utc).isoformat(),status='FROZEN_FIXED_FRESH_CONTINUATION_NO_LAUNCH_YET',runner_sha256=sha(runner),inputs=inp,root_denominator={'path':str(registry),'sha256':sha(registry)},fixed_denominator24_identity_ids=ids,prospective_calls=list(range(3,11)),job_indices=list(range(8,24)),CLI_numbers=list(range(29,37)),global_cap=36,timeout_seconds=7200,automatic_retry=False,failed_jobs6_7_not_retried=True,new_model_calls=0,cash_cost='UNKNOWN_NOT_ZERO'))
receipt=ROOT/'fresh_continuation_after_CLI28_AST_acceptance.json'
save(receipt,dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_AST_ACTUAL_BINDINGS_FIXED24_NO_MODEL_PENDING_ROOT_START',runner={'path':str(runner),'sha256':sha(runner)},binding={'path':str(binding),'sha256':sha(binding)},checks=checks,fixed_denominator=24,identity_count=24,root_qualified_refs_at_registry=den['qualified_references'],new_model_calls=0,new_optimizer_updates=0,new_426=0,previous_sources_and_freezes_unchanged=True,authenticated_POST_still_not_verified=True,requires_new_root_admission=True))
print(json.dumps(dict(runner_sha256=sha(runner),binding_sha256=sha(binding),AST_acceptance_sha256=sha(receipt),new_model_calls=0),ensure_ascii=False))
