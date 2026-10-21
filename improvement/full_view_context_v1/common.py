"""Pinned assets for one same-native-frame view experiment."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
PREVIOUS = WORK / 'video_text_grounding_20261021_v1'
CLIP = WORK / 'independent_text_grounding_20261021_v1'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE = WRAPPER.parent.parent / 'controller'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'
JOB = 'same_native_view_clip56_20261021_v1'
MEAN = [.48145466, .4578275, .40821073]
STD = [.26862954, .26130258, .27577711]


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))


def checked(value):
    path = Path(value['path'])
    assert digest(path) == value['sha256'], path
    if 'bytes' in value:
        assert path.stat().st_size == value['bytes']
    return path


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def save_array(path, value):
    import numpy as np
    with Path(path).open('xb') as stream:
        np.save(stream, value, allow_pickle=False)


def normalize(values):
    import numpy as np
    values = values.astype(np.float64)
    norm = np.linalg.norm(values, axis=-1, keepdims=True)
    assert np.isfinite(values).all() and np.all(norm > 0)
    return values / norm
