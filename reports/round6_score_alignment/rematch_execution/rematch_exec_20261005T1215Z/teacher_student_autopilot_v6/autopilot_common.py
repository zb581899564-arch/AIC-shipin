"""Shared immutable bindings and atomic state for this one Linux continuation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = Path('/home/inspur/aic_video_work')
PY = ROOT / 'env/qwen3vl_isolated_20260910/bin/python'


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def write(path, value, *, fresh=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if fresh:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(content)
    else:
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(path)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify():
    path = HERE / 'source_lock.json'
    registration = HERE / 'registration.json'
    if registration.exists():
        require(read(registration)['source_lock_sha256'] == sha(path), 'registered source lock changed')
    lock = read(path)
    for name, digest in lock['files'].items():
        require(sha(name) == digest, 'autopilot bound source changed: ' + name)
    return read(HERE / 'config.json')


def progress(stage, **fields):
    value = {'stage': stage, 'utc': utc(), 'pid': os.getpid(), 'uploaded': False,
             'automatic_return': False, **fields}
    write(HERE / 'progress.json', value)
    print(json.dumps(value, ensure_ascii=False), flush=True)
    return value
