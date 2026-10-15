"""One small control deployment; baseline ZIP only, no raw/proof exports."""
import base64
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2];REPORT=PROJECT/'reports/rapid_risk_three_20261013_v1'

def main():
    if (REPORT/'deployment.json').exists():raise ValueError('do not repeat deployment')
    controls={'code/'+p.name:p.read_bytes() for p in Path(__file__).parent.glob('*.py') if p.name!='deploy.py'}
    for n in ['authorization.json','protocol.json','official_rule_check.json']:controls[n]=(REPORT/n).read_bytes()
    controls['control/baseline_D8.zip']=(PROJECT/'deliveries/DURATION_GUARD_D8_8B_20261013/candidate_DURATION_GUARD_D8_8B.zip').read_bytes()
    controls['control/history.json']=(REPORT/'history.json').read_bytes()
    original=json.loads((PROJECT/'reports/boundary_refinement_20261012_v1/input_01/source_bindings.json').read_text())
    binding={k:original[k] for k in ['status','source_field_files','original_source_manifest','input_native_clocks_previously_decoded_and_accepted']}
    controls['control/source_binding.json']=json.dumps(binding).encode()
    members={k:hashlib.sha256(v).hexdigest() for k,v in controls.items()};buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in controls.items():z.writestr(k,v)
    raw=buffer.getvalue();digest=hashlib.sha256(raw).hexdigest();(REPORT/'control_packet.zip').write_bytes(raw)
    script='raw=__import__("base64").b64decode('+repr(base64.b64encode(raw).decode())+')\nexpected='+repr(digest)+'\nmembers='+repr(members)+'\n'+'''import pathlib,json,zipfile,io,hashlib,subprocess,os,datetime
root=pathlib.Path('/home/inspur/aic_video_work/rapid_risk_three_20261013_v1')
if root.exists():raise ValueError('unique root exists; inspect instead of relaunch')
if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('controlSHA')
z=zipfile.ZipFile(io.BytesIO(raw))
if z.testzip()!=None or set(z.namelist())!=set(members):raise ValueError('CRC/member inventory')
for k,h in members.items():
 if pathlib.PurePosixPath(k).is_absolute() or '..' in pathlib.PurePosixPath(k).parts or hashlib.sha256(z.read(k)).hexdigest()!=h:raise ValueError('memberSHA/path')
root.mkdir();z.extractall(root)
(root/'deployment.json').write_text(json.dumps({'control_bytes':len(raw),'control_SHA256':expected,'members':members}))
(root/'launch_claim.json').write_text(json.dumps({'CPU_only':True,'unique':True,'new_model_calls':0}))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
cmd=['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python',str(root/'code/package_three.py')]
with (root/'package.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=log,env=env,start_new_session=True)
receipt={'pid':p.pid,'command':cmd,'control_bytes':len(raw),'control_SHA256':expected,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(root/'launch.json').write_text(json.dumps(receipt));print(json.dumps(receipt))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes',
                           'aic-inspur-home','python3 -'],input=script,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    receipt=json.loads(result.stdout);(REPORT/'deployment.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))

if __name__=='__main__':main()
