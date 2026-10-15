"""Record root's actually viewed preregistered interior images, not new inference."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
from PIL import Image
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
specs=[
 (12,'实际O7998仍为手持轮胎胎面特写，手指靠浅色沟槽，未见新的显著关系；仅短代表画面的编辑结束选择。','LEFT'),
 (13,'实际O14492仍为倾斜手持照片，未切到F8充满内框的稳定高处横身照片。','RIGHT'),
 (14,'实际O15119已经切入投影广场，人形高处前倾/伸身可见；不是前访谈脸近景。','LEFT'),
 (15,'实际O15276已经切回室内男子脸近景，不能由此补此前动作最终落地。','LEFT')]
bindings={}
for num,fact,choice in specs:
 d=R/f'boundary_phase_v2_task{num:02d}';reg=read(d/'registration.json');rec=read(d/'receipt.json')
 assert bind(Path(rec['path']))['sha256']==rec['png_sha256'] and rec['source_ordinal']==reg['interior_registered']['source_ordinal']
 with Image.open(rec['path']) as im:assert im.size==(rec['width'],rec['height']) and hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==rec['rgb_pixel_sha256']
 left,right=reg['endpoints'];pair=[left['local_seconds_exact'],rec['local_seconds_exact']] if choice=='LEFT' else [rec['local_seconds_exact'],right['local_seconds_exact']]
 assert F(pair[1])-F(pair[0])<=F('.5')
 p=d/'main_observation.json'
 v=dict(status='ROOT_ACTUALLY_VIEWED_REGISTERED_NATIVE_EDITING_BOUNDARY_IMAGE',utc=datetime.now(timezone.utc).isoformat(),
  actual_decoder_receipt=bind(d/'receipt.json'),registration=bind(d/'registration.json'),actual_png_sha256=rec['png_sha256'],root_display_detail='original',
  visible_static_fact=fact,reviewed_editing_range_local_exact=pair,selected_point_is_not_measured_cut=True,student_floor64_unchanged=True,
  interpretation_limit='Observed editorial/scene bracket only. No unseen physical result, no source clock or student sample change.',new_model_calls=0,new_optimizer_updates=0)
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
 bindings[num]=bind(p)
for tag,nums in [('19_j0n_w11',[12]),('21_cjibt_w16',[13,14,15])]:
 p=R/(tag+'_boundary_observations_acceptance.json');v=dict(status='PASS_ACTUAL_NATIVE_INTERIOR_OBSERVATIONS_NOT_FINAL_SEMANTIC_ADMISSION',observations=[bindings[x] for x in nums],actual_new_images=len(nums),new_model_calls=0,new_optimizer_updates=0,original_physical_unknowns_preserved=True)
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
 print(json.dumps(bind(p),ensure_ascii=False))
