"""Record actual root views of two native editing-boundary supplements."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,v):
 text=json.dumps(v,ensure_ascii=False,indent=2)
 with p.open('x',encoding='utf-8') as f:f.write(text)
rows=[]
for n,fact,note in [(10,'实际O4387摩托车已在地面双轮近地骑行，仍为离台后的结果姿态；没有F56的近前轮转身画面。',
 'Use interior/F56 as observed editorial division; exact new physical action onset is not asserted.'),
 (11,'实际O4444仍为地面摩托车与骑手腿的近景，前轮接地/车体偏侧，尚未切到访谈；后轮接地点细节未可靠显出。',
 'Use interior/F60 as finite scene-end editing bracket; do not invent completed rear-wheel landing.')]:
 folder=R/('boundary_phase_v2_task%02d'%n);r=read(folder/'receipt.json');reg=read(folder/'registration.json')
 assert reg['job_index']==17 and r['actual_new_images']==1 and bind(Path(r['path']))['sha256']==r['png_sha256']
 narrowed=[r['local_seconds_exact'],reg['endpoints'][1]['local_seconds_exact']]
 assert F(narrowed[1])-F(narrowed[0])<=F('.5')
 op=folder/'main_observation.json'
 save(op,dict(status='ROOT_ACTUALLY_VIEWED_REGISTERED_NATIVE_EDITING_BOUNDARY_IMAGE',utc=datetime.now(timezone.utc).isoformat(),
  actual_decoder_receipt=bind(folder/'receipt.json'),registration=bind(folder/'registration.json'),
  actual_png_sha256=r['png_sha256'],root_display_detail='original',visible_static_fact=fact,
  reviewed_editing_range_local_exact=narrowed,interpretation_limit=note,
  selected_point_is_not_measured_cut=True,student_floor64_unchanged=True,new_model_calls=0,new_optimizer_updates=0))
 rows.append(bind(op))
save(R/'17_eyq_w04_boundary_observations_acceptance.json',dict(status='PASS_TWO_ACTUAL_NATIVE_EDITING_BOUNDARY_OBSERVATIONS_NOT_FINAL_SEMANTIC_ADMISSION',
 observations=rows,physical_final_landing_UNKNOWN_preserved=True,actual_new_images=2,new_model_calls=0,new_optimizer_updates=0))
print(json.dumps(bind(R/'17_eyq_w04_boundary_observations_acceptance.json')))
