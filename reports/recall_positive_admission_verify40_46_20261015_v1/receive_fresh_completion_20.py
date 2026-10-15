"""Once-only short receipt for a naturally completed first fresh confirmation."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REPORT = Path(__file__).resolve().parent
ROOT = '/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1'


def main():
    target = REPORT/'fresh_completion_receipt_20.json'
    assert not target.exists(), 'Do not repeat completed summary transfer'
    code = r'''
import base64,datetime as dt,hashlib,json,pathlib,socket
main=pathlib.Path('__ROOT__');r=main/'fresh_01';h=main.parent
assert socket.gethostname()=='inspur-NP5570M5'
read=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
chainp=r/'confirm/chain_02/completion.json';chain=read(chainp)
assert not (r/'confirm/chain_02/failure.json').exists()
allowed=['PASS_POSITIVE_FRESH_CONFIRM_PENDING_FIXED40','STOP_POSITIVE_CONFIRM_REJECTED']
assert chain['status'] in allowed,'Use explicit terminal diagnosis for a zero-candidate or engineering STOP'
resultp=main/'confirm/comparison_01/result.json';result=read(resultp)
assert chain['comparison_ref']==dict(path=str(resultp),sha256=sha(resultp))
assert result['status']==chain['status'] and result['group']=='confirm' and len(result['cases'])==4 and len(result['conditions'])==8
assert all(type(v) is bool for v in result['conditions'].values())
assert (result['status'].startswith('PASS'))==all(result['conditions'].values())
ledger=[json.loads(line) for line in (h/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
controller=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'
stages={};bindings={}
def bind(path):bindings[str(path)]=sha(path);return read(path)
for name in ['B0','VERIFY','POSITIVE']:
 root=main if name=='POSITIVE' else r
 cpup=root/('confirm/POSITIVE/cpu_01/completion.json' if name=='POSITIVE' else 'cpu_acceptance_confirm.json' if name=='B0' else 'confirm/VERIFY/cpu_01/completion.json')
 inp=root/('confirm/'+name+'/input_qa_01/completion.json')
 gpup=root/('confirm/'+name+'/gpu_01/completion.json')
 outp=root/('confirm/'+name+('/output_qa_01/completion.json' if name=='POSITIVE' else '/replay_01/completion.json'))
 gatep=root/('gpu_admission_confirm_'+name+'.json')
 cpu,qa,gpu,out,gate=map(bind,[cpup,inp,gpup,outp,gatep])
 count=len(cpu['entries'])
 assert 0<count==qa['calls']==gpu['calls']==out['calls']==len(qa['proofs'])==len(gpu['entries'])==len(out['proofs'])
 assert qa['CPU_only'] and out['CPU_only'] and not qa['CUDA_initialized'] and not out['CUDA_initialized']
 assert qa.get('new_model_calls',0)==out.get('new_model_calls',0)==0
 journalp=gpup.parent/'attempts.jsonl';journal=[json.loads(line) for line in journalp.read_text().splitlines() if line.strip()]
 assert len(journal)==2*count
 assert all(journal[2*i]['event']=='BEGIN' and journal[2*i+1]['event']=='ACCEPTED' and journal[2*i]['case_id']==journal[2*i+1]['case_id'] for i in range(count))
 bindings[str(journalp)]=sha(journalp)
 resourcep=controller/(gate['gpu_job_name']+'.resource.json');resource=bind(resourcep)
 assert [row for row in ledger if row['name']==gate['gpu_job_name']]==[resource]
 assert resource['status']=='completed' and resource['exit_code']==0 and out['resource_terminal_sha256']==sha(resourcep)
 stages[name]=dict(actual_model_calls=count,first_independent_input_QA=count,first_independent_output_QA=count,
                  unique_ledger_exact=True,resource=resource)
assert stages['B0']['actual_model_calls']==28
primaryp=r/'confirm/inputs_01/completion.json';primary=bind(primaryp)
assert primary['primary_encode_calls_started']==primary['primary_encode_calls_returned']==primary['actual_input_count']==28
assert primary['actual_new_RGB_decode_passes']==4 and primary['original_clock_measurements_repeated']==0
for path in [chainp,resultp,r/'positive_fresh_registration.json',r/'positive_fresh_recovery_registration_v2.json',
             r/'confirm/chain_01/failure.json',main/'protocol_v2.json',main/'registration_confirm.json',
             main/'dev/selection_before_confirmation.json',r/'reference_01/completion.json']:
 bind(path)
export=read(main/'confirm/POSITIVE/verification_export.json');decisions={}
for event in export['events']:
 decision=event['decision_result']['decision'];decisions[decision]=decisions.get(decision,0)+1
assert sum(decisions.values())==stages['POSITIVE']['actual_model_calls']
value=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),status=chain['status'],
 stages=stages,total_actual_fresh_model_calls=sum(v['actual_model_calls'] for v in stages.values()),
 new_positive_decisions=decisions,actual_media_sources=4,actual_media_bytes=41763431,primary_inputs=28,source_RGB_decode_passes=4,
 successful_primary_or_media_or_RGB_operations_repeated=0,retained_original_engineering_failure=True,
 total_GPU_charged_seconds=sum(v['resource']['charged_seconds'] for v in stages.values()),
 production_admitted=False,fixed40_actual_calls=0,production_actual_calls=0,new_ZIPs=0,result=result,bindings=bindings)
# Preserve the wrapper's actual schema for expense rather than infer a different unit.
summary=main/'fresh_completion_summary_20.json'
assert not summary.exists(),'Inspect existing exact summary for explicit transfer recovery'
data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();assert len(data)<131072
with summary.open('xb') as stream:stream.write(data)
print(json.dumps(dict(linux_path=str(summary),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),base64=base64.b64encode(data).decode())))
'''.replace('__ROOT__',ROOT)
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','python3 -'],
        input=code,text=True,encoding='utf8',capture_output=True,timeout=45)
    if result.returncode:
        raise RuntimeError('Inspect retained terminal/transfer state before an explicit recovery: '+result.stderr[-5000:])
    envelope = json.loads(result.stdout);data = base64.b64decode(envelope.pop('base64'))
    assert len(data)==envelope['bytes'] and hashlib.sha256(data).hexdigest()==envelope['sha256']
    value = json.loads(data)
    with (REPORT/'fresh_completion_summary_20.json').open('xb') as stream:stream.write(data)
    receipt = dict(**envelope,windows_size_and_sha_matched=True,result=value)
    with target.open('x',encoding='utf8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=value['status'],bytes=envelope['bytes'],sha256=envelope['sha256'],
        calls=value['total_actual_fresh_model_calls'],decisions=value['new_positive_decisions'],
        conditions=value['result']['conditions'],macro=value['result']['macro']),ensure_ascii=False))


if __name__=='__main__':main()
