"""Small read-only metadata status receipt; no restart or payload export."""
import json
import shlex
import subprocess

PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15',
       '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-home']
code = r'''import hashlib,json,os
from pathlib import Path
p=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_v1')
out=p/'metadata_01'
if (out/'completion.json').exists():
 value=json.loads((out/'completion.json').read_text());value['completion_sha256']=hashlib.sha256((out/'completion.json').read_bytes()).hexdigest();print(json.dumps(value))
elif (out/'failure.json').exists():
 value=json.loads((out/'failure.json').read_text());value['status']='FAILED_RETAINED_NO_RESTART';value['actual_files']=[{'name':q.name,'bytes':q.stat().st_size} for q in out.iterdir() if q.is_file()];print(json.dumps(value))
else:
 launch=json.loads((p/'metadata_launch_01.json').read_text());pid=launch['pid'];proc=Path('/proc')/str(pid)
 attempts=[json.loads(x) for x in (out/'http.jsonl').read_text().splitlines()] if (out/'http.jsonl').exists() else []
 print(json.dumps({'status':'RUNNING_OR_TERMINAL_NOT_YET_WRITTEN','pid':pid,'proc_exists':proc.exists(),'argv':(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace') if proc.exists() else None,'accepted_metadata_ranges':sum(x['event']=='ACCEPTED' for x in attempts),'requested_metadata_ranges':sum(x['event']=='REQUEST' for x in attempts),'files':[{'name':q.name,'bytes':q.stat().st_size} for q in out.iterdir() if q.is_file()] if out.exists() else []}))
'''
result = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)], capture_output=True, check=True)
print(result.stdout.decode(), end='')
