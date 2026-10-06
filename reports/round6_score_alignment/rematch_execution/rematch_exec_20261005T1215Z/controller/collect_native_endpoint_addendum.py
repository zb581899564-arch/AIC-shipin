"""CPU metadata-only supplement for non-CFR terminal frame identity.

Preserve the original 426-source audit; no images, labels, models or GPU.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import socket
import subprocess

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
EXPECTED_RECEIPT = 'efcb86a8435523e53c17e86eedc9506e134b9571a84acdd0ebf5e8af8d17bff5'
EXPECTED_M0 = '57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32'
FFPROBE = Path('/home/inspur/anaconda3/envs/Andy/bin/ffprobe')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')

if __name__ == '__main__':
    if socket.gethostname() != 'inspur-NP5570M5':
        raise RuntimeError('registered training host identity mismatch')
    receipt_path = RUN/'baseline_pts_v3/scan_01/pts_origin_receipt.json'
    manifest_path = RUN/'baseline_a/m0_finalize_01/clean_manifest_426.json'
    if sha(receipt_path) != EXPECTED_RECEIPT or sha(manifest_path) != EXPECTED_M0:
        raise RuntimeError('complete input evidence changed')
    receipt, manifest = read(receipt_path), read(manifest_path)
    if receipt['audited_sources'] != 426 or len(manifest['records']) != 426:
        raise RuntimeError('complete denominator missing')
    by_id = {r['video_id']: r for r in manifest['records']}
    non_cfr = [r for r in receipt['records'] if
               r.get('max_normalized_cfr_error_sec', 0) > r['one_frame_tolerance_sec']]
    root = RUN/'baseline_pts_v4/endpoint_addendum_01'
    root.mkdir(parents=True, exist_ok=False)
    records = []
    for prior in non_cfr:
        item = by_id[prior['video_id']]
        source = Path(item['source_path']).resolve(strict=True)
        allowed = (RUN/'baseline_a/m0_426_02/media').resolve()
        if source.parent != allowed or sha(source) != item['source_sha256']:
            raise RuntimeError('source identity or path changed')
        output = root/(item['video_id']+'.ffprobe.json')
        proc = subprocess.run([str(FFPROBE), '-v', 'error', '-select_streams', 'v:0',
            '-show_frames', '-show_streams', '-show_entries',
            'stream=width,height,time_base,start_pts,start_time,duration_ts,duration,avg_frame_rate,r_frame_rate,nb_frames:frame=best_effort_timestamp,best_effort_timestamp_time,pkt_duration,pkt_duration_time,duration,duration_time',
            '-of', 'json', str(source)], capture_output=True, text=True, check=True, timeout=600)
        # Save actual raw integer/tick metadata without rewriting media.
        data = json.loads(proc.stdout)
        with output.open('x', encoding='utf-8') as stream:
            stream.write(proc.stdout)
        if sha(source) != item['source_sha256']:
            raise RuntimeError('source changed during supplement')
        frames = data.get('frames', [])
        row = {'video_id': item['video_id'], 'source_sha256': item['source_sha256'],
            'source_sha256_before': item['source_sha256'], 'source_sha256_after': sha(source),
            'metadata_path': str(output), 'metadata_sha256': sha(output),
            'ffprobe_json': {'path': str(output), 'sha256': sha(output)},
            'expected_frames': item['n_frames'], 'ffprobe_frames': len(frames),
            'last_frame_numeric_metadata': frames[-1] if frames else None,
            'source_hash_verified_before_and_after': True}
        records.append(row)
        print(json.dumps({'video_id': item['video_id'], 'frames': len(frames),
                          'last_frame': row['last_frame_numeric_metadata']}), flush=True)
    result = {'schema': 'aic_native_endpoint_addendum_v1',
        'status': 'COLLECTED_METADATA_ONLY_NOT_IDENTITY_ADMISSION',
        'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'prior_receipt_sha256': EXPECTED_RECEIPT, 'input_manifest_sha256': EXPECTED_M0,
        'records': records, 'source_count': len(records), 'ffprobe_sha256': sha(FFPROBE),
        'collector_sha256': sha(__file__), 'source_bytes_modified': False,
        'images_exported_or_displayed': False, 'labels_read': False,
        'models_run': False, 'GPU_used': False, 'inference_allowed': False}
    write(root/'addendum_receipt.json', result)
    print(json.dumps({'status': result['status'], 'sources': len(records),
                      'receipt_sha256': sha(root/'addendum_receipt.json')}), flush=True)
