"""Only small control deployment and local metadata; no model/media/ZIP transfer."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from register_b2_package_v1 import remote,REMOTE,PY,RUN

ENTRY='teacher_student_autopilot_v13'


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
    if path.name=='accepted_resume_manifest.json' and path.exists():
        assert not json.loads(path.read_bytes()).get('accepted'), 'never overwrite nonempty approved success manifest; fetch actual receipt first'
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
        script="""import shutil,json
from pathlib import Path
r=Path(%r);old=r/'teacher_student_autopilot_v11';new=r/%r
assert not any((new/n).exists() for n in ('source_lock.json','registration.json','start_receipt.json'))
for name in ('selection_01','pilot_selection'):
    src=old/name;dst=new/name
    assert not dst.exists(), 'selection already copied; never overwrite'
    shutil.copytree(src,dst)
    for p in src.rglob('*'):
        if p.is_file():assert p.read_bytes()==(dst/p.relative_to(src)).read_bytes()
print(json.dumps({'status':'PASS_ORIGINAL_PREREGISTERED_SELECTION_BYTES_REUSED','new_seed':False,'new_unseen_selection_claimed':False,'train':128,'dev':32,'pilot':24}))
"""%(REMOTE,ENTRY)
    elif stage=='manifest':
        script="""from pathlib import Path
import hashlib,json
r=Path(%r);old=r/'teacher_student_autopilot_v12/v11_resume_manifest.json';new=r/%r/'v11_resume_manifest.json'
assert not new.exists() and hashlib.sha256(old.read_bytes()).hexdigest()=='a0de013f0407197b129b074e3b20e159726a83ef64b2845e8f2d38998f0afad4'
new.write_bytes(old.read_bytes());print(json.dumps({'status':'PASS_ORIGINAL_EXACT_MANIFEST_COPY_NO_NEW_GENERATION'}))
"""%(REMOTE,ENTRY)
    else:
        script='import subprocess\nsubprocess.run([%r,"-B",%r],check=True)'%(PY,REMOTE+'/'+ENTRY+'/'+('v11_resume' if stage=='manifest' else stage)+'.py')
    remote(script)


def acceptance():
    remote('''import subprocess,json,datetime
from pathlib import Path
here=Path(%r)/%r; results={}
for name in ('resume_cpu_tests.py',):
    attempt=1
    while (here/(name+'.attempt'+str(attempt)+'.stdout.txt')).exists():attempt+=1
    with (here/(name+'.attempt'+str(attempt)+'.stdout.txt')).open('x') as out,(here/(name+'.attempt'+str(attempt)+'.stderr.txt')).open('x') as err:
        result=subprocess.run([%r,'-B',str(here/name)],cwd=here,stdout=out,stderr=err)
    results[name]=result.returncode
    print(name, result.returncode, flush=True)
    if result.returncode:raise RuntimeError('new CPU acceptance failed: '+name)
(here/'cpu_acceptance.json').write_text(json.dumps({'status':'PASS_V8_CPU_STAGE_AND_CONTRACT_TESTS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests':results,'GPU_started':False},indent=2)+chr(10))
'''%(REMOTE,ENTRY,PY))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('deploy','selection','manifest','accept','prepare','launch'));args=parser.parse_args()
    if args.stage=='deploy':deploy()
    elif args.stage=='accept':acceptance()
    else:run(args.stage)
