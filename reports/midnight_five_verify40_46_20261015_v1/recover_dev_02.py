"""Explicit namespace recovery: old chain failed before its first input/QA/model."""
from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
WORK=Path(__file__).resolve().parents[2];REP=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1';PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home']
files={}
for f in (WORK/'improvement/midnight_five_runtime_v1').glob('*.py'):
 ast.parse(f.read_text(encoding='utf8'));files['code_v2/'+f.name]=f
for f in (WORK/'improvement/midnight_five_reference_v1').glob('*.py'):
 ast.parse(f.read_text(encoding='utf8'));files['reference_code_v2/'+f.name]=f
m={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in files.items()};p=REP/'remaining_recovery_control_02.zip'
with zipfile.ZipFile(p,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for name,f in files.items():z.write(f,name)
 z.writestr('manifest.json',json.dumps(m))
size=p.stat().st_size;sha=hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(p),'aic-inspur-home:'+ROOT+'/'+p.name],check=True,capture_output=True)
code=f'''from pathlib import Path
import zipfile,hashlib,json,os,subprocess
r=Path({ROOT!r});old=r/'dev';p=r/{p.name!r}
assert (old/'chain_failure.json').exists() and not (old/'gpu_01').exists() and not list((old/'cpu_01').glob('*/input.json'))
assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={sha!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for name,d in m.items():
  assert '..' not in Path(name).parts and not Path(name).is_absolute() and hashlib.sha256(z.read(name)).hexdigest()==d
  f=r/name;f.parent.mkdir(exist_ok=True)
  with f.open('xb') as h:h.write(z.read(name))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
probe='import sys;sys.path.insert(0,'+repr(str(r/'code_v2'))+');import mf_common; mf_common.library();print("IMPORT_NAMESPACE_PASS_NO_MODEL_OR_INPUT_QA")'
subprocess.run([{PY!r},'-B','-c',probe],env=env,check=True)
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
d=r/'dev_recovery_02';d.mkdir()
reg=json.loads((old/'registration.json').read_text());reg.update(stage=d.name,code_files={{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'code_v2').glob('*.py')}},explicit_recovery_from_failure_ref=ref(old/'chain_failure.json'),prior_model_calls=0,prior_successful_new_QA=0,prior_media_vision_cache_repeated=False)
(d/'registration.json').write_text(json.dumps(reg,indent=2))
(r/'recovery_acceptance_02.json').write_text(json.dumps(dict(bytes={size},sha256={sha!r},status='PASS_REMAINING_NAMESPACE_RECOVERY_SIZE_SHA_CRC_MEMBER_SHA',old_failure_ref=ref(old/'prepare_failure.json'),prior_model_calls=0,prior_successful_new_inputs=0)))
env['CUDA_VISIBLE_DEVICES']='0'
with (d/'parent.log').open('x') as log:
 child=subprocess.Popen([{PY!r},'-B',str(r/'code_v2/controller.py'),'--stage',d.name],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch=dict(pid=child.pid,start_ticks=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],argv=[{PY!r},'-B',str(r/'code_v2/controller.py'),'--stage',d.name],registration_ref=ref(d/'registration.json'),CUDA='0')
(r/'dev_recovery_launch_02.json').write_text(json.dumps(launch,indent=2));print(json.dumps(launch))
'''
res=subprocess.run(SSH+['python3','-'],input=code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-2400:] if res.returncode else '');res.check_returncode()
with (REP/'remaining_recovery_launch_02.json').open('x',encoding='utf8') as f:json.dump(dict(bytes=size,sha256=sha,remote_output=res.stdout),f,indent=2)
