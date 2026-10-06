"""Freeze unchanged temporal inference before repairing the spatial frame reader."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
from candidate_gate import load_qualified_holdout

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
OUTPUT = ROOT / 'runs/improvement_recovery_temporal_multi_v2'
OLD = ROOT / 'runs/improvement_test174_multi_v2'
HOLDOUT = ROOT / 'runs/improvement_holdout_v2'
PYTHON = str(ROOT / 'env/qwen3vl/bin/python')
FIELDS = ('video_id', 'source_group', 'segments_sec', 'segments_frames', 'query',
          'policy', 'adapter', 'constrained_json', 'constraint_backend', 'sampling')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def main():
    plan, _ = load_qualified_holdout(HOLDOUT, 'multi')
    for relative, expected in plan['source_hashes'].items():
        if relative != 'dev' and sha(ROOT / relative) != expected:
            raise ValueError('frozen inference drift: ' + relative)
    resource = json.loads((CAMPAIGN / 'test174_v2_multi.resource.json').read_text())
    if resource['exit_code'] != -15 or resource['status'] != 'failed':
        raise ValueError('original faulty job has not been reconciled')
    if (CAMPAIGN / 'active_gpu_job.json').exists():
        raise ValueError('GPU queue still active')
    OUTPUT.mkdir(parents=True, exist_ok=False)
    old_statuses = read(OLD / 'status.jsonl')
    index_path = ROOT / 'inference/test_index.json'
    command = [PYTHON, '-m', 'inference_v2.baseline_v2', '--model',
               str(ROOT / 'models/Qwen3-VL-4B-Instruct'), '--index', str(index_path),
               '--temporal-policy', 'multi', '--constrained-json', '--temporal-only',
               '--temporal-out', str(OUTPUT / 'temporal.jsonl'),
               '--raw-out', str(OUTPUT / 'raw.jsonl')]
    launch = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), policy='multi',
                  reason='Generic spatial frame-index correctness recovery; temporal model and decisions unchanged',
                  command=command, original_run=str(OLD), original_completed_status_rows=len(old_statuses),
                  original_artifact_hashes={p.name: sha(p) for p in OLD.iterdir() if p.is_file()},
                  decoder_probe_sha256=sha(ROOT / 'reports/supervisor_crop_decode_failure_probe.json'),
                  holdout_plan_sha256=sha(HOLDOUT / 'plan.json'),
                  holdout_summary_sha256=sha(HOLDOUT / 'summary.json'),
                  index_sha256=sha(index_path), source_hashes=plan['source_hashes'],
                  query_aware=False, adapter=None, max_seconds=1800,
                  no_new_holdout_or_tuning=True)
    write(OUTPUT / 'launch.json', launch)
    code = subprocess.run([PYTHON, str(CAMPAIGN / 'budget_run.py'), '--name',
                           'recovery_temporal174_multi_v2', '--max-seconds', '1800', '--'] + command,
                          cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT))).returncode
    if code:
        raise RuntimeError('temporal recovery GPU job failed')
    rows = read(OUTPUT / 'temporal.jsonl')
    by_id = {str(r['video_id']): r for r in rows}
    media = json.loads((ROOT / 'reports/supervisor_test_metadata.json').read_text())
    # The metadata file uses a records list; the canonical schema loader handles its envelope.
    from evaluation.schema import load_media_metadata
    expected = load_media_metadata(ROOT / 'reports/supervisor_test_metadata.json')
    if len(rows) != 174 or len(by_id) != 174 or set(by_id) != set(expected):
        raise ValueError('temporal recovery exact coverage failed')
    for row in rows:
        if row['status'] not in ('ok', 'valid_empty') or row['query'] is not None or row['adapter'] is not None:
            raise ValueError('invalid temporal inference: ' + str(row['video_id']))
        if row['policy'] != 'multi' or row['constrained_json'] is not True:
            raise ValueError('changed temporal policy/decoding')
    differences = []
    for old in old_statuses:
        new = by_id[str(old['video_id'])]
        for key in FIELDS:
            if old[key] != new[key]:
                differences.append({'video_id': old['video_id'], 'field': key})
        for key in ('n_frames', 'fps', 'width', 'height'):
            if old['metadata'][key] != new['metadata'][key]:
                differences.append({'video_id': old['video_id'], 'field': 'metadata.' + key})
    for name, digest in launch['original_artifact_hashes'].items():
        if sha(OLD / name) != digest:
            raise ValueError('original partial artifact changed: ' + name)
    if sha(index_path) != launch['index_sha256']:
        raise ValueError('test index changed')
    report = dict(status='passed' if not differences else 'failed', videos=len(rows),
                  compared_original_complete_rows=len(old_statuses), changed_fields=differences,
                  temporal_sha256=sha(OUTPUT / 'temporal.jsonl'), launch_sha256=sha(OUTPUT / 'launch.json'),
                  no_test_labels_or_manual_corrections=True, no_new_holdout=True)
    write(OUTPUT / 'freeze_report.json', report)
    if differences:
        raise ValueError('temporal decisions differ; spatial replay blocked')
    state = json.loads((CAMPAIGN / 'campaign_state.json').read_text())
    state.update(status='recovery_temporal_frozen_spatial_reader_review_pending',
                 recovery_temporal_run=str(OUTPUT), original_failed_candidate=str(OLD),
                 recovery_temporal_sha256=report['temporal_sha256'],
                 updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    write(CAMPAIGN / 'campaign_state.json', state)
    print(json.dumps(report))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if OUTPUT.exists():
            write(OUTPUT / 'failure.json', {'error': repr(exc), 'status': 'needs_supervisor_review'})
        raise
