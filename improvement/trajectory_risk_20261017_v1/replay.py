"""Independent reconstruction of source shots, PTS nearest and median geometry."""
import json,sys,zipfile,hashlib
from pathlib import Path
from fractions import Fraction
root=Path(sys.argv[1]);method=sys.argv[2]
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
reg=read(root/'registration.json');inputs=read(reg['field_inputs']['path'])
shots=rows(inputs['source_field_files']['field_shots.jsonl']['path']);outputs=rows(inputs['source_field_files']['anchor_output.jsonl']['path']);clocks=read(inputs['source_clocks']['path'])
with zipfile.ZipFile(reg['baseline']['path']) as z:base=[json.loads(s) for s in z.read('predictions.jsonl').splitlines()]
new=rows(root/method/'predictions.jsonl');old={(r['video_id'],p['frame']):p['bboxes'] for r in base for p in r['predictions']}
actual={(r['video_id'],p['frame']):p['bboxes'] for r in new for p in r['predictions']};assert actual.keys()==old.keys()
shmap={};sid=-1;prev=None;members={}
for r in sorted(shots,key=lambda r:(r['video_id'],r['source_frame'])):
 k=(r['video_id'],r['source_frame'])
 if prev is None or prev[0]!=k[0] or prev[1]+1!=k[1] or r['is_shot_start']:sid+=1;members[sid]=[]
 shmap[k]=sid;members[sid].append(k);prev=k
support={s:[] for s in members}
for r in outputs:support[shmap[r['video_id'],r['source_frame']]].append(r)
expected={}
def median(v):
 v=sorted(v);n=len(v);return v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2
for s,keys in members.items():
 aa=support[s];assert aa
 vid=keys[0][0];raw=clocks[vid][reg['pts_key']];ts={str(i):(raw[str(i)] if isinstance(raw,dict) else raw[i]) for i in range(clocks[vid]['n_frames'])}
 if method=='SHOT_MEDIAN_CENTER':
  wanted=[round(median([a['box_xyw'][j] for a in aa])) for j in (0,1)]+[aa[0]['box_xyw'][2]]
  for k in keys:
   if k in old:expected[k]=wanted
 else:
  aa.sort(key=lambda a:a['source_frame']);j=0
  for k in keys:
   if k not in old:continue
   f=k[1];t=Fraction(ts[str(f)])
   while j+1<len(aa) and Fraction(ts[str(aa[j+1]['source_frame'])])<=t:j+=1
   a=aa[j]
   if j+1<len(aa):
    b=aa[j+1]
    if abs(Fraction(ts[str(b['source_frame'])])-t)<abs(Fraction(ts[str(a['source_frame'])])-t):a=b
   expected[k]=a['box_xyw']
assert expected==actual,'Independent source geometry/PTS differs'
assert all(actual[k][2]==b[2] for k,b in old.items())
assert len(new)==426 and all(r['predictions'] for r in new)
out=dict(status='PASS_INDEPENDENT_TRAJECTORY_REPLAY',method=method,frames=len(actual),unchanged_time_and_width=True,same_shot_support=True,exact_rational_pts=True)
with (root/method/'independent_replay.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out),flush=True)
