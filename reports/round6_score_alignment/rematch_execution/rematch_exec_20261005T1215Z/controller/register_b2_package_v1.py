"""Small authorized SSH code deployment and sequential B2 CPU/freeze/launch."""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

RUN=Path(__file__).resolve().parent.parent
REMOTE='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
ENTRY='b_score_aligned_package_v1'


def remote(script, echo=True):
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','aic-inspur-home',PY+' -B -'],
        input=script.encode('utf-8'),capture_output=True,timeout=2400)
    if echo and result.stdout:print(result.stdout.decode('utf-8',errors='replace'),end='',flush=True)
    if result.stderr:print(result.stderr.decode('utf-8',errors='replace'),end='',flush=True)
    if result.returncode:raise RuntimeError('remote B2 control failed: '+str(result.returncode))
    return result.stdout


def deploy():
    payload={}
    for path in (RUN/ENTRY).iterdir():
        if path.is_file() and path.suffix in ('.py','.md','.json') and path.name not in (
            'source_lock.json','cpu_acceptance.json','processor_acceptance.json','cache_bindings.json','registration.json','launch.json','progress.json','completion.json'):
            data=path.read_bytes();payload[path.name]=dict(sha256=hashlib.sha256(data).hexdigest(),data=base64.b64encode(data).decode())
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    remote("""import base64,hashlib,json,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r)/%r;root.mkdir(exist_ok=True)
payload=json.loads(base64.b64decode(%r))
for name,row in payload.items():
    assert Path(name).name==name
    path=root/name;data=base64.b64decode(row['data'])
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    if path.exists() and path.read_bytes()!=data:
        assert not (root/'source_lock.json').exists() and not (root/'registration.json').exists(),'frozen B2 code'
        old=path.read_bytes();archive=root/'prelock_repairs';archive.mkdir(exist_ok=True)
        (archive/(name+'.'+hashlib.sha256(old).hexdigest())).write_bytes(old)
        path.write_bytes(data)
    elif path.exists():assert path.read_bytes()==data
    else:
        assert not (root/'source_lock.json').exists() and not (root/'registration.json').exists()
        path.write_bytes(data)
print(json.dumps({'status':'PASS_SMALL_B2_CONTROL_DEPLOYMENT','files':len(payload),
    'bytes':sum(len(base64.b64decode(r['data'])) for r in payload.values())}))
"""%(REMOTE,ENTRY,encoded))


def accept():
    remote("""import os,subprocess,time,json
from pathlib import Path
root=Path(%r)/%r
env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
    HF_HOME=str(root.parent/'cache/hf'),XDG_CACHE_HOME=str(root.parent/'cache'),TMPDIR=str(root.parent/'tmp'))
for name,args in [('cpu_tests.py',[]),('processor_cpu.py',[]),('prepare.py',[])]:
    if (root/'source_lock.json').exists():raise RuntimeError('never rerun frozen CPU registration')
    tag=str(time.time_ns())
    result=subprocess.run([%r,'-B',str(root/name),*args],cwd=root,env=env,capture_output=True,timeout=1800)
    (root/(name+'.'+tag+'.stdout.log')).write_bytes(result.stdout)
    (root/(name+'.'+tag+'.stderr.log')).write_bytes(result.stderr)
    print(result.stdout.decode(errors='replace'),flush=True)
    if result.returncode:
        print(result.stderr.decode(errors='replace'),flush=True)
        raise RuntimeError(name+' failed B2 CPU registration')
script='from common import verify; c=verify(); print(c["candidate_arm"])'
result=subprocess.run([%r,'-B','-c',script],cwd=root,env=env,capture_output=True,timeout=600)
print(result.stdout.decode(errors='replace'),flush=True)
if result.returncode:
    print(result.stderr.decode(errors='replace'),flush=True)
    raise RuntimeError('B2 sealed preflight failed')
"""%(REMOTE,ENTRY,PY,PY))
    fetch(('cpu_acceptance.json','processor_acceptance.json','cache_bindings.json','source_lock.json'))


def fetch(names):
    raw=remote("""import base64,json
from pathlib import Path
root=Path(%r)/%r
print(json.dumps({name:base64.b64encode((root/name).read_bytes()).decode() for name in %r if (root/name).is_file()}))
"""%(REMOTE,ENTRY,names),echo=False)
    for name,data in json.loads(raw).items():
        (RUN/ENTRY/name).write_bytes(base64.b64decode(data))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('deploy','accept','launch','fetch'));args=parser.parse_args()
    if args.stage=='deploy':deploy()
    elif args.stage=='accept':accept()
    elif args.stage=='launch':
        remote('import subprocess\nsubprocess.run([%r,"-B",%r],check=True)'%(PY,REMOTE+'/'+ENTRY+'/launch.py'))
        fetch(('launch.json','registration.json','progress.json','completion.json'))
    else:fetch(('launch.json','registration.json','progress.json','completion.json','cpu_acceptance.json','processor_acceptance.json','cache_bindings.json','source_lock.json'))
