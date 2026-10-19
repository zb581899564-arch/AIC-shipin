"""Bounded CPU-only child; parent keeps a physical CUDA index, uses no GPU."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True)
root = Path(parser.parse_args().root)
record = lambda path, value: path.write_text(json.dumps(value, indent=2) + '\n')
if not os.environ.get('CUDA_VISIBLE_DEVICES'):
    raise ValueError('Parent must retain its actual CUDA index')
record(root / 'controller_started.json', dict(pid=os.getpid(),
       start_ticks=Path('/proc/self/stat').read_text().split()[21],
       argv=sys.argv, parent_cuda=os.environ['CUDA_VISIBLE_DEVICES']))
env = os.environ.copy()
env.update(CUDA_VISIBLE_DEVICES='', AIC_RESIDUAL_ROOT=str(root), OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
try:
    completed = subprocess.run([sys.executable, str(root / 'code/pilot.py'), '--root', str(root)],
                               env=env, timeout=1800)
    if completed.returncode:
        raise RuntimeError('CPU pilot exit %d; preserve first failure' % completed.returncode)
    result = json.loads((root / 'completion.json').read_text())
    record(root / 'controller_completion.json', dict(exit_code=0, result=result,
           utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
except Exception as error:
    record(root / 'controller_failure.json', dict(error=repr(error),
           preserve_success=True, production_admitted=False))
    raise
