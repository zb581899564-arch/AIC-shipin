"""Copy small accepted receipts over the same required Mac route without reruns."""
import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
DATA='/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2'
files={'upload_verification.json':DATA+'/upload_verification.json',
       'linux_readiness_completion.json':DATA+'/linux_readiness_completion.json',
       'linux_cpu_preflight/crop/preflight.json':'/home/inspur/aic_video_work/runs/qwen_annotation_v2_crop_preflight_001/preflight.json',
       'linux_cpu_preflight/temporal/preflight.json':'/home/inspur/aic_video_work/runs/qwen_annotation_v2_temporal_preflight_001/preflight.json'}
code=f'''import base64,hashlib,json
from pathlib import Path
files={files!r}
result={{}}
for name,path in files.items():
 p=Path(path);assert p.resolve(strict=True)==p
 b=p.read_bytes()
 result[name]={{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}}
print(json.dumps(result))
'''
encoded=base64.b64encode(code.encode()).decode()
command=['ssh','-o','ProxyJump=macmini','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
         '-o','ConnectTimeout=20','aic-inspur-home','python3 -B -c "import base64;exec(base64.b64decode(\''+encoded+'\'))"']
result=json.loads(subprocess.check_output(command,text=True))
binding={}
for name,record in result.items():
    raw=base64.b64decode(record['base64'])
    assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']
    parsed=json.loads(raw)
    if name=='linux_readiness_completion.json':
        assert parsed['status']=='PASS_LINUX_UPLOAD_SELECTED_HASHES_AND_ALL_REAL_IMAGE_CPU_PREFLIGHTS'
        assert parsed['zip_sha256']=='45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c'
    path=HERE/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(raw)
    binding[name]={'remote_path':files[name],'bytes':len(raw),'sha256':record['sha256']}
receipt={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_REMOTE_RECEIPTS_COPIED_EXACT_BYTES',
         'route':'LINUX_MACMINI_PROXYJUMP_WINDOWS','files':binding,'cpu_jobs_rerun':False,
         'training_started':False}
with (HERE/'linux_receipt_copy.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt),flush=True)
