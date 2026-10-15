"""One explicit remaining-only recovery after the retained source-order QA failure."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT = Path(__file__).resolve().parent
WORK = REPORT.parents[1]
MAIN = '/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1'
ROOT = MAIN+'/fresh_01'
SSH = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
       '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -']


def remote(code):
    result = subprocess.run(SSH, input=code, text=True, encoding='utf8', capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Inspect retained remote state; never repeat an uncertain deployment/launcher: '+result.stderr[-6000:])
    return json.loads(result.stdout)


def save(name, value):
    with (REPORT/name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def main():
    assert not (REPORT/'fresh_remaining_recovery_launch_19.json').exists()
    pre = remote(r'''
import datetime as dt,hashlib,json,pathlib,shutil,socket,subprocess
r=pathlib.Path('__ROOT__');main=r.parent;h=main.parent
assert socket.gethostname()=='inspur-NP5570M5'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(pathlib.Path(p).read_text())
assert not any((r/name).exists() for name in ['recovery_v2','positive_fresh_recovery_registration_v2.json','remaining_recovery_claim_19.json','incoming_remaining_recovery_19.zip','confirm/chain_02','confirm/B0/input_qa_01','cpu_acceptance_confirm.json','gpu_admission_confirm_B0.json','confirm/B0/gpu_01','confirm/VERIFY'])
assert not (main/'registration_confirm.json').exists()
old=read(r/'positive_fresh_registration.json');primary=read(r/'confirm/inputs_01/completion.json');failure=read(r/'confirm/chain_01/failure.json')
assert primary['actual_input_count']==primary['primary_encode_calls_started']==primary['primary_encode_calls_returned']==28
assert primary['actual_new_RGB_decode_passes']==4 and primary['first_independent_input_replays_already_completed']==0
assert failure['stage']=='FIRST_ALL_NATIVE_INPUT_QA_PRE_GPU' and not (r/'confirm/chain_01/completion.json').exists()
assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(old['deadline'])
run=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ledger=h/'improvement_round1/gpu_ledger.jsonl'
ledgertext=ledger.read_text() if ledger.exists() else ''
for budget in old['gpu_budget'].values():
 assert not (run/'controller'/(budget['gpu_job_name']+'.resource.json')).exists()
 assert budget['gpu_job_name'] not in ledgertext
 newname=budget['gpu_job_name'].removesuffix('_v1')+'_v2'
 assert newname not in ledgertext and not (run/'controller'/(newname+'.resource.json')).exists()
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(main) not in argv:continue
  stat=(p/'stat').read_text().rsplit(')',1)[1].split()
  owned.append(dict(pid=p.name,ppid=stat[1],state=stat[0],start_ticks=stat[19],argv=argv,io=(p/'io').read_text()))
 except (OSError,ProcessLookupError):pass
assert not owned
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),owned=owned,
 disk=list(shutil.disk_usage(r)),memory=pathlib.Path('/proc/meminfo').read_text(),
 tasks=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],capture_output=True,text=True,check=True).stdout.splitlines()[:18],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 actual_primary_inputs=28,adopted_RGB_sources=4,first_input_QA_calls=0,actual_model_calls=0,
 retained_failure_sha256=sha(r/'confirm/chain_01/failure.json'),primary_completion_sha256=sha(r/'confirm/inputs_01/completion.json'),
 diagnosis_sha256=sha(r/'remaining_recovery_diagnosis_17.json'),deadline_unchanged=old['deadline'])))
'''.replace('__ROOT__', ROOT))
    save('fresh_remaining_recovery_resources_19.json', pre)
    directory = WORK/'improvement/recall_positive_fresh_recovery_v2'
    files = {}
    for path in directory.iterdir():
        if path.is_file() and path.suffix in ('.py','.md'):
            if path.suffix == '.py': ast.parse(path.read_text(encoding='utf8'))
            files['recovery_v2/code/'+path.name] = path.read_bytes()
    assert len([name for name in files if name.endswith('.py')]) == 12
    files['fresh_remaining_recovery_review_18.md'] = (REPORT/'fresh_remaining_recovery_review_18.md').read_bytes()
    manifest = {name: dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}
    files['manifest.json'] = json.dumps(dict(files=manifest),sort_keys=True).encode()
    bundle = REPORT/'fresh_remaining_recovery_control_19.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items(): archive.writestr(name,data)
    data = bundle.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    assert len(data) < 262144
    sent = subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        str(bundle),'aic-inspur-home:'+ROOT+'/incoming_remaining_recovery_19.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:
        raise RuntimeError('Transfer outcome unknown: inspect actual size/SHA before any further action. '+sent.stderr)
    value = remote(r'''
import ast,copy,datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
r=pathlib.Path('__ROOT__');main=r.parent;h=main.parent
assert socket.gethostname()=='inspur-NP5570M5'
assert not (r/'recovery_v2').exists() and not (r/'positive_fresh_recovery_registration_v2.json').exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bundle=r/'incoming_remaining_recovery_19.zip'
assert bundle.stat().st_size==__BYTES__ and sha(bundle)=='__SHA__'
with zipfile.ZipFile(bundle) as archive:
 assert len(archive.namelist())==len(set(archive.namelist())) and archive.testzip() is None
 manifest=json.loads(archive.read('manifest.json'))['files'];assert set(archive.namelist())==set(manifest)|{'manifest.json'}
 for name,row in manifest.items():
  path=pathlib.PurePosixPath(name);assert not path.is_absolute() and '..' not in path.parts
  assert not (r/name).exists(),'Never overwrite frozen original/deployed files'
  data=archive.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 for name in manifest:
  target=r/name;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as stream:stream.write(archive.read(name))
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'recovery_v2/code'))
import model_common as io
from fresh_registration import registration,media_files,first_remaining_launch,REGISTRATION_NAME
original=io.read(r/'positive_fresh_registration.json');reg=copy.deepcopy(original);required=reg['required_files']
def add(path,expected=None):
 path=pathlib.Path(path).resolve();assert path.is_relative_to(h) and path.is_file()
 actual=sha(path);assert expected is None or actual==expected
 assert str(path) not in required or required[str(path)]==actual,'Frozen original dependency changed'
 required[str(path)]=actual;return dict(path=str(path),sha256=actual)
for path in (r/'recovery_v2/code').glob('*.py'):ast.parse(path.read_text());add(path)
oldcode={str(path.resolve()):sha(path) for path in (r/'code').glob('*.py')};assert len(oldcode)==12
for name,digest in oldcode.items():add(name,digest)
refs=dict(original_registration_ref=add(r/'positive_fresh_registration.json'),original_chain_failure_ref=add(r/'confirm/chain_01/failure.json'),
 primary_completion_ref=add(r/'confirm/inputs_01/completion.json'),diagnosis_ref=add(r/'remaining_recovery_diagnosis_17.json'),
 source_clocks_ref=add(r/'confirm/source_clocks.json'),view_plan_ref=add(r/'confirm/view_plan.json'))
primary=io.read(refs['primary_completion_ref']['path']);closure=r/'confirm/inputs_01/implementation_closure.json'
add(closure,primary['implementation_closure_sha256'])
for name,digest in io.read(closure)['files'].items():add(name,digest)
for name,digest in io.read(refs['diagnosis_ref']['path'])['bindings'].items():add(name,digest)
add(r/'fresh_remaining_recovery_review_18.md')
reg.update(status='REGISTERED_POSITIVE_FIRST_FRESH_REMAINING_RECOVERY_V2',original_code_files=oldcode,**refs)
for budget in reg['gpu_budget'].values():budget['gpu_job_name']=budget['gpu_job_name'].removesuffix('_v1')+'_v2'
assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline'])
io.save(r/REGISTRATION_NAME,reg)
registration(r);_,reference=media_files(r,reg);first_remaining_launch(r,main,reg)
gpu=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert gpu and gpu[0].strip()=='0'
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'recovery_v2/code/fresh_chain.py'),'--root',str(r),'--positive-root',str(main)]
io.save(r/'remaining_recovery_claim_19.json',dict(utc=io.utc(),argv=argv,registration_ref=dict(path=str(r/REGISTRATION_NAME),sha256=sha(r/REGISTRATION_NAME)),
 original_failure_ref=refs['original_chain_failure_ref'],adopted_primary_completion_ref=refs['primary_completion_ref'],parent_CUDA=env['CUDA_VISIBLE_DEVICES']))
with (r/'remaining_recovery_19.log').open('xb') as log:parent=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(parent.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=io.utc(),host=socket.gethostname(),pid=parent.pid,start_ticks=stat[19],argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/REGISTRATION_NAME),
 original_registration_sha256=refs['original_registration_ref']['sha256'],adopted_primary_inputs=28,adopted_RGB_sources=4,
 first_input_QA_calls_at_launch=0,new_model_calls_at_launch=0,successful_primary_or_media_or_RGB_operations_repeated=0,
 deadline_unchanged=reg['deadline'],production_admitted=False,no_fixed40_426_or_package_started=True)
io.save(r/'remaining_recovery_launch_19.json',value);print(json.dumps(value))
'''.replace('__ROOT__',ROOT).replace('__BYTES__',str(len(data))).replace('__SHA__',digest))
    save('fresh_remaining_recovery_launch_19.json',value)
    print(json.dumps(value,ensure_ascii=False))


if __name__ == '__main__': main()
