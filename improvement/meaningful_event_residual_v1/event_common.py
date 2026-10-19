"""Explicit event-level residual experiment; historical artifacts stay immutable."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

W = Path('/home/inspur/aic_video_work')
ROOT = W/'meaningful_residual_20261018_v1'
SRC = W/'source_clear_residual_20261018_v1'
OLD = W/'semantic_context_production_20261016_v1'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = W/'env/qwen3vl_isolated_20260910/bin/python'
BASE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    p = Path(path)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p))


def bound(value):
    p = Path(value['path'])
    require(p.is_file() and sha(p) == value['sha256'], 'Changed adopted file: '+str(p))
    return p


def clean(value):
    if hasattr(value, 'item') and callable(value.item):
        return clean(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f:
        json.dump(clean(value), f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def event(stage, **values):
    require('utc' not in values and 'stage' not in values, 'Event timestamp belongs to logger')
    row = clean(dict(utc=utc(), stage=stage, **values))
    with (ROOT/'journal.jsonl').open('a') as f:
        f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
        f.flush()
        os.fsync(f.fileno())
    print(json.dumps(row, ensure_ascii=False), flush=True)


def cpu():
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child masks only its own CUDA')
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat('2026-10-18T16:00:00+00:00'), 'Human deadline reached')


def module(name, path):
    path = Path(path)
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve() == path.resolve(), 'Module identity collision')
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def old_modules():
    # The old renderer has no write side effects. Its original ROOT must not be
    # rebound; no old entry point is called by this experiment.
    sys.path.append(str(SRC/'code'))
    return module('adopted_source_clear_renderer', SRC/'code/render.py'), module('adopted_source_clear_common', SRC/'code/sr_common.py')


def canonical(rows):
    rows = [{k: r[k] for k in ('video_id', 'targetRatioWH', 'predictions')}
            for r in sorted(rows, key=lambda r: r['video_id'])]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def failure(stage, error):
    import traceback
    save(ROOT/(stage+'_failure_'+str(os.getpid())+'.json'), dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(), successes_preserved=True))
