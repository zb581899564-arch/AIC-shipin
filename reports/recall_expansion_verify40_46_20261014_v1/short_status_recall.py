"""One bounded read-only existing-SSH snapshot, never a launcher/watcher."""
import argparse
import json
from pathlib import Path
import subprocess

SCRIPT = r'''
import pathlib,json,datetime,socket
root=pathlib.Path('/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1')
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':socket.gethostname(),'actual_commands':[], 'stages':{},'calls':{},'terminal':None,'group_terminals':{}}
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  argv=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
  if not any(str(root) in arg for arg in argv):continue
  stat=(proc/'stat').read_text().split(') ',1)[1].split()
  result['actual_commands'].append({'pid':int(proc.name),'ppid':int(stat[1]),'state':stat[0],'start_ticks':stat[19],'argv':argv,'io':(proc/'io').read_text()})
 except (OSError,ValueError,IndexError):pass
for group in ['dev','confirm']:
 for stage in ['reference_03','inputs_01','inputs_02','inputs_03','input_admission_01','admission_02','admission_03','first_input_replay_recovery_02','B0/gpu_01','B0/replay_01','VERIFY/cpu_01','VERIFY/gpu_01','VERIFY/replay_01','comparison_01','chain_01','chain_02','chain_03','control_07']:
  folder=root/group/stage
  summary={}
  for name in ['completion.json','failure.json','result.json']:
   path=folder/name
   if path.exists():
    body=json.loads(path.read_text());summary[name]={k:body[k] for k in ['status','stage','group','calls','actual_input_count','expected_input_count','B0_calls','VERIFY_calls','error','macro','conditions','utc'] if k in body}
    if 'traceback' in body:summary[name]['traceback_tail']=body['traceback'][-1600:]
  if folder.exists():result['stages'][group+'/'+stage]=summary
  journal=folder/'attempts.jsonl'
  if journal.exists():
   rows=[json.loads(x) for x in journal.read_text().splitlines() if x.strip()]
   result['calls'][group+'/'+stage]={'BEGIN':sum(x['event']=='BEGIN' for x in rows),'ACCEPTED':sum(x['event']=='ACCEPTED' for x in rows)}
 result['stages'][group+'/CPU_proof_count']=sum(len(list((root/group/name).rglob('proof.json'))) for name in ['inputs_01','inputs_02','inputs_03'])
 chain=root/group/next((name for name in ['chain_03','chain_02','chain_01'] if (root/group/name).exists()),'chain_01')
 if (chain/'completion.json').exists():result['group_terminals'][group]=json.loads((chain/'completion.json').read_text())
 elif (chain/'failure.json').exists():result['group_terminals'][group]=json.loads((chain/'failure.json').read_text())
 control=root/group/'control_07/failure.json'
 if control.exists():result['group_terminals'][group]=json.loads(control.read_text())
result['active_group']='confirm' if (root/'confirm/control_07').exists() else 'dev'
result['terminal']=result['group_terminals'].get(result['active_group'])
active=root/result['active_group']
log_root=next((active/name for name in ['chain_03','chain_02','control_07','chain_01'] if (active/name).exists()),active)
logs=list(log_root.glob('*.log'))
result['latest_log_tail']={p.name:p.read_text(errors='replace')[-1000:] for p in sorted(logs,key=lambda p:p.stat().st_mtime)[-2:]}
print(json.dumps(result))
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--save',type=Path)
    parser.add_argument('--ssh-alias',choices=('aic-inspur-home','aic-inspur-tailscale'),default='aic-inspur-home')
    args=parser.parse_args()
    import base64
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(SCRIPT.encode()).decode()+'\'))"'
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',args.ssh_alias,command],
                          capture_output=True,text=True,timeout=35)
    if result.returncode:raise RuntimeError(result.stderr)
    value=json.loads(result.stdout)
    if args.save:
        with args.save.open('x',encoding='utf8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
    print(json.dumps(value,ensure_ascii=False))

if __name__=='__main__':main()
