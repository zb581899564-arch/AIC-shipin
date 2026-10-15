"""Read-only, bounded AIC storage/dependency audit through the existing SSH alias."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import datetime,json,os,pathlib,socket,subprocess
H=pathlib.Path('/home/inspur/aic_video_work')
C=H/'recall_consensus_verify40_46_20261015_v1'
T=H/'twenty_hour_five_20261014_v1'
assert socket.gethostname()=='inspur-NP5570M5'
v={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':socket.gethostname(),'disk':{},'trees':{},'registrations':{},'processes':[]}
s=os.statvfs(H);v['disk']={'total':s.f_blocks*s.f_frsize,'available':s.f_bavail*s.f_frsize}
for rel,depth in [('round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z',2),('gnmc_width_sft1000_iteration_20261013_v1',3),('gnmc_spatial_sft_iteration_20261013_v1',3),('gnmc_width_sft_iteration_20261013_v1',3),('human_reference_iteration_20261013_v1',2),('twenty_hour_five_20261014_v1/temporal_family_native_package_v3',2)]:
 p=H/rel
 if not p.exists():continue
 r=subprocess.run(['nice','-n','19','ionice','-c','3','du','-x','-B1',f'--max-depth={depth}',str(p)],text=True,capture_output=True,timeout=90)
 entries=[]
 for row in r.stdout.splitlines():
  size,path=row.split('\t',1)
  if int(size)>=50000000:entries.append({'bytes':int(size),'path':path})
 v['trees'][rel]={'exit':r.returncode,'largest':sorted(entries,key=lambda x:-x['bytes'])[:35],'stderr':r.stderr[-400:]}
for name in ['fresh_confirm_registration.json','fresh_recovery_registration_02.json']:
 p=C/name;d=json.loads(p.read_text());files=d.get('required_files',{})
 v['registrations'][name]={'required_files_count':len(files),'required_files_type':type(files).__name__,'keys':list(d),'required_path_sample':list(files)[:5]}
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  if not argv or not any('/home/inspur/aic_' in x for x in argv):continue
  if any('base64.b64decode' in x for x in argv):continue
  stat=(p/'stat').read_text().split(') ',1)[1].split()
  v['processes'].append({'pid':int(p.name),'ppid':int(stat[1]),'state':stat[0],'start_ticks':stat[19],'argv':argv,'cwd':os.readlink(p/'cwd')})
 except (OSError,IndexError,ValueError):pass
v['memory']=subprocess.run(['free','-b'],capture_output=True,text=True).stdout
v['gpu']=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout
print(json.dumps(v))
'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--save',type=Path,required=True);args=ap.parse_args()
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(REMOTE.encode()).decode()+'\'))"'
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],capture_output=True,text=True,timeout=180)
    if r.returncode:raise RuntimeError(r.stderr[-2000:])
    v=json.loads(r.stdout)
    with args.save.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
    print(json.dumps(v,ensure_ascii=False))


if __name__=='__main__':main()
