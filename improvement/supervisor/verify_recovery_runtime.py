"""Verify isolated offline inference reproduces frozen temporal and corrected spatial outputs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from recovery_contract import read, sha, validate_recovery, validate_recovery_artifacts

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
QUEUE_PYTHON = str(ROOT / 'env/qwen3vl/bin/python')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate-run', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    candidate, output = Path(args.candidate_run).resolve(), Path(args.output).resolve()
    executable = ROOT / 'env/qwen3vl_isolated_20260910/bin/python'
    if not candidate.is_relative_to(ROOT) or not output.is_relative_to(ROOT):
        raise ValueError('paths must remain in project')
    if 'include-system-site-packages = false' not in (executable.parent.parent / 'pyvenv.cfg').read_text().lower():
        raise ValueError('runtime inherits system packages')
    acceptance = json.loads((candidate / 'acceptance.json').read_text())
    launch = json.loads((candidate / 'launch.json').read_text())
    if acceptance['status'] != 'PASS_READY_FOR_OFFICIAL_EVALUATION':
        raise ValueError('candidate delivery acceptance missing')
    if sha(candidate / 'predictions.jsonl') != acceptance['prediction_sha256']:
        raise ValueError('accepted candidate predictions changed')
    validate_recovery(launch, read(candidate / 'status.jsonl'))
    validate_recovery_artifacts(candidate, launch, read(candidate / 'status.jsonl'))
    output.mkdir(exist_ok=False, parents=True)
    from inference_v2.baseline_v2 import load_index
    index = load_index(str(ROOT / 'inference/test_index.json'))[:3]
    index_path = output / 'test3_index.json'
    index_path.write_text(json.dumps(index, indent=2) + '\n')
    common = [str(executable), '-m', 'inference_v2.baseline_v2', '--model',
              str(ROOT / 'models/Qwen3-VL-4B-Instruct'), '--constrained-json', '--temporal-only']
    jobs = [
        ('isolated_reader_v1_dev3_windowed', common + ['--index', str(CAMPAIGN / 'frozen_data/dev.jsonl'),
          '--query-aware', '--num-videos', '3', '--temporal-policy', 'windowed',
          '--temporal-out', str(output / 'dev_windowed.jsonl'), '--raw-out', str(output / 'dev_raw.jsonl')]),
        ('isolated_reader_v1_test3_multi', common + ['--index', str(index_path), '--temporal-policy', 'multi',
          '--temporal-out', str(output / 'test_temporal.jsonl'), '--raw-out', str(output / 'test_temporal_raw.jsonl')]),
    ]
    for name, command in jobs:
        run_job(name, command)
    fields = ('video_id', 'status', 'segments_sec', 'segments_frames', 'query', 'policy', 'adapter', 'constrained_json', 'sampling')
    before_dev = {str(r['video_id']): r for r in read(ROOT / 'runs/improvement_dev_v2/windowed_predictions.jsonl')}
    before_test = {str(r['video_id']): r for r in read(Path(launch['engineering_recovery']['temporal_run']) / 'temporal.jsonl')}
    after_dev, after_test = read(output / 'dev_windowed.jsonl'), read(output / 'test_temporal.jsonl')
    if len(after_dev) != 3 or len(after_test) != 3:
        raise ValueError('isolated temporal replay incomplete')
    changes = []
    for scope, rows, before in [('dev', after_dev, before_dev), ('test', after_test, before_test)]:
        for r in rows:
            for k in fields:
                if r[k] != before[str(r['video_id'])][k]:
                    changes.append({'scope': scope, 'video_id': r['video_id'], 'field': k})
    if changes:
        (output / 'report.json').write_text(json.dumps({'status': 'failed', 'temporal_changes': changes}, indent=2))
        raise ValueError('isolated temporal output differs; corrected crop replay blocked')
    spatial = [str(executable), '-m', 'inference_recovery.spatial_replay', '--model',
               str(ROOT / 'models/Qwen3-VL-4B-Instruct'), '--index', str(index_path),
               '--temporal', str(output / 'test_temporal.jsonl'), '--out', str(output / 'predictions.jsonl'),
               '--status-out', str(output / 'status.jsonl'), '--raw-out', str(output / 'spatial_raw.jsonl')]
    run_job('isolated_reader_v1_spatial3', spatial)
    before = {str(r['video_id']): r for r in read(candidate / 'predictions.jsonl')}
    after = read(output / 'predictions.jsonl')
    statuses = read(output / 'status.jsonl')
    wanted = {str(r['video_id']) for r in index}
    if len(after) != 3 or len(statuses) != 3 or {str(r['video_id']) for r in after} != wanted:
        raise ValueError('isolated spatial replay exact coverage failed')
    changed = [r['video_id'] for r in after if r != before[str(r['video_id'])]]
    failures = [r['video_id'] for r in statuses if r['status'] not in ('ok', 'valid_empty') or r['failed_count'] or r['fallback_count']]
    report = dict(status='passed' if not (changed or failures) else 'failed', isolated_python=str(executable),
                  temporal_windowed_videos=3, temporal_multi_videos=3, corrected_spatial_videos=3,
                  temporal_changed=[], spatial_changed_ids=changed, invalid_or_fallback_ids=failures,
                  candidate_prediction_sha256=sha(candidate / 'predictions.jsonl'),
                  candidate_acceptance_sha256=sha(candidate / 'acceptance.json'),
                  recovery_source_hashes=launch['engineering_recovery']['recovery_source_hashes'],
                  scope='offline CUDA temporal and image inference using same weights and corrected source-frame reader',
                  all_174_recomputed_in_isolated_runtime=False, replay_is_validation_only=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    if report['status'] != 'passed':
        raise ValueError('isolated spatial outputs differ')


def run_job(name, command):
    code = subprocess.run([QUEUE_PYTHON, str(CAMPAIGN / 'budget_run.py'), '--name', name,
                           '--max-seconds', '900', '--'] + command, cwd=ROOT,
                          env=dict(os.environ, PYTHONPATH=str(ROOT))).returncode
    if code:
        raise RuntimeError('isolated replay GPU job failed: ' + name)


if __name__ == '__main__':
    main()
