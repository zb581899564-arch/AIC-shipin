"""Single owned controller launch, without signalling any previous job."""
from autopilot_common import *
import fcntl
import socket
import subprocess


def main():
    require(socket.gethostname() == 'inspur-NP5570M5', 'wrong launch host')
    lock=(HERE/'launch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not (HERE/'start_receipt.json').exists() and not (HERE/'registration.json').exists(), 'already launched; inspect real command instead')
    verify()
    command=[str(PY),'-B',str(HERE/'controller.py')]
    with (HERE/'controller.log').open('x') as log:
        child=subprocess.Popen(command,cwd=RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(HERE/'start_receipt.json',dict(status='LAUNCHED_NOT_ACCEPTED',utc=utc(),pid=child.pid,pgid=child.pid,
        command=command,source_lock_sha256=sha(HERE/'source_lock.json'), automatic_return=False,uploaded=False),fresh=True)
    print(json.dumps(read(HERE/'start_receipt.json')),flush=True)


if __name__ == '__main__': main()
