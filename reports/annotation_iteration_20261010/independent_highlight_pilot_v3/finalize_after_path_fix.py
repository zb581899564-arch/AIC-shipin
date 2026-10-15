"""Finish receipt only; preserve completed observations and partial closure outputs."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent; OLD=ROOT.parent/'slot6_silver24_v1'
sys.path.insert(0,str(OLD))
from silver_contract import verify_window
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bound(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
write(ROOT/'ENGINEERING_ERRATUM.json',dict(error='Closure used reports/annotation_iteration_20261010/SAFE_37_66 instead of actual deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66',
 failed_component='close_pilot.py baseline-path final receipt, after blind/window/denominator checks',
 successful_observations_and_partial_outputs_overwritten=False,
 repair='Correct source path; finalize receipt only; no model/decoder/processor/image-review rerun.'))
record=read(ROOT/'main_adjudication/window_reference.json'); plan=read(OLD/'source_window_plan.json')
try: verify_window(record,plan['jobs'][0]); contract=dict(accepted=True,error=None)
except ValueError as e:contract=dict(accepted=False,error=str(e))
assert not contract['accepted']
denominator=read(ROOT/'denominator24.json');assert len(denominator)==24
safe=ROOT.parents[2]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
assert bound(safe)['sha256']=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
final=read(ROOT/'main_adjudication/final_review.json')
checks={}
for name in ('blind_native','blind_student'):
    s=read(ROOT/name/'seal.json');assert bound(ROOT/name/'proposal.json')['sha256']==s['proposal_sha256']
    checks[name]=dict(seal=bound(ROOT/name/'seal.json'),proposal=bound(ROOT/name/'proposal.json'),actual_reads=64)
out=dict(status='STOP_FIRST_PILOT_DO_NOT_EXPAND_OR_TRAIN',utc=datetime.now(timezone.utc).isoformat(),
 observed_windows=1,qualified_windows=0,remaining_unobserved_windows=23,fixed24_plan=bound(OLD/'source_window_plan.json'),
 teacher_tool_supply=bound(ROOT/'teacher_attempt01/audit.json'),independent_checks=checks,
 root_complete_adjudication=bound(ROOT/'main_adjudication/final_review.json'),root_reference=bound(ROOT/'main_adjudication/window_reference.json'),
 original_silver_contract=contract,denominator=bound(ROOT/'denominator24.json'),teacher_semantic_correction_groups=len(final['teacher_semantic_errors']),
 no_quality_gate_relaxed=True,new_gemini_cli_calls=1,historical_cli_calls_before_stage=21,registered_cli_calls_after_stage=22,
 gemini_cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0,new_GPU_calls=0,new_426_inference_calls=0,new_Pro_calls=0,
 new_zip=False,safe_baseline=bound(safe),human_gold=False,spatial_reference_stop_preserved=True,
 new_protocol_required_before_further_teacher_calls=True,
 next_action='Separate native-video context from explicit PNG ordinal/time facts; correct student-preview wording and specify own-output review policy in a new protocol. Preserve this failure; validate same first fixed window before expansion.',
 engineering_erratum=bound(ROOT/'ENGINEERING_ERRATUM.json'))
write(ROOT/'acceptance.json',out)
print(json.dumps(dict(status=out['status'],contract=contract,qualified=0,remaining=23,new_cli=1,new_training=0,new_zip=False,safe_sha=bound(safe)['sha256']),ensure_ascii=False))
