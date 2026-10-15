"""Exact allowlist cleanup, with a separate dependency/open-file preflight and immutable inventory."""
import argparse,base64,json,subprocess
from pathlib import Path

REMOTE=r'''
import datetime,hashlib,json,os,pathlib,socket,stat
H=pathlib.Path('/home/inspur/aic_video_work').resolve();C=H/'recall_consensus_verify40_46_20261015_v1'
T=H/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
A=H/'storage_cleanup_best40_46_20261015_v1'
assert socket.gethostname()=='inspur-NP5570M5'
TARGETS=[H/'gnmc_width_sft1000_iteration_20261013_v1/tensors',H/'gnmc_width_sft1000_iteration_20261013_v1/rgb',H/'gnmc_spatial_sft_iteration_20261013_v1/tensors',H/'gnmc_spatial_sft_iteration_20261013_v1/rgb',H/'gnmc_width_sft_iteration_20261013_v1/tensors',H/'human_reference_iteration_20261013_v1/rgb_02']
AUTH='如果linux容量不够那你把之前做的失败的方向的包都清理清理，只保留目前最高的包的数据就行，其他储存腾出来'
BASE=T/'package_VERIFY/candidate_TEMPORAL_VERIFY.zip'
BASESHA='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def stamp(p):
 s=p.lstat();return dict(device=s.st_dev,inode=s.st_ino,size=s.st_size,blocks_bytes=s.st_blocks*512,mtime_ns=s.st_mtime_ns,nlink=s.st_nlink)
def within(p,q):return p==q or q in p.parents
def assert_targets():
 for p in TARGETS:
  assert p.is_absolute() and p.resolve()==p and p!=H and within(p,H) and not within(p,C),str(p)
  assert p.is_dir() and not p.is_symlink(),str(p)
def active_conflicts():
 conflicts=[];checked=0;inaccessible=0
 for proc in pathlib.Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  try:
   uid=proc.stat().st_uid
   argv=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
   if any('base64.b64decode' in x for x in argv):continue
   paths=[]
   for a in argv:
    if a.startswith('/'):paths.append(('argv',a))
   try:paths.append(('cwd',os.readlink(proc/'cwd')))
   except OSError:pass
   try:
    for fd in (proc/'fd').iterdir():
     try:paths.append(('fd',os.readlink(fd).removesuffix(' (deleted)')))
     except OSError:pass
   except OSError:pass
   try:
    for line in (proc/'maps').read_text().splitlines():
     parts=line.split(None,5)
     if len(parts)==6 and parts[5].startswith('/'):paths.append(('mmap',parts[5].removesuffix(' (deleted)')))
   except OSError:pass
   checked+=1
   for kind,value in paths:
    for target in TARGETS:
     if within(pathlib.Path(value),target):conflicts.append(dict(pid=int(proc.name),kind=kind,path=value,argv=argv))
  except OSError:
   inaccessible+=1
 return dict(conflicts=conflicts,processes_checked=checked,inaccessible_processes=inaccessible)
def protected():
 result={};refs=set()
 def walk(v):
  if isinstance(v,str) and v.startswith('/'):refs.add(v)
  elif isinstance(v,dict):
   for k,x in v.items():
    if isinstance(k,str) and k.startswith('/'):refs.add(k)
    walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 for p in [C/'fresh_confirm_registration.json',C/'fresh_recovery_registration_02.json',T/'source_package_lock.json',T/'package_inputs.json']:
  assert p.is_file(),str(p);result[str(p)]=sha(p);walk(json.loads(p.read_text()))
 assert sha(BASE)==BASESHA,'Best package identity changed';result[str(BASE)]=BASESHA
 hits={str(t):sorted(x for x in refs if within(pathlib.Path(x),t)) for t in TARGETS}
 return result,hits
assert_targets()
if MODE=='plan':
 pins,hits=protected();running=active_conflicts();assert not running['conflicts'],running['conflicts']
 entries=[];excluded=[];metadata=[]
 for target in TARGETS:
  if hits[str(target)]:excluded.append(dict(path=str(target),reason='BEST_OR_LIVE_DIRECT_LOCK_REFERENCE',references=hits[str(target)]));continue
  for p in sorted(target.rglob('*')):
   assert not p.is_symlink(),str(p)
   if not p.is_file():continue
   assert p.resolve()==p and within(p,target)
   if p.suffix.lower() not in {'.pt','.npy','.npz','.png','.jpg','.jpeg','.bin','.zst','.gz'}:
    metadata.append(str(p));continue
   s=stamp(p)
   assert stat.S_ISREG(p.lstat().st_mode) and s['nlink']==1,'Unexpected shared hardlink '+str(p)
   entries.append(dict(path=str(p),**s))
 A.mkdir(exist_ok=True)
 before=os.statvfs(H).f_bavail*os.statvfs(H).f_frsize
 plan=dict(schema='USER_AUTHORIZED_FAILED_CACHE_PURGE_V1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),user_authorization_verbatim=AUTH,targets=[str(x) for x in TARGETS],protected_small_file_sha256=pins,excluded=excluded,open_file_preflight=running,entries=entries,metadata_preserved=metadata,files=len(entries),allocated_bytes=sum(x['blocks_bytes'] for x in entries),logical_bytes=sum(x['size'] for x in entries),available_before=before,scope='Only obsolete failed-GNMC and rejected-A/B/C binary RGB/tensor cache payloads; no original media/models/live/best data',historical_failed_quality_or_fees_rewritten=False,old_cache_replay_will_be_unavailable=True)
 save(A/'deletion_plan_03.json',plan)
 print(json.dumps({k:v for k,v in plan.items() if k not in ['entries','metadata_preserved','protected_small_file_sha256']}|dict(plan_sha256=sha(A/'deletion_plan_03.json'),metadata_preserved_count=len(metadata))))
elif MODE=='apply':
 p=A/'deletion_plan_03.json';assert sha(p)==EXPECTED
 plan=json.loads(p.read_text());assert not (A/'deletion_completion_04.json').exists()
 pins,hits=protected();assert pins==plan['protected_small_file_sha256']
 running=active_conflicts();assert not running['conflicts'],running['conflicts']
 for entry in plan['entries']:
  p=pathlib.Path(entry['path']);assert any(within(p,t) for t in TARGETS) and p.resolve()==p and not p.is_symlink()
  assert stamp(p)=={k:entry[k] for k in ['device','inode','size','blocks_bytes','mtime_ns','nlink']},str(p)
 save(A/'deletion_started_04.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=EXPECTED,files=plan['files']))
 deleted=[]
 try:
  for entry in plan['entries']:
   p=pathlib.Path(entry['path']);p.unlink();deleted.append(entry['path'])
  after=os.statvfs(H).f_bavail*os.statvfs(H).f_frsize
  assert all(not pathlib.Path(p).exists() for p in deleted)
  pins2,_=protected();assert pins2==pins
  receipt=dict(status='COMPLETED_USER_AUTHORIZED_FAILED_CACHE_PURGE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=EXPECTED,deleted_files=len(deleted),deleted_logical_bytes=plan['logical_bytes'],deleted_allocated_bytes=plan['allocated_bytes'],available_before=plan['available_before'],available_after=after,available_delta=after-plan['available_before'],best_zip_sha256=BASESHA,best_and_live_metadata_unchanged=True,original_media_models_environments_live_task_deleted=False,process_signals_sent=0,excluded=plan['excluded'],old_results_and_fees_unchanged=True,old_deleted_binary_cache_replay_available=False)
  save(A/'deletion_completion_04.json',receipt);print(json.dumps(receipt))
 except BaseException as e:
  save(A/'deletion_failure_04.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),error=repr(e),deleted_files=deleted,plan_sha256=EXPECTED));raise
else:raise ValueError(MODE)
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['plan','apply']);p.add_argument('--plan-sha',default='');p.add_argument('--save',type=Path,required=True);a=p.parse_args()
    code='MODE='+repr(a.mode)+'\nEXPECTED='+repr(a.plan_sha)+'\n'+REMOTE
    cmd='nice -n 19 ionice -c 3 python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(code.encode()).decode()+'\'))"'
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',cmd],capture_output=True,text=True,timeout=120)
    if r.returncode:raise RuntimeError(r.stderr[-2500:])
    d=json.loads(r.stdout)
    with a.save.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
    print(json.dumps(d,ensure_ascii=False))

if __name__=='__main__':main()
