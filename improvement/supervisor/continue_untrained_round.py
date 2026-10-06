"""Advance the approved untrained route through frozen holdout and first candidate."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/home/inspur/aic_video_work')
CAMPAIGN = ROOT / 'improvement_round1'
PYTHON = str(ROOT / 'env/qwen3vl/bin/python')
HOLDOUT = ROOT / 'runs/improvement_holdout_v2'


def state(**fields):
    path = CAMPAIGN / 'campaign_state.json'
    value = json.loads(path.read_text())
    value.update(fields, updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                 active_orchestrator_pid=os.getpid())
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def run(command):
    result = subprocess.run([PYTHON] + command, cwd=ROOT,
                            env=dict(os.environ, PYTHONPATH=str(ROOT))).returncode
    if result:
        state(status='needs_supervisor_review', failed_command=command, returncode=result)
        raise SystemExit(result)


def main():
    gate_test = json.loads((ROOT / 'reports/supervisor_canonical_dev_gate_test.json').read_text())
    if gate_test['status'] != 'passed':
        raise ValueError('canonical dev regression has not passed')
    if (CAMPAIGN / 'holdout_comparison_lock.json').exists() or (CAMPAIGN / 'active_gpu_job.json').exists():
        raise ValueError('existing final comparison or active GPU; supervisor must reconcile')
    state(status='holdout_comparison_running', holdout_run=str(HOLDOUT),
          training_deferred_for_round1=True,
          training_deferred_reason='Media source gate remains unresolved at candidate freeze',
          dev_completed=['single', 'multi', 'windowed'], dev_qualified=['windowed', 'multi'])
    run([str(CAMPAIGN / 'run_holdout_suite.py'), '--dev-run', str(ROOT / 'runs/improvement_dev_v2'),
         '--output', str(HOLDOUT), '--name-prefix', 'holdout_v2', '--max-seconds-per-policy', '7200'])
    summary = json.loads((HOLDOUT / 'summary.json').read_text())
    policy = summary['selected']
    state(holdout_used=True, holdout_accepted=summary['accepted_in_dev_order'], selected_policy=policy)
    if policy is None:
        state(status='no_holdout_qualified_candidate', official_improvement=False)
        return
    output = ROOT / ('runs/improvement_test174_' + policy + '_v2')
    state(status='full_test_inference_running', candidate_run=str(output))
    run([str(CAMPAIGN / 'run_candidate.py'), '--holdout-run', str(HOLDOUT), '--policy', policy,
         '--output', str(output), '--job-name', 'test174_v2_' + policy, '--max-seconds', '7200'])
    acceptance = json.loads((output / 'acceptance.json').read_text())
    if acceptance['status'] != 'PASS_READY_FOR_OFFICIAL_EVALUATION':
        raise ValueError('candidate acceptance failed')
    state(status='candidate_ready_for_supervisor_and_official_upload',
          candidate_archive=acceptance['archive'], candidate_archive_sha256=acceptance['archive_sha256'],
          official_improvement=False)
    print(json.dumps({'candidate_ready': True, 'policy': policy, 'archive': acceptance['archive']}), flush=True)


if __name__ == '__main__':
    main()
