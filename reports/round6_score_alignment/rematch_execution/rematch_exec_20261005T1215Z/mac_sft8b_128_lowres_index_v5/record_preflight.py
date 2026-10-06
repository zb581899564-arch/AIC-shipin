"""Record actual task environment and real CPU acceptance without GPU training."""
import datetime as dt
import importlib.metadata as metadata
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=Path('/Users/choubk/codex-workspace');ASSET_ROOT=Path('/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z')
assert ROOT in HERE.parents and Path(sys.executable)==ASSET_ROOT/'env/bin/python'
packages=dict(torch='2.5.1',torchvision='0.20.1',transformers='4.57.1',peft='0.17.1',numpy='2.2.6',
              av='16.0.1',Pillow='11.3.0',safetensors='0.6.2',**{'huggingface-hub':'0.36.0'})
actual={name:metadata.version(name) for name in packages}
assert actual==packages
cpu_log=HERE/'controller/cpu_acceptance_03.log'
if not cpu_log.exists():
    with cpu_log.open('xb') as log:
        result=subprocess.run([sys.executable,'-B',str(HERE/'test_mac_cpu.py'),'--mac'],stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0
summaries=[json.loads(line) for line in cpu_log.read_text().splitlines() if line.startswith('{')]
assert summaries[-1]==dict(status='PASS_MAC_CPU_CONTRACTS',tests=8,failures=0,errors=0,real_codec_processor_test=True)
freeze=''.join(name+'=='+version+'\n' for name,version in sorted(
    (dist.metadata['Name'],dist.version) for dist in metadata.distributions()))
(HERE/'environment_final_freeze.txt').write_text(freeze)
cache_keys=['XDG_CONFIG_HOME','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','PIP_CACHE_DIR','TMPDIR','PYTHONPYCACHEPREFIX']
cache={name:os.environ.get(name) for name in cache_keys}
assert all(value and ROOT in Path(value).resolve().parents for value in cache.values())
receipt=dict(status='PASS_MAC_REAL_CPU_ACCEPTANCE_AND_PINNED_ENVIRONMENT',tests=8,
    real_codec_processor_test=True,packages=actual,torchvision_addition_to_initial_environment_recorded=True,
    python=sys.executable,cache_scope=cache,cpu_log_sha256=hashlib.sha256(cpu_log.read_bytes()).hexdigest(),
    hostname=subprocess.check_output(['/bin/hostname'],text=True).strip(),
    hardware=subprocess.check_output(['/usr/sbin/sysctl','hw.model','hw.memsize','hw.ncpu','machdep.cpu.brand_string'],text=True),
    checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),training_started=False)
(HERE/'preparation_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
