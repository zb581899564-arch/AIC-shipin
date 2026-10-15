"""Small immutable artifacts for the independently registered recall pilot."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

HOME = Path('/home/inspur/aic_video_work')
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PYTHON = HOME/'env/qwen3vl_isolated_20260910/bin/python'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()

def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def checked(path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(HOME) and path.is_file() and sha(path) == digest,
            'Changed/out-of-workspace input: '+str(path))
    return path
