"""One small natural terminal receipt, raw/cache/model evidence stays on Linux."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REPORT=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1'


def main():
    assert not (REPORT/'dev_completion_receipt_04.json').exists()
    code=r'''
import base64,datetime as dt,hashlib,json,pathlib,socket
r=pathlib.Path('__ROOT__');h=r.parent
assert socket.gethostname()=='inspur-NP5570M5'
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
chainp=r/'chain_01/completion.json';chain=read(chainp);assert not (r/'chain_01/failure.json').exists()
assert chain['status'] in ['PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM','STOP_ADAPTER_ROLE_DEV_REJECTED']
resultp=r/'comparison_01/result.json';result=read(resultp)
assert result['status']==chain['status'] and result['group']=='dev' and len(result['cases'])==4 and len(result['conditions'])==8
assert (result['status'].startswith('PASS'))==all(result['conditions'].values())
assert chain['comparison_ref']==dict(path=str(resultp),sha256=sha(resultp))
gpup=r/'gpu_01/completion.json';qap=r/'output_qa_01/completion.json';gpu,qa=read(gpup),read(qap)
assert gpu['status']=='PASS_ROLE_ALL10_MODEL_CALLS_NOT_QUALITY' and qa['status']=='PASS_ROLE_ALL10_OUTPUT_QA_NOT_QUALITY'
assert gpu['calls']==len(gpu['entries'])==qa['calls']==len(qa['proofs'])==len(qa['events'])==10
assert qa['input_encoder_calls']==qa['new_model_calls']==qa['prior_QA_repeated']==0
assert qa['CPU_only'] is True and qa['CUDA_initialized'] is False
assert qa['gpu_completion_ref']==dict(path=str(gpup),sha256=sha(gpup))
journalp=r/'gpu_01/attempts.jsonl';journal=[json.loads(x) for x in journalp.read_text().splitlines() if x.strip()]
assert len(journal)==20
for i,row in enumerate(gpu['entries'],1):
 a,b=journal[2*(i-1):2*i]
 assert a['event']=='BEGIN' and b['event']=='ACCEPTED' and a['call_id']==b['call_id']==i and a['case_id']==b['case_id']==row['case_id'] and b['done_ref']==row['done_ref']
gate=read(r/'gpu_admission.json');resourcep=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'/(gate['gpu_job_name']+'.resource.json')
resource=read(resourcep);ledger=[json.loads(x) for x in (h/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
assert [x for x in ledger if x['name']==gate['gpu_job_name']]==[resource]
assert resource['status']=='completed' and resource['exit_code']==0 and sha(resourcep)==qa['resource_terminal_sha256']==chain['resource_terminal_sha256']
identityp=pathlib.Path(gpu['model_identity_ref']['path']);assert sha(identityp)==gpu['model_identity_ref']['sha256']
identity=read(identityp);assert identity['inventory']['actual_physical_parameters']==8782459120 and identity['activation_role']=='BASE_ONLY_FOR_NEW_ADMISSION_TIME_FOR_PROPOSALS'
value=dict(status=chain['status'],utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),actual_new_calls=10,
 actual_adopted_first_input_QA=10,actual_new_first_output_QA=10,new_input_encodes=0,new_media_or_decode_calls=0,
 unique_natural_ledger_exact=True,resource=resource,result=result,
 original_positive_confirm_STOP_preserved=True,production_admitted=False,fresh_confirmation_admitted=False,new_ZIPs=0,
 bindings={str(p):sha(p) for p in [chainp,resultp,gpup,qap,journalp,identityp,resourcep,r/'registration.json',r/'protocol.json']})
p=r/'dev_completion_summary_04.json';assert not p.exists(),'Adopt existing summary only through explicit transfer recovery'
data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();assert len(data)<65536
with p.open('xb') as stream:stream.write(data)
print(json.dumps(dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),linux_path=str(p),base64=base64.b64encode(data).decode())))
'''.replace('__ROOT__',ROOT)
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -'],input=code,
        text=True,encoding='utf8',capture_output=True,timeout=45)
    if result.returncode:raise RuntimeError('Inspect retained actual terminal/summary before explicit recovery: '+result.stderr[-4500:])
    envelope=json.loads(result.stdout);data=base64.b64decode(envelope.pop('base64'))
    assert len(data)==envelope['bytes'] and hashlib.sha256(data).hexdigest()==envelope['sha256']
    value=json.loads(data)
    with (REPORT/'dev_completion_summary_04.json').open('xb') as stream:stream.write(data)
    with (REPORT/'dev_completion_receipt_04.json').open('x',encoding='utf8') as stream:
        json.dump(dict(**envelope,windows_size_and_sha_matched=True,result=value),stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=value['status'],bytes=envelope['bytes'],sha256=envelope['sha256'],resource_seconds=value['resource']['charged_seconds'],
        conditions=value['result']['conditions'],decisions=value['result']['new_decisions'],macro=value['result']['macro'],paired=value['result']['paired_decisions']),ensure_ascii=False))


if __name__=='__main__':main()
