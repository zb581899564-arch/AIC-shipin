"""Transfer only new control scripts through Mac, then launch the authorized pilot."""
import ast
import base64
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
source=HERE/'finetune_20261009_v3'
files={}
for p in [source/n for n in ('controller.py','observed_train.py','observed_predict.py','crop_recovery_acceptance.json')]:
    raw=p.read_bytes()
    if p.suffix=='.py':ast.parse(raw)
    files[p.name]={'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}
code=f'''import ast,base64,hashlib,json,os,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path('/home/inspur/aic_video_work');assert root.resolve(strict=True)==root
dest=root/'runs/annotation_finetune_20261009_v3'
assert dest.parent.resolve(strict=True)==dest.parent and not dest.exists() and not dest.is_symlink()
files={files!r}
dest.mkdir()
for name,record in files.items():
 raw=base64.b64decode(record['base64']);assert hashlib.sha256(raw).hexdigest()==record['sha256']
 if name.endswith('.py'):ast.parse(raw)
 with (dest/name).open('xb') as f:f.write(raw)
assert len(files)==4
py=root/'env/qwen3vl_isolated_20260910/bin/python'
with (dest/'controller.log').open('xb') as log:
 p=subprocess.Popen([str(py),'-B',str(dest/'controller.py')],stdin=subprocess.DEVNULL,
 stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
 env={{**os.environ,'USE_TF':'0','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1'}})
receipt={{'status':'AUTHORIZED_FINETUNE_CONTROLLER_LAUNCHED_NOT_YET_VALIDATED','pid':p.pid,
 'directory':str(dest),'scripts_sha256':{{n:r['sha256'] for n,r in files.items()}},
 'route':'WINDOWS_MACMINI_PROXYJUMP_LINUX','control_script_bytes':sum(len(base64.b64decode(r['base64'])) for r in files.values())}}
with (dest/'launch.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''
cmd=['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
     '-o','ConnectTimeout=20','aic-inspur-home','python3','-B','-']
r=subprocess.run(cmd,input=code,text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stderr+r.stdout)
receipt=json.loads(r.stdout)
with (source/'launch.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt),flush=True)
