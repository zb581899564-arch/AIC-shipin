import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/09_WxtbjNsCQ8A_W05/manifest.json')
def gap(a,b):
 v=[m['frames'][a]['local_seconds_exact'],m['frames'][b]['local_seconds_exact']]
 assert F(v[1])-F(v[0])<=F('0.5');return v
out=dict(status='MAIN_PRETEACHER_EDITORIAL_REVIEW_PENDING_LAWFUL_TEACHER',utc=datetime.now(timezone.utc).isoformat(),
 window_id=m['window_id'],teacher_content_read=False,root_candidate_prediction_exposure=False,
 root_read_all64_native_static_facts_and_all64_student_static_facts=True,
 root_actually_viewed_native_samples=[32,33,44,45,46,53,55,56,58,59,61,62],root_actually_viewed_student_samples=[33,46,55,56,58],
 root_did_not_claim_all64_direct_image_views=True,
 independent_native64=bind(R/'native_reviews/09_WxtbjNsCQ8A_W05.native_review.json'),
 independent_student64=bind(R/'student_reviews/09_WxtbjNsCQ8A_W05.independent_student64_review_v1.json'),
 events=[dict(first=33,last=44,type='clear_typical_image',description='蜂箱入口木板、聚集蜜蜂和空中蜂影的清楚典型近景',
   editing_start_range_local_exact=gap(32,33),editing_end_range_local_exact=gap(44,45),not_single_bee_track=True),
 dict(first=46,last=58,type='visible_box_lid_closure',description='从已举起盖板和裸露框条状态，将盖板放低至水平盖住箱口，再保留可见覆盖结果',
   necessary_preparation='F46已竖起盖板的初始状态；不倒推未见开盖过程',visible_result='F56盖住箱口，F57..58保持覆盖状态；此前F55仍有明显开缝',
   editing_start_range_local_exact=gap(45,46),editing_end_range_local_exact=gap(58,59),physical_completion_range_note='F55/F56接触间隙1001/2000秒保留原宽度；训练编辑终点是结果已可见后的F58/F59，而非精确触盖瞬间')],
 complete_domain_editorial_decision_by_samples=[dict(first=0,last=32,decision='NO',reason='常态采访、指向与叠化铺垫；不推断音频内容'),
 dict(first=33,last=44,decision='KEEP',event_index=0),dict(first=45,last=45,decision='NO',reason='双镜头叠化过渡，后续F46初始盖板状态清楚'),
 dict(first=46,last=58,decision='KEEP',event_index=1),dict(first=59,last=61,decision='NO',reason='闭合结果已保留，随后重复持盖与手部停留，无新盖板结果'),
 dict(first=62,last=63,decision='NO',reason='新镜头起始持罐局部，标签不可可靠读，当前尾部没有独立操作结果')],
 explicit_disagreements=['原生初判将盖板段留至F61；主控保留至F58的覆盖结果，后续重复持盖另列NO，未把持续手接触解释为尚未盖住。'],
 all_no_reasons_reviewed=True,all_selected_editing_boundary_ranges_at_most_half_second=True,
 training_admitted=False,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0)
with (R/'09_wxt_w05_main_preteacher_review.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],review=bind(R/'09_wxt_w05_main_preteacher_review.json')),ensure_ascii=False))
