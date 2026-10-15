"""Record only images actually opened by ROOT in this turn; no new blind review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent
O=R.parent/'slot6_silver24_v1/observations'
rows={22:('22_Yi4Ij2NM7U4_W03',[(25,2445,'White onion held away from the mouth, upper edge irregular; no swallowing or internal transfer established.'),(61,2856,'Forearm and torso obscure the board and possible knife contact; a completed cut is not visually established.')]),
      23:('23_Yi4Ij2NM7U4_W06',[(15,4491,'Clear transparent pack with several red-brown long foods, held beside the face and pointed at.'),(50,4890,'Red bottle with white cap held beside the face and pointed at; no opening or pouring shown.')])}
for index,(name,items) in rows.items():
 actual=[]
 for i,ordinal,fact in items:
  p=O/name/'frames'/f'F{i:02d}_O{ordinal:06d}.png'
  actual.append(dict(sample_index=i,image=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()),visible_static_fact=fact))
 v=dict(status='ROOT_ACTUAL_ORIGINAL_IMAGE_RECHECK_NOT_NEW_BLIND_INITIAL',utc=datetime.now(timezone.utc).isoformat(),
  job_index=index,window_id='Yi4Ij2NM7U4:SLOT6:'+('3' if index==22 else '6'),actual_images=actual,
  teacher_completed_content_read_at_recheck=False,root_direct64_image_review=False,root_video_view=False,
  candidate_prediction_exposure=False,training_admitted=False)
 p=R/f'{index}_yi4_root_actual_pixels_schema_recovery_v1.json'
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
 print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False))
