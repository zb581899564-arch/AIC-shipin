"""Run one authorized CPU finalization stage and record its real natural exit."""
import argparse
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
ROOT = CAMPAIGN / 'cpu_finalization_control7_03'
PY = HOME / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = HOME / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
STAGES = {
    'binder': (
        CAMPAIGN / 'temporal_family_package_bootstrap_control7_v2/code/bind.py',
        '9b92209adac7ad78099405e8ee49b3271422ff0583bee510f7e3ecabf1f98b68',
        ['--config', str(CAMPAIGN / 'temporal_family_package_bootstrap_control7_v2/config_02.json')],
        CAMPAIGN / 'temporal_family_native_package_v3/technical_preparation_receipt.json',
        'TECHNICAL_PACKAGE_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM'),
    'original': (
        CAMPAIGN / 'temporal_family_native_package_v3/code/package_family.py',
        '9a0369a1034b96e16a570ca4864032beeb606842b1fc897e833c492094c7962e', [],
        CAMPAIGN / 'temporal_family_native_package_v3/completion.json',
        'COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_NEW_FAMILY_PACKAGES'),
    'half_binder': (
        CAMPAIGN / 'temporal_family_half_bootstrap_control7_v1/code/bind_half.py',
        '0906994b7722a1a16d0fe0950a21f9adca1db596c2ad2d4998397c55f8470222',
        ['--config', str(CAMPAIGN / 'temporal_family_half_bootstrap_control7_v1/config_01.json')],
        CAMPAIGN / 'temporal_family_half_package_v1/technical_preparation_receipt.json',
        'TECHNICAL_HALF_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM'),
    'half': (
        CAMPAIGN / 'temporal_family_half_package_v1/code/package_half.py',
        'e6c371f3642aa37803f1b49ee905c9014beda83628eb65523acd709281fdafdc', [],
        CAMPAIGN / 'temporal_family_half_package_v1/completion.json',
        'COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_SUPPLEMENTARY_HALF_PACKAGES'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def ticks(pid):
    fields = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
    return int(fields[19])


def main(stage):
    if sys.platform != 'linux' or socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Actual registered Linux host required')
    code, expected_sha, extra, completion, expected_status = STAGES[stage]
    if sha(code) != expected_sha:
        raise ValueError('Frozen CPU writer changed')
    if completion.exists():
        raise ValueError('Existing successful or partial stage must not be repeated')
    control = CAMPAIGN / 'temporal_global_recovery_control7_v1'
    terminal = json.loads((control / 'run_01/completion.json').read_text())
    global_done = json.loads((control / 'exports_01/global_completion.json').read_text())
    if terminal['status'] != 'PASS_CONTROL7_REMAINING_AGGREGATE_RECOVERY_NO_NEW_MODEL_OR_QA_NOT_QUALITY':
        raise ValueError('Real independent CONTROL7 aggregate-only natural terminal required')
    if not all(type(terminal[key]) is int and terminal[key] == 0 for key in (
            'actual_new_model_calls_in_recovery', 'actual_first_QA_calls_in_recovery',
            'old_successful_operations_repeated')) or terminal['old_control6_failure_not_reclassified'] is not True:
        raise ValueError('Recovery must preserve all original successful calls and the actual C6 failure')
    if terminal['coverage'] != dict(source_count=426, actual_model_calls=1992, logical_requests=1995, batches=49) or \
            type(terminal['actual_total_model_calls_in_original_graph']) is not int or \
            terminal['actual_total_model_calls_in_original_graph'] != 1992 or \
            type(terminal['actual_new_model_calls']) is not int or terminal['actual_new_model_calls'] != 1959:
        raise ValueError('Original full graph denominator changed')
    global_path = control / 'exports_01/global_completion.json'
    if terminal['global_completion_path'] != str(global_path) or terminal['global_completion_sha256'] != sha(global_path):
        raise ValueError('Real accepted C7 global export identity changed')
    original_control = CAMPAIGN / 'temporal_production_control_v6'
    if (original_control / 'run_01/completion.json').exists():
        raise ValueError('Failed original C6 must never be reclassified as completed')
    for key, filename in (('old_control6_failure_ref', 'failure.json'), ('old_control6_journal_ref', 'journal.jsonl')):
        actual_path = original_control / 'run_01' / filename
        ref = terminal[key]
        if ref['path'] != str(actual_path) or ref['sha256'] != sha(actual_path):
            raise ValueError('Actual old C6 failure or journal identity changed')
    old_failure = json.loads((original_control / 'run_01/failure.json').read_text())
    if old_failure['status'] != 'FAILED_CONTROL_PRESERVE_ALL_ATTEMPTS_SUCCESS_RAW_COSTS' or \
            old_failure['journal_sha256'] != terminal['old_control6_journal_ref']['sha256']:
        raise ValueError('Actual original C6 failure is missing or modified')
    if global_done['status'] != 'PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS':
        raise ValueError('Real complete first QA required')
    out = ROOT / stage
    out.mkdir(exist_ok=False)
    argv = [str(PY), '-B', '-u', str(code), *extra]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', AIC_WORK_ROOT=str(HOME))
    env['PYTHONPATH'] = ':'.join(str(RUN / name) for name in (
        'b_score_aligned_package_v4', 'baseline_a_pts_v1', 'baseline_a_pts_v1/vendor',
        'balanced_two_window_risk_v3', 'temporal_sft8b_v1', 'resource_unlimited_v1_20261007'))
    with (out / 'child.log').open('xb') as log:
        child = subprocess.Popen(argv, cwd=CAMPAIGN, env=env, stdout=log, stderr=subprocess.STDOUT)
        save(out / 'child_launch.json', dict(pid=child.pid, start_ticks=ticks(child.pid), argv=argv,
             utc=dt.datetime.now(dt.timezone.utc).isoformat(), stage=stage, CPU_only=True))
        result = child.wait()
    if result != 0:
        save(out / 'failure.json', dict(exit_code=result, stage=stage, naturally_exited=True,
             log=str(out / 'child.log'), successful_stages_preserved=True, repeated=False))
        raise SystemExit(result)
    actual = json.loads(completion.read_text())
    if actual['status'] != expected_status:
        raise ValueError('Stage exit0 has unexpected completion scope')
    status = 'PASS_ORIGINAL_EIGHT_ARM_RENDERER_NATURAL_EXIT0' if stage == 'original' else 'PASS_CPU_FINALIZATION_STAGE_NATURAL_EXIT0'
    save(out / 'natural_terminal.json', dict(status=status, stage=stage, exit_code=result,
         naturally_completed=True, completion_ref=dict(path=str(completion), sha256=sha(completion)),
         renderer_ref=dict(path=str(code), sha256=expected_sha), argv=argv,
         process_was_killed_or_restarted=False, model_processor_decoder_calls=0,
         utc=dt.datetime.now(dt.timezone.utc).isoformat()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=STAGES, required=True)
    main(parser.parse_args().stage)
