import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/12_-esJrBWj2d8_W01/manifest.json')
def gap(a,b):
 v=[m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']];assert F(v[1])-F(v[0])<=F('0.5');return v
out=dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],
 teacher_content_read=False,root_candidate_prediction_exposure=False,root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[4,5,7,14,18,24,25,27,28,44,51,52,58,59,60,63],root_actually_viewed_student_samples=[5,18,25,27,58],
 root_did_not_claim_all64_direct_image_views=True,independent_native64=bind(R/'native_reviews/12_-esJrBWj2d8_W01.native_review.json'),
 independent_student64=bind(R/'student_reviews/12_-esJrBWj2d8_W01.independent_student64_review_v1.json'),
 events=[dict(first=5,last=27,type='visible_foil_box_opening_to_withdrawn_hand_result',description='红封盖盒在木地板放稳、手沿盖边操作和抬起封盖，撤手后敞开盒及猫靠近盒中可见',
   necessary_preparation='F05..07初始红封盖盒与持盒手姿态',visible_result='F25封盖在手中、右手撤离，F26..27人起身而敞开盒与猫鼻口靠近可见',
   editing_start_range_local_exact=gap(4,5),editing_end_range_local_exact=gap(27,28),
   not_claiming_cat_finished_eating=True,not_claiming_exact_unobserved_foil_separation_time=True),
 dict(first=52,last=58,type='clear_typical_image',description='猫头近景、白边盒与棕色内容的清楚短代表画面，至抬头后内容表面清楚露出',
   editing_start_range_local_exact=gap(51,52),editing_end_range_local_exact=gap(58,59),not_claiming_swallowing=True)],
 complete_domain_editorial_decision_by_samples=[dict(first=0,last=4,decision='NO',reason='地毯上普通嗅看封盖盒，未见独立突出结果'),
 dict(first=5,last=27,decision='KEEP',event_index=0),dict(first=28,last=51,decision='NO',reason='撤手后的反复低头接触及较近相同姿态；所选更清楚的猫/盒内容短代表画面从F52起'),
 dict(first=52,last=58,decision='KEEP',event_index=1),dict(first=59,last=63,decision='NO',reason='内容表面已呈现，随后重复低头与换侧全身机位无新操作结果')],
 explicit_disagreements=['原生初判因遮挡不选开盒，学生把完整进食终止记UNKNOWN；主控保留这些初判，只对实际红封盖→抬盖→撤手敞开盒的可见局部结果作有限编辑裁决，没有标记进食结束。',
 '原生初判的44..63长期典型画面支持域不等于必须整段剪入；主控保留F52..58毛纹、盒与露出内容的短代表画面，重复低头和换侧机位另列NO。'],
 all_no_reasons_reviewed=True,all_selected_editing_boundary_ranges_at_most_half_second=True,
 evaluation_reference_only=True,training_admitted=False,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'12_esjr_w01_main_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],review=bind(R/'12_esjr_w01_main_preteacher_review.json')),ensure_ascii=False))
