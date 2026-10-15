"""Single bounded read-only snapshot of this independent fresh4 run."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

SCRIPT=r'''
import datetime,json,pathlib,socket
r=pathlib.Path('/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1')
assert socket.gethostname()=='inspur-NP5570M5'
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),actual_commands=[],stages={},calls={},terminal=None)
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  if not any(str(r) in x for x in argv):continue
  parts=(p/'stat').read_text().split(') ',1)[1].split()
  v['actual_commands'].append(dict(pid=int(p.name),ppid=int(parts[1]),state=parts[0],start_ticks=parts[19],argv=argv,io=(p/'io').read_text()))
 except (OSError,IndexError,ValueError):pass
for name in ['fresh_control_01','confirm/reference_01','confirm/inputs_01','confirm/inputs_02','confirm/admission_01','confirm/admission_02','confirm/chain_01','confirm/chain_02','confirm/B0/gpu_01','confirm/B0/replay_01','confirm/VERIFY/cpu_01','confirm/VERIFY/gpu_01','confirm/VERIFY/replay_01','confirm/comparison_01']:
 folder=r/name;data={}
 for item in ['completion.json','failure.json','result.json']:
  p=folder/item
  if p.exists():
   body=json.loads(p.read_text());data[item]={k:body[k] for k in ['status','stage','error','calls','actual_input_count','source_count','group','utc','conditions','macro'] if k in body}
   if 'traceback' in body:data[item]['traceback_tail']=body['traceback'][-1800:]
 if folder.exists():v['stages'][name]=data
 if name.endswith('reference_01') and folder.exists():v['accepted_reference_slots']=len(list(folder.glob('accepted_slot_*.json')))
 if name.endswith(('inputs_01','inputs_02')) and folder.exists():v['primary_proof_count']=len(list(folder.rglob('proof.json')))
 if name.endswith('replay_01') and folder.exists():v['stages'][name]['actual_case_proof_count']=len([p for p in folder.glob('*.json') if p.stem not in ['completion','failure','started','launch_claim']])
 journal=folder/'attempts.jsonl'
 if journal.exists():
  rows=[json.loads(x) for x in journal.read_text().splitlines() if x.strip()]
  v['calls'][name]={k:sum(x['event']==k for x in rows) for k in ['BEGIN','ACCEPTED']}
v['active_execution']='recovery_v2' if (r/'capacity_recovery_launch_08.json').exists() else 'first_v1'
for parent in (['confirm/chain_02'] if v['active_execution']=='recovery_v2' else ['fresh_control_01','confirm/chain_01']):
 for ending in ['completion.json','failure.json']:
  p=r/parent/ending
  if p.exists():v['terminal']=json.loads(p.read_text());break
 if v['terminal'] is not None:break
logs=([r/'capacity_recovery_08.log']+list((r/'confirm/chain_02').glob('*.log'))) if v['active_execution']=='recovery_v2' else ([r/'fresh_control_04.log']+list((r/'fresh_control_01').glob('*.log'))+list((r/'confirm/chain_01').glob('*.log')))
v['latest_log_tails']={p.name:p.read_text(errors='replace')[-1500:] for p in sorted((p for p in logs if p.exists()),key=lambda p:p.stat().st_mtime)[-2:]}
print(json.dumps(v))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--save',type=Path);a=p.parse_args()
    cmd='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(SCRIPT.encode()).decode()+'\'))"'
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',cmd],capture_output=True,text=True,timeout=35)
    if result.returncode:raise RuntimeError(result.stderr)
    v=json.loads(result.stdout)
    if a.save:
        with a.save.open('x',encoding='utf8') as s:json.dump(v,s,ensure_ascii=False,indent=2)
    print(json.dumps(v,ensure_ascii=False))


if __name__=='__main__':main()
