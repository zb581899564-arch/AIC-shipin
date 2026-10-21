"""Estimate this fixed model/batch against current shared capacity."""
import json
from pathlib import Path
import shutil
import socket
import subprocess
from common import ROOT, CLIP, read, write


def live_reason():
    params = read(CLIP / 'asset_acceptance.json')['actual_clip_parameters']
    assert params == 151277313
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free,memory.used,utilization.gpu',
                                  '--format=csv,noheader,nounits'], text=True).strip()
    free = int(gpu.split(',')[0]) * 1024 * 1024
    # Frozen parameters with loading headroom plus registered batch activations.
    estimated = params * 4 * 2 + 32 * 50 * 768 * 4 * 32
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory',
                                   '--format=csv,noheader,nounits'], text=True).strip()
    processes = []
    for line in apps.splitlines():
        pid = line.split(',')[0].strip()
        folder = Path('/proc') / pid
        if pid.isdigit() and folder.exists():
            processes.append(dict(pid=int(pid), stat=(folder / 'stat').read_text(),
                argv=(folder / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')))
    record = dict(host=socket.gethostname(), GPU=gpu, current_free_gpu_bytes=free,
                  model_and_batch_estimate_bytes=estimated, parameters=params, outside_compute=processes,
                  disk_free_bytes=shutil.disk_usage(ROOT).free,
                  memory_available=[s for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')],
                  no_external_process_changes=True)
    write(ROOT / 'resource_before_gpu.json', record)
    assert record['host'] == 'inspur-NP5570M5' and free > estimated
    assert record['disk_free_bytes'] > read(ROOT / 'protocol.json')['planned_output_bytes']
    return json.dumps(record, separators=(',', ':'))
