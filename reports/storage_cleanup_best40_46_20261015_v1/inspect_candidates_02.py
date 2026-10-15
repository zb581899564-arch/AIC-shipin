"""Inspect exact candidate payloads and live/best dependency pins; no deletion."""
import base64,json,subprocess
from pathlib import Path

CODE=r'''
import collections,datetime,json,os,pathlib,socket
H=pathlib.Path('/home/inspur/aic_video_work');C=H/'recall_consensus_verify40_46_20261015_v1';T=H/'twenty_hour_five_20261014_v1'
R=H/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
assert socket.gethostname()=='inspur-NP5570M5'
v={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_roots':{},'protected_registrations':{},'best_package_files':[]}
roots=[H/'gnmc_width_sft1000_iteration_20261013_v1',H/'gnmc_spatial_sft_iteration_20261013_v1',H/'gnmc_width_sft_iteration_20261013_v1',H/'human_reference_iteration_20261013_v1',R/'teacher32b_linux_download_v1']
for root in roots:
 if not root.exists():continue
 item={'top':[{'name':p.name,'kind':'dir' if p.is_dir() else 'file','size':p.stat().st_size} for p in root.iterdir()],'metadata':{},'payload_samples':{}}
 for pattern in ['*completion*.json','*failure*.json','chain*/completion.json','chain*/failure.json','*01/completion.json','*01/failure.json','*02/completion.json','*02/failure.json']:
  for p in root.glob(pattern):
   if not p.is_file() or p.stat().st_size>200000:continue
   try:
    d=json.loads(p.read_text());item['metadata'][str(p.relative_to(root))]={k:d[k] for k in ['status','stage','error','verdict','reason','quality','quality_pass','dev_pass','all_gates_pass','utc','actual_accepted_train','accepted_train'] if k in d}
   except (ValueError,OSError):pass
 for sub in ['tensors','rgb','rgb_02','assets']:
  p=root/sub
  if not p.exists():continue
  files=[x for x in p.rglob('*') if x.is_file()]
  types=collections.Counter(x.suffix for x in files)
  item['payload_samples'][sub]={'count':len(files),'extensions':dict(types),'largest':[{'path':str(x.relative_to(root)),'size':x.stat().st_size} for x in sorted(files,key=lambda x:-x.stat().st_size)[:5]],'symlinks':[str(x) for x in p.rglob('*') if x.is_symlink()]}
 v['candidate_roots'][str(root)]=item
for name in ['fresh_confirm_registration.json','fresh_recovery_registration_02.json']:
 d=json.loads((C/name).read_text());files=d.get('required_files',{});v['protected_registrations'][name]=files
for p in sorted((T/'temporal_family_native_package_v3/package_VERIFY').iterdir()):
 item={'path':str(p),'size':p.stat().st_size}
 if p.suffix=='.json' and p.stat().st_size<300000:
  item['json']=json.loads(p.read_text())
 v['best_package_files'].append(item)
print(json.dumps(v))
'''
cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(CODE.encode()).decode()+'\'))"'
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',cmd],capture_output=True,text=True,timeout=40)
if r.returncode:raise RuntimeError(r.stderr)
d=json.loads(r.stdout)
p=Path(__file__).with_name('candidate_dependencies_02.json')
with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
for key in ['utc','candidate_roots','best_package_files']:print(key,json.dumps(d[key],ensure_ascii=False))
for name,files in d['protected_registrations'].items():
 print(name,'candidate references',[p for p in files if any(k in p for k in ['gnmc_','human_reference','teacher32b_linux_download'])])
