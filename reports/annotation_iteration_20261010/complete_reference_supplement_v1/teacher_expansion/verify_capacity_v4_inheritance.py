from pathlib import Path
import json,hashlib,ast
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent;NEW=BASE/'capacity_v4_tool_batches';OLD=BASE/'capacity_v3_network'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for n in range(2,11):
    of=read(OLD/f'call{n:02d}/freeze.json');nf=read(NEW/f'call{n:02d}/freeze.json')
    assert not (OLD/f'call{n:02d}/request.json').exists() and not (NEW/f'call{n:02d}/request.json').exists()
    for p,s in of['inputs'].items():
        assert sha(Path(p))==s,('OLD_SOURCE_INPUT_SHA_DRIFT',p)
        if p!=str(OLD/f'call{n:02d}/index.json'):assert nf['inputs'][p]==s,('SOURCE_BINDING_NOT_EXACT',p)
    for p,s in nf['inputs'].items():assert sha(Path(p))==s,('NEW_INPUT_SHA_DRIFT',p)
    assert nf['fixed_job_indices']==[2*n+2,2*n+3] and nf['timeout_seconds']==7200 and nf['CLI_after']==26+n
    checks.append(dict(call=n,old_input_count=len(of['inputs']),new_input_count=len(nf['inputs']),all_old_and_new_SHA_exact=True,clip_SHA_inherited_exact=True))
astchecks=[]
for p in NEW.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));astchecks.append(dict(path=str(p),sha256=sha(p),AST_PASS=True))
dry=NEW/'dry_run_acceptance.json'
out=NEW/'dry_run_source_inheritance_acceptance.json'
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_INDEPENDENT_OLD_NEW_SOURCE_SHA_AND_AST_NO_MODEL',checks=checks,AST=astchecks,dry_run_sha256=sha(dry),checker_sha256=sha(Path(__file__)),new_model_calls=0,current_call01_execution_sources_unchanged=True)
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),status=v['status']),ensure_ascii=False))
