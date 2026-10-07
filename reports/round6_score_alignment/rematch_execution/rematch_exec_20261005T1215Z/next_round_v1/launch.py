"""One background continuation, no repeated launcher and no website upload."""
from common import *
import os
import subprocess
import datetime as dt

verify()
require(not (HERE/'launch.json').exists() and not (HERE/'completion.json').exists(),'registered continuation already exists')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
with (HERE/'controller.log').open('x') as stream:
    p=subprocess.Popen([sys.executable,'-B',str(HERE/'controller.py')],cwd=RUN,stdin=subprocess.DEVNULL,
        stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=env)
write(HERE/'launch.json',dict(pid=p.pid,utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_lock_sha256=sha(HERE/'source_lock.json'),uploaded=False))
print(json.dumps(read(HERE/'launch.json')),flush=True)
