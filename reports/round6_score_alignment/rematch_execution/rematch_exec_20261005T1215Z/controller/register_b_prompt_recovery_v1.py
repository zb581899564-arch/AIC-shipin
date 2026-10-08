"""Only small explicitly authorized direct-SSH control code, no new data/model."""
import argparse
import base64
import hashlib
import json
from register_b2_package_v1 import remote,REMOTE,RUN,PY

ENTRY='b_prompt_recovery_v1'


def deploy():
    payload={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'data':base64.b64encode(p.read_bytes()).decode()}
        for p in (RUN/ENTRY).iterdir() if p.is_file() and p.suffix in ('.py','.md')}
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    remote('''import base64,hashlib,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r)/%r
root.mkdir(exist_ok=True)
assert not (root/'source_lock.json').exists() and not (root/'start.json').exists(), 'already frozen or started'
payload=json.loads(base64.b64decode(%r))
for name,row in payload.items():
 assert Path(name).name==name
 data=base64.b64decode(row['data']);assert hashlib.sha256(data).hexdigest()==row['sha256']
 p=root/name
 if p.exists() and p.read_bytes()!=data:
  old=p.read_bytes();archive=root/'prelock_repairs';archive.mkdir(exist_ok=True)
  backup=archive/(name+'.'+hashlib.sha256(old).hexdigest())
  if not backup.exists():backup.write_bytes(old)
  p.write_bytes(data)
 elif not p.exists():p.write_bytes(data)
 if p.suffix=='.py':compile(data,str(p),'exec')
print(json.dumps({'status':'PASS_SMALL_UNFROZEN_BOUNDARY_CONTROL_DEPLOYMENT','files':len(payload),'bytes':sum(len(base64.b64decode(x['data'])) for x in payload.values())}))
'''%(REMOTE,ENTRY,encoded))


def command(stage):
    file={'prepare':'prepare.py','checks':'cpu_checks.py','freeze':'freeze.py','launch':'launch.py'}[stage]
    remote('''import os,subprocess,time
from pathlib import Path
root=Path(%r)/%r
env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
 HF_HOME=str(root.parent/'cache/hf'),XDG_CACHE_HOME=str(root.parent/'cache'),TMPDIR=str(root.parent/'tmp'))
with (root/('control_'+%r+'_'+str(time.time_ns())+'.log')).open('x') as log:
 result=subprocess.run([%r,'-B',str(root/%r)],env=env,cwd=root,stdout=log,stderr=subprocess.STDOUT)
 log.flush()
 print(Path(log.name).read_text(),flush=True)
 if result.returncode:raise RuntimeError('control stage failed; original log retained: '+log.name)
'''%(REMOTE,ENTRY,stage,PY,file))


def fetch():
    names=('prepared.json','cpu_acceptance.json','source_lock.json','preflight.json','start.json','registration.json','progress.json','first_real_acceptance.json','inference_completion.json','completion.json','final_acceptance.json','scientific_stop.json','execution_failure.json')
    data=json.loads(remote('''import json,base64
from pathlib import Path
root=Path(%r)/%r
print(json.dumps({n:base64.b64encode((root/n).read_bytes()).decode() for n in %r if (root/n).is_file()}))
'''%(REMOTE,ENTRY,names),echo=False))
    for name,value in data.items():(RUN/ENTRY/name).write_bytes(base64.b64decode(value))
    print('PASS_SMALL_BOUNDARY_CONTROL_RECEIPTS',list(data))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('deploy','prepare','checks','freeze','launch','fetch'))
    stage=parser.parse_args().stage
    if stage=='deploy':deploy()
    elif stage=='fetch':fetch()
    else:command(stage)
