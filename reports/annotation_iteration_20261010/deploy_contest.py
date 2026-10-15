"""Small reviewed controls via live Mac jump; preserve all previous files."""
import base64,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R='/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2'
names=['contest_engine.py','contest_controller_v1.py','selector_contract.py','score_grammar.py','quality_result.json','cpu_quality_acceptance_protocol.json','CONTEST_PROTOCOL.md']
files={n:{'base64':base64.b64encode((H/n).read_bytes()).decode(),'sha256':hashlib.sha256((H/n).read_bytes()).hexdigest()} for n in names}
code=f'''from pathlib import Path
import base64,hashlib,json,os,socket,subprocess
assert socket.gethostname()=='inspur-NP5570M5'
r=Path({R!r});assert (r/'completion.json').exists();assert not (r/'contest_v1').exists()
files={files!r}
for name,item in files.items():
 raw=base64.b64decode(item['base64']);assert hashlib.sha256(raw).hexdigest()==item['sha256'];p=r/name
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
d=r/'contest_v1';d.mkdir()
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (d/'controller.log').open('xb') as log:child=subprocess.Popen([py,'-B',str(r/'contest_controller_v1.py')],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env={{**os.environ,'USE_TF':'0'}})
receipt={{'pid':child.pid,'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX_SMALL_CONTROLS','files':{{n:v['sha256'] for n,v in files.items()}}}}
with (d/'launch.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''
result=subprocess.run(['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=20','aic-inspur-home','python3','-B','-'],input=code,text=True,capture_output=True)
if result.returncode:raise RuntimeError(result.stderr+result.stdout)
receipt=json.loads(result.stdout)
with (H/'contest_launch.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps({'pid':receipt['pid'],'bytes':sum((H/n).stat().st_size for n in names)}))
