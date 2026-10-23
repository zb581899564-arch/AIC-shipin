"""Explicit CPU-dependency recovery; same pilot, zero previous GPU/input success."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from deploy_pilot15 import PROTOCOL, REPORT

HERE=Path(__file__).parent
INDEPENDENT='''def independent_AP(scores,labels):
    total=int(labels.sum())
    if total==0:raise ValueError('No positive reference')
    value=0.
    for threshold in np.unique(scores[labels==1]):
        selected=scores>=threshold
        positive_at_level=int(((scores==threshold)&(labels==1)).sum())
        value+=(positive_at_level/total)*(int(labels[selected].sum())/int(selected.sum()))
    return value


'''


def recovery_files():
    files={path.name:path.read_text(encoding='utf-8') for path in HERE.glob('pilot15_*.py')}
    files['direct.py']=(HERE/'direct.py').read_text(encoding='utf-8')
    files['pilot15_common.py']=files['pilot15_common.py'].replace("ROOT=ADMISSION/'matched_hl_pilot15'","ROOT=ADMISSION/'matched_hl_pilot16'")
    files['pilot15_controller.py']=files['pilot15_controller.py'].replace("20261021_v15'","20261021_v16'")
    checks=files['pilot15_checks.py'].replace('from sklearn.metrics import average_precision_score\n','')
    checks=checks.replace('from pilot15_review import average_precision','from pilot15_review import average_precision, independent_AP')
    checks=checks.replace('average_precision_score(truth,scores)','independent_AP(scores,truth)')
    files['pilot15_checks.py']=checks
    review=files['pilot15_review.py'].replace('    from sklearn.metrics import average_precision_score\n','')
    review=review.replace('def main():',INDEPENDENT+'def main():')
    review=review.replace('average_precision_score(labels[labels>=0],scores[labels>=0])','independent_AP(scores[labels>=0],labels[labels>=0])')
    files['pilot15_review.py']=review
    return {name:value.encode('utf-8') for name,value in files.items()}


def main():
    files=recovery_files()
    output=HERE/'remaining16';output.mkdir()
    for name,data in files.items():(output/name).write_bytes(data)
    envelope=dict(files={name:base64.b64encode(value).decode() for name,value in files.items()},
        sha256={name:hashlib.sha256(value).hexdigest() for name,value in files.items()},protocol=PROTOCOL)
    script=r'''
import base64,hashlib,json,os,pathlib,subprocess,time
payload=json.loads(PAYLOAD);admission=pathlib.Path('/home/inspur/aic_video_work/highlight_source_admission_20261021_v1')
old=admission/'matched_hl_pilot15'
failure=json.loads((old/'failure.json').read_text())
if 'checks' not in failure['traceback'] or (old/'input_acceptance.json').exists() or (old/'gpu_launch.json').exists():raise ValueError('Recovery not restricted to original zero-input/zero-GPU failure')
root=admission/'matched_hl_pilot16';root.mkdir();code=root/'code';code.mkdir()
for name,encoded in payload['files'].items():
 data=base64.b64decode(encoded)
 if hashlib.sha256(data).hexdigest()!=payload['sha256'][name]:raise ValueError('Small code identity failed')
 with (code/name).open('xb') as stream:stream.write(data)
with (root/'protocol.json').open('x') as stream:json.dump(payload['protocol'],stream,indent=2)
with (root/'recovery_registration.json').open('x') as stream:json.dump(dict(previous_failure=str(old/'failure.json'),previous_GPU_calls=0,previous_successful_new_RGB=0,change='Replace unavailable sklearn AP dependency with independent positive-threshold set arithmetic; same protocol/seed/200updates/600seconds',code_sha256=payload['sha256'],no_old_success_repeated=True),stream,indent=2)
with (root/'controller.log').open('x') as log:
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
 p=subprocess.Popen(['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B','-u',str(code/'pilot15_controller.py')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 result=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=p.args,root=str(root),time=time.time(),code_sha256=payload['sha256'])
 with (root/'controller_launch.json').open('x') as stream:json.dump(result,stream,indent=2)
 print(json.dumps(result))
'''.replace('PAYLOAD',repr(json.dumps(envelope)))
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','aic-inspur-tailscale',
        '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -'],
        input=script.encode(),capture_output=True,timeout=60)
    receipt=dict(returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode())
    with (REPORT/'remaining16_launch.json').open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)
    print(json.dumps(receipt))
    if result.returncode:raise RuntimeError('Actual recovery deployment failure; no blind repeat')


if __name__=='__main__':main()
