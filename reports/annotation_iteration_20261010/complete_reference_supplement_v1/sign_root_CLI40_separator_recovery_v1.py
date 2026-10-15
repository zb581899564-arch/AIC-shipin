from pathlib import Path
from datetime import datetime,timezone
import json
import recover_CLI40_effective_literal_separator_v1 as r
R=Path(__file__).resolve().parent
expected=['0a0e87d7e5421c5fc8b63506ccc2d530081eed8a8580a08cf72f4927ace17025','b7963a805471837b36f15fb6eedc07fc03dd6f42da34a88116bad17e2b9a7c1c']
helpers={str(R/n):r.sha(R/n) for n in r.HELPERS}
assert list(helpers.values())==expected
np=R/'CLI40_effective_literal_separator_necessary_CPU_receipt_v1.json'
assert r.sha(np)=='6a7c2e0349dddec1d57c123c00259b222f5d83b48bf66a8373dcf83f9abb3045'
n=r.read(np);assert n['helpers']==helpers and len(n['counterexample_classes'])==12 and all(x['rejected'] for x in n['counterexample_classes'])
rp=R/'root_actual_CLI40_separator_identity_v1.json';ip=R/'plan_review/CLI40_effective_separator_independent_recovery_v1.json'
assert r.sha(rp)=='1772717c43c1dc926177944cc2cb36b4e03b24b3bf7e8780b88ca55b79fd9a60'
assert r.sha(ip)=='c3eef4b766a50857093d34fa37a54d4db5d1f2636ff928118180db82d3304e01' and not r.read(ip)['issues']
v=dict(status=r.GATE_STATUS,utc=datetime.now(timezone.utc).isoformat(),CLI=40,job_index=23,window_id='Yi4Ij2NM7U4:SLOT6:6',automatic_retry=False,no_new_model=True,old_REJECTED_preserved=True,helpers=helpers,negative_receipt_binding=r.bind(np),root_samefile_identity_binding=r.bind(rp),independent_recovery_review_binding=r.bind(ip),bindings=r.required_bindings(),user_authorization=r.bind(R/'schema_recovery_22_23_user_authorization_v1.json'),ROOT_actual_code_review=True,ROOT_actual_samefile_and_SHA_checks=True,scope='Exactly eight registered effective paths with one extra separator; finite observation recovery only. Original literal noncompliance and strict REJECT remain.',training_admitted=False)
with r.GATE.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(r.bind(r.GATE),ensure_ascii=False))
