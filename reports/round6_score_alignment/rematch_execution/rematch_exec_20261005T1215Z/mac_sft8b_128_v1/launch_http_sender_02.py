import json
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent
assert not (HERE/'http_sender_launch.json').exists()
with (HERE/'http_sender_background_02.log').open('xb') as log:
    child=subprocess.Popen([sys.executable,'-B',str(HERE/'asset_http_sender.py')],cwd=HERE,
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(50):
    if (HERE/'http_sender_launch.json').exists():break
    assert child.poll() is None,'owned sender exited';time.sleep(.1)
print((HERE/'http_sender_launch.json').read_text())

