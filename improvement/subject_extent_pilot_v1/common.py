"""Bounded external-only pilot; no production data or historical run mutation."""
import hashlib
import json
import os
from pathlib import Path
import sys

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK / 'subject_extent_pilot_20261024_v1'
S1 = WORK / 'sprint_spatial_s1_20261021_v1'
WIDTH = WORK / 'gnmc_width_iteration_20261013_v1'
CHECKOUT = WORK / 'final_sprint_temporal_field_checkout_20261023_v6'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE = WRAPPER.parent.parent / 'controller'
LEDGER = WORK / 'improvement_round1/gpu_ledger.jsonl'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(WORK):
        raise ValueError('Reference outside project')
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def checked(value):
    p = Path(value['path']).resolve(strict=True)
    if not p.is_relative_to(WORK) or p.stat().st_size != value['bytes'] or sha(p) != value['sha256']:
        raise ValueError('Bound asset changed')
    return p


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)


def append(path, value):
    with Path(path).open('a') as f:
        f.write(json.dumps(value, allow_nan=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def paths():
    sys.path.insert(0, str(CHECKOUT))
    sys.path[:0] = [str(RUN / p) for p in ('b_score_aligned_package_v4', 'baseline_a_pts_v1',
                                          'baseline_a_pts_v1/vendor', 'temporal_sft8b_v1')]


def signature(tensors):
    import torch
    return {k: dict(shape=list(v.shape), dtype=str(v.dtype), sha256=hashlib.sha256(
        v.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest())
        for k, v in tensors.items()}
