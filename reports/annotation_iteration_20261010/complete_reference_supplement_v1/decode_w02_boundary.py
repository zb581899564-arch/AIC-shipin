"""One registered interior native observation for a newly consequential gap."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys,time
ROOT=Path(__file__).resolve().parent
OBS=ROOT.parent/'slot6_silver24_v1/observations/01_kLxoNp-UchI_W02'
RUN=ROOT.parents[2]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
OUT=ROOT/'boundary_w02_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
manifest=read(OBS/'manifest.json'); clock=read(OBS/'native_clock.json')
left,right=manifest['frames'][15],manifest['frames'][16]
assert F(right['local_seconds_exact'])-F(left['local_seconds_exact'])==F('0.5005')
ordinal=(left['source_ordinal']+right['source_ordinal'])//2
point=next(r for r in clock if r['source_ordinal']==ordinal)
OUT.mkdir(exist_ok=False)
save(OUT/'registration.json',dict(utc=datetime.now(timezone.utc).isoformat(),
 purpose='New W02 end of lying-face sequence: existing observed gap exceeds frozen 0.5 allowance. One interior native image permits actual visual support, not automatic narrowing.',
 original_W01_boundary_STOP_not_reversed=True,source_sha256=manifest['source_sha256'],
 manifest_sha256=sha(OBS/'manifest.json'),native_clock_sha256=sha(OBS/'native_clock.json'),
 main_observations_sha256=sha(ROOT/'01_w02_main_native_observations.json'),
 endpoints=[left,right],interior_registered=point,max_new_images=1,new_model_calls=0,new_optimizer_updates=0))
import av
from PIL import Image
sys.path.insert(0,str(RUN/'teacher_student_autopilot_v14'))
from source_color import convert_frame
source=Path(manifest['source_path']);assert sha(source)==manifest['source_sha256']
started=time.monotonic();found=False
with av.open(str(source)) as container:
    assert len(container.streams.video)==1
    for i,frame in enumerate(container.decode(container.streams.video[0])):
        if i!=ordinal:continue
        actual=F(frame.pts)*frame.time_base
        assert actual==F(point['global_seconds_exact'])
        rgb=convert_frame(frame,manifest['source_sha256'],'rgb24')
        path=OUT/f'O{i:06d}.png';Image.fromarray(rgb).save(path)
        save(OUT/'receipt.json',dict(status='PASS_ONE_ACTUAL_NATIVE_BOUNDARY_IMAGE_NOT_SEMANTIC_ACCEPTANCE',
            source_ordinal=i,global_seconds_exact=str(actual),local_seconds_exact=point['local_seconds_exact'],
            path=str(path),png_sha256=sha(path),rgb_pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
            width=rgb.shape[1],height=rgb.shape[0],wall_seconds=time.monotonic()-started,new_model_calls=0,new_optimizer_updates=0))
        found=True;break
assert found
print(json.dumps(read(OUT/'receipt.json'),ensure_ascii=False))
