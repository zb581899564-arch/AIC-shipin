"""Supervisor numeric review of the twelve retained v3 failures, no admission."""
import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parent.parent
CTRL = RUN/'controller'
CODE = RUN/'baseline_pts_v4/native_clock_core.py'
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE.parent))
from native_clock_core import audit_record

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

if __name__ == '__main__':
    before = sha(CODE)
    prior = read(CTRL/'pts_origin_v3_01_receipt.json')
    manifest = read(CTRL/'m0_finalize_01/clean_manifest_426.json')
    addendum = read(CTRL/'native_endpoint_addendum_01_receipt.json')
    meta = {r['video_id']: r for r in manifest['records']}
    supplemental = {r['video_id']: r for r in addendum['records']}
    results = []
    for original in prior['records']:
        if original['pass']:
            continue
        vid = original['video_id']
        numeric_path = CTRL/'pts_failed_numeric'/(vid+'.numeric.json')
        if sha(numeric_path) != original['numeric_evidence_sha256']:
            raise RuntimeError('retained numeric SHA mismatch')
        raw = None
        addon = supplemental.get(vid)
        if addon:
            raw_path = CTRL/'pts_failed_numeric'/(vid+'.ffprobe.json')
            if sha(raw_path) != addon['ffprobe_json']['sha256']:
                raise RuntimeError('raw supplement SHA mismatch')
            raw = read(raw_path)
        record, arrays = audit_record(meta[vid], read(numeric_path), original, addon, raw)
        results.append({'video_id': vid, 'status': record['status'], 'cfr_eligible': record['cfr_eligible'],
            'identity_pass': record['identity_pass'], 'native_clock_usable': record['native_clock_usable'],
            'failures': record['failures'], 'duration_seconds': record['duration_seconds'],
            'terminal_evidence': record['terminal_evidence']})
    if sha(CODE) != before:
        raise RuntimeError('core changed during independent review')
    report = {'scope': 'SUPERVISOR_SUBSET_REVIEW_NOT_SOURCE_LOCK_OR_INFERENCE_ADMISSION',
        'core_sha256': before, 'prior_receipt_sha256': sha(CTRL/'pts_origin_v3_01_receipt.json'),
        'audited_failed_sources': len(results), 'results': results,
        'labels_read': False, 'models_run': False, 'GPU_used': False, 'inference_allowed': False}
    with (CTRL/'native_clock_subset_review.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps([{'video_id': r['video_id'], 'status': r['status'], 'failures': r['failures']}
                      for r in results], indent=2))
