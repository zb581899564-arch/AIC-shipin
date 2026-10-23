"""Shared live admission based on the actual registered model and output plan."""
import json
import shutil
import socket
import subprocess
from pathlib import Path
from common import ROOT, read, write


def admission(name):
    query = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free,memory.used,utilization.gpu',
                                    '--format=csv,noheader,nounits'], text=True).strip()
    free = int(query.split(',')[0]) * 1024 ** 2
    # BF16 frozen8B plus rank8 gradients/optimizer and131K single-image activations.
    estimate = 8767123696 * 2 + 7671808 * 4 * 5 + 768 * 4096 * 4 * 96
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    others = []
    for row in apps.splitlines():
        pid = row.split(',')[0].strip()
        if pid.isdigit() and (Path('/proc') / pid).exists():
            p = Path('/proc') / pid
            others.append(dict(pid=int(pid), argv=(p / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace'), stat=(p / 'stat').read_text()))
    record = dict(host=socket.gethostname(), gpu=query, outside_compute=others, memory_estimate_bytes=estimate,
        actual_free_gpu_bytes=free, disk_free=shutil.disk_usage(ROOT).free,
        memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')])
    write(ROOT / f'resource_{name}.json', record)
    if record['host'] != 'inspur-NP5570M5' or free < estimate or record['disk_free'] < read(ROOT / 'protocol.json')['remaining_output_budget_bytes']:
        raise ValueError('Actual shared capacity cannot hold this fixed job; do not change outsiders')
    return json.dumps(record, separators=(',', ':'))
