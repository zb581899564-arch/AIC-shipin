"""Concrete media-only upload bundle; creation never uploads or trains."""
from pathlib import Path
import json,zipfile,hashlib,subprocess
HERE=Path(__file__).resolve().parent/'slot6_silver24_v1'
plan=json.loads((HERE/'source_window_plan.json').read_text())
out=HERE/'SLOT6_NATIVE_SOURCE_INPUTS.zip';assert not out.exists()
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_STORED) as z:
    z.write(HERE/'source_window_plan.json','source_window_plan.json')
    for r in plan['media']:
        p=Path(r['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
        z.write(p,'media/'+p.name);z.write(p.parent/'native_pts.npz','clocks/'+r['source_id']+'.npz')
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None and len(z.namelist())==25
receipt=dict(status='LOCAL_REVIEWABLE_MEDIA_PACKAGE_NOT_UPLOADED_NOT_TRAINING_READY',path=str(out),bytes=out.stat().st_size,
    sha256=hashlib.sha256(out.read_bytes()).hexdigest(),native_media_bytes=plan['media_bytes'],files=25,
    direction='Windows -> Linux via live online Mac SSH jump; no Mac payload landing',
    maximum_two_network_leg_payload_bytes=out.stat().st_size*2,transfer_authorized=False,uploaded=False,
    description='12 native source media plus 12 exact PTS arrays and public-rule source/window plan; no model or final silver labels')
with (HERE/'transfer_package_receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
ids=[x['source_id'] for x in plan['media']]
code='''import json, pathlib, subprocess, platform, shutil
ids=IDS
root=pathlib.Path('/home/inspur/aic_video_work/datasets')
names={x+'.mp4' for x in ids}; found=[]
for p in root.rglob('*.mp4'):
 if p.name in names:found.append(dict(path=str(p),bytes=p.stat().st_size))
out=dict(host=platform.node(),machine=platform.machine(),found_by_original_filename=found,not_semantic_or_reencoded_search=True,
 disk_free_bytes=shutil.disk_usage('/home/inspur/aic_video_work').free,
 gpu=subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total','--format=csv,noheader'],capture_output=True,text=True).stdout,
 processes=subprocess.run(['ps','-eo','pid,ppid,pgid,comm,%cpu,%mem'],capture_output=True,text=True).stdout)
print(json.dumps(out))
'''.replace('IDS',repr(ids))
proc=subprocess.run(['ssh','aic-inspur-home','python3','-'],input=code,encoding='utf-8',capture_output=True,timeout=60)
with (HERE/'linux_presence_resources_01.json').open('x',encoding='utf-8') as f:json.dump(dict(exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr),f,ensure_ascii=False,indent=2)
assert proc.returncode==0
actual=json.loads(proc.stdout);assert actual['host']=='inspur-NP5570M5' and actual['machine']=='x86_64'
print(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in actual.items() if k!='processes'},ensure_ascii=False,indent=2))
