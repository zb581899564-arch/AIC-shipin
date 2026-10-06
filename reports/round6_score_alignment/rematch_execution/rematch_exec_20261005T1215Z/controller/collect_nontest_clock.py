"""Read-only source clocks for eight frozen non-test engineering sources."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
MANIFEST = RUN/'baseline_a/inputs/non_test_frozen8.json'
EXPECTED = '7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a'
WORKER = RUN/'baseline_pts_v3/numeric_source_worker.py'
WORKER_SHA = '0ab8632ded07c7b3c13c362845d7e46d68f67d721ccd2bd74eff58bb0bd81638'
FFPROBE = Path('/home/inspur/anaconda3/envs/Andy/bin/ffprobe')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1<<20), b''):
            h.update(block)
    return h.hexdigest()

def write(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write('\n')

if __name__ == '__main__':
    if sha(MANIFEST) != EXPECTED or sha(WORKER) != WORKER_SHA:
        raise RuntimeError('registered frozen source evidence changed')
    sys.path.insert(0, str(WORKER.parent))
    from a_contract import validate_manifest
    from time_origin_core import audit_origin
    spec = importlib.util.spec_from_file_location('non_test_numeric_worker', WORKER)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    manifest = json.loads(MANIFEST.read_text())
    validate_manifest(manifest)
    if manifest['kind'] != 'NONTEST_FROZEN8':
        raise RuntimeError('only eight non-test sources admitted')
    root = RUN/'controller/nontest_clock_numeric_01'
    root.mkdir(exist_ok=False)
    records = []
    for r in manifest['records']:
        source = Path(r['source_path']).resolve(strict=True)
        if not any(Path(p).resolve() in source.parents for p in manifest['allowed_source_roots']):
            raise RuntimeError('non-test source root mismatch')
        if sha(source) != r['source_sha256']:
            raise RuntimeError('non-test source hash changed')
        data = worker.read_numeric_source(source, FFPROBE, 0)
        if sha(source) != r['source_sha256']:
            raise RuntimeError('non-test source changed during scan')
        path = root/(r['video_id']+'.numeric.json')
        write(path, data)
        prior = audit_origin(data['raw_pts_sec'], r['fps_num'], r['fps_den'], r['n_frames'],
            data['stream_start_time'], data['stream_time_base'], data['decord_timestamps'],
            data['decord_fps'], data['decord_frames'], data['decord_numeric_epsilon'])
        record = {'video_id': r['video_id'], 'source_sha256': r['source_sha256'],
            'numeric_evidence_path': str(path), 'numeric_evidence_sha256': sha(path),
            'source_hash_verified_before_and_after': True, 'v3_audit': prior}
        records.append(record)
        print(json.dumps({'video_id': r['video_id'], 'frames': data['decord_frames'],
                          'v3_pass': prior['pass'], 'failures': prior['failures']}), flush=True)
    receipt = {'schema': 'aic_nontest_numeric_clock_v1', 'status': 'COLLECTED_NOT_ADMISSION',
        'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'input_manifest_sha256': EXPECTED, 'source_count': len(records), 'records': records,
        'numeric_worker_sha256': WORKER_SHA, 'collector_sha256': sha(__file__),
        'source_bytes_modified': False, 'images_exported_or_displayed': False,
        'labels_read': False, 'models_run': False, 'GPU_used': False}
    write(root/'nontest_numeric_receipt.json', receipt)
    print(json.dumps({'sources': len(records), 'receipt_sha256': sha(root/'nontest_numeric_receipt.json')}), flush=True)
