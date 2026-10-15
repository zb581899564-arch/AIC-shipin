"""ROOT explicit admission of last window; no old whole-rejection reclassification."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
R=Path(__file__).resolve().parent;N=R/'teacher_expansion/schema_recovery_23_continuation_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
review=Path(sys.argv[1]).resolve(strict=True);expected_sha=sys.argv[2];expected_status=sys.argv[3]
assert review.parent==R/'plan_review' and sha(review)==expected_sha and read(review)['status']==expected_status
b=read(N/'execution_code_binding.json')
for key in ('sources','actual_prior_bindings'):
 for p,h in b[key].items():assert sha(p)==h,(key,p)
fr=read(N/'call40/freeze.json')
for p,h in fr['inputs'].items():assert sha(p)==h,p
assert not any(Path(p).exists() for p in fr['write_whitelist'])
assert not any((R/'teacher_expansion').rglob('call40/request.json'))
assert fr['CLI_before']==39 and fr['CLI_after']==40 and fr['fixed_job_indices']==[23]
recovery=R/'20_cjibt_w13_root_semantic_recovery_receipt_v1.json';w20=read(recovery)
auth=R/'schema_recovery_22_23_user_authorization_v1.json'
gate=dict(status='ROOT_APPROVED_START_SCHEMA_RECOVERY_CONTINUATION_SINGLE_CLI40_JOB23',utc=datetime.now(timezone.utc).isoformat(),
 execution_binding_sha256=sha(N/'execution_code_binding.json'),dry_run_sha256=sha(N/'dry_run_acceptance.json'),
 negative_receipt_sha256=sha(N/'independent_CPU_negative_acceptance.json'),user_authorization=bound(auth),
 CLI=40,global_cap=40,no41=True,automatic_retry=False,fixed_job_indices=[23],timeout_seconds=3600,
 previous39_recovery=fr['previous39_recovery'],ROOT_w20_complete_independent_semantic_recovery_PASS=True,
 w20_semantic_recovery_receipt=dict(bound(recovery),status=w20['status']),w20_reference_binding=w20['reference_binding'],
 independent_static_review=bound(review),actual_input_SHA_count=len(fr['inputs']),scientific_training_or_quality_PASS=False)
sys.path.insert(0,str(N));from launch import verify_w20_recovery,verify_previous39
verify_w20_recovery(gate);verify_previous39(gate)
p=N/'root_start_admission_CLI40.json'
with p.open('x',encoding='utf-8') as f:json.dump(gate,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps(dict(status=gate['status'],path=str(p),sha256=sha(p),actual_inputs=len(fr['inputs'])),ensure_ascii=False))
