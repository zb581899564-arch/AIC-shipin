"""Named metadata only: counts/storage, never media/GT/model/decoder imports."""
import json
import shlex
import subprocess
from pathlib import Path
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15',
     '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-home']
code=r'''import hashlib,json,shutil,socket
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
here=run/'balanced_two_window_risk_v3'
def read(p):return json.loads(Path(p).read_text())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()).hexdigest()
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
plan=read(here/'input_01/rematch_plan.json');jobs=plan['jobs']
accepted={r['video_id']:r for r in rows(here/'rematch_01/temporal.jsonl')}
old={r['video_id']:r for r in rows(run/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl')}
registry={r['video_id']:r for r in read(plan['input_ref']['registry'])['records']}
assert len(jobs)==len(accepted)==len(registry)==426 and sum(len(j['windows']) for j in jobs)==521
counts=dict(records=426,windows=521,events=0,endpoint_requests=0,verify_requests=0,alias_done=0,fresh_done=0,
            raw_receipt_files_present=0,full_source_clock_files_present=0,accepted_status_windows=0,
            endpoint_windows_at_least64_pts=0,endpoint_windows_below64_pts=0,
            original_source_start_endpoints=0,original_source_terminal_endpoints=0,
            original_other_endpoints=0,planned_native_source_media_present=0)
rgb_literal=raw_tensor=old_rgb_literal=old_tensor_literal=source_bytes=source_pixels=clock_bytes=0
clock_terminal_kinds={};named_files={};cache_keys=set();cache_files=set();missing_cache_paths=0;source_dims=set()
cache_name_counts={}
def inspect_refs(obj):
 global missing_cache_paths
 if isinstance(obj,dict):
  for k,v in obj.items():
   if isinstance(v,str) and ('path' in k.lower() or 'cache' in k.lower()) and any(v.lower().endswith(s) for s in ('.npz','.npy','.pt','.pt.gz','.png','.jpg','.jpeg','.webp','.bin')):
    cache_keys.add(k);p=Path(v)
    if p.is_file():cache_files.add(str(p))
    else:missing_cache_paths+=1
   if isinstance(v,(dict,list)):inspect_refs(v)
 elif isinstance(obj,list):
  for v in obj:
   if isinstance(v,(dict,list)):inspect_refs(v)
for job in jobs:
 vid=job['video_id'];meta=job['metadata'];record=accepted[vid];clock_record=registry[vid]
 assert len(record['windows'])==len(job['windows'])
 width,height=meta['width'],meta['height'];source_dims.add((width,height));source_pixels+=width*height
 media=Path(meta['source_path'])
 if media.is_file():counts['planned_native_source_media_present']+=1;source_bytes+=media.stat().st_size
 cp=Path(clock_record['clock_arrays']['path']);assert cp.is_file();counts['full_source_clock_files_present']+=1;clock_bytes+=cp.stat().st_size
 arrays=read(cp);arrays=arrays.get('arrays',arrays)
 pts=[F(x)*F(arrays['raw_time_base']) for x in arrays['native_pts_ticks']]
 origin=F(arrays['raw_first_pts_ticks'])*F(arrays['raw_time_base']);normalized=[p-origin for p in pts]
 assert len(pts)==meta['n_frames']
 domain_start=F(str(meta['scope_start_sec']));domain_end=F(str(meta['scope_end_sec']))
 terminal=clock_record.get('terminal_evidence',{});kind=terminal.get('kind','ABSENT');clock_terminal_kinds[kind]=clock_terminal_kinds.get(kind,0)+1
 for ix,(part,done) in enumerate(zip(job['windows'],record['windows'])):
  same=part['window']==part['base_window'];stem=digest(vid)
  path=here/('rematch_01/aliases/'+stem+'/'+str(ix)+'.json' if same else 'rematch_01/local/'+stem+'/'+str(ix)+'/BW/done.json')
  assert path.is_file();rawdone=read(path)
  counts['alias_done' if same else 'fresh_done']+=1
  if same:assert rawdone['status']=='PASS_EXACT_V14_UNCHANGED_REQUEST_AUTHORITY_HANDOFF' and done['parsed_segments']==old[vid]['windows'][ix]['parsed_segments']
  else:assert rawdone['parsed_segments']==done['parsed_segments']
  assert done['output_valid'] is True and not done['parse_errors'] and done['status'] in ('MODEL_OK','LEGAL_EMPTY')
  counts['accepted_status_windows']+=1
  e=len(done['parsed_segments']);counts['events']+=e
  ev=done['video_identity'];pf=ev['actual_pixels_per_frame'];n=ev['sampled_frames']
  old_rgb_literal+=n*width*height*3;old_tensor_literal+=n*pf*3*4
  rgb_literal+=3*e*64*width*height*3;raw_tensor+=3*e*64*pf*3*4
  if 'raw_receipt' in done and Path(done['raw_receipt']).is_file():counts['raw_receipt_files_present']+=1
  inspect_refs(done)
  for a,b in done['parsed_segments']:
   start=F(str(part['start_sec']))+F(str(a));end=F(str(part['start_sec']))+F(str(b))
   for point,side in ((start,'start'),(end,'end')):
    lo=max(domain_start,point-3);hi=min(domain_end,point+3)
    count=bisect_left(normalized,hi)-bisect_left(normalized,lo)
    counts['endpoint_windows_at_least64_pts' if count>=64 else 'endpoint_windows_below64_pts']+=1
    if side=='start' and point==domain_start:counts['original_source_start_endpoints']+=1
    elif side=='end' and point==domain_end:counts['original_source_terminal_endpoints']+=1
    else:counts['original_other_endpoints']+=1
counts['endpoint_requests']=2*counts['events'];counts['verify_requests']=counts['events'];counts['max_shared_three_requests']=3*counts['events']
named_roots=[here/'rematch_01',run/'context_advisory_v1/rematch_01',run/'teacher_student_autopilot_v14/rematch_01',run/'b_score_aligned_package_v4/rematch_01']
for root in named_roots:
 found=[]
 if root.exists():
  for p in root.rglob('*'):
   if p.is_file() and any(p.name.lower().endswith(s) for s in ('.npz','.npy','.pt','.pt.gz','.png','.jpg','.jpeg','.webp')):found.append(p)
 cache_name_counts[str(root)]={'stored_rgb_or_tensor_files':len(found),'total_bytes':sum(p.stat().st_size for p in found),'file_suffix_counts':{s:sum(str(p).lower().endswith(s) for p in found) for s in ('.npz','.npy','.pt','.pt.gz','.png','.jpg','.jpeg','.webp')}}
for root in [here/'rematch_01',run/'b_score_aligned_package_v4/rematch_01']:
 for name in ('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl','metadata.json','schedule.stage.json','spatial.stage.json'):
  p=root/name;named_files[str(p)]={'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else None}
firstCPU={'logical_tensor_bytes':286454472,'gzip_bytes':64299657,'rgb_npz_bytes':70064675,'scope':'root-reported first Charades source window; not a proven production compression bound'}
ratio=firstCPU['gzip_bytes']/firstCPU['logical_tensor_bytes']
result={'status':'READ_ONLY_PRODUCTION_COUNTS_AND_STORAGE_BUDGET_NOT_ADMISSION','counts':counts,
 'source_media_total_bytes_from_stat':source_bytes,'source_geometry_count':len(source_dims),
 'full_source_clock_array_total_bytes':clock_bytes,'terminal_evidence_kind_counts':clock_terminal_kinds,
 'literal_old521_sampled_RGB_bytes_if_materialized':old_rgb_literal,'old521_pixel_tensor_lower_bytes':old_tensor_literal,
 'literal_all_3E_new_native64_RGB_bytes_without_dedup':rgb_literal,'pixel_tensor_3E_lower_bytes_before_serialization':raw_tensor,
 'disk_available_bytes_now':shutil.disk_usage(run).free,'first_Charades_CPU_reference':firstCPU,
 'first_Charades_gzip_ratio':ratio,'scenario_3E_gzip_pixel_tensor_bytes_at_that_ratio':int(raw_tensor*ratio),
 'existing_cache_references_in_accepted_done':{'path_keys':sorted(cache_keys),'existing_files':len(cache_files),'existing_total_bytes':sum(Path(p).stat().st_size for p in cache_files),'missing_references_count':missing_cache_paths},
 'scoped_cache_inventory':cache_name_counts,'frozen_crop_field_metadata_sizes_only':named_files,
 'endpoint_domain_note':'Counts use frozen inference scope and accepted existing whole tick clocks; legacy terminal witness does not itself establish newly measured packet-last duration. No method/parameter chosen from these counts.',
 'tensor_estimate_note':'Uses old per-window actual_pixels_per_frame times64xRGB float32 for each event3 request; actual new prompt/grid/cache size and compression remain unmeasured. Literal RGB holds source resolution. Overlap/dedup ignored for conservative gross budget.',
 'no_video_content_GT_models_decoders_or_CPU_encoders_read_or_run':True,'no_old_success_deleted':True,'production_started':False}
print(json.dumps(result))
'''
if __name__=='__main__':
 r=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)],capture_output=True)
 if r.returncode:
  print(r.stderr.decode(),end='');raise SystemExit(r.returncode)
 value=json.loads(r.stdout)
 target=Path(__file__).with_name('production_budget_04.json')
 with target.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
 print(json.dumps(value))
