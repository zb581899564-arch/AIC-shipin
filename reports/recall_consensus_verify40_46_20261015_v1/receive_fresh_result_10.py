"""Receive only a natural fresh confirmation terminal and small bound results."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

SCRIPT=r'''
import base64,hashlib,json,pathlib,socket,sys
r=pathlib.Path('/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1')
assert socket.gethostname()=='inspur-NP5570M5'
sys.dont_write_bytecode=True;sys.path.insert(0,str(r/'recovery_v2/code'))
import model_common as io
chain_path=r/'confirm/chain_02/completion.json';chain=io.read(chain_path)
assert chain['status'] in ['PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40','STOP_CONSENSUS_FRESH_CONFIRM_REJECTED']
p=r/'confirm/comparison_01/result.json';result=io.read(p)
assert chain['comparison_ref']==dict(path=str(p),sha256=io.sha(p)) and result['status']==chain['status'] and len(result['cases'])==4
assert result['bindings']['protocol_sha256']==io.PROTOCOL_SHA and result['bindings']['registration_sha256']==io.sha(r/'fresh_recovery_registration_02.json')
assert result['bindings']['original_registration_sha256']==io.sha(r/'fresh_confirm_registration.json')
stages={}
for name in ['B0','VERIFY']:
 gate_path=io.gpu_admission_path(r,name)
 if name=='VERIFY' and chain[name]['calls']==0:
  assert not gate_path.exists();stages[name]=dict(calls=0,GPU_started=False,first_QA_not_applicable=True);continue
 gate=io.read(gate_path);resource,resource_sha=io.terminal(gate)
 gpu=r/'confirm'/name/'gpu_01';qa_path=r/'confirm'/name/'replay_01/completion.json';qa=io.read(qa_path)
 io.completed_job(gpu,gate,gate_path,gate['expected_input_count'],name)
 n=gate['expected_input_count']
 assert qa['status']=='PASS_ALL_RECALL_'+name+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and qa['calls']==len(qa['proofs'])==n
 assert qa['CPU_only'] is True and qa['CUDA_initialized'] is False and qa['gpu_completion_sha256']==io.sha(gpu/'completion.json')
 assert qa['resource_terminal_sha256']==resource_sha
 stages[name]=dict(calls=n,first_independent_QA_proofs=n,resource_status=resource['status'],exit_code=resource['exit_code'],
  charged_seconds=resource['charged_seconds'],sampled_peak_memory_mib=resource['sampled_peak_memory_mib'],
  model_parameters=io.MODEL_PARAMETERS,unique_resource_ref=dict(path=str(io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json')),sha256=resource_sha),
  first_QA_ref=dict(path=str(qa_path),sha256=io.sha(qa_path)))
value=dict(schema='CONSENSUS_FRESH4_COMPLETED_RESULT_RECEIPT_V2',utc=io.utc(),chain_completion_ref=dict(path=str(chain_path),sha256=io.sha(chain_path)),
 result_ref=dict(path=str(p),sha256=io.sha(p)),result=result,stages=stages,total_actual_model_calls=sum(x['calls'] for x in stages.values()),
 total_GPU_charged_seconds=sum(x.get('charged_seconds',0) for x in stages.values()),actual_model_parameters=io.MODEL_PARAMETERS,optimizer_updates=0,
 production_admitted=False,raw_and_media_tensors_kept_on_Linux=True)
payload=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
print(json.dumps(dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=base64.b64encode(payload).decode())))
'''


def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    if args.output.exists():raise ValueError('Existing receipt must not be overwritten/retransferred')
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(SCRIPT.encode()).decode()+'\'))"'
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],capture_output=True,text=True,timeout=45)
    if p.returncode:raise RuntimeError(p.stderr)
    packet=json.loads(p.stdout);payload=base64.b64decode(packet['base64'],validate=True)
    assert len(payload)==packet['bytes'] and hashlib.sha256(payload).hexdigest()==packet['sha256']
    with args.output.open('xb') as f:f.write(payload)
    x=json.loads(payload)
    print(json.dumps(dict(status=x['result']['status'],conditions=x['result']['conditions'],macro=x['result']['macro'],
        actual_calls=x['total_actual_model_calls'],GPU_charged_seconds=x['total_GPU_charged_seconds'],
        receipt_bytes=packet['bytes'],receipt_sha256=packet['sha256']),ensure_ascii=False))


if __name__=='__main__':main()
