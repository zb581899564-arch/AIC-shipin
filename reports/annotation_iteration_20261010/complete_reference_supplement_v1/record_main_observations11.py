import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
m=read(R.parent/'slot6_silver24_v1/observations/11_byxOvuiIJV0_W04/manifest.json')
for task,inside,outside,fact,semantic in [
 (3,15,None,'实际O3054已切到高位宽景群舞；没有单人倒立后的落地画面。','单人可见倒置姿态画面的编辑终点；绝不解释为落地完成'),
 (4,None,23,'实际O3134仍是清楚高位宽景群舞，队列与围观空间关系可辨。','典型宽景画面的编辑终点；随后F23为倾斜近景')]:
    d=R/f'boundary_phase_v2_task{task:02d}';rec=read(d/'receipt.json')
    endpoints=[m['frames'][inside]['local_seconds_exact'],rec['local_seconds_exact']] if inside is not None else [rec['local_seconds_exact'],m['frames'][outside]['local_seconds_exact']]
    width=F(endpoints[1])-F(endpoints[0]);assert width<=F('0.5')
    out=dict(utc=datetime.now(timezone.utc).isoformat(),actual_registered_image_root_viewed=True,
      visible_static_fact=fact,decision='KEEP',editorial_semantics=semantic,interior_receipt=bind(d/'receipt.json'),
      actual_image_sha256=rec['png_sha256'],reviewed_editing_end_range_local_exact=endpoints,
      range_width_exact=str(width),selected_editing_point_local_exact=str((F(endpoints[0])+F(endpoints[1]))/2),
      selected_point_is_not_measured_cut=True,historical_original_gap_preserved=True,
      physical_landing_after_F15_observed=False,student_floor64_not_changed=True,teacher_and_training_admission_pending=True)
    with (d/'main_observation.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
with (R/'11_byx_w04_boundary_observation_acceptance.json').open('x',encoding='utf-8') as f:
    json.dump(dict(status='PASS_TWO_ACTUAL_ROOT_REVIEWED_BOUNDARY_OBSERVATIONS_REFERENCE_PENDING',utc=datetime.now(timezone.utc).isoformat(),
      main_review=bind(R/'11_byx_w04_main_preteacher_review.json'),observations=[bind(R/f'boundary_phase_v2_task{x:02d}/main_observation.json') for x in (3,4)],
      new_actual_native_images=2,new_model_calls=0,new_optimizer_updates=0,training_admitted=False,
      unobserved_landing_not_backfilled=True),f,ensure_ascii=False,indent=2)
print('PASS_ACTUAL_OBSERVATIONS_RECORDED_REFERENCE_PENDING')
