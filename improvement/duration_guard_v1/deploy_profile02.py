"""Deploy only the independent reserved-five profile over authorized small-control SSH."""
import hashlib
import io
import json
import shlex
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/duration_guard_iteration_20261013_v1'
CODE=Path(__file__).parent
REMOTE='/home/inspur/aic_video_work/duration_guard_iteration_20261013_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15',
     '-o','ServerAliveInterval=15','aic-inspur-home']

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    rows={'code/'+p.name:p for p in sorted(CODE.glob('*.py')) if p.name!='deploy_profile02.py'}
    for name in ('PROTOCOL.md','EVALUATION_POLICY.md','NATIVE_MAPPING_CONTRACT_V3.md',
            'new5_source_registration_01.json','new5_route_authorization_01.json',
            'new5_cpu_registration_02.json','new5_inference_registration_02.json','profile_engineering_fix_01.json'):
        rows[name]=REPORT/name
    rows['screen_selection_before_new5_confirm.json']=REPORT/'screen_01/selection_before_new5_confirm.json'
    rows['known_identity_snapshot_01.json']=ROOT/'reports/human_reference_iteration_20261013_v1/known_identity_snapshot_01.json'
    manifest={name:dict(bytes=path.stat().st_size,sha256=sha(path.read_bytes())) for name,path in rows.items()}
    package=REPORT/'new5_cpu_control_02.zip'
    with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED) as out:
        for name,path in rows.items(): out.writestr(name,path.read_bytes())
        out.writestr('manifest_profile02.json',json.dumps(manifest,indent=2))
    payload=package.read_bytes()
    script='''import datetime,hashlib,io,json,os,socket,subprocess,sys,zipfile
from pathlib import Path
base=Path(REMOTE)
assert socket.gethostname()=='inspur-NP5570M5'
assert not (base/'cpu_chain_01').exists() and not (base/'new5_chain_01').exists()
owned=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  argv=(p/'cmdline').read_bytes().split(b'\\0')
  if any(x.startswith((str(base)+'/code/').encode()) for x in argv): owned.append(p.name)
 except (OSError,PermissionError): pass
assert not owned,owned
raw=sys.stdin.buffer.read()
assert len(raw)==SIZE and hashlib.sha256(raw).hexdigest()==DIGEST
archive=zipfile.ZipFile(io.BytesIO(raw))
assert archive.testzip() is None
manifest=json.loads(archive.read('manifest_profile02.json'))
assert set(archive.namelist())==set(manifest)|{'manifest_profile02.json'}
pending=[]
for name,item in manifest.items():
 path=base/name
 assert path.resolve().is_relative_to(base.resolve()) and not path.is_symlink()
 data=archive.read(name)
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
 if path.exists(): assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],str(path)
 else: pending.append((path,data))
for path,data in pending:
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f: f.write(data)
receipt=dict(status='PASS_RESERVED5_PROFILE02_SMALL_CONTROL_TRANSFER',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),members=manifest,created_members=len(pending),existing_equal_members=len(manifest)-len(pending),hostname=socket.gethostname(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_model_calls=0)
with (base/'control_deployment_02.json').open('x') as f: json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''
    script=script.replace('REMOTE',repr(REMOTE)).replace('SIZE',str(len(payload))).replace('DIGEST',repr(sha(payload)))
    response=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(script)],input=payload,capture_output=True,check=True)
    result=json.loads(response.stdout)
    assert result['bytes']==len(payload) and result['sha256']==sha(payload) and result['members']==manifest
    with (REPORT/'control_deployment_02.json').open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='members'}))

if __name__=='__main__': main()
