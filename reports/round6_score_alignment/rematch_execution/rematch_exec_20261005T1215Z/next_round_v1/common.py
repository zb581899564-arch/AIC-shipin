"""Shared next-round paths and immutable receipts; no model imports."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = Path(os.environ.get('AIC_WORK_ROOT', '/home/inspur/aic_video_work'))
BASELINE = RUN/'baseline_a_pts_v1'
sys.path[:0] = [str(HERE), str(BASELINE), str(BASELINE/'vendor'), str(RUN/'temporal_sft8b_v1')]
sys.path.append(str(ROOT/'round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/code'))

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def write_rows(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True)+'\n')

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def verify():
    lock = read(HERE/'source_lock.json')
    for path, digest in lock['files'].items():
        require(sha(path) == digest, 'registered source changed: '+path)
    return read(HERE/'config.json')

def inputs(scope):
    config = read(HERE/'config.json')
    item = config['inputs'][scope]
    require(sha(item['manifest']) == item['manifest_sha256'], 'input manifest changed')
    from frame_contract import load_clocks
    manifest = read(item['manifest'])
    clocks = load_clocks(manifest, item['registry'], item['registry_sha256'])
    return item, manifest, clocks

def progress(out, value):
    out = Path(out)
    temp = out/'progress.tmp'
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(out/'progress.json')
    print(json.dumps(value, ensure_ascii=False), flush=True)
