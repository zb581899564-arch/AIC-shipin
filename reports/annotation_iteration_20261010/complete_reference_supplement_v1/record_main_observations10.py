import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/10_byxOvuiIJV0_W02/manifest.json')
for task,frame,edge,fact in [(5,16,'end','实际O1615仍为清楚高位正面群舞，完整前排及围观布局可辨。'),
 (6,42,'start','实际O1923已是近侧面，男子手中展开黑外套、身体转动；尚非外套落地结果。')]:
 d=R/f'boundary_phase_v2_task{task:02d}';rec=read(d/'receipt.json')
 bracket=[rec['local_seconds_exact'],m['frames'][frame]['local_seconds_exact']] if edge=='end' else [m['frames'][frame]['local_seconds_exact'],rec['local_seconds_exact']]
 width=F(bracket[1])-F(bracket[0]);assert width<=F('0.5')
 out=dict(utc=datetime.now(timezone.utc).isoformat(),actual_registered_image_root_viewed=True,visible_static_fact=fact,
   decision='KEEP',interior_receipt=bind(d/'receipt.json'),actual_image_sha256=rec['png_sha256'],
   **{f'reviewed_editing_{edge}_range_local_exact':bracket},range_width_exact=str(width),
   selected_editing_point_local_exact=str((F(bracket[0])+F(bracket[1]))/2),selected_point_is_not_measured_cut=True,
   historical_original_gap_preserved=True,student_floor64_not_changed=True,teacher_and_training_admission_pending=True)
 with (d/'main_observation.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
with (R/'10_byx_w02_boundary_observation_acceptance.json').open('x',encoding='utf-8') as f:
 json.dump(dict(status='PASS_TWO_ACTUAL_ROOT_REVIEWED_BOUNDARY_OBSERVATIONS_REFERENCE_PENDING',utc=datetime.now(timezone.utc).isoformat(),
 main_review=bind(R/'10_byx_w02_main_preteacher_review.json'),observations=[bind(R/f'boundary_phase_v2_task{x:02d}/main_observation.json') for x in (5,6)],
 new_actual_native_images=2,new_model_calls=0,new_optimizer_updates=0,training_admitted=False),f,ensure_ascii=False,indent=2)
print('PASS_ACTUAL_OBSERVATIONS_RECORDED_REFERENCE_PENDING')
