"""Generate a full automatic test candidate after the frozen holdout gate."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from candidate_gate import load_qualified_holdout

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
PYTHON = str(ROOT / 'env/qwen3vl/bin/python')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--holdout-run', required=True)
    ap.add_argument('--policy', required=True, choices=['multi', 'windowed'])
    ap.add_argument('--output', required=True)
    ap.add_argument('--job-name', required=True)
    ap.add_argument('--max-seconds', type=int, default=7200)
    args = ap.parse_args()
    holdout, output = Path(args.holdout_run).resolve(), Path(args.output).resolve()
    plan, summary = load_qualified_holdout(holdout, args.policy)
    if not output.is_relative_to(ROOT):
        raise ValueError('candidate output must remain in the project workspace')
    for relative, expected in plan['source_hashes'].items():
        if relative != 'dev' and sha(ROOT / relative) != expected:
            raise ValueError('frozen candidate source drift: ' + relative)
    if (CAMPAIGN / 'active_gpu_job.json').exists():
        raise ValueError('GPU queue is active; wait for the owned job')
    output.mkdir(parents=True, exist_ok=False)
    index, metadata = ROOT / 'inference/test_index.json', ROOT / 'reports/supervisor_test_metadata.json'
    command = [PYTHON, '-m', 'inference_v2.baseline_v2', '--model',
               str(ROOT / 'models/Qwen3-VL-4B-Instruct'), '--index', str(index),
               '--temporal-policy', args.policy, '--constrained-json',
               '--out', str(output / 'predictions.jsonl'),
               '--raw-out', str(output / 'raw.jsonl'),
               '--status-out', str(output / 'status.jsonl')]
    launch = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), policy=args.policy,
                  command=command, holdout_plan_sha256=sha(holdout / 'plan.json'),
                  holdout_summary_sha256=sha(holdout / 'summary.json'), index_sha256=sha(index),
                  metadata_sha256=sha(metadata), query_aware=False, adapter=None,
                  test_use='automatic local inference only', crop_stage='unchanged frozen baseline',
                  source_hashes=plan['source_hashes'], max_seconds=args.max_seconds)
    (output / 'launch.json').write_text(json.dumps(launch, indent=2) + '\n')
    code = subprocess.run([PYTHON, str(CAMPAIGN / 'budget_run.py'), '--name', args.job_name,
                           '--max-seconds', str(args.max_seconds), '--'] + command, cwd=ROOT).returncode
    if code:
        raise SystemExit(code)
    if sha(index) != launch['index_sha256']:
        raise ValueError('test index drift during inference')
    code = subprocess.run([PYTHON, str(CAMPAIGN / 'accept_candidate.py'), '--run', str(output),
                           '--holdout-run', str(holdout), '--policy', args.policy], cwd=ROOT,
                          env=__import__('os').environ | {'PYTHONPATH': str(ROOT)}).returncode
    raise SystemExit(code)


if __name__ == '__main__':
    main()
