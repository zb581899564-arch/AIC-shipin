"""Record actual root pre-teacher finite editing judgments; no reference admission."""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
m=read(R.parent/'slot6_silver24_v1/observations/11_byxOvuiIJV0_W04/manifest.json')
def gap(a,b):return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
events=[]
for first,last,kind,description,result in [
 (1,6,'closed_visible_action','单手支撑侧翻的准备、倒置、落脚和重新站立','F06实际重新站立，动作结果可见'),
 (7,15,'visible_pose_milestone','低位地板动作进入双手支撑倒置姿态','F14与F15实际腿抬高和张开倒置；目标止于可见姿态，不声称其后落地或整套舞蹈完成'),
 (16,22,'clear_typical_image','高位清楚宽景中的成排群舞典型画面','全队与围观空间关系清楚，末帧多人抬臂')]:
    events.append(dict(first=first,last=last,type=kind,description=description,visible_result=result,
      editing_start_range_local_exact=gap(first-1,first),editing_end_range_local_exact=gap(last,last+1),
      physical_landing_after_F15_observed=False if first==7 else None))
out=dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER_AND_BOUNDARY_OBSERVATIONS',
 utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],teacher_content_read=False,
 root_candidate_prediction_exposure=False,root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[0,1,4,6,13,14,15,16,22,23],root_actually_viewed_student_samples=[4,6,14,15],
 root_did_not_claim_all64_direct_image_views=True,
 independent_native64=bind(R/'native_reviews/11_byxOvuiIJV0_W04.native_review.json'),
 independent_student64=bind(R/'student_reviews/11_byxOvuiIJV0_W04.independent_student64_review_v1.json'),
 events=events,complete_domain_editorial_decision_by_samples=[
 dict(first=0,last=0,decision='NO',reason='旁观者抬手的前镜头尾部，非所选支撑动作的必要准备'),
 dict(first=1,last=6,decision='KEEP',event_index=0),dict(first=7,last=15,decision='KEEP',event_index=1),
 dict(first=16,last=22,decision='KEEP',event_index=2),
 dict(first=23,last=45,decision='NO',reason='同群舞转为斜近景、遮挡、模糊与队列打散；选过清楚代表宽景后的重复过程，无额外清楚短时亮点'),
 dict(first=46,last=56,decision='NO',reason='普通拥挤街道人流和抬镜头过渡，没有独立突出结果'),
 dict(first=57,last=57,decision='NO',reason='实际黑画面'),
 dict(first=58,last=63,decision='NO',reason='静态Management TEAM片尾合照，未选常规署名展示')],
 explicit_disagreements=['独立初判指出F15后落地未见；保留这个事实。主控选择实际已形成的支撑倒置姿态作为有限画面目标，未把切镜当作落地完成。',
 '连续KEEP的三个事件仍分别记录，不因相接合并事件；训练时间区间可按集合正常并合。'],
 boundary_remaining='F15/F16与F22/F23实际间隙各1001/2000秒；须有登记的实际中间原生图观察，不自动缩窄。',
 all_no_reasons_reviewed=True,training_admitted=False,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'11_byx_w04_main_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':out['status'],'review':bind(R/'11_byx_w04_main_preteacher_review.json')},ensure_ascii=False))
