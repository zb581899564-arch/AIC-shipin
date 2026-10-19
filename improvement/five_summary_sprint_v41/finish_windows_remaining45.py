"""Explicit remaining delivery leg after original foreground tool handle vanished; SSH control and final ZIPs only.

Not a recurring task. No intermediate evidence/raw/media download or model retry.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import subprocess
import time
import traceback
import zipfile

WORK=Path(__file__).resolve().parents[2]
REPORT=WORK/'reports/bottleneck_24h_20261019_v1'
REMOTE='/home/inspur/aic_video_work/five_summary_sprint_20261019_v41'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ConnectionAttempts=1',
     '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-tailscale','python3 -']
DEADLINE=datetime.fromisoformat('2026-10-19T15:52:37+00:00')


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)


def remote(script):
    result=subprocess.run(SSH,input=script,text=True,capture_output=True,encoding='utf-8',timeout=40)
    require(result.returncode==0,'Strict SSH final-delivery control failed: '+result.stderr.strip())
    return json.loads(result.stdout.strip().splitlines()[-1])


def inspect():
    return remote(r'''
import json,pathlib,datetime
R=pathlib.Path('__ROOT__')
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'WAIT_REGISTERED_FINITE_CHAIN'}
ready=R/'delivery_ready43.json'
if ready.exists():
 d=json.loads(ready.read_text());out={'status':'READY','ready':{k:d[k] for k in ['accepted_packages','requested_packages','packages','pending','official_effect','protected40_47_unchanged']}}
else:
 for name in ['completion_chain43_failure.json','formal_chain_failure41.json']:
  p=R/name
  if p.exists():
   d=json.loads(p.read_text());out={'status':'FAILED','failure_path':str(p),'error':d['error']};break
print(json.dumps(out))
'''.replace('__ROOT__',REMOTE))


def validate(path,item):
    require(path.stat().st_size==item['zip']['bytes'] and sha(path)==item['zip']['sha256'],'Final Windows ZIP size/SHA differs from Linux')
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None,'Final archive single JSONL/CRC')
        content=archive.read('predictions.jsonl')
    require(hashlib.sha256(content).hexdigest()==item['member_sha256'],'Final member SHA differs from Linux')
    rows=[json.loads(x) for x in content.splitlines() if x.strip()]
    require(len(rows)==426 and {r['video_id'] for r in rows}=={str(i) for i in range(426)},'Final426 complete source index')
    frames=0
    for row in rows:
        require(abs(row['model_params_b']-item['actual_pipeline_parameters']/1e9)<1e-12 and row['model_params_b']<=9,'Actual per-policy model parameters')
        seen=set()
        for p in row['predictions']:
            require(type(p['frame']) is int and p['frame']>=0 and p['frame'] not in seen,'Final native frame shape/dedup')
            seen.add(p['frame']);box=p['bboxes']
            require(len(box)==3 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in box) and box[0]>=0 and box[1]>=0 and box[2]>0,'Final box numeric legality')
        frames+=len(seen)
    require(frames==item['frames'],'Final frame count differs from Linux package')
    return dict(policy=item['policy'],name=item['name'],path=str(path),bytes=path.stat().st_size,sha256=sha(path),
        member_sha256=item['member_sha256'],frames=frames,added_frames=item['added_frames'],removed_frames=item['removed_frames'],
        actual_pipeline_parameters=item['actual_pipeline_parameters'],records=426,CRC=True,Windows_Linux_consistent=True,
        official_effect='UNKNOWN',independent11strict_Linux=item['independent11strict'])


def run():
    require(not (REPORT/'windows_delivery_leg45_claim.json').exists(),'Existing finite delivery leg; inspect instead of duplicate')
    save(REPORT/'windows_delivery_leg45_claim.json',dict(pid=os.getpid(),command=[sys.executable,*sys.argv],start_utc=datetime.now(timezone.utc).isoformat(),
        bounded_until_utc=DEADLINE.isoformat(),remote_root=REMOTE,final_ZIPs_only=True,new_automation=False,new_goal=False,remaining_delivery_registration='windows_delivery_remaining_registration45.json'))
    while True:
        require(datetime.now(timezone.utc)<DEADLINE,'Original final delivery boundary reached')
        status=inspect()
        if status['status']=='FAILED':raise ValueError(status['error']+'; '+status['failure_path'])
        if status['status']=='READY':break
        time.sleep(min(45,max(.1,(DEADLINE-datetime.now(timezone.utc)).total_seconds())))
    ready=status['ready'];receipts=[]
    for item in sorted(ready['packages'],key=lambda v:v['policy']):
        require(datetime.now(timezone.utc)<DEADLINE,'Final transfer start beyond original boundary')
        directory=WORK/'deliveries'/('FIVE_SUMMARY_%02d_%s_20261019'%(item['policy'],item['name']))
        directory.mkdir(exist_ok=True)
        target=directory/Path(item['zip']['path']).name;partial=directory/(target.name+'.partial')
        if target.exists():
            receipts.append(validate(target,item));continue
        if partial.exists():
            validate(partial,item) # A complete previous transfer may be adopted, never blindly repeated.
        else:
            command=['scp','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ConnectionAttempts=1',
                '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',
                'aic-inspur-tailscale:'+item['zip']['path'],str(partial)]
            result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=180)
            require(partial.exists(),'Final ZIP transfer produced no file: '+result.stderr.strip())
            # A late transport error does not justify repeating a fully received/hash-accepted ZIP.
            validate(partial,item)
        partial.rename(target);receipts.append(validate(target,item))
    completion=dict(status='COMPLETE_FIVE_WINDOWS_DELIVERED' if len(receipts)==5 else 'PARTIAL_DISTINCT_ACCEPTED_WINDOWS_DELIVERY',
        requested_packages=5,delivered_packages=len(receipts),packages=receipts,pending=ready['pending'],
        protected40_47_unchanged=ready['protected40_47_unchanged'],official_effect='UNKNOWN',website_submitted=False,
        semantic_quality_review=False,external_new_confirmation=False,utc=datetime.now(timezone.utc).isoformat())
    save(REPORT/'five_sprint_windows_delivery43.json',completion)
    payload=json.dumps(completion,ensure_ascii=False)
    script='import pathlib,json\np=pathlib.Path('+repr(REMOTE+'/windows_delivery_receipt43.json')+')\nassert not p.exists()\nwith p.open("x") as f:json.dump(json.loads('+repr(payload)+'),f,ensure_ascii=False,indent=2)\nprint(json.dumps({"status":"WINDOWS_FINAL_DELIVERY_RECEIPT_ACCEPTED"}))\n'
    remote(script)
    index=['# 今晚五候选交付','',completion['status'],'','40.47原包保持不动。以下仅工程验收通过，官方效果UNKNOWN；不是五个独立模型。','']
    for row in receipts:index.append(f"- {row['policy']} {row['name']}：[{Path(row['path']).name}](<{Path(row['path']).as_posix()}>)；{row['frames']}帧，增{row['added_frames']}/删{row['removed_frames']}。")
    (REPORT/'FIVE_PACKAGE_DELIVERY43.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    statepath=REPORT/'current_state.json';state=json.loads(statepath.read_text(encoding='utf-8'))
    state.update(stage=completion['status'],new_packages=len(receipts),last_update_utc=completion['utc'],next='Read five_sprint_windows_delivery43.json and FIVE_PACKAGE_DELIVERY43.md. No automatic website submission or further experiments.')
    state.setdefault('five_summary_sprint41',{}).update(stage=completion['status'],new_packages=len(receipts),Windows_delivery_receipt='five_sprint_windows_delivery43.json')
    statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(completion,ensure_ascii=False),flush=True)


if __name__=='__main__':
    try:run()
    except BaseException as error:
        target=REPORT/'windows_delivery_leg45_failure.json'
        if not target.exists():save(target,dict(error=repr(error),traceback=traceback.format_exc(),
            automatic_retry=False,preserve_all_received_files=True,utc=datetime.now(timezone.utc).isoformat()))
        raise
