"""Small immutable evidence utilities for the independent VideoXum media stages."""
import datetime
import hashlib
import json
import os
from pathlib import Path

BASE = Path('/home/inspur/aic_video_work/sparse_context_iteration_20261013_v1')
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
LEGACY = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def check_file(path, digest, size=None):
    path = Path(path)
    if sha(path) != digest or (size is not None and path.stat().st_size != size):
        raise ValueError('Immutable evidence file changed: ' + str(path))
    return path
