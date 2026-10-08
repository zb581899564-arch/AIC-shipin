"""One Linux background launch, never overwrite or restart."""
import fcntl
import os
import socket
import subprocess
import nd_common as c


def main():
    c.require(socket.gethostname()=='inspur-NP5570M5','wrong host')
    lock=(c.HERE/'launch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    c.require(not (c.HERE/'start.json').exists() and not (c.HERE/'registration.json').exists(),'already launched')
    c.verify()
    c.require(c.read(c.HERE/'preflight.json')['status']=='PASS_FROZEN_NESTED_DENSITY_CPU_BINDING','frozen CPU preflight')
    env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        HF_HOME=str(c.RUN/'cache/hf'),XDG_CACHE_HOME=str(c.RUN/'cache'),TMPDIR=str(c.RUN/'tmp'))
    command=[c.PY,'-B',str(c.HERE/'controller.py')]
    with (c.HERE/'controller.log').open('xb') as log:
        process=subprocess.Popen(command,cwd=c.RUN,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt={'utc':c.utc(),'pid':process.pid,'pgid':process.pid,'full_command':command,
        'source_lock_sha256':c.sha(c.HERE/'source_lock.json'),'single_launcher':True,'startup_is_not_inference_or_quality':True}
    c.save(c.HERE/'start.json',receipt);print(receipt,flush=True)


if __name__=='__main__':main()
