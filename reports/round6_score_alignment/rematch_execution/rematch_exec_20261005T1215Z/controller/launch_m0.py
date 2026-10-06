import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
ROOT=Path('/home/inspur/aic_video_work')
PYTHON=str(ROOT/'env/qwen3vl_isolated_20260910/bin/python')
if __name__=='__main__':
    script=RUN/'controller/run_m0.py'
    # Uncompressed video occupancy from ZIP metadata; no media/JSONL content read.
    import shutil
    import zipfile
    archives=list((ROOT/'round6_score_alignment/rematch_intake/rematch_download_20261005T041135Z/archive').glob('*.zip'))
    if len(archives)!=1:
        raise RuntimeError('ambiguous archive')
    with zipfile.ZipFile(archives[0]) as z:
        expected=sum(i.file_size for i in z.infolist() if i.filename.lower().endswith('.mp4') and not i.filename.startswith('__MACOSX/'))
    reserve=expected+256*2**20
    current=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    # Include still-unwritten model shards when checking simultaneous occupancy.
    model_state=json.loads((RUN/'controller/model_download_v2_status.json').read_text())
    model_remaining=max(0,model_state['expected_model_bytes']-sum(f['bytes'] for f in model_state['completed']))
    if current+reserve+model_remaining>80*2**30 or shutil.disk_usage(ROOT).free<reserve+model_remaining:
        raise RuntimeError('simultaneous preparation occupancy/capacity would exceed authorized boundary')
    with (RUN/'controller/m0_426_02.launcher.log').open('x') as log:
        proc=subprocess.Popen([PYTHON,'-B','-u',str(script)],cwd=RUN,stdout=log,stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,start_new_session=True)
    receipt=dict(pid=proc.pid,started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),GPU_used=False,
        expected_video_uncompressed_bytes=expected,predicted_simultaneous_occupied_bytes=current+reserve+model_remaining,
        note='metadata and automatic source-identity scan only; no images shown, no inference/upload')
    with (RUN/'controller/m0_426_02.launch.json').open('x') as out:
        json.dump(receipt,out,indent=2)
    print(json.dumps(receipt),flush=True)
