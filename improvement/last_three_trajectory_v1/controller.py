"""Run each newly registered CPU stage once; no old launcher or model calls."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import time
import traceback
from common import ROOT, PY, save_new


def stage(name, script):
    if datetime.now(timezone.utc) >= datetime.fromisoformat('2026-10-24T03:20:00+00:00'):
        raise TimeoutError('Preserve at least40minutes for transfer/submission before noon')
    command=[str(PY),'-u','-B',str(ROOT/'code'/script)]
    started=time.monotonic()
    with (ROOT/(name+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        ticks=Path('/proc/'+str(process.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
        save_new(ROOT/(name+'_launch.json'),dict(pid=process.pid,start_ticks=ticks,argv=command))
        code=process.wait(timeout=3600)
    save_new(ROOT/(name+'_terminal.json'),dict(exit_code=code,wall_seconds=time.monotonic()-started))
    if code:
        raise RuntimeError(name+' failed naturally; preserve raw, no implicit retry')


def main():
    save_new(ROOT/'controller_claim.json',dict(pid=os.getpid(),started_at=datetime.now(timezone.utc).isoformat()))
    try:
        for name,script in [('targeted_tests','test_curves.py'),('prepare','prepare.py'),('produce','produce.py'),('finalize','finalize.py')]:
            stage(name,script)
    except Exception:
        save_new(ROOT/'failure.json',dict(traceback=traceback.format_exc(),old_successes_preserved=True))
        raise


if __name__ == '__main__':
    main()
