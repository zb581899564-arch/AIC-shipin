"""Once-only recovery of failed global metadata projection; no inference or QA."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HOME = Path('/home/inspur/aic_video_work')
CAMPAIGN = HOME / 'twenty_hour_five_20261014_v1'
BASE = CAMPAIGN / 'temporal_global_recovery_control7_v1'
OLD = CAMPAIGN / 'temporal_production_control_v6'
PY = HOME / 'env/qwen3vl_isolated_20260910/bin/python'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def save(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())


def append(path, value):
    with path.open('a', encoding='utf8') as f:
        f.write(json.dumps(value, separators=(',', ':')) + '\n')
        f.flush()
        os.fsync(f.fileno())


def main():
    assert socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux'
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    reg = read(BASE / 'registration.json')
    permission = read(BASE / 'main_execution_admission.json')
    assert permission['status'] == 'MAIN_APPROVED_ONCE_FAILED_GLOBAL_METADATA_RECOVERY_NO_MODELS_OR_QA'
    assert permission['registration_sha256'] == sha(BASE / 'registration.json')
    for key in ('old_control6_failure_ref', 'old_control6_journal_ref', 'identity_diagnosis_ref', 'aggregate_writer_ref'):
        expected = reg[key]
        assert sha(Path(expected['path'])) == expected['sha256'], key
    assert not (OLD / 'run_01/completion.json').exists()
    assert read(Path(reg['old_control6_failure_ref']['path']))['status'] == 'FAILED_CONTROL_PRESERVE_ALL_ATTEMPTS_SUCCESS_RAW_COSTS'
    journal = [json.loads(line) for line in (OLD / 'run_01/journal.jsonl').read_text().splitlines()]
    failures = [row for row in journal if row['event'] == 'FAILED']
    assert len(failures) == 1 and failures[0]['phase'] == 'GLOBAL_AGGREGATE' and failures[0]['item'] == 'ALL426'
    complete = [row for row in journal if row['event'] in ('COMPLETE', 'REUSE') and row.get('exit_code') == 0]
    counts = {kind:sum(row['phase'] == kind for row in complete) for kind in (
        'SOURCE_PREPARE', 'BATCH_INPUT_ADMIT', 'GPU_WRAPPER', 'TERMINAL_CAPTURE',
        'FIRST_INPUT_REPLAY', 'OUTPUT_REPLAY', 'LEASE_CLOSE')}
    assert counts == dict(SOURCE_PREPARE=426, BATCH_INPUT_ADMIT=49, GPU_WRAPPER=49,
                         TERMINAL_CAPTURE=49, FIRST_INPUT_REPLAY=1992, OUTPUT_REPLAY=49, LEASE_CLOSE=49)
    run = BASE / 'run_01'
    run.mkdir(exist_ok=False)
    save(run / 'launch_claim.json', dict(pid=os.getpid(), registration_ref=ref(BASE / 'registration.json'),
         upstream_actual_success_counts=counts, new_model_calls=0, new_first_QA_calls=0))
    argv = [str(PY), '-B', '-u', str(BASE / 'code/aggregate.py'), '--registration', str(OLD / 'registration.json')]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', AIC_WORK_ROOT=str(HOME))
    original_run = HOME / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    env['PYTHONPATH'] = ':'.join(str(original_run / name) for name in ('b_score_aligned_package_v4','baseline_a_pts_v1','baseline_a_pts_v1/vendor','balanced_two_window_risk_v3','temporal_sft8b_v1','resource_unlimited_v1_20261007'))
    log_path = run / 'aggregate.log'
    with log_path.open('xb') as log:
        p = subprocess.Popen(argv, cwd=BASE, env=env, stdout=log, stderr=subprocess.STDOUT)
        fields = (Path('/proc') / str(p.pid) / 'stat').read_text().rsplit(')', 1)[1].split()
        ticks = int(fields[19])
        append(run / 'journal.jsonl', dict(event='BEGIN', phase='GLOBAL_RECOVERY', item='ALL426',
               pid=p.pid, start_ticks=ticks, argv=argv, utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        exit_code = p.wait()
    event = 'COMPLETE' if exit_code == 0 else 'FAILED'
    append(run / 'journal.jsonl', dict(event=event, phase='GLOBAL_RECOVERY', item='ALL426',
           exit_code=exit_code, utc=dt.datetime.now(dt.timezone.utc).isoformat(),
           log_path=str(log_path), log_sha256=sha(log_path)))
    if exit_code != 0:
        save(run / 'failure.json', dict(status='FAILED_CONTROL7_METADATA_RECOVERY_PRESERVE_ALL_SUCCESS',
             exit_code=exit_code, old_control6_failure_ref=reg['old_control6_failure_ref'],
             log_ref=ref(log_path), model_or_QA_reruns=0))
        raise SystemExit(exit_code)
    terminal_path = run / 'aggregate_natural_terminal.json'
    save(terminal_path, dict(status='PASS_CONTROL7_AGGREGATE_REAL_NATURAL_EXIT0', exit_code=0,
         naturally_completed=True, process_was_killed_or_restarted=False, argv=argv,
         writer_ref=reg['aggregate_writer_ref'], log_ref=ref(log_path), pid=p.pid, start_ticks=ticks))
    global_path = BASE / 'exports_01/global_completion.json'
    global_done = read(global_path)
    assert global_done['status'] == 'PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS'
    assert len(global_done['actual_unique_MODEL_ids']) == len(global_done['actual_unique_MODEL_proofs']) == 1992
    assert len(global_done['actual_source_ids']) == 426 and len(global_done['batch_natural_terminals']) == 49
    save(run / 'completion.json', dict(
        status='PASS_CONTROL7_REMAINING_AGGREGATE_RECOVERY_NO_NEW_MODEL_OR_QA_NOT_QUALITY',
        coverage=dict(source_count=426, actual_model_calls=1992, logical_requests=1995, batches=49),
        global_completion_path=str(global_path), global_completion_sha256=sha(global_path),
        actual_total_model_calls_in_original_graph=1992, actual_new_model_calls=1959,
        actual_new_model_calls_in_recovery=0, actual_first_QA_calls_in_recovery=0,
        old_control6_failure_ref=reg['old_control6_failure_ref'], old_control6_journal_ref=reg['old_control6_journal_ref'],
        recovery_registration_ref=ref(BASE / 'registration.json'), aggregate_natural_terminal_ref=ref(terminal_path),
        old_successful_operations_repeated=0, old_control6_failure_not_reclassified=True,
        original_controlled_STOP5_not_resumed=True, upstream_actual_success_counts=counts,
        scientific_quality_claim=False))


if __name__ == '__main__':
    main()
