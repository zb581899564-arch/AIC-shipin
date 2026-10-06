"""Prove the isolated runtime reproduces fixed temporal and full-pipeline outputs."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
QUEUE_PYTHON = str(ROOT / 'env/qwen3vl/bin/python')


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--python', required=True)
    ap.add_argument('--candidate-run', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    executable = Path(args.python).absolute()
    candidate, output = Path(args.candidate_run).resolve(), Path(args.output).resolve()
    if not executable.is_relative_to(ROOT / 'env') or not output.is_relative_to(ROOT):
        raise ValueError('runtime/output must remain in the project workspace')
    config = (executable.parent.parent / 'pyvenv.cfg').read_text().lower()
    if 'include-system-site-packages = false' not in config:
        raise ValueError('runtime still inherits system site packages')
    acceptance = json.loads((candidate / 'acceptance.json').read_text())
    if acceptance['status'] != 'PASS_READY_FOR_OFFICIAL_EVALUATION':
        raise ValueError('full candidate must be accepted before replay')
    policy = json.loads((candidate / 'launch.json').read_text())['policy']
    output.mkdir(exist_ok=False, parents=True)
    common = [str(executable), '-m', 'inference_v2.baseline_v2', '--model',
              str(ROOT / 'models/Qwen3-VL-4B-Instruct'), '--constrained-json', '--num-videos', '3']
    jobs = [
        ('isolated_replay_dev3_windowed', common + ['--index', str(CAMPAIGN / 'frozen_data/dev.jsonl'),
            '--temporal-only', '--query-aware', '--temporal-policy', 'windowed',
            '--temporal-out', str(output / 'dev_windowed.jsonl'), '--raw-out', str(output / 'dev_raw.jsonl')]),
        ('isolated_replay_test3_' + policy, common + ['--index', str(ROOT / 'inference/test_index.json'),
            '--temporal-policy', policy, '--out', str(output / 'predictions.jsonl'),
            '--status-out', str(output / 'status.jsonl'), '--raw-out', str(output / 'test_raw.jsonl')]),
    ]
    for name, command in jobs:
        code = subprocess.run([QUEUE_PYTHON, str(CAMPAIGN / 'budget_run.py'), '--name', name,
                               '--max-seconds', '900', '--'] + command, cwd=ROOT,
                              env=dict(os.environ, PYTHONPATH=str(ROOT))).returncode
        if code:
            raise SystemExit(code)
    before = {r['video_id']: r for r in read(ROOT / 'runs/improvement_dev_v2/windowed_predictions.jsonl')}
    after = read(output / 'dev_windowed.jsonl')
    if len(after) != 3:
        raise ValueError('temporal replay incomplete')
    fields = ('video_id', 'status', 'segments_sec', 'segments_frames', 'query', 'policy', 'constrained_json')
    changed = [r['video_id'] for r in after if any(r[k] != before[r['video_id']][k] for k in fields)]
    original = {r['video_id']: r for r in read(candidate / 'predictions.jsonl')}
    replayed = read(output / 'predictions.jsonl')
    statuses = read(output / 'status.jsonl')
    if len(replayed) != 3 or len(statuses) != 3:
        raise ValueError('full replay incomplete')
    changed_full = [r['video_id'] for r in replayed if r != original[r['video_id']]]
    failures = [r['video_id'] for r in statuses if r['status'] not in ('ok', 'valid_empty')
                or r['failed_count'] or r['fallback_count']]
    report = {'status': 'passed' if not (changed or changed_full or failures) else 'failed',
              'isolated_python': str(executable), 'candidate_run': str(candidate),
              'temporal_windowed_videos': len(after), 'temporal_changed_ids': changed,
              'full_pipeline_videos': len(replayed), 'full_pipeline_changed_ids': changed_full,
              'invalid_or_fallback_ids': failures,
              'scope': 'same saved weights, offline reload, actual CUDA temporal and image crop inference',
              'all_174_recomputed_in_isolated_runtime': False,
              'replay_is_validation_only': True}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    raise SystemExit(0 if report['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
