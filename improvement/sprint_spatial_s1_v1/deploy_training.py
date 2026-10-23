"""Necessary small training controls; never overwrite completed preparation code."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'reports/sprint_spatial_s1_20261021_v1'
FILES = ['condition_inputs.py', 'model_io.py', 'train_arms.py', 'audit_review.py',
         'confirm.py', 'training_controller.py', 'test_training_contracts.py']


def main():
    payload = {}
    for name in FILES:
        data = (HERE / name).read_bytes()
        ast.parse(data, filename=name)
        payload[name] = dict(base64=base64.b64encode(data).decode(), sha256=hashlib.sha256(data).hexdigest())
    script = '''
import ast,base64,hashlib,json,pathlib,os,subprocess,sys
r=pathlib.Path('/home/inspur/aic_video_work/sprint_spatial_s1_20261021_v1')
files=json.loads(PAYLOAD)
if not (r/'center_source_lock.json').exists() or (r/'training_code_acceptance02.json').exists():
 raise ValueError('Frozen preparation inputs required; no repeated deployment')
for name,sha in json.loads((r/'code_acceptance.json').read_text())['code_sha256'].items():
 if hashlib.sha256((r/'code'/name).read_bytes()).hexdigest()!=sha: raise ValueError('Preparation code changed')
for name,entry in files.items():
 raw=base64.b64decode(entry['base64']);ast.parse(raw,filename=name)
 if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Small code transfer mismatch')
 if (r/'code'/name).exists():raise FileExistsError(name)
for name,entry in files.items():
 with (r/'code'/name).open('xb') as f:f.write(base64.b64decode(entry['base64']))
sys.path.insert(0,str(r/'code'))
from common import ref,write,run_stage
receipt=dict(files={name:ref(r/'code'/name) for name in files},bytes=sum(len(base64.b64decode(x['base64'])) for x in files.values()),
 unchanged_preparation_code=True,route='Existing authorized Tailscale necessary small-code control; no intermediate data transfer')
write(r/'training_code_acceptance02.json',receipt)
run_stage('training_cpu_contracts','test_training_contracts.py')
print(json.dumps(dict(deployment=receipt,CPU=json.loads((r/'training_cpu_contract_acceptance.json').read_text()))))
'''.replace('PAYLOAD', repr(json.dumps(payload)))
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-tailscale', '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],
        input=script.encode(), capture_output=True, timeout=75)
    receipt = dict(exit_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode())
    with (REPORT / 'training_deploy02.json').open('x', encoding='utf8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False))
    if result.returncode:
        raise RuntimeError('Actual deployment/preflight failure; inspect preserved stage before recovery')


if __name__ == '__main__':
    main()
