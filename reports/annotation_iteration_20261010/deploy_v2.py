"""Small reviewed controls through online Mac ProxyJump; no dataset/model upload."""
import ast,base64,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
old=H.parent/'qwen8b_annotation_20261009_v1/training_v2'
observed=old/'finetune_20261009_v3/observed_train.py'
if not (H/'observed_train.py').exists():(H/'observed_train.py').write_bytes(observed.read_bytes())
config=json.loads((old/'configs/temporal_fixed.json').read_text());config.update(learning_rate=1e-4,epochs=3,gradient_accumulation_steps=4,status='FROZEN_ONE_SUFFICIENT_OPTIMIZATION_RECIPE')
if not (H/'temporal_config.json').exists():(H/'temporal_config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
files={}
for name in ('controller_v2.py','observed_train.py','predict_scores.py','score_grammar.py','vision_dependency.py','temporal_config.json','PLAN.md'):
    p=H/name;raw=p.read_bytes()
    if p.suffix=='.py':ast.parse(raw)
    files[name]={'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}
code=f'''import ast,base64,hashlib,json,os,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path('/home/inspur/aic_video_work');dest=root/'runs/annotation_iteration_20261010_v2'
assert dest.parent.resolve(strict=True)==dest.parent and not dest.exists()
files={files!r}
dest.mkdir()
for name,item in files.items():
 raw=base64.b64decode(item['base64']);assert hashlib.sha256(raw).hexdigest()==item['sha256']
 if name.endswith('.py'):ast.parse(raw)
 with (dest/name).open('xb') as f:f.write(raw)
py=root/'env/qwen3vl_isolated_20260910/bin/python'
with (dest/'controller.log').open('xb') as log:
 p=subprocess.Popen([str(py),'-B',str(dest/'controller_v2.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={{**os.environ,'USE_TF':'0','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1'}})
receipt={{'pid':p.pid,'remote_directory':str(dest),'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX','control_bytes':sum(len(base64.b64decode(v['base64'])) for v in files.values()),'files_sha256':{{n:v['sha256'] for n,v in files.items()}},'status':'LAUNCHED_NOT_YET_QUALITY_VALIDATED'}}
with (dest/'launch.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''
assert not (H/'launch_v2.json').exists()
r=subprocess.run(['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=20','aic-inspur-home','python3','-B','-'],input=code,text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stderr+r.stdout)
value=json.loads(r.stdout)
with (H/'launch_v2.json').open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
