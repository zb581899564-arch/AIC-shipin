"""Deploy one small cached-metadata/code packet and claim one Linux research chain."""
import base64
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPORT = PROJECT/'reports/gnmc_width_iteration_20261013_v1'
OLD = PROJECT/'reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z'

def main():
    if (REPORT/'deployment.json').exists(): raise ValueError('deployment is not repeated')
    controls = {}
    # Reuse the existing verified author annotation bytes, without choosing or scoring any photo locally.
    for name in ['validation.json','test.json']:
        controls['control/'+name] = (OLD/'pilot/gnmc/selected/raw_metadata'/name).read_bytes()
    for name in ['LICENSE.txt','README.md']:
        controls['control/'+name] = (OLD/'pilot/gnmc/selected/raw_metadata'/name).read_bytes()
    rows = [json.loads(s) for s in (OLD/'pilot_manifest.jsonl').read_text(encoding='utf-8').splitlines() if s]
    protected = {'filenames':[r['original_filename'] for r in rows],
        'media_sha256':[r['media_sha256'] for r in rows],
        'exposure':'all old eight GNMC references exposed; not fresh confirmation',
        'full_original_source_isolation':'UNKNOWN'}
    controls['control/protected.json'] = json.dumps(protected,ensure_ascii=False).encode()
    # Header inventory is control metadata from the already verified archive, not a new media extraction.
    with zipfile.ZipFile(OLD/'pilot/gnmc/GNMC.zip') as z:
        idx = {i.filename:{'name':i.filename,'header_offset':i.header_offset,'bytes':i.file_size,
            'compressed_bytes':i.compress_size,'compression':i.compress_type,'crc32':i.CRC}
            for i in z.infolist() if i.filename.startswith(('GNMC/validation/','GNMC/test/')) and i.filename.endswith('.jpeg')}
    controls['control/zip_index.json'] = json.dumps(idx,separators=(',',':')).encode()
    for name in ['protocol.json','purpose_reply.json','official_rule_check.json']:
        controls[name]=(REPORT/name).read_bytes()
    for p in HERE.glob('*.py'):
        if p.name != 'deploy.py': controls['code/'+p.name]=p.read_bytes()
    packet = io.BytesIO()
    with zipfile.ZipFile(packet,'w',zipfile.ZIP_DEFLATED) as z:
        for name,content in controls.items():z.writestr(name,content)
    raw=packet.getvalue();digest=hashlib.sha256(raw).hexdigest()
    if len(raw)>1048576: raise ValueError('control packet exceeds the declared small-transfer scope')
    REPORT.mkdir(exist_ok=True)
    (REPORT/'control_packet.zip').write_bytes(raw)
    data=base64.b64encode(raw).decode()
    script=f'''import base64,hashlib,io,json,os,shutil,socket,subprocess,zipfile
from pathlib import Path
assert socket.gethostname()=="inspur-NP5570M5"
root=Path("/home/inspur/aic_video_work/gnmc_width_iteration_20261013_v1")
if root.exists():raise ValueError("new root already exists; inspect it, never repeat deployment/launcher")
raw=base64.b64decode({data!r})
assert len(raw)=={len(raw)} and hashlib.sha256(raw).hexdigest()=={digest!r}
root.mkdir()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None
 for member in z.infolist():
  p=root/member.filename
  assert not Path(member.filename).is_absolute() and ".." not in Path(member.filename).parts
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open("xb") as f:f.write(z.read(member))
 with (root/"deployment.json").open("x") as f:json.dump({{"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"members":len(z.infolist()),"cached_author_metadata_reused":True}},f)
gpu=subprocess.check_output(["nvidia-smi","--query-gpu=index","--format=csv,noheader,nounits"],text=True).splitlines()
assert len(gpu)==1
env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu[0].strip(),PYTHONUNBUFFERED="1",PYTHONDONTWRITEBYTECODE="1")
command=["/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python",str(root/"code/controller.py")]
with (root/"chain_launch_claim.json").open("x") as f:json.dump({{"command":command,"CUDA_VISIBLE_DEVICES":env["CUDA_VISIBLE_DEVICES"]}},f)
with (root/"chain.log").open("x") as log:
 p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
with (root/"chain_launch.json").open("x") as f:json.dump({{"pid":p.pid,"command":command,"CUDA_VISIBLE_DEVICES":env["CUDA_VISIBLE_DEVICES"]}},f)
print(json.dumps({{"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"root":str(root),"pid":p.pid,"command":command}}))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes',
        'aic-inspur-home','python3','-'],input=script,text=True,encoding='utf-8',capture_output=True,check=True)
    receipt=json.loads(result.stdout)
    if receipt['bytes']!=len(raw) or receipt['sha256']!=digest:raise ValueError('deployment identity mismatch')
    with (REPORT/'deployment.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
