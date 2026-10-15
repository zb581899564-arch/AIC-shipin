import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/15_i3wAGJaaktw_W03/manifest.json')
def gap(a,b):
 v=[m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
 assert F(v[1])-F(v[0])<=F('0.5');return v
out=dict(status='MAIN_PRETEACHER_PARTIAL_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),window_id=m['window_id'],
 teacher_content_read=False,root_candidate_prediction_exposure=False,root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[0,2,3,6,7,8,10,11,16,17,18,19,20,44,45,46,50,59,60,63],root_actually_viewed_student_samples=[6,8,17,19],
 root_did_not_claim_all64_direct_image_views=True,independent_native64=bind(R/'native_reviews/15_i3wAGJaaktw_W03.native_review.json'),
 independent_student64=bind(R/'student_reviews/15_i3wAGJaaktw_W03.independent_student64_review_v1.json'),
 events=[dict(first=3,last=6,type='typical_towel_and_dog_image',description='白毛巾贴棕卷毛犬身与人员手的位置变化，短操作代表画面',
   editing_start_range_local_exact=gap(2,3),editing_end_range_local_exact=gap(6,7),not_claiming_dryness_or_completed_towel_step=True),
 dict(first=7,last=10,type='clear_typical_paw_tool_image',description='小犬后腿被手抬起，黑色电推状工具贴爪毛且位置改变的近景',
   editing_start_range_local_exact=gap(6,7),editing_end_range_local_exact=gap(10,11),not_claiming_cut_hair_or_completed_full_step=True)],
 complete_domain_editorial_decision_by_samples=[dict(first=0,last=2,decision='NO',reason='笼内犬被栅栏与设备遮挡且近景焦点软'),
 dict(first=3,last=6,decision='KEEP',event_index=0),dict(first=7,last=10,decision='KEEP',event_index=1),
 dict(first=11,last=16,decision='NO',reason='大狗轻抚与头嘴小变化，重复叙述配画'),
 dict(first=17,last=19,decision='UNKNOWN',reason='灰犬抬前爪画面有显著模糊、工具与接触点不清，仅3张不足裁定新的清楚工具操作高光；不硬标NO或补完成结果'),
 dict(first=20,last=44,decision='NO',reason='固定人物头肩与嘴眼小变，不推断未听讲话'),dict(first=45,last=45,decision='NO',reason='叠化'),
 dict(first=46,last=59,decision='NO',reason='重复普通货架平移，包装反光/裁切，无突出结果'),dict(first=60,last=60,decision='NO',reason='叠化'),
 dict(first=61,last=63,decision='NO',reason='同类货架包装重复近景')],
 explicit_disagreements=['原生初判保留灰犬工具典型图像，但实际根部接触与工具位置模糊，主控保留该短域UNKNOWN而非把它强行解释成确定操作。',
 '学生关于完整修剪结束UNKNOWN保留；另选的白毛巾及电推状工具只作有限典型图像，没有补写剪落毛、干燥或整段步骤结束。',
 '两件相邻典型图像事件保持各自身份与6/7编辑区间，不因最终KEEP归并为一个连续时间区间而减少真实事件数。'],
 consequential_unknowns=['Gray dog paw/tool highlight status at F17..19 remains unresolved; evaluation only.'],
 all_no_reasons_reviewed=True,all_selected_KEEP_editing_boundary_ranges_at_most_half_second=True,
 unresolved_gray_offset_original_gap_exact='1001/2000',unresolved_gray_gap_not_admitted_as_a_KEEP_target_boundary=True,
 evaluation_reference_only=True,training_admitted=False,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'15_i3w_w03_main_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],review=bind(R/'15_i3w_w03_main_preteacher_review.json')),ensure_ascii=False))
