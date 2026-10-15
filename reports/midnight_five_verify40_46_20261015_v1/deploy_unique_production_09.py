from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1';PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
files={'production_code_v3/'+p.name:p for p in (W/'improvement/midnight_production_unique_v3').glob('*.py')}
for p in files.values():ast.parse(p.read_text(encoding='utf8'))
manifest={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}
archive=R/'unique_production_control_09.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for n,p in files.items():z.write(p,n)
    z.writestr('manifest.json',json.dumps(manifest))
size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-home:'+ROOT+'/'+archive.name],check=True,capture_output=True)
code=f'''from pathlib import Path
import json,zipfile,hashlib,subprocess,os,sys,socket,datetime as dt
r=Path({ROOT!r});home=r.parent
assert socket.gethostname()=='inspur-NP5570M5'
probe=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True,check=True)
print('GPU',probe.stdout.strip())
print('MEM',next(v for v in Path('/proc/meminfo').read_text().splitlines() if v.startswith('MemAvailable:')))
st=os.statvfs(r);print('DISK_AVAILABLE',st.f_bavail*st.f_frsize)
print('CURRENT_GPU_COMPUTE',subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip())
ledger=[json.loads(v) for v in (home/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if v.strip()]
assert not any(v['name'] in ('midnight_three_semantic_recall_rank_aux519_20261015_v1','midnight_three_semantic_recall_rank_aux518_20261015_v1') for v in ledger)
assert not (r/'production/gpu_01').exists() and not (r/'production/chain_started.json').exists()
active=home/'improvement_round1/active_gpu_job.json'
if active.exists():
 v=json.loads(active.read_text());print('ACTIVE',json.dumps(v));assert v.get('status') in ('completed','failed','timeout','cancelled'),'Another owned GPU reservation must finish first'
p=r/{archive.name!r};assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for n,d in m.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and hashlib.sha256(z.read(n)).hexdigest()==d
  f=r/n;f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as h:h.write(z.read(n))
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
sys.path.insert(0,str(r/'production_code_v3'))
from alias_contract import semantic,accepted_cpu
cpu_path=r/'production/cpu_01/completion.json';c=json.loads(cpu_path.read_text());assert c['actual_count']==519
groups={{}};aliases=[]
for row in c['entries']:
 q=json.loads(Path(row['input_ref']['path']).read_text());key=json.dumps([q['retarget']['full_tensor_signature'],len(q['candidate_events'])],sort_keys=True,separators=(',',':'))
 if key in groups:
  canonical,previous=groups[key];assert semantic(q)==semantic(previous)
  aliases.append(dict(alias_case_id=q['case_id'],canonical_case_id=previous['case_id'],alias_input_ref=row['input_ref'],canonical_input_ref=canonical['input_ref'],input_signature=q['retarget']['full_tensor_signature'],candidate_count=len(q['candidate_events']),native_identity_equal=True,candidate_semantics_equal=True))
 else:groups[key]=(row,q)
assert len(groups)==518 and len(aliases)==1
stage=r/'production_unique_09';stage.mkdir(exist_ok=False)
table=dict(schema='PRE_GPU_IDENTICAL_NEW_INPUT_ALIAS_TABLE_V1',logical_count=519,model_count=518,registered_before_GPU=True,actual_parameters=8782459120,generation=dict(do_sample=False,max_new_tokens=192,model_role='BASE_ONLY'),cpu_completion_ref=ref(cpu_path),aliases=aliases,registered_UTC=dt.datetime.now(dt.timezone.utc).isoformat())
with (stage/'identical_input_alias_table.json').open('x') as f:json.dump(table,f,indent=2)
old=json.loads((r/'production/registration.json').read_text())
reg=dict(old,schema='ADOPT_COMPLETED_519_CPU_NEW_UNIQUE_518_GPU_V1',stage='production_unique_09',code_files={{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'production_code_v3').glob('*.py')}},gpu_job_name='midnight_three_semantic_recall_rank_aux518_20261015_v1',adopted_CPU_completion_ref=ref(cpu_path),original_CPU_registration_ref=ref(r/'production/registration.json'),identical_input_alias_table_ref=ref(stage/'identical_input_alias_table.json'),expected_actual_model_calls=518,logical_count=519,new_CPU_preparations=0,new_vision_encodes=0,alias_application_requires_independent_native_QA=True,registered_UTC=table['registered_UTC'])
with (stage/'registration.json').open('x') as f:json.dump(reg,f,indent=2)
accepted_cpu(reg)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
argv=[{PY!r},'-B',str(r/'production_code_v3/controller.py'),'--stage','production_unique_09']
with (stage/'controller.log').open('x') as log:
 child=subprocess.Popen(argv,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch=dict(pid=child.pid,start_ticks=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],argv=argv,parent_CUDA='0',registration_ref=ref(stage/'registration.json'),control_bytes={size},control_sha256={digest!r},unique_new_model_calls=518,adopted_identical_input_aliases=1,CPU_QA_adopted=519,UTC=dt.datetime.now(dt.timezone.utc).isoformat())
with (r/'production_unique_launch_09.json').open('x') as f:json.dump(launch,f,indent=2)
print(json.dumps(launch))
'''
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home','python3','-'],input=code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-3000:]);res.check_returncode()
with (R/'production_unique_launch_09.json').open('x',encoding='utf8') as f:json.dump(dict(control_bytes=size,control_sha256=digest,stdout=res.stdout),f,indent=2)
