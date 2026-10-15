"""Root's observed motorcycle highlight sequence before teacher exposure."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/17_EYqVtI9YWJA_W04/manifest.json')
def gap(a,b):return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
out=dict(status='MAIN_NATIVE_ONLY_PRETEACHER_REVIEW_PENDING_STUDENT_AND_LAWFUL_TEACHER',
 utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],teacher_content_read=False,
 root_candidate_prediction_exposure=False,student_content_read=False,root_read_all64_native_static_facts=True,
 root_direct64_image_review=False,root_actually_viewed_native_samples=[25,26,28,31,33,34,35,37,38,43,44,45,46,48,50,51,53,55,56,57,58,59,60],
 independent_native64=bind(R/'native_reviews/17_EYqVtI9YWJA_W04.native_review.json'),
 provisional_events=[
  dict(first=26,last=33,type='ramp_airborne_to_platform',description='接近斜坡、抬前轮上坡、双轮悬空跨向台面，F33双轮在台顶',
       editing_start_range_local_exact=gap(25,26),editing_end_range_local_exact=gap(33,34)),
  dict(first=34,last=44,type='platform_wheel_support_turn',description='台上抬轮并转身，F38前轮支台而后轮抬起，F43前轮抬起，F44车体近水平朝右',
       editing_start_range_local_exact=gap(33,34),editing_end_range_local_exact=gap(44,45),
       not_claiming_exact_angle_or_unseen_hops=True),
  dict(first=45,last=50,type='platform_rear_wheel_balance',description='台顶前倾抬后轮、降低和回近水平；台缘/低清细节不足测精确轮胎接触瞬间',
       editing_start_range_local_exact=gap(44,45),editing_end_range_local_exact=gap(50,51),
       exact_contact_time='UNKNOWN_NOT_INVENTED'),
  dict(first=51,last=55,type='airborne_off_platform_to_ground',description='台顶屈膝至双轮悬空离台，F55车在地面双轮骑行',
       editing_start_range_local_exact=gap(50,51),editing_end_range_local_exact=gap(55,56)),
  dict(first=56,last=59,type='ground_front_wheel_support_typical_image',description='地面转身，F57清楚前轮支地后轮高抬，后续正面车和轮近景',
       editing_start_range_local_exact=gap(55,56),editing_end_range_local_exact=gap(59,60),
       physical_result_status='UNKNOWN_REAR_WHEEL_CONTACT_OBSCURED_BEFORE_INTERVIEW_CUT')],
 no_sample_ranges=[dict(first=0,last=25,reason='普通访谈、手势与笑貌，无音频叙事推断'),
                   dict(first=60,last=63,reason='切回普通访谈手势，没有新的突出视觉动作')],
 boundary_tasks_requested=[dict(left=55,right=56),dict(left=59,right=60)],
 interpretation_limit='Finite highlight image/action evidence is visible; precise tyre contact and last physical action completion are not. This provisional record does not erase original UNKNOWN or admit a complete editing reference before independent student/teacher comparison.',
 training_admitted=False,all_target_boundaries_adjudicated=False,new_model_calls=0,new_optimizer_updates=0)
with (R/'17_eyq_w04_main_native_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(R/'17_eyq_w04_main_native_preteacher_review.json')))
