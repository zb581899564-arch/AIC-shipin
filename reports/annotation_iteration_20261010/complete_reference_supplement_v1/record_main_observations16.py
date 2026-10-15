"""Record three actually displayed, preregistered native observations."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
spec={
 7:dict(fact='前景黑衣骑手遮挡，后方红蓝白骑手已抬前轮；已切入动作，无起始准备证据。',
        editing_decision='KEEP_CLEAR_TYPICAL_WHEEL_LIFT',range_side='left',not_claiming='Unseen preparation, exact scene-cut time or physical onset'),
 8:dict(fact='红蓝白车体已近水平，朝左缓骑；后方黑衣车近水平，无新的转向或抬轮。',
        editing_decision='NO_REPEAT_POST_TURN_RIDING',range_side='left',not_claiming='Exact tyre contact at an unseen instant'),
 9:dict(fact='红蓝白骑手前倾屈膝、画面与车下部模糊/裁切，尚无清楚的双人前轮高抬姿态。',
        editing_decision='NOT_CLEAR_HIGHLIGHT_IMAGE_ON_ITS_OWN',range_side=None,not_claiming='Precise preparation onset or a completed physical action')}
rows=[]
for n,s in spec.items():
 folder=R/('boundary_phase_v2_task%02d'%n);r=read(folder/'receipt.json');reg=read(folder/'registration.json')
 assert reg['job_index']==16 and r['actual_new_images']==1
 assert bind(Path(r['path']))['sha256']==r['png_sha256']
 eps=reg['endpoints'];point=r['local_seconds_exact']
 narrowed=[eps[0]['local_seconds_exact'],point] if s['range_side']=='left' else None
 if narrowed:assert F(narrowed[1])-F(narrowed[0])<=F('.5')
 value=dict(status='ROOT_ACTUALLY_VIEWED_REGISTERED_NATIVE_BOUNDARY_IMAGE',utc=datetime.now(timezone.utc).isoformat(),
  registration=bind(folder/'registration.json'),actual_decoder_receipt=bind(folder/'receipt.json'),
  actual_path=r['path'],actual_png_sha256=r['png_sha256'],root_display_detail='original',
  root_visible_fact=s['fact'],root_finite_editing_decision=s['editing_decision'],
  editing_boundary_range_local_exact=narrowed,not_claiming=s['not_claiming'],
  new_model_calls=0,new_optimizer_updates=0)
 save(folder/'main_observation.json',value);rows.append(bind(folder/'main_observation.json'))
save(R/'16_eyq_w03_boundary_observations_acceptance.json',dict(
 status='PASS_THREE_ACTUAL_NATIVE_BOUNDARY_OBSERVATIONS_NOT_FINAL_SEMANTIC_ADMISSION',
 observations=rows,task07_start_range_local_exact=read(R/'boundary_phase_v2_task07/main_observation.json')['editing_boundary_range_local_exact'],
 task08_end_range_local_exact=read(R/'boundary_phase_v2_task08/main_observation.json')['editing_boundary_range_local_exact'],
 task09_not_used_as_known_start=True,
 paired_lift_editing_proposal='Use clear paired front-wheel-high typical image F45..52 with F44/F45 start range, not inferred full preparation/completion. F44 and interior are blurred/cropped ordinary preparation, not a clear highlight by themselves.',
 all_three_identity_and_current_png_bindings_checked=True,actual_new_images=3,new_model_calls=0,new_optimizer_updates=0))
print(json.dumps(bind(R/'16_eyq_w03_boundary_observations_acceptance.json')))
