"""Shared artifact identities; prediction identity excludes accounting fields."""
from pathlib import Path
import hashlib
import json
import zipfile
from routing_production60_common import ADMISSION, RUN, WORK, FULL_PARAMETERS, read, ref, save, checked

ROOT = ADMISSION / 'routing_package63'
PRODUCTION = ADMISSION / 'routing_production62'
POLICIES = ('source_rerank', 'source_remove')


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_lines(path, rows):
    with Path(path).open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n')


def canonical(rows):
    """Numerically identical int/float boxes must never manufacture novelty."""
    normalized = [dict(video_id=row['video_id'], targetRatioWH=row['targetRatioWH'],
        predictions=[dict(frame=p['frame'], bboxes=[float(v) for v in p['bboxes']])
                     for p in sorted(row['predictions'], key=lambda p: p['frame'])])
        for row in sorted(rows, key=lambda r: r['video_id'])]
    data = json.dumps(normalized, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def zip_rows(path):
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != ['predictions.jsonl']:
            raise ValueError('Expected exactly one predictions.jsonl member')
        return [json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]


def frame_boxes(rows):
    result = {(row['video_id'], p['frame']): p['bboxes'] for row in rows for p in row['predictions']}
    if len(result) != sum(len(row['predictions']) for row in rows):
        raise ValueError('Duplicate source/frame artifact')
    return result
