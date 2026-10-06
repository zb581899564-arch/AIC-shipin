"""Start the registered CPU metadata repair and PTS scan, preserving logs."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL=RUN/'controller'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
if __name__=='__main__':
    command=[PY,'-B','-u',str(CTRL/'run_m0_repair.py')]
    with (CTRL/'m0_repair_01.launcher.log').open('x') as log:
        process=subprocess.Popen(command,cwd=RUN,stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt={'task':'m0_repair_01','pid':process.pid,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'command':command,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'gpu_used':False,'models_run':False,'images_exported_or_displayed':False}
    with (CTRL/'m0_repair_01.launch.json').open('x') as output:
        json.dump(receipt,output,indent=2)
        output.write('\n')
    print(json.dumps(receipt),flush=True)
