import json, hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/14_i3wAGJaaktw_W02/manifest.json')
def gap(a,b):
 v=[m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
 assert F(v[1])-F(v[0])<=F('0.5');return v
out=dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],
 teacher_content_read=False,root_candidate_prediction_exposure=False,root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[0,12,14,18,23,37,43,57,58,59,60,61,62,63],root_actually_viewed_student_samples=[58,60,61],
 root_did_not_claim_all64_direct_image_views=True,independent_native64=bind(R/'native_reviews/14_i3wAGJaaktw_W02.native_review.json'),
 independent_student64=bind(R/'student_reviews/14_i3wAGJaaktw_W02.independent_student64_review_v1.json'),
 events=[dict(first=58,last=61,type='clear_typical_image_of_head_side_hand_and_tool',
   description='长毛小犬伏台、手分开头侧毛，另一手持金属夹环柄及白色端部工具靠近头侧的短代表近景',
   editing_start_range_local_exact=gap(57,58),editing_end_range_local_exact=gap(61,62),
   not_claiming_tool_purpose_or_ear_cleaning=True,not_claiming_completed_grooming_or_full_operation=True)],
 complete_domain_editorial_decision_by_samples=[dict(first=0,last=13,decision='NO',reason='大狗站台与人物普通布置/拿布/讲话姿态，没有突出操作结果'),
 dict(first=14,last=14,decision='NO',reason='叠化过渡'),dict(first=15,last=57,decision='NO',reason='普通扶背、托下颌、头部小变化与人物面向镜头嘴形，反复构图未见新视觉结果'),
 dict(first=58,last=61,decision='KEEP',event_index=0),dict(first=62,last=63,decision='NO',reason='栅栏及设备遮挡的趴卧犬，静态等待构图重复')],
 explicit_disagreements=['原生初判白刷状仅是外观近似，实际可见环柄金属夹及白色端部，撤回工具为刷子的确定解释；不推断清洁目的或部位。',
 '学生初判完整处理步骤及起止UNKNOWN保留。主控目标只为实际头毛、手与工具关系的清楚短代表镜头，编辑入出边界可见，不把未知完整疗程变成已完成动作。'],
 all_no_reasons_reviewed=True,all_selected_editing_boundary_ranges_at_most_half_second=True,
 evaluation_reference_only=True,training_admitted=False,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'14_i3w_w02_main_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],review=bind(R/'14_i3w_w02_main_preteacher_review.json')),ensure_ascii=False))
