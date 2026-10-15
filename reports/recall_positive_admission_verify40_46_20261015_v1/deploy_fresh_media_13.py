"""One new fixed4 reference acquisition, only after frozen actual dev PASS."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT = Path(__file__).resolve().parent
WORK = REPORT.parents[1]
HOME = '/home/inspur/aic_video_work'
PARENT = HOME+'/recall_positive_admission_verify40_46_20261015_v1'
ROOT = PARENT+'/fresh_01'
SSH = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
       '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -']


def remote(code):
    p = subprocess.run(SSH,input=code,text=True,encoding='utf8',capture_output=True,timeout=60)
    if p.returncode:
        raise RuntimeError('Inspect retained deployment state; never implicitly retry: '+p.stderr[-4500:])
    return json.loads(p.stdout)


def save(name,value):
    with (REPORT/name).open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)


def main():
    assert not (REPORT/'fresh_media_launch_13.json').exists()
    pre = remote(r'''
import datetime as dt,hashlib,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');p=r.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
assert not (p/'incoming_fresh_media_13.zip').exists()
c=json.loads((p/'dev/chain_01/completion.json').read_text());v=json.loads((p/'dev/comparison_01/result.json').read_text())
assert c['status']==v['status']=='PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION' and all(v['conditions'].values())
assert c['comparison_ref']['sha256']==hashlib.sha256((p/'dev/comparison_01/result.json').read_bytes()).hexdigest()
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),disk=list(shutil.disk_usage(p)),
 memory=pathlib.Path('/proc/meminfo').read_text(),commands=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],capture_output=True,text=True,check=True).stdout.splitlines()[:20],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 actual_dev_status=v['status'],new_media_calls=0)))
'''.replace('__ROOT__',ROOT))
    save('fresh_media_resources_before_launch_13.json',pre)
    directory=WORK/'improvement/recall_positive_media_v1'
    files={}
    for path in directory.iterdir():
        if path.is_file() and path.suffix in ('.py','.md'):
            if path.suffix=='.py':ast.parse(path.read_text(encoding='utf8'))
            files['media_code/'+path.name]=path.read_bytes()
    assert 'media_code/positive_media.py' in files
    files['public_routes.json']=(REPORT/'public_routes_for_media_12.json').read_bytes()
    files['existing_dependency_refs.json']=(REPORT/'fresh_existing_dependency_refs_11.json').read_bytes()
    files['manifest.json']=json.dumps(dict(files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'fresh_media_control_13.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert len(data)<262144
    sent=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        str(bundle),'aic-inspur-home:'+PARENT+'/incoming_fresh_media_13.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:raise RuntimeError('SCP outcome unknown; inspect exact file before explicit recovery: '+sent.stderr)
    value=remote(r'''
import datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');parent=r.parent;h=pathlib.Path('__HOME__');incoming=parent/'incoming_fresh_media_13.zip'
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert incoming.stat().st_size==__BYTES__ and sha(incoming)=='__SHA__'
with zipfile.ZipFile(incoming) as z:
 assert len(set(z.namelist()))==len(z.namelist()) and z.testzip() is None
 m=json.loads(z.read('manifest.json'))['files'];assert set(z.namelist())==set(m)|{'manifest.json'}
 for name,row in m.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  data=z.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 r.mkdir();z.extractall(r)
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'media_code'))
import positive_media as src
deps=src.read(r/'existing_dependency_refs.json');required={};codes={}
def add(path,expected=None,code=False):
 path=pathlib.Path(path).resolve();assert path.is_relative_to(h) and path.is_file()
 digest=sha(path);assert expected is None or digest==expected
 required[str(path)]=digest
 if code:codes[str(path)]=digest
 return dict(path=str(path),sha256=digest)
refs={
 'protocol_ref':add(parent/'protocol_v2.json'), 'authorization_ref':add(parent/'USER_AUTHORIZATION.json'),
 'development_result_ref':add(parent/'dev/comparison_01/result.json'),
 'development_selection_ref':add(parent/'dev/selection_before_confirmation.json'),
 'development_registration_ref':add(parent/'registration.json'),
 'source_candidates_ref':add(parent/'reference_candidates.json'), 'public_routes_ref':add(r/'public_routes.json'),
 'annotation_file_ref':add(deps['annotation_file_path'],deps['annotation_file_sha256']),
 'known_exclusions_ref':add(deps['known_exclusions_path'],deps['known_exclusions_sha256'])}
for path in (r/'media_code').glob('*.py'):add(path,code=True)
for value in deps['native_profile_refs']:add(value['path'],value['sha256'],code=True)
for value in deps['all14_media_receipts']+deps['source_scope_refs']:add(value['path'],value['sha256'])
add(r/'existing_dependency_refs.json');add(parent/'official_rule_check_01.json')
candidates=src.read(parent/'reference_candidates.json')
reg=dict(schema=src.SCHEMA,status=src.STATUS,group='confirm',registered_at_utc=src.utc(),expected_accepted_sources=4,
 maximum_media_pool_bytes=49919698,route_acquisition_method='HEAD',windows_video_body_bytes=0,
 selection=candidates['selection'],ordered_engineering_reserves=candidates['ordered_engineering_reserves'],
 prior_media_receipts=deps['all14_media_receipts'],old_exposed_and_reserved_ids=candidates['exclusions']['all_old_conservative_plus_acquired_IDs'],
 source_scope_refs=deps['source_scope_refs'],required_files=required,required_code_files=codes,**refs)
src.save(r/'media_registration.json',reg)
src.registration(r)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'media_code/positive_media.py'),'--root',str(r)]
src.save(r/'media_launch_claim_13.json',dict(utc=src.utc(),argv=argv,registration_sha256=sha(r/'media_registration.json'),CPU_only=True))
with (r/'media_13.log').open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=src.utc(),host=socket.gethostname(),pid=p.pid,start_ticks=stat[19],argv=argv,CPU_only=True,
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'media_registration.json'),
 selected_confirm_ids=[v['video_id'] for v in reg['selection']],maximum_media_pool_bytes=49919698,
 new_model_calls_at_launch=0,production_admitted=False,Windows_media_body_bytes=0,old_success_repeated=False)
src.save(r/'media_launch_13.json',value);print(json.dumps(value))
'''.replace('__ROOT__',ROOT).replace('__HOME__',HOME).replace('__BYTES__',str(len(data))).replace('__SHA__',digest))
    save('fresh_media_launch_13.json',value)
    print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':main()
