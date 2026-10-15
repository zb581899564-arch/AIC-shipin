import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/10_byxOvuiIJV0_W02/manifest.json')
def gap(a,b):return [m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
out=dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER_AND_BOUNDARY_OBSERVATIONS',
 utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],teacher_content_read=False,root_candidate_prediction_exposure=False,
 root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[0,4,10,16,22,23,37,42,43,45,48,49,50,54,55,63],root_actually_viewed_student_samples=[10,43,45,49],
 root_did_not_claim_all64_direct_image_views=True,
 independent_native64=bind(R/'native_reviews/10_byxOvuiIJV0_W02.native_review.json'),
 independent_student64=bind(R/'student_reviews/10_byxOvuiIJV0_W02.independent_student64_review_v1.json'),
 events=[dict(first=10,last=15,type='clear_typical_image',description='高位正面完整队列群舞、围观人群与街道布局的清楚代表画面',
   editing_start_range_local_exact=gap(9,10),editing_end_range_local_exact=gap(15,16),physical_dance_completion_not_claimed=True),
 dict(first=43,last=49,type='visible_coat_flourish_to_standing_result',description='单人挥动黑外套，降低身体/转身，将外套留在地面并站回双腿展开姿态',
   necessary_preparation='F43持衣展开的动作起始画面',visible_result='F48外套已在左地面；F49双腿展开直立，外套仍在左地面',
   editing_start_range_local_exact=gap(42,43),editing_end_range_local_exact=gap(49,50),
   entire_following_dance_completion_not_claimed=True)],
 complete_domain_editorial_decision_by_samples=[dict(first=0,last=9,decision='NO',reason='局部近景与背面宽景的常态队列舞步；用后续清楚正面全队列代表这一群舞，不重复保留每个机位'),
 dict(first=10,last=15,decision='KEEP',event_index=0),dict(first=16,last=22,decision='NO',reason='正面代表画面之后的侧面同类手臂和跨步重复，没有独立突出结果'),
 dict(first=23,last=36,decision='NO',reason='网格后旁观者、普通车流、旗布和过曝天空过渡；无可见完整独立动作亮点'),
 dict(first=37,last=42,decision='NO',reason='中央舞者站立展臂和外围群舞，与已选表演布局重复，实际外套动作准备从F43开始'),
 dict(first=43,last=49,decision='KEEP',event_index=1),dict(first=50,last=54,decision='NO',reason='外套已落地且站姿已保留后的逆光常态展开手臂/重心转换'),
 dict(first=55,last=63,decision='NO',reason='近景常态手臂伸展，没有新明显支撑/翻转/释放结果；不把窗口末尾当作舞蹈完成')],
 explicit_disagreements=['原生初判对八个机位分别KEEP；主控没有把八个事件合成少数事件，而对重复机位明确NO，只保留清楚正面代表画面与具有可见结果的独立外套动作。',
 '学生初判对整段舞蹈/地板转身的后续完成存疑；此事实保留，目标仅为外套从手中到地面并站立的已见局部结果，不声称整套舞蹈完成。'],
 boundary_remaining='F15/F16与F42/F43间隙各1001/2000秒，须实际登记中间帧观察，不自动缩窄。',
 editorial_choice_not_derived_from_event_quota=True,all_no_reasons_reviewed=True,training_admitted=False,
 new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'10_byx_w02_main_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],review=bind(R/'10_byx_w02_main_preteacher_review.json')),ensure_ascii=False))
