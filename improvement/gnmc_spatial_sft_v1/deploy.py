"""Small new control packet; all media and computation stay on Linux."""
import base64
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
REPORT=PROJECT/'reports/gnmc_spatial_sft_iteration_20261013_v1'
HERE=Path(__file__).parent

def main():
    if (REPORT/'deployment.json').exists(): raise ValueError('do not deploy/launch twice')
    packet={('code/'+p.name):p.read_bytes() for p in HERE.glob('*.py') if p.name!='deploy.py'}
    for name in ['train_candidates.json','train_index.json']: packet['control/'+name]=(REPORT/name).read_bytes()
    for name in ['protocol.json','official_rule_check.json']: packet[name]=(REPORT/name).read_bytes()
    members={k:hashlib.sha256(v).hexdigest() for k,v in packet.items()};buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in packet.items(): z.writestr(k,v)
    raw=buf.getvalue();digest=hashlib.sha256(raw).hexdigest();(REPORT/'control_packet.zip').write_bytes(raw)
    bootstrap='''import base64,hashlib,io,json,os,pathlib,subprocess,zipfile,datetime
root=pathlib.Path('/home/inspur/aic_video_work/gnmc_spatial_sft_iteration_20261013_v1')
if root.exists(): raise ValueError('unique new research root already exists; inspect instead of relaunch')
raw=base64.b64decode(PACKET)
if hashlib.sha256(raw).hexdigest()!=DIGEST: raise ValueError('control SHA')
z=zipfile.ZipFile(io.BytesIO(raw))
if z.testzip() is not None or set(z.namelist())!=set(MEMBERS): raise ValueError('CRC/member inventory')
for name,h in MEMBERS.items():
 if pathlib.PurePosixPath(name).is_absolute() or '..' in pathlib.PurePosixPath(name).parts or hashlib.sha256(z.read(name)).hexdigest()!=h: raise ValueError('unsafe/mismatched member')
root.mkdir();z.extractall(root)
(root/'deployment.json').write_text(json.dumps({'control_bytes':len(raw),'control_sha256':DIGEST,'member_sha256':MEMBERS}))
(root/'chain_launch_claim.json').write_text(json.dumps({'unique':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
env=os.environ.copy();gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index','--format=csv,noheader'],text=True).splitlines()[0].strip();env['CUDA_VISIBLE_DEVICES']=gpu
cmd=['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python',str(root/'code/controller.py')]
with (root/'chain.log').open('x') as log: proc=subprocess.Popen(cmd,stdout=log,stderr=log,env=env,start_new_session=True)
receipt={'pid':proc.pid,'command':cmd,'CUDA_VISIBLE_DEVICES':gpu,'control_bytes':len(raw),'control_sha256':DIGEST,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(root/'chain_launch.json').write_text(json.dumps(receipt));print(json.dumps(receipt))
'''
    script=bootstrap.replace('PACKET',repr(base64.b64encode(raw).decode())).replace('DIGEST',repr(digest)).replace('MEMBERS',repr(members))
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes',
                           'aic-inspur-home','python3 -'],input=script,text=True,capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr or result.stdout)
    receipt=json.loads(result.stdout);(REPORT/'deployment.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__': main()
