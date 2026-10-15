"""ROOT admission of one explicit single-window route; never launches a model."""
from pathlib import Path
import json, hashlib, sys
from datetime import datetime, timezone
R=Path(__file__).resolve().parent
N=R/'teacher_expansion/schema_recovery_22_23_v1'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(p): return {'path':str(p),'sha256':sha(p)}
number=int(sys.argv[1]); assert number in (39,40)
review=R/'plan_review/schema_recovery_22_23_v1_independent_static_review.json'
assert read(review)['status']=='PASS_INDEPENDENT_SCHEMA_RECOVERY_22_23_STATIC_BEFORE_LAUNCH'
assert sha(review)=='4a23a09318915baae414fee4cef3aada2e116ca060500b73f1f05328b6357eb7'
binding=read(N/'execution_code_binding.json')
for key in ('sources','actual_prior_bindings'):
 for p,h in binding[key].items(): assert sha(p)==h,(key,p)
a=N/f'call{number}'; freeze=read(a/'freeze.json')
for p,h in freeze['inputs'].items(): assert sha(p)==h,p
assert not any(Path(p).exists() for p in freeze['write_whitelist'])
assert not (a/'request.json').exists()
recovery=R/'20_cjibt_w13_root_semantic_recovery_receipt_v1.json'
w20=read(recovery)
auth=R/'schema_recovery_22_23_user_authorization_v1.json'
gate={'status':f'ROOT_APPROVED_START_SCHEMA_RECOVERY_SINGLE_CLI{number}_JOB{number-17}',
 'utc':datetime.now(timezone.utc).isoformat(),
 'execution_binding_sha256':sha(N/'execution_code_binding.json'),
 'dry_run_sha256':sha(N/'dry_run_acceptance.json'),
 'negative_receipt_sha256':sha(N/'independent_CPU_negative_acceptance.json'),
 'user_authorization':bound(auth),'CLI':number,'global_cap':40,'no41':True,
 'automatic_retry':False,'fixed_job_indices':[number-17],'timeout_seconds':3600,
 'ROOT_w20_complete_independent_semantic_recovery_PASS':True,
 'w20_semantic_recovery_receipt':dict(bound(recovery),status=w20['status']),
 'w20_reference_binding':w20['reference_binding'],
 'independent_static_review':bound(review),'actual_input_SHA_count':len(freeze['inputs']),
 'scientific_training_or_quality_PASS':False}
sys.path.insert(0,str(N))
from launch import verify_w20_recovery, verify_previous39
verify_w20_recovery(gate)
if number==39:
 assert (R/'teacher_expansion/global_CLI_ledger.jsonl').read_bytes()==(N/'actual_global38_ledger_prefix.jsonl').read_bytes()
else:
 previous=N/'root_actual_CLI39_confirmation.json'
 gate['previous39_confirmation']=dict(bound(previous),status=read(previous)['status'])
 verify_previous39(gate)
p=N/f'root_start_admission_CLI{number}.json'
with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(gate,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'status':gate['status'],'path':str(p),'sha256':sha(p),'inputs_verified':len(freeze['inputs'])},ensure_ascii=False))
