"""New task-owned environment; existing Mac envs and system settings untouched."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/choubk/codex-workspace')
assert ROOT in HERE.parents and not HERE.is_symlink()
controller=HERE/'controller';controller.mkdir(exist_ok=True)
completion=controller/'environment_completion.json';assert not completion.exists()
packages=['torch==2.5.1','transformers==4.57.1','peft==0.17.1','numpy==2.2.6',
          'av==16.0.1','Pillow==11.3.0','safetensors==0.6.2','huggingface-hub==0.36.0']
result=dict(status='INSTALLING_TASK_SCOPED_MPS_ENVIRONMENT',packages=packages)
env=dict(os.environ,UV_NO_CONFIG='1',UV_LINK_MODE='copy',UV_CACHE_DIR=str(HERE/'cache/uv'),
         UV_PYTHON_INSTALL_DIR=str(ROOT/'envs/python'),UV_NO_MODIFY_PATH='1')
uv=str(ROOT/'bin/uv');environment=HERE/'env'
try:
    assert not environment.exists()
    with (controller/'environment_install.log').open('x') as log:
        subprocess.run([uv,'venv','--python',str(ROOT/'envs/ml/bin/python'),str(environment)],env=env,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run([uv,'pip','install','--python',str(environment/'bin/python'),'--cache-dir',str(HERE/'cache/uv'),
                       '--index-url','https://pypi.org/simple',*packages],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    frozen=subprocess.check_output([uv,'pip','freeze','--python',str(environment/'bin/python')],env=env,text=True)
    (controller/'environment_freeze.txt').write_text(frozen)
    result.update(status='PASS_TASK_SCOPED_MPS_ENVIRONMENT',python=str(environment/'bin/python'),existing_ml_environment_unchanged=True)
except Exception as exc:
    result.update(status='STOP_TASK_SCOPED_MPS_ENVIRONMENT',failure=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
result['checked_utc']=dt.datetime.now(dt.timezone.utc).isoformat();completion.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True);raise SystemExit(0 if result['status'].startswith('PASS_') else 3)
