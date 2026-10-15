"""One small-code deployment and first new CPU-only consensus comparison."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

REPORT = Path(__file__).resolve().parent
WORK = REPORT.parents[1]
NEW = '/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1'
OLD = '/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1'
INCOMING = '/home/inspur/aic_video_work/incoming_recall_consensus_control_01.zip'


def remote(script, seconds=45):
    command = 'python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(script.encode()).decode()+'\'))"'
    p = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],
                       capture_output=True,text=True,timeout=seconds)
    if p.returncode:
        raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)


def main():
    snapshot = remote(r'''
import datetime,json,os,pathlib,shutil,socket,subprocess
n=pathlib.Path('__NEW__');incoming=pathlib.Path('__INCOMING__')
assert socket.gethostname()=='inspur-NP5570M5'
assert not n.exists() and not incoming.exists(),'Existing new root/bundle requires explicit inspection, never overwrite/restart'
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),
 cpu_count=os.cpu_count(),load=list(os.getloadavg()),memory=pathlib.Path('/proc/meminfo').read_text(),
 disk=list(shutil.disk_usage(n.parent)),active_commands=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:16],
 GPU=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 planned_operation='First new pure CPU comparison of8 previously exposed external sources;0 new model/decode/processor;small code only')))
'''.replace('__NEW__',NEW).replace('__INCOMING__',INCOMING))
    (REPORT/'resources_before_development_01.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    files = {'code/'+p.name:p.read_bytes() for p in (WORK/'improvement/recall_consensus_verify40_46_v1').glob('*.py')}
    for name in ('protocol.json','USER_AUTHORIZATION.json','official_rule_check_01.json'):
        files[name]=(REPORT/name).read_bytes()
    dependencies={OLD+'/code/'+name:hashlib.sha256((WORK/'improvement/recall_expansion_verify40_46_v1'/name).read_bytes()).hexdigest()
                  for name in ('stage_io.py','evaluate_pilot.py')}
    manifest=dict(files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()},
                  adopted_readonly_dependencies=dependencies)
    files['deployment_manifest.json']=json.dumps(manifest,ensure_ascii=False,sort_keys=True).encode()
    bundle=REPORT/'control_01.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert len(data)<65536
    p=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=12',str(bundle),'aic-inspur-home:'+INCOMING],capture_output=True,text=True,timeout=60)
    if p.returncode:raise RuntimeError('Inspect remote bundle before any explicit remaining transfer: '+p.stderr)
    result=remote(r'''
import base64,datetime,hashlib,json,os,pathlib,socket,subprocess,zipfile
assert socket.gethostname()=='inspur-NP5570M5'
n=pathlib.Path('__NEW__');o=pathlib.Path('__OLD__');p=pathlib.Path('__INCOMING__')
assert not n.exists() and p.stat().st_size==__SIZE__ and hashlib.sha256(p.read_bytes()).hexdigest()=='__SHA__'
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 m=json.loads(z.read('deployment_manifest.json'))
 assert set(z.namelist())==set(m['files'])|{'deployment_manifest.json'}
 for name,row in m['files'].items():
  key=pathlib.PurePosixPath(name);assert not key.is_absolute() and '..' not in key.parts
  b=z.read(name);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 for name,sha in m['adopted_readonly_dependencies'].items():assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==sha
 n.mkdir();z.extractall(n)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
python='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
args=[python,'-B',str(n/'code/evaluate_development.py'),'--root',str(n),'--old-root',str(o)]
with (n/'development_controller.log').open('xb') as log:run=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
result_path=n/'development_01/result.json'
if not result_path.exists():raise RuntimeError('Real new comparison failed; preserve new root/log and old successes; no automatic rerun')
result=json.loads(result_path.read_text());assert run.returncode in (0,5)
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),root=str(n),argv=args,CPU_only=True,
 bundle_bytes=__SIZE__,bundle_sha256='__SHA__',CRC_member_SHA_passed=True,exit_code=run.returncode,
 result=result,result_path=str(result_path),result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
 new_model_calls=0,old_success_repeated=0,production_admitted=False)
payload=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
with (n/'development_controller_completion.json').open('xb') as s:s.write(payload)
print(json.dumps(dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=base64.b64encode(payload).decode())))
'''.replace('__NEW__',NEW).replace('__OLD__',OLD).replace('__INCOMING__',INCOMING).replace('__SIZE__',str(len(data))).replace('__SHA__',digest),seconds=60)
    payload=base64.b64decode(result['base64'],validate=True)
    assert len(payload)==result['bytes'] and hashlib.sha256(payload).hexdigest()==result['sha256']
    with (REPORT/'development_receipt_01.json').open('xb') as f:f.write(payload)
    result=json.loads(payload)
    print(json.dumps(dict(status=result['result']['status'],macro=result['result']['macro'],conditions=result['result']['conditions'],
        cases=[dict(video_id=c['video_id'],F1_delta_exact=c['F1_delta_exact'],added_native_frames=c['added_native_frames']) for c in result['result']['cases']],
        new_model_calls=0,bundle_bytes=len(data)),ensure_ascii=False))


if __name__=='__main__':main()
