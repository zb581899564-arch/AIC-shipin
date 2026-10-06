"""Launch one locked continuation; no stage is rerun."""
import hashlib,json,subprocess,sys
from pathlib import Path
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL=RUN/'controller'
lock=CTRL/'format_recovery_finish_lock.json'
expected=hashlib.sha256(lock.read_bytes()).hexdigest()
for name,digest in json.loads(lock.read_text())['files'].items():
    if hashlib.sha256((CTRL/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('finish helper identity changed')
if (CTRL/'format_finish.registration.json').exists() or (CTRL/'format_finish.launch.json').exists():
    raise RuntimeError('continuation already launched; no duplication')
with (CTRL/'format_finish.launcher.log').open('x') as log:
    proc=subprocess.Popen([sys.executable,'-B','-u',str(CTRL/'finish_format_recovery.py'),
        '--expected-lock-sha256',expected],cwd=RUN,stdin=subprocess.DEVNULL,stdout=log,
        stderr=subprocess.STDOUT,start_new_session=True)
with (CTRL/'format_finish.launch.json').open('x') as handle:
    json.dump(dict(pid=proc.pid,lock_sha256=expected,competition_upload_authorized=False),handle,indent=2)
print(json.dumps(dict(pid=proc.pid,lock_sha256=expected)))
