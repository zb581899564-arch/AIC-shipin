"""Root semantic adjudication of explicitly composed observations, evaluation only."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
p=R/'13_esjr_w06_main_preteacher_review.json';pre=read(p)
t=R/'13_esjr_w06_composed_observation_completion.json';teacher=read(t)
value=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),window_id=pre['window_id'],
 candidate_prediction_exposure=False,root_read_all64_teacher_facts=True,root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,
 selected_preteacher_event_indices=[0],unknown_local_exact=[],consequential_unknowns=[],
 evidence=dict(preteacher_main_review=bind(p),teacher_observation_audit=bind(t),
  original_teacher_program_bound_facts=teacher['program_bound_facts'],composed_protocol=teacher['protocol'],root_effective8=teacher['root_effective8'],
  original_Gemini_failure=bind(R/'teacher_expansion/capacity_v4_tool_batches/call05/engineering_wrong_preview_paths_CLI31.json'),
  bounded_student_reinspection=bind(R/'student_reviews/13_-esJrBWj2d8_W06.student_bounded_reinspection_v1.json'),
  bounded_student_acceptance=bind(R/'13_esjr_w06_bounded_student_acceptance.json')),
 differences_adjudicated=pre['explicit_disagreements']+[
  'Original Gemini task13 remains FAILED: all64 native facts and native video were actually delivered, but its eight guessed preview paths ERROR and no proposal exists. This final reference uses a separately declared composite observation; its effective8 are actual root views, never attributed to Gemini.',
  'Teacher labels the cat supine/four limbs stretched and infers calm, docile, relaxed or sleeping. Actual native and effective images show a reclining cat with overlapped limbs and varying eye opening. Root uses only clear short representative pose/image, with no emotion or sleep target.',
  'Teacher one-image captions infer repeated rubbing, no resistance, environmental dynamics and prospective lifting. None is accepted from a static frame. Existing independent whole-window facts support hand contact then withdrawal; routine gentle contact has insufficient distinct visual highlight here and stays NO.',
  'Teacher F53..55 invents a plate lifted/retracted, F54 claims only a fragment right. Root actual native F53/F54/F55 and effectiveF54 show the patterned plate on the lower image/floor area, sometimes clipped by camera, without evidence of lifting or removal. The ordinary pull/push/position change stays NO and its purpose is not inferred.',
  'Food type, meat or moist-food composition and water/feeding function inferred by teacher are not target facts. Root keeps visible containers, pellets, colored remnants and cabinet/floor relations only.',
  'The short F00..08 representative cat image begins at the declared domain boundary and ends in the exact adjacent F08/F09 editing bracket; this is an editorial choice within repeated imagery, not an observed physical event ending or measured cut.'
 ],
 actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],student_sample_indices=pre['root_actually_viewed_student_samples'],
  additional_postteacher_native_samples=[53,54,55],additional_postteacher_student_previews=[0,9,18,27,36,45,54,63],
  read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,read_bounded_student_facts=11,
  root_direct64_image_review=False,root_native_video_view=False,original_Gemini_proposal_absent=True),
 reference_scope_and_reason='Evaluation-only finite visual editing silver from separately provenance-bound actual media. Select a short clear reclining-cat representative image and explicitly reject repeated pose, routine contact and ordinary plate positioning; no physical ending, audio, emotion or food composition is invented. Original Gemini failed task is preserved. Not gold or official quality.')
out=R/'13_esjr_w06_root_eval_decision.json'
with out.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(out),ensure_ascii=False))
