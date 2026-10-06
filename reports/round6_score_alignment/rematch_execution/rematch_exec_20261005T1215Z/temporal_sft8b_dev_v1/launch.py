import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import hashlib
from evaluate import HERE,RUN,ROOT,require,sha,read,write

a=read(HERE/'admission.json')
require(a['authorized'],'missing admission')
for path,digest in a['files'].items(): require(sha(path)==digest,'bound identity changed')
require(not (HERE/'launch.json').exists(),'registered once only')
compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
require(not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists(),'shared GPU conflict')
linux_bytes=int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
# Live Mac whole-root occupancy measured over its approved bin/run at launch registration.
mac_bytes=27302036*1024
remaining_mac_full_bytes=1100000000
combined=linux_bytes+mac_bytes+remaining_mac_full_bytes+a['planned_output_bytes']
require(combined<=80*2**30,'combined Linux/Mac registered peak exceeds boundary')
command=[sys.executable,'-B',str(RUN/'controller/gpu_run.py'),'--name','rematch_sft8b_dev_01',
    '--max-seconds',str(a['max_wall_seconds']),'--planned-output-bytes',str(a['planned_output_bytes']),
    '--capacity-reason','Fixed 112 dev windows x 2 arms; 100MB bounded JSON evidence; combined Linux/Mac projected peak checked',
    '--queue-seconds','1800','--',sys.executable,'-B',str(HERE/'evaluate.py'),'evaluate']
with (HERE/'launch.log').open('x') as log:
    p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=RUN,start_new_session=True)
receipt=dict(pid=p.pid,command=command,started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    launcher_sha256=sha(__file__),admission_sha256=sha(HERE/'admission.json'),combined_projected_bytes=combined,
    mac_snapshot_bytes=mac_bytes,remaining_mac_full_bytes=remaining_mac_full_bytes,linux_work_bytes=linux_bytes)
write(HERE/'launch.json',receipt)
print(json.dumps(receipt))
