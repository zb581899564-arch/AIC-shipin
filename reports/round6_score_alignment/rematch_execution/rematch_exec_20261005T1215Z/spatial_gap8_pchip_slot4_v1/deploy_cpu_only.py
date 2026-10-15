"""Small authorized control upload into this new unfrozen route only."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REMOTE='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/spatial_gap8_pchip_slot4_v1'

def main():
    files=[]
    for name in sys.argv[1:]:
        assert Path(name).name==name
        data=(HERE/name).read_bytes()
        if name.endswith('.py'):ast.parse(data.decode('utf-8-sig'),filename=name)
        files.append(dict(name=name,sha256=hashlib.sha256(data).hexdigest(),data=base64.b64encode(data).decode()))
    bootstrap='''import json,sys,base64,hashlib,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
p=Path(REMOTE)
assert not (p/'source_lock.json').exists() and not (p/'start.json').exists()
fs=json.load(sys.stdin);p.mkdir(exist_ok=True)
for v in fs:
 assert Path(v['name']).name==v['name']
 data=base64.b64decode(v['data']);assert hashlib.sha256(data).hexdigest()==v['sha256']
 q=p/v['name']
 if q.exists() and q.read_bytes()!=data:
  old=q.read_bytes();h=hashlib.sha256(old).hexdigest()
  a=p/'prelock_repairs'/h/v['name'];a.parent.mkdir(parents=True,exist_ok=True)
  if a.exists():assert a.read_bytes()==old
  else:
   with a.open('xb') as s:s.write(old)
  q.write_bytes(data)
 elif not q.exists():
  with q.open('xb') as s:s.write(data)
print(json.dumps({'status':'DEPLOYED_NEW_UNFROZEN_CPU_CODE_ONLY','files':{v['name']:v['sha256'] for v in fs},'bytes':sum(len(base64.b64decode(v['data'])) for v in fs),'no_launcher':True}))'''.replace('REMOTE',repr(REMOTE))
    cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','aic-inspur-home',
         '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -c '+shlex.quote(bootstrap)]
    result=subprocess.run(cmd,input=json.dumps(files),text=True,capture_output=True)
    print(result.stdout);print(result.stderr);result.check_returncode()

if __name__=='__main__':main()
