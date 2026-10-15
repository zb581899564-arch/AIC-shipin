import os,json,socket,subprocess,datetime,hashlib
from pathlib import Path
B=Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1')
assert socket.gethostname()=='inspur-NP5570M5'
assert not (B/'media_01/completion.json').exists()
assert len(list((B/'media_01').glob('*.download.json')))==0
assert len(list((B/'media_01').glob('*.partial')))==0
claim=dict(status='EXPLICIT_RESUME_TRANSIENT_DNS_NO_SUCCESS_REPEATED',pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),recovery_sha256=hashlib.sha256((B/'download_dns_recovery_01.json').read_bytes()).hexdigest(),original_failure_sha256=hashlib.sha256((B/'media_01/failure.json').read_bytes()).hexdigest(),argv=['/usr/bin/python3','-u',str(B/'code/download_entry.py'),'--resume'],new_model_calls=0)
with (B/'download_resume_claim_01.json').open('x') as f:json.dump(claim,f,indent=2)
with (B/'download_resume_01.log').open('xb') as log:
 p=subprocess.Popen(claim['argv'],cwd=str(B/'code'),stdout=log,stderr=subprocess.STDOUT)
 with (B/'download_resume_child_01.json').open('x') as f:json.dump(dict(pid=p.pid,ppid=os.getpid(),argv=claim['argv']),f,indent=2)
 rc=p.wait()
completion=dict(status='COMPLETED_RESUME' if rc==0 else 'FAILED_RESUME_KEEP_ALL',exit_code=rc,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_model_calls=0,original_failure_retained=(B/'media_01/failure.json').exists())
with (B/'download_resume_terminal_01.json').open('x') as f:json.dump(completion,f,indent=2)
raise SystemExit(rc)
