"""Detached environment preparation with explicit workspace paths."""
import datetime as dt
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=Path('/Users/choubk/codex-workspace')
assert ROOT in HERE.parents
controller=HERE/'controller';controller.mkdir(exist_ok=True)
receipt=controller/'environment_launch.json';assert not receipt.exists()
with (controller/'environment_background.log').open('xb') as log:
    child=subprocess.Popen([str(ROOT/'bin/run'),str(ROOT/'envs/ml/bin/python'),'-B',str(HERE/'install_mac_env.py')],
        cwd=HERE,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
receipt.write_text(json.dumps(dict(status='DETACHED_ENV_PREPARATION_STARTED',pid=child.pid,
    started_utc=dt.datetime.now(dt.timezone.utc).isoformat()),indent=2)+'\n')
print(receipt.read_text())
