"""Explicit zero-success dependency recovery, preserving the original import failure."""
import base64
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
REPORT=HERE.parents[2]/'reports/i3d_umt_cross_domain_20261021_v1'
REMOTE='/home/inspur/aic_video_work/i3d_umt_cross_domain_20261021_v1/crossdata12'


def main():
    names=['review.py','controller.py','fit_and_review.py']
    files={n:base64.b64encode((HERE/n).read_bytes()).decode() for n in names}
    files['prepare_raw.py']=base64.b64encode((HERE.parent/'prepare_raw.py').read_bytes()).decode()
    # train.py has not executed. Keep original deployment bytes and deploy revised tolerance separately.
    files['train13.py']=base64.b64encode((HERE/'train.py').read_bytes()).decode()
    payload=json.dumps(files)
    script=r'''
import json,pathlib,base64,subprocess,os,hashlib
r=pathlib.Path(REMOTE_PATH)
assert not (r/'inputs').exists() and not (r/'registration.json').exists()
log=(r/'prepare.log').read_text()
assert 'ModuleNotFoundError' in log and 'prepare_raw' in log
with (r/'prepare_failure12_preserved.json').open('x') as f:json.dump({'status':'ACTUAL_IMPORT_FAILURE_BEFORE_ANY_INPUT','traceback':log,'successful_new_inputs':0},f,indent=2)
for name,encoded in json.loads(PAYLOAD).items():
 p=r/'code'/name
 with p.open('xb') as out:out.write(base64.b64decode(encoded))
# The original train.py is unexecuted and frozen in deployment12; choose explicit train13 in new entry13.
entry="import train13\nimport review\nif __name__ == '__main__':\n    train13.main()\n    review.main()\n"
(r/'code/fit_and_review13.py').write_text(entry)
controller=(r/'code/controller.py').read_text().replace("'fit_and_review.py'","'fit_and_review13.py'")
(r/'code/controller13.py').write_text(controller)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (r/'new_cpu_checks13.log').open('x') as logf:
 result=subprocess.run([py,'-B',str(r/'code/checks.py')],env=env,cwd=r,stdin=subprocess.DEVNULL,stdout=logf,stderr=subprocess.STDOUT,timeout=90)
with (r/'new_cpu_checks13_terminal.json').open('x') as f:json.dump({'exit_code':result.returncode},f)
if result.returncode:raise RuntimeError('New CPU contracts failed; no prepare or GPU launch')
code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'code').glob('*.py')}
with (r/'remaining13_registration.json').open('x') as f:json.dump({'old_failure_preserved':True,'new_input_successes_before_recovery':0,'scientific_protocol_unchanged':True,'change':'Supply omitted exact resize helper; explicit unexecuted train13 reload tolerance','code_sha256':code},f,indent=2)
logf=(r/'prepare13.log').open('x')
p=subprocess.Popen([py,'-u','-B',str(r/'code/prepare.py')],env=env,cwd=r,stdin=subprocess.DEVNULL,stdout=logf,stderr=subprocess.STDOUT,start_new_session=True)
launch={'pid':p.pid,'start_ticks':pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],'argv':[py,'-u','-B',str(r/'code/prepare.py')]}
with (r/'prepare_launch13.json').open('x') as f:json.dump(launch,f,indent=2)
env['CUDA_VISIBLE_DEVICES']='0'
cf=(r/'controller13.log').open('x')
c=subprocess.Popen([py,'-u','-B',str(r/'code/controller13.py')],env=env,cwd=r,stdin=subprocess.DEVNULL,stdout=cf,stderr=subprocess.STDOUT,start_new_session=True)
out={'prepare':launch,'controller':{'pid':c.pid,'start_ticks':pathlib.Path(f'/proc/{c.pid}/stat').read_text().rsplit(')',1)[1].split()[19]},'CPU_checks':'PASS4','control_code_bytes':sum(len(base64.b64decode(s)) for s in json.loads(PAYLOAD).values()),'automatic426':False}
with (r/'launch13.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
'''.replace('REMOTE_PATH',repr(REMOTE)).replace('PAYLOAD',repr(payload))
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
             'aic-inspur-tailscale','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -']
    p=subprocess.run(command,input=script.encode(),capture_output=True,timeout=115)
    receipt=dict(returncode=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode())
    with (REPORT/'crossdata13_launch.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    print(json.dumps(receipt,ensure_ascii=False))
    if p.returncode:raise RuntimeError('Inspect authoritative state; no blind repeat')


if __name__=='__main__':
    main()
