from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'boundary_ht5_w02_end_v1/receipt.json';r=read(p)
assert r['source_ordinal']==2361 and sha(Path(r['path']))==r['png_sha256']
n=read(ROOT/'native_reviews/04_HT5vyqe0Xaw_W02.native_review.json')
left=n['frames'][39];width=F(r['local_seconds_exact'])-F(left['local_seconds_exact']);assert 0<width<=F('0.5')
v=dict(status='ROOT_ACTUAL_INTERIOR_IMAGE_EDITORIAL_OBSERVATION',utc=datetime.now(timezone.utc).isoformat(),receipt=dict(path=str(p),sha256=sha(p)),original_registered_gap_exact='1001/2000',
 root_actually_viewed_image=True,static_visual_fact='蓝白卡车正面、打开左门和两侧树木与路面。构图与F39/F40同一整体车头展示，没有新动作或清晰新增结果。',
 finite_editing_verdict='NO_REPETITION_AFTER_SHORT_TYPICAL_IMAGE',inside_evidence='F39',outside_evidence='O002361',reviewed_local_bracket_exact=[left['local_seconds_exact'],r['local_seconds_exact']],reviewed_width_exact=str(width),
 interpretation='Observed editorial endpoint of brief representative shot, not a physical cut or vehicle motion boundary. Actual interior image supplies new observation; no invented timestamps or shrinking without pixels.',new_model_calls=0,new_optimizer_updates=0)
with (ROOT/'boundary_ht5_w02_end_v1/main_observation.json').open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(v['status'],v['reviewed_width_exact'])
