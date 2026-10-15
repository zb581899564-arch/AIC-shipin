"""Additional full-resolution observations for small-object ambiguity."""
import os,json,hashlib,zipfile
from pathlib import Path
from fractions import Fraction as F
import av
from PIL import Image
ROOT=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
OUT=ROOT/'reliable_reference_20261012_v1/detail_01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,indent=2)
def main(registration):
 os.environ['CUDA_VISIBLE_DEVICES']='';OUT.mkdir(exist_ok=False)
 save(OUT/'registration.json',registration);records=[]
 for r in registration['rows']:
  cp=ROOT/'context_advisory_v1/input_01'/(r['source_key']+'.clock.json');assert sha(cp)==r['clock_sha256']
  clock=json.loads(cp.read_text());src=Path(clock['source_path']);assert sha(src)==r['source_key']
  pts=[F(x) for x in clock.get('exact_pts',clock.get('pts_rational'))]
  desired={F(o['exact_pts']):o for o in r['observations']};assert all(pts[o['ordinal']]==F(o['exact_pts']) for o in r['observations'])
  seen=set()
  with av.open(str(src)) as c:
   st=c.streams.video[0];lo=min(desired);hi=max(desired)
   c.seek(max(0,int((lo-2)/F(st.time_base))),stream=st,backward=True,any_frame=False)
   for f in c.decode(st):
    t=F(f.pts)*F(f.time_base)
    if t>hi:break
    if t in desired:
     o=desired[t];rgb=f.reformat(format='rgb24');im=Image.frombytes('RGB',(rgb.width,rgb.height),bytes(rgb.planes[0]),'raw','RGB',rgb.planes[0].line_size,1)
     p=OUT/(r['case_id']+'_ID'+str(o['id'])+'.jpg');im.save(p,quality=95)
     records.append(dict(case_id=r['case_id'],observation=o,path=p.name,sha256=sha(p),bytes=p.stat().st_size));seen.add(t)
  assert seen==set(desired)
 save(OUT/'preparation_receipt.json',dict(status='PASS_DETAIL_NATIVE_IDENTITY',records=records,new_model_calls=0))
 zp=OUT/'detail_material.zip'
 with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for p in sorted(OUT.glob('*.jpg')):z.write(p,p.name)
  z.write(OUT/'preparation_receipt.json','preparation_receipt.json')
 save(OUT/'transfer_receipt.json',dict(bytes=zp.stat().st_size,sha256=sha(zp)))
 print('COMPLETE',zp.stat().st_size,sha(zp),flush=True)
