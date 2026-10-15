from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1';PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
files={'finalization_code_v1/finalize.py':W/'improvement/midnight_finalization_v1/finalize.py'}
for p in files.values():ast.parse(p.read_text(encoding='utf8'))
archive=R/'finalization_control_15.zip';manifest={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for n,p in files.items():z.write(p,n)
    z.writestr('manifest.json',json.dumps(manifest))
size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-tailscale:'+ROOT+'/'+archive.name],check=True,capture_output=True)
code=f'''from pathlib import Path
import json,hashlib,zipfile,datetime as dt,os,subprocess
r=Path({ROOT!r});p=r/{archive.name!r};assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for n,d in m.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and hashlib.sha256(z.read(n)).hexdigest()==d
  f=r/n;f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as h:h.write(z.read(n))
record=dict(status='FROZEN_CPU_FINALIZER_DEPLOYED',code_files={{str(r/n):d for n,d in m.items()}},control_bytes={size},control_sha256={digest!r},UTC=dt.datetime.now(dt.timezone.utc).isoformat())
with (r/'finalization_deployment_15.json').open('x') as f:json.dump(record,f,indent=2)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
argv=[{PY!r},'-B',str(r/'finalization_code_v1/finalize.py'),'wait_risk']
with (r/'risk_finalization_15.log').open('x') as log:
 child=subprocess.Popen(argv,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch=dict(pid=child.pid,start_ticks=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],argv=argv,CPU_only=True,no_new_model_calls=True,wait_existing_natural_unique_production_then_only_three_risk_CPU_packages=True,UTC=dt.datetime.now(dt.timezone.utc).isoformat(),deployment=record)
with (r/'risk_finalization_launch_15.json').open('x') as f:json.dump(launch,f,indent=2)
print(json.dumps(launch))
'''
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-tailscale','python3','-'],input=code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-3000:])
with (R/'finalization_launch_15_result.json').open('x',encoding='utf8') as f:json.dump(dict(exit=res.returncode,stdout=res.stdout,stderr=res.stderr[-3000:]),f,indent=2)
res.check_returncode()
