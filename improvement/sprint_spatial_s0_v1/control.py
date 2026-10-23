"""Explicit S0 asset identities and immutable small stage receipts."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/sprint_spatial_s0_20261021_v1')
WORK = ROOT.parent
S1 = WORK / 'sprint_spatial_s1_20261021_v1'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE = RUN / 'controller'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def reference(path):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(WORK):
        raise ValueError('Asset outside project root')
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))


def checked(value):
    path = Path(value['path']).resolve(strict=True)
    if not path.is_relative_to(WORK) or path.stat().st_size != value['bytes'] or digest(path) != value['sha256']:
        raise ValueError('Frozen asset identity mismatch')
    return path


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def append(path, value):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def geometry():
    entry = read(S1 / 'center_source_lock.json')['code']['geometry.py']
    spec = importlib.util.spec_from_file_location('frozen_s1_deployment_geometry', checked(entry))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def signature(value):
    return dict(shape=list(value.shape), dtype=str(value.dtype),
        sha256=hashlib.sha256(value.contiguous().numpy().tobytes()).hexdigest())
