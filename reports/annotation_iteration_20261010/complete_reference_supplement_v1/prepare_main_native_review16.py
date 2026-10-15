"""Freeze the root's actually observed native evidence before boundary probes."""
import json, hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
R=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p): return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/16_EYqVtI9YWJA_W03/manifest.json')
def bracket(a,b):
    return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
out=dict(status='MAIN_NATIVE_ONLY_PRETEACHER_REVIEW_PENDING_STUDENT_AND_LAWFUL_TEACHER',
 utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],teacher_content_read=False,
 root_candidate_prediction_exposure=False,student_content_read=False,
 root_read_all64_native_static_facts=True,root_direct64_image_review=False,
 root_actually_viewed_native_samples=[16,17,19,20,25,26,28,34,35,36,38,39,40,44,45,52,53],
 independent_native64=bind(R/'native_reviews/16_EYqVtI9YWJA_W03.native_review.json'),
 observed_vehicle_fact='Vehicles show engines, exhaust and wide tyres: motorcycle stunt display; do not call them BMX bicycles.',
 provisional_events=[
  dict(first=16,last=18,type='clear_typical_front_wheel_lift',description='切入已高抬前轮，F17清楚近竖直抬轮姿态，F19两轮近地',
       preparation_status='UNKNOWN_CUT_ENTERS_MID_ACTION',editing_start_range_local_exact=bracket(15,16),editing_end_range_local_exact=bracket(18,19)),
  dict(first=19,last=25,type='rear_wheel_lift',description='红蓝白骑手F19两轮近地前倾，F20后轮高抬以前轮行进，F25两轮地面',
       editing_start_range_local_exact=bracket(18,19),editing_end_range_local_exact=bracket(25,26)),
  dict(first=26,last=28,type='second_rider_short_rear_wheel_lift',description='黑衣骑手F26后轮短抬，后续趋于水平；F28低清像素不能单独证明精确接地时刻',
       physical_contact_time='UNKNOWN_NOT_INVENTED',editing_start_range_local_exact=bracket(25,26),editing_end_range_local_exact=bracket(28,29)),
  dict(first=35,last=39,type='lifted_front_wheel_turn',description='屈膝至前轮抬起并转身，F38/39车体近水平、朝左骑行',
       editing_start_range_local_exact=bracket(34,35),editing_end_range_local_exact=bracket(39,40)),
  dict(first=44,last=52,type='paired_front_wheel_lift',description='两名骑手同步抬前轮驶远，F52仍抬轮，F53切访谈',
       result_status='UNKNOWN_CUT_BEFORE_FRONT_WHEEL_LOWERED',editing_start_range_local_exact=bracket(43,44),editing_end_range_local_exact=bracket(52,53))],
 no_sample_ranges=[dict(first=0,last=15,reason='普通访谈及反复手势，无音频推断'),
  dict(first=29,last=34,reason='普通站立缓骑定位'),dict(first=40,last=43,reason='动作后普通缓骑定位'),
  dict(first=53,last=63,reason='访谈笑貌及举手，无独立突出视觉结果')],
 boundary_tasks_requested=[dict(left=15,right=16),dict(left=39,right=40),dict(left=43,right=44)],
 interpretation_limit='Finite editing value and observed scene limits are separate from exact tyre contact, unseen preparation or physical action completion. No full editing target is admitted before student and teacher review.',
 training_admitted=False,all_boundaries_adjudicated=False,new_model_calls=0,new_optimizer_updates=0)
with (R/'16_eyq_w03_main_native_preteacher_review.json').open('x',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(R/'16_eyq_w03_main_native_preteacher_review.json')))
