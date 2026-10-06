"""Launch an exclusive registered A-PTS job, using the existing shared ledger."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL = RUN/'controller'
PYTHON = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=['a_pts_nontest_02','a_pts_temporal_01','a_pts_space_01'])
    args = parser.parse_args()
    admission_path = CTRL/(args.name+'.admission.json')
    admission = json.loads(admission_path.read_text())
    if admission.get('authorized') is not True or admission.get('budget_runner_required') is not True:
        raise RuntimeError('no complete A-PTS resource admission')
    command = [PYTHON,'-B','-u',str(CTRL/'gpu_run.py'),
        '--name','rematch_'+args.name,'--max-seconds',str(admission['single_job_max_seconds']),
        '--planned-output-bytes',str(admission['planned_output_bytes']),
        '--capacity-reason',admission['capacity_reason'],'--queue-seconds','1800','--',
        PYTHON,'-B','-u',str(CTRL/'execute_registered_a_pts.py'),'--admission',str(admission_path)]
    with (CTRL/(args.name+'.launcher.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=RUN, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = {'task': args.name, 'pid': child.pid,
        'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'command':command,
        'admission_sha256':hashlib.sha256(admission_path.read_bytes()).hexdigest(),
        'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'competition_upload_authorized':False}
    with (CTRL/(args.name+'.launch.json')).open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print(json.dumps(receipt), flush=True)
