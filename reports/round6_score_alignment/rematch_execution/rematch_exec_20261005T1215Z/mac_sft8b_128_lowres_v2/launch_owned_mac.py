"""Only this task's two registered scripts may be detached."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent;ROOT=Path('/Users/choubk/codex-workspace')
p=argparse.ArgumentParser();p.add_argument('script',choices=['asset_http_receiver.py','finish_mac.py'])
p.add_argument('--expected-lock');args=p.parse_args();assert ROOT in HERE.parents
key=Path(args.script).stem;receipt=HERE/'controller'/(key+'_launch.json');assert not receipt.exists()
command=[str(ROOT/'bin/run'),'/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z/env/bin/python','-B',str(HERE/args.script)]
if args.expected_lock:command+=['--expected-lock',args.expected_lock]
with (HERE/'controller'/(key+'_background.log')).open('xb') as log:
    child=subprocess.Popen(command,cwd=HERE,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
receipt.write_text(json.dumps(dict(status='DETACHED_TASK_MAC_SCRIPT_STARTED',script=args.script,pid=child.pid,
    started_utc=dt.datetime.now(dt.timezone.utc).isoformat()),indent=2)+'\n')
print(receipt.read_text())
