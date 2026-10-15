"""Return only small submission ZIP and accepted receipts through Mac."""
import base64,hashlib,json,subprocess,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R='/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2/contest_v1'
names=['completion.json','state.json','started.json','launch.json','aic_ANNSEL10_nontest_01.resource.json','aic_ANNSEL10_rematch_01.resource.json']
for scope in ('nontest','rematch'):
    names += [scope+'_01/'+n for n in ('prepared.json','generation.json','cpu_replay.json','package_receipt.json','independent_validation.json')]
names+=['rematch_01/candidate_IMAGE_SCORE_237STEP_8B.zip']
code=f'''from pathlib import Path
import base64,hashlib,json,zipfile,sys,inspect
r=Path({R!r});assert json.loads((r/'state.json').read_text())['stage']=='COMPLETE_ZIP_READY_FOR_INDEPENDENT_FINAL_ACCEPTANCE'
owned=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:cmd=proc.joinpath('cmdline').read_bytes().decode(errors='replace').split('\\x00')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if any(str(r.parent/name) in cmd for name in ('contest_controller_v1.py','contest_engine.py')):owned.append(int(proc.name))
assert not owned,owned
sys.path.insert(0,str(r.parent));import contest_engine as engine
assert Path(engine.sc.__file__).resolve()==(r.parent/'selector_contract.py').resolve()
assert Path(inspect.getfile(engine.Constraint)).resolve()==(r.parent/'score_grammar.py').resolve()
assert Path(engine.c.__file__).resolve()==(engine.B4/'common.py').resolve()
ledger=[json.loads(s) for s in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
for scope in ('nontest','rematch'):
 d=r/(scope+'_01');receipt=json.loads((d/'package_receipt.json').read_text());independent=json.loads((d/'independent_validation.json').read_text())
 assert receipt['videos']==(8 if scope=='nontest' else 426) and all(independent['checks'].values()) and len(independent['checks'])==11
 p=Path(receipt['candidate']);assert hashlib.sha256(p.read_bytes()).hexdigest()==receipt['zip_sha256']==independent['zip_sha256']
 assert p.stat().st_size==receipt['zip_bytes']
 with zipfile.ZipFile(p) as z:assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
 g=json.loads((d/'generation.json').read_text());replay=json.loads((d/'cpu_replay.json').read_text())
 assert hashlib.sha256((d/'raw.jsonl').read_bytes()).hexdigest()==g['raw_sha256']==replay['raw_sha256']
 resource=json.loads((r/('aic_ANNSEL10_'+scope+'_01.resource.json')).read_text());assert resource['status']=='completed' and resource['exit_code']==0
 matches=[v for v in ledger if v['name']==resource['name']];assert len(matches)==1 and matches[0]==resource
result={{}}
for n in {names!r}:
 raw=(r/n).read_bytes();result[n]={{'base64':base64.b64encode(raw).decode(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}}
assert sum(v['bytes'] for v in result.values())<4_000_000
print(json.dumps(result))
'''
result=subprocess.run(['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=20','aic-inspur-home','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B','-'],input=code,text=True,capture_output=True)
if result.returncode:raise RuntimeError(result.stderr+result.stdout)
files=json.loads(result.stdout);dest=H/'contest_results';dest.mkdir(exist_ok=True)
for name,item in files.items():
    raw=base64.b64decode(item['base64']);assert hashlib.sha256(raw).hexdigest()==item['sha256'];p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==raw
    else:
        with p.open('xb') as f:f.write(raw)
with (H/'contest_transfer.json').open('x') as f:json.dump({'route':'LIVE_MACMINI_PROXYJUMP','raw_bytes':sum(v['bytes'] for v in files.values()),'files':{n:{k:i[k] for k in ('bytes','sha256')} for n,i in files.items()}},f,indent=2)
print(json.dumps({'files':len(files),'bytes':sum(v['bytes'] for v in files.values())}))
