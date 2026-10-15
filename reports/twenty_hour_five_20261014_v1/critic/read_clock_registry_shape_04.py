"""Only shape of named frozen clocks and source-field metadata, no media."""
import shlex
import subprocess
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','aic-inspur-home']
code=r'''import json
from pathlib import Path
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
p=run/'baseline_pts_v4/scan_01/clock_registry.json';v=json.loads(p.read_text())
result={'registry_keys':list(v)}
for k,x in v.items():
 if isinstance(x,list):result[k]={'length':len(x),'first_keys':list(x[0]) if x and isinstance(x[0],dict) else None,'first':x[0] if x and isinstance(x[0],dict) else None}
 if isinstance(x,dict):result[k]={'length':len(x),'first_value_keys':list(next(iter(x.values()))) if x and isinstance(next(iter(x.values())),dict) else None}
for base in [run/'b_score_aligned_package_v4/rematch_01',run/'balanced_two_window_risk_v3/rematch_01']:
 path=base/'field_frames.jsonl';first=json.loads(next(line for line in path.open() if line.strip()))
 result[str(base)]={'field_frame_keys':list(first),'field_file_bytes':path.stat().st_size,'metadata_keys':list(json.loads((base/'metadata.json').read_text()))}
print(json.dumps(result))
'''
if __name__=='__main__':
 r=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)],capture_output=True,check=True)
 print(r.stdout.decode(),end='')
