"""First of at most four risk tasks: two seconds of fresh contiguous native frames."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,av
from PIL import Image
ROOT=Path(__file__).resolve().parent/'slot6_silver24_v1'
folder=Path(json.loads((ROOT/'observations/jobs.json').read_text())['first_four'][1])
m=json.loads((folder/'manifest.json').read_text());source=Path(m['source_path'])
out=ROOT/'supplements/risk01_kL_W02_local1to3';out.mkdir(parents=True,exist_ok=False)
a,b=F(61),F(63);rows=[]
assert b-a<=2
with av.open(str(source)) as inp:
    for ordinal,frame in enumerate(inp.decode(video=0)):
        pts=F(frame.pts)*frame.time_base
        if pts<a:continue
        if pts>=b:break
        rgb=frame.to_ndarray(format='rgb24');p=out/f'R{len(rows):03d}_O{ordinal:06d}.png';Image.fromarray(rgb).save(p)
        rows.append(dict(frame_id=f'R{len(rows):03d}',source_ordinal=ordinal,global_seconds_exact=str(pts),
            window_local_seconds_exact=str(pts-F(60)),path=str(p),
            png_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rgb_pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
assert rows and len(rows)<=128 and all(rows[i+1]['source_ordinal']==rows[i]['source_ordinal']+1 for i in range(len(rows)-1))
receipt=dict(status='NEW_NATIVE_OBSERVATION_RISK_TASK_01_NOT_A_LABEL',task_kind='BOUNDARY_ACTION_RISK',
    planned_risk_task_number=1,risk_task_budget_max=4,window_id=m['window_id'],source_sha256=m['source_sha256'],
    source_path=str(source),manifest_sha256=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
    global_domain_exact=[str(a),str(b)],local_domain_exact=['1','3'],frames=rows,
    factual_question='此2秒范围内观察到哪些姿态变化？镜头切换与连续动作分别有哪些直接像素证据？不推断不可见动作、动机或音频。',
    selection_before_candidate_predictions=True,new_model_calls=0,new_optimizer_updates=0,
    native_all_frames_in_supplement=True,all_full_source_frames_observed=False,training_admitted=False)
with (out/'manifest.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=receipt['status'],frames=len(rows),manifest=str(out/'manifest.json'))))
