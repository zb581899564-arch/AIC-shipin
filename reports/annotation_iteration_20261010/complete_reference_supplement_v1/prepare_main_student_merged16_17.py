"""Root preteacher finite editing judgments; original physical UNKNOWN preserved."""
import json,hashlib,copy
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction as F
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
for n,tag,wname,student_indices in [(16,'16_eyq_w03','16_EYqVtI9YWJA_W03',[17,20,45,52]),(17,'17_eyq_w04','17_EYqVtI9YWJA_W04',[31,33,53,55,57])]:
 p=R/(tag+'_main_native_preteacher_review.json');old=read(p);out=copy.deepcopy(old)
 sp=R/'student_reviews'/(wname+'.independent_student64_review_v1.json');s=read(sp)
 assert s['window_id']==old['window_id'] and not s['teacher_content_received'] and not s['candidate_predictions_received']
 assert s['actual_viewing']['effective_input_pngs_visually_inspected']==64 and len(s['student_view_inventory'])==64
 receipt=read(Path(s['machine_binding']['student_receipt_path']));assert receipt['patch_inverse_exact']
 for a,b in zip(s['student_view_inventory'],receipt['frames']):
  assert a['frame_id']==b['frame_id'] and a['source_ordinal']==b['source_ordinal'] and a['png_sha256']==b['png_sha256']
  assert bind(Path(a['path']))['sha256']==a['png_sha256']
 out.update(status='MAIN_PRETEACHER_FINITE_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),
  previous_native_only_review=bind(p),student_content_read=True,independent_student64=bind(sp),
  root_read_all64_native_static_facts_and_all64_student_static_facts=True,root_actually_viewed_student_samples=student_indices,
  events=copy.deepcopy(old['provisional_events']),all_no_reasons_reviewed=True,evaluation_reference_only=True)
 out.pop('provisional_events');out.pop('no_sample_ranges');out.pop('boundary_tasks_requested')
 if n==16:
  acc=read(R/'16_eyq_w03_boundary_observations_acceptance.json')
  out['boundary_observations']=bind(R/'16_eyq_w03_boundary_observations_acceptance.json')
  out['student_arithmetic_erratum']=bind(R/'student_reviews/16_EYqVtI9YWJA_W03.student_boundary_arithmetic_errata_v1.json')
  out['events'][0]['editing_start_range_local_exact']=acc['task07_start_range_local_exact']
  out['events'][3]['editing_end_range_local_exact']=acc['task08_end_range_local_exact']
  last=out['events'][4];last.update(first=45,last=52,type='short_paired_wheel_high_typical_image',
   description='两车前轮高举、两骑手共同驶远的短清楚典型画面；不声称最终降轮或全跳跃完成',
   editing_start_range_local_exact=[receipt['frames'][44]['local_seconds_exact'],receipt['frames'][45]['local_seconds_exact']],
   necessary_preparation='F44与已观察中间帧均模糊/下沿截断，不将不清准备作为该典型图像目标',
   visible_result='F45..52两车前轮高位和共同驶远清楚可见；物理最终降轮未知且不作为目标')
  out['complete_domain_editorial_decision_by_samples']=[
   dict(first=0,last=15,decision='NO',reason='普通访谈及手势'),
   dict(first=16,last=18,decision='KEEP',event_index=0),dict(first=19,last=25,decision='KEEP',event_index=1),
   dict(first=26,last=28,decision='KEEP',event_index=2),dict(first=29,last=34,decision='NO',reason='普通缓骑定位'),
   dict(first=35,last=39,decision='KEEP',event_index=3),dict(first=40,last=44,decision='NO',reason='普通缓骑及模糊截断准备，未形成清楚典型姿态'),
   dict(first=45,last=52,decision='KEEP',event_index=4),dict(first=53,last=63,decision='NO',reason='普通访谈及笑貌手势')]
  out['explicit_disagreements']=[
   'Student physical start/completion UNKNOWN is preserved in the sealed initial review; finite representative-image boundaries are not an assertion of unseen physical preparation, precise tyre contact or full display completion.',
   'Actual registered probes narrow the scene entrance and post-turn editing limits only. No student64 sample or source clock changed.',
   'Student16 original F18/F19 arithmetic error is preserved with its program-derived erratum: actual gap7007/15000, not1001/2000. F44/F45 is also7007/15000; pose visibility rather than time gap limits full physical onset.',
   'The paired image starts at clear F45, not blurred/cropped F44; observed probe09 does not create an invented preparation. F52 still has raised wheels before scene exit.'
  ]
 else:
  accpath=R/'17_eyq_w04_boundary_observations_acceptance.json';acc=read(accpath)
  out['boundary_observations']=bind(accpath)
  out['events'][3]['editing_end_range_local_exact']=read(Path(acc['observations'][0]['path']))['reviewed_editing_range_local_exact']
  out['events'][4]['editing_start_range_local_exact']=out['events'][3]['editing_end_range_local_exact']
  out['events'][4]['editing_end_range_local_exact']=read(Path(acc['observations'][1]['path']))['reviewed_editing_range_local_exact']
  out['events'][4].update(necessary_preparation='实际地面转身进入前轮支地、后轮高位的清楚近景',
   visible_result='F57 actual effective input完整高位后轮可见；后续近轮画面和切访谈是有限编辑域，不声称后轮最终落地')
  out['complete_domain_editorial_decision_by_samples']=[dict(first=0,last=25,decision='NO',reason='普通访谈笑貌及手势')]+[
   dict(first=e['first'],last=e['last'],decision='KEEP',event_index=i) for i,e in enumerate(out['events'])]+[
   dict(first=60,last=63,decision='NO',reason='普通访谈及手势')]
  out['explicit_disagreements']=[
   'The ramp event includes visible ground approach, airborne wheels and two-wheel platform result. Its editing entrance F25/F26 does not invent the exact front-wheel lift onset; internal F27/F28 gap1001/2000 remains a physical onset limitation.',
   'Platform wheel-turn, short rear-wheel lift, departure-to-ground and final ground-turn representative images remain separate events; touching output intervals do not merge their semantic identities.',
   'Student F57 original caption misses the visible high rear wheel. Root actually checked original effectiveF57: rear wheel fully visible at right, front wheel supporting ground. This root-exposed correction is not a new independent blind initial judgment.',
   'Final rear-wheel landing is still obscured before interview. Registered probes narrow finite post-landing editorial division and scene end only, not the physical landing or exact cut.'
  ]
 for e in out['events']:
  for key in ['editing_start_range_local_exact','editing_end_range_local_exact']:
   a,b=map(F,e[key]);assert 0<=a<=b<=30 and b-a<=F('.5')
 out['all_selected_editing_boundary_ranges_at_most_half_second']=True
 out['interpretation_limit']='Preteacher finite visual editing judgment only. Original independent physical UNKNOWN stays preserved; no final complete reference admission before actual teacher/effective input comparison. No gold, audio or unseen physical result.'
 target=R/(tag+'_main_preteacher_review_v2.json')
 with target.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
 print(json.dumps(bind(target),ensure_ascii=False))
