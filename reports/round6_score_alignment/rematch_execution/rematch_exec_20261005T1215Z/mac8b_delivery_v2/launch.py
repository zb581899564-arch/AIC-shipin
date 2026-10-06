"""Exclusive detached continuation registration; no duplicate runs."""
from runtime import *
import subprocess
import datetime as dt

verify()
require(not (HERE/'launch.json').exists() and not (HERE/'continuation_registration.json').exists(),'continuation already registered')
with (HERE/'controller.log').open('x') as log:
    process=subprocess.Popen([sys.executable,'-B',str(HERE/'controller.py')],cwd=RUN,stdin=subprocess.DEVNULL,
        stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
write(HERE/'launch.json',dict(pid=process.pid,utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_lock_sha256=sha(HERE/'source_lock.json'),
    user_request='mac的开发测评和提交包尽早完成',automatic_website_upload=False))
print(json.dumps(read(HERE/'launch.json')))
