"""Exclusive detached launch through the unchanged shared resource runner."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
from admit_a_pts_stage import sha,read,require

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL = RUN/'controller'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['probe','recover','schedule','space'])
    args = parser.parse_args()
    admission_path = CTRL/('format_'+args.phase+'_01.admission.json')
    a = read(admission_path)
    require(a['authorized'] is True and a['phase'] == args.phase,'wrong admitted phase')
    command = [sys.executable,'-B','-u',str(CTRL/'gpu_run.py'),'--name','rematch_format_'+args.phase+'_01',
        '--max-seconds',str(a['single_job_max_seconds']),'--planned-output-bytes',str(a['planned_output_bytes']),
        '--capacity-reason',a['capacity_reason'],'--queue-seconds','1800','--',sys.executable,'-B','-u',
        str(CTRL/'execute_format_recovery_stage.py'),'--admission',str(admission_path)]
    with (CTRL/('format_'+args.phase+'_01.launcher.log')).open('x') as log:
        proc = subprocess.Popen(command,cwd=RUN,stdin=subprocess.DEVNULL,stdout=log,
            stderr=subprocess.STDOUT,start_new_session=True)
    record = dict(pid=proc.pid,phase=args.phase,started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        admission_sha256=sha(admission_path),command=command,competition_upload_authorized=False)
    with (CTRL/('format_'+args.phase+'_01.launch.json')).open('x') as stream:
        json.dump(record,stream,indent=2)
        stream.write('\n')
    print(json.dumps(record),flush=True)
