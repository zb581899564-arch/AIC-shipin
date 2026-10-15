import base64
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPORT=HERE.parents[1]/'reports/gnmc_width_iteration_20261013_v1'

def main():
    if (REPORT/'recovery_deployment_01.json').exists():raise ValueError('recovery deployment is not repeated')
    protocol={'version':2,'repair':'own common.py name shadowed original engine common; rename own module gw_common',
        'input_root':'/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1',
        'reuse':'all40 originals/RGB/proofs/80actual cached processor inputs; no download/prepare/decode/encode rerun',
        'old_source_lock_sha256':'bd88d52a3e18aaced8661f658bb6d5a402ac241e09d4dc69f606dbdabcb50848',
        'previous_actual_model_answers':0,'previous_failed_job_seconds_preserved':62.10517555847764,
        'prompt_geometry_parameters_groups_and_gates_unchanged':True,
        'new_jobs':['gnmc_width_screen20_original_b_20261013_v2','gnmc_width_confirm20_original_b_20261013_v2'],
        'no_automatic_production':True}
    files={'recovery_protocol.json':json.dumps(protocol,ensure_ascii=False,indent=2).encode()}
    for p in HERE.glob('*.py'):
        if p.name!='deploy_recovery.py':files['code/'+p.name]=p.read_bytes()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    raw=buf.getvalue();digest=hashlib.sha256(raw).hexdigest()
    expected={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    script=f'''import base64,hashlib,io,json,os,socket,subprocess,zipfile
from pathlib import Path
assert socket.gethostname()=="inspur-NP5570M5"
root=Path("/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1/recovery_01")
if root.exists():raise ValueError("recovery already exists; inspect actual state, do not relaunch")
raw=base64.b64decode({base64.b64encode(raw).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={digest!r}
root.mkdir();expected={expected!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None
 for n in z.namelist():
  assert not Path(n).is_absolute() and ".." not in Path(n).parts
  p=root/n;p.parent.mkdir(parents=True,exist_ok=True);b=z.read(n)
  assert hashlib.sha256(b).hexdigest()==expected[n]
  with p.open("xb") as f:f.write(b)
python="/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python"
check="import sys;sys.path.insert(0,"+repr(str(root/"code"))+");import gw_common;gw_common.paths();import engine,common;assert callable(engine.require);assert common.__file__==str(gw_common.RUN/'b_score_aligned_package_v4/common.py');print(common.__file__)"
probe=subprocess.run([python,"-c",check],env=dict(os.environ,CUDA_VISIBLE_DEVICES="",PYTHONDONTWRITEBYTECODE="1"),capture_output=True,text=True,check=True)
with (root/"namespace_acceptance.json").open("x") as f:json.dump({{"status":"PASS_ORIGINAL_ENGINE_COMMON_NAMESPACE_RESTORED","original_common":probe.stdout.strip(),"model_calls":0}},f)
indices=subprocess.check_output(["nvidia-smi","--query-gpu=index","--format=csv,noheader,nounits"],text=True).splitlines();assert len(indices)==1
env=dict(os.environ,CUDA_VISIBLE_DEVICES=indices[0].strip(),PYTHONUNBUFFERED="1",PYTHONDONTWRITEBYTECODE="1")
command=[python,str(root/"code/recover.py")]
with (root/"chain_launch_claim.json").open("x") as f:json.dump({{"command":command,"CUDA_VISIBLE_DEVICES":env["CUDA_VISIBLE_DEVICES"]}},f)
with (root/"chain.log").open("x") as log:p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
out={{"root":str(root),"pid":p.pid,"command":command,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"member_SHA_CRC_passed":True,"namespace_check_passed":True}}
with (root/"chain_launch.json").open("x") as f:json.dump(out,f)
print(json.dumps(out))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes',
        'aic-inspur-home','python3','-'],input=script,text=True,encoding='utf-8',capture_output=True,check=True)
    result=json.loads(r.stdout)
    if result['sha256']!=digest or result['bytes']!=len(raw):raise ValueError('recovery packet mismatch')
    with (REPORT/'recovery_deployment_01.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result))

if __name__=='__main__':main()
