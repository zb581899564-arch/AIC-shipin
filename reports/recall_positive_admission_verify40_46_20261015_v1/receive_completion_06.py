"""Receive one small natural-completion summary, never raw/tensors/media."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REPORT = Path(__file__).resolve().parent
ROOT = '/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1'


def main():
    target = REPORT/'dev_completion_receipt_06.json'
    assert not target.exists(), 'Completed transfer must not be repeated'
    code = r'''
import base64,datetime as dt,hashlib,json,pathlib,socket
r=pathlib.Path('__ROOT__');h=r.parent
assert socket.gethostname()=='inspur-NP5570M5'
read=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
chainp=r/'dev/chain_01/completion.json';chain=read(chainp)
assert not (r/'dev/chain_01/failure.json').exists()
assert chain['status'] in ['PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION','STOP_POSITIVE_DEV_REJECTED']
resultp=r/'dev/comparison_01/result.json';result=read(resultp)
assert chain['comparison_ref']==dict(path=str(resultp),sha256=sha(resultp))
assert result['status']==chain['status'] and len(result['cases'])==4 and len(result['conditions'])==8
assert (result['status'].startswith('PASS'))==all(result['conditions'].values())
cpup=r/'dev/POSITIVE/cpu_01/completion.json';inputp=r/'dev/POSITIVE/input_qa_01/completion.json'
gpup=r/'dev/POSITIVE/gpu_01/completion.json';outp=r/'dev/POSITIVE/output_qa_01/completion.json'
cpu,inp,gpu,out=map(read,[cpup,inputp,gpup,outp])
assert cpu['expected_input_count']==inp['calls']==gpu['calls']==out['calls']==chain['actual_new_calls']==10
assert len(cpu['entries'])==len(inp['proofs'])==len(gpu['entries'])==len(out['proofs'])==10
assert inp['CPU_only'] and out['CPU_only'] and not inp['CUDA_initialized'] and not out['CUDA_initialized']
gate=read(r/'gpu_admission_dev_POSITIVE.json')
resourcep=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(gate['gpu_job_name']+'.resource.json')
resource=read(resourcep)
ledger=[json.loads(x) for x in (h/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
assert [x for x in ledger if x['name']==gate['gpu_job_name']]==[resource]
assert resource['status']=='completed' and resource['exit_code']==0 and sha(resourcep)==chain['resource_terminal_sha256']
journal=[json.loads(x) for x in (r/'dev/POSITIVE/gpu_01/attempts.jsonl').read_text().splitlines() if x.strip()]
assert len(journal)==20 and sum(x['event']=='BEGIN' for x in journal)==sum(x['event']=='ACCEPTED' for x in journal)==10
export=read(r/'dev/POSITIVE/verification_export.json');decisions={}
for e in export['events']:
 d=e['decision_result']['decision'];decisions[d]=decisions.get(d,0)+1
assert sum(decisions.values())==10
value=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),
 status=chain['status'],actual_new_model_calls=10,actual_first_input_QA=10,actual_first_output_QA=10,
 unique_ledger_exact=True,resource=resource,new_decisions=decisions,
 new_media_decodes=0,new_vision_processor_calls=0,old_success_repeated=False,
 production_admitted=False,fixed40_actual_calls=0,production_actual_calls=0,new_ZIPs=0,
 result=result,bindings={str(p):sha(p) for p in [chainp,resultp,cpup,inputp,gpup,outp,resourcep,r/'registration.json',r/'protocol_v2.json']})
p=r/'dev_completion_summary_06.json'
assert not p.exists(),'Existing summary must be adopted by explicit transfer recovery, not overwritten'
data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
assert len(data)<131072
with p.open('xb') as stream:stream.write(data)
print(json.dumps(dict(linux_path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),base64=base64.b64encode(data).decode())))
'''.replace('__ROOT__', ROOT)
    p = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -'],
        input=code,text=True,encoding='utf8',capture_output=True,timeout=45)
    if p.returncode:
        raise RuntimeError('Inspect state before an explicit recovery; no automatic repeat: '+p.stderr[-4000:])
    envelope = json.loads(p.stdout); data = base64.b64decode(envelope.pop('base64'))
    assert len(data) == envelope['bytes'] and hashlib.sha256(data).hexdigest() == envelope['sha256']
    value = json.loads(data)
    with (REPORT/'dev_completion_summary_06.json').open('xb') as stream:
        stream.write(data)
    assert hashlib.sha256((REPORT/'dev_completion_summary_06.json').read_bytes()).hexdigest() == envelope['sha256']
    receipt = dict(**envelope,windows_size_and_sha_matched=True,result=value)
    with target.open('x',encoding='utf8') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=value['status'],bytes=envelope['bytes'],sha256=envelope['sha256'],
        decisions=value['new_decisions'],conditions=value['result']['conditions'],macro=value['result']['macro']),ensure_ascii=False))


if __name__ == '__main__':
    main()
