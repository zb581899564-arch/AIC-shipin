"""One read-only source-clock capacity estimate; no inputs, media or inference."""
import base64
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import collections,datetime,hashlib,json,pathlib,shutil,socket
from fractions import Fraction as F
from bisect import bisect_left
root=pathlib.Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_native_package_v3')
refs=json.loads((root/'package_inputs.json').read_text())
docs={}
for name in ['metadata','source_manifest','source_clocks']:
 ref=refs[name];data=pathlib.Path(ref['path']).read_bytes()
 assert hashlib.sha256(data).hexdigest()==ref['sha256'],name+' frozen metadata changed'
 docs[name]=json.loads(data)
rows=docs['metadata']['records'];assert rows==docs['source_manifest']['records'] and len(rows)==426
clocks=docs['source_clocks'];assert len(clocks)==426
physical={};total_views=0;unique=set();wanted=collections.defaultdict(set)
geometry=collections.Counter();too_short=0;raw_view_bytes=0;largest_rgb_union=0
for index,row in enumerate(rows):
 clock=clocks[str(index)]
 assert clock['source_sha256']==row['source_sha256'] and clock['source_path']==row['source_path']
 points=list(map(F,clock['normalized_exact_pts']));end=F(clock['physical_end_exact'])
 assert len(points)==row['n_frames'] and points[0]==0 and all(a<b for a,b in zip(points,points[1:]))
 assert end==points[-1]+F(clock['last_frame_duration_exact']) and F(clock['last_frame_duration_exact'])>0
 sha=row['source_sha256'];w,h=row['width'],row['height'];geometry[(w,h)]+=1
 signature=(w,h,tuple(points),end)
 assert sha not in physical or physical[sha]==signature,'same bytes have conflicting original clocks'
 physical[sha]=signature
 starts={F(0)} if end<=15 else {F(15,2)*i for i in range(int((end-15)/F(15,2))+1)}|{end-15}
 for start in sorted(starts):
  stop=min(start+15,end);first,last=bisect_left(points,start),bisect_left(points,stop)
  total_views+=1
  if last-first<64:too_short+=1;continue
  selected=tuple(first+j*(last-first-1)//63 for j in range(64))
  key=(sha,start,stop,selected)
  if key in unique:continue
  unique.add(key);wanted[sha].update(selected);raw_view_bytes+=64*w*h*3
union_bytes=sum(len(wanted[sha])*physical[sha][0]*physical[sha][1]*3 for sha in wanted)
largest_rgb_union=max((len(wanted[sha])*physical[sha][0]*physical[sha][1]*3 for sha in wanted),default=0)
free=shutil.disk_usage(root).free
out=dict(schema='RECALL_PRODUCTION_READONLY_CLOCK_BUDGET_V1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 host=socket.gethostname(),source_records=426,physical_sha_sources=len(physical),
 candidate_record_views=total_views,candidate_unique_physical_views=len(unique),
 insufficient_native64_views=too_short,metadata_only_aliases=total_views-too_short-len(unique),
 aliases_not_yet_proven_tensor_prompt_model_identical=True,
 source_RGB_union_uncompressed_bytes=union_bytes,largest_source_RGB_union_uncompressed_bytes=largest_rgb_union,
 per_unique_view_RGB_duplication_uncompressed_bytes=raw_view_bytes,
 geometry_counts=[dict(width=w,height=h,records=n) for (w,h),n in sorted(geometry.items())],
 disk_free_bytes_snapshot=free,compression_ratio_not_assumed=True,
 accepted_old_B0_view_reuse_not_yet_audited=True,
 media_reads=0,decodes=0,encodes=0,model_calls=0,production_admitted=False,
 interpretation='Capacity planning only. No source-content or prediction-based parameter selection.',
 frozen_metadata_refs={k:refs[k] for k in docs})
print(json.dumps(out))
'''

def main():
    command = 'python3 -c "import base64;exec(base64.b64decode(\'' + base64.b64encode(REMOTE.encode()).decode() + '\'))"'
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                             'aic-inspur-home', command], capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(result.stderr)
    value = json.loads(result.stdout)
    target = Path(__file__).with_name('production_metadata_budget_10.json')
    with target.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
    print(json.dumps(value, ensure_ascii=False))

if __name__ == '__main__':
    main()
