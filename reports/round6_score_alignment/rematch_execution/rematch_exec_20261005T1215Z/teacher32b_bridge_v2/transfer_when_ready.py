"""Once-only direct teacher asset delivery; existing frozen Z finishes intact."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import time
import hashlib

HERE=Path(__file__).resolve().parent
DOWNLOAD=HERE.parent/'teacher32b_prepare_v1'
REMOTE='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def utc():return datetime.now(timezone.utc).isoformat()


def write(name,value):
    p=HERE/name;t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');t.replace(p)


def remote(code,timeout=180):
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','aic-inspur-home',PY+' -B -'],
          input=code,text=True,encoding='utf-8',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if result.returncode:raise RuntimeError('direct SSH operation failed; diagnostics retained in transfer log')
    return json.loads(result.stdout)


def main():
    import msvcrt
    lock=(HERE/'transfer.lock').open('a+b');lock.seek(0)
    if not lock.read(1):lock.write(b'1');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    with (HERE/'transfer_registration.json').open('x',encoding='utf-8') as f:
        json.dump(dict(pid=os.getpid(),utc=utc(),Mac_used=False,project_disk_limit_bytes=None,
             route='DIRECT_WINDOWS_LINUX',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),f)
    start=time.monotonic();errors=0
    try:
        while True:
            if time.monotonic()-start>3*86400:raise TimeoutError('registered preparation wait expired')
            p=DOWNLOAD/'download_completion.json'
            download=json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
            if download and download['status']!='PASS_ALL_PINNED_TEACHER_WEIGHTS_DOWNLOADED':
                raise RuntimeError('pinned weight download STOP; preserved without transfer')
            try:
                state=remote("from pathlib import Path\nimport json,shutil\nr=Path("+repr(REMOTE)+")\np=r/'next_round_v1/completion.json'\nb=r/'teacher32b_runtime_v2/runtime_build_completion.json'\nprint(json.dumps({'Z_completion':json.loads(p.read_text()) if p.exists() else None,'runtime':json.loads(b.read_text()) if b.exists() else None,'disk_free_bytes':shutil.disk_usage(r).free}))\n")
                errors=0
            except Exception:
                errors+=1
                if errors>10:raise RuntimeError('bounded direct SSH preparation queries exhausted')
                write('transfer_progress.json',dict(status='WAITING_DIRECT_SSH_RETRY',utc=utc(),pid=os.getpid(),errors=errors,Mac_used=False))
                time.sleep(30);continue
            runtime=state['runtime'];z=state['Z_completion']
            if runtime and runtime['status']!='PASS_PINNED_CUDA_RUNTIME_BUILD_ONLY':
                raise RuntimeError('runtime build STOP; no model inference attempted')
            # This protects the byte-locked Z controller, not a new resource quota.
            # New teacher stages have no 80/51 GiB/Mac reservation gate.
            if download and z and runtime:
                break
            write('transfer_progress.json',dict(status='WAITING_DOWNLOAD_AND_FROZEN_Z_COMPLETION',utc=utc(),pid=os.getpid(),
                 weight_download_complete=download is not None,Z_complete=z is not None,runtime_complete=runtime is not None,
                 project_disk_limit_bytes=None,Mac_used=False))
            time.sleep(30)
        recipe=json.loads((DOWNLOAD/'recipe.json').read_text(encoding='utf-8'))
        if state['disk_free_bytes']<sum(x['size_bytes'] for x in recipe['files']):
            raise RuntimeError('actual Linux filesystem cannot cover teacher artifacts')
        receipts=[]
        for row in recipe['files']:
            source=DOWNLOAD/'assets'/row['path'];target=REMOTE+'/teacher32b_prepare_v1/assets/'+row['path']
            assert source.is_file() and source.stat().st_size==row['size_bytes']
            remote("from pathlib import Path\nimport json\np=Path("+repr(target)+")\np.parent.mkdir(exist_ok=True)\nassert not p.exists(),'target already exists; do not replace it'\nprint(json.dumps({'target_ready':True}))\n")
            write('transfer_progress.json',dict(status='COPYING_PINNED_TEACHER_TO_LINUX',utc=utc(),pid=os.getpid(),file=row['path'],
                 project_disk_limit_bytes=None,Mac_used=False))
            # A single owned partial survives an interrupted copy. Never weaken
            # host verification or silently switch hosts/routes.
            copied=subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=10',str(source),
                         'aic-inspur-home:'+target+'.incomplete'],timeout=24*3600)
            if copied.returncode:raise RuntimeError('direct teacher transfer failed; partial preserved')
            receipt=remote("from pathlib import Path\nimport json,hashlib\np=Path("+repr(target)+")\na=Path(str(p)+'.incomplete')\nh=hashlib.sha256()\nwith a.open('rb') as f:\n for b in iter(lambda:f.read(8*2**20),b''):h.update(b)\nassert a.stat().st_size=="+str(row['size_bytes'])+"\nassert h.hexdigest()=="+repr(row['lfs_sha256'])+"\na.replace(p)\nprint(json.dumps({'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest(),'status':'PASS_TRANSFER_BYTES_SHA256'}))\n",timeout=3600)
            receipts.append(receipt)
        result=dict(status='PASS_TEACHER_ASSETS_READY_ON_LINUX',utc=utc(),pid=os.getpid(),files=receipts,
             runtime_revision=runtime['source_revision'],Mac_used=False,project_disk_limit_bytes=None,
             GPU_probe_started=False,labels_generated=False,T_training_started=False,
             next_action='Real CUDA video/teacher receipt probe under shared GPU lock; then validate new labels before T')
        remote("from pathlib import Path\nimport json\np=Path("+repr(REMOTE+'/teacher32b_prepare_v1/assets_ready_completion.json')+")\np.write_text("+repr(json.dumps(result,ensure_ascii=False,indent=2)+'\n')+")\nprint(json.dumps({'written':True}))\n")
    except Exception as exc:
        result=dict(status='STOP_TEACHER_ASSET_PREPARATION',utc=utc(),pid=os.getpid(),failure_type=type(exc).__name__,
                  failure=str(exc),partials_preserved=True,Mac_used=False)
    write('transfer_completion.json',result);write('transfer_progress.json',result)
    return 0 if result['status'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
