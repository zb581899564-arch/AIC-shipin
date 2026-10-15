"""Bind completed independent reviews and preserve first-pilot failure."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent; OLD=ROOT.parent/'slot6_silver24_v1'
sys.path.insert(0,str(OLD))
from silver_contract import verify_window
from quality_contract import reference
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def bound(p):return dict(path=str(p),sha256=sha(p))
plan=read(OLD/'source_window_plan.json'); prepared=read(ROOT/'preparation.json')
assert sha(OLD/'source_window_plan.json')==prepared['fixed24_plan_sha256']
checks={}; evidence={}
for name,indexname in [('blind_native','native_index.json'),('blind_student','student_index.json')]:
    d=ROOT/name; s=read(d/'seal.json'); idx=read(ROOT/indexname)
    assert sha(d/'proposal.json')==s['proposal_sha256']
    assert sha(ROOT/indexname)==s['index_sha256']
    assert len(idx['frames'])==64
    for f in idx['frames']:assert sha(Path(f['path']))==f['png_sha256']
    assert len(read(d/'proposal.json')['frame_observations'])==64
    checks[name]=dict(seal_sha256=sha(d/'seal.json'),proposal_sha256=sha(d/'proposal.json'),actual_reads=64)
native_seal=read(ROOT/'blind_native/seal.json')
assert native_seal['receipt_declarations']['teacher_packet_received'] is False
blind_wrapper=dict(blind_attestation=dict(teacher_content_received=False),
 native_seal=bound(ROOT/'blind_native/seal.json'),student_seal=bound(ROOT/'blind_student/seal.json'),
 historical_aggregate_scores_in_inherited_AGENTS=True,new_blind_dataset=False,human_gold=False)
write(ROOT/'main_adjudication/blind_initial_binding.json',blind_wrapper)
packet=read(ROOT/'teacher_packet.json'); final=read(ROOT/'main_adjudication/final_review.json')
student_receipt=Path(packet['student_processor_receipt']['path'])
assert sha(student_receipt)==packet['student_processor_receipt']['sha256']
parts={k:[] for k in ('KEEP','NO','UNKNOWN')}
for row in final['window_coverage']:parts[row['label']].append((str(F(row['start'])+30),str(F(row['end'])+30)))
reference([(30,60)],parts['KEEP'],parts['NO'],parts['UNKNOWN'])
assert len(read(ROOT/'main_adjudication/observations.json')['frame_observations'])==64
for f in read(ROOT/'main_adjudication/observations.json')['frame_observations']:assert sha(Path(f['path']))==f['png_sha256']
record=dict(window_id=final['window_id'],source_sha256=final['source_sha256'],reference_kind=final['reference_kind'],
 keep_global_exact=parts['KEEP'],no_global_exact=parts['NO'],unknown_global_exact=parts['UNKNOWN'],
 evidence=dict(teacher_observation_audit=bound(ROOT/'teacher_attempt01/audit.json'),
 blind_initial=bound(ROOT/'main_adjudication/blind_initial_binding.json'),
 blind_student_visibility=bound(ROOT/'blind_student/proposal.json'),student_processor=bound(student_receipt),
 final_main_review=bound(ROOT/'main_adjudication/final_review.json')),
 main_review_assertions={k:True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed',
 'no_audio_content_invented','necessary_preparation_and_result_considered','no_artificial_event_merging',
 'no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
 boundary_decisions=[dict(uncertainty_start_exact=b['uncertainty_start_local_exact'],
 uncertainty_end_exact=b['uncertainty_end_local_exact'],inside_evidence=b['inside_evidence'],
 outside_evidence_or_domain_boundary=b['outside_evidence_or_domain_boundary']) for b in final['boundary_decisions']],
 consequential_unknowns=final['consequential_unknowns'],events=final['events'],
 explicit_no_highlight=False,all_target_boundaries_adjudicated=True,student_observable_complete_target=True,
 training_admitted=False,reason='Frozen teacher observation contract violation; semantic corrections retained separately.')
write(ROOT/'main_adjudication/window_reference.json',record)
try:
    verify_window(record,plan['jobs'][0]); contract=dict(accepted=True,error=None)
except ValueError as e:contract=dict(accepted=False,error=str(e))
assert contract['accepted'] is False, 'Unexpected acceptance: inspect, do not silently advance'
denominator=[dict(index=i,window_id=j['window']['window_id'],source_group=j['source_group'],role=j['role'],
 status='REJECTED_FIRST_PILOT' if i==0 else 'NOT_OBSERVED_THIS_VERSION_NO_LABEL_CREATED',training_admitted=False)
 for i,j in enumerate(plan['jobs'])]
write(ROOT/'denominator24.json',denominator)
safe=ROOT.parents[2]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
assert sha(safe)=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
acceptance=dict(status='STOP_FIRST_PILOT_DO_NOT_EXPAND_OR_TRAIN',utc=datetime.now(timezone.utc).isoformat(),
 observed_windows=1,qualified_windows=0,remaining_unobserved_windows=23,fixed24_plan=bound(OLD/'source_window_plan.json'),
 teacher_tool_supply=bound(ROOT/'teacher_attempt01/audit.json'),independent_checks=checks,
 root_complete_adjudication=bound(ROOT/'main_adjudication/final_review.json'),root_reference=bound(ROOT/'main_adjudication/window_reference.json'),
 original_silver_contract=contract,denominator=bound(ROOT/'denominator24.json'),
 teacher_semantic_correction_groups=len(final['teacher_semantic_errors']),
 no_quality_gate_relaxed=True,old_successes_not_rerun=True,new_gemini_cli_calls=1,historical_cli_calls_before_stage=21,
 registered_cli_calls_after_stage=22,gemini_cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0,new_GPU_calls=0,
 new_426_inference_calls=0,new_Pro_calls=0,new_zip=False,safe_baseline=bound(safe),
 next_action='Separate native-video context from explicit PNG ordinal/time facts; fix preview wording and own-output review policy in a new protocol. Preserve this failure; validate same first fixed window before expansion.',
 human_gold=False,spatial_reference_stop_preserved=True)
write(ROOT/'acceptance.json',acceptance)
print(json.dumps({k:v for k,v in acceptance.items() if k not in ('independent_checks','fixed24_plan')},ensure_ascii=False))
