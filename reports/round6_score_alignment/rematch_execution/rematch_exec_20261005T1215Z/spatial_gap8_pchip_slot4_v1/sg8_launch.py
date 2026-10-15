"""Single background controller, only after complete frozen G0 admission."""
import fcntl
import os
import socket
import subprocess
from sg8_common import HERE,RUN,PY,read,sha,save,require,verify,utc


def main():
    require(socket.gethostname()=='inspur-NP5570M5','wrong host')
    lock=(HERE/'launch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not (HERE/'start.json').exists() and not (HERE/'registration.json').exists(),'single launcher already used')
    verify()
    preflight=read(HERE/'preflight.json')
    require(preflight['status']=='PASS_FROZEN_SG8_NATIVE_G0_AND_ALL_BOUND_BYTES' and
        preflight['source_lock_sha256']==sha(HERE/'source_lock.json'),'frozen G0 preflight missing')
    env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        HF_HOME=str(RUN/'cache/hf'),XDG_CACHE_HOME=str(RUN/'cache'),TMPDIR=str(RUN/'tmp'))
    command=[PY,'-B',str(HERE/'sg8_controller.py')]
    with (HERE/'controller.log').open('xb') as log:
        p=subprocess.Popen(command,cwd=HERE,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    value=dict(utc=utc(),pid=p.pid,pgid=p.pid,full_command=command,source_lock_sha256=sha(HERE/'source_lock.json'),
        single_launcher=True,startup_is_not_model_call_or_quality=True)
    save(HERE/'start.json',value);print(value,flush=True)


if __name__=='__main__':main()
