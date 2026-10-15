"""Root's finite editing decisions, separately from teachers' original proposals."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
from PIL import Image
R=Path(__file__).resolve().parent;O=R.parent/'slot6_silver24_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
plan_path=R/'student_reviews/bounded_reinspection_fixed_plan_v2.json';plan=read(plan_path)
assert sha(plan_path)=='678f90aea5c01cc127c700d66ff48b028c59d91e599d3bee8daed3e9636d7947'
for ix,stem,short,teacherfile,pre in [
 (9,'09_WxtbjNsCQ8A_W05','09_wxt_w05','09_teacher_completed_pair_observation.json','09_wxt_w05_main_preteacher_review.json'),
 (10,'10_byxOvuiIJV0_W02','10_byx_w02','10_byx_w02_lawful_observation_completion.json','10_byx_w02_main_preteacher_review.json')]:
 p=R/'student_reviews'/(stem+'.student_bounded_reinspection_v1.json');s=read(p)
 seal=read(p.with_name(p.stem+'.seal.json'))
 assert sha(p)==seal['review_sha256'] and s['fixed_job_index']==ix and s['not_new_blind_initial']
 assert not any(s[k] for k in ('teacher_content_received','scores_received','candidate_predictions_received','root_final_content_read'))
 assert s['material_scene_subject_object_action_error_found'] is False
 assert sha(s['original_review_path'])==s['original_review_sha256']
 fixed=next(x for x in plan['windows'] if x['job_index']==ix)
 assert fixed['review_sha256']==s['original_review_sha256']
 receipt=read(s['machine_binding']['student_receipt_path'])
 assert sha(s['machine_binding']['student_receipt_path'])==s['machine_binding']['student_receipt_sha256']
 assert receipt['patch_inverse_exact'] is True and len(receipt['frames'])==64
 assert [row['frame_id'] for row in s['selected_slot_inventory']]==[f'F{i:02d}' for i in fixed['slots']]
 for row, frozen in zip(s['selected_slot_inventory'],fixed['input_binding']):
  frame=receipt['frames'][int(row['frame_id'][1:])]
  for k in ('frame_id','path','png_sha256','rgb_pixel_sha256'):
   assert row[k]==frozen[k]==frame[k]
  for k in ('source_ordinal','global_seconds_exact','local_seconds_exact'):assert row[k]==frame[k]
  assert row['tool_supply']['status']=='SUCCESS_IMAGE_RETURNED_AND_EMITTED'
  assert row['tool_supply']['path']==row['path'] and row['tool_supply']['frame_id']==row['frame_id']
  assert sha(row['path'])==row['png_sha256']==row['actual_png_sha256']
  with Image.open(row['path']) as im:assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==row['rgb_pixel_sha256']==row['actual_rgb_pixel_sha256']
  assert row['fresh_visible_static_fact'] and row['original_sealed_fact']
 acc=R/(short+'_bounded_student_acceptance.json')
 save(acc,dict(status='PASS_ROOT_READ_ALL_SELECTED_FRESH_FACTS_AND_ACTUAL_BINDINGS_NOT_ALL64_CAPTION_CERTIFICATION',
  utc=datetime.now(timezone.utc).isoformat(),bounded_reinspection=bind(p),original_blind_student=bind(s['original_review_path']),
  actual_selected_images=len(fixed['slots']),current_selected_png_rgb_pts_bindings_checked=True,
  detail_qualifications=s['detail_qualifications'],teacher_exposure=False,root_direct_new_image_views=0,
  old_initial_not_relabelled_blind=True,new_model_calls=0,new_optimizer_updates=0))
 main=read(R/pre);native_path=Path(main['independent_native64']['path']);native=read(native_path)
 assert not native['teacher_content_received'] and not native['student_content_received'] and not native['candidatePredictionExposure']
 wrapper=R/(short+'_independent_native_blind_binding.json')
 save(wrapper,dict(status='BOUND_REAL_PRETEACHER_NATIVE64_REVIEW_NOT_NEW_IMAGE_OBSERVATION',
  window_id=main['window_id'],blind_attestation=dict(teacher_content_received=False,candidate_prediction_received=False,student_content_received=False),
  sealed_native_review=bind(native_path),actual_native_images=64,root_not_blind=True,training_admitted=False))
 evs=json.loads(json.dumps(main['events']))
 if ix==10:
  evs[0]['editing_end_range_local_exact']=read(R/'boundary_phase_v2_task05/main_observation.json')['reviewed_editing_end_range_local_exact']
  evs[1]['editing_start_range_local_exact']=read(R/'boundary_phase_v2_task06/main_observation.json')['reviewed_editing_start_range_local_exact']
 keep=[];bds=[];events=[]
 for n,e in enumerate(evs):
  ranges=[e['editing_start_range_local_exact'],e['editing_end_range_local_exact']]
  assert all(F(b)-F(a)<=F('.5') for a,b in ranges)
  interval=[str(sum(map(F,pair))/2) for pair in ranges];keep.append(interval)
  events.append(dict(event_id='M'+str(n+1),local=interval,visible_fact=e['description'],
   necessary_preparation=e.get('necessary_preparation','短代表画面的清楚关系建立；不推断整个活动开端'),
   visible_result=e.get('visible_result','该短代表画面的实际可见布局；不声明整场活动完成'),
   evidence_frame_ids=[f'F{i:02d}' for i in range(e['first'],e['last']+1)],
   editing_boundary_midpoints_not_measured_cuts=True))
  for kind,pair in zip(('start','end'),ranges):
   bds.append(dict(uncertainty_start_exact=pair[0],uncertainty_end_exact=pair[1],time_basis='LOCAL',
    inside_evidence=f"F{e['first'] if kind=='start' else e['last']:02d}",
    outside_evidence_or_domain_boundary='Root preteacher segment and separately bound native interior observation where applicable; see evidence',
    editing_boundary_only=True))
 no=[];last=F(0)
 for a,b in keep:
  if F(a)>last:no.append([str(last),a])
  last=F(b)
 if last<F(30):no.append([str(last),'30'])
 teacher=read(R/teacherfile)
 evidence=dict(teacher_observation_audit=bind(R/teacherfile),blind_initial=bind(wrapper),
  blind_student_visibility=bind(s['original_review_path']),student_processor=bind(s['machine_binding']['student_receipt_path']),
  bounded_student_reinspection=bind(p),bounded_student_acceptance=bind(acc),preteacher_main_review=bind(R/pre),
  original_teacher_proposal=teacher['proposal'],original_teacher_program_bound_facts=teacher['program_bound_facts'])
 differences=list(main['explicit_disagreements'])
 if ix==9:
  differences+=['Teacher all-NO is retained as original disagreement. Its F45..50 opening description conflicts with visible downward lid closure, and F55 is still gapped while F56 covers the box. Blue/white lower-third and held jar pixels do not justify invented opening or honey content.',
   'Root retains the short clear bee/entrance typical image and actual lid-lowering with visible covered result under the fixed editing definition. Student uncertainty about a broader unseen task remains in its original initial; this finite closure target does not infer prior opening or later work.',
   'F55/F56 physical contact bracket of 1001/2000 is preserved. Editing endpoint follows the observed covered result at F58/F59; it is not an exact lid-contact time.']
 else:
  evidence['boundary_native_observations']=bind(R/'10_byx_w02_boundary_observation_acceptance.json')
  differences+=['Teacher proposes only a longer floor-dance segment. Root independently retains one short clear frontal group image plus coat flourish/low turn/coat-on-ground and upright result. No difficult leg technique or complete dance endpoint is inferred from blurred pixels.',
   'Teacher calls 8 preview images the student input; actual student input has64 processor-bound effective images and independent64 review. Teacher preview wording and audio-absence statement are not ground truth.',
   'Two original editing gaps of1001/2000 are preserved and narrowed only through the actually registered and viewed O1615/O1923 observations, each remaining1001/4000. No floor64 sampling changed.',
   'Bounded reinspection qualifies F00 gender and F42 arm pose. Neither qualification changes the selected clear group layout or coat-on-ground result; no gender or both-arm claim enters this target.']
 final=dict(status='ROOT_FINAL_COMPLETE_FINITE_EDITORIAL_REFERENCE_ADJUDICATED',utc=datetime.now(timezone.utc).isoformat(),
  window_id=main['window_id'],root_semantic_adjudication_complete=True,candidate_prediction_exposure_before_freeze=False,
  keep_local_exact=keep,no_local_exact=no,unknown_local_exact=[],events=events,boundary_decisions=bds,
  consequential_unknowns=[],explicit_no_highlight=False,all_target_boundaries_adjudicated=True,
  student_observable_complete_target=True,training_admitted=True,
  main_review_assertions={k:True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented',
   'necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
  evidence=evidence,actual_root_observation_scope=dict(native_sample_indices=main['root_actually_viewed_native_samples'],
   student_sample_indices=main['root_actually_viewed_student_samples'],read_native_static_facts=64,read_student_static_facts=64,
   read_teacher_static_facts=64,read_selected_bounded_student_facts=len(fixed['slots']),root_direct64_image_review=False),
  all_NO_sample_ranges=[v for v in main['complete_domain_editorial_decision_by_samples'] if v['decision']=='NO'],
  differences_adjudicated=differences,not_derived_from_training_quota=True,
  reference_scope_and_reason='Complete finite visual editing silver target: separately adjudicated visible facts, full NO reasons, clear preparation/result or typical-image scope, student visibility and bounded editing endpoints. Not gold, exhaustive motion/audio truth or official score.')
 save(R/(short+'_final_main_review.json'),final)
 print(json.dumps(dict(job=ix,final_main_review=bind(R/(short+'_final_main_review.json')),keep=keep),ensure_ascii=False))
