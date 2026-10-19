"""New-purpose feature experiment. Never reruns historical generation."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get('AIC_RESIDUAL_ROOT','/home/inspur/aic_video_work/score_residual_execution_20261016_v1'))
WORK = ROOT.parent
PYTHON = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
    return h.hexdigest()

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()

def event(stage, **kw):
    d = dict(utc=utc(), stage=stage, **kw)
    with (ROOT/'journal.jsonl').open('a') as f:
        f.write(json.dumps(d, ensure_ascii=False, allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())
    print(json.dumps(d, ensure_ascii=False), flush=True)

def require(ok, reason):
    if not ok: raise ValueError(reason)
