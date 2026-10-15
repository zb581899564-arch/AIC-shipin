"""Root semantic review after actual media, never adopts teacher ALL-NO automatically."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
for n,tag,wname in [(14,'14_i3w_w02','14_i3wAGJaaktw_W02'),(15,'15_i3w_w03','15_i3wAGJaaktw_W03')]:
 pp=R/(tag+'_main_preteacher_review.json');pre=read(pp);tp=R/(tag+'_composed_observation_completion.json');t=read(tp)
 unknown=[];consequential=[]
 if n==15:
  m=read(Path(read(pre['independent_native64']['path'])['job'])/'manifest.json')
  mid=lambda a,b:str((F(m['frames'][a]['local_seconds_exact'])+F(m['frames'][b]['local_seconds_exact']))/2)
  unknown=[[mid(16,17),mid(19,20)]];consequential=pre['consequential_unknowns']
 differences=pre['explicit_disagreements']+[
  'Original CLI32 exact tool-count/sequence audit remains REJECTED for both windows. Separate root media composition uses only its actual64native/clip/effective8 DONE and real facts/proposal;11 reads of the same frozen index are individually retained outside media, and three bare nonmedia error_message records have no known cause. No failed media tool, retry or original PASS is invented.',
  'Teacher marks all segments NO because it requires a full long action or treats montage as ordinary. Root follows the frozen visual editorial standard: a short clear typical image can be salient without proving an entire physical service is complete. Native64 and actual effective64, not only Gemini8previews, determine student visibility.',
  'Breed, professional role, audio absence, purpose, rest and eye movement claimed by teacher are not adopted as target facts; observed body, hands, tools and visible static image relations are used.',
  'Every ordinary/repetitive NO range was reviewed separately; teacher decimal cut ranges do not override exact adjacent-frame editing brackets.'
 ]
 if n==14:
  differences += ['Teacher F58..61 asserts ear cleaning/care. Actual root nativeF58 and original preteacher native/effectiveF58/F60/F61 show separated head-side hair, a ring-handle metal tool with white end and hands. This clear short relation is KEEP; cleaning location, hair plucking, tool purpose and completed grooming remain outside the target.',
   'Teacher8preview slots skip the selectedF58..61 event. This does not mean student64 cannot see it; actual original effectiveF58/F60/F61 are clear. Long repetitive holding/interview and final occluded cage scene remain NO.']
 else:
  differences += ['Towel against brown curly dog and hand/tool near lifted black-brown dog paw are two distinct short visible typical images at F03..06 and F07..10. No dryness, cut hairs, full grooming or paw treatment completion is claimed.',
   'Teacher F19 asserts scissors trim paw hair. Actual root recheckF19 shows gray-dog lifted forepaw and lower blurred metal object, without clear contact/result. Preteacher F17..19 remains UNKNOWN; no NO/KEEP is assigned to satisfy coverage.',
   'Partly closed eyes at boundedF31 are a static state, not proven blink movement. Commodity packaging labels and shelf movements do not become audio or purpose targets.']
 value=dict(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),window_id=pre['window_id'],
  candidate_prediction_exposure=False,root_read_all64_teacher_facts=True,root_read_all64_native_and_student_facts=True,all_NO_ranges_reviewed=True,
  selected_preteacher_event_indices=[0] if n==14 else [0,1],unknown_local_exact=unknown,consequential_unknowns=consequential,
  evidence=dict(preteacher_main_review=bind(pp),teacher_observation_audit=bind(tp),original_teacher_proposal=t['proposal'],
   original_teacher_program_bound_facts=t['program_bound_facts'],composed_protocol=t['protocol'],original_strict_audit=t['original_strict_audit'],
   actual_media_inventory=t['actual_media_inventory'],bounded_student_reinspection=bind(R/'student_reviews'/(wname+'.student_bounded_reinspection_v1.json')),
   bounded_student_acceptance=bind(R/(tag+'_bounded_student_acceptance.json'))),
  differences_adjudicated=differences,
  actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],student_sample_indices=pre['root_actually_viewed_student_samples'],
   additional_postteacher_native_samples=[58] if n==14 else [19],read_native_static_facts=64,read_student_static_facts=64,read_teacher_static_facts=64,
   read_bounded_student_facts=8,root_direct64_image_review=False,root_native_video_view=False,original_Gemini_strict_failed=True),
  reference_scope_and_reason='Evaluation-only finite visual editorial silver from explicitly composed actual media. Clear representative dog/hand/tool images are independently adjudicated, purpose and entire service completion are not targets. Gray-dog blurred tool-contact uncertainty is retained where present. Original strict CLI32 failure remains immutable; not human gold or official quality.')
 op=R/(tag+'_root_eval_decision.json')
 with op.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
 print(json.dumps(bind(op),ensure_ascii=False))

