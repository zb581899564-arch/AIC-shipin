"""Validate and package an automatically generated, holdout-qualified AIC candidate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from evaluation.schema import load_jsonl_records, load_media_metadata, validate_submission_records
from candidate_gate import load_qualified_holdout
from recovery_contract import validate_recovery, validate_recovery_artifacts

ROOT = Path('/home/inspur/aic_video_work')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--holdout-run', required=True)
    ap.add_argument('--policy', required=True, choices=['multi', 'windowed'])
    args = ap.parse_args()
    run, holdout = Path(args.run).resolve(), Path(args.holdout_run).resolve()
    if not run.is_relative_to(ROOT):
        raise ValueError('candidate must remain in the project workspace')
    plan, result = load_qualified_holdout(holdout, args.policy)
    for relative, digest in plan['source_hashes'].items():
        if relative == 'dev':
            continue
        if sha(ROOT / relative) != digest:
            raise ValueError('candidate source drift: ' + relative)
    launch = json.loads((run / 'launch.json').read_text())
    if launch['policy'] != args.policy or launch['holdout_plan_sha256'] != sha(holdout / 'plan.json'):
        raise ValueError('full inference launch does not match selected candidate')
    if launch['holdout_summary_sha256'] != sha(holdout / 'summary.json'):
        raise ValueError('holdout results changed after full inference launch')
    if launch['index_sha256'] != sha(ROOT / 'inference/test_index.json'):
        raise ValueError('test index identity changed')
    prediction_path = run / 'predictions.jsonl'
    rows, parse_errors = load_jsonl_records(prediction_path)
    metadata_path = ROOT / 'reports/supervisor_test_metadata.json'
    if sha(metadata_path) != launch['metadata_sha256']:
        raise ValueError('test metadata changed during inference')
    metadata = load_media_metadata(metadata_path)
    validation = validate_submission_records(rows, metadata)
    if parse_errors or not validation.ok or validation.issues or len(rows) != 174:
        raise ValueError('complete strict format validation failed: ' + str((parse_errors + validation.issues)[:10]))
    statuses, status_parse = load_jsonl_records(run / 'status.jsonl')
    index = {str(r['video_id']): r for r in statuses}
    if status_parse or len(index) != len(statuses) or set(index) != set(metadata):
        raise ValueError('full inference status coverage failed')
    recovery = None
    if 'engineering_recovery' in launch:
        recovery = validate_recovery(launch, statuses, ROOT)
        recovery.update(validate_recovery_artifacts(run, launch, statuses, ROOT))
    for row in rows:
        record = index[str(row['video_id'])]
        if record['status'] not in ('ok', 'valid_empty') or record['policy'] != args.policy:
            raise ValueError('invalid inference result: ' + str(row['video_id']))
        if record.get('adapter') is not None or not record.get('constrained_json'):
            raise ValueError('candidate model/decoding contract mismatch')
        if record['failed_count'] or record['fallback_count']:
            raise ValueError('candidate contains a crop failure or parse fallback: ' + str(row['video_id']))
        actual = [p['frame'] for p in row['predictions']]
        expected = [f for start, end in record['segments_frames'] for f in range(start, end)]
        if actual != expected or len(actual) != record['n_predictions']:
            raise ValueError('temporal-to-dense-frame mapping mismatch: ' + str(row['video_id']))
        if bool(actual) != (record['status'] == 'ok'):
            raise ValueError('empty/failure distinction mismatch')
        if set(row) != {'video_id', 'targetRatioWH', 'predictions'}:
            raise ValueError('unexpected top-level submission fields')
        for pred in row['predictions']:
            if set(pred) != {'frame', 'bboxes'} or any(type(v) is not int for v in pred['bboxes']):
                raise ValueError('submission fields must match the integer baseline format')
    archive = run / ('aic-qwen3vl-' + args.policy + '-20260910.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(prediction_path, 'predictions.jsonl')
    with zipfile.ZipFile(archive) as z:
        if z.namelist() != ['predictions.jsonl'] or z.testzip() is not None:
            raise ValueError('archive layout/integrity failed')
        if hashlib.sha256(z.read('predictions.jsonl')).hexdigest() != sha(prediction_path):
            raise ValueError('archive prediction identity mismatch')
    report = dict(status='PASS_READY_FOR_OFFICIAL_EVALUATION', official_score=None,
                  prediction_sha256=sha(prediction_path), archive_sha256=sha(archive),
                  archive=str(archive), archive_bytes=archive.stat().st_size,
                  videos=len(rows), frames=validation.valid_prediction_count,
                  status_counts=dict(Counter(r['status'] for r in statuses)),
                  crop_failures=0, crop_parse_fallbacks=0,
                  total_processing_seconds=sum(r['timing']['total_sec'] for r in statuses),
                  peak_reported_vram_mib=max(r['VRAM']['peak_mib'] for r in statuses),
                  holdout_plan_sha256=sha(holdout / 'plan.json'),
                  holdout_report_sha256=sha(holdout / (args.policy + '_report.json')),
                  inference_launch_sha256=sha(run / 'launch.json'),
                  engineering_recovery=recovery,
                  validation=validation.as_dict(include_predictions=False))
    (run / 'acceptance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'validation'}))


if __name__ == '__main__':
    main()
