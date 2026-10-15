"""Read actual argv/parent/IO/terminal evidence; never restart any stage."""
import json
import shlex
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/duration_guard_iteration_20261013_v1'
SCRIPT=r'''
import datetime,json,os,shutil,socket,subprocess
from pathlib import Path
b=Path('/home/inspur/aic_video_work/duration_guard_iteration_20261013_v1')
name='duration_guard_reserved5_original_b_native64_20261013_v1'
assert socket.gethostname()=='inspur-NP5570M5'
actual=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
  if not any(x.startswith(str(b)+'/code/') or x==name for x in args):continue
  status=(p/'status').read_text()
  env=(p/'environ').read_bytes().split(b'\0')
  cuda=[x.decode() for x in env if x.startswith(b'CUDA_VISIBLE_DEVICES=')]
  fds={f.name:os.readlink(f) for f in (p/'fd').iterdir()}
  actual.append(dict(pid=int(p.name),argv=args,ppid=int(next(s.split()[1] for s in status.splitlines() if s.startswith('PPid:'))),status=status,IO=(p/'io').read_text(),fds=fds,CUDA_VISIBLE_DEVICES=cuda))
 except OSError:continue
receipts={}
for rel in ('media_stage_completion.json','cpu_chain_01/state.json','cpu_chain_01/completion.json',
 'cpu_chain_01/failure.json','mapping_01/progress.json','mapping_01/completion.json','mapping_01/failure.json',
 'rgb_01/completion.json','rgb_01/failure.json','processor_01/completion.json','processor_01/failure.json',
 'native_input_acceptance.json','new5_chain_01/state.json','new5_chain_01/completion.json','new5_chain_01/failure.json',
 'new5_gpu_01/completion.json','new5_gpu_01/failure.json','new5_replay_01/completion.json','new5_replay_01/failure.json',
 'developer_export_acceptance.json'):
 if (b/rel).exists():receipts[rel]=json.loads((b/rel).read_text())
tails={}
for rel in ('cpu_chain_01/NATIVE_MAPPING.log','cpu_chain_01/NATIVE_RGB.log','cpu_chain_01/CPU_PROCESSOR.log',
 'cpu_chain_01.log','new5_chain_01.log','new5_chain_01/NEW5_B_GPU_WRAPPER.log','new5_chain_01/INDEPENDENT_CPU_REPLAY_EXPORT.log'):
 p=b/rel
 if p.exists():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-3200));tails[rel]=f.read().decode(errors='replace')
counts=dict(rgb_inputs=len(list((b/'rgb_01').glob('*/input.json'))),processor_proofs=len(list((b/'processor_01').glob('H*.json'))),model_done=len(list((b/'new5_gpu_01').glob('*/done.json'))),independent_replay=len(list((b/'new5_replay_01').glob('H*.json'))))
attempts=b/'new5_gpu_01/attempts.jsonl'
events=[json.loads(s) for s in attempts.read_text().splitlines() if s.strip()] if attempts.exists() else []
counts.update(model_begun=sum(e['event']=='BEGIN_MODEL_CALL' for e in events),model_accepted=sum(e['event']=='ACCEPTED_MODEL_CALL' for e in events))
resource_path=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller')/(name+'.resource.json')
resource=json.loads(resource_path.read_text()) if resource_path.exists() else None
ledger=[json.loads(s) for s in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s.strip() and json.loads(s)['name']==name]
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),actual=actual,receipts=receipts,tails=tails,counts=counts,resource=resource,matching_ledger=ledger,disk_free=shutil.disk_usage(b).free,gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True),memory_available=next(x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))))
'''

def main():
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
        '-o','ConnectTimeout=15','-o','ServerAliveInterval=15','aic-inspur-home',
        'python3 -c '+shlex.quote(SCRIPT)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=55)
    value=json.loads(result.stdout)
    index=1
    while (REPORT/f'new5_live_{index:02d}.json').exists():index+=1
    with (REPORT/f'new5_live_{index:02d}.json').open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False)
    print(json.dumps(dict(checkpoint=f'new5_live_{index:02d}.json',utc=value['utc'],
        actual=[{k:p[k] for k in ('pid','ppid','argv','CUDA_VISIBLE_DEVICES','IO')} for p in value['actual']],
        states={p:r for p,r in value['receipts'].items() if p.endswith('state.json') or p.endswith('failure.json')},
        counts=value['counts'],gpu=value['gpu'],resource=value['resource'],
        failure_tails=value['tails'] if any(p.endswith('failure.json') for p in value['receipts']) else {}),ensure_ascii=False))

if __name__=='__main__':main()
