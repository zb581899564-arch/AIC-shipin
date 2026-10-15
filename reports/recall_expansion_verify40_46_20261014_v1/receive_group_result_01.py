"""Receive only a completed group's small result and unique GPU receipts.

No model, processor, decode, replay, comparison, launcher or recovery runs here.
All original evidence stays on Linux; Windows verifies the received JSON bytes.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import base64,datetime,hashlib,json,pathlib,socket,sys
r=pathlib.Path('/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1')
assert socket.gethostname()=='inspur-NP5570M5'
group=__GROUP_LITERAL__
sys.path.insert(0,str(r/'code'))
import model_common as io
chain=r/group/('chain_02' if group=='dev' else 'chain_03')
complete=io.read(chain/'completion.json')
assert complete['group']==group and complete['status'] in (
 'COMPLETE_EXTERNAL_GROUP_PROXY_PASS_PENDING_FIXED_FACTS','STOP_EXTERNAL_RECALL_PROXY_REJECTED')
comparison=io.read(r/group/'comparison_01/result.json')
assert complete['comparison_sha256']==io.sha(r/group/'comparison_01/result.json')
assert complete['proxy_result']==comparison['status']
assert comparison['group']==group and len(comparison['cases'])==4
assert comparison['bindings']['protocol_sha256']==io.sha(r/'protocol.json')
stages={};refs={}
for stage in ['B0','VERIFY']:
 gate_path=r/('gpu_admission_'+group+'_'+stage+'.json')
 gate=io.read(gate_path);resource,resource_sha=io.terminal(gate)
 resource_path=io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json')
 gpu=r/group/stage/'gpu_01';qa=r/group/stage/'replay_01'
 done=io.read(gpu/'completion.json');replay=io.read(qa/'completion.json')
 expected=gate['expected_input_count']
 assert done['status']=='PASS_ALL_RECALL_'+stage+'_CALLS_NOT_QUALITY'
 assert replay['status']=='PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY'
 assert done['calls']==replay['calls']==expected
 assert replay['CPU_only'] is True and replay['CUDA_initialized'] is False
 assert replay['gpu_completion_sha256']==io.sha(gpu/'completion.json')
 assert replay['resource_terminal_sha256']==resource_sha
 journal=io.rows(gpu/'attempts.jsonl')
 counts={name:sum(row['event']==name for row in journal) for name in ['BEGIN','ACCEPTED']}
 assert counts=={'BEGIN':expected,'ACCEPTED':expected} and len(journal)==2*expected
 identity=io.read(gpu/'model_identity.json')['identity'];io.verify_identity(identity)
 stages[stage]=dict(calls=expected,first_independent_replay_proofs=len(replay['proofs']),
  actual_model_parameters=identity['logical_parameters'],journal=counts,
  unique_shared_ledger_terminal=True,resource_status=resource['status'],exit_code=resource['exit_code'],
  charged_seconds=resource['charged_seconds'],sampled_peak_memory_mib=resource['sampled_peak_memory_mib'],
  resource_ref=dict(path=str(resource_path),sha256=resource_sha))
 for p in [gate_path,gpu/'completion.json',qa/'completion.json',gpu/'attempts.jsonl',r/('source_lock_'+group+'_'+stage+'.json')]:
  refs[str(p)]=io.sha(p)
export=r/group/'VERIFY/verification_export.json'
assert comparison['bindings']['verification_export_sha256']==io.sha(export)
assert comparison['bindings']['cpu_acceptance_sha256']==io.sha(r/('cpu_acceptance_'+group+'.json'))
value=dict(schema='RECALL_SMALL_GROUP_COMPLETION_RECEIPT_V1',utc=io.utc(),group=group,
 chain_completion=complete,comparison=comparison,stages=stages,bindings=refs,
 total_actual_model_calls=sum(x['calls'] for x in stages.values()),
 total_charged_gpu_seconds=sum(x['charged_seconds'] for x in stages.values()),
 comparison_ref=dict(path=str(r/group/'comparison_01/result.json'),sha256=io.sha(r/group/'comparison_01/result.json')),
 production_started=False,original_raw_tensors_media_kept_on_Linux=True)
payload=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
print(json.dumps(dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=base64.b64encode(payload).decode())))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=('dev', 'confirm'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Do not repeat or overwrite a successful result receipt')
    script = REMOTE.replace('__GROUP_LITERAL__', repr(args.group))
    encoded = base64.b64encode(script.encode()).decode()
    command = 'python3 -c "import base64;exec(base64.b64decode(\'' + encoded + '\'))"'
    proc = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                           'aic-inspur-home', command], capture_output=True, text=True, timeout=40)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    packet = json.loads(proc.stdout)
    payload = base64.b64decode(packet['base64'], validate=True)
    if len(payload) != packet['bytes'] or hashlib.sha256(payload).hexdigest() != packet['sha256']:
        raise ValueError('Linux/Windows result receipt size or SHA differs')
    result = json.loads(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(payload)
    if args.output.stat().st_size != packet['bytes'] or hashlib.sha256(args.output.read_bytes()).hexdigest() != packet['sha256']:
        raise ValueError('Saved Windows receipt differs from the Linux bytes')
    print(json.dumps(dict(group=args.group, status=result['comparison']['status'],
        macro=result['comparison']['macro'], conditions=result['comparison']['conditions'],
        total_actual_model_calls=result['total_actual_model_calls'],
        total_charged_gpu_seconds=result['total_charged_gpu_seconds'],
        received_bytes=packet['bytes'], received_sha256=packet['sha256']), ensure_ascii=False))


if __name__ == '__main__':
    main()
