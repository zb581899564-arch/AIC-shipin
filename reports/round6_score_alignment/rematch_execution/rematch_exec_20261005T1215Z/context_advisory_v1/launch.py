"""One Linux-owned session, never repeat or replace an existing launcher."""
import datetime as dt
import fcntl
import json
import os
import socket
import subprocess
from pathlib import Path
import runtime as rt
import experiment as ex
import context_contract as cc


def main():
    cc.require(socket.gethostname() == 'inspur-NP5570M5', 'wrong launch host')
    guard = (rt.HERE/'launch.lock').open('a')
    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cc.require(not (rt.HERE/'start.json').exists() and not (rt.HERE/'registration.json').exists(), 'already started; never relaunch')
    ex.verify()
    cc.require(ex.read(rt.HERE/'preflight.json')['frozen_binding_verified'] is True, 'actual frozen CPU admission missing')
    command = ['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python', '-B', str(rt.HERE/'controller.py')]
    env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        HF_HOME=str(rt.RUN/'cache/hf'), XDG_CACHE_HOME=str(rt.RUN/'cache'), TMPDIR=str(rt.RUN/'tmp'))
    with (rt.HERE/'controller.log').open('xb') as output:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
            cwd=rt.RUN, env=env, start_new_session=True)
    receipt = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(), 'pid':process.pid, 'pgid':process.pid,
        'full_command':command, 'source_lock_sha256':ex.sha(rt.HERE/'source_lock.json'),
        'single_launcher':True, 'startup_is_not_model_or_ZIP_acceptance':True}
    rt.raw_write(rt.HERE/'start.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__': main()
