"""Copy small receipts/raw answers through Mac; never downloads weights or old media."""
import base64,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R='/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2'
names=['completion.json','started.json','launch.json','state.json','vision_dependency.json','train/training_acceptance.json','train/train_metrics.json','train/optimizer_observations.jsonl']
names += [f'{x}_predictions.jsonl' for x in ('new','base','pilot','production_B')]
names += [f'aic_ANNITER10_{x}_01.resource.json' for x in ('train','new','base','pilot','production_B','vision')]
code=f'''from pathlib import Path
import base64,hashlib,json
r=Path({R!r});assert (r/'completion.json').exists()
assert json.loads((r/'state.json').read_text())['stage']=='COMPLETE_AWAIT_INDEPENDENT_CPU_QUALITY'
owned=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:cmd=proc.joinpath('cmdline').read_bytes().decode().split('\\x00')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if any(str(r/name) in cmd for name in ('controller_v2.py','observed_train.py','predict_scores.py','vision_dependency.py')):owned.append({{'pid':int(proc.name),'command':cmd}})
assert not owned,owned
ledger=[json.loads(s) for s in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
names={names!r};result={{}}
for n in names:
 p=r/n;raw=p.read_bytes();result[n]={{'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}}
 if n.endswith('.resource.json'):
  receipt=json.loads(raw);assert receipt['status']=='completed' and receipt['exit_code']==0
  matches=[v for v in ledger if v['name']==receipt['name']];assert len(matches)==1 and matches[0]==receipt
print(json.dumps(result))
'''
r=subprocess.run(['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=20','aic-inspur-home','python3','-B','-'],input=code,text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stderr+r.stdout)
data=json.loads(r.stdout);assert sum(v['bytes'] for v in data.values())<2_000_000
dest=H/'results';dest.mkdir(exist_ok=True)
for name,item in data.items():
 raw=base64.b64decode(item['base64']);assert hashlib.sha256(raw).hexdigest()==item['sha256']
 path=dest/name;path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():assert path.read_bytes()==raw
 else:
  with path.open('xb') as f:f.write(raw)
receipt={'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX_RECEIPT_DOWNLOAD','bytes':sum(v['bytes'] for v in data.values()),'files':{k:{n:v[n] for n in ('bytes','sha256')} for k,v in data.items()}}
with (H/'result_transfer.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps({'bytes':receipt['bytes'],'files':len(data)}))
