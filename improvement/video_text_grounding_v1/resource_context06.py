"""Refresh shared capacity immediately before the deferred first GPU launch."""
import json
from pathlib import Path
import shutil
import subprocess
from common import ROOT, read, write


def live_reason(context='wrapper'):
    identity = read(ROOT / 'model_acceptance.json')
    config = identity['config']
    device = subprocess.check_output(['nvidia-smi','--query-gpu=memory.free,memory.used,utilization.gpu',
                                      '--format=csv,noheader,nounits'],text=True).strip()
    free = int(device.split(',')[0]) * 1024 * 1024
    # A conservative allocation estimate derived from this actual frozen model
    # and registered batch/grid, not a global fixed GPU/worker admission line.
    grid = (config['image_resolution'] // config['vision_patch_size']) ** 2 + 2
    transient = 8 * config['T'] * grid * config['vision_width'] * 4 * 32
    estimated = identity['parameters'] * 4 * 2 + transient
    apps = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory',
                                   '--format=csv,noheader,nounits'],text=True).strip()
    processes = []
    for line in apps.splitlines():
        pid = line.split(',')[0].strip()
        if not pid.isdigit():
            continue
        folder = Path('/proc') / pid
        if folder.exists():
            processes.append(dict(pid=int(pid),stat=(folder/'stat').read_text(),
                 argv=(folder/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
    snapshot = dict(host=subprocess.check_output(['hostname'],text=True).strip(),
          gpu_memory_free_bytes=free,gpu_summary=device,actual_model_parameters=identity['parameters'],
          model_derived_estimate_bytes=estimated,outside_compute_processes=processes,
          disk_free_bytes=shutil.disk_usage(ROOT).free,
          memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')],
          no_outside_process_changes=True)
    assert context in ('wrapper', 'encoder')
    write(ROOT / f'live_resource_{context}06.json',snapshot)
    assert snapshot['host']=='inspur-NP5570M5'
    assert free > estimated, 'Current free GPU cannot hold this model-derived estimate; defer without touching outsiders'
    assert snapshot['disk_free_bytes'] > read(ROOT/'protocol.json')['planned_output_bytes']
    return json.dumps(snapshot,separators=(',',':'))
