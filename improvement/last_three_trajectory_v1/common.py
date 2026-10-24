"""Explicit new CPU risk run; all original files and failures remain immutable."""
import hashlib
import json
from pathlib import Path
import sys

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK / 'last_three_trajectory_20261024_v1'
OLD = WORK / 'final_sprint_temporal_field_checkout_20261023_v6'
ASSETS = WORK / 'final_sprint_temporal_r_production_20261023_v6/assets.json'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
sys.path.insert(0, str(OLD))
from improvement.final_sprint_v1.contracts import checked, ref, save_new, stable_key, strict_load as read


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def save_lines(path, rows):
    with Path(path).open('x') as f:
        for row in rows:
            f.write(json.dumps(row, separators=(',', ':'), allow_nan=False)+'\n')
    return ref(path)


def fail(message):
    raise ValueError(message)
