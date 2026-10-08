"""Small explicitly authorized control deployment; no data/model/ZIP transfer."""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from register_b2_package_v1 import remote, REMOTE, RUN, PY

ENTRY = 'context_advisory_v1'


def deploy():
    payload = {}
    for path in (RUN/ENTRY).iterdir():
        if path.is_file() and path.suffix in ('.py','.md'):
            data=path.read_bytes(); payload[path.name]={'sha256':hashlib.sha256(data).hexdigest(),'data':base64.b64encode(data).decode()}
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    remote('''import base64,hashlib,json,socket,py_compile
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r)/%r
assert not (root/'source_lock.json').exists() and not (root/'start.json').exists(), 'already frozen or started'
payload=json.loads(base64.b64decode(%r))
for name,row in payload.items():
    assert Path(name).name==name
    data=base64.b64decode(row['data']); assert hashlib.sha256(data).hexdigest()==row['sha256']
    path=root/name
    if path.exists() and path.read_bytes()!=data:
        archive=root/'prelock_repairs';archive.mkdir(exist_ok=True)
        old=path.read_bytes(); backup=archive/(name+'.'+hashlib.sha256(old).hexdigest())
        if not backup.exists():backup.write_bytes(old)
        path.write_bytes(data)
    elif not path.exists():path.write_bytes(data)
    if path.suffix=='.py':compile(path.read_text(),str(path),'exec')
print(json.dumps({'status':'PASS_SMALL_UNFROZEN_CONTROL_DEPLOYMENT','files':len(payload),'bytes':sum(len(base64.b64decode(r['data'])) for r in payload.values())}))
'''%(REMOTE,ENTRY,encoded))


def command(stage):
    filename={'engineering':'engineering_checks.py','freeze':'freeze.py','launch':'launch.py'}[stage]
    remote('''import os,subprocess
from pathlib import Path
root=Path(%r)/%r
env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
    HF_HOME=str(root.parent/'cache/hf'),XDG_CACHE_HOME=str(root.parent/'cache'),TMPDIR=str(root.parent/'tmp'))
subprocess.run([%r,'-B',str(root/%r)],env=env,cwd=root,check=True)
'''%(REMOTE,ENTRY,PY,filename))


def fetch():
    names=('prepared.json','draft_preflight.json','cpu_build_acceptance.json','source_lock.json','preflight.json','start.json','registration.json','progress.json','completion.json','execution_failure.json')
    data=json.loads(remote('''import json,base64
from pathlib import Path
root=Path(%r)/%r
print(json.dumps({n:base64.b64encode((root/n).read_bytes()).decode() for n in %r if (root/n).is_file()}))
'''%(REMOTE,ENTRY,names),echo=False))
    for name, value in data.items():(RUN/ENTRY/name).write_bytes(base64.b64decode(value))
    print(json.dumps({'status':'PASS_SMALL_CONTROL_RECEIPT_FETCH','names':list(data)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('deploy','engineering','freeze','launch','fetch'))
    stage=p.parse_args().stage
    if stage=='deploy':deploy()
    elif stage=='fetch':fetch()
    else:command(stage)
