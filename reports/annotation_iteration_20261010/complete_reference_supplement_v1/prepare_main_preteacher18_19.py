"""Root actual review: negative parking-window and finite tyre detail/removal."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
for n,stem,observed in [(18,'18_j0n_w02',[6,17,18,60,63]),(19,'19_j0n_w11',[4,7,14,16,18,51,52,54,58])]:
 np=next((R/'native_reviews').glob(f'{n:02d}*.native_review.json'));native=read(np);m=read(Path(native['job'])/'manifest.json')
 def gap(a,b):return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
 out=dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER' if n==18 else 'MAIN_NATIVE_ONLY_PRETEACHER_REVIEW_PENDING_STUDENT_AND_LAWFUL_TEACHER',
  utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],teacher_content_read=False,root_candidate_prediction_exposure=False,
  root_read_all64_native_static_facts=True,root_actually_viewed_native_samples=observed,root_direct64_image_review=False,
  independent_native64=bind(np),training_admitted=False,evaluation_reference_only=True,new_model_calls=0,new_optimizer_updates=0,
  all_no_reasons_reviewed=True)
 if n==18:
  sp=next((R/'student_reviews').glob('18*independent_student64_review_v1.json'));s=read(sp)
  assert len(s['student_view_inventory'])==64 and not s['teacher_content_received']
  out.update(independent_student64=bind(sp),root_read_all64_native_static_facts_and_all64_student_static_facts=True,
   root_actually_viewed_student_samples=[18,63],events=[],explicit_no_highlight=True,
   complete_domain_editorial_decision_by_samples=[dict(first=x['first'],last=x['last'],decision='NO',reason=x['reason']) for x in native['domain_segments']],
   explicit_disagreements=['Student initial NO is retained. Its target observable UNKNOWN refers to no retained physical event; it does not require inventing KEEP or an unseen impact. Root full finite sampled-domain editorial choice is NO with concrete segment reasons.',
    'Actual F06/F17/F18/F60/F63 show bending, holding a bent rod, ordinary reaching and unstable tilted framing, without a visible distinctive treatment/impact/result. No audio, argument, intent, damage or ground-object function is inferred.',
    'Full-domain NO is finite visual editing advice based on all64 supplied observations, not proof that no action could occur between samples.'],
   all_selected_editing_boundary_ranges_at_most_half_second=True)
 else:
  out.update(student_content_read=False,provisional_events=[
   dict(first=4,last=7,type='clear_typical_tyretread_detail',description='双手所持轮胎胎面与浅色沟槽的短清楚特写，手指示向纹路，不推断磨损诊断',
    editing_start_range_local_exact=gap(3,4),editing_end_range_local_exact=gap(7,8),not_full_physical_event=True),
   dict(first=14,last=18,type='wheel_out_from_arch',description='车旁俯身握轮到轮胎外倾移出，轮拱内圆形区域露出；仅局部取轮，不声称完整维修',
    editing_start_range_local_exact=gap(13,14),editing_end_range_local_exact=gap(18,19),
    necessary_preparation='F14..15车旁俯身、手与轮心附近小物',visible_result='F16..18轮胎移到轮拱外、黑色轮拱内圆形区域露出')],
   no_sample_ranges=[dict(first=0,last=3,reason='持胎姿态建立，清楚纹路代表画面见后短特写'),
    dict(first=8,last=13,reason='同一胎面反复手指示向，无新突出结果'),
    dict(first=19,last=51,reason='轮胎对位及轮心遮挡长操作，重复弯腰扶轮，完整安装紧固未显示'),
    dict(first=52,last=58,reason='手靠轮心后站起撤手可见，但与此前持续操作相同；紧固与完整安装结果不清，有限普通重复操作不独立选高光'),
    dict(first=59,last=63,reason='另一人步过和车旁站立普通遮挡')],
   explicit_disagreements=['Native initial E3 retains F52..58 as typical operation. Actual root F51/F52/F54/F58 shows routine wheel-center hand contact followed by standing, with no new salient visible object relation or proven installation result; root provisional editorial choice NO, original E3 is unchanged.',
    'Tyre detail is a short typical image; wheel removal is a separate visible local event. Unknown tightening or full repair does not become a positive target.'],
   boundary_tasks_requested=[dict(left=7,right=8)],all_boundaries_adjudicated=False)
 out['interpretation_limit']='Finite visible editing advice only; no audio, intent, between-sample motion or full repair completion inferred. Actual lawful teacher and student comparison still required before final reference.'
 op=R/(stem+('_main_preteacher_review.json' if n==18 else '_main_native_preteacher_review.json'))
 with op.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
 print(json.dumps(bind(op),ensure_ascii=False))
