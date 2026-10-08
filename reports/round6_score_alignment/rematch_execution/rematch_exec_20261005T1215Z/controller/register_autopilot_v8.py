"""Only small control deployment and local metadata; no model/media/ZIP transfer."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from register_b2_package_v1 import remote,REMOTE,PY,RUN

ENTRY='teacher_student_autopilot_v8'


def deploy():
    root=RUN/ENTRY; payload={}
    for path in root.rglob('*'):
        if not path.is_file() or any(n in path.parts for n in ('__pycache__','prelock_repairs','selection_01','pilot_selection')): continue
        if path.name in ('source_lock.json','registration.json','start_receipt.json','progress.json','completion.json','cpu_acceptance.json'): continue
        if path.name.endswith(('.stdout.txt','.stderr.txt')): continue
        if path.suffix not in ('.py','.txt','.json','.md','.cpp'): continue
        data=path.read_bytes(); payload[path.relative_to(root).as_posix()]=dict(sha256=hashlib.sha256(data).hexdigest(),data=base64.b64encode(data).decode())
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    remote('''import base64,hashlib,json,socket,shutil
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(%r)/%r;root.mkdir(exist_ok=True)
payload=json.loads(base64.b64decode(%r))
frozen=any((root/n).exists() for n in ('source_lock.json','registration.json','start_receipt.json'))
for name,row in payload.items():
    path=root/name;assert path.resolve().is_relative_to(root.resolve())
    data=base64.b64decode(row['data']);assert hashlib.sha256(data).hexdigest()==row['sha256']
    if path.exists() and path.read_bytes()==data:continue
    assert not frozen, 'never change registered control: '+name
    if path.exists():
        old=path.read_bytes();archive=root/'prelock_repairs'/name;archive.parent.mkdir(parents=True,exist_ok=True)
        archive.with_name(archive.name+'.'+hashlib.sha256(old).hexdigest()).write_bytes(old)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
old=Path(%r)/'teacher_student_autopilot_v7/runtime_schema_check'
target=root/'runtime_schema_check'
if not target.exists():assert not frozen;shutil.copyfile(old,target);target.chmod(0o755)
assert target.read_bytes()==old.read_bytes()
print(json.dumps({'status':'PASS_V8_SMALL_CONTROL_DEPLOYMENT','files':len(payload),'bytes':sum(len(base64.b64decode(r['data'])) for r in payload.values())}))
'''%(REMOTE,ENTRY,encoded,REMOTE))


def run(stage):
    if stage=='selection':
        script='''import subprocess,json
from pathlib import Path
root=Path(%r);here=root/%r
old=root/'next_round_v1/supervision_v2/selection_02'
receipt=json.loads((old/'selection_receipt.json').read_text())
command=[%r,'-B',str(here/'prepare_selection.py'),'--old-selection-dir',str(old),'--train-manifest',receipt['manifests']['train']['path'],'--dev-manifest',receipt['manifests']['dev']['path'],'--ffprobe','/home/inspur/anaconda3/envs/Andy/bin/ffprobe']
with (here/'selection_prepare.log').open('x') as log:
    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,cwd=root)
assert result.returncode==0,'selection failed; inspect preserved log'
print(json.dumps(json.loads((here/'selection_01/selection_receipt.json').read_text()),ensure_ascii=False))
'''%(REMOTE,ENTRY,PY)
    else:
        script='import subprocess\nsubprocess.run([%r,"-B",%r],check=True)'%(PY,REMOTE+'/'+ENTRY+'/'+stage+'.py')
    remote(script)


def acceptance():
    remote('''import subprocess,json,datetime
from pathlib import Path
here=Path(%r)/%r; results={}
for name in ('teacher_boundary_cpu_tests.py','student_cpu_tests.py','student_v8_cpu_tests.py','selection_cpu_tests.py','pipeline_cpu_tests.py'):
    with (here/(name+'.stdout.txt')).open('x') as out,(here/(name+'.stderr.txt')).open('x') as err:
        result=subprocess.run([%r,'-B',str(here/name)],cwd=here,stdout=out,stderr=err)
    results[name]=result.returncode
    print(name, result.returncode, flush=True)
    if result.returncode:raise RuntimeError('new CPU acceptance failed: '+name)
(here/'cpu_acceptance.json').write_text(json.dumps({'status':'PASS_V8_CPU_STAGE_AND_CONTRACT_TESTS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests':results,'GPU_started':False},indent=2)+chr(10))
'''%(REMOTE,ENTRY,PY))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('deploy','selection','accept','prepare','launch'));args=parser.parse_args()
    if args.stage=='deploy':deploy()
    elif args.stage=='accept':acceptance()
    else:run(args.stage)
