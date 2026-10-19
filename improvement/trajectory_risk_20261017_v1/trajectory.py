"""Two registered CPU trajectory risks; exact baseline times and sizes retained."""
import bisect,copy,hashlib,json,os,statistics,subprocess,sys,traceback,zipfile
from pathlib import Path
from fractions import Fraction
W=Path('/home/inspur/aic_video_work')
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PARAMS=8782557449
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def bound(r):
 p=Path(r['path']);assert sha(p)==r['sha256'],str(p);return p
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def jl(p,v):
 with p.open('x') as f:
  for x in v:f.write(json.dumps(x,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n')
def canonical(v):
 return hashlib.sha256(json.dumps([{k:r[k] for k in ('video_id','targetRatioWH','predictions')} for r in sorted(v,key=lambda x:x['video_id'])],sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main(root):
 reg=read(root/'registration.json');assert reg['methods']==['NEAREST_PTS_ANCHOR','SHOT_MEDIAN_CENTER']
 assert reg['actual_total_parameters']==PARAMS
 for r in reg['code'].values():bound(r)
 assert read(bound(reg['rule_check']))['status']=='PASS_CURRENT_RULES_SCOPE'
 inputs=read(bound(reg['field_inputs'])); paths={k:bound(v) for k,v in inputs['source_field_files'].items()}
 meta=read(bound(inputs['metadata']));manifest=read(bound(inputs['source_manifest'])); clocks=read(bound(inputs['source_clocks']))
 baseline=bound(reg['baseline']);assert sha(baseline)=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
 with zipfile.ZipFile(baseline) as z:
  assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
  base=[json.loads(s) for s in z.read('predictions.jsonl').splitlines()]
 before={(r['video_id'],p['frame']):p['bboxes'] for r in base for p in r['predictions']}
 assert len(base)==426 and len(before)==123506
 sys.path[:0]=[str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
 from field_contract import compose_from_field
 from pts_contract import legacy_manifest
 from p2j_core import group_shots,box_is_legal
 field=rows(paths['field_frames.jsonl']);shots=rows(paths['field_shots.jsonl']); requests=rows(paths['anchor_requests.jsonl']);out=rows(paths['anchor_output.jsonl'])
 selected=[r for r in field if (r['video_id'],r['source_frame']) in before]
 assert len(selected)==len(before)
 # New composition identity audit only: no successful model/decoder/processor repeated.
 original,old_prov=compose_from_field(legacy_manifest(manifest),selected,shots,requests,out)
 assert {(r['video_id'],p['frame']):p['bboxes'] for r in original for p in r['predictions']}==before
 save(root/'baseline_identity.json',dict(status='PASS_EXACT40_47_FRAME_BOX_IDENTITY',frames=len(before)))
 outputs={(r['video_id'],r['source_frame']):r for r in out}; sh=group_shots(shots)
 metadata={str(r['video_id']):r for r in meta['records']}
 lookup={}; schedules={}; timestamps={}
 for shotid,ss in enumerate(sh):
  vid=ss[0]['video_id'];ff=[r['source_frame'] for r in ss]
  aa=[f for f in ff if (vid,f) in outputs];assert aa and aa[0]==ff[0] and aa[-1]==ff[-1]
  boxes=[outputs[vid,a]['box_xyw'] for a in aa];assert len({b[2] for b in boxes})==1
  center=[int(round(statistics.median(b[j] for b in boxes))) for j in (0,1)]+[boxes[0][2]]
  schedules[shotid]=(vid,aa,center)
  for f in ff:lookup[vid,f]=shotid
 # Timestamp field is frozen by registration, never guessed per video.
 for vid,c in clocks.items():
  ts=c[reg['pts_key']];assert isinstance(ts,(dict,list)) and len(ts)==c['n_frames']
  t=[Fraction(ts[str(f)] if isinstance(ts,dict) else ts[f]) for f in range(c['n_frames'])];assert all(b>a for a,b in zip(t,t[1:]));timestamps[vid]=t
 history=set(reg['historical_canonical_sha256'])|{canonical(base)}
 for r in reg['current_candidate_completions']:history.add(read(bound(r))['canonical_sha256'])
 for method in reg['methods']:
  directory=root/method;directory.mkdir();prediction=copy.deepcopy(base);provenance=[];changed=0;changedids=set()
  for rr in prediction:
   vid=rr['video_id'];m=metadata[vid];tt=timestamps[vid]
   for pp in rr['predictions']:
    f=pp['frame'];sid=lookup[vid,f];_,aa,med=schedules[sid]
    if method=='NEAREST_PTS_ANCHOR':
     pos=bisect.bisect_left(aa,f);candidates=aa[max(0,pos-1):min(len(aa),pos+1)]
     anchor=min(candidates,key=lambda a:(abs(tt[f]-tt[a]),a));box=list(outputs[vid,anchor]['box_xyw']);support=[anchor]
    else:box=list(med);support=aa
    assert box[2]==pp['bboxes'][2] and box_is_legal(box,m['width'],m['height'],*m['targetRatioWH'])
    if box!=pp['bboxes']:changed+=1;changedids.add(vid)
    pp['bboxes']=box
    provenance.append(dict(video_id=vid,source_frame=f,shot_id=sid,box_xyw=box,legal=True,spatial_source=method,support_anchor_count=len(support),support_first=support[0],support_last=support[-1]))
   rr['model_params_b']=PARAMS/1e9
  digest=canonical(prediction);assert changed>0 and digest not in history,'Duplicate or no change'
  history.add(digest);jl(directory/'predictions.jsonl',prediction);jl(directory/'provenance.jsonl',provenance)
  if not (root/'selected.jsonl').exists():jl(root/'selected.jsonl',selected);save(root/'metadata.json',meta)
  pending=directory/f'candidate_{method}.PENDING.zip'
  with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as z:z.write(directory/'predictions.jsonl','predictions.jsonl')
  # Frozen strict loader is retained; only the declared spatial-source allowlist
  # is extended in an independent version, never falsely labelled linear.
  original_validator=RUN/'baseline_a_pts_v1/vendor/independent_validate.py'
  validator=directory/'independent_validate_trajectory.py'
  old=original_validator.read_text();needle='{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}'
  assert old.count(needle)==1
  validator.write_text(old.replace(needle,'{"NEAREST_PTS_ANCHOR", "SHOT_MEDIAN_CENTER"}'))
  subprocess.run([sys.executable,'-B',str(validator),'--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(root/'metadata.json'),'--selected',str(root/'selected.jsonl'),'--predictions',str(directory/'predictions.jsonl'),'--provenance',str(directory/'provenance.jsonl'),'--zip',str(pending),'--report',str(directory/'independent11.json')],check=True,stdout=subprocess.DEVNULL)
  assert len(read(directory/'independent11.json')['checks'])==11 and all(read(directory/'independent11.json')['checks'].values())
  subprocess.run([sys.executable,'-B',str(root/'code/replay.py'),str(root),method],check=True)
  with zipfile.ZipFile(pending) as z:assert z.testzip() is None and hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==sha(directory/'predictions.jsonl')
  final=directory/f'candidate_{method}.zip';pending.rename(final)
  save(directory/'completion.json',dict(status='PASS_ENGINEERING_UNKNOWN_ONLINE_EFFECT',method=method,path=str(final),bytes=final.stat().st_size,sha256=sha(final),member_sha256=sha(directory/'predictions.jsonl'),canonical_sha256=digest,records=426,frames=len(before),changed_boxes=changed,changed_sources=len(changedids),added=0,removed=0,all_original_widths_retained=True,native_pts=True,new_model_calls=0,new_training_updates=0,actual_total_parameters=PARAMS,independent11strict=True,independent_trajectory_replay=True,online_effect='UNKNOWN',website_submitted=False))
  print(json.dumps(read(directory/'completion.json')),flush=True)
 save(root/'completion.json',dict(status='COMPLETE_TWO_TRAJECTORY_RISKS',packages=[read(root/m/'completion.json') for m in reg['methods']],new_GPU_calls=0))
if __name__=='__main__':
 root=Path(sys.argv[1])
 try:main(root)
 except BaseException as e:
  if not (root/'failure.json').exists():save(root/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),preserve_success=True,no_restart=True))
  raise
