"""Exclusive one-shot Linux background controller, no automatic file return."""
from common import *
import subprocess


def main():
    verify()
    require(not (HERE/'launch.json').exists() and not (HERE/'completion.json').exists(), 'B2 launcher already used')
    claim=os.open(HERE/'launch.claim',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.write(claim,json.dumps(dict(launcher_pid=os.getpid(),utc=utc(),source_lock_sha256=sha(HERE/'source_lock.json'))).encode())
    os.close(claim)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',PYTHONFAULTHANDLER='1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',PYTHONNOUSERSITE='1',
        HF_HOME=str(RUN/'cache/hf'),XDG_CACHE_HOME=str(RUN/'cache'),TMPDIR=str(RUN/'tmp'),
        CUDA_CACHE_PATH=str(RUN/'cache/cuda'),TORCH_HOME=str(RUN/'cache/torch'),
        TRITON_CACHE_DIR=str(RUN/'cache/triton'),TORCHINDUCTOR_CACHE_DIR=str(RUN/'cache/inductor'))
    with (HERE/'controller.log').open('x') as stream:
        process=subprocess.Popen([sys.executable,'-B',str(HERE/'controller.py')],cwd=RUN,stdin=subprocess.DEVNULL,
            stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=env)
    receipt=dict(pid=process.pid,utc=utc(),source_lock_sha256=sha(HERE/'source_lock.json'),
                 automatic_return=False,uploaded=False)
    write(HERE/'launch.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    main()
