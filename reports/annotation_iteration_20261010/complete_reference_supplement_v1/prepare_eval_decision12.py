"""Root adjudication after all teacher facts and actual disagreement image checks."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
p=R/'12_esjr_w01_main_preteacher_review.json';pre=read(p)
t=R/'12_esjr_w01_lawful_observation_completion.json';teacher=read(t)
evidence=dict(preteacher_main_review=bind(p),teacher_observation_audit=bind(t),
 original_teacher_proposal=teacher['proposal'],original_teacher_program_bound_facts=teacher['program_bound_facts'],
 bounded_student_reinspection=bind(R/'student_reviews/12_-esJrBWj2d8_W01.student_bounded_reinspection_v1.json'),
 bounded_student_acceptance=bind(R/'12_esjr_w01_bounded_student_acceptance.json'))
value=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),
 window_id=pre['window_id'],candidate_prediction_exposure=False,root_read_all64_teacher_facts=True,
 root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,selected_preteacher_event_indices=[0,1],
 unknown_local_exact=[],consequential_unknowns=[],evidence=evidence,
 differences_adjudicated=pre['explicit_disagreements']+[
  'Teacher supports opening but describes eager cat, ingestion, cat-food composition and complete feeding interaction. Root retains only observed lid lift/removed cover/withdrawn hand/open container and nearby cat muzzle, without emotions, swallowed food or full feeding completion.',
  'Root additionally retains the short clear cat/white-rimmed box/brown contents typical image at F52..58; teacher marks the whole post-opening tail NO. F58 actually exposes the contents as the muzzle is above the opening. This finite representative shot is not a claim of licking or swallowing.',
  'Actual post-teacher rechecks F18/F25/F52/F58 agree with the finite preteacher facts. Bounded student F39 correction withdraws too-definite mouth-inside/contact wording; that ordinary repetitive range remains NO and supplies no ingestion target.',
  'Teacher8 previews are not actual student64 input. All64 effective views and normalized processor receipt are separate evidence; teacher’s8-only and audio-absence statements are not adopted.',
  'Original teacher wide decimal uncertainty ranges are preserved as its proposal. Root editing brackets derive from exact actual adjacent samples with widths at most0.5 seconds and are not measured cuts.'
 ],actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],
  student_sample_indices=pre['root_actually_viewed_student_samples'],additional_postteacher_native_samples=[18,25,52,58],
  read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,read_bounded_student_facts=11,
  root_direct64_image_review=False),
 reference_scope_and_reason='Evaluation-only complete finite visual editing silver: opening has an observed local result, and a separate short clear typical cat/container image. Complete ingestion, emotions and unheard audio remain outside the target. Not gold or official quality.')
text=json.dumps(value,ensure_ascii=False,indent=2)
out=R/'12_esjr_w01_root_eval_decision.json'
with out.open('x',encoding='utf-8') as f:f.write(text)
print(json.dumps(bind(out)))
