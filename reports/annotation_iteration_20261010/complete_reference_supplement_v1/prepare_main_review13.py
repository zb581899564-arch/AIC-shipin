import json, hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
R = Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p): return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m = read(R.parent/'slot6_silver24_v1/observations/13_-esJrBWj2d8_W06/manifest.json')
gap = [m['frames'][8]['local_seconds_exact'],m['frames'][9]['local_seconds_exact']]
assert F(gap[1])-F(gap[0]) <= F('0.5')
out = dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],
 teacher_content_read=False,root_candidate_prediction_exposure=False,root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[0,6,8,9,27,28,34,38,39,43,51,58,63],root_actually_viewed_student_samples=[0,8,34,39],
 root_did_not_claim_all64_direct_image_views=True,independent_native64=bind(R/'native_reviews/13_-esJrBWj2d8_W06.native_review.json'),
 independent_student64=bind(R/'student_reviews/13_-esJrBWj2d8_W06.independent_student64_review_v1.json'),
 events=[dict(first=0,last=8,type='clear_typical_reclining_cat_image',description='橘条纹猫侧卧椅垫，四肢叠放、完整躯干与脸朝镜头的短代表画面',
   editing_start_domain_boundary=True,editing_end_range_local_exact=gap,
   not_claiming_emotion_or_sleep=True,not_claiming_physical_event_completion=True)],
 complete_domain_editorial_decision_by_samples=[dict(first=0,last=8,decision='KEEP',event_index=0),
   dict(first=9,last=27,decision='NO',reason='同一侧卧猫脸/全身构图持续重复，眨眼和尾端小动不独立增加视觉高光'),
   dict(first=28,last=42,decision='NO',reason='胸腹普通温和抚摸后撤手可见且局部完整，但显著反应或新结果不足；不将闭眼解释为情绪且抚摸前F10..11已闭眼'),
   dict(first=43,last=50,decision='NO',reason='普通喂食器、花盘残块与散落碎屑静物；不推断内容和健康'),
   dict(first=51,last=58,decision='NO',reason='花盘普通拉近再推回摆放，目的与成分未知，无显著操作结果'),
   dict(first=59,last=63,decision='NO',reason='同一碗盘与残块静物重复停留')],
 explicit_disagreements=['学生初判保留局部完整抚摸，完整性可见不等于必选高光；主控对视觉价值作独立NO裁决，保留初判不改写。',
   '原生初判0..27是典型猫图像支持域，不要求整段剪入。主控选短代表0..8，剩余重复明确NO；F8/F9是编辑区间而非声称镜头切点。'],
 all_no_reasons_reviewed=True,all_selected_editing_boundary_ranges_at_most_half_second=True,
 evaluation_reference_only=True,training_admitted=False,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'13_esjr_w06_main_preteacher_review.json').open('x',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],review=bind(R/'13_esjr_w06_main_preteacher_review.json')),ensure_ascii=False))
