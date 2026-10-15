"""Preserve the failed root serialization and make a separate corrected verifier."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'accept_teacher_fragment_scope_v8_root.py'
partial=R/'19_j0n_w11_lawful_observation_completion.json'
receipt=R/'root_fragment_v8_serialization_failure_preserved_v1.json'
data={'status':'ROOT_SERIALIZATION_ENGINEERING_FAILURE_PRESERVED_NOT_MODEL_FAILURE','original_verifier':{'path':str(old),'sha256':sha(old)},'partial_output':{'path':str(partial),'sha256':sha(partial),'bytes':partial.stat().st_size},'actual_exception':'TypeError: Object of type Match is not JSON serializable','cause':'Regex match variable n shadowed the CLI number before JSON dump','old_sources_and_raw_unchanged':True,'new_model_calls':0}
with receipt.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
s=old.read_text(encoding='utf-8')
changes=[('n=36 if job<21 else 37','number=36 if job<21 else 37'),("c=V/f'call{n}'","c=V/f'call{number}'"),("req['CLI_after']==n","req['CLI_after']==number"),('global_CLI=n,','global_CLI=number,'),("with output.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)","serialized=json.dumps(out,ensure_ascii=False,indent=2)\n with output.open('x',encoding='utf-8') as f:f.write(serialized)")]
for a,b in changes:
 assert s.count(a)==1,a
 s=s.replace(a,b)
ast.parse(s)
target=R/'accept_teacher_fragment_scope_v8_root_v2.py'
with target.open('x',encoding='utf-8') as f:f.write(s)
print(json.dumps({'path':str(target),'sha256':sha(target),'failure_receipt_sha256':sha(receipt)},ensure_ascii=False))
