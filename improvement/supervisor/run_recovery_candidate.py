"""Replay every spatial prediction with exact frame input and frozen temporal decisions."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
from candidate_gate import load_qualified_holdout
from recovery_contract import RECOVERY_KIND, frozen_temporal, sha

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
PYTHON = str(ROOT / 'env/qwen3vl/bin/python')
HOLDOUT = ROOT / 'runs/improvement_holdout_v2'
TEMPORAL = ROOT / 'runs/improvement_recovery_temporal_multi_v2'
OUTPUT = ROOT / 'runs/improvement_test174_multi_reader_v1'
JOB = 'test174_multi_reader_v1'


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def main():
    plan, _ = load_qualified_holdout(HOLDOUT, 'multi')
    _, temporal_launch, report = frozen_temporal(TEMPORAL)
    review = json.loads((CAMPAIGN / 'recovery_reader_review.json').read_text())
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'inference_recovery').glob('*.py')}
    if review['status'] != 'passed' or review['source_hashes'] != source_hashes:
        raise ValueError('supervisor reader acceptance missing or source drifted')
    if (CAMPAIGN / 'active_gpu_job.json').exists():
        raise ValueError('GPU queue active')
    OUTPUT.mkdir(exist_ok=False)
    command = [PYTHON, '-m', 'inference_recovery.spatial_replay', '--model',
               str(ROOT / 'models/Qwen3-VL-4B-Instruct'), '--index', str(ROOT / 'inference/test_index.json'),
               '--temporal', str(TEMPORAL / 'temporal.jsonl'), '--out', str(OUTPUT / 'predictions.jsonl'),
               '--status-out', str(OUTPUT / 'status.jsonl'), '--raw-out', str(OUTPUT / 'raw.jsonl')]
    launch = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), policy='multi', command=command,
                  holdout_plan_sha256=sha(HOLDOUT / 'plan.json'), holdout_summary_sha256=sha(HOLDOUT / 'summary.json'),
                  index_sha256=sha(ROOT / 'inference/test_index.json'),
                  metadata_sha256=sha(ROOT / 'reports/supervisor_test_metadata.json'),
                  source_hashes=plan['source_hashes'], query_aware=False, adapter=None, max_seconds=7200,
                  test_use='automatic local inference only', crop_stage='frozen base-model crop functions with exact sequential source-frame decoding',
                  engineering_recovery=dict(kind=RECOVERY_KIND, temporal_run=str(TEMPORAL),
                    temporal_sha256=report['temporal_sha256'], recovery_source_hashes=source_hashes,
                    reader_review_sha256=sha(CAMPAIGN / 'recovery_reader_review.json'),
                    no_new_holdout_or_tuning=True, all_test_videos_replayed=True, job_name=JOB))
    for k in ('holdout_plan_sha256', 'holdout_summary_sha256', 'index_sha256'):
        if launch[k] != temporal_launch[k]:
            raise ValueError('frozen temporal lineage differs: ' + k)
    write(OUTPUT / 'launch.json', launch)
    state = json.loads((CAMPAIGN / 'campaign_state.json').read_text())
    state.update(status='corrected_spatial_replay_running', candidate_run=str(OUTPUT),
                 active_orchestrator_pid=os.getpid(), updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    write(CAMPAIGN / 'campaign_state.json', state)
    code = subprocess.run([PYTHON, str(CAMPAIGN / 'budget_run.py'), '--name', JOB,
                           '--max-seconds', '7200', '--'] + command, cwd=ROOT).returncode
    if code:
        raise RuntimeError('corrected spatial replay GPU job failed')
    code = subprocess.run([PYTHON, str(CAMPAIGN / 'accept_candidate.py'), '--run', str(OUTPUT),
                           '--holdout-run', str(HOLDOUT), '--policy', 'multi'], cwd=ROOT,
                          env=dict(os.environ, PYTHONPATH=str(ROOT))).returncode
    if code:
        raise RuntimeError('corrected spatial replay delivery gate failed')
    state = json.loads((CAMPAIGN / 'campaign_state.json').read_text())
    state.update(status='corrected_candidate_accepted_isolated_replay_pending',
                 updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    write(CAMPAIGN / 'campaign_state.json', state)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if OUTPUT.exists():
            write(OUTPUT / 'failure.json', {'status': 'needs_supervisor_review', 'error': repr(exc)})
        raise
