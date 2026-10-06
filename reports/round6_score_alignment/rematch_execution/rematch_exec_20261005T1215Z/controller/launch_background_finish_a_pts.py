"""Start one detached CPU supervisor for the already registered A pipeline."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL = RUN/'controller'
if __name__ == '__main__':
    hashes_path = CTRL/'background_pipeline_helpers.json'
    hashes = json.loads(hashes_path.read_text())
    for name,digest in hashes['files'].items():
        if hashlib.sha256((CTRL/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('registered helper changed: '+name)
    record = CTRL/'background_finish.launch.json'
    if record.exists() or (CTRL/'a_pts_pipeline_completion.json').exists():
        raise RuntimeError('background continuation already exists; read its status')
    command = [sys.executable,'-B','-u',str(CTRL/'finish_registered_a_pts.py'),
        '--helpers-sha256',hashlib.sha256(hashes_path.read_bytes()).hexdigest()]
    with (CTRL/'background_finish.log').open('x') as log:
        child = subprocess.Popen(command,cwd=RUN,stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    result = dict(pid=child.pid,command=command,competition_upload_authorized=False,
        scope='existing temporal completion then evidence/resource-gated space, compose and package only')
    with record.open('x') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result),flush=True)
