"""Bounded read-only facts status, or the first CPU-only veto after complete actual execution."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import datetime,hashlib,json,os,pathlib,socket,subprocess
root=pathlib.Path('/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1/fixed40_01')
assert socket.gethostname()=='inspur-NP5570M5'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),root_exists=root.exists(),stages={},calls={},actual_commands=[],terminal=None)
if MODE=='veto':
 complete=root/'facts/chain_01/completion.json'
 assert complete.is_file() and not (complete.parent/'failure.json').exists(),'Complete natural facts chain required'
 d=read(complete);assert d['status']=='PASS_FIXED40_EXECUTION_AND_FIRST_QA_PENDING_FACT_VETO'
 assert d['execution_receipt_ref']==ref(root/'execution_export_01/execution_receipt.json')
 assert d['first_independent_qa_ref']==ref(root/'execution_export_01/first_independent_qa.json')
 assert not (root/'fact_veto_01').exists(),'Existing veto output requires inspection; no repeat'
 preflight=dict(utc=v['utc'],host=socket.gethostname(),memory=pathlib.Path('/proc/meminfo').read_text(),disk_available_bytes=os.statvfs(root).f_bavail*os.statvfs(root).f_frsize,
  actual_tasks=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,pmem,args','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:20],
  GPU=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout,
  execution_kind='CPU metadata/actual completed evidence check only; no training, tensor encoding, media decoding or model')
 with (root/'fact_veto_resource_preflight_16.json').open('x',encoding='utf-8') as f:json.dump(preflight,f,ensure_ascii=False,indent=2)
 argv=['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B',str(root/'code/facts_veto.py'),'--root',str(root),'--output',str(root/'fact_veto_01/result.json')]
 claim=root/'fact_veto_claim_16.json'
 with claim.open('x',encoding='utf-8') as f:json.dump(dict(utc=v['utc'],argv=argv,actual_chain_completion_ref=ref(complete),CPU_only=True,repeated_first_QA=False),f)
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
 with (root/'fact_veto_16.log').open('xb') as log:
  result=subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert result.returncode==0,'Actual first veto failed; preserve claim/log and inspect explicitly'
 p=root/'fact_veto_01/result.json';d=read(p)
 assert d['status'] in ['PASS_KNOWN_ORDINARY_SUFFICIENT_CONDITION_NOT_QUALITY','INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE']
 payload=(json.dumps(dict(schema='CONSENSUS_FIXED40_ACTUAL_VETO_RECEIPT_V1',utc=v['utc'],result_ref=ref(p),result=d,chain_completion_ref=ref(complete),production_admitted=False),ensure_ascii=False,indent=2)+'\n').encode()
 print(json.dumps(dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=__import__('base64').b64encode(payload).decode())))
else:
 for name in ['facts/chain_01','inputs_01','admission_01','facts/B0/gpu_01','facts/B0/replay_01','facts/VERIFY/cpu_01','facts/VERIFY/gpu_01','facts/VERIFY/replay_01','execution_export_01','fact_veto_01']:
  folder=root/name;values={}
  for filename in ['completion.json','failure.json','result.json','execution_receipt.json']:
   p=folder/filename
   if p.exists():
    body=read(p);values[filename]={k:body[k] for k in ['status','stage','error','calls','source_count','actual_input_count','expected_input_count','group','utc','conditions','touched_ordinary_observations','B0_actual_model_calls','VERIFY_actual_model_calls'] if k in body}
    if name=='facts/chain_01':v['terminal']=values[filename]
  if folder.exists():v['stages'][name]=values
  if name=='inputs_01' and folder.exists():v['first_primary_CPU_proofs']=len(list(folder.rglob('proof.json')))
  p=folder/'attempts.jsonl'
  if p.exists():
   rows=[json.loads(line) for line in p.read_text().splitlines() if line.strip()]
   v['calls'][name]={event:sum(row['event']==event for row in rows) for event in ['BEGIN','ACCEPTED']}
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   argv=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
   if any('base64.b64decode' in x for x in argv) or not any(str(root) in x for x in argv):continue
   fields=(p/'stat').read_text().split(') ',1)[1].split()
   v['actual_commands'].append(dict(pid=int(p.name),ppid=int(fields[1]),state=fields[0],start_ticks=fields[19],argv=argv,io=(p/'io').read_text()))
  except (OSError,IndexError,ValueError):pass
 print(json.dumps(v))
'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['status','veto']);ap.add_argument('--save',type=Path);a=ap.parse_args()
    if a.mode=='veto' and (a.save is None or a.save.exists()):raise ValueError('First veto requires a new local receipt filename')
    code='MODE='+repr(a.mode)+'\n'+REMOTE
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(code.encode()).decode()+'\'))"'
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],capture_output=True,text=True,timeout=90 if a.mode=='veto' else 35)
    if r.returncode:raise RuntimeError(r.stderr[-2000:])
    value=json.loads(r.stdout)
    if a.mode=='veto':
        payload=base64.b64decode(value['base64'],validate=True)
        assert len(payload)==value['bytes'] and hashlib.sha256(payload).hexdigest()==value['sha256']
        with a.save.open('xb') as f:f.write(payload)
        d=json.loads(payload);print(json.dumps(dict(status=d['result']['status'],conditions=d['result']['conditions'],touched_ordinary_observations=d['result']['touched_ordinary_observations'],receipt_bytes=len(payload),receipt_sha256=value['sha256']),ensure_ascii=False))
    else:
        if a.save:
            with a.save.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
        print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':main()
